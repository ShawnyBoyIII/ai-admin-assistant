import argparse
import subprocess
import sys
import wave
import math
import struct
from pathlib import Path


REQUIRED_OUTPUTS = [
    'transcript.txt',
    'summary.txt',
    'tasks.json',
    'reminders.json',
    'emails_draft.json',
    'AI_Admin_Assistant_Output.docx',
    'job_result.json',
]


def create_smoke_wav(path: Path, seconds: int = 2, sample_rate: int = 16000):
    path.parent.mkdir(parents=True, exist_ok=True)
    amp = 12000
    with wave.open(str(path), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for i in range(sample_rate * seconds):
            val = int(amp * math.sin(2 * math.pi * 440 * i / sample_rate))
            wav.writeframes(struct.pack('<h', val))


def run_processor(project_root: Path, input_dir: Path, output_dir: Path):
    cmd = [
        sys.executable,
        str(project_root / 'services' / 'processor' / 'main.py'),
        '--input',
        str(input_dir),
        '--output',
        str(output_dir),
    ]
    subprocess.run(cmd, check=True, cwd=project_root)


def assert_outputs(output_dir: Path, job_id: str):
    job_dir = output_dir / 'jobs' / job_id
    missing = [name for name in REQUIRED_OUTPUTS if not (job_dir / name).exists()]
    if missing:
        raise RuntimeError(f'Missing outputs in {job_dir}: {missing}')


def main():
    parser = argparse.ArgumentParser(description='AI Admin Assistant health check')
    parser.add_argument('--project-root', default='.', help='Project root folder')
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    input_dir = root / 'sample_audio'
    output_dir = root / 'output'
    smoke_path = input_dir / 'health_smoke.wav'

    create_smoke_wav(smoke_path)
    run_processor(root, input_dir, output_dir)
    assert_outputs(output_dir, 'health_smoke')
    print('Health check passed.')


if __name__ == '__main__':
    main()
