# Windows Batch Files Guide

This folder contains convenient Windows batch files (.bat) for easy access to all toolkit functions.

## 🚀 Quick Start

**Double-click:** [START_HERE.bat](START_HERE.bat)

This opens an interactive menu with access to all toolkit functions.

---

## 📁 Available Batch Files

### Main Menu
- **START_HERE.bat** - Interactive menu for all functions

### Setup & Testing (Run these first!)
1. **1_SETUP.bat** - Install all Python dependencies
2. **2_PREFLIGHT_CHECK.bat** - Verify system readiness
3. **3_RUN_TESTS.bat** - Run comprehensive test suite

### Analysis Tools
4. **4_BATCH_ANALYZER.bat** - Analyze audio files in a directory
5. **5_REALTIME_MONITOR.bat** - Live audio monitoring
6. **6_HEALTH_ASSESSMENT.bat** - Health impact analysis
7. **7_LONG_DURATION_RECORDER.bat** - Extended recording sessions

---

## 📋 First-Time Setup

### Step 1: Install Dependencies
```
Double-click: 1_SETUP.bat
```
This will:
- Check Python version
- Install all required packages from requirements.txt
- Create output directories
- Verify installation

### Step 2: Run Pre-flight Check
```
Double-click: 2_PREFLIGHT_CHECK.bat
```
This will verify:
- Python version (3.8+)
- All packages installed correctly
- FFmpeg availability
- Audio devices
- GPU support (optional)
- Disk space and permissions

### Step 3: Run Tests (Optional but Recommended)
```
Double-click: 3_RUN_TESTS.bat
```
This will test:
- All Python modules
- Dependencies
- Basic functionality
- System compatibility

---

## 🎯 Using the Tools

### Batch File Analyzer

**Simple Usage:**
```
Double-click: 4_BATCH_ANALYZER.bat
(You'll be prompted for the audio directory)
```

**With Options:**
```
Right-click folder → Open Command Prompt here

Then run:
4_BATCH_ANALYZER.bat "C:\Path\To\Audio" --gpu
```

**Options:**
- `--gpu` - Enable GPU acceleration
- `--export-formats csv json excel` - Choose export formats
- `--lfn-threshold -20.0` - Set LFN alert threshold
- `--hf-threshold -30.0` - Set ultrasonic threshold
- `--no-trends` - Disable trend plots

---

### Real-time Monitor

**Simple Usage:**
```
Double-click: 5_REALTIME_MONITOR.bat
```

**With Options:**
```
5_REALTIME_MONITOR.bat --gpu --auto-start --duration 300
```

**Options:**
- `--gpu` - Enable GPU acceleration
- `--device N` - Select specific audio device
- `--lfn-threshold 45.0` - Set LFN threshold
- `--hf-threshold 50.0` - Set ultrasonic threshold
- `--auto-start` - Start monitoring immediately
- `--duration N` - Auto-stop after N seconds

---

### Health Assessment

**Simple Usage:**
```
Double-click: 6_HEALTH_ASSESSMENT.bat
(Choose auto-find or specify path)
```

**With Options:**
```
6_HEALTH_ASSESSMENT.bat --auto-find
6_HEALTH_ASSESSMENT.bat "C:\Path\To\Results.csv"
6_HEALTH_ASSESSMENT.bat --spectrograms
```

---

### Long Duration Recorder

**Simple Usage:**
```
Double-click: 7_LONG_DURATION_RECORDER.bat
(You'll be prompted for duration and output folder)
```

**Features:**
- Records for 8+ hours
- Automatically segments files (30-minute chunks)
- Memory-efficient
- Prevents memory overflow

---

## 🔧 Troubleshooting Batch Files

### Problem: "Python not found"

**Solution:**
1. Install Python 3.8+ from python.org
2. During installation, check "Add Python to PATH"
3. Restart Command Prompt
4. Run: `python --version` to verify

---

### Problem: "Access Denied" or "Permission Error"

**Solution:**
Right-click the .bat file → "Run as Administrator"

---

### Problem: Batch file closes immediately

