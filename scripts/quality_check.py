import json
from pathlib import Path
import sys


def load_pipeline_module(project_root: Path):
    processor_dir = project_root / 'services' / 'processor'
    sys.path.insert(0, str(processor_dir))
    from pipeline import generate_admin_pack
    return generate_admin_pack


def main():
    project_root = Path(__file__).resolve().parents[1]
    generate_admin_pack = load_pipeline_module(project_root)

    sample_transcript = (
        "We need to finalize the BRD by Friday and send it to the client.\n"
        "I will draft the follow-up email today.\n"
        "Please review the acceptance criteria tomorrow morning.\n"
        "Team should schedule a checkpoint next week.\n"
        "Action item: update RAID log before end of day."
    )

    pack = generate_admin_pack(sample_transcript)

    assert pack.get('summary'), 'Missing summary'
    assert len(pack.get('tasks', [])) >= 3, 'Expected at least 3 tasks'
    assert len(pack.get('email_drafts', [])) >= 1, 'Expected at least 1 email draft'
    assert len(pack.get('reminders', [])) >= 1, 'Expected at least 1 reminder'

    high_priorities = [t for t in pack['tasks'] if t.get('priority') == 'High']
    assert high_priorities, 'Expected at least one high priority task'

    output_path = project_root / 'output' / 'quality_check_result.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(pack, indent=2), encoding='utf-8')
    print('Quality check passed.')


if __name__ == '__main__':
    main()
