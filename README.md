# 🎬 Minecraft Beat-Sync Cutter 🎵

Schneidet deine **Minecraft Cinematics** (oder beliebige Videos) automatisch **haargenau auf den Beat, die Kicks und Synth-Drops** deines Lieblingssongs!

Kein manuelles Schneiden in Premiere Pro, DaVinci Resolve oder CapCut nötig. Ein Befehl reicht und das Video ist perfekt auf die Musik synchronisiert. 🚀

---

## 🐣 Schritt-für-Schritt Anleitung für Einsteiger / Anfänger

Du hast noch nie mit Python oder dem Terminal gearbeitet? Kein Problem! Befolge einfach diese einfachen Schritte:

### 1️⃣ Voraussetzungen installieren

#### 🐧 Auf Linux (Ubuntu/Debian)
Öffne dein Terminal (Strg + Alt + T) und füg diesen Befehl ein:
```bash
sudo apt update && sudo apt install -y python3 python3-pip ffmpeg git
```

#### 🪟 Auf Windows
1. Lade dir [Python](https://www.python.org/downloads/) herunter (Haken bei **"Add Python to PATH"** bei der Installation aktivieren!).
2. Lade dir [FFmpeg](https://ffmpeg.org/download.html) herunter und füge es zu deinen Umgebungsvariablen hinzu.

---

### 2️⃣ Dieses Projekt herunterladen (Klonen)

Öffne dein Terminal / die Eingabeaufforderung und führe aus:

```bash
git clone https://github.com/DasFletchi/Minecraft-Beat-Sync-Cutter.git
cd Minecraft-Beat-Sync-Cutter
```

---

### 3️⃣ Benötigte Pakete installieren

Führe folgenden Befehl im Ordner aus:

```bash
pip install librosa numpy soundfile
```
*(Falls eine Meldung bezüglich "externally-managed-environment" kommt, erstelle ein venv mit `python3 -m venv venv && source venv/bin/activate`)*

---

### 4️⃣ Video synchronisieren (Der Zauberbefehl ✨)

Kopiere dein **Video** und dein **Audio/Song** in den gleichen Ordner oder erstelle deine Dateien an einem beliebigen Ort.

Führe dann einfach den Befehl aus:

```bash
python beat_sync_cutter.py --video "DeinMinecraftVideo.mp4" --audio "DeinSong.mp3" --output "MeinFertigesBeatVideo.mp4"
```

> 💡 **Tipp:** Wenn deine Dateinamen Leerzeichen enthalten, setze sie immer in Anführungszeichen `" "` (wie oben gezeigt).

---

## ⚙️ Einstellungen & Optionen (Optional)

Wenn du das Verhalten anpassen möchtest, kannst du folgende Zusatz-Parameter an den Befehl anhängen:

| Parameter | Beschreibung | Beispiel |
|-----------|--------------|----------|
| `--video` / `-v` | **(Pflicht)** Pfad zu deinem Video | `--video "video.mp4"` |
| `--audio` / `-a` | **(Pflicht)** Pfad zu deiner Audiodatei | `--audio "song.mp3"` |
| `--output` / `-o` | Name des fertigen Videos | `--output "result.mp4"` |
| `--min-cut-dur` | Mindestlänge eines Clips in Sekunden (verhindert zu schnelles Flackern) | `--min-cut-dur 0.4` |
| `--scale` | Auflösung des Ausgabevideos (z.B. `1920:-2` für Full HD) | `--scale 1920:-2` |

---

## 📜 Lizenz
MIT License - Kostenlos nutzbar & anpassbar!