**Solution:**
The scripts have `pause` at the end, but if it still closes:
1. Open Command Prompt
2. Navigate to toolkit folder: `cd C:\path\to\LFN_Audio_Toolkit_Production`
3. Run the batch file from command prompt: `1_SETUP.bat`

---

### Problem: Can't run with parameters

**To run with command-line options:**
1. Open Command Prompt in the toolkit folder:
   - Shift + Right-click in folder → "Open PowerShell window here"
   - Or: Win+R → type `cmd` → navigate to folder

2. Run with parameters:
   ```
   4_BATCH_ANALYZER.bat "C:\Audio\Files" --gpu
   5_REALTIME_MONITOR.bat --auto-start --duration 600
   ```

---

## 💡 Tips & Tricks

### Drag and Drop
You can drag a folder onto `4_BATCH_ANALYZER.bat` to analyze it:
1. Open File Explorer
2. Drag audio folder onto the .bat file
3. Release - it will start analyzing

### Desktop Shortcuts
Create shortcuts for quick access:
1. Right-click any .bat file
2. Send to → Desktop (create shortcut)
3. Rename as needed

### Schedule Recordings
Use Windows Task Scheduler with batch files:
1. Open Task Scheduler
2. Create Basic Task
3. Action: Start a program
4. Program: `C:\...\5_REALTIME_MONITOR.bat`
5. Add arguments: `--auto-start --duration 3600`

---

## 📊 What Each Batch File Does

| Batch File | Purpose | Run When |
|------------|---------|----------|
| START_HERE.bat | Main menu | Anytime for easy access |
| 1_SETUP.bat | Install dependencies | First time setup |
| 2_PREFLIGHT_CHECK.bat | System verification | After setup, before first use |
| 3_RUN_TESTS.bat | Functionality tests | After setup (optional) |
| 4_BATCH_ANALYZER.bat | Analyze audio files | When you have files to analyze |
| 5_REALTIME_MONITOR.bat | Live monitoring | For real-time audio analysis |
| 6_HEALTH_ASSESSMENT.bat | Health analysis | After batch analysis |
| 7_LONG_DURATION_RECORDER.bat | Long recordings | For 8+ hour sessions |

---

## 🎓 Usage Examples

### Example 1: First-Time User
```
1. Double-click: START_HERE.bat
2. Select [1] Setup and Install
3. Select [2] Pre-flight Check
4. Select [4] Batch Analyzer
5. Enter path when prompted
```

### Example 2: Quick Analysis
```
1. Drag folder onto 4_BATCH_ANALYZER.bat
2. Wait for analysis to complete
3. Check outputs folder for results
```

### Example 3: Scheduled Monitoring
```
Create Task Scheduler entry:
Program: 5_REALTIME_MONITOR.bat
Arguments: --auto-start --duration 7200 --gpu
Schedule: Daily at 10:00 PM
```

### Example 4: Health Check Workflow
```
1. Run 4_BATCH_ANALYZER.bat on audio files
2. Run 6_HEALTH_ASSESSMENT.bat --auto-find
3. Review health assessment report
```

---

## 🔗 Related Documentation

- **README.md** - Full toolkit documentation
- **TROUBLESHOOTING.md** - Problem solving guide
- **DEPLOYMENT_CHECKLIST.md** - Complete analysis report
- **USER_GUIDE.md** - Detailed user guide (in docs/)

---

## ⚡ Quick Reference Card

**Print this for quick reference:**

```
┌─────────────────────────────────────────────────────┐
│      LFN Audio Toolkit - Quick Reference           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  SETUP (First Time):                               │
│    1. Double-click START_HERE.bat                  │
│    2. Select [1] Setup                             │
│    3. Select [2] Pre-flight Check                  │
│                                                     │
│  ANALYZE FILES:                                    │
│    Drag folder → 4_BATCH_ANALYZER.bat              │
│                                                     │
│  LIVE MONITORING:                                  │
│    Double-click 5_REALTIME_MONITOR.bat             │
│                                                     │
│  HEALTH CHECK:                                     │
│    Double-click 6_HEALTH_ASSESSMENT.bat            │
│                                                     │
│  HELP:                                             │
│    See TROUBLESHOOTING.md                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

**Version:** 2.0.0
**Last Updated:** December 10, 2025
**Platform:** Windows 10/11
