# lfn_batch_file_analyzer_enhanced.py
# -*- coding: utf-8 -*-
import os
import subprocess
import json
import sys

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# Import required packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import spectrogram, find_peaks
import soundfile as sf
from datetime import datetime

# Try to import CuPy for GPU acceleration
try:
    import cupy as cp
    from cupyx.scipy.signal import spectrogram as gpu_spectrogram
    GPU_AVAILABLE = True
    print("🚀 GPU acceleration enabled (CuPy detected)")
except ImportError:
    GPU_AVAILABLE = False
    print("💻 Running on CPU (install cupy for GPU acceleration)")

LF_RANGE = (20, 100)
HF_RANGE = (20000, 24000)
OUTPUT_CSV = "lfn_analysis_results.csv"
OUTPUT_JSON = "lfn_analysis_results.json"
OUTPUT_EXCEL = "lfn_analysis_results.xlsx"
SPECTROGRAM_FOLDER = "spectrograms"
TRENDS_FOLDER = "trends"

# Alert thresholds (dB)
LFN_ALERT_THRESHOLD = -20.0
HF_ALERT_THRESHOLD = -30.0

os.makedirs(SPECTROGRAM_FOLDER, exist_ok=True)
os.makedirs(TRENDS_FOLDER, exist_ok=True)
results = []


def convert_to_wav(input_path, output_path):
    """Convert audio file to WAV format using ffmpeg."""
    command = ["ffmpeg", "-y", "-i", input_path, "-ar", "44100", "-ac", "1", output_path]
    try:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ ffmpeg conversion failed: {e}")
        raise

def compute_spectrogram_optimized(audio_data, sr, use_gpu=False):
    """
    Compute spectrogram with optional GPU acceleration.
    Returns: freqs, times, Sxx_db
    """
    if use_gpu and GPU_AVAILABLE:
        try:
            audio_gpu = cp.asarray(audio_data)
            freqs, times, Sxx = gpu_spectrogram(audio_gpu, fs=sr, nperseg=4096, noverlap=2048)
            # Convert back to CPU for further processing
            Sxx = cp.asnumpy(Sxx)
            freqs = cp.asnumpy(freqs)
            times = cp.asnumpy(times)
        except Exception as e:
            print(f"⚠️ GPU computation failed, falling back to CPU: {e}")
            freqs, times, Sxx = spectrogram(audio_data, fs=sr, nperseg=4096, noverlap=2048)
    else:
        freqs, times, Sxx = spectrogram(audio_data, fs=sr, nperseg=4096, noverlap=2048)
    
    Sxx_db = 10 * np.log10(Sxx + 1e-10)
    return freqs, times, Sxx_db

def detect_peaks_in_range(freqs, spec, freq_range, prominence=5):
    """
    Detect multiple peaks in a frequency range with prominence filtering.
    Returns list of (frequency, dB, time_index) tuples.
    """
    mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
    masked_freqs = freqs[mask]
    masked_spec = spec[mask, :]
    
    if masked_spec.size == 0:
        return []
    
    # Find peaks across all time frames
    all_peaks = []
    for t_idx in range(masked_spec.shape[1]):
        spec_slice = masked_spec[:, t_idx]
        peaks, properties = find_peaks(spec_slice, prominence=prominence)
        for peak in peaks:
            all_peaks.append({
                'frequency': masked_freqs[peak],
                'db': spec_slice[peak],
                'time_idx': t_idx
            })
    
    # Sort by dB and return top peaks
    all_peaks.sort(key=lambda x: x['db'], reverse=True)
    return all_peaks[:10]  # Return top 10 peaks

