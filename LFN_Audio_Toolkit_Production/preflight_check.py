#!/usr/bin/env python3
"""
LFN Audio Toolkit - Pre-flight Checklist
=========================================
Comprehensive system readiness verification before running the toolkit.

Run this script to verify:
- Python version compatibility
- Required package installations
- FFmpeg availability
- Audio device configuration
- GPU support (optional)
- File system permissions
- Disk space availability
"""

import sys
import subprocess
import platform
import os
import shutil
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @staticmethod
    def disable():
        """Disable colors for Windows compatibility"""
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.RED = ''
        Colors.BLUE = ''
        Colors.BOLD = ''
        Colors.END = ''

# Disable colors on Windows unless ANSI is supported
if sys.platform == 'win32':
    try:
        import colorama
        colorama.init()
    except ImportError:
        Colors.disable()

def print_section(title):
    """Print formatted section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_check(name, status, message="", critical=True):
    """Print check result with color coding"""
    if status:
        icon = f"{Colors.GREEN}✓{Colors.END}"
        status_text = f"{Colors.GREEN}PASS{Colors.END}"
    else:
        icon = f"{Colors.RED}✗{Colors.END}" if critical else f"{Colors.YELLOW}⚠{Colors.END}"
        status_text = f"{Colors.RED}FAIL{Colors.END}" if critical else f"{Colors.YELLOW}WARN{Colors.END}"

    print(f"{icon} {name:.<50} {status_text}")
    if message:
        indent = "  "
        print(f"{indent}{Colors.YELLOW if not status else ''}{message}{Colors.END}")

def check_python_version():
    """Check Python version meets requirements"""
    print_section("Python Environment")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    meets_requirement = version.major >= 3 and version.minor >= 8

    print(f"Python Version: {version_str}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}\n")

    print_check(
        "Python 3.8+ Required",
        meets_requirement,
        "Current: " + version_str + (" (Upgrade required!)" if not meets_requirement else ""),
        critical=True
    )

    return meets_requirement

def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name

    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

def check_required_packages():
    """Check all required Python packages"""
    print_section("Required Python Packages")

    packages = {
        'soundfile': 'soundfile',
        'sounddevice': 'sounddevice',
        'numpy': 'numpy',
        'scipy': 'scipy',
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'openpyxl': 'openpyxl'
    }

    all_installed = True
    missing_packages = []

    for package, import_name in packages.items():
        installed = check_package(package, import_name)
        print_check(package, installed, critical=True)
        if not installed:
            all_installed = False
            missing_packages.append(package)

    if not all_installed:
        print(f"\n{Colors.RED}Missing packages:{Colors.END}")
        print(f"  Run: pip install {' '.join(missing_packages)}")
        print(f"  Or run: python setup.py")

    return all_installed

def check_optional_packages():
    """Check optional packages (GPU support)"""
    print_section("Optional Packages (GPU Acceleration)")

    cupy_installed = check_package('cupy', 'cupy')
    print_check(
        "CuPy (GPU Acceleration)",
        cupy_installed,
        "Install with: pip install cupy-cuda11x or cupy-cuda12x" if not cupy_installed else "GPU acceleration available!",
        critical=False
    )

    if cupy_installed:
        try:
            import cupy as cp
            cuda_version = cp.cuda.runtime.runtimeGetVersion()
            print(f"  CUDA Version: {cuda_version}")
        except:
            pass

    return cupy_installed

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print_section("External Dependencies")

    ffmpeg_path = shutil.which('ffmpeg')
    ffmpeg_available = ffmpeg_path is not None

    message = ""
    if not ffmpeg_available:
        if platform.system() == 'Windows':
            message = "Install: choco install ffmpeg (or download from ffmpeg.org)"
        elif platform.system() == 'Darwin':
            message = "Install: brew install ffmpeg"
        else:
            message = "Install: sudo apt install ffmpeg (or equivalent)"
    else:
        message = f"Found at: {ffmpeg_path}"
        # Try to get version
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                message += f"\n  {version_line}"
        except:
            pass

    print_check(
        "FFmpeg (Audio Conversion)",
        ffmpeg_available,
        message,
        critical=False  # Not critical for all tools
    )

    return ffmpeg_available

def check_audio_devices():
    """Check available audio input devices"""
    print_section("Audio Devices")

    try:
        import sounddevice as sd
        devices = sd.query_devices()

        input_devices = [d for d in devices if d['max_input_channels'] > 0]

        has_input = len(input_devices) > 0

        print_check(
            "Audio Input Devices Available",
            has_input,
            f"Found {len(input_devices)} input device(s)" if has_input else "No input devices detected!",
            critical=False  # Not critical for batch analysis
        )

        if has_input:
            print("\n  Available Input Devices:")
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    print(f"    [{i}] {device['name']} ({device['max_input_channels']} channels)")

        return has_input

    except Exception as e:
        print_check(
            "Audio Device Check",
            False,
            f"Error: {str(e)}",
            critical=False
        )
        return False

def check_disk_space():
    """Check available disk space"""
    print_section("System Resources")

    try:
        stat = shutil.disk_usage(Path.cwd())
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_gb = stat.used / (1024**3)

        sufficient = free_gb >= 1.0  # At least 1GB free

        print(f"Disk Space:")
        print(f"  Total: {total_gb:.2f} GB")
        print(f"  Used:  {used_gb:.2f} GB")
        print(f"  Free:  {free_gb:.2f} GB\n")

        print_check(
            "Sufficient Disk Space (≥1GB)",
            sufficient,
            f"Only {free_gb:.2f} GB available" if not sufficient else f"{free_gb:.2f} GB available",
            critical=True
        )

        return sufficient

    except Exception as e:
        print_check(
            "Disk Space Check",
            False,
            f"Error: {str(e)}",
            critical=False
        )
        return False

def check_output_directories():
    """Check if output directories exist and are writable"""
    print_section("File System Permissions")

    base_dir = Path(__file__).parent
    directories = {
        'outputs': base_dir / 'outputs',
        'spectrograms': base_dir / 'outputs' / 'spectrograms',
        'trends': base_dir / 'outputs' / 'trends',
        'recordings': base_dir / 'outputs' / 'recordings'
    }

    all_ok = True

    for name, path in directories.items():
        exists = path.exists()
        writable = False

        if exists:
            writable = os.access(path, os.W_OK)
        else:
            # Try to create it
            try:
                path.mkdir(parents=True, exist_ok=True)
                writable = True
                exists = True
            except:
                pass

        status = exists and writable
        message = ""
        if not exists:
            message = f"Does not exist: {path}"
        elif not writable:
            message = f"Not writable: {path}"

        print_check(
            f"Directory: {name}",
            status,
            message,
            critical=True
        )

        if not status:
            all_ok = False

    return all_ok

def check_module_imports():
    """Try to import all toolkit modules"""
    print_section("Toolkit Module Integrity")

    base_dir = Path(__file__).parent
    sys.path.insert(0, str(base_dir))

    modules = {
        'Batch File Analyzer': 'src.lfn_batch_file_analyzer',
        'Real-time Monitor': 'src.lfn_realtime_monitor',
        'Long Duration Recorder': 'src.long_duration_recorder',
        'Health Assessment': 'src.lfn_health_assessment'
    }

    all_ok = True

    for name, module_path in modules.items():
        try:
            __import__(module_path)
            print_check(name, True, critical=True)
        except ImportError as e:
            print_check(name, False, f"Import error: {str(e)}", critical=True)
            all_ok = False
        except Exception as e:
            print_check(name, False, f"Error: {str(e)}", critical=True)
            all_ok = False

    return all_ok

def generate_report(checks):
    """Generate final summary report"""
    print_section("Pre-flight Check Summary")

    critical_checks = {
        'Python Version': checks.get('python_version', False),
        'Required Packages': checks.get('required_packages', False),
        'Disk Space': checks.get('disk_space', False),
        'Output Directories': checks.get('output_directories', False),
        'Module Integrity': checks.get('module_integrity', False)
    }

    optional_checks = {
        'FFmpeg': checks.get('ffmpeg', False),
        'GPU Support': checks.get('gpu_support', False),
        'Audio Devices': checks.get('audio_devices', False)
    }

    critical_passed = all(critical_checks.values())

    print(f"{Colors.BOLD}Critical Requirements:{Colors.END}")
    for name, status in critical_checks.items():
        icon = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
        print(f"  {icon} {name}")

    print(f"\n{Colors.BOLD}Optional Features:{Colors.END}")
    for name, status in optional_checks.items():
        icon = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.YELLOW}○{Colors.END}"
        print(f"  {icon} {name}")

    print("\n" + "="*70)

    if critical_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ SYSTEM READY{Colors.END}")
        print(f"{Colors.GREEN}All critical checks passed! The toolkit is ready to use.{Colors.END}")

        if not all(optional_checks.values()):
            print(f"\n{Colors.YELLOW}Note: Some optional features are unavailable but the toolkit will work.{Colors.END}")

        print("\n" + Colors.BOLD + "Quick Start:" + Colors.END)
        print("  1. Batch Analysis:  python src/lfn_batch_file_analyzer.py <directory>")
        print("  2. Real-time:       python src/lfn_realtime_monitor.py")
        print("  3. Long Recording:  See long_duration_recorder.py")
        print("  4. Health Report:   python src/lfn_health_assessment.py --auto-find")

        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ SYSTEM NOT READY{Colors.END}")
        print(f"{Colors.RED}Critical checks failed. Please address the issues above.{Colors.END}")

        print("\n" + Colors.BOLD + "Recommended Actions:" + Colors.END)
        if not checks.get('python_version'):
            print("  • Upgrade Python to version 3.8 or higher")
        if not checks.get('required_packages'):
            print("  • Run: python setup.py (to install all dependencies)")
        if not checks.get('output_directories'):
            print("  • Ensure write permissions in the toolkit directory")
        if not checks.get('module_integrity'):
            print("  • Verify all source files are present in src/ directory")

        return False

def main():
    """Main pre-flight check routine"""
    print(f"\n{Colors.BOLD}LFN Audio Toolkit - Pre-flight Check{Colors.END}")
    print(f"Version 2.0.0 - System Readiness Verification")
    print(f"Running on: {platform.system()} {platform.release()}")

    checks = {}

    # Run all checks
    checks['python_version'] = check_python_version()
    checks['required_packages'] = check_required_packages()
    checks['gpu_support'] = check_optional_packages()
    checks['ffmpeg'] = check_ffmpeg()
    checks['audio_devices'] = check_audio_devices()
    checks['disk_space'] = check_disk_space()
    checks['output_directories'] = check_output_directories()
    checks['module_integrity'] = check_module_imports()

    # Generate final report
    system_ready = generate_report(checks)

    print()

    # Exit with appropriate code
    sys.exit(0 if system_ready else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Pre-flight check cancelled by user.{Colors.END}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n{Colors.RED}Unexpected error during pre-flight check:{Colors.END}")
        print(f"{Colors.RED}{str(e)}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
