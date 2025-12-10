#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LFN Health Impact Assessment Tool
Advanced medical-grade analysis of Low Frequency Noise exposure risks
"""

import pandas as pd
import numpy as np
import os
import sys
import argparse
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# Health risk frequency bands (Hz)
CRITICAL_BANDS = {
    'infrasonic': (1, 20),      # Strongest physiological effects
    'low_critical': (20, 50),   # Sleep disruption, anxiety  
    'mid_critical': (50, 80),   # Cardiac/vestibular effects
    'high_lfn': (80, 100)       # Hearing threshold effects
}

# Risk thresholds (dB SPL - Sound Pressure Level re: 20 µPa)
# Based on WHO Environmental Noise Guidelines 2018 & EPA recommendations
RISK_LEVELS = {
    'severe': 55,      # Above WHO/EPA limits - immediate health concern
    'moderate': 45,    # WHO night guideline - sleep disruption risk
    'mild': 40,        # WHO recommended limit - monitoring recommended  
    'minimal': 35      # Background/safe levels
}

# WHO/EPA Environmental Noise Guidelines (A-weighted, overall noise)
# Note: These are for total environmental noise, not LFN-specific
WHO_NIGHT_LIMIT = 45   # WHO nighttime limit (Lnight) for sleep protection
WHO_NIGHT_INTERIM = 53 # WHO interim target
EPA_DAY_LIMIT = 55     # EPA day-night average outdoor limit
EPA_INDOOR_LIMIT = 45  # EPA indoor limit for sleep/rest areas
MEDICAL_CONCERN = 55   # Level requiring medical consultation

def find_csv_files(directory="."):
    """Find all LFN analysis CSV files in directory"""
    csv_files = []
    search_dir = Path(directory)
    
    # Look for standard result files
    patterns = [
        "lfn_analysis_results.csv",
        "*_analysis_results.csv", 
        "lfn_results*.csv"
    ]
    
    for pattern in patterns:
        csv_files.extend(list(search_dir.glob(pattern)))
    
    return [str(f) for f in csv_files]

def find_spectrograms(directory="."):
    """Find all spectrogram PNG files in directory and subdirectories"""
    spectrograms = []
    search_dir = Path(directory)
    
    # Search recursively for spectrogram files
    patterns = ["**/spectrograms/**/*.png", "**/lfn_*.png"]
    
    for pattern in patterns:
        spectrograms.extend(list(search_dir.glob(pattern)))
    
    return [str(f) for f in spectrograms]

def parse_spectrogram_filename(filename):
    """Extract LFN data from spectrogram filename"""
    import re
    basename = os.path.basename(filename)
    
    # Pattern: lfn_HHMMSS_LXX_YY.Y_HZZZZZ_WW.W.png
    # L = LFN freq, Y = LFN dB, H = Ultrasonic freq, W = Ultrasonic dB
    pattern = r'lfn_\d+_L(\d+)_([-\d.]+)_H(\d+)_([-\d.]+)\.png'
    match = re.match(pattern, basename)
    
    if match:
        return {
            'filename': basename,
            'lfn_freq': int(match.group(1)),
            'lfn_db': float(match.group(2)),
            'ultrasonic_freq': int(match.group(3)),
            'ultrasonic_db': float(match.group(4))
        }
    return None

def create_csv_from_spectrograms(spectrogram_files, output_file="spectrogram_analysis.csv"):
    """Create CSV from spectrogram filenames"""
    data = []
    
    for filepath in spectrogram_files:
        parsed = parse_spectrogram_filename(filepath)
        if parsed:
            # Convert to absolute dB SPL (assume measurements were relative to 20 µPa reference)
            abs_db_spl = parsed['lfn_db'] + 94  # Convert relative dB to absolute dB SPL
            # Check if alert threshold exceeded (45 dB SPL = WHO night limit)
            alert = "ALERT" if abs_db_spl >= 45 else "None"
            
            data.append({
                'Filename': parsed['filename'],
                'LFN Peak (Hz)': parsed['lfn_freq'],
                'LFN dB': abs_db_spl,  # Absolute dB SPL
                'Ultrasonic Peak (Hz)': parsed['ultrasonic_freq'],
                'Ultrasonic dB': parsed['ultrasonic_db'] + 94,  # Convert to absolute
                'Alerts': alert
            })
    
    if data:
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        return output_file, len(data)
    
    return None, 0

def classify_frequency_band(frequency):
    """Classify frequency into health impact band"""
    for band_name, (low, high) in CRITICAL_BANDS.items():
        if low <= frequency <= high:
            return band_name.replace('_', ' ').title()
    return 'Out of Range'

def classify_risk_level(db_level):
    """Classify dB SPL level into health risk category"""
    # Levels are now absolute dB SPL, higher values = higher risk
    if db_level >= RISK_LEVELS['severe']:
        return 'SEVERE'
    elif db_level >= RISK_LEVELS['moderate']:
        return 'MODERATE'
    elif db_level >= RISK_LEVELS['mild']:
        return 'MILD'
    else:
        return 'MINIMAL'

def get_health_impact(frequency, db_level):
    """Return specific health impact for frequency/level combination (dB SPL)"""
    
    # Severe level impacts (immediate concern)
    if db_level >= 55:
        return "⚠️ IMMEDIATE HEALTH CONCERN - Exceeds WHO/EPA limits"
    
    # Frequency-specific impacts
    if 1 <= frequency <= 20 and db_level >= 40:
        return "Infrasonic effects: nausea, disorientation, panic"
    elif 20 <= frequency <= 50 and db_level >= 45:
        return "Sleep disruption, anxiety, chronic fatigue"
    elif 46 <= frequency <= 60 and db_level >= 45:
        return "Sleep disruption, possible cardiac stress responses"
    elif 60 <= frequency <= 80 and db_level >= 45:
        return "Vestibular effects, concentration issues, headaches"
    elif 80 <= frequency <= 100 and db_level >= 45:
        return "Hearing threshold effects, tinnitus risk"
    elif db_level >= 40:
        return "Monitor for cumulative effects, document symptoms"
    else:
        return "Low risk - within WHO/EPA guidelines"

def get_medical_recommendations(frequency, db_level, exposure_duration=None):
    """Provide medical recommendations based on exposure (dB SPL)"""
    recommendations = []
    
    if db_level >= 55:
        recommendations.append("🏥 Seek medical consultation immediately")
        recommendations.append("📋 Document all symptoms with timestamps")
        recommendations.append("🚨 Environment exceeds WHO/EPA safety limits")
        
    if db_level >= 45:
        recommendations.append("🛏️ Avoid exposure during sleep hours")
        recommendations.append("📱 Monitor symptoms: sleep quality, headaches, anxiety")
        recommendations.append("🔇 Consider noise mitigation or relocation")
        
    if 50 <= frequency <= 60 and db_level >= 45:
        recommendations.append("💓 Monitor heart rate variability and blood pressure")
        
    if exposure_duration and exposure_duration > 4:
        recommendations.append("⏱️ Limit continuous exposure to <2 hours when possible")
        
    if not recommendations:
        recommendations.append("📊 Continue monitoring, maintain exposure log")
        
    return recommendations

def calculate_cumulative_exposure(df):
    """Calculate cumulative exposure metrics"""
    # Convert Alerts column to string type to handle None/NaN values
    df['Alerts'] = df['Alerts'].astype(str)
    alerts = df[df['Alerts'].str.contains('ALERT', na=False)]
    
    if len(alerts) == 0:
        return {
            'total_alerts': 0,
            'avg_frequency': 0.0,
            'avg_level': 0.0,
            'max_level': 0.0,
            'risk_hours': 0.0
        }
    
    # Extract frequency and level from alerts
    frequencies = []
    levels = []
    
    for _, row in alerts.iterrows():
        try:
            freq = float(row['LFN Peak (Hz)'])
            level = float(row['LFN dB'])
            frequencies.append(freq)
            levels.append(level)
        except (ValueError, KeyError):
            continue
    
    if not frequencies:
        return {
            'total_alerts': int(len(alerts)),
            'avg_frequency': 0.0,
            'avg_level': 0.0, 
            'max_level': 0.0,
            'risk_hours': 0.0
        }
    
    return {
        'total_alerts': int(len(alerts)),
        'avg_frequency': float(np.mean(frequencies)),
        'avg_level': float(np.mean(levels)),
        'max_level': float(np.max(levels)),
        'risk_hours': float(len(alerts) * 0.5)  # Estimate 30min per recording
    }

def generate_health_report(csv_file, output_dir="."):
    """Generate comprehensive health impact report"""
    
    print(f"\n🏥 HEALTH IMPACT ANALYSIS")
    print("=" * 70)
    print(f"📁 Data Source: {os.path.basename(csv_file)}")
    print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return
    
    # Calculate cumulative metrics
    metrics = calculate_cumulative_exposure(df)
    
    print(f"\n📊 EXPOSURE SUMMARY")
    print("-" * 40)
    print(f"Total Alert Files: {metrics['total_alerts']}")
    print(f"Average Frequency: {metrics['avg_frequency']:.1f} Hz")
    print(f"Average Level: {metrics['avg_level']:.1f} dB")
    print(f"Maximum Level: {metrics['max_level']:.1f} dB")
    print(f"Estimated Risk Hours: {metrics['risk_hours']:.1f} hours")
    
    # Overall risk assessment (absolute dB SPL)
    print(f"\n🎯 OVERALL RISK ASSESSMENT")
    print("-" * 40)
    
    if metrics['total_alerts'] == 0:
        overall_risk = "🟢 LOW RISK"
        print(f"{overall_risk} - No alerts detected, continue monitoring")
    elif metrics['max_level'] >= RISK_LEVELS['severe']:
        overall_risk = "🔴 HIGH RISK"
        print(f"{overall_risk} - Immediate medical attention recommended")
    elif metrics['avg_level'] >= RISK_LEVELS['moderate']:
        overall_risk = "🟡 MODERATE RISK"
        print(f"{overall_risk} - Health effects likely, mitigation needed")
    elif metrics['total_alerts'] > 0:
        overall_risk = "🟠 LOW-MODERATE RISK"
        print(f"{overall_risk} - Monitor symptoms, consider reduction")
    else:
        overall_risk = "🟢 LOW RISK"
        print(f"{overall_risk} - Continue monitoring as precaution")
    
    # File-by-file analysis
    alerts = df[df['Alerts'].str.contains('ALERT', na=False)]
    
    if len(alerts) > 0:
        print(f"\n📋 DETAILED FILE ANALYSIS")
        print("-" * 40)
        
        for idx, (_, row) in enumerate(alerts.iterrows(), 1):
            try:
                filename = row['Filename']
                frequency = float(row['LFN Peak (Hz)'])
                db_level = float(row['LFN dB'])
                
                band = classify_frequency_band(frequency)
                risk = classify_risk_level(db_level)
                impact = get_health_impact(frequency, db_level)
                
                print(f"\n{idx}. 📁 {filename}")
                print(f"   🎯 Frequency: {frequency:.1f} Hz ({band})")
                print(f"   📊 Level: {db_level:.1f} dB ({risk} risk)")
                print(f"   ⚕️ Health Impact: {impact}")
                
                # Medical recommendations
                recommendations = get_medical_recommendations(frequency, db_level)
                if recommendations:
                    print(f"   📋 Recommendations:")
                    for rec in recommendations:
                        print(f"      • {rec}")
                        
            except (ValueError, KeyError) as e:
                print(f"   ⚠️ Could not parse data for row {idx}: {e}")
                continue
    
    # Generate compliance report
    print(f"\n📜 REGULATORY COMPLIANCE")
    print("-" * 40)
    
    if metrics['total_alerts'] == 0:
        print("✅ No alerts detected - monitoring within safe limits")
    else:
        if metrics['max_level'] > WHO_NIGHT_LIMIT:
            print(f"⚠️ WHO Night Limit Exceeded: {metrics['max_level']:.1f} dB > {WHO_NIGHT_LIMIT} dB")
        else:
            print(f"✅ WHO Night Limit Compliant: {metrics['max_level']:.1f} dB ≤ {WHO_NIGHT_LIMIT} dB")
            
        if metrics['avg_level'] > EPA_DAY_LIMIT:
            print(f"⚠️ EPA Day Limit Exceeded: {metrics['avg_level']:.1f} dB > {EPA_DAY_LIMIT} dB")
        else:
            print(f"✅ EPA Day Limit Compliant: {metrics['avg_level']:.1f} dB ≤ {EPA_DAY_LIMIT} dB")
            
        if metrics['max_level'] > MEDICAL_CONCERN:
            print(f"⚠️ Medical Consultation Recommended: {metrics['max_level']:.1f} dB > {MEDICAL_CONCERN} dB")
    
    # Save detailed report
    report_data = {
        'analysis_date': datetime.now().isoformat(),
        'source_file': csv_file,
        'overall_risk': overall_risk,
        'metrics': metrics,
        'compliance': {
            'who_night_compliant': bool(metrics['max_level'] <= WHO_NIGHT_LIMIT),
            'epa_day_compliant': bool(metrics['avg_level'] <= EPA_DAY_LIMIT),
            'medical_consultation_needed': bool(metrics['max_level'] > MEDICAL_CONCERN)
        },
        'alert_files': []
    }
    
    for _, row in alerts.iterrows():
        try:
            file_data = {
                'filename': row['Filename'],
                'frequency': float(row['LFN Peak (Hz)']),
                'db_level': float(row['LFN dB']),
                'band': classify_frequency_band(float(row['LFN Peak (Hz)'])),
                'risk_level': classify_risk_level(float(row['LFN dB'])),
                'health_impact': get_health_impact(float(row['LFN Peak (Hz)']), float(row['LFN dB'])),
                'recommendations': get_medical_recommendations(float(row['LFN Peak (Hz)']), float(row['LFN dB']))
            }
            report_data['alert_files'].append(file_data)
        except (ValueError, KeyError):
            continue
    
    # Save JSON report
    report_file = os.path.join(output_dir, f"health_assessment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    try:
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"\n💾 Detailed report saved: {report_file}")
    except Exception as e:
        print(f"⚠️ Could not save report: {e}")
    
    print(f"\n{'='*70}")
    print("🏥 Health assessment complete. Consult healthcare provider if concerned.")
    print(f"{'='*70}\n")
    
    return report_data

def main():
    parser = argparse.ArgumentParser(description="LFN Health Impact Assessment Tool")
    parser.add_argument("path", nargs="?", help="CSV file or directory to analyze (optional - will search for results)")
    parser.add_argument("--output-dir", "-o", default=".", help="Output directory for reports")
    parser.add_argument("--auto-find", "-a", action="store_true", help="Automatically find CSV files in current directory")
    parser.add_argument("--spectrograms", "-s", action="store_true", help="Analyze spectrograms directly from directory")
    
    args = parser.parse_args()
    
    print("🏥 LFN Health Impact Assessment Tool")
    print("=" * 50)
    
    csv_files = []
    temp_csv = None
    
    # Check if path is a directory with spectrograms
    if args.path and os.path.isdir(args.path):
        print(f"📁 Searching for spectrograms in: {args.path}")
        spectrograms = find_spectrograms(args.path)
        
        if spectrograms:
            print(f"🔍 Found {len(spectrograms)} spectrogram files")
            print("📊 Creating analysis CSV from spectrograms...")
            
            temp_csv = os.path.join(args.output_dir, "temp_spectrogram_analysis.csv")
            csv_file, count = create_csv_from_spectrograms(spectrograms, temp_csv)
            
            if csv_file:
                print(f"✅ Successfully parsed {count} spectrograms")
                csv_files = [csv_file]
            else:
                print("❌ No valid spectrograms found")
                return
        else:
            print("❌ No spectrogram files found in directory")
            # Fall back to CSV search
            print("📁 Searching for CSV files instead...")
            found_files = find_csv_files(args.path)
            if found_files:
                csv_files = found_files
            else:
                print("❌ No CSV or spectrogram files found")
                return
    
    elif args.spectrograms or (args.path and not os.path.exists(args.path)):
        # Spectrogram mode
        search_dir = args.path if args.path else "."
        print(f"📁 Searching for spectrograms in: {search_dir}")
        spectrograms = find_spectrograms(search_dir)
        
        if spectrograms:
            print(f"🔍 Found {len(spectrograms)} spectrogram files")
            print("📊 Creating analysis CSV from spectrograms...")
            
            temp_csv = os.path.join(args.output_dir, "temp_spectrogram_analysis.csv")
            csv_file, count = create_csv_from_spectrograms(spectrograms, temp_csv)
            
            if csv_file:
                print(f"✅ Successfully parsed {count} spectrograms")
                csv_files = [csv_file]
            else:
                print("❌ No valid spectrograms found")
                return
        else:
            print("❌ No spectrogram files found")
            return
    
    elif args.auto_find or not args.path:
        # Auto-find CSV files
        found_files = find_csv_files(args.output_dir)
        if found_files:
            print(f"📁 Found {len(found_files)} CSV file(s):")
            for i, f in enumerate(found_files, 1):
                print(f"  {i}. {os.path.basename(f)}")
            
            if len(found_files) == 1:
                csv_files = found_files
            else:
                print("\nSelect file to analyze (or 'all' for all files):")
                choice = input("Enter choice: ").strip().lower()
                
                if choice == 'all':
                    csv_files = found_files
                else:
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(found_files):
                            csv_files = [found_files[idx]]
                        else:
                            print("Invalid selection")
                            return
                    except ValueError:
                        print("Invalid selection")
                        return
        else:
            print("❌ No CSV files found. Run the batch analyzer first.")
            return
    else:
        # Use specified file
        if os.path.exists(args.path):
            csv_files = [args.path]
        else:
            print(f"❌ File not found: {args.path}")
            return
    
    # Analyze each CSV file
    for csv_file in csv_files:
        generate_health_report(csv_file, args.output_dir)
    
    # Clean up temporary CSV
    if temp_csv and os.path.exists(temp_csv):
        try:
            os.remove(temp_csv)
            print(f"🗑️ Cleaned up temporary file: {temp_csv}")
        except:
            pass

if __name__ == "__main__":
    main()