#!/usr/bin/env python3
"""
LFN Audio Toolkit - Test Runner
================================
Automated testing script to verify all toolkit functionality.

This script performs:
1. Syntax validation of all Python modules
2. Import tests for all dependencies
3. Module initialization tests
4. Basic functionality tests (without requiring audio files)
5. Configuration validation
"""

import sys
import os
import importlib
from pathlib import Path
import traceback

# Color output for better readability
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_section(title):
    """Print formatted section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def test_module_syntax(module_path):
    """Test Python module syntax by compiling it"""
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, module_path, 'exec')
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def test_module_import(module_name):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, f"Import error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def run_syntax_tests():
    """Test syntax of all Python files"""
    print_section("Syntax Validation Tests")

    base_dir = Path(__file__).parent
    python_files = {
        'setup.py': base_dir / 'setup.py',
        'preflight_check.py': base_dir / 'preflight_check.py',
        'src/__init__.py': base_dir / 'src' / '__init__.py',
        'lfn_batch_file_analyzer.py': base_dir / 'src' / 'lfn_batch_file_analyzer.py',
        'lfn_realtime_monitor.py': base_dir / 'src' / 'lfn_realtime_monitor.py',
        'long_duration_recorder.py': base_dir / 'src' / 'long_duration_recorder.py',
        'lfn_health_assessment.py': base_dir / 'src' / 'lfn_health_assessment.py',
    }

    results = {}
    all_passed = True

    for name, path in python_files.items():
        if not path.exists():
            print(f"{Colors.RED}✗{Colors.END} {name:.<50} MISSING")
            results[name] = False
            all_passed = False
            continue

        passed, error = test_module_syntax(path)
        if passed:
            print(f"{Colors.GREEN}✓{Colors.END} {name:.<50} OK")
        else:
            print(f"{Colors.RED}✗{Colors.END} {name:.<50} FAIL")
            print(f"  {Colors.YELLOW}{error}{Colors.END}")
            all_passed = False

        results[name] = passed

    return all_passed, results

def run_import_tests():
    """Test imports of all required packages"""
    print_section("Dependency Import Tests")

    # Add src to path for imports
    base_dir = Path(__file__).parent
    sys.path.insert(0, str(base_dir))

    packages = {
        'Core Dependencies': [
            ('soundfile', 'soundfile'),
            ('sounddevice', 'sounddevice'),
            ('numpy', 'numpy'),
            ('scipy', 'scipy'),
            ('pandas', 'pandas'),
            ('matplotlib', 'matplotlib'),
            ('openpyxl', 'openpyxl'),
        ],
        'Optional Dependencies': [
            ('cupy (GPU)', 'cupy'),
        ],
        'Toolkit Modules': [
            ('Batch Analyzer', 'src.lfn_batch_file_analyzer'),
            ('Real-time Monitor', 'src.lfn_realtime_monitor'),
            ('Long Duration Recorder', 'src.long_duration_recorder'),
            ('Health Assessment', 'src.lfn_health_assessment'),
        ]
    }

    all_passed = True
    results = {}

    for category, package_list in packages.items():
        print(f"\n{Colors.BOLD}{category}:{Colors.END}")

        for name, import_name in package_list:
            passed, error = test_module_import(import_name)

            if passed:
                print(f"{Colors.GREEN}✓{Colors.END} {name:.<50} OK")
            elif 'Optional' in category:
                print(f"{Colors.YELLOW}○{Colors.END} {name:.<50} NOT INSTALLED (optional)")
            else:
                print(f"{Colors.RED}✗{Colors.END} {name:.<50} FAIL")
                if error:
                    print(f"  {Colors.YELLOW}{error}{Colors.END}")
                if 'Optional' not in category:
                    all_passed = False

            results[name] = passed

    return all_passed, results

def run_functionality_tests():
    """Run basic functionality tests without requiring audio files"""
    print_section("Functionality Tests")

    tests = []
    all_passed = True

    # Test 1: Output directory creation
    print(f"\n{Colors.BOLD}Test 1: Output Directory Creation{Colors.END}")
    try:
        base_dir = Path(__file__).parent
        test_dirs = [
            base_dir / 'outputs',
            base_dir / 'outputs' / 'spectrograms',
            base_dir / 'outputs' / 'trends',
            base_dir / 'outputs' / 'recordings'
        ]

        for dir_path in test_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            if dir_path.exists() and os.access(dir_path, os.W_OK):
                print(f"{Colors.GREEN}✓{Colors.END} {dir_path.name:.<40} Created & Writable")
            else:
                print(f"{Colors.RED}✗{Colors.END} {dir_path.name:.<40} Failed")
                all_passed = False

    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} Directory creation failed: {str(e)}")
        all_passed = False

    # Test 2: Module version information
    print(f"\n{Colors.BOLD}Test 2: Module Version Information{Colors.END}")
    try:
        sys.path.insert(0, str(base_dir / 'src'))
        import __init__ as toolkit_init
        print(f"{Colors.GREEN}✓{Colors.END} Toolkit version: {toolkit_init.__version__}")
        print(f"  Author: {toolkit_init.__author__}")
        print(f"  License: {toolkit_init.__license__}")
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} Version info failed: {str(e)}")
        all_passed = False

    # Test 3: NumPy operations
    print(f"\n{Colors.BOLD}Test 3: NumPy Operations Test{Colors.END}")
    try:
        import numpy as np
        test_array = np.random.randn(1000)
        result = np.fft.fft(test_array)
        print(f"{Colors.GREEN}✓{Colors.END} NumPy FFT operations working")
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} NumPy test failed: {str(e)}")
        all_passed = False

    # Test 4: SciPy signal processing
    print(f"\n{Colors.BOLD}Test 4: SciPy Signal Processing Test{Colors.END}")
    try:
        import numpy as np
        from scipy import signal
        test_data = np.random.randn(10000)
        f, t, Sxx = signal.spectrogram(test_data, fs=44100)
        print(f"{Colors.GREEN}✓{Colors.END} SciPy spectrogram generation working")
        print(f"  Generated spectrogram: {Sxx.shape[0]} freq bins x {Sxx.shape[1]} time bins")
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} SciPy test failed: {str(e)}")
        all_passed = False

    # Test 5: Matplotlib plotting
    print(f"\n{Colors.BOLD}Test 5: Matplotlib Plotting Test{Colors.END}")
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        test_file = base_dir / 'outputs' / 'test_plot.png'
        plt.savefig(test_file)
        plt.close(fig)

        if test_file.exists():
            print(f"{Colors.GREEN}✓{Colors.END} Matplotlib plot generation working")
            test_file.unlink()  # Clean up
        else:
            print(f"{Colors.RED}✗{Colors.END} Plot file not created")
            all_passed = False

    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} Matplotlib test failed: {str(e)}")
        all_passed = False

    # Test 6: Pandas DataFrame operations
    print(f"\n{Colors.BOLD}Test 6: Pandas DataFrame Test{Colors.END}")
    try:
        import pandas as pd
        df = pd.DataFrame({
            'Filename': ['test.wav'],
            'LFN Peak (Hz)': [45.5],
            'LFN dB': [-15.2]
        })
        csv_file = base_dir / 'outputs' / 'test_results.csv'
        df.to_csv(csv_file, index=False)

        if csv_file.exists():
            print(f"{Colors.GREEN}✓{Colors.END} Pandas CSV export working")
            csv_file.unlink()  # Clean up
        else:
            print(f"{Colors.RED}✗{Colors.END} CSV file not created")
            all_passed = False

    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} Pandas test failed: {str(e)}")
        all_passed = False

    # Test 7: Audio device detection
    print(f"\n{Colors.BOLD}Test 7: Audio Device Detection{Colors.END}")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]

        if input_devices:
            print(f"{Colors.GREEN}✓{Colors.END} Found {len(input_devices)} audio input device(s)")
            for i, dev in enumerate(input_devices[:3]):  # Show first 3
                print(f"  [{i}] {dev['name']}")
        else:
            print(f"{Colors.YELLOW}⚠{Colors.END} No audio input devices detected (not critical)")

    except Exception as e:
        print(f"{Colors.YELLOW}⚠{Colors.END} Audio device test failed: {str(e)} (not critical)")

    # Test 8: GPU availability check
    print(f"\n{Colors.BOLD}Test 8: GPU Acceleration Check{Colors.END}")
    try:
        import cupy as cp
        print(f"{Colors.GREEN}✓{Colors.END} CuPy available - GPU acceleration enabled")
        try:
            cuda_version = cp.cuda.runtime.runtimeGetVersion()
            print(f"  CUDA version: {cuda_version}")
        except:
            pass
    except ImportError:
        print(f"{Colors.YELLOW}○{Colors.END} CuPy not available - GPU acceleration disabled (optional)")

    return all_passed

def main():
    """Main test runner"""
    print(f"\n{Colors.BOLD}LFN Audio Toolkit - Test Suite{Colors.END}")
    print(f"Version 2.0.0")
    print(f"Python {sys.version}")

    test_results = {
        'syntax': False,
        'imports': False,
        'functionality': False
    }

    # Run all test suites
    try:
        test_results['syntax'], _ = run_syntax_tests()
        test_results['imports'], _ = run_import_tests()
        test_results['functionality'] = run_functionality_tests()

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Testing interrupted by user{Colors.END}\n")
        sys.exit(130)

    except Exception as e:
        print(f"\n\n{Colors.RED}Unexpected error during testing:{Colors.END}")
        print(f"{Colors.RED}{str(e)}{Colors.END}")
        traceback.print_exc()
        sys.exit(1)

    # Final summary
    print_section("Test Summary")

    all_passed = all(test_results.values())

    print(f"\n{Colors.BOLD}Test Results:{Colors.END}")
    for test_name, passed in test_results.items():
        icon = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
        status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{icon} {test_name.title():.<50} {status}")

    print("\n" + "="*70)

    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.END}")
        print(f"{Colors.GREEN}The toolkit is ready to use!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.END}")
        print(f"{Colors.RED}Please address the failures above before using the toolkit.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
