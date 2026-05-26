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

## Continuous Processing (Computer B)
```bash
python3 services/processor/main.py --input ./dropbox_in --output ./output --watch --poll-seconds 5
```
Job states are written to `output/jobs/<job_id>/status.json` with:
- `received`
- `processing`
- `done`
- `failed`

## Health Check
```bash
cd ai-admin-assistant
source .venv/bin/activate
python scripts/health_check.py --project-root .
python scripts/quality_check.py
```

## Optional GPU Transcription & Speaker Diarization (Windows RTX machine)
Install optional dependencies on Computer B:
```powershell
pip install -r requirements-gpu-transcription.txt
```

To enable **Speaker Diarization** (separating speakers like "SPEAKER_00" and "SPEAKER_01") and **Personal Voice Detection** (automatically renaming your voice to "You"):
1. Create an account on [Hugging Face](https://huggingface.co/) and generate a read-only Access Token.
2. Visit the following links while logged into Hugging Face and accept their user agreements:
   - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
   - [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
   - [pyannote/embedding](https://huggingface.co/pyannote/embedding) (For personal voice detection)
3. Add your token to your `.env` file: `HF_TOKEN=your_token_here`
4. *(Optional)* Place a short (10-30 second) recording of your own voice in the project root named `reference_voice.wav`. The pipeline will use this to identify and label your tasks specifically as "You".

## Local LLM Extraction Setup (Optional but Recommended)
To improve task extraction, summarization, and email drafting quality without sending your private transcripts to the cloud, this project supports [Ollama](https://ollama.com/) for entirely local processing.
1. Download and install [Ollama](https://ollama.com/).
2. Open a terminal and pull the Llama 3 model:
   ```bash
   ollama run llama3
   ```
3. Update your `.env` file to enable it (enabled by default):
   ```env
   USE_OLLAMA=true
   OLLAMA_URL=http://localhost:11434/api/generate
   OLLAMA_MODEL=llama3
   ```
4. If Ollama is unavailable or errors out, the pipeline will seamlessly fallback to rule-based keyword extraction.

## Recording Disclaimer
See [Recording Disclaimer](docs/recording_disclaimer.md) before using microphone capture.

## Future Enhancements
- Further tuning of LLM prompts for multi-speaker task prioritization.

## Windows Transfer
Use `docs/windows_setup.md` for deployment on both machines.
Use `docs/uat_test_plan.md` for the 2-3 day UAT checklist.

## MVP1 Status
- [x] Project scaffold
- [x] Recorder app scaffold with timed recording + save
- [x] Processing pipeline scaffold (transcribe -> generate -> export)
- [x] Continuous folder watch + job status tracking
- [x] Rule-based admin extraction quality pass
- [x] Word export + JSON/text outputs
- [ ] Model wiring and production tuning on RTX machine
