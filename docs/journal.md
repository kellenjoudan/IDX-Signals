## Week 3 Journal - Data Engineer
- Merged `check.py` and `check2.py` into unified module `src/idxlab/data/validate.py`.
- Added zero-volume day tagging to refine `is_suspended`.
- Fixed gap check to ignore market-wide closures (e.g., Lebaran) and isolate single-ticker gaps.
- Confirmed `AADI` missing due to post-2024 IPO date.
- Added unit tests in `tests/test_validate.py` (3/3 passing).
- Generated `docs/results/data_quality.md` and updated `DATA_CONTRACT.md`.