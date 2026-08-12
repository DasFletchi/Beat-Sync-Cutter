# Beat-Sync Cutter 🎬🎵

Automatically cut and sync cinematics (or any video footage) to audio beats, transients, kick drums, and synth drops using Python, **Librosa** audio onset detection, and **FFmpeg**.

---

## 🌟 Features
- **True Transient & Beat Onset Detection:** Uses `librosa.onset` to detect actual audio hits (kicks, snares, synth drops) instead of rigid grid BPM.
- **Dynamic Scene Switching:** Swaps camera angles and cinematics on every hit.
- **Fast & Efficient Rendering:** Lightweight encoding settings with configurable resolutions.
- **Automatic Audio Overlay:** Merges the original audio track perfectly synced to the new cut sequence.

---

## 📋 Requirements & Installation

Make sure you have `ffmpeg` installed on your system:
```bash
sudo apt install ffmpeg
```

Install Python dependencies:
```bash
pip install librosa numpy soundfile
```

---

## 🚀 Quick Start

Run the script by providing your video clips and audio track:

```bash
python beat_sync_cutter.py --video "/path/to/minecraft_cinematic.webm" --audio "/path/to/song.mp3" --output "synced_edit.mp4"
```

### Options

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--video` | `-v` | Path to source video file | *Required* |
| `--audio` | `-a` | Path to input audio file | *Required* |
| `--output` | `-o` | Output file path | `output_synced.mp4` |
| `--min-cut-dur` | | Minimum clip cut length in seconds | `0.35` |
| `--scale` | | FFmpeg video scale resolution | `1280:-2` |

---

## 📜 License
MIT License
