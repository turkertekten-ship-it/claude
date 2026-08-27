You are a release engineer working on this repository.

Context: the repo is a Python 3.11 stdlib-only project; CI runs
`bash tests/run_all.sh` on every push, and it currently passes.

Write a GitHub Actions workflow file at `.github/workflows/ci.yml` that runs
that script on push and on pull request.

Constraints: no third-party actions beyond `actions/checkout`; do not add
dependencies; keep the file under 40 lines.

Output: the file contents only, as one YAML code block, with no commentary.

Acceptance test: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"`
parses it, and the job name is exactly `checks`.

If the repository already has a workflow at that path, say so and stop rather
than overwriting it.
