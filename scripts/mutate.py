"""Mutation harness that refuses to report a result it did not produce.

Three times this session a mutation silently failed to apply - a pattern with
different indentation, a short assert guarding a long replacement - and the
suite passed on unmutated code, which the harness printed as SURVIVED. A
SURVIVED that means "nothing was changed" is a false negative in the one tool
whose job is finding false negatives.
"""
import pathlib, shutil, subprocess, sys, tempfile

def run(mutations, test):
    backup = tempfile.mkdtemp()
    shutil.copytree("src", pathlib.Path(backup) / "src")
    try:
        for path, old, new in mutations:
            p = pathlib.Path(path)
            before = p.read_text()
            after = before.replace(old, new, 1)
            if after == before:
                print(f"HARNESS ERROR: no change applied to {path}")
                return 2
            p.write_text(after)
        subprocess.run("find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null", shell=True)
        r = subprocess.run([sys.executable, "-m", "unittest", test],
                           capture_output=True, text=True,
                           env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"})
        return 0 if r.returncode != 0 else 1
    finally:
        shutil.rmtree("src"); shutil.copytree(pathlib.Path(backup) / "src", "src")
        subprocess.run("find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null", shell=True)

TEST = "tests.test_review_regressions.CorpusIsUnredactedAndTheIndexIsNotTest"
CASES = {
    "boundary only": [("src/oodarag/models.py",
                       "self.text = redact_secrets(self.text)", "self.text = self.text")],
    "connector only": [("src/oodarag/ingest/filesystem.py",
                        "redact_secrets(data.decode(", "(data.decode(")],
    "pipeline only": [("src/oodarag/pipeline.py",
                       "redact_secrets(clean(raw.text))", "clean(raw.text)")],
    "all three": [("src/oodarag/models.py",
                   "self.text = redact_secrets(self.text)", "self.text = self.text"),
                  ("src/oodarag/ingest/filesystem.py",
                   "redact_secrets(data.decode(", "(data.decode("),
                  ("src/oodarag/pipeline.py",
                   "redact_secrets(clean(raw.text))", "clean(raw.text)")],
}
for label, muts in CASES.items():
    code = run(muts, TEST)
    print({0: "CAUGHT   ", 1: "SURVIVED ", 2: "ERROR    "}[code] + f" {label}")
