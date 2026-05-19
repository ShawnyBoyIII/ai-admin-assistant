import os
from pathlib import Path


def transcribe_audio(audio_path: Path) -> str:
    """
    MVP1 stub transcription path.
    If faster-whisper is installed and model downloads are configured,
    replace with GPU-enabled transcription in production setup.
    """
    try:
        from faster_whisper import WhisperModel
        from dotenv import load_dotenv

        load_dotenv()
        model_size = os.getenv("WHISPER_MODEL_SIZE", "small")
        device = os.getenv("WHISPER_DEVICE", "auto")
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "auto")

        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        segments, _info = model.transcribe(str(audio_path), beam_size=5)
        text = "\n".join([seg.text.strip() for seg in segments if seg.text.strip()])
        return text or ""
    except Exception as exc:
        return f"[Transcription unavailable in current environment: {exc}]"
