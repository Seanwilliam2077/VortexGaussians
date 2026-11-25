"""Render individual Mandarin WAVs with the offline Windows desktop voice."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import wave


MANIFEST = Path(__file__).with_name("narration.json")
SPEAK = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $s.SelectVoice($env:VORTEX_NARRATOR)
    $s.Rate = [int]$env:VORTEX_SPEECH_RATE
    $fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(
        22050,
        [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
        [System.Speech.AudioFormat.AudioChannel]::Mono)
    $s.SetOutputToWaveFile($env:VORTEX_SCENE_WAV, $fmt)
    $s.Speak($env:VORTEX_SCENE_TEXT)
} finally {
    $s.Dispose()
}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Local directory for private WAVs")
    parser.add_argument("--scene", action="append", type=int, help="Repeat to select scenes; default is all")
    parser.add_argument("--update-durations", action="store_true", help="Record observed WAV durations")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    info = json.loads(MANIFEST.read_text(encoding="utf-8"))
    chosen = set(args.scene or (scene["id"] for scene in info["scenes"]))
    if chosen - {s["id"] for s in info["scenes"]}:
        parser.error("Unknown scene number")
    for scene in info["scenes"]:
        if scene["id"] not in chosen:
            continue
        if not scene["spoken"]:
            parser.error(f"Scene {scene['id']} has no approved result yet")
        output = (args.output / scene["wav"]).resolve()
        env = {**os.environ, "VORTEX_SCENE_TEXT": scene["spoken"],
               "VORTEX_SCENE_WAV": str(output), "VORTEX_NARRATOR": info["voice"],
               "VORTEX_SPEECH_RATE": str(info["speech_rate"])}
        subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", SPEAK],
                       env=env, check=True)
        with wave.open(str(output), "rb") as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 22050):
                raise ValueError(f"Unexpected format in {output.name}")
            scene["duration_seconds"] = round(wav.getnframes() / wav.getframerate(), 4)
        print(f"{output.name} {scene['duration_seconds']:.4f} s")
    if args.update_durations:
        MANIFEST.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
