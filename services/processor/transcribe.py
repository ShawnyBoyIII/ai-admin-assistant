import os
from pathlib import Path


def transcribe_audio(audio_path: Path) -> str:
    """
    Transcription with diarization (speaker separation).
    Uses faster-whisper for transcription and pyannote.audio for diarization.
    """
    try:
        from faster_whisper import WhisperModel
        from pyannote.audio import Pipeline
        import torch
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

        # Collect transcribed segments with their start and end times
        whisper_segments = []
        for seg in segments:
            if seg.text.strip():
                whisper_segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip()
                })

        hf_token = os.getenv("HF_TOKEN")

        if not hf_token:
            print("HF_TOKEN not found in .env, skipping diarization.")
            text = "\n".join([seg["text"] for seg in whisper_segments])
            if not text:
                print("Warning: Transcription resulted in empty text.")
            return text or ""

        print(f"Running speaker diarization on {audio_path.name}...")
        try:
            diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=hf_token
            )

            # Use GPU for diarization if available
            if device == "cuda":
                diarization_pipeline.to(torch.device("cuda"))

            diarization_result = diarization_pipeline(str(audio_path))

            # The result is a DiarizeOutput object, we want the annotation part
            if hasattr(diarization_result, "speaker_diarization"):
                annotation = diarization_result.speaker_diarization
            else:
                annotation = diarization_result

            # Identify personal voice if reference audio exists
            from pyannote.audio import Model, Inference
            from scipy.spatial.distance import cdist

            user_speaker_label = None
            reference_audio_path = Path("reference_voice.wav")

            if reference_audio_path.exists():
                try:
                    print("Loading embedding model for personal voice detection...")
                    emb_model = Model.from_pretrained("pyannote/embedding", token=hf_token)
                    if device == "cuda":
                        emb_model.to(torch.device("cuda"))
                    inference = Inference(emb_model, window="whole")

                    # Get embedding for the reference voice
                    reference_emb = inference(str(reference_audio_path))

                    # Get embeddings for each detected speaker in the diarization
                    speaker_embeddings = {}
                    from pyannote.core import Segment

                    for speaker in annotation.labels():
                        # Extract audio segments for this speaker
                        speaker_timeline = annotation.label_timeline(speaker)
                        if len(speaker_timeline) > 0:
                            # We can just use the longest segment for a quick embedding, or average them.
                            # For simplicity, let's take the first segment that is at least 2 seconds long,
                            # or the longest segment if none are 2 seconds.
                            segments = list(speaker_timeline)
                            segments.sort(key=lambda s: s.duration, reverse=True)
                            longest_segment = segments[0]

                            # Extract the embedding for this specific segment
                            # For Inference with `window="whole"`, we can pass an excerpt
                            # using a cropped audio dict
                            from pyannote.audio.core.io import Audio
                            audio_io = Audio()
                            waveform, sample_rate = audio_io.crop(str(audio_path), longest_segment)

                            # Reshape for inference (1, channels, samples)
                            emb = inference({"waveform": waveform, "sample_rate": sample_rate})
                            speaker_embeddings[speaker] = emb

                    # Compare reference embedding to speaker embeddings using cosine distance
                    if speaker_embeddings:
                        best_speaker = None
                        best_distance = float("inf")

                        # Reshape reference for cdist
                        ref_emb_reshaped = reference_emb.reshape(1, -1)

                        for speaker, emb in speaker_embeddings.items():
                            emb_reshaped = emb.reshape(1, -1)
                            # Cosine distance: 0 means identical, 1 means orthogonal
                            distance = cdist(ref_emb_reshaped, emb_reshaped, metric="cosine")[0][0]
                            if distance < best_distance:
                                best_distance = distance
                                best_speaker = speaker

                        # Threshold for matching (e.g., 0.3 or 0.4)
                        if best_distance < 0.4:
                            print(f"Personal voice detected! Identified as {best_speaker} (Distance: {best_distance:.3f})")
                            user_speaker_label = best_speaker
                        else:
                            print(f"No strong match for personal voice. Closest was {best_speaker} (Distance: {best_distance:.3f})")

                except Exception as e:
                    print(f"Personal voice detection failed: {e}")


            diarization_segments = []
            for turn, _, speaker in annotation.itertracks(yield_label=True):
                # Replace the generic speaker label with "You" if it matches
                display_speaker = "You" if speaker == user_speaker_label else speaker
                diarization_segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": display_speaker
                })

            # Align whisper segments with diarization segments
            # A simple intersection approach: assign the speaker who speaks the most during the segment
            final_text = []
            for w_seg in whisper_segments:
                w_start = w_seg["start"]
                w_end = w_seg["end"]

                speaker_durations = {}
                for d_seg in diarization_segments:
                    d_start = d_seg["start"]
                    d_end = d_seg["end"]

                    # Calculate overlap
                    overlap_start = max(w_start, d_start)
                    overlap_end = min(w_end, d_end)
                    overlap = max(0, overlap_end - overlap_start)

                    if overlap > 0:
                        speaker = d_seg["speaker"]
                        speaker_durations[speaker] = speaker_durations.get(speaker, 0) + overlap

                if speaker_durations:
                    # Find speaker with max overlap
                    best_speaker = max(speaker_durations.items(), key=lambda x: x[1])[0]
                    final_text.append(f"[{best_speaker}] {w_seg['text']}")
                else:
                    final_text.append(f"[Unknown Speaker] {w_seg['text']}")

            text = "\n".join(final_text)
            if not text:
                print("Warning: Transcription resulted in empty text.")
            return text or ""

        except Exception as e:
            print(f"Diarization failed: {e}. Returning plain transcript.")
            text = "\n".join([seg["text"] for seg in whisper_segments])
            return text or ""

    except ImportError as exc:
        raise RuntimeError(f"Transcription dependency missing for {audio_path}: {exc}") from exc
    except Exception as exc:
        print(f"Error during transcription: {exc}")
        # Reraise exception to fail the job rather than silently succeeding with a stub
        raise
