# AI Admin Assistant - MVP1 UAT Plan (2-3 Days)

## UAT Goal
Validate end-to-end reliability and output usefulness for daily Business Analyst workflows.

## Test Environment
1. Laptop A: Windows 11 recorder app.
2. Computer B: Windows 11 processor service with shared input folder.
3. Use at least 6 recordings across different meeting types.

## Runbook Before UAT
1. Start processor watcher on Computer B:
   `python services\processor\main.py --input .\dropbox_in --output .\output --watch --poll-seconds 5`
2. Start recorder app on Laptop A:
   `python apps\recorder\app.py`
3. Confirm `.wav` files from Laptop A appear in `dropbox_in`.

## Day 1 - Functional Flow
1. Recording Consent Flow:
- Expected: consent prompt appears before recording starts.
- Pass: recording is blocked when consent is declined.

2. Timed Recording:
- Test with 2, 5, and 15 minutes.
- Pass: auto-stop triggers at configured duration and file is saved.

3. End-to-End Processing:
- Expected files per job folder:
  - `transcript.txt`
  - `summary.txt`
  - `tasks.json`
  - `reminders.json`
  - `emails_draft.json`
  - `AI_Admin_Assistant_Output.docx`
  - `status.json`
  - `job_result.json`
- Pass: `status.json` ends in `done` and all files exist.

## Day 2 - Output Quality
1. Task Quality:
- Pass if at least 70% of generated tasks are actionable and relevant.

2. Email Draft Quality:
- Pass if drafts need only light edits (tone, names, minor context).

3. Reminder Quality:
- Pass if reminder timing labels (`Today`, `Tomorrow`, weekdays, `Next week`) are mostly correct.

4. Summary Quality:
- Pass if summary reflects key discussion points and major decisions.

## Day 3 - Reliability and Edge Cases
1. Quiet/Noisy Audio:
- Run one low-volume test and one noisy environment test.
- Pass if system still completes and flags usable outputs.

2. Reprocessing Behavior:
- Re-run watcher with same file names.
- Pass if completed files are skipped unless `--force` is used.

3. Watcher Stability:
- Keep watcher running for at least 2 hours.
- Pass if no crash and new files are picked up automatically.

4. Failure Observation:
- Temporarily move or lock an input file during processing.
- Pass if job status is `failed` with `error.log` when an unhandled exception occurs.

## Metrics to Record
1. Processing time per recording.
2. Percent of tasks accepted without rewrite.
3. Percent of email draft lines reused as-is.
4. Number of failed jobs.

## Exit Criteria
1. 0 critical failures in consent, recording, or file generation.
2. At least 80% of recordings complete with `done` status.
3. At least 70% task usefulness and 70% email reuse with light edits.

## Bug Logging Format
1. Date/time.
2. Recording file name.
3. Expected result.
4. Actual result.
5. Severity (`Critical`, `High`, `Medium`, `Low`).
6. Screenshot or output file reference.
