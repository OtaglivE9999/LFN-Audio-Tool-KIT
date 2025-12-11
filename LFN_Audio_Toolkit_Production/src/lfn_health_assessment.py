#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LFN Health Impact Assessment Tool
Advanced medical-grade analysis of Low Frequency Noise exposure risks

SCIENTIFIC BASIS:
This tool incorporates research from Dr. Mariana Alves-Pereira and colleagues
on Vibroacoustic Disease (VAD) - a whole-body pathology caused by chronic
exposure to Infrasound and Low-Frequency Noise (ILFN).

Key References:
1. Alves-Pereira M, Castelo Branco NAA. "Vibroacoustic Disease: Biological 
   effects of infrasound and low-frequency noise explained by mechanotransduction 
   cellular signalling." Progress in Biophysics and Molecular Biology, 2007.
2. Castelo Branco NAA, Alves-Pereira M. "Vibroacoustic disease." Noise & Health, 2004.
3. Alves-Pereira M. "Noise-induced extra-aural pathology: A review and commentary."
   Aviation, Space, and Environmental Medicine, 1999.
4. Alves-Pereira M, Castelo Branco NAA. "Public Health and Noise Exposure: The 
   Importance of Low-Frequency Noise." Inter-Noise, 2007.

VAD is characterized by:
- Abnormal proliferation of extracellular matrices (collagen, elastin)
- Thickening of blood vessel walls, pericardium, and cardiac structures
- Neurological, respiratory, and cognitive impairments
- Symptoms progressing through 3 clinical stages based on exposure duration
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

# =============================================================================
# VIBROACOUSTIC DISEASE (VAD) RESEARCH - Dr. Mariana Alves-Pereira
# =============================================================================
# VAD is caused by chronic exposure to ILFN (Infrasound & Low-Frequency Noise)
# The pathology affects multiple organ systems through mechanotransduction
# cellular signalling, causing abnormal tissue growth and structural changes.

# ILFN Frequency Bands based on Alves-Pereira research
# ILFN range: 0-500 Hz (infrasound <20 Hz, low-frequency 20-500 Hz)
CRITICAL_BANDS = {
    'infrasonic': (0, 20),           # Infrasound - whole body resonance effects
    'cardiac_resonance': (1, 8),     # Heart/thorax resonance (Alves-Pereira)
    'vestibular_critical': (8, 12),  # Vestibular system most sensitive
    'respiratory': (12, 20),         # Respiratory tract resonance
    'low_lfn': (20, 50),             # Lower LFN - significant VAD risk
    'mid_lfn': (50, 100),            # Mid LFN - auditory & extra-auditory
    'upper_lfn': (100, 200),         # Upper LFN range
    'extended_lfn': (200, 500)       # Extended LFN per VAD research
}

# VAD Clinical Stages (Alves-Pereira & Castelo Branco, 2004)
# Based on years of occupational/environmental ILFN exposure
VAD_STAGES = {
    'stage_i': {
        'years_exposure': (1, 4),
        'name': 'Stage I (Initial)',
        'description': 'Slight mood changes, bronchitis, infections',
        'symptoms': [
            'Mood swings, irritability',
            'Slight memory/concentration deficits', 
            'Repeated respiratory infections',
            'Bronchitis episodes',
            'Heartburn, digestive issues'
        ]
    },
    'stage_ii': {
        'years_exposure': (4, 10),
        'name': 'Stage II (Moderate)', 
        'description': 'Chest pain, fatigue, skin changes, depression',
        'symptoms': [
            'Chest pain without cardiac pathology',
            'Definite mood changes, depression',
            'Decreased cognitive function',
            'Fatigue, decreased pain sensitivity',
            'Skin and mucosal infections',
            'GI disorders (reflux, ulcers)',
            'Joint pain, muscle aches'
        ]
    },
    'stage_iii': {
        'years_exposure': (10, 50),
        'name': 'Stage III (Severe)',
        'description': 'Psychiatric disorders, hemorrhages, severe pain',
        'symptoms': [
            'Severe psychiatric manifestations',
            'Intense/persistent fatigue',
            'Seizures possible',
            'Nose/digestive hemorrhages',
            'Severe headaches, intracranial hypertension',
            'Pericardial thickening (echocardiogram)',
            'Cardiac valve abnormalities',
            'Significant cognitive impairment'
        ]
    }
}

