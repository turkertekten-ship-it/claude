"""Making the loop actually run at the end of every day.

A self-improvement system that depends on remembering to invoke it is a
self-improvement system that runs twice and is never thought of again. So the
scheduling is a first-class feature rather than a line in the README, and it
generates real units for whatever the machine actually uses.

The four backends differ in one way that matters more than syntax:

    systemd   Persistent=true    - a missed run fires on next boot
    launchd   StartCalendarInterval - a missed run fires on wake
    cron      no catch-up        - a laptop asleep at 22:30 simply skips the day
    GitHub    scheduled workflow - runs regardless of your machine, but only
                                   sees the repository, not your shell or chats

Catch-up is the whole game for a nightly job on a laptop, which is why cron is
offered but not recommended, and why the generator says so in the emitted
comment rather than leaving the user to discover it in three weeks of silence.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

LABEL = "oodarag-reflect"
DEFAULT_TIME = "22:30"


@dataclass(slots=True)
class ScheduleSpec:
    root: Path
    hour: int = 22
    minute: int = 30
    apply: bool = False
    python: str = ""

    @classmethod
    def parse(cls, root: Path, at: str = DEFAULT_TIME, apply: bool = False) -> ScheduleSpec:
        try:
            hh, mm = at.split(":", 1)
            hour, minute = int(hh), int(mm)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"--at must look like HH:MM, got {at!r}") from e
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"--at out of range: {at!r}")
        return cls(root=Path(root).resolve(), hour=hour, minute=minute, apply=apply,
                   python=sys.executable or "python3")

    @property
    def command(self) -> str:
        flag = " --apply" if self.apply else ""
        # PYTHONPATH rather than an install step: the package is deliberately
        # dependency-free and usable straight from a checkout, and a scheduled
        # job that breaks when a virtualenv is rebuilt is a job that dies quietly.
        return (
            f"cd {self.root} && PYTHONPATH={self.root}/src "
            f"{self.python} -m oodarag.cli reflect run{flag}"
        )


def cron_line(spec: ScheduleSpec) -> str:
    return (
        f"# {LABEL}: nightly OODA review of your files, prompts and terminal history.\n"
        f"# NOTE: cron does not catch up missed runs - if the machine is asleep at "
        f"{spec.hour:02d}:{spec.minute:02d}, that day is simply skipped.\n"
        f"# Prefer the systemd or launchd unit if you have one.\n"
        f"{spec.minute} {spec.hour} * * * {spec.command} >> {spec.root}/.oodarag/reflect/cron.log 2>&1\n"
    )


def systemd_units(spec: ScheduleSpec) -> dict[str, str]:
    service = f"""[Unit]
Description=oodarag nightly reflect cycle
Documentation=https://github.com/turkertekten-ship-it/claude

[Service]
Type=oneshot
WorkingDirectory={spec.root}
Environment=PYTHONPATH={spec.root}/src
ExecStart={spec.python} -m oodarag.cli reflect run{' --apply' if spec.apply else ''}
# The loop is bounded internally, but a hung filesystem call should not leave a
# unit running until morning.
TimeoutStartSec=900
Nice=10
IOSchedulingClass=idle
"""
    timer = f"""[Unit]
Description=Run the oodarag reflect cycle at the end of each day

[Timer]
OnCalendar=*-*-* {spec.hour:02d}:{spec.minute:02d}:00
# Fire on next boot if the machine was off at the scheduled time. Without this a
# laptop that is closed every evening never runs the loop at all.
Persistent=true
# Spread the load a little so a fleet of machines does not stampede a shared FS.
RandomizedDelaySec=300
Unit={LABEL}.service

[Install]
WantedBy=timers.target
"""
    return {f"{LABEL}.service": service, f"{LABEL}.timer": timer}


def launchd_plist(spec: ScheduleSpec) -> str:
    apply_arg = "\n        <string>--apply</string>" if spec.apply else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.oodarag.reflect</string>
    <key>ProgramArguments</key>
    <array>
        <string>{spec.python}</string>
        <string>-m</string>
        <string>oodarag.cli</string>
        <string>reflect</string>
        <string>run</string>{apply_arg}
    </array>
    <key>WorkingDirectory</key>
    <string>{spec.root}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>{spec.root}/src</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>{spec.hour}</integer>
        <key>Minute</key><integer>{spec.minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{spec.root}/.oodarag/reflect/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>{spec.root}/.oodarag/reflect/launchd.err</string>
    <key>LowPriorityIO</key>
    <true/>
    <key>Nice</key>
    <integer>10</integer>
</dict>
</plist>
"""


