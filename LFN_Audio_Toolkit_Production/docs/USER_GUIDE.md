# User Guide - LFN Audio Toolkit

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Introduction

The LFN Audio Toolkit is designed for professional analysis of Low Frequency Noise (LFN) and ultrasonic frequencies in audio recordings. This guide will help you get started and make the most of the toolkit's features.

## Installation

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Python**: Version 3.8 or higher
- **RAM**: Minimum 4GB (8GB+ recommended for large files)
- **Disk Space**: 500MB for installation + space for output files
- **Audio Hardware**: Microphone or audio interface (for real-time monitoring)

### Step-by-Step Installation

1. **Download the toolkit**
   ```bash
   git clone https://github.com/yourusername/lfn-audio-toolkit.git
   cd lfn-audio-toolkit
   ```

2. **Run setup**
   ```bash
   python setup.py
   ```
   
   This will:
   - Check Python version compatibility
   - Install required dependencies
   - Create output directories
   - Verify installation
   - Check for GPU support (optional)

3. **Verify installation**
   ```bash
   python src/lfn_health_assessment.py
   ```

## Basic Usage

### 1. Batch File Analysis

Analyze one or more audio files:

```bash
# Single file
python src/lfn_batch_file_analyzer.py path/to/audio.wav

# Directory of files
python src/lfn_batch_file_analyzer.py path/to/audio/folder

# With GPU acceleration
python src/lfn_batch_file_analyzer.py path/to/audio/folder --gpu
```

**Output Files:**
- `lfn_analysis_results.csv` - Tabular results
- `lfn_analysis_results.json` - Structured data with metadata
- `spectrograms/` - Visual representations

### 2. Real-Time Monitoring

Monitor live audio input:

```bash
# Default settings (10-second recordings)
python src/lfn_realtime_monitor.py

# Custom duration
python src/lfn_realtime_monitor.py --duration 30

# Specific audio device
python src/lfn_realtime_monitor.py --device-id 1
```

**To find your device ID:**
```python
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### 3. Long Duration Recording

Record audio for extended periods:

```bash
python src/long_duration_recorder.py
```

Follow the prompts to configure:
- Duration (in hours)
- Audio device
- Output directory
- Segment duration

## Advanced Features

### GPU Acceleration

Enable GPU processing for 10x speedup:

1. **Install CuPy**
   ```bash
   # For CUDA 11.x
   pip install cupy-cuda11x
   
   # For CUDA 12.x
   pip install cupy-cuda12x
   ```

2. **Use --gpu flag**
   ```bash
   python src/lfn_batch_file_analyzer.py path/to/audio --gpu
   ```

### Export Formats

Choose output formats:

```bash
# Multiple formats
python src/lfn_batch_file_analyzer.py path/to/audio --export-formats csv json excel

# CSV only (default)
python src/lfn_batch_file_analyzer.py path/to/audio --export-formats csv
```

### Trend Analysis

Generate time-series plots:

```bash
python src/lfn_batch_file_analyzer.py path/to/audio --trends
```

This creates plots showing frequency levels over time.

### Block Processing

For very large files, process in chunks:

```bash
# Process in 30-second blocks
python src/lfn_batch_file_analyzer.py path/to/largefile.wav --block-duration 30
```

## Understanding Results

### CSV Output

| Column | Description |
|--------|-------------|
| filename | Audio file name |
| duration | Length in seconds |
| sample_rate | Audio sample rate (Hz) |
| lfn_peak_1_freq | Strongest LFN frequency (Hz) |
| lfn_peak_1_db | Strength of LFN peak (dB) |
| ultrasonic_peak_1_freq | Strongest ultrasonic frequency (Hz) |
| ultrasonic_peak_1_db | Strength of ultrasonic peak (dB) |
| lfn_alert | True if LFN exceeds threshold |
| ultrasonic_alert | True if ultrasonic exceeds threshold |

### Alert Thresholds

**Default thresholds:**
- **LFN Alert**: -20.0 dB (20-100 Hz range)
- **Ultrasonic Alert**: -30.0 dB (20-24 kHz range)

Files exceeding these levels will be flagged for review.

### Interpreting dB Values

- **-20 dB**: Significant signal, likely audible/detectable
- **-30 dB**: Moderate signal
- **-40 dB**: Weak signal
- **-60 dB or lower**: Very weak or noise floor

## Best Practices

### Recording Quality

1. **Use quality microphones**: EMM-6 or similar measurement microphones
2. **Avoid clipping**: Monitor input levels, keep peaks below 0 dB
3. **Minimize ambient noise**: Record in quiet environments
4. **Use proper sample rate**: 48 kHz recommended (44.1 kHz minimum)

### File Management

1. **Organize by date**: Use date-based folder structure
2. **Consistent naming**: Use descriptive, consistent filenames
3. **Backup important data**: Keep copies of critical recordings
4. **Clean up regularly**: Delete unnecessary files to save space

### Performance Tips

1. **GPU acceleration**: Use for batch processing of many files
2. **Block processing**: Enable for files over 1 hour
3. **Close other programs**: Free up system resources
4. **Use SSD storage**: Faster read/write for large files

## Troubleshooting

### Common Issues

**"No audio devices found"**
- Check microphone is connected
- Verify device permissions (especially macOS)
- Try different USB port

**"Module not found" errors**
- Run `pip install -r requirements.txt` again
- Check Python version is 3.8+

**Poor quality spectrograms**
- Check audio file quality
- Ensure proper sample rate (44.1+ kHz)
- Avoid compressed formats (MP3) when possible

**Out of memory errors**
- Use --block-duration for large files
- Close other applications
- Reduce file size or split into segments

### Getting Help

- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Search [GitHub Issues](https://github.com/yourusername/lfn-audio-toolkit/issues)
- Open a new issue with details

## Next Steps

- Explore [API Reference](API_REFERENCE.md) for custom scripts
- Read [FAQ](FAQ.md) for common questions
- Check [Contributing Guide](../CONTRIBUTING.md) to help improve the toolkit

---

**Last Updated**: December 2025  
**Version**: 2.0.0
