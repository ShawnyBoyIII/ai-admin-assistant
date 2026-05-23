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
        model_size = os.getenv("WHISPER_MODEL_SIZE", "base")

        # If device is auto, prefer cuda if available
        device = os.getenv("WHISPER_DEVICE", "auto")
        if device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                else:
                    device = "cpu"
            except ImportError:
                # If torch isn't installed, default to cpu or let faster_whisper decide
                pass

        # Better defaults for RTX cards
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "auto")
        if compute_type == "auto" and device == "cuda":
            compute_type = "float16" # Leverage RTX hardware

        print(f"Loading WhisperModel: size={model_size}, device={device}, compute_type={compute_type}")
        model = WhisperModel(model_size, device=device, compute_type=compute_type)

        print(f"Transcribing {audio_path.name}...")
        segments, _info = model.transcribe(str(audio_path), beam_size=5)
        text = "\n".join([seg.text.strip() for seg in segments if seg.text.strip()])

        if not text:
            print("Warning: Transcription resulted in empty text.")

        return text or ""
    except ImportError as exc:
        print(f"faster-whisper is not installed. Returning fallback transcription. Error: {exc}")
        return f"[Transcription unavailable: {exc}]"
    except Exception as exc:
        print(f"Error during transcription: {exc}")
        # Reraise exception to fail the job rather than silently succeeding with a stub
        raise
