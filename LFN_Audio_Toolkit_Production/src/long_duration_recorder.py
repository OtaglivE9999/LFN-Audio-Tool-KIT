"""
Long Duration Recording Solution
===============================

Memory-efficient recording for 8+ hour sessions using file segmentation
and real-time processing to avoid memory overflow.
"""
# -*- coding: utf-8 -*-
import sys

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

import numpy as np
import soundfile as sf
import sounddevice as sd
import os
import time
from datetime import datetime, timedelta
import logging
import threading
import queue

class LongDurationRecorder:
    """
    Memory-efficient recorder for 8+ hour sessions
    Records in segments and processes incrementally
    """
    
    def __init__(self, sample_rate=48000, channels=2, segment_duration=1800):
        """
        Initialize long duration recorder
        
        Args:
            sample_rate: Audio sample rate (48kHz recommended)
            channels: Number of audio channels (2 for stereo)
            segment_duration: Duration of each file segment in seconds (default: 30 minutes)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.segment_duration = segment_duration  # 30 minutes per segment
        self.is_recording = False
        self.audio_queue = queue.Queue(maxsize=10)  # Limit queue size
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def record_long_session(self, total_duration_hours, output_dir="long_recording", device=None):
        """
        Record for many hours using segmented files
        
        Args:
            total_duration_hours: Total recording time in hours (e.g., 8.0 for 8 hours)
            output_dir: Directory to save recording segments
            device: Audio device ID (None for default)
        """
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        total_duration_seconds = total_duration_hours * 3600
        segments_needed = int(np.ceil(total_duration_seconds / self.segment_duration))
        
        self.logger.info(f"Starting {total_duration_hours} hour recording session")
        self.logger.info(f"Recording will be split into {segments_needed} segments of {self.segment_duration/60:.1f} minutes each")
        
        # Memory usage estimate
        segment_memory_gb = (self.segment_duration * self.sample_rate * self.channels * 4) / (1024**3)
        self.logger.info(f"Memory usage per segment: {segment_memory_gb:.2f} GB (safe for processing)")
        
        self.is_recording = True
        start_time = datetime.now()
        
        # Start audio capture thread
        capture_thread = threading.Thread(
            target=self._audio_capture_worker,
            args=(device, total_duration_seconds)
        )
        capture_thread.start()
        
        # Process segments as they're captured
        segment_count = 0
        try:
            while self.is_recording and segment_count < segments_needed:
                try:
                    # Get next audio segment from queue (with timeout)
                    audio_data = self.audio_queue.get(timeout=60)  # 1 minute timeout
                    
                    if audio_data is None:  # End signal
                        break
                        
                    # Generate filename with timestamp
                    current_time = start_time + timedelta(seconds=segment_count * self.segment_duration)
                    filename = f"recording_segment_{segment_count+1:03d}_{current_time.strftime('%Y%m%d_%H%M%S')}.wav"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Apply EMM6 correction in chunks (memory-efficient)
                    corrected_audio = self._apply_emm6_correction_chunked(audio_data)
                    
                    # Save segment to file
                    sf.write(filepath, corrected_audio.T, self.sample_rate)
                    
                    segment_count += 1
                    elapsed_hours = segment_count * self.segment_duration / 3600
                    remaining_hours = total_duration_hours - elapsed_hours
                    
                    self.logger.info(f"Saved segment {segment_count}/{segments_needed} - "
                                   f"Elapsed: {elapsed_hours:.1f}h, Remaining: {remaining_hours:.1f}h")
                    
                    # Clean up memory
                    del audio_data, corrected_audio
                    
                except queue.Empty:
                    self.logger.warning("Audio queue timeout - checking if recording is still active")
                    continue
                    
        except KeyboardInterrupt:
            self.logger.info("Recording interrupted by user")
        except Exception as e:
            self.logger.error(f"Error during recording: {e}")
        finally:
            self.is_recording = False
            capture_thread.join()
            
        end_time = datetime.now()
        actual_duration = (end_time - start_time).total_seconds() / 3600
        
        self.logger.info(f"Recording session complete!")
        self.logger.info(f"Planned duration: {total_duration_hours:.1f} hours")
        self.logger.info(f"Actual duration: {actual_duration:.1f} hours")
        self.logger.info(f"Segments saved: {segment_count}")
        self.logger.info(f"Output directory: {os.path.abspath(output_dir)}")
        
        return output_dir, segment_count
    
    def _audio_capture_worker(self, device, total_duration):
        """Background thread for audio capture"""
        try:
            samples_per_segment = int(self.segment_duration * self.sample_rate)
            total_samples = int(total_duration * self.sample_rate)
            samples_captured = 0
            
            self.logger.info(f"Starting audio capture (device: {device})")
            
            with sd.InputStream(
                device=device,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=np.float32
            ) as stream:
                
                while self.is_recording and samples_captured < total_samples:
                    # Calculate how many samples to capture for this segment
                    remaining_samples = total_samples - samples_captured
                    current_segment_samples = min(samples_per_segment, remaining_samples)
                    
                    # Capture audio segment
                    audio_data, overflowed = stream.read(current_segment_samples)
                    
                    if overflowed:
                        self.logger.warning("Audio buffer overflow detected")
                    
                    # Convert to (channels, samples) format
                    if audio_data.ndim == 1:
                        audio_segment = audio_data.reshape(-1, 1).T
                    else:
                        audio_segment = audio_data.T
                    
                    # Add to queue (this will block if queue is full)
                    self.audio_queue.put(audio_segment)
                    
                    samples_captured += current_segment_samples
                    
        except Exception as e:
            self.logger.error(f"Audio capture error: {e}")
        finally:
            # Signal end of recording
            self.audio_queue.put(None)
            self.logger.info("Audio capture thread finished")
    
    def _apply_emm6_correction_chunked(self, audio, chunk_size=1048576):
        """
        Apply EMM6 correction using chunked processing to avoid memory issues
        """
        from scipy import signal
        
        if audio is None or audio.size == 0:
            return audio
        
        channels, samples = audio.shape
        
        # Design filter once
        sos_lowcut = signal.butter(2, 10, btype='highpass', fs=self.sample_rate, output='sos')
        
        # Process in chunks
        filtered = np.zeros_like(audio, dtype=np.float32)
        
        num_chunks = (samples + chunk_size - 1) // chunk_size
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min(start_idx + chunk_size, samples)
            
            for ch in range(channels):
                chunk = audio[ch, start_idx:end_idx]
                
                if len(chunk) > 100:  # Only filter if chunk is large enough
                    try:
                        filtered[ch, start_idx:end_idx] = signal.sosfilt(sos_lowcut, chunk)
                    except (ValueError, RuntimeError) as e:
                        # If filter fails, use original chunk
                        filtered[ch, start_idx:end_idx] = chunk
                else:
                    filtered[ch, start_idx:end_idx] = chunk
        
        return filtered

def main():
    """Example usage for long duration recording"""
    
    # Calculate safe parameters
    print("Long Duration Recording Setup")
    print("=" * 40)
    
    # Show memory comparison
    durations = [1, 4, 8, 12, 24]  # hours
    print("\nMemory usage comparison:")
    print("Duration | Monolithic | Segmented (30min)")
    print("-" * 45)
    
    for hours in durations:
        samples = hours * 3600 * 48000
        monolithic_gb = (samples * 2 * 4) / (1024**3)
        segmented_gb = (30 * 60 * 48000 * 2 * 4) / (1024**3)
        
        print(f"{hours:2d} hours  | {monolithic_gb:8.1f} GB | {segmented_gb:8.1f} GB")
    
    print(f"\n✅ Segmented recording uses constant ~1.3 GB regardless of duration!")
    print(f"🚀 Can record for days without memory issues!")
    
    # Example recording
    print(f"\nExample: 8-hour recording session")
    recorder = LongDurationRecorder(segment_duration=1800)  # 30-minute segments
    
    # This would actually start recording:
    # recorder.record_long_session(8.0, "night_recording_8h")

if __name__ == "__main__":
    main()