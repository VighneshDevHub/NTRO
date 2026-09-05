# Phase 3 — Secure File & Folder Eraser Module

## What this phase delivers

Genuinely new work (no TrustWipe precedent) addressing all three
erasure targets the PS calls out:
1. **Content** — overwritten with random bytes before deletion
2. **Metadata** — filename scrubbed via multiple renames, timestamps reset
3. **Freed disk space** — overwritten with a temp fill file so nothing
   lingers in blocks the OS just marked "free"

Plus **batch operations** (multiple files/folders in one run) as
explicitly required by the PS, with honest partial-failure reporting.

## Directory structure

```
file-folder-eraser/
├── src/
│   ├── main.py                    # CLI entrypoint
│   ├── metadata_scrubber.py       # filename rename passes + timestamp reset
│   ├── freespace_overwriter.py    # fills freed disk blocks
│   ├── selective_deleter.py       # orchestrates 1 file/folder's full erasure
│   ├── batch_runner.py            # orchestrates N targets + one freespace pass
│   ├── report_builder.py          # emits operation_type: "FILE_ERASE"
│   └── api_client.py
└── tests/
```

## Commands to run it yourself

```bash
cd file-folder-eraser
pip install -r requirements.txt
pytest -v      # 19 passed, 1 skipped (see note below)

# Make sure the Phase 1 backend is running:
#   cd ../backend && uvicorn app.main:app --port 8000

mkdir case_notes
echo "CONFIDENTIAL WITNESS STATEMENT" > case_notes/witness.txt
python -m src.main --targets case_notes --operator "investigator-1" --api-url http://localhost:8000 --freespace-max-bytes 2000000
```

## How to test it manually / for your demo

1. Create a folder with a few files containing recognizable text
2. `ls` the folder, `cat` a file — confirm readable content
3. Run the agent targeting that folder
4. `ls` again — the entire folder is gone, not just emptied
5. `GET /api/v1/operations/{certificate_id}` — confirm `details` shows
   `files_deleted`, `metadata_scrubbed: true`, and
   `freespace_bytes_overwritten` > 0
6. `GET /api/v1/verify/{certificate_id}` — green

## A real bug found and fixed during testing

**The bug:** when the batch target was an entire *folder* (not
individual files), `secure_delete_folder` correctly removes the folder
itself at the end — but the free-space overwrite step then tried to
write its temp fill file into that now-deleted folder, crashing with
`FileNotFoundError`.

**The fix:** added `_nearest_existing_dir()`, which walks up the path
until it finds a directory that still exists, and does the free-space
pass there instead. Added `test_run_batch_freespace_overwrite_works_when_target_is_a_whole_folder`
as a regression test — this exact scenario (whole-folder target +
free-space overwrite enabled) is now covered so it can't silently
reappear.

This was caught by actually running the live demo end-to-end (not just
unit tests in isolation) — the unit tests for `batch_runner` and
`freespace_overwriter` each passed individually before this fix, since
neither tested the specific combination that broke. Worth remembering:
passing unit tests don't guarantee passing integration — this is why
every phase gets a live run, not just `pytest`.

## A test we skip on purpose, and why

`test_overwrite_free_space_raises_on_unwritable_directory` is skipped
when running as root (`os.geteuid() == 0`), because root bypasses Unix
permission bits entirely — a chmod'd "unwritable" directory isn't
actually unwritable to root, so the test's premise doesn't hold in that
environment. It will run and pass under a normal user account. This is
disclosed rather than silently passing on a technicality.

## What we tested

| Test file | What it proves |
|---|---|
| `test_metadata_scrubber.py` (4 tests) | Filename renamed away from original, multiple passes happen, timestamps reset to epoch |
| `test_selective_deleter.py` (5 tests) | Content overwrite happens before deletion; missing files fail gracefully instead of crashing; whole folders (including nested subfolders) are fully removed |
| `test_freespace_overwriter.py` (3 tests, 1 skipped under root) | Respects the byte cap, cleans up its own temp file, raises loudly (not silently) if the directory isn't writable |
| `test_batch_runner.py` (6 tests) | Multiple files processed correctly; one bad target doesn't abort the whole batch; folders expand correctly; **the whole-folder + freespace regression case specifically** |
| `test_report_builder.py` (2 tests) | `success` correctly reflects whether ANY deletion failed, not just whether the batch ran |

19 passed, 1 environment-conditional skip. Also ran a full live
end-to-end demo: created a real case-notes folder with two files
containing recognizable confidential text, ran the agent, confirmed the
entire folder was gone, fetched the signed record showing correct
`details`, and verified it green.

## Honest limitations (state these plainly in your SIH presentation)

- Filename/timestamp scrubbing at the **filesystem journal level**
  (NTFS `$LogFile`, ext4 journal entries) is not addressed — this
  requires OS/filesystem-specific tooling below what portable Python
  can reach. What's implemented here (directory-entry renaming +
  timestamp reset) is a genuine, meaningful mitigation, not a complete
  guarantee against a well-resourced forensic lab examining journal
  history.
- Free-space overwriting fills space with a single temp file — on a
  fragmented volume this may not touch every individual freed block in
  one pass. A production version would iterate until free space
  stabilizes near zero across multiple passes.

## Next: Phase 4

The Advanced File Carving & Recovery module — the hardest, most novel
phase: signature-based scanning to recover files from a raw image with
no working filesystem, plus confidence scoring. Say "next" when ready.
