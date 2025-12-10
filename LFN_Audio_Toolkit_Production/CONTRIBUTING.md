# Contributing to LFN Audio Toolkit

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs
1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/lfn-audio-toolkit/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version)
   - Error messages/logs

### Suggesting Features
1. Check existing [Feature Requests](https://github.com/yourusername/lfn-audio-toolkit/issues?q=label%3Aenhancement)
2. Create a new issue with:
   - Clear use case description
   - Expected benefits
   - Proposed implementation (optional)

### Code Contributions

#### Setup Development Environment
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/lfn-audio-toolkit.git
cd lfn-audio-toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

#### Making Changes
1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards:
   - Follow PEP 8 style guide
   - Add docstrings to functions and classes
   - Include type hints where appropriate
   - Write clear, descriptive commit messages

3. Test your changes:
   ```bash
   python src/lfn_health_assessment.py
   # Run relevant analysis scripts to verify
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a Pull Request:
   - Provide clear description of changes
   - Reference any related issues
   - Include screenshots if UI changes
   - Ensure all tests pass

## 📝 Coding Standards

### Python Style
- Follow PEP 8
- Use meaningful variable names
- Maximum line length: 100 characters
- Use f-strings for formatting

### Documentation
- Add docstrings to all functions:
  ```python
  def analyze_audio(file_path: str, use_gpu: bool = False) -> dict:
      """
      Analyze audio file for LFN and ultrasonic content.
      
      Args:
          file_path: Path to audio file
          use_gpu: Enable GPU acceleration
          
      Returns:
          Dictionary with analysis results
          
      Raises:
          FileNotFoundError: If audio file doesn't exist
      """
  ```

### Commit Messages
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line: brief summary (50 chars or less)
- Blank line, then detailed description if needed

Examples:
```
Add GPU acceleration support for batch processing

Implement CuPy-based FFT computation to speed up batch
analysis by 10x on CUDA-enabled systems.
```

## 🧪 Testing

### Manual Testing
- Test on multiple audio file formats (WAV, FLAC, MP3)
- Verify output files are generated correctly
- Check error handling with invalid inputs

### Performance Testing
- Profile memory usage with large files
- Benchmark processing speed improvements
- Test GPU vs CPU performance

## 📚 Documentation

When adding new features:
- Update README.md
- Add examples to docs/
- Update command-line help text
- Include usage examples

## 🐛 Debugging

### Useful Debug Commands
```bash
# Check audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Test GPU availability
python -c "import cupy; print(cupy.cuda.runtime.runtimeGetVersion())"

# Verify dependencies
pip list | grep -E "soundfile|numpy|scipy|pandas"
```

## 📋 Pull Request Checklist

Before submitting:
- [ ] Code follows style guidelines
- [ ] Added/updated documentation
- [ ] Added/updated tests
- [ ] Tested on multiple scenarios
- [ ] No breaking changes (or documented)
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

## 🏆 Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Credited in documentation

## ❓ Questions

- Open a [Discussion](https://github.com/yourusername/lfn-audio-toolkit/discussions)
- Email: support@example.com

## 📜 Code of Conduct

Be respectful and inclusive. We're all here to learn and improve the project together.

Thank you for contributing! 🎉
