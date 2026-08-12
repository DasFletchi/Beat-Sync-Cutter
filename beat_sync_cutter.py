#!/usr/bin/env python3
"""
Minecraft Beat Sync Cutter
Automatically cuts and syncs video scenes to audio transient/beat onsets using Librosa and FFmpeg.
"""

import os
import sys
import argparse
import numpy as np
import librosa
import subprocess

def get_video_duration(video_path):
    cmd = ["ffprobe", "-i", video_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            hours, mins, secs = float(parts[0]), float(parts[1]), float(parts[2])
            return hours * 3600 + mins * 60 + secs
    return 0.0

def main():
    parser = argparse.ArgumentParser(description="Sync video scene cuts to audio beat/onset hits.")
    parser.add_argument("--video", "-v", required=True, help="Path to input video file (e.g., Minecraft Cinematics)")
    parser.add_argument("--audio", "-a", required=True, help="Path to input audio file (e.g., MP3/WAV track)")
    parser.add_argument("--output", "-o", default="output_synced.mp4", help="Path for synced output MP4 file")
    parser.add_argument("--min-cut-dur", type=float, default=0.35, help="Minimum cut duration in seconds (default: 0.35)")
    parser.add_argument("--scale", default="1280:-2", help="FFmpeg output scale resolution (default: 1280:-2)")
    args = parser.parse_args()

    video_file = os.path.abspath(args.video)
    audio_file = os.path.abspath(args.audio)
    output_file = os.path.abspath(args.output)

    if not os.path.exists(video_file):
        print(f"Error: Video file not found: {video_file}")
        sys.exit(1)
    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found: {audio_file}")
        sys.exit(1)

    print("🎵 Loading audio & analyzing musical onset strength...")
    y, sr = librosa.load(audio_file)
    audio_duration = librosa.get_duration(y=y, sr=sr)

    # Calculate local transient energy peaks
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
    
    # Peak pick for exact onset locations (kick/snare/synth hits)
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        backtrack=True,
        pre_max=3,
        post_max=3,
        pre_avg=3,
        post_avg=5,
        delta=0.07,
        wait=4
    )
    
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    print(f"⚡ Detected {len(onset_times)} raw audio hits.")

    # Filter out cuts shorter than min_cut_dur to maintain visual flow
    filtered_times = []
    last_t = -1.0
    for t in onset_times:
        if t - last_t >= args.min_cut_dur:
            filtered_times.append(t)
            last_t = t

    print(f"✂️ Filtered to {len(filtered_times)} sharp beat-synced cuts.")

    cut_times = [0.0] + filtered_times + [audio_duration]
    video_duration = get_video_duration(video_file)

    temp_dir = "/tmp/mc_cuts_cli"
    os.system(f"rm -rf {temp_dir} && mkdir -p {temp_dir}")

    segment_files = []
    concat_list_path = os.path.join(temp_dir, "concat.txt")

    src_cursor = 0.0
    print("🎬 Slicing video segments...")
    for i in range(len(cut_times) - 1):
        dur = cut_times[i+1] - cut_times[i]
        if dur <= 0.05:
            continue
        
        if src_cursor + dur > video_duration - 1.0:
            src_cursor = (src_cursor % 10.0)

        seg_out = os.path.join(temp_dir, f"cut_{i:04d}.mp4")
        cmd = [
            "ffmpeg", "-y", "-ss", f"{src_cursor:.3f}", "-i", video_file,
            "-t", f"{dur:.3f}", "-an",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-vf", f"scale={args.scale}",
            seg_out
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        segment_files.append(seg_out)

        src_cursor += dur + 3.1

    with open(concat_list_path, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")

    print("🚀 Concatenating cuts and syncing audio...")
    final_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_file
    ]
    res = subprocess.run(final_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        print(f"✅ SUCCESS: Synced video rendered to: {output_file}")
    else:
        print(f"❌ ERROR rendering final video:\n{res.stderr}")

if __name__ == "__main__":
    main()
