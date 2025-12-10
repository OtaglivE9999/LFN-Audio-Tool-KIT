# LFN Audio Toolkit - Troubleshooting Guide

This guide covers common issues and their solutions when using the LFN Audio Toolkit.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Audio Device Issues](#audio-device-issues)
- [FFmpeg Issues](#ffmpeg-issues)
- [GPU Acceleration Issues](#gpu-acceleration-issues)
- [Runtime Errors](#runtime-errors)
- [Performance Issues](#performance-issues)
- [Output File Issues](#output-file-issues)
- [Platform-Specific Issues](#platform-specific-issues)

---

## Installation Issues

### Problem: `pip install` fails with permission errors

**Symptoms:**
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solutions:**

**Option 1:** Install for current user only (recommended)
```bash
pip install --user -r requirements.txt
```

**Option 2:** Use virtual environment (best practice)
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Option 3:** Run as administrator (Windows only, not recommended)
```bash
# Right-click Command Prompt -> Run as Administrator
pip install -r requirements.txt
```

---

### Problem: `ModuleNotFoundError` after installation

**Symptoms:**
```python
ModuleNotFoundError: No module named 'soundfile'
```

**Solutions:**

1. **Verify installation:**
```bash
pip list | grep soundfile  # Linux/Mac
pip list | findstr soundfile  # Windows
```

2. **Reinstall the missing package:**
```bash
pip install --upgrade soundfile
```

3. **Check Python version mismatch:**
```bash
# Ensure you're using the same Python version
python --version
pip --version
```

4. **Use the correct pip for your Python:**
```bash
python -m pip install soundfile
```

---

### Problem: `setup.py` fails during installation

**Symptoms:**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solutions:**

**Windows:**
1. Install Microsoft C++ Build Tools:
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++"

**Alternative:** Use precompiled wheels
```bash
pip install --only-binary :all: -r requirements.txt
```

---

## Audio Device Issues

### Problem: No audio input devices detected

**Symptoms:**
```
Error: Device has no input channels
No audio input devices available
```

**Solutions:**

1. **List available devices:**
```python
import sounddevice as sd
print(sd.query_devices())
```

2. **Check system audio settings:**
   - **Windows:** Settings → System → Sound → Input
   - **macOS:** System Preferences → Sound → Input
   - **Linux:** `arecord -l` or PulseAudio Volume Control

3. **Ensure microphone is not muted:**
   - Check physical mute button
   - Check system volume mixer
   - Verify app has microphone permissions

4. **Select specific device:**
```bash
python src/lfn_realtime_monitor.py --device 1
```

---

### Problem: Audio device access denied

**Symptoms:**
```
PortAudioError: Device unavailable
PermissionError: [Errno 13] Permission denied
```

**Solutions:**

**Windows:**
- Settings → Privacy → Microphone → Allow apps to access microphone

**macOS:**
- System Preferences → Security & Privacy → Privacy → Microphone
- Add Terminal/IDE to allowed apps

**Linux:**
```bash
# Add user to audio group
sudo usermod -a -G audio $USER
# Log out and back in
```

---

### Problem: Audio buffer overflow warnings

**Symptoms:**
```
[WARN] Audio buffer overflow detected
```

**Solutions:**

1. **Increase buffer size:** Reduce sample rate or increase blocksize
2. **Close other audio applications**
3. **Check CPU usage** - ensure system isn't overloaded
4. **Disable real-time effects** in audio drivers

---

## FFmpeg Issues

### Problem: `ffmpeg` not found

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
ffmpeg conversion failed
```

**Solutions:**

1. **Install FFmpeg:**

   **Windows (Chocolatey):**
   ```bash
   choco install ffmpeg
   ```

   **Windows (Manual):**
   - Download from: https://ffmpeg.org/download.html
   - Extract to C:\ffmpeg
   - Add to PATH: System Properties → Environment Variables → Path → Add `C:\ffmpeg\bin`

   **macOS:**
   ```bash
   brew install ffmpeg
   ```

   **Linux (Debian/Ubuntu):**
   ```bash
   sudo apt update && sudo apt install ffmpeg
   ```

2. **Verify installation:**
```bash
ffmpeg -version
```

3. **Specify FFmpeg path manually:**
```python
# In lfn_batch_file_analyzer.py, line 54:
command = ["C:\\path\\to\\ffmpeg.exe", "-y", "-i", input_path, ...]
```

---

### Problem: Audio conversion fails

**Symptoms:**
```
❌ ffmpeg conversion failed: CalledProcessError
```

**Solutions:**

1. **Check file format support:**
```bash
ffmpeg -formats | grep mp3
```

2. **Manually test conversion:**
```bash
ffmpeg -i input.mp3 -ar 44100 -ac 1 output.wav
```

3. **Check file corruption:**
   - Try opening file in media player
   - Verify file isn't 0 bytes

4. **Use WAV files directly** to bypass conversion

---

## GPU Acceleration Issues

### Problem: CuPy installation fails

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement cupy-cuda11x
```

**Solutions:**

1. **Check CUDA version:**
```bash
nvidia-smi
# Look for "CUDA Version: X.X"
```

2. **Install matching CuPy version:**
```bash
# For CUDA 11.x
pip install cupy-cuda11x

# For CUDA 12.x
pip install cupy-cuda12x
```

3. **If no NVIDIA GPU:** Skip GPU installation (toolkit works without it)

---

### Problem: GPU falls back to CPU despite CuPy installed

**Symptoms:**
```
⚠️ GPU computation failed, falling back to CPU
[CPU] Running on CPU
```

**Solutions:**

1. **Verify CUDA installation:**
```python
import cupy as cp
print(cp.cuda.runtime.runtimeGetVersion())
```

2. **Check GPU memory:**
```bash
nvidia-smi
# Look for available memory
```

3. **Close other GPU applications** (games, CUDA apps, browsers with hardware acceleration)

4. **Update NVIDIA drivers:**
   - Download latest from: https://www.nvidia.com/drivers

---

## Runtime Errors

### Problem: `MemoryError` during long recordings

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Solutions:**

1. **Use segmented recording:**
```python
from src.long_duration_recorder import LongDurationRecorder
recorder = LongDurationRecorder(segment_duration=1800)  # 30-min segments
recorder.record_long_session(8.0, "output")
```

2. **Reduce sample rate:**
```bash
python src/lfn_realtime_monitor.py --sample-rate 44100
```

3. **Close other applications** to free RAM

4. **Monitor memory usage:**
```python
import psutil
print(f"Available RAM: {psutil.virtual_memory().available / 1024**3:.2f} GB")
```

---

### Problem: Database locked errors

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**

1. **Close other instances** of the real-time monitor
2. **Delete lock file:**
```bash
rm lfn_live_log.db-journal
```
3. **Increase timeout:**
```python
# In lfn_realtime_monitor.py:
conn.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
```

---

### Problem: UTF-8 encoding errors on Windows

**Symptoms:**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Solutions:**

1. **Set environment variable:**
```bash
set PYTHONIOENCODING=utf-8
```

2. **Already handled in scripts** - UTF-8 encoding is forced at lines 9-15 in each script

3. **Use Windows Terminal** instead of cmd.exe

---

## Performance Issues

### Problem: Real-time monitoring is slow/laggy

**Symptoms:**
- Analysis takes >5 seconds per interval
- Spectrograms delayed
- Console output slow

**Solutions:**

1. **Enable GPU acceleration:**
```bash
python src/lfn_realtime_monitor.py --gpu
```

2. **Reduce spectrogram resolution:**
```python
# In lfn_realtime_monitor.py, line 62:
SPECTROGRAM_NPERSEG = 1024  # Was 2048
```

3. **Increase duration interval:**
```python
# In lfn_realtime_monitor.py, line 50:
DURATION_SEC = 10  # Was 5
```

4. **Disable trend plots** if not needed

5. **Close resource-heavy applications**

---

### Problem: Batch processing is very slow

**Symptoms:**
- Processing 100 files takes hours
- High CPU/memory usage

**Solutions:**

1. **Enable GPU acceleration:**
```bash
python src/lfn_batch_file_analyzer.py "path" --gpu
```

2. **Use block processing for large files:**
```bash
python src/lfn_batch_file_analyzer.py "path" --block-duration 30
```

3. **Disable trend tracking:**
```bash
python src/lfn_batch_file_analyzer.py "path" --no-trends
```

4. **Process in smaller batches**

---

## Output File Issues

### Problem: Spectrograms not generated

**Symptoms:**
- No PNG files in `spectrograms/` folder
- "Spectrogram: None" in results

**Solutions:**

1. **Check directory permissions:**
```bash
# Windows
icacls spectrograms
# Linux/Mac
ls -la spectrograms/
```

2. **Manually create directory:**
```bash
mkdir -p outputs/spectrograms
```

3. **Check disk space:**
```bash
df -h .  # Linux/Mac
dir     # Windows
```

4. **Verify matplotlib backend:**
```python
import matplotlib
print(matplotlib.get_backend())
# Should be 'Agg' for non-interactive
```

---

### Problem: Excel export fails

**Symptoms:**
```
⚠️ Excel export failed: ...
```

**Solutions:**

1. **Verify openpyxl installed:**
```bash
pip install --upgrade openpyxl
```

2. **Close Excel** if file is open

3. **Check write permissions** in output directory

4. **Use CSV instead:**
```bash
python src/lfn_batch_file_analyzer.py "path" --export-formats csv
```

---

### Problem: Output files have incorrect paths on Windows

**Symptoms:**
```
FileNotFoundError: [WinError 3] The system cannot find the path specified
```

**Solutions:**

1. **Use raw strings or forward slashes:**
```python
path = r"C:\Users\Name\Desktop\audio"  # Raw string
# Or
path = "C:/Users/Name/Desktop/audio"   # Forward slashes work on Windows
```

2. **Avoid paths >260 characters** (Windows limitation)
   - Use shorter folder names
   - Place toolkit closer to C:\

3. **Use pathlib:**
```python
from pathlib import Path
path = Path("C:/Users/Name/Desktop/audio")
```

---

## Platform-Specific Issues

### Windows: "Python not recognized" error

**Solutions:**

1. **Add Python to PATH:**
   - Reinstall Python with "Add to PATH" checked
   - Or manually: System Properties → Environment Variables → Path → Add Python directory

2. **Use Python launcher:**
```bash
py script.py  # Instead of python script.py
```

3. **Use full path:**
```bash
C:\Python39\python.exe script.py
```

---

### macOS: "command not found: python"

**Solutions:**

1. **Use python3:**
```bash
python3 src/lfn_batch_file_analyzer.py "path"
```

2. **Create alias:**
```bash
echo "alias python=python3" >> ~/.zshrc
source ~/.zshrc
```

3. **Install Python from python.org** (not just Xcode tools)

---

### Linux: PortAudio errors

**Symptoms:**
```
OSError: PortAudio library not found
ImportError: libportaudio.so.2: cannot open shared object file
```

**Solutions:**

1. **Install PortAudio:**
```bash
# Debian/Ubuntu
sudo apt install portaudio19-dev python3-pyaudio

# Fedora
sudo dnf install portaudio-devel

# Arch
sudo pacman -S portaudio
```

2. **Reinstall sounddevice:**
```bash
pip uninstall sounddevice
pip install --no-cache-dir sounddevice
```

---

## Still Having Issues?

If your problem isn't covered here:

1. **Run the pre-flight check:**
```bash
python preflight_check.py
```

2. **Run the test suite:**
```bash
python run_tests.py
```

3. **Check logs:** Look for error messages and stack traces

4. **Gather system information:**
```bash
python --version
pip list
# GPU info (if applicable):
nvidia-smi
```

5. **Create an issue on GitHub** with:
   - Full error message and traceback
   - System information (OS, Python version)
   - Steps to reproduce
   - Output of `preflight_check.py`

---

## Quick Diagnostics

Run these commands to diagnose common issues:

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check FFmpeg
ffmpeg -version

# Check audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Check GPU
python -c "import cupy as cp; print(cp.cuda.runtime.runtimeGetVersion())"

# Run full diagnostic
python preflight_check.py
```

---

## Emergency Fixes

### Complete reinstall:

```bash
# 1. Remove virtual environment (if using)
rm -rf venv/  # Linux/Mac
rmdir /s venv  # Windows

# 2. Clear pip cache
pip cache purge

# 3. Reinstall everything
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verify installation
python preflight_check.py
```

---

## Performance Tuning Checklist

- [ ] GPU acceleration enabled (`--gpu` flag)
- [ ] FFmpeg installed and in PATH
- [ ] Sufficient RAM available (4GB+ free)
- [ ] SSD storage (faster than HDD)
- [ ] Close unnecessary applications
- [ ] Use appropriate sample rates (44100 or 48000 Hz)
- [ ] Disable antivirus real-time scanning for output folders
- [ ] Use batch processing for multiple files
- [ ] Enable segmented recording for long sessions

---

**Last Updated:** December 10, 2025
**Toolkit Version:** 2.0.0
