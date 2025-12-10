# -*- coding: utf-8 -*-
import ast
import json
import os
import queue
import sqlite3
import sys
import threading
import time
import traceback
import warnings
from datetime import datetime, timedelta

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# Suppress warnings early
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings(
    'ignore', category=UserWarning, message='.*Matplotlib.*'
)

# Set matplotlib backend before importing pyplot (must be before plt import)
import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sounddevice as sd  # noqa: E402
from scipy.signal import spectrogram, find_peaks  # noqa: E402

# Try GPU acceleration
try:
    import cupy as cp
    from cupyx.scipy.signal import spectrogram as gpu_spectrogram
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# Get script directory for reliable path resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SAMPLE_RATE = 44100  # Default sample rate used as a fallback
DURATION_SEC = 5
LF_RANGE = (20, 100)
HF_RANGE = (20000, 24000)
DB_PATH = os.path.join(SCRIPT_DIR, "lfn_live_log.db")
ALERT_LOG_PATH = os.path.join(SCRIPT_DIR, "alerts_log.json")

# Alert thresholds (dB SPL - Sound Pressure Level)
# Aligned with WHO Environmental Noise Guidelines 2018
LFN_ALERT_THRESHOLD = 45.0  # WHO night limit for sleep protection
HF_ALERT_THRESHOLD = 50.0   # Ultrasonic monitoring threshold

# Spectrogram configuration
SPECTROGRAM_NPERSEG = 2048
SPECTROGRAM_NOVERLAP = 1536
SPECTROGRAM_WINDOW = 'hann'
MAX_FREQ_DISPLAY = 1000  # Maximum frequency to display in main spectrogram
FULL_SPEC_FREQ = 8000   # Full spectrogram frequency range

monitoring = False
audio_queue = queue.Queue()
alert_history = []
use_gpu = False
requested_sample_rate = None


def _safe_float(value):
    """Convert database values into floats, handling legacy byte blobs."""
    if value is None:
        return np.nan
    if isinstance(value, (int, float, np.floating)):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        try:
            return float(np.frombuffer(value, dtype=np.float32, count=1)[0])
        except (ValueError, IndexError):
            return np.nan
    if isinstance(value, str):
        val = value.strip()
        if not val:
            return np.nan
        if val.startswith("b'") or val.startswith('b"'):
            try:
                byte_val = ast.literal_eval(val)
                arr = np.frombuffer(byte_val, dtype=np.float32, count=1)
                return float(arr[0])
            except (ValueError, SyntaxError, IndexError):
                return np.nan
        try:
            return float(val)
        except ValueError:
            return np.nan
    return np.nan


def get_db_connection():
    """Open SQLite connection with graceful UTF-8 handling."""
    conn = sqlite3.connect(DB_PATH)

    def _text_factory(b):
        if isinstance(b, (bytes, bytearray)):
            return b.decode('utf-8', errors='ignore')
        return b

    conn.text_factory = _text_factory
    return conn


