"""Make a local lossless 60 fps clip from the delivered native bottom-up RGBA sequence."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
FRAME = 940 * 528 * 4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=HERE/"private/225-254-bottom-up.rgba")
    parser.add_argument("--evidence", type=Path, default=HERE/"evidence")
    parser.add_argument("--out", type=Path, default=HERE/"private/kept-take-60fps.mkv")
    parser.add_argument("--preview", type=Path, help="Optional local lossy H.264 viewing copy")
    args = parser.parse_args()
    report = json.loads((args.evidence/"process-1/RUN.json").read_bytes())
    expected = report["trials"][0]["frame_digests"]
    with args.raw.open("rb") as f:
        for digest in expected:
            buf = f.read(FRAME)
            if len(buf) != FRAME or sha256(buf).hexdigest() != digest:
                raise ValueError("Native frame digest mismatch")
        if f.read(1) or len(expected) != 30:
            raise ValueError("Native frame sequence size mismatch")
    subprocess.run(["ffmpeg","-v","error","-n","-f","rawvideo","-pixel_format","rgba",
                    "-video_size","940x528","-framerate","60","-i",str(args.raw),
                    "-vf","vflip","-c:v","ffv1","-level","3","-threads","2",
                    "-pix_fmt","bgra",str(args.out)],check=True)
    verify = subprocess.Popen(["ffmpeg","-v","error","-i",str(args.out),"-vf","vflip",
                              "-threads","1","-f","rawvideo","-pix_fmt","rgba","pipe:1"],
                              stdout=subprocess.PIPE)
    try:
        with verify.stdout as f:
            actual = [sha256(f.read(FRAME)).hexdigest() for _ in expected]
            extra = f.read(1)
        if verify.wait() or extra or expected != actual:
            raise ValueError("Decoded local clip did not reproduce the delivered native frames")
    finally:
        if verify.poll() is None:
            verify.kill()
            verify.wait()
    print(f"Verified {len(expected)} lossless frames at 60 fps.")
    if args.preview:
        # The verified container already has display orientation. Decode to YUV
        # from that stream without any second flip or synthetic intermediate.
        subprocess.run(["ffmpeg","-v","error","-n","-i",str(args.out),"-an","-c:v","libx264",
                        "-threads","2","-crf","15","-pix_fmt","yuv420p","-movflags","+faststart",
                        str(args.preview)],check=True)
        probe = subprocess.check_output(["ffprobe","-v","error","-count_frames","-select_streams","v:0",
            "-show_entries","stream=width,height,r_frame_rate,nb_read_frames,duration","-of","json",
            str(args.preview)])
        [stream] = json.loads(probe)["streams"]
        if (stream["width"], stream["height"], stream["r_frame_rate"], stream["nb_read_frames"]) != (940,528,"60/1","30"):
            raise ValueError("Wrong playback geometry or cadence")
        if abs(float(stream["duration"]) - 0.5) > 1e-6:
            raise ValueError("Wrong preview duration")
        print("Verified local H.264 preview:", json.dumps(stream))


if __name__ == "__main__":
    main()