# VAD-specific thresholds (dB SPL - unweighted, not A-weighted)
# Based on Alves-Pereira research: ILFN effects occur at levels 
# considered "acceptable" by conventional A-weighted standards
# A-weighting severely underestimates ILFN exposure risk
VAD_RISK_LEVELS = {
    'critical': 90,     # Severe VAD risk - occupational exposure levels
    'high': 75,         # High risk - chronic exposure concern
    'moderate': 60,     # Moderate risk - residential ILFN exposure
    'low': 50,          # Low risk - monitoring recommended
    'minimal': 40       # Background levels
}

# Risk thresholds (dB SPL - Sound Pressure Level re: 20 µPa)
# IMPORTANT: These must be measured with linear/C-weighting, NOT A-weighting
# A-weighting underestimates LFN by 20-50 dB (Alves-Pereira, 2007)
RISK_LEVELS = {
    'severe': 70,       # VAD critical threshold for residential
    'moderate': 55,     # Significant biological effects expected
    'mild': 45,         # Monitoring recommended per VAD research
    'minimal': 35       # Background/safe levels
}

# WHO/EPA Environmental Noise Guidelines (A-weighted, overall noise)
# NOTE: A-weighting is INAPPROPRIATE for ILFN assessment (Alves-Pereira)
# These limits do NOT protect against VAD/ILFN health effects
WHO_NIGHT_LIMIT = 45   # WHO nighttime limit (Lnight) - A-weighted
WHO_NIGHT_INTERIM = 53 # WHO interim target - A-weighted
EPA_DAY_LIMIT = 55     # EPA day-night average outdoor limit - A-weighted
EPA_INDOOR_LIMIT = 45  # EPA indoor limit - A-weighted
MEDICAL_CONCERN = 55   # A-weighted level requiring consultation

# VAD-specific thresholds (Linear/C-weighted or unweighted)
VAD_RESIDENTIAL_LIMIT = 50  # dB(Lin) - chronic residential exposure concern
VAD_OCCUPATIONAL_LIMIT = 90 # dB(Lin) - occupational VAD threshold
VAD_MEDICAL_CONCERN = 60    # dB(Lin) - medical evaluation recommended

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
    """
    Classify frequency into health impact band based on VAD research
    
    Reference: Alves-Pereira M, Castelo Branco NAA. "Vibroacoustic Disease: 
    Biological effects of infrasound and low-frequency noise explained by 
    mechanotransduction cellular signalling." 2007.
    """
    # Check specific resonance bands first (Alves-Pereira research)
    if 1 <= frequency <= 8:
        return 'Cardiac/Thorax Resonance (VAD Critical)'
    elif 8 < frequency <= 12:
        return 'Vestibular Critical Band'
    elif 12 < frequency <= 20:
        return 'Respiratory Resonance (Infrasonic)'
    
    # General ILFN bands
    for band_name, (low, high) in CRITICAL_BANDS.items():
        if low <= frequency <= high:
            return band_name.replace('_', ' ').title()
    
    if frequency > 500:
        return 'Above ILFN Range'
    return 'Out of Range'

def classify_risk_level(db_level):
    """
    Classify dB SPL level into health risk category per VAD research
    
    IMPORTANT: Assumes LINEAR/C-weighted measurements, not A-weighted.
    A-weighting severely underestimates ILFN exposure (Alves-Pereira, 2007)
    """
    if db_level >= VAD_RISK_LEVELS['critical']:
        return 'VAD CRITICAL'
    elif db_level >= VAD_RISK_LEVELS['high']:
        return 'HIGH (VAD Risk)'
    elif db_level >= VAD_RISK_LEVELS['moderate']:
        return 'MODERATE'
    elif db_level >= VAD_RISK_LEVELS['low']:
        return 'LOW'
    else:
        return 'MINIMAL'

