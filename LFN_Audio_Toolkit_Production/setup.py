#!/usr/bin/env python3
"""
LFN Audio Toolkit - Setup and Installation Script
Automated installation and configuration for the LFN Audio Analysis Toolkit
"""

import sys
import subprocess
import platform
import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_python_version():
    """Check if Python version meets requirements"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Python 3.8 or higher is required!")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print("✅ Python version check passed")
    return True

def install_dependencies():
    """Install required Python packages"""
    print_header("Installing Dependencies")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ ERROR: requirements.txt not found!")
        return False
    
    print("Installing packages from requirements.txt...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("\n✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to install dependencies: {e}")
        return False

def check_gpu_support():
    """Check if GPU acceleration is available"""
    print_header("Checking GPU Support")
    
    try:
        import cupy as cp
        print("✅ CuPy is installed - GPU acceleration available")
        print(f"   CUDA version: {cp.cuda.runtime.runtimeGetVersion()}")
        return True
    except ImportError:
        print("ℹ️  CuPy not installed - GPU acceleration not available")
        print("   To enable GPU support, install CuPy:")
        print("   pip install cupy-cuda11x  (for CUDA 11.x)")
        print("   pip install cupy-cuda12x  (for CUDA 12.x)")
        return False

def check_audio_devices():
    """Check available audio input devices"""
    print_header("Checking Audio Devices")
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        
        print("Available audio input devices:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  [{i}] {device['name']} - {device['max_input_channels']} channels")
        
        print("\n✅ Audio devices detected")
        return True
    except Exception as e:
        print(f"⚠️  Warning: Could not query audio devices: {e}")
        return False

def create_output_directories():
    """Create necessary output directories"""
    print_header("Creating Output Directories")
    
    base_dir = Path(__file__).parent
    directories = [
        base_dir / "outputs",
        base_dir / "outputs" / "spectrograms",
        base_dir / "outputs" / "trends",
        base_dir / "outputs" / "recordings",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory.name}/")
    
    return True

def verify_installation():
    """Verify that all components are properly installed"""
    print_header("Verifying Installation")
    
    required_modules = [
        "soundfile",
        "sounddevice",
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
        "openpyxl"
    ]
    
    all_ok = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - MISSING")
            all_ok = False
    
    return all_ok

def print_next_steps():
    """Print instructions for next steps"""
    print_header("Installation Complete!")
    
    print("🎉 LFN Audio Toolkit is ready to use!\n")
    print("Next steps:")
    print("\n1. Batch Analysis:")
    print("   python src/lfn_batch_file_analyzer.py <audio_directory>")
    print("\n2. Real-Time Monitoring:")
    print("   python src/lfn_realtime_monitor.py")
    print("\n3. Long Duration Recording:")
    print("   python src/long_duration_recorder.py")
    print("\n4. Health Check:")
    print("   python src/lfn_health_assessment.py")
    print("\nFor more information, see README.md")
    print("="*60 + "\n")

def main():
    """Main setup routine"""
    print_header("LFN Audio Toolkit - Installation")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️  Warning: Some dependencies failed to install")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Check GPU support (optional)
    check_gpu_support()
    
    # Check audio devices
    check_audio_devices()
    
    # Create output directories
    create_output_directories()
    
    # Verify installation
    if not verify_installation():
        print("\n⚠️  Warning: Some required modules are missing")
        print("Please check the errors above and reinstall dependencies")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
