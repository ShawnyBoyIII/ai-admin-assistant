import json
import re
from pathlib import Path

from doc_builder import build_docx
from transcribe import transcribe_audio


ACTION_KEYWORDS = [
    "action",
    "follow up",
    "follow-up",
    "send",
    "review",
    "prepare",
    "draft",
    "schedule",
    "confirm",
    "update",
    "share",
    "finalize",
    "deliver",
    "submit",
    "need to",
    "we need",
    "i will",
]

TIME_KEYWORDS = [
    "today",
    "tomorrow",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "next week",
    "eod",
    "end of day",
    "by ",
    "before ",
]

HIGH_PRIORITY_KEYWORDS = ["asap", "urgent", "blocker", "critical", "today", "eod", "end of day"]
MEDIUM_PRIORITY_KEYWORDS = [
    "tomorrow",
    "this week",
    "next week",
    "follow up",
    "review",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "by ",
]


def split_lines(transcript_text: str):
    raw_lines = [ln.strip(" -\t") for ln in transcript_text.splitlines() if ln.strip()]
    return [ln for ln in raw_lines if "transcription unavailable" not in ln.lower()]


def infer_priority(line: str) -> str:
    lowered = line.lower()
    if any(token in lowered for token in HIGH_PRIORITY_KEYWORDS):
        return "High"
    if any(token in lowered for token in MEDIUM_PRIORITY_KEYWORDS):
        return "Medium"
    return "Low"


def infer_owner(line: str) -> str:
    lowered = line.lower()
    if "i will" in lowered or lowered.startswith("i "):
        return "You"
    if "we " in lowered or "team" in lowered:
        return "Team"

    name_match = re.search(r"\b([A-Z][a-z]+)\s+(?:will|to|needs to|should)\b", line)
    if name_match:
        return name_match.group(1)
    return "You"


def normalize_task_text(line: str) -> str:
    text = re.sub(r"^(action item|todo|to do)\s*[:\-]\s*", "", line, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:220]


def extract_tasks(lines):
    selected = []
    seen = set()

    for line in lines:
        lowered = line.lower()
        if any(keyword in lowered for keyword in ACTION_KEYWORDS):
            task_text = normalize_task_text(line)
            task_key = task_text.lower()
            if task_key and task_key not in seen:
                seen.add(task_key)
                selected.append(task_text)

    if not selected:
        selected = [normalize_task_text(line) for line in lines[:5]]

    tasks = []
    for idx, task_text in enumerate(selected[:20], start=1):
        tasks.append(
            {
                "id": idx,
                "task": task_text,
                "priority": infer_priority(task_text),
                "owner": infer_owner(task_text),
            }
        )
    return tasks


def infer_when(line: str) -> str:
    lowered = line.lower()
    if "today" in lowered or "eod" in lowered or "end of day" in lowered:
        return "Today"
    if "tomorrow" in lowered:
        return "Tomorrow"
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        if day.lower() in lowered:
            return day
    if "next week" in lowered:
        return "Next week"
    if "this week" in lowered:
        return "This week"

    by_match = re.search(r"\bby ([A-Za-z0-9 ,:/-]+)", line, flags=re.IGNORECASE)
    if by_match:
        return f"By {by_match.group(1).strip()[:30]}"
    return "TBD"


def extract_reminders(lines):
    reminders = []
    seen = set()
    for line in lines:
        lowered = line.lower()
        if any(token in lowered for token in TIME_KEYWORDS) and any(
            action in lowered for action in ACTION_KEYWORDS
        ):
            key = lowered[:180]
            if key in seen:
                continue
            seen.add(key)
            reminders.append(
                {
                    "when": infer_when(line),
                    "text": normalize_task_text(line),
                }
            )
    if not reminders:
        reminders.append(
            {
                "when": "Tomorrow 9:00 AM",
                "text": "Review generated tasks and send critical emails",
            }
        )
    return reminders[:10]


def build_summary(lines):
    if not lines:
        return "No transcript content available."
    if len(lines) <= 6:
        return " ".join(lines)
    return " ".join(lines[:4]) + " ... " + " ".join(lines[-2:])


def build_email_drafts(summary: str, tasks):
    task_lines = "\n".join([f"- {item['task']}" for item in tasks[:5]]) or "- No major action items captured."
    recap_body = (
        "Hi Team,\n\n"
        "Here is a quick recap from our discussion:\n"
        f"{summary}\n\n"
        "Proposed next steps:\n"
        f"{task_lines}\n\n"
        "Please reply if any updates are needed.\n\n"
        "Thanks,"
    )

    status_body = (
        "Hi,\n\n"
        "Status update draft:\n"
        f"- Total action items identified: {len(tasks)}\n"
        f"- High priority items: {len([t for t in tasks if t['priority'] == 'High'])}\n\n"
        "I will proceed with the actions above unless priorities change.\n\n"
        "Thanks,"
    )

    return [
        {"subject": "Follow-up on discussion items", "body": recap_body},
        {"subject": "Status update and next steps", "body": status_body},
    ]


def generate_admin_pack(transcript_text: str):
    lines = split_lines(transcript_text)
    summary = build_summary(lines)
    tasks = extract_tasks(lines)
    reminders = extract_reminders(lines)
    email_drafts = build_email_drafts(summary, tasks)

    return {"summary": summary, "tasks": tasks, "reminders": reminders, "email_drafts": email_drafts}


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
