# LFN Audio Analysis Toolkit

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Professional toolkit for detecting and analyzing Low Frequency Noise (LFN) and ultrasonic frequencies in audio recordings.

## 🎯 Features

### Core Capabilities
- **Multi-Peak Detection**: Analyzes top 10 peaks per frequency range
- **LFN Analysis**: 20-100 Hz range detection and measurement
- **Ultrasonic Analysis**: 20-24 kHz range detection and measurement
- **Real-Time Monitoring**: Live audio capture and analysis
- **Batch Processing**: Analyze multiple audio files in one session
- **Long Duration Recording**: Extended recording sessions with automatic file management

### Performance
- **GPU Acceleration**: Optional CUDA support via CuPy (10x speedup)
- **Memory Optimized**: Efficient processing of large audio files
- **Vectorized Operations**: Fast NumPy-based computations

### Output Formats
- **CSV**: Spreadsheet-compatible results
- **JSON**: Structured data with metadata
- **Excel**: Multi-sheet workbooks with statistics
- **Spectrograms**: High-quality visualization (150 DPI PNG)
- **Trend Plots**: Time-series analysis graphs

## 📋 Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- FFmpeg (for batch audio file conversion)
- Audio input device (for real-time monitoring)
- Optional: CUDA-capable GPU for acceleration

## 🚀 Quick Start

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/lfn-audio-toolkit.git
cd lfn-audio-toolkit
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Optional: Install GPU acceleration**
```bash
# For CUDA 11.x
pip install cupy-cuda11x

# For CUDA 12.x
pip install cupy-cuda12x
```

4. **Install FFmpeg (Required for Batch Analyzer)**

FFmpeg is required to convert various audio formats (MP3, MP4, FLAC, etc.) to WAV for analysis.

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
# Extract and add to PATH
```

**macOS:**
```bash
# Using Homebrew
brew install ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version
```

> **Note**: FFmpeg is only required for the Batch File Analyzer when processing non-WAV audio files. Real-time monitoring and long duration recording work without FFmpeg.

5. **Run Pre-flight Check (Recommended)**
```bash
python preflight_check.py
```

This will verify:

- Python version compatibility
- All required packages are installed
- FFmpeg availability
- Audio device configuration
- System resources and permissions

### Basic Usage

#### Batch Analysis
Analyze audio files in a directory:
```bash
python src/lfn_batch_file_analyzer.py "path/to/audio/files"
```

With options:
```bash
# Enable GPU acceleration
python src/lfn_batch_file_analyzer.py "path/to/audio" --gpu

# Export to multiple formats
python src/lfn_batch_file_analyzer.py "path/to/audio" --export-formats csv json excel

# Generate trend plots
python src/lfn_batch_file_analyzer.py "path/to/audio" --trends
```

#### Real-Time Monitoring
Monitor live audio input:
```bash
python src/lfn_realtime_monitor.py
```

With options:
```bash
# Use specific audio device
python src/lfn_realtime_monitor.py --device-id 1

# Set custom duration (seconds)
python src/lfn_realtime_monitor.py --duration 30

# Enable GPU acceleration
python src/lfn_realtime_monitor.py --gpu
```

#### Long Duration Recording
Record audio for extended periods:
```bash
python src/long_duration_recorder.py
```

## 📊 Output Files

### Batch Analysis Results
- `lfn_analysis_results.csv` - Detailed analysis data
- `lfn_analysis_results.json` - Structured results with metadata
- `lfn_analysis_results.xlsx` - Excel workbook with multiple sheets
- `spectrograms/` - Folder containing spectrogram images
- `trends/` - Folder containing time-series plots

### Real-Time Monitoring
- `outputs/spectrograms/YYYY-MM-DD/` - Daily spectrogram archive
- `alerts_log.json` - Alert history and threshold violations

## ⚙️ Configuration

### Alert Thresholds
Edit the threshold values in the source files:

**LFN Alert Threshold**: -20.0 dB (20-100 Hz)
**Ultrasonic Alert Threshold**: -30.0 dB (20-24 kHz)

### Custom Settings
Modify settings in `config/settings.json` (create if needed):
```json
{
  "lfn_threshold_db": -20.0,
  "ultrasonic_threshold_db": -30.0,
  "sample_rate": 48000,
  "block_duration": 10.0
}
```

## 📖 Documentation

- [User Guide](docs/USER_GUIDE.md) - Detailed usage instructions
- [API Reference](docs/API_REFERENCE.md) - Developer documentation
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [FAQ](docs/FAQ.md) - Frequently asked questions

## 🔧 Command-Line Options

### lfn_batch_file_analyzer.py
```
Arguments:
  directory              Path to audio directory or single file

Options:
  --block-duration SECS  Process in chunks (default: full file)
  --gpu                  Enable GPU acceleration
  --export-formats F...  Output formats: csv, json, excel
  --trends               Generate time-series plots
  --no-trends            Skip trend generation
```

### lfn_realtime_monitor.py
```
Options:
  --gpu                  Enable GPU acceleration
  --device-id ID         Audio input device ID
  --duration SECS        Recording duration
  --output-dir PATH      Custom output directory
```

### long_duration_recorder.py
```
Options:
  --duration HOURS       Recording duration in hours
  --device-id ID         Audio input device ID
  --output-dir PATH      Output directory
  --segment-duration MIN Segment duration in minutes
```

## 🐛 Health Check

Run system health assessment:
```bash
python src/lfn_health_assessment.py
```

This checks:
- Python environment and dependencies
- Audio device availability
- GPU acceleration status
- Disk space and permissions
- Configuration validity

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/lfn-audio-toolkit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/lfn-audio-toolkit/discussions)
- **Email**: support@example.com

## 🙏 Acknowledgments

- Built with Python, NumPy, SciPy, and Matplotlib
- GPU acceleration powered by CuPy
- Audio processing with sounddevice and soundfile

## 📈 Roadmap

- [ ] Web-based dashboard for remote monitoring
- [ ] Machine learning-based anomaly detection
- [ ] Multi-channel audio support
- [ ] Cloud storage integration
- [ ] Mobile app companion

---

**Version**: 2.0.0  
**Last Updated**: December 2025  
**Status**: Production Ready
