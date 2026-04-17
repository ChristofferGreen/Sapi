# Example Site Bundle

This directory contains a resumable example-site runner and the PDF set it ingests.

Files:

- `run_example_site.sh`: creates an example site at a caller-provided path, ingests the bundled PDFs in order, and generates comments after ingest completes.
- `subspaces.tsv`: parent-space and subspace structure for the example site.
- `ingest_plan.tsv`: ordered ingest plan. Each row maps one target subspace to one bundled PDF.
- `pdfs/`: the PDFs to ingest. These are stored as symlinks to the verified seed PDFs under `verification/reingest_seed_pdfs`.

Runtime state:

- The runner writes its resumable state to `<site_path>/example_runner/status.env`.
- Command logs go to `<site_path>/example_runner/logs/`.
- Semantic prompts and Codex stdout/stderr traces are written by the normal pipeline to `<site_path>/outputs/llm_traces/`.

Resume behavior:

- The status file stores the next ingest index and next comment index.
- If a run fails, fix the issue and rerun the same command. The script resumes from the recorded position.
- To restart from scratch, remove the target site directory or delete `<site_path>/example_runner/status.env`.
