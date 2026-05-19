import argparse
import json
from datetime import datetime
from pathlib import Path

from pipeline import process_audio_file


def ensure_output_dirs(base: Path):
    (base / "jobs").mkdir(parents=True, exist_ok=True)


def run(input_dir: Path, output_dir: Path):
    ensure_output_dirs(output_dir)
    audio_files = sorted([p for p in input_dir.glob("*.wav")])

    if not audio_files:
        print(f"No .wav files found in {input_dir}")
        return

    for audio_file in audio_files:
        job_id = audio_file.stem
        job_dir = output_dir / "jobs" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        print(f"Processing {audio_file.name}...")

        result = process_audio_file(audio_file, job_dir)
        (job_dir / "job_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Done: {job_dir}")


def parse_args():
    parser = argparse.ArgumentParser(description="AI Admin Assistant processor")
    parser.add_argument("--input", required=True, help="Folder containing wav files")
    parser.add_argument("--output", required=True, help="Folder to write outputs")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(Path(args.input), Path(args.output))