def get_vad_stage_assessment(exposure_hours, db_level):
    """
    Assess potential VAD stage based on exposure duration
    
    Based on Alves-Pereira & Castelo Branco clinical staging (2004):
    - Stage I: 1-4 years exposure
    - Stage II: 4-10 years exposure  
    - Stage III: >10 years exposure
    """
    # Estimate years from hours (assuming 8hr daily occupational or 16hr residential)
    estimated_years = exposure_hours / (365 * 16)  # Conservative residential estimate
    
    if estimated_years >= 10 and db_level >= VAD_RISK_LEVELS['moderate']:
        return VAD_STAGES['stage_iii']
    elif estimated_years >= 4 and db_level >= VAD_RISK_LEVELS['low']:
        return VAD_STAGES['stage_ii']
    elif estimated_years >= 1 and db_level >= VAD_RISK_LEVELS['minimal']:
        return VAD_STAGES['stage_i']
    return None

def get_health_impact(frequency, db_level):
    """
    Return specific health impact for frequency/level combination
    
    Based on Dr. Mariana Alves-Pereira's VAD research:
    - ILFN causes mechanotransduction cellular signalling disruption
    - Effects include abnormal collagen/elastin proliferation
    - Multiple organ systems affected (cardiovascular, respiratory, neurological)
    
    Reference: Progress in Biophysics and Molecular Biology, 2007
    """
    
    # VAD Critical levels (occupational exposure equivalent)
    if db_level >= VAD_RISK_LEVELS['critical']:
        return "🚨 VAD CRITICAL - Occupational exposure level, severe pathology risk"
    
    # High VAD risk - chronic exposure effects
    if db_level >= VAD_RISK_LEVELS['high']:
        impacts = []
        if 1 <= frequency <= 8:
            impacts.append("Cardiac resonance - pericardial thickening risk")
        if 8 < frequency <= 12:
            impacts.append("Vestibular disruption - balance/spatial issues")
        if frequency <= 20:
            impacts.append("Whole-body vibration effects (VAD mechanism)")
        return "⚠️ HIGH VAD RISK: " + "; ".join(impacts) if impacts else "⚠️ HIGH VAD RISK"
    
    # Frequency-specific impacts based on VAD research
    if 1 <= frequency <= 8 and db_level >= VAD_RISK_LEVELS['moderate']:
        return "Cardiac/thorax resonance band - potential pericardial effects (Alves-Pereira)"
    
    elif 8 < frequency <= 12 and db_level >= VAD_RISK_LEVELS['moderate']:
        return "Vestibular critical band - balance issues, vertigo, nausea (VAD research)"
    
    elif 12 < frequency <= 20 and db_level >= VAD_RISK_LEVELS['moderate']:
        return "Respiratory resonance - bronchitis, respiratory tract effects (VAD Stage I)"
    
    elif 20 <= frequency <= 50 and db_level >= VAD_RISK_LEVELS['low']:
        return "LFN band - sleep disruption, mood changes, cognitive effects (VAD research)"
    
    elif 50 <= frequency <= 100 and db_level >= VAD_RISK_LEVELS['low']:
        return "Mid-LFN - fatigue, concentration issues, irritability"
    
    elif 100 <= frequency <= 200 and db_level >= VAD_RISK_LEVELS['low']:
        return "Upper LFN - auditory effects, potential tinnitus"
    
    elif 200 <= frequency <= 500 and db_level >= VAD_RISK_LEVELS['low']:
        return "Extended ILFN range - monitoring recommended"
    
    elif db_level >= VAD_RISK_LEVELS['minimal']:
        return "Monitor for cumulative VAD effects, document symptoms"
    else:
        return "Below VAD concern threshold - continue monitoring"

