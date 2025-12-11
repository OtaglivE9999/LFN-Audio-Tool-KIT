# Changelog

All notable changes to the LFN Audio Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-01-13

### Added - VAD Research Integration
- **Vibroacoustic Disease (VAD) research** from Dr. Mariana Alves-Pereira integrated into health assessment
- Body resonance frequency bands based on peer-reviewed research:
  - Cardiac (1-8 Hz)
  - Vestibular (8-12 Hz)
  - Respiratory (12-20 Hz)
  - Abdominal (20-40 Hz)
  - Neurological (40-100 Hz)
- VAD clinical staging system (Stage I, II, III) based on exposure duration
- Updated risk thresholds using Linear/C-weighted measurements (not A-weighted)
- Warning about A-weighting underestimating ILFN exposure by 20-50 dB
- Scientific references to Alves-Pereira & Castelo Branco publications (1999, 2004, 2007)

### Changed
- `lfn_health_assessment.py` completely rewritten with VAD-specific health impacts
- Risk levels now aligned with occupational exposure research (Critical: 90dB, High: 75dB)
- Medical recommendations updated with VAD-specific guidance
- Health report now includes VAD stage assessment

### Documentation
- Added comprehensive VAD research documentation in health assessment module
- Updated medical recommendations with specialist referral guidance

## [2.0.0] - 2025-12-10

### Added
- Complete production-ready package structure
- Comprehensive README with installation and usage instructions
- Automated setup script for easy installation
- GitHub-ready repository structure
- Professional documentation and contributing guidelines
- MIT License
- .gitignore for clean repository
- Output directory structure with gitkeep files

### Changed
- Reorganized project structure for better portability
- Moved core scripts to `src/` directory
- Updated documentation for clarity and completeness

### Fixed
- Dependency management with comprehensive requirements.txt
- Platform compatibility improvements

## [1.x.x] - Previous Versions

### Features
- Multi-peak detection (top 10 peaks per range)
- LFN analysis (20-100 Hz)
- Ultrasonic analysis (20-24 kHz)
- Real-time monitoring capabilities
- Batch file processing
- Long duration recording
- GPU acceleration support
- Multiple export formats (CSV, JSON, Excel)
- High-quality spectrograms
- Time-series trend analysis
- Alert system with configurable thresholds
- Memory optimization
- Health assessment tools

---

## Release Notes

### Version 2.0.0 - Production Release

This release marks the transition to a production-ready, portable toolkit suitable for:
- GitHub repository hosting
- Easy deployment on multiple systems
- Professional audio analysis workflows
- Research and development environments

#### Migration Notes
If upgrading from previous versions:
1. Run `python setup.py` to verify installation
2. Check `config/` directory for new settings
3. Update any custom scripts to use new `src/` path structure

#### Known Issues
- None at this time

#### Future Plans
- Web-based dashboard for remote monitoring
- Machine learning-based anomaly detection
- Multi-channel audio support
- Cloud storage integration
- Mobile app companion

---

For detailed changes and technical updates, see the commit history on GitHub.
