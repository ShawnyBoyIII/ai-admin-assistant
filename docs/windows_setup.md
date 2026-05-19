# Windows 11 Setup

## Laptop A (Recorder)
1. Install Python 3.11+
2. Open PowerShell in project folder
3. Run:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python apps\recorder\app.py
```
4. Allow microphone permission when prompted by Windows.

## Computer B (Processor, RTX 5070)
1. Install latest NVIDIA drivers + CUDA runtime
2. Install Python 3.11+
3. In PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-gpu-transcription.txt
copy .env.example .env
python services\processor\main.py --input .\dropbox_in --output .\output --watch --poll-seconds 5
```

## Transfer Options from A -> B
- Shared network folder (recommended MVP1)
- Synced folder (OneDrive/Dropbox)

Set recorder output directory to the shared inbound folder used by B.