def init_db():
    """Initialize SQLite database with enhanced schema."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS live_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            lfn_peak REAL,
            lfn_db REAL,
            hf_peak REAL,
            hf_db REAL,
            alert_triggered INTEGER,
            gpu_accelerated INTEGER
        )''')

        # Create alerts table
        c.execute('''CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            alert_type TEXT,
            frequency REAL,
            db_level REAL,
            message TEXT
        )''')

        def ensure_columns(table, definitions):
            c.execute(f"PRAGMA table_info({table})")
            existing = {row[1] for row in c.fetchall()}
            for column, ddl in definitions.items():
                if column not in existing:
                    c.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

        ensure_columns('live_logs', {
            'alert_triggered': 'alert_triggered INTEGER DEFAULT 0',
            'gpu_accelerated': 'gpu_accelerated INTEGER DEFAULT 0'
        })

        ensure_columns('alerts', {
            'frequency': 'frequency REAL',
            'db_level': 'db_level REAL',
            'message': 'message TEXT'
        })

        conn.commit()
        conn.close()

    except (sqlite3.Error, OSError) as e:
        print(f"[WARN] Warning: Could not initialize database: {e}")
        try:
            conn.close()
        except (sqlite3.Error, NameError):
            pass


def log_alert(alert_type, frequency, db_level, message):
    """Log alert to database and JSON file."""
    conn = get_db_connection()
    c = conn.cursor()
    timestamp = datetime.now().isoformat()

    c.execute(
        "INSERT INTO alerts "
        "(timestamp, alert_type, frequency, db_level, message) "
        "VALUES (?, ?, ?, ?, ?)",
        (timestamp, alert_type, frequency, db_level, message)
    )
    conn.commit()
    conn.close()

    # Also append to JSON log
    alert_data = {
        "timestamp": timestamp,
        "type": alert_type,
        "frequency_hz": frequency,
        "db_level": db_level,
        "message": message
    }
    alert_history.append(alert_data)

    # Save to file
    try:
        with open(ALERT_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump({"alerts": alert_history}, f, indent=2)
    except (OSError, IOError, TypeError) as e:
        print(f"[WARN] Failed to save alert log: {e}")

    print(f"[ALERT] {message}")


def compute_spectrogram_gpu(audio_data, sr):
    """Compute spectrogram with GPU acceleration and enhanced parameters."""
    global use_gpu
    if use_gpu and GPU_AVAILABLE:
        try:
            audio_gpu = cp.asarray(audio_data)
            f, t, Sxx = gpu_spectrogram(
                audio_gpu, fs=sr,
                nperseg=SPECTROGRAM_NPERSEG,
                noverlap=SPECTROGRAM_NOVERLAP,
                window=SPECTROGRAM_WINDOW
            )
            return cp.asnumpy(f), cp.asnumpy(t), cp.asnumpy(Sxx)
        except (RuntimeError, MemoryError, ValueError) as e:
            print(f"[WARN] GPU failed, using CPU: {e}")
            use_gpu = False

    return spectrogram(
        audio_data, fs=sr,
        nperseg=SPECTROGRAM_NPERSEG,
        noverlap=SPECTROGRAM_NOVERLAP,
        window=SPECTROGRAM_WINDOW
    )


def analyze_and_plot(audio_data, sr):
    """Enhanced analysis with peak detection and alert system."""
    try:
        # Ensure we have a proper numpy array
        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data, dtype=np.float32)

        # If it's already a numpy array but wrong dtype, convert it
        if audio_data.dtype != np.float32:
            # Use view if the underlying bytes are float32, otherwise convert
            try:
                audio_data = audio_data.astype(np.float32)
            except (ValueError, TypeError):
                # If direct conversion fails, try interpreting the bytes
                audio_data = np.frombuffer(
                    audio_data.tobytes(), dtype=np.float32
                )

        # Flatten to 1D
        audio_data = audio_data.flatten()

        # Validate audio data
        if not np.isfinite(audio_data).all():
            audio_data = np.nan_to_num(
                audio_data, nan=0.0, posinf=0.0, neginf=0.0
            )

        # Check if audio data is empty or too short
        if len(audio_data) < SPECTROGRAM_NPERSEG:
            print(
                f"[WARN] Audio buffer too short "
                f"({len(audio_data)} samples), skipping analysis"
            )
            return

        # Normalize audio data
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val

        # Compute spectrogram
        f, t, Sxx = compute_spectrogram_gpu(audio_data, sr)
        Sxx_db = 10 * np.log10(Sxx + 1e-10)

        # LFN analysis with peak detection
        lfn_mask = (f >= LF_RANGE[0]) & (f <= LF_RANGE[1])
        lfn_freqs = f[lfn_mask]
        lfn_spec = Sxx_db[lfn_mask, :]

        if lfn_spec.size > 0:
            # Find all peaks in LFN range
            lfn_max_spectrum = np.max(lfn_spec, axis=1)
            peaks, _ = find_peaks(lfn_max_spectrum, prominence=3)

            if len(peaks) > 0:
                # Get strongest peak
                peak_idx = peaks[np.argmax(lfn_max_spectrum[peaks])]
                lfn_peak = lfn_freqs[peak_idx]
                lfn_db = lfn_max_spectrum[peak_idx]
            else:
                idx = np.argmax(lfn_spec)
                lfn_peak = lfn_freqs[np.unravel_index(idx, lfn_spec.shape)[0]]
                lfn_db = np.max(lfn_spec)
        else:
            lfn_peak, lfn_db = 0, -100

        # Ultrasonic analysis with peak detection
        hf_mask = (f >= HF_RANGE[0]) & (f <= HF_RANGE[1])
        hf_freqs = f[hf_mask]
        hf_spec = Sxx_db[hf_mask, :]

        if hf_freqs.size > 0 and hf_spec.size > 0:
            hf_max_spectrum = np.max(hf_spec, axis=1)
            peaks, _ = find_peaks(hf_max_spectrum, prominence=3)

            if len(peaks) > 0:
                peak_idx = peaks[np.argmax(hf_max_spectrum[peaks])]
                hf_peak = hf_freqs[peak_idx]
                hf_db = hf_max_spectrum[peak_idx]
            else:
                idx = np.argmax(hf_spec)
                hf_peak = hf_freqs[np.unravel_index(idx, hf_spec.shape)[0]]
                hf_db = np.max(hf_spec)
        else:
            hf_peak, hf_db = 0, -100

        # Check for alerts
        alert_triggered = False
        if lfn_db > LFN_ALERT_THRESHOLD:
            log_alert(
                "LFN", lfn_peak, lfn_db,
                f"[LFN] ALERT: {lfn_peak:.1f} Hz @ {lfn_db:.1f} dB"
            )
            alert_triggered = True

        if hf_db > HF_ALERT_THRESHOLD:
            log_alert(
                "Ultrasonic", hf_peak, hf_db,
                f"[HF] Ultrasonic ALERT: {hf_peak:.1f} Hz @ {hf_db:.1f} dB"
            )
            alert_triggered = True

        # Database logging
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """INSERT INTO live_logs
               (timestamp, lfn_peak, lfn_db, hf_peak, hf_db,
                alert_triggered, gpu_accelerated)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), lfn_peak, lfn_db, hf_peak, hf_db,
             int(alert_triggered), int(use_gpu and GPU_AVAILABLE))
        )
        conn.commit()
        conn.close()

        # Enhanced plot with multiple spectrogram views
        plt.clf()
        fig = plt.gcf()
        fig.set_size_inches(16, 12)

        # Create timestamp for this analysis
        analysis_time = datetime.now().strftime("%H:%M:%S")

        # Main LFN-focused spectrogram (subplot 1)
        ax1 = plt.subplot(3, 2, 1)
        freq_mask_lfn = f <= MAX_FREQ_DISPLAY
        im1 = plt.pcolormesh(
            t, f[freq_mask_lfn], Sxx_db[freq_mask_lfn, :],
            shading='gouraud', cmap='plasma', vmin=-80, vmax=-20
        )

        # Add alert marker if triggered
        title = (
            f"LFN Spectrogram ({analysis_time}) - "
            f"Peak: {lfn_peak:.1f} Hz @ {lfn_db:.1f} dB"
        )
        if alert_triggered and lfn_db > LFN_ALERT_THRESHOLD:
            title += " [ALERT]"
            ax1.set_title(title, color='red', fontweight='bold', fontsize=10)
        else:
            ax1.set_title(title, fontsize=10)

        ax1.set_ylabel("Frequency (Hz)")
        ax1.set_xlabel("Time (s)")

        # Add LFN range indicators
        ax1.axhline(
            y=LF_RANGE[0], color='cyan', linestyle='--',
            linewidth=1, alpha=0.8, label='LFN Range'
        )
        ax1.axhline(
            y=LF_RANGE[1], color='cyan', linestyle='--',
            linewidth=1, alpha=0.8
        )
        ax1.legend(loc='upper right', fontsize=8)

        # Add colorbar for LFN spectrogram
        cbar1 = plt.colorbar(im1, ax=ax1, shrink=0.8)
        cbar1.set_label("Intensity (dB)", fontsize=8)

        # Full frequency range spectrogram (subplot 2)
        ax2 = plt.subplot(3, 2, 2)
        freq_mask_full = f <= FULL_SPEC_FREQ
        im2 = plt.pcolormesh(
            t, f[freq_mask_full], Sxx_db[freq_mask_full, :],
            shading='gouraud', cmap='viridis', vmin=-80, vmax=-30
        )

        ax2.set_title(
            f"Full Spectrum (0-{FULL_SPEC_FREQ} Hz) - "
            f"HF: {hf_peak:.1f} Hz @ {hf_db:.1f} dB",
            fontsize=10
        )
        ax2.set_ylabel("Frequency (Hz)")
        ax2.set_xlabel("Time (s)")

        # Add HF range indicators if visible
        if HF_RANGE[0] <= FULL_SPEC_FREQ:
            hf_display_max = min(HF_RANGE[1], FULL_SPEC_FREQ)
            ax2.axhline(
                y=HF_RANGE[0], color='orange', linestyle=':',
                linewidth=1, alpha=0.6, label='HF Range'
            )
            if hf_display_max < FULL_SPEC_FREQ:
                ax2.axhline(
                    y=hf_display_max, color='orange', linestyle=':',
                    linewidth=1, alpha=0.6
                )
            ax2.legend(loc='upper right', fontsize=8)

        cbar2 = plt.colorbar(im2, ax=ax2, shrink=0.8)
        cbar2.set_label("Intensity (dB)", fontsize=8)

        # LFN Frequency Spectrum Analysis (subplot 3)
        ax3 = plt.subplot(3, 2, 3)
        if lfn_spec.size > 0:
            lfn_spectrum = np.mean(Sxx_db[lfn_mask, :], axis=1)
        else:
            lfn_spectrum = []
        if len(lfn_spectrum) > 0:
            ax3.plot(lfn_freqs, lfn_spectrum, 'b-', linewidth=2, alpha=0.8)
            ax3.fill_between(lfn_freqs, lfn_spectrum, alpha=0.3, color='blue')
            if lfn_peak > 0:
                ax3.axvline(
                    x=lfn_peak, color='red', linestyle='--',
                    linewidth=2, label=f'Peak: {lfn_peak:.1f} Hz'
                )
                ax3.legend(fontsize=8)
        ax3.set_xlabel("Frequency (Hz)")
        ax3.set_ylabel("Intensity (dB)")
        ax3.set_title("LFN Frequency Spectrum", fontsize=10)
        ax3.grid(True, alpha=0.3)

        # Peak Detection Visualization (subplot 4)
        ax4 = plt.subplot(3, 2, 4)
        if lfn_spec.size > 0:
            lfn_max_spectrum = np.max(lfn_spec, axis=1)
            peaks, _ = find_peaks(lfn_max_spectrum, prominence=3)

            ax4.plot(
                lfn_freqs, lfn_max_spectrum, 'g-',
                linewidth=1.5, label='Max Spectrum'
            )
            if len(peaks) > 0:
                ax4.plot(
                    lfn_freqs[peaks], lfn_max_spectrum[peaks], 'ro',
                    markersize=8, label=f'{len(peaks)} Peaks Detected'
                )
                # Annotate strongest peaks
                for i, peak in enumerate(peaks[:3]):  # Show top 3 peaks
                    ax4.annotate(
                        f'{lfn_freqs[peak]:.1f}Hz',
                        (lfn_freqs[peak], lfn_max_spectrum[peak]),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8, alpha=0.8
                    )
            ax4.legend(fontsize=8)
        ax4.set_xlabel("Frequency (Hz)")
        ax4.set_ylabel("Peak Intensity (dB)")
        ax4.set_title("LFN Peak Detection", fontsize=10)
        ax4.grid(True, alpha=0.3)

        # Time series plot of recent measurements (subplot 5-6)
        ax5 = plt.subplot(3, 1, 3)
        conn = get_db_connection()
        try:
            # First try measurements table, then fall back to live_logs
            try:
                df = pd.read_sql_query(
                    "SELECT * FROM measurements ORDER BY id DESC LIMIT 100",
                    conn
                )
            except (sqlite3.OperationalError, pd.errors.DatabaseError):
                df = pd.read_sql_query(
                    "SELECT * FROM live_logs ORDER BY id DESC LIMIT 100",
                    conn
                )

            if len(df) > 0:
                numeric_columns = [
                    'lfn_peak', 'lfn_db', 'hf_peak', 'hf_db',
                    'lfn_peak_freq', 'lfn_peak_db',
                    'hf_peak_freq', 'hf_peak_db'
                ]
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = df[col].apply(_safe_float)
                # Remove rows invalid for the columns we plan to plot
                check_cols = [
                    'lfn_db', 'hf_db', 'lfn_peak_db', 'hf_peak_db'
                ]
                needed_cols = [c for c in check_cols if c in df.columns]
                if needed_cols:
                    df = df.dropna(subset=needed_cols, how='all')
        except (sqlite3.Error, pd.errors.DatabaseError, ValueError) as e:
            print(f"[WARN] Could not read database for timeline: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()

        if len(df) > 0:
            df = df.iloc[::-1]  # Reverse to chronological order
            indices = range(len(df))

            # Create time axis from recent measurements
            if len(indices) > 50:
                time_points = [i * DURATION_SEC for i in indices[-50:]]
            else:
                time_points = [i * DURATION_SEC for i in indices]
            recent_df = df.iloc[-50:] if len(df) > 50 else df

            # Check for column existence and use appropriate column names
            if 'lfn_db' in recent_df.columns:
                lfn_col = 'lfn_db'
            elif 'lfn_peak_db' in recent_df.columns:
                lfn_col = 'lfn_peak_db'
            else:
                lfn_col = None

            if 'hf_db' in recent_df.columns:
                hf_col = 'hf_db'
            elif 'hf_peak_db' in recent_df.columns:
                hf_col = 'hf_peak_db'
            else:
                hf_col = None
            if 'alert_triggered' in recent_df.columns:
                alert_col = 'alert_triggered'
            else:
                alert_col = None

            if lfn_col and len(time_points) == len(recent_df):
                lfn_label = f'LFN ({LF_RANGE[0]}-{LF_RANGE[1]} Hz)'
                ax5.plot(time_points, recent_df[lfn_col],
                         'b-', label=lfn_label, linewidth=2)
            if hf_col and len(time_points) == len(recent_df):
                hf_label = (
                    f'Ultrasonic ({HF_RANGE[0]/1000:.0f}-'
                    f'{HF_RANGE[1]/1000:.0f} kHz)'
                )
                ax5.plot(
                    time_points, recent_df[hf_col], 'g-',
                    label=hf_label, linewidth=2
                )

            # Add threshold lines
            ax5.axhline(
                y=LFN_ALERT_THRESHOLD, color='red', linestyle='--',
                label=f'LFN Threshold ({LFN_ALERT_THRESHOLD} dB)',
                alpha=0.7, linewidth=1.5
            )
            ax5.axhline(
                y=HF_ALERT_THRESHOLD, color='orange', linestyle='--',
                label=f'HF Threshold ({HF_ALERT_THRESHOLD} dB)',
                alpha=0.7, linewidth=1.5
            )

            # Highlight alert regions if data is available
            if alert_col and len(time_points) == len(recent_df):
                alert_mask = recent_df[alert_col] == 1
                if alert_mask.any():
                    ax5.fill_between(
                        time_points, -100, 0, where=alert_mask,
                        alpha=0.2, color='red', label='Alert Periods'
                    )

            ax5.set_xlabel("Time (seconds ago)")
            ax5.set_ylabel("Intensity (dB)")
            last_time = time_points[-1] if time_points else 0
            ax5.set_title(
                f"Frequency Intensity Timeline "
                f"(Last {len(recent_df)} measurements over {last_time:.0f}s)",
                fontsize=10
            )
            ax5.legend(loc='upper left', fontsize=8)
            ax5.grid(True, alpha=0.3)

            # Invert x-axis to show most recent on the right
            ax5.set_xlim(max(time_points) if time_points else 0, 0)

        plt.tight_layout(pad=2.0)

        # Create organized folder structure for spectrograms (use absolute path)
        date_folder = datetime.now().strftime("%Y-%m-%d")
        spec_dir = os.path.join(SCRIPT_DIR, "spectrograms", date_folder)
        
        # Ensure directory exists with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                os.makedirs(spec_dir, exist_ok=True)
                # Verify it actually exists
                if os.path.exists(spec_dir) and os.path.isdir(spec_dir):
                    break
                else:
                    if attempt < max_retries - 1:
                        time.sleep(0.1)
            except OSError as e:
                if attempt == max_retries - 1:
                    raise OSError(f"Failed to create directory {spec_dir}: {e}")
                time.sleep(0.1)

        # Generate shorter filename to avoid Windows MAX_PATH (260 char) issues
        timestamp = datetime.now().strftime("%H%M%S")
        alert_suffix = "_A" if alert_triggered else ""
        gpu_suffix = "_G" if (use_gpu and GPU_AVAILABLE) else ""

        # Shortened format: lfn_HHMMSS_L{freq}_{db}_H{freq}_{db}.png
        filename = (
            f"lfn_{timestamp}_L{lfn_peak:.0f}_{lfn_db:.1f}_"
            f"H{hf_peak:.0f}_{hf_db:.1f}{alert_suffix}{gpu_suffix}.png"
        )
        output_path = os.path.join(spec_dir, filename)
        
        # Use Windows long path prefix if path is getting long
        if len(output_path) > 240 and os.name == 'nt':
            if not output_path.startswith('\\\\?\\'):
                output_path = '\\\\?\\' + os.path.abspath(output_path)

        # Save high-quality spectrogram
        plt.savefig(
            output_path, dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none'
        )
        plt.close(fig)

        # Create summary info file for this spectrogram
        info_path = output_path.replace('.png', '_info.txt')
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write("LFN Real-Time Monitor Spectrogram Analysis\n")
            f.write("==========================================\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"LFN Peak: {lfn_peak:.2f} Hz at {lfn_db:.2f} dB\n")
            f.write(f"HF Peak: {hf_peak:.2f} Hz at {hf_db:.2f} dB\n")
            alert_str = 'Yes' if alert_triggered else 'No'
            f.write(f"Alert Triggered: {alert_str}\n")
            gpu_str = 'Yes' if (use_gpu and GPU_AVAILABLE) else 'No'
            f.write(f"GPU Acceleration: {gpu_str}\n")
            f.write(f"Sample Rate: {sr} Hz\n")
            f.write(f"Analysis Duration: {DURATION_SEC} seconds\n")
            f.write(f"LFN Range: {LF_RANGE[0]}-{LF_RANGE[1]} Hz\n")
            f.write(f"HF Range: {HF_RANGE[0]}-{HF_RANGE[1]} Hz\n")
            f.write(f"LFN Threshold: {LFN_ALERT_THRESHOLD} dB\n")
            f.write(f"HF Threshold: {HF_ALERT_THRESHOLD} dB\n")

        # Enhanced status output
        status_icon = "[ALERT]" if alert_triggered else "[DATA]"
        gpu_status = "[GPU]" if (use_gpu and GPU_AVAILABLE) else "[CPU]"

        print(
            f"{status_icon} LFN: {lfn_peak:.1f}Hz@{lfn_db:.1f}dB | "
            f"HF: {hf_peak:.1f}Hz@{hf_db:.1f}dB {gpu_status} | "
            f"[SAVED] {output_path}"
        )

    except (ValueError, TypeError, RuntimeError, OSError) as e:
        print(f"[ERROR] Error during analysis: {e}")
        traceback.print_exc()
        # Still try to log basic data to database
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute(
                """INSERT INTO live_logs
                   (timestamp, lfn_peak, lfn_db, hf_peak, hf_db,
                    alert_triggered, gpu_accelerated)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), 0, -100, 0, -100, 0,
                 int(use_gpu and GPU_AVAILABLE))
            )
            conn.commit()
            conn.close()
        except sqlite3.Error:
            pass  # Silently fail if we can't even log basic data


def audio_callback(indata, _frames, _time_info, _status):
    """Audio stream callback - float32 data from sounddevice."""
    if monitoring:
        # With dtype='float32' in InputStream, indata is already float32
        audio_queue.put(indata.copy())


def _build_rate_candidates(device_info):
    rates = []
    if requested_sample_rate:
        rates.append(float(requested_sample_rate))
    rates.append(float(SAMPLE_RATE))
    device_default_sr = float(device_info.get('default_samplerate') or 0)
    if device_default_sr:
        if not any(abs(device_default_sr - r) < 1 for r in rates):
            rates.append(device_default_sr)
    return rates


def _attempt_stream(device_idx, channels):
    device_info = sd.query_devices(device_idx, 'input')
    preferred_rates = _build_rate_candidates(device_info)
    attempts = []

    for rate in preferred_rates:
        try:
            sd.check_input_settings(
                device=device_idx, samplerate=rate, channels=channels
            )
            # Explicitly specify dtype='float32' for proper audio format
            test_stream = sd.InputStream(
                samplerate=rate, device=device_idx, channels=channels,
                callback=audio_callback, dtype='float32'
            )
            try:
                test_stream.start()
                test_stream.stop()
            finally:
                test_stream.close()

            if requested_sample_rate and abs(rate - requested_sample_rate) > 1:
                print(
                    f"[INFO] Requested sample rate "
                    f"{int(requested_sample_rate)} Hz unsupported; "
                    f"using {int(rate)} Hz instead."
                )
            elif not requested_sample_rate and abs(rate - SAMPLE_RATE) > 1:
                print(
                    f"[INFO] Adjusted sample rate to device default "
                    f"({int(rate)} Hz) to ensure compatibility."
                )

            # Create main stream with explicit float32 dtype
            stream = sd.InputStream(
                samplerate=rate, device=device_idx, channels=channels,
                callback=audio_callback, dtype='float32'
            )
            return stream, rate, device_info
        except sd.PortAudioError as err:
            attempts.append((rate, err))
    return None, None, attempts


def _find_alternative_device(original_idx):
    try:
        target_name = sd.query_devices(original_idx, 'input')['name']
    except (sd.PortAudioError, IndexError, KeyError):
        return []
    alternatives = []
    for idx, info in enumerate(sd.query_devices()):
        if info['max_input_channels'] <= 0:
            continue
        if info['name'] == target_name and idx != original_idx:
            alternatives.append(idx)
    return alternatives


def record_loop(device=None):
    """Main recording and analysis loop."""
    global monitoring

    try:
        device_info = sd.query_devices(device, 'input')
        max_channels = device_info['max_input_channels']
        channels = min(max_channels, 2)
        if channels == 0:
            print(
                f"[ERROR] Error: Device {device} has no input "
                "channels. Please select an input device."
            )
            monitoring = False
            return
    except (sd.PortAudioError, IndexError, KeyError) as e:
        print(f"[ERROR] Error querying device: {e}")
        monitoring = False
        return

    stream, samplerate, attempts = _attempt_stream(device, channels)

    if stream is None:
        if attempts:
            last_errno = getattr(attempts[-1][1], 'errno', None)
        else:
            last_errno = None
        if last_errno == -9999:
            alternatives = _find_alternative_device(device)
            for alt_idx in alternatives:
                alt_info = sd.query_devices(alt_idx, 'input')
                alt_channels = min(alt_info['max_input_channels'], 2)
                stream, samplerate, alt_attempts = _attempt_stream(
                    alt_idx, alt_channels
                )
                if stream is not None:
                    print(
                        f"ℹ️ Switched to alternate driver for "
                        f"'{alt_info['name']}' (device #{alt_idx}) "
                        "to bypass host error."
                    )
                    device = alt_idx
                    channels = alt_channels
                    if isinstance(alt_attempts, list):
                        attempts.extend(alt_attempts)
                    break
            if stream is None:
                print(
                    "[ERROR] Host API error persists even after "
                    "trying alternate drivers. Consider selecting "
                    "the MME/DirectSound variant of the device or "
                    "lowering the channel count."
                )
                if attempts:
                    rates_str = ", ".join(
                        f"{int(rate)} Hz" for rate, _ in attempts
                    )
                    print(f"   Attempted sample rates: {rates_str}")
                monitoring = False
                return
        else:
            if attempts:
                msg = ", ".join(
                    f"{int(rate)} Hz ({err})" for rate, err in attempts
                )
                print(f"[ERROR] Unable to open input stream. Attempts: {msg}")
            else:
                print(
                    "[ERROR] Unable to open input stream "
                    "for the selected device."
                )
            monitoring = False
            return

    try:
        with stream:
            print(
                f"[*] Monitoring started with {channels} channel(s) "
                "(Press ENTER to stop)..."
            )
            if use_gpu and GPU_AVAILABLE:
                print("[GPU] GPU acceleration enabled")
            print(f"[RATE] Sample rate: {int(samplerate)} Hz")
            print(
                f"[SPEC] Spectrogram config: {SPECTROGRAM_NPERSEG} samples, "
                f"{SPECTROGRAM_WINDOW} window"
            )
            print(
                "[SAVE] Enhanced spectrograms saved to 'spectrograms/' "
                "folder with date organization"
            )

            while monitoring:
                time.sleep(DURATION_SEC)
                buffer = []
                while not audio_queue.empty():
                    chunk = audio_queue.get()
                    # Ensure chunk is float32 numpy array
                    if isinstance(chunk, np.ndarray):
                        if chunk.dtype != np.float32:
                            chunk = chunk.astype(np.float32)
                    else:
                        chunk = np.asarray(chunk, dtype=np.float32)
                    buffer.append(chunk)

                if buffer:
                    try:
                        # Concatenate all chunks
                        audio_data = np.concatenate(buffer, axis=0)

                        # Ensure float32
                        if audio_data.dtype != np.float32:
                            audio_data = audio_data.astype(np.float32)

                        # Convert to mono if stereo
                        if audio_data.ndim > 1:
                            audio_data = np.mean(
                                audio_data, axis=1, dtype=np.float32
                            )

                        analyze_and_plot(audio_data, samplerate)
                    except ValueError as ve:
                        print(f"[WARN] Audio data conversion issue: {ve}")
                        continue
                    except (TypeError, RuntimeError, OSError) as e:
                        print(f"[ERROR] Error during analysis: {e}")
                        traceback.print_exc()
                        continue
    except sd.PortAudioError as e:
        print(f"[ERROR] Error opening audio stream: {e}")
        monitoring = False
    except (OSError, RuntimeError) as e:
        print(f"[ERROR] Unexpected error during monitoring: {e}")
        monitoring = False


def toggle_monitoring(device=None):
    """Start/stop monitoring."""
    global monitoring
    if not monitoring:
        monitoring = True
        thread = threading.Thread(
            target=record_loop, args=(device,), daemon=True
        )
        thread.start()
    else:
        monitoring = False
        print("[STOP] Monitoring stopped.")


def print_statistics():
    """Print session statistics."""
    conn = get_db_connection()

    # Get overall stats
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM live_logs")
    total_measurements = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM alerts")
    total_alerts = cursor.fetchone()[0]

    sql = ("SELECT AVG(lfn_db), MAX(lfn_db), "
           "AVG(hf_db), MAX(hf_db) FROM live_logs")
    cursor.execute(sql)
    stats = cursor.fetchone()

    conn.close()

    print(f"\n{'='*60}")
    print("[STATS] Session Statistics")
    print(f"{'='*60}")
    print(f"Total Measurements: {total_measurements}")
    print(f"Total Alerts: {total_alerts}")
    if stats:
        lfn_avg, lfn_max, hf_avg, hf_max = stats

        def _fmt(value):
            try:
                return f"{float(value):.2f}"
            except (TypeError, ValueError):
                return "N/A"

        if any(value is not None for value in stats):
            print(f"LFN Average: {_fmt(lfn_avg)} dB | Max: {_fmt(lfn_max)} dB")
            print(f"Ultrasonic Average: {_fmt(hf_avg)} dB | "
                  f"Max: {_fmt(hf_max)} dB")
    print(f"{'='*60}\n")


def print_spectrogram_info():
    """Display information about saved spectrograms."""
    print(f"\n{'='*60}")
    print("[INFO] Spectrogram Information")
    print(f"{'='*60}")

    base_dir = os.path.join(SCRIPT_DIR, "spectrograms")
    if not os.path.exists(base_dir):
        print("No spectrograms folder found.")
        print(f"{'='*60}\n")
        return

    total_files = 0
    total_size = 0
    folders = []

    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            folder_files = [
                f for f in os.listdir(item_path)
                if f.endswith('.png')
            ]
            folder_size = sum(
                os.path.getsize(os.path.join(item_path, f))
                for f in os.listdir(item_path)
            )
            folders.append((item, len(folder_files), folder_size))
            total_files += len(folder_files)
            total_size += folder_size

    if folders:
        print(f"Total spectrograms: {total_files}")
        print(f"Total storage: {total_size / 1024 / 1024:.2f} MB")
        print("\nBy date folder:")
        for folder, count, size in sorted(folders, reverse=True):
            print(f"  {folder}: {count} files ({size / 1024 / 1024:.2f} MB)")
    else:
        print("No spectrograms found.")

    print(f"{'='*60}\n")


def clean_old_spectrograms():
    """Clean old spectrogram files (older than 7 days)."""
    import shutil
    from pathlib import Path

    print(f"\n{'='*60}")
    print("[CLEAN] Cleaning Old Spectrograms")
    print(f"{'='*60}")

    base_dir = Path(os.path.join(SCRIPT_DIR, "spectrograms"))
    if not base_dir.exists():
        print("No spectrograms folder found.")
        print(f"{'='*60}\n")
        return

    cutoff_date = datetime.now() - timedelta(days=7)
    cleaned_count = 0
    cleaned_size = 0

    for folder in base_dir.iterdir():
        if folder.is_dir():
            try:
                folder_date = datetime.strptime(folder.name, "%Y-%m-%d")
                if folder_date < cutoff_date:
                    folder_size = sum(
                        f.stat().st_size
                        for f in folder.rglob('*')
                        if f.is_file()
                    )
                    file_count = len(list(folder.glob('*.png')))
                    shutil.rmtree(folder)
                    cleaned_count += file_count
                    cleaned_size += folder_size
                    size_mb = folder_size / 1024 / 1024
                    print(f"  Removed {folder.name}: "
                          f"{file_count} files ({size_mb:.2f} MB)")
            except ValueError:
                # Skip folders that don't match date format
                continue

    if cleaned_count > 0:
        freed_mb = cleaned_size / 1024 / 1024
        print(f"\nCleaned {cleaned_count} old spectrograms "
              f"({freed_mb:.2f} MB freed)")
    else:
        print("No old spectrograms to clean.")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced real-time LFN monitor with GPU acceleration"
    )
    parser.add_argument(
        "--gpu", action="store_true", help="Enable GPU acceleration"
    )
    parser.add_argument(
        "--lfn-threshold", type=float, default=-20.0,
        help="LFN alert threshold in dB"
    )
    parser.add_argument(
        "--hf-threshold", type=float, default=-30.0,
        help="Ultrasonic alert threshold in dB"
    )
    parser.add_argument(
        "--device", type=int, default=None,
        help="Audio input device index"
    )
    parser.add_argument(
        "--sample-rate", type=float, default=None,
        help="Override sample rate in Hz (falls back to device default)"
    )
    parser.add_argument(
        "--auto-start", action="store_true",
        help="Automatically start monitoring without user input"
    )
    parser.add_argument(
        "--duration", type=int, default=None,
        help="Auto-stop after specified seconds (0 = run indefinitely)"
    )
    args = parser.parse_args()

    # Set global settings
    use_gpu = args.gpu
    LFN_ALERT_THRESHOLD = args.lfn_threshold
    HF_ALERT_THRESHOLD = args.hf_threshold
    requested_sample_rate = args.sample_rate

    # Ensure output directories exist at startup
    try:
        os.makedirs(os.path.join(SCRIPT_DIR, "spectrograms"), exist_ok=True)
        date_folder = datetime.now().strftime("%Y-%m-%d")
        os.makedirs(os.path.join(SCRIPT_DIR, "spectrograms", date_folder), exist_ok=True)
        print(f"[OK] Output directory verified: {os.path.join(SCRIPT_DIR, 'spectrograms', date_folder)}")
    except OSError as e:
        print(f"[WARN] Could not create output directories: {e}")

    init_db()

    print(f"\n{'='*60}")
    print("[*] Enhanced LFN Real-Time Monitor")
    print("    with Advanced Spectrograms")
    print(f"{'='*60}")
    gpu_status = 'Enabled' if use_gpu and GPU_AVAILABLE else 'Disabled'
    print(f"GPU Acceleration: {gpu_status}")
    print(f"LFN Alert Threshold: {LFN_ALERT_THRESHOLD} dB")
    print(f"Ultrasonic Alert Threshold: {HF_ALERT_THRESHOLD} dB")
    print(f"Spectrogram Resolution: {SPECTROGRAM_NPERSEG} samples, "
          f"{SPECTROGRAM_WINDOW} window")
    print(f"{'='*60}\n")

    if args.device is None:
        print("Available audio input devices:")
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            # Only show devices with input channels
            if dev['max_input_channels'] > 0:
                marker = ">"
                if i != sd.default.device[0]:
                    marker = " "
                in_ch = dev['max_input_channels']
                out_ch = dev['max_output_channels']
                print(f"{marker} {i:3d} {dev['name']}, {dev['hostapi']} "
                      f"({in_ch} in, {out_ch} out)")

        try:
            prompt = "\nEnter device index or press ENTER for default: "
            selected_device = input(prompt)
        except EOFError:
            # Auto-select default device when input stream is closed
            print("\n[AUTO] Input stream closed, using default device...")
            selected_device = None
        except KeyboardInterrupt:
            print("\n[EXIT] Device selection cancelled.")
            sys.exit(0)

        if selected_device and selected_device.strip().isdigit():
            selected_device = int(selected_device)
        else:
            selected_device = None

        # Validate selected device has input channels
        if selected_device is not None:
            try:
                device_info = sd.query_devices(selected_device, 'input')
                if device_info['max_input_channels'] == 0:
                    print(f"[ERROR] Error: Device {selected_device} "
                          "has no input channels. Select an input device.")
                    exit(1)
            except (sd.PortAudioError, IndexError, KeyError) as e:
                print(f"[ERROR] Error: Invalid device selection - {e}")
                exit(1)
    else:
        selected_device = args.device
        # Validate the specified device
        try:
            device_info = sd.query_devices(selected_device, 'input')
            if device_info['max_input_channels'] == 0:
                print(f"[ERROR] Error: Device {selected_device} "
                      "has no input channels. Select an input device.")
                exit(1)
        except (sd.PortAudioError, IndexError, KeyError) as e:
            print(f"[ERROR] Error: Invalid device {selected_device} - {e}")
            exit(1)

    # Auto-start mode
    if args.auto_start:
        print("\n[AUTO] Auto-start enabled - beginning monitoring...")
        toggle_monitoring(device=selected_device)
        
        try:
            if args.duration and args.duration > 0:
                print(f"[AUTO] Will run for {args.duration} seconds...")
                time.sleep(args.duration)
                monitoring = False
                print(f"\n[AUTO] Duration reached ({args.duration}s), stopping...")
            else:
                print("[AUTO] Running indefinitely - press Ctrl+C to stop")
                while monitoring:
                    time.sleep(1)
        except KeyboardInterrupt:
            monitoring = False
            print("\n[EXIT] Monitoring stopped by user.")
        finally:
            print_statistics()
    else:
        # Interactive mode
        print("\n[*] Commands:")
        print("  ENTER - Start/Stop monitoring")
        print("  's' + ENTER - Show statistics")
        print("  'spec' + ENTER - Show spectrogram info")
        print("  'clean' + ENTER - Clean old spectrograms")
        print("  Ctrl+C - Exit\n")

        try:
            while True:
                try:
                    cmd = input()
                except EOFError:
                    # Auto-start on EOF instead of exiting
                    print("\n[AUTO] Input closed, starting monitoring...")
                    if not monitoring:
                        toggle_monitoring(device=selected_device)
                    # Keep running until Ctrl+C
                    try:
                        while monitoring:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        pass
                    break
                except KeyboardInterrupt:
                    monitoring = False
                    print("\n[EXIT] Monitoring session ended.")
                    break

                if cmd.lower() == 's':
                    print_statistics()
                elif cmd.lower() == 'spec':
                    print_spectrogram_info()
                elif cmd.lower() == 'clean':
                    clean_old_spectrograms()
                else:
                    toggle_monitoring(device=selected_device)
        except KeyboardInterrupt:
            monitoring = False
            print("\n[EXIT] Monitoring session ended.")
        except (OSError, RuntimeError) as e:
            monitoring = False
            print(f"\n[ERROR] Unexpected error: {e}")
        finally:
            print_statistics()