def analyze_audio_enhanced(filepath, label, block_duration=None, use_gpu=False, track_over_time=True):
    """
    Enhanced audio analysis with GPU support, peak tracking, and alert detection.
    """
    with sf.SoundFile(filepath) as f:
        sr = f.samplerate
        block_frames = int(sr * block_duration) if block_duration else f.frames

        max_lfn_db = -np.inf
        max_lfn_peak = 0
        max_hf_db = -np.inf
        max_hf_peak = 0

        spec_accum = None
        time_accum = []
        current_time = 0.0
        
        # Time-series tracking
        lfn_timeline = []
        hf_timeline = []
        timestamps = []

        for block in f.blocks(blocksize=block_frames, dtype='float32'):
            if block.ndim > 1:
                block = block.mean(axis=1)

            # Use optimized spectrogram computation
            freqs, times, Sxx_db = compute_spectrogram_optimized(block, sr, use_gpu)

            # LFN analysis with peak detection
            lfn_peaks = detect_peaks_in_range(freqs, Sxx_db, LF_RANGE)
            if lfn_peaks:
                top_lfn = lfn_peaks[0]
                if top_lfn['db'] > max_lfn_db:
                    max_lfn_db = top_lfn['db']
                    max_lfn_peak = top_lfn['frequency']
                
                # Track over time
                if track_over_time:
                    lfn_timeline.append(top_lfn['db'])
                    timestamps.append(current_time + times[top_lfn['time_idx']])

            # HF analysis with peak detection
            hf_peaks = detect_peaks_in_range(freqs, Sxx_db, HF_RANGE)
            if hf_peaks:
                top_hf = hf_peaks[0]
                if top_hf['db'] > max_hf_db:
                    max_hf_db = top_hf['db']
                    max_hf_peak = top_hf['frequency']
                
                # Track over time
                if track_over_time:
                    hf_timeline.append(top_hf['db'])

            # Accumulate low-frequency spec for plotting (optimized)
            freq_mask_500 = freqs <= 500
            spec_slice = Sxx_db[freq_mask_500, :]
            if spec_accum is None:
                spec_freqs = freqs[freq_mask_500]
                spec_accum = spec_slice
            else:
                # Use concatenation instead of hstack for better performance
                spec_accum = np.concatenate((spec_accum, spec_slice), axis=1)

            time_accum.extend(times + current_time)
            current_time += len(block) / sr

    # Generate alerts
    alerts = []
    if max_lfn_db > LFN_ALERT_THRESHOLD:
        alerts.append(f"⚠️ LFN ALERT: {max_lfn_db:.1f} dB at {max_lfn_peak:.1f} Hz")
    if max_hf_db > HF_ALERT_THRESHOLD:
        alerts.append(f"⚠️ Ultrasonic ALERT: {max_hf_db:.1f} dB at {max_hf_peak:.1f} Hz")

    # Save spectrogram image
    plt.figure(figsize=(12, 6))
    plt.pcolormesh(time_accum, spec_freqs, spec_accum, shading='gouraud', cmap='viridis')
    title = f"Spectrogram: {label}"
    if alerts:
        title += " [ALERTS DETECTED]"
    plt.title(title)
    plt.ylabel("Frequency (Hz)")
    plt.xlabel("Time (s)")
    plt.colorbar(label="Intensity (dB)")
    out_img = os.path.join(SPECTROGRAM_FOLDER, f"{os.path.splitext(label)[0]}.png")
    plt.tight_layout()
    plt.savefig(out_img, dpi=150)
    plt.close()

    # Generate trend visualization if time tracking enabled
    trend_img = None
    if track_over_time and lfn_timeline:
        trend_img = generate_trend_plot(timestamps, lfn_timeline, hf_timeline, label)

    return {
        "Filename": label,
        "LFN Peak (Hz)": round(float(max_lfn_peak), 2),
        "LFN dB": round(float(max_lfn_db), 2),
        "Ultrasonic Peak (Hz)": round(float(max_hf_peak), 2),
        "Ultrasonic dB": round(float(max_hf_db), 2),
        "Spectrogram": out_img,
        "Trend Plot": trend_img,
        "Alerts": "; ".join(alerts) if alerts else "None",
        "Analysis Timestamp": datetime.now().isoformat(),
        "GPU Accelerated": use_gpu and GPU_AVAILABLE
    }

