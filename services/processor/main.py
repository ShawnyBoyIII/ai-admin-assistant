import argparse
import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from pipeline import process_audio_file

AUDIO_EXTENSIONS = (".wav", ".mp3", ".m4a", ".flac")


def ensure_output_dirs(base: Path):
    (base / "jobs").mkdir(parents=True, exist_ok=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_status(job_dir: Path, audio_file: Path, state: str, error: str | None = None):
    status = {
        "audio_file": str(audio_file),
        "state": state,
        "updated_at_utc": utc_now_iso(),
    }
    if error:
        status["error"] = error
    (job_dir / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")


def discover_audio_files(input_dir: Path):
    return sorted([p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS])


def is_job_done(job_dir: Path) -> bool:
    status_path = job_dir / "status.json"
    if not status_path.exists():
        return False
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
        return status.get("state") == "done"
    except json.JSONDecodeError:
        return False


def process_one_file(audio_file: Path, output_dir: Path, force: bool = False) -> str:
    job_id = audio_file.stem
    job_dir = output_dir / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    if is_job_done(job_dir) and not force:
        print(f"Skipping {audio_file.name}: already done.")
        return "skipped"

    write_status(job_dir, audio_file, "received")
    write_status(job_dir, audio_file, "processing")
    print(f"Processing {audio_file.name}...")

    try:
        result = process_audio_file(audio_file, job_dir)
        result["processed_at_utc"] = utc_now_iso()
        (job_dir / "job_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        write_status(job_dir, audio_file, "done")
        print(f"Done: {job_dir}")
        return "done"
    except Exception:
        err = traceback.format_exc()
        (job_dir / "error.log").write_text(err, encoding="utf-8")
        write_status(job_dir, audio_file, "failed", error=err.splitlines()[-1] if err else "Unknown error")
        print(f"Failed: {job_dir}")
        return "failed"


def run_once(input_dir: Path, output_dir: Path, force: bool = False):
    ensure_output_dirs(output_dir)
    input_dir.mkdir(parents=True, exist_ok=True)
    audio_files = discover_audio_files(input_dir)

    if not audio_files:
        print(f"No audio files found in {input_dir}")
        return

    for audio_file in audio_files:
        process_one_file(audio_file, output_dir, force=force)


def run_watch(input_dir: Path, output_dir: Path, poll_seconds: int, force: bool = False):
    ensure_output_dirs(output_dir)
    input_dir.mkdir(parents=True, exist_ok=True)
    print(f"Watching {input_dir} every {poll_seconds}s for audio files...")
    print("Press Ctrl+C to stop.")
    seen_versions = set()

    try:
        while True:
            audio_files = discover_audio_files(input_dir)
            for audio_file in audio_files:
                version_key = (str(audio_file.resolve()), audio_file.stat().st_mtime_ns)
                if version_key in seen_versions and not force:
                    continue
                outcome = process_one_file(audio_file, output_dir, force=force)
                if outcome in {"done", "skipped"} and not force:
                    seen_versions.add(version_key)
            time.sleep(poll_seconds)
    except KeyboardInterrupt:
        print("Watch stopped by user.")


def parse_args():
    parser = argparse.ArgumentParser(description="AI Admin Assistant processor")
    parser.add_argument("--input", required=True, help="Folder containing wav files")
    parser.add_argument("--output", required=True, help="Folder to write outputs")
    parser.add_argument("--watch", action="store_true", help="Continuously watch input folder for new files")
    parser.add_argument("--poll-seconds", type=int, default=5, help="Polling interval for --watch mode")
    parser.add_argument("--force", action="store_true", help="Reprocess jobs even if status is done")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    if args.watch:
        run_watch(input_dir, output_dir, poll_seconds=max(1, args.poll_seconds), force=args.force)
    else:
        run_once(input_dir, output_dir, force=args.force)