def get_medical_recommendations(frequency, db_level, exposure_duration=None):
    """
    Provide medical recommendations based on VAD research
    
    Based on Alves-Pereira clinical protocols for VAD assessment:
    1. Echocardiogram (pericardial thickness measurement)
    2. Respiratory function tests
    3. Neurological/cognitive assessment
    4. Complete symptom documentation
    """
    recommendations = []
    
    # Critical VAD exposure
    if db_level >= VAD_RISK_LEVELS['critical']:
        recommendations.extend([
            "🏥 URGENT: Seek occupational medicine specialist",
            "💓 Request echocardiogram (check pericardial thickness - VAD marker)",
            "🫁 Respiratory function testing recommended",
            "🧠 Neurological evaluation for cognitive effects",
            "📋 Document ALL symptoms with dates and exposure times",
            "🚨 Environment exceeds VAD occupational threshold"
        ])
    
    # High VAD risk
    elif db_level >= VAD_RISK_LEVELS['high']:
        recommendations.extend([
            "🏥 Schedule medical consultation (VAD-aware physician)",
            "💓 Consider echocardiogram if exposure >1 year",
            "📋 Keep detailed symptom diary (mood, sleep, cognitive)",
            "🔇 Implement noise mitigation immediately",
            "⚠️ Exposure level associated with VAD development"
        ])
    
    # Moderate risk
    elif db_level >= VAD_RISK_LEVELS['moderate']:
        recommendations.extend([
            "🛏️ Avoid ILFN exposure during sleep hours",
            "📱 Monitor: sleep quality, mood, concentration, fatigue",
            "🔇 Consider noise mitigation or relocation",
            "📋 Document symptoms per VAD staging criteria"
        ])
    
    # Frequency-specific recommendations (Alves-Pereira research)
    if 1 <= frequency <= 12 and db_level >= VAD_RISK_LEVELS['low']:
        recommendations.append("💓 Cardiac monitoring recommended (resonance frequency band)")
    
    if 8 <= frequency <= 20 and db_level >= VAD_RISK_LEVELS['low']:
        recommendations.append("🌀 Report any balance/vestibular symptoms")
    
    if frequency <= 20 and db_level >= VAD_RISK_LEVELS['moderate']:
        recommendations.append("🫁 Monitor respiratory health (bronchitis, infections)")
    
    # Chronic exposure considerations
    if exposure_duration:
        years_estimate = exposure_duration / (365 * 16)
        if years_estimate >= 4:
            recommendations.append("⏱️ Long-term exposure detected - comprehensive VAD screening advised")
        elif years_estimate >= 1:
            recommendations.append("📊 Monitor for VAD Stage I symptoms (mood, respiratory)")
    
    if not recommendations:
        recommendations.append("📊 Continue monitoring, maintain ILFN exposure log")
        recommendations.append("📖 Reference: Alves-Pereira VAD research for symptom awareness")
    
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
    """
    Generate comprehensive health impact report based on VAD research
    
    Analysis methodology based on:
    - Dr. Mariana Alves-Pereira's Vibroacoustic Disease research (1980s-present)
    - ILFN exposure assessment protocols
    - VAD clinical staging criteria
    """
    
    print(f"\n🏥 VIBROACOUSTIC DISEASE (VAD) HEALTH ASSESSMENT")
    print("=" * 70)
    print("Based on Dr. Mariana Alves-Pereira ILFN Research")
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
    
    print(f"\n📊 ILFN EXPOSURE SUMMARY")
    print("-" * 40)
    print(f"Total Alert Files: {metrics['total_alerts']}")
    print(f"Average Frequency: {metrics['avg_frequency']:.1f} Hz")
    print(f"Average Level: {metrics['avg_level']:.1f} dB (Linear/C-weighted)")
    print(f"Maximum Level: {metrics['max_level']:.1f} dB")
    print(f"Estimated Exposure Hours: {metrics['risk_hours']:.1f} hours")
    
    # VAD-specific risk assessment
    print(f"\n🔬 VAD RISK ASSESSMENT (Alves-Pereira Criteria)")
    print("-" * 40)
    
    if metrics['total_alerts'] == 0:
        overall_risk = "🟢 LOW RISK"
        print(f"{overall_risk} - No ILFN alerts detected")
    elif metrics['max_level'] >= VAD_RISK_LEVELS['critical']:
        overall_risk = "🔴 VAD CRITICAL"
        print(f"{overall_risk} - Occupational exposure levels detected!")
        print("   ⚠️ Immediate medical evaluation recommended")
        print("   💓 Request echocardiogram (pericardial thickening check)")
    elif metrics['max_level'] >= VAD_RISK_LEVELS['high']:
        overall_risk = "🟠 HIGH VAD RISK"
        print(f"{overall_risk} - Chronic exposure concern")
        print("   ⚠️ VAD development possible with continued exposure")
    elif metrics['avg_level'] >= VAD_RISK_LEVELS['moderate']:
        overall_risk = "🟡 MODERATE VAD RISK"
        print(f"{overall_risk} - Residential ILFN exposure concern")
        print("   📋 Monitor for VAD Stage I symptoms")
    elif metrics['total_alerts'] > 0:
        overall_risk = "🟡 LOW-MODERATE RISK"
        print(f"{overall_risk} - Monitor symptoms, consider reduction")
    else:
        overall_risk = "🟢 LOW RISK"
        print(f"{overall_risk} - Continue monitoring")
    
    # VAD Stage Assessment
    if metrics['risk_hours'] > 0:
        vad_stage = get_vad_stage_assessment(metrics['risk_hours'], metrics['max_level'])
        if vad_stage:
            print(f"\n📋 POTENTIAL VAD STAGE: {vad_stage['name']}")
            print(f"   Description: {vad_stage['description']}")
            print("   Symptoms to monitor:")
            for symptom in vad_stage['symptoms'][:5]:
                print(f"      • {symptom}")
    
    # Frequency band analysis (VAD research)
    print(f"\n🎯 ILFN FREQUENCY BAND ANALYSIS")
    print("-" * 40)
    
    # Check for critical VAD frequencies
    alerts = df[df['Alerts'].str.contains('ALERT', na=False)]
    infrasound_count = 0
    cardiac_resonance_count = 0
    vestibular_count = 0
    
    for _, row in alerts.iterrows():
        try:
            freq = float(row['LFN Peak (Hz)'])
            if freq <= 20:
                infrasound_count += 1
            if 1 <= freq <= 8:
                cardiac_resonance_count += 1
            if 8 < freq <= 12:
                vestibular_count += 1
        except:
            continue
    
    if infrasound_count > 0:
        print(f"⚠️ Infrasound (<20 Hz) detections: {infrasound_count}")
        print("   Whole-body effects expected per VAD research")
    if cardiac_resonance_count > 0:
        print(f"💓 Cardiac resonance (1-8 Hz) detections: {cardiac_resonance_count}")
        print("   Pericardial/cardiac effects possible (Alves-Pereira)")
    if vestibular_count > 0:
        print(f"🌀 Vestibular band (8-12 Hz) detections: {vestibular_count}")
        print("   Balance/spatial orientation effects expected")
    
    # File-by-file analysis
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
                print(f"   📊 Level: {db_level:.1f} dB ({risk})")
                print(f"   ⚕️ VAD Impact: {impact}")
                
                # Medical recommendations
                recommendations = get_medical_recommendations(frequency, db_level, metrics['risk_hours'])
                if recommendations:
                    print(f"   📋 Recommendations:")
                    for rec in recommendations[:4]:  # Limit to top 4
                        print(f"      • {rec}")
                        
            except (ValueError, KeyError) as e:
                print(f"   ⚠️ Could not parse data for row {idx}: {e}")
                continue
    
    # VAD-specific compliance report
    print(f"\n📜 ILFN/VAD COMPLIANCE ASSESSMENT")
    print("-" * 40)
    print("⚠️ NOTE: Standard A-weighted limits do NOT protect against VAD")
    print("   (Alves-Pereira, 2007: A-weighting underestimates ILFN by 20-50 dB)")
    print()
    
    if metrics['total_alerts'] == 0:
        print("✅ No ILFN alerts detected")
    else:
        # VAD-specific thresholds
        if metrics['max_level'] > VAD_OCCUPATIONAL_LIMIT:
            print(f"🚨 VAD Occupational Limit EXCEEDED: {metrics['max_level']:.1f} dB > {VAD_OCCUPATIONAL_LIMIT} dB")
        elif metrics['max_level'] > VAD_MEDICAL_CONCERN:
            print(f"⚠️ VAD Medical Concern Level: {metrics['max_level']:.1f} dB > {VAD_MEDICAL_CONCERN} dB")
        
        if metrics['avg_level'] > VAD_RESIDENTIAL_LIMIT:
            print(f"⚠️ VAD Residential Limit: {metrics['avg_level']:.1f} dB > {VAD_RESIDENTIAL_LIMIT} dB")
        else:
            print(f"✅ Below VAD Residential Concern: {metrics['avg_level']:.1f} dB ≤ {VAD_RESIDENTIAL_LIMIT} dB")
        
        # Traditional limits (for reference only)
        print("\n📋 Traditional Limits (A-weighted, less relevant for ILFN):")
        if metrics['max_level'] > WHO_NIGHT_LIMIT:
            print(f"   WHO Night: {metrics['max_level']:.1f} dB > {WHO_NIGHT_LIMIT} dB(A)")
        if metrics['max_level'] > MEDICAL_CONCERN:
            print(f"   Medical Consultation: {metrics['max_level']:.1f} dB > {MEDICAL_CONCERN} dB(A)")
    
    # Save detailed report
    report_data = {
        'analysis_date': datetime.now().isoformat(),
        'source_file': csv_file,
        'methodology': 'Vibroacoustic Disease (VAD) Assessment - Dr. Mariana Alves-Pereira Research',
        'overall_risk': overall_risk,
        'metrics': metrics,
        'vad_assessment': {
            'infrasound_detections': infrasound_count,
            'cardiac_resonance_detections': cardiac_resonance_count,
            'vestibular_detections': vestibular_count,
            'estimated_exposure_years': metrics['risk_hours'] / (365 * 16)
        },
        'compliance': {
            'vad_residential_compliant': bool(metrics['avg_level'] <= VAD_RESIDENTIAL_LIMIT),
            'vad_occupational_compliant': bool(metrics['max_level'] <= VAD_OCCUPATIONAL_LIMIT),
            'medical_evaluation_recommended': bool(metrics['max_level'] > VAD_MEDICAL_CONCERN),
            'who_night_compliant': bool(metrics['max_level'] <= WHO_NIGHT_LIMIT),
            'epa_day_compliant': bool(metrics['avg_level'] <= EPA_DAY_LIMIT)
        },
        'references': [
            'Alves-Pereira M, Castelo Branco NAA. "Vibroacoustic Disease." Noise & Health, 2004.',
            'Alves-Pereira M, Castelo Branco NAA. Progress in Biophysics and Molecular Biology, 2007.',
            'Alves-Pereira M. "Noise-induced extra-aural pathology." Aviation, Space, and Environmental Medicine, 1999.'
        ],
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
    report_file = os.path.join(output_dir, f"vad_health_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    try:
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"\n💾 VAD Assessment Report saved: {report_file}")
    except Exception as e:
        print(f"⚠️ Could not save report: {e}")
    
    print(f"\n{'='*70}")
    print("🏥 VAD Health Assessment Complete")
    print("📖 Based on Dr. Mariana Alves-Pereira's research on Vibroacoustic Disease")
    print("⚕️ Consult healthcare provider familiar with ILFN/VAD if concerned")
    print(f"{'='*70}\n")
    
    return report_data

def main():
    parser = argparse.ArgumentParser(
        description="LFN Health Impact Assessment Tool - Based on VAD Research",
        epilog="""
Scientific Basis: Dr. Mariana Alves-Pereira's Vibroacoustic Disease (VAD) research.
VAD is a whole-body pathology caused by chronic ILFN (Infrasound & Low-Frequency Noise) exposure.

Key References:
- Alves-Pereira M, Castelo Branco NAA. "Vibroacoustic Disease." Noise & Health, 2004.
- Alves-Pereira M. Progress in Biophysics and Molecular Biology, 2007.

IMPORTANT: A-weighted measurements severely underestimate ILFN exposure.
Use Linear or C-weighted measurements for accurate VAD risk assessment.
        """
    )
    parser.add_argument("path", nargs="?", help="CSV file or directory to analyze")
    parser.add_argument("--output-dir", "-o", default=".", help="Output directory for reports")
    parser.add_argument("--auto-find", "-a", action="store_true", help="Auto-find CSV files")
    parser.add_argument("--spectrograms", "-s", action="store_true", help="Analyze spectrograms")
    
    args = parser.parse_args()
    
    print("🏥 LFN/ILFN Health Impact Assessment Tool")
    print("=" * 60)
    print("📖 Based on Dr. Mariana Alves-Pereira's VAD Research")
    print("   Vibroacoustic Disease (VAD) Assessment Protocol")
    print("=" * 60)
    
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