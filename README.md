# AI Admin Assistant (MVP1)

AI Admin Assistant turns meeting/work audio into a ready-to-use admin pack:
- Actionable tasks
- Draft emails
- Reminder suggestions
- Summary notes
- Consolidated `.docx` output

## Architecture
- **Laptop A (Windows 11)**: Recorder app (`apps/recorder`)
- **Computer B (Windows 11 RTX rig)**: Processing service (`services/processor`)

## Quick Start (Mac dev)
```bash
cd ai-admin-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 services/processor/main.py --input ./sample_audio --output ./output
```

## Health Check
```bash
cd ai-admin-assistant
source .venv/bin/activate
python scripts/health_check.py --project-root .
```

## Optional GPU Transcription (Windows RTX machine)
Install optional dependencies on Computer B:
```powershell
pip install -r requirements-gpu-transcription.txt
```

## Windows Transfer
Use `docs/windows_setup.md` for deployment on both machines.

## MVP1 Status
- [x] Project scaffold
- [x] Recorder app scaffold with timed recording + save
- [x] Processing pipeline scaffold (transcribe -> generate -> export)
- [x] Word export + JSON/text outputs
- [ ] Model wiring and production tuning on RTX machine