def generate_trend_plot(timestamps, lfn_values, hf_values, label):
    """Generate time-series trend plot for LFN and HF over time."""
    plt.figure(figsize=(14, 6))
    
    # Ensure arrays are same length
    min_len = min(len(timestamps), len(lfn_values), len(hf_values))
    timestamps = timestamps[:min_len]
    lfn_values = lfn_values[:min_len]
    hf_values = hf_values[:min_len]
    
    plt.subplot(2, 1, 1)
    plt.plot(timestamps, lfn_values, 'b-', linewidth=1.5, label='LFN (20-100 Hz)')
    plt.axhline(y=LFN_ALERT_THRESHOLD, color='r', linestyle='--', label=f'Alert Threshold ({LFN_ALERT_THRESHOLD} dB)')
    plt.ylabel("Intensity (dB)")
    plt.title(f"Frequency Trends Over Time: {label}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 1, 2)
    plt.plot(timestamps, hf_values, 'g-', linewidth=1.5, label='Ultrasonic (20-24 kHz)')
    plt.axhline(y=HF_ALERT_THRESHOLD, color='r', linestyle='--', label=f'Alert Threshold ({HF_ALERT_THRESHOLD} dB)')
    plt.xlabel("Time (s)")
    plt.ylabel("Intensity (dB)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    out_img = os.path.join(TRENDS_FOLDER, f"{os.path.splitext(label)[0]}_trends.png")
    plt.tight_layout()
    plt.savefig(out_img, dpi=150)
    plt.close()
    
    return out_img

def export_results(results, output_dir, formats=None):
    """
    Export analysis results to multiple formats.
    
    Args:
        results: List of analysis results
        output_dir: Directory to save results
        formats: List of export formats (default: ['csv', 'json', 'excel'])
    """
    if formats is None:
        formats = ['csv', 'json', 'excel']
    
    df = pd.DataFrame(results)
    
    exports_done = []
    
    if 'csv' in formats:
        csv_path = os.path.join(output_dir, OUTPUT_CSV)
        df.to_csv(csv_path, index=False)
        exports_done.append(f"CSV: {csv_path}")
    
    if 'json' in formats:
        json_path = os.path.join(output_dir, OUTPUT_JSON)
        # Convert to JSON with proper formatting
        json_data = {
            "analysis_session": {
                "timestamp": datetime.now().isoformat(),
                "total_files": len(results),
                "gpu_enabled": GPU_AVAILABLE
            },
            "results": results
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        exports_done.append(f"JSON: {json_path}")
    
    if 'excel' in formats:
        excel_path = os.path.join(output_dir, OUTPUT_EXCEL)
        try:
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Analysis Results', index=False)
                
                # Add summary sheet
                summary_data = {
                    "Metric": [
                        "Total Files Analyzed",
                        "Files with LFN Alerts",
                        "Files with Ultrasonic Alerts",
                        "Max LFN dB",
                        "Max Ultrasonic dB",
                        "Average LFN dB",
                        "Average Ultrasonic dB"
                    ],
                    "Value": [
                        len(results),
                        sum(1 for r in results if "LFN ALERT" in r.get("Alerts", "")),
                        sum(1 for r in results if "Ultrasonic ALERT" in r.get("Alerts", "")),
                        max(r["LFN dB"] for r in results) if results else 0,
                        max(r["Ultrasonic dB"] for r in results) if results else 0,
                        sum(r["LFN dB"] for r in results) / len(results) if results else 0,
                        sum(r["Ultrasonic dB"] for r in results) / len(results) if results else 0
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            exports_done.append(f"Excel: {excel_path}")
        except Exception as e:
            print(f"⚠️ Excel export failed: {e}")
    
    return exports_done

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced batch audio analysis for LFN and ultrasonic peaks")
    parser.add_argument("directory", help="Path to the audio directory")
    parser.add_argument("--block-duration", type=float, default=None,
                        help="Chunk size in seconds for processing large files")
    parser.add_argument("--gpu", action="store_true",
                        help="Enable GPU acceleration (requires CuPy)")
    parser.add_argument("--no-trends", action="store_true",
                        help="Disable time-series trend tracking")
    parser.add_argument("--export-formats", nargs='+', 
                        default=['csv', 'json', 'excel'],
                        choices=['csv', 'json', 'excel'],
                        help="Output formats (default: all)")
    parser.add_argument("--lfn-threshold", type=float, default=-20.0,
                        help="LFN alert threshold in dB (default: -20.0)")
    parser.add_argument("--hf-threshold", type=float, default=-30.0,
                        help="Ultrasonic alert threshold in dB (default: -30.0)")
    args = parser.parse_args()

    # Update global thresholds
    global LFN_ALERT_THRESHOLD, HF_ALERT_THRESHOLD
    LFN_ALERT_THRESHOLD = args.lfn_threshold
    HF_ALERT_THRESHOLD = args.hf_threshold

    input_dir = args.directory
    use_gpu = args.gpu and GPU_AVAILABLE
    track_trends = not args.no_trends

    print(f"\n{'='*60}")
    print(f"🎵 Enhanced LFN Audio Analysis Tool")
    print(f"{'='*60}")
    print(f"📁 Input Path: {input_dir}")
    print(f"🚀 GPU Acceleration: {'Enabled' if use_gpu else 'Disabled'}")
    print(f"📊 Trend Tracking: {'Enabled' if track_trends else 'Disabled'}")
    print(f"📤 Export Formats: {', '.join(args.export_formats)}")
    print(f"⚠️  LFN Alert Threshold: {LFN_ALERT_THRESHOLD} dB")
    print(f"⚠️  Ultrasonic Alert Threshold: {HF_ALERT_THRESHOLD} dB")
    print(f"{'='*60}\n")

    supported_formats = ["wav", "mp3", "mp4", "flac", "ogg", "m4a"]
    
    # Handle both files and directories
    if os.path.isfile(input_dir):
        audio_files = [os.path.basename(input_dir)]
        input_dir = os.path.dirname(input_dir)
    elif os.path.isdir(input_dir):
        audio_files = [f for f in os.listdir(input_dir) 
                       if f.lower().split('.')[-1] in supported_formats]
    else:
        print(f"❌ Invalid path: {input_dir}")
        return

    if not audio_files:
        print(f"⚠️ No audio files found in {input_dir}")
        return

    print(f"Found {len(audio_files)} audio file(s) to process\n")

    for idx, file in enumerate(audio_files, 1):
        ext = file.lower().split('.')[-1]
        full_path = os.path.join(input_dir, file)
        label = os.path.splitext(file)[0]
        wav_path = full_path
        
        if ext != "wav":
            wav_path = os.path.join(input_dir, f"{label}_converted.wav")
            print(f"[{idx}/{len(audio_files)}] 🔄 Converting {file} to WAV...")
            try:
                convert_to_wav(full_path, wav_path)
            except Exception as e:
                print(f"❌ Conversion failed: {e}\n")
                continue
        
        print(f"[{idx}/{len(audio_files)}] 🔍 Analyzing {file}...")
        try:
            result = analyze_audio_enhanced(
                wav_path, 
                file, 
                block_duration=args.block_duration,
                use_gpu=use_gpu,
                track_over_time=track_trends
            )
            results.append(result)
            
            # Print immediate results
            print(f"  ✓ LFN: {result['LFN Peak (Hz)']} Hz @ {result['LFN dB']} dB")
            print(f"  ✓ Ultrasonic: {result['Ultrasonic Peak (Hz)']} Hz @ {result['Ultrasonic dB']} dB")
            if result['Alerts'] != "None":
                print(f"  {result['Alerts']}")
            print()
            
        except Exception as e:
            print(f"❌ Error analyzing {file}: {e}\n")

    if results:
        print(f"\n{'='*60}")
        print("📊 Exporting results...")
        print(f"{'='*60}")
        
        exports = export_results(results, input_dir, args.export_formats)
        for export in exports:
            print(f"✅ {export}")
        
        print(f"\n📁 Spectrograms saved to: {SPECTROGRAM_FOLDER}/")
        if track_trends:
            print(f"📈 Trend plots saved to: {TRENDS_FOLDER}/")
        
        print(f"\n{'='*60}")
        print(f"✅ Analysis complete! Processed {len(results)} file(s)")
        print(f"{'='*60}\n")
    else:
        print("⚠️ No files processed successfully.")

if __name__ == "__main__":
    main()
