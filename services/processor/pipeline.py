import json
from pathlib import Path

from doc_builder import build_docx
from transcribe import transcribe_audio


def generate_admin_pack(transcript_text: str):
    lines = [ln.strip() for ln in transcript_text.splitlines() if ln.strip()]

    tasks = []
    reminders = []
    email_drafts = []

    for i, line in enumerate(lines[:20], start=1):
        tasks.append(
            {
                "id": i,
                "task": f"Review and action: {line[:100]}",
                "priority": "Medium",
                "owner": "You",
            }
        )

    reminders.append({"when": "Tomorrow 9:00 AM", "text": "Review generated tasks and send critical emails"})

    email_drafts.append(
        {
            "subject": "Follow-up on discussion items",
            "body": "Hi Team,\n\nBased on today\'s discussion, please find the next steps attached.\n\nThanks,",
        }
    )

    summary = " ".join(lines[:8]) if lines else "No transcript content available."

    return {
        "summary": summary,
        "tasks": tasks,
        "reminders": reminders,
        "email_drafts": email_drafts,
    }


def process_audio_file(audio_path: Path, output_dir: Path):
    transcript_text = transcribe_audio(audio_path)
    (output_dir / "transcript.txt").write_text(transcript_text, encoding="utf-8")

    pack = generate_admin_pack(transcript_text)

    (output_dir / "summary.txt").write_text(pack["summary"], encoding="utf-8")
    (output_dir / "tasks.json").write_text(json.dumps(pack["tasks"], indent=2), encoding="utf-8")
    (output_dir / "reminders.json").write_text(json.dumps(pack["reminders"], indent=2), encoding="utf-8")
    (output_dir / "emails_draft.json").write_text(json.dumps(pack["email_drafts"], indent=2), encoding="utf-8")

    docx_path = output_dir / "AI_Admin_Assistant_Output.docx"
    build_docx(docx_path, pack)

    return {
        "audio_file": str(audio_path),
        "docx_output": str(docx_path),
        "status": "done",
    }