def github_workflow(spec: ScheduleSpec) -> str:
    """A scheduled Action, for the half of the corpus that lives in the repo.

    Deliberately dry-run on the schedule. A workflow that starts rewriting files
    the moment it is merged is a workflow people revert; this one produces a
    report you can read, and applying is an explicit `workflow_dispatch` choice.
    """
    utc_hour = spec.hour  # documented below as local-vs-UTC, not silently converted
    return f"""name: nightly-reflect

# The end-of-day OODA review, for the repository half of the corpus.
#
# GitHub cron is UTC and has no local-timezone concept, so {utc_hour:02d}:{spec.minute:02d}
# below is UTC - adjust it to whatever "end of day" means where you are.
# Scheduled runs are DRY RUN: they publish a report artifact and change nothing.
# To let it actually edit files, run it from the Actions tab with apply=true, or
# flip the default once you trust it.

on:
  schedule:
    - cron: '{spec.minute} {utc_hour} * * *'
  workflow_dispatch:
    inputs:
      apply:
        description: 'Apply safe-tier edits instead of only reporting'
        type: boolean
        default: false

permissions:
  contents: write
  pull-requests: write

concurrency:
  group: nightly-reflect
  cancel-in-progress: false

jobs:
  reflect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          # The loop reads git history to date findings and to check the tree is
          # clean; a shallow clone would make both of those lie.
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run the reflect cycle
        env:
          PYTHONPATH: src
          OODARAG_LOG_FORMAT: json
        run: |
          python -m oodarag.cli reflect run \\
            ${{{{ inputs.apply == true && '--apply' || '' }}}}

      - name: Upload the nightly report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: reflect-report
          path: .oodarag/reflect/reports/
          if-no-files-found: warn
          retention-days: 30

      - name: Open a pull request for anything it changed
        if: ${{{{ inputs.apply == true }}}}
        uses: peter-evans/create-pull-request@v6
        with:
          branch: reflect/nightly
          title: 'Nightly reflect: applied safe-tier improvements'
          commit-message: 'Nightly reflect: apply safe-tier improvements'
          body-path: .oodarag/reflect/reports/latest.md
          delete-branch: true
          add-paths: |
            .
            ':!.oodarag'
"""


def render(kind: str, spec: ScheduleSpec) -> dict[str, str]:
    """name -> content for the chosen backend."""
    if kind == "cron":
        return {"crontab-entry": cron_line(spec)}
    if kind == "systemd":
        return systemd_units(spec)
    if kind == "launchd":
        return {"com.oodarag.reflect.plist": launchd_plist(spec)}
    if kind == "github":
        return {".github/workflows/nightly-reflect.yml": github_workflow(spec)}
    raise ValueError(f"unknown schedule kind: {kind!r}")


def install_hint(kind: str, spec: ScheduleSpec, written: list[Path]) -> str:
    """The one command the user still has to run, spelled out exactly.

    Deliberately never run for them: installing a timer is a change to the
    machine's behaviour outside this repository, and that is the user's call.
    """
    files = "\n".join(f"  {p}" for p in written)
    if kind == "cron":
        return (
            f"Wrote:\n{files}\n\n"
            "Install it with:\n"
            f"  (crontab -l 2>/dev/null; cat {written[0]}) | crontab -\n"
            "Then check with: crontab -l"
        )
    if kind == "systemd":
        return (
            f"Wrote:\n{files}\n\n"
            "Install (user scope, no root needed):\n"
            f"  mkdir -p ~/.config/systemd/user && cp {written[0].parent}/{LABEL}.* "
            "~/.config/systemd/user/\n"
            "  systemctl --user daemon-reload\n"
            f"  systemctl --user enable --now {LABEL}.timer\n"
            f"  systemctl --user list-timers {LABEL}.timer\n\n"
            "If you want it to run while you are logged out:\n"
            "  loginctl enable-linger $USER"
        )
    if kind == "launchd":
        return (
            f"Wrote:\n{files}\n\n"
            "Install:\n"
            f"  cp {written[0]} ~/Library/LaunchAgents/\n"
            "  launchctl load ~/Library/LaunchAgents/com.oodarag.reflect.plist\n"
            "  launchctl list | grep oodarag"
        )
    if kind == "github":
        return (
            f"Wrote:\n{files}\n\n"
            "Commit it to the default branch - scheduled workflows only run there.\n"
            "Scheduled runs are dry-run and publish a report artifact; to let it apply\n"
            "edits, trigger it from the Actions tab with apply=true."
        )
    return f"Wrote:\n{files}"
