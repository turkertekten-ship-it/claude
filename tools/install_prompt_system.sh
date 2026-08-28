#!/usr/bin/env bash
# Install the prompt system into the user scope, so every terminal on this
# machine gets it rather than only sessions opened inside this repository.
#
# What it installs, and why each piece has to leave the repo:
#   ~/.claude/skills/prompt-forge/   the procedure  (a repo-local skill is invisible elsewhere)
#   ~/.claude/commands/prompt*.md    /prompt, /prompt-audit, /prompt-habits
#   ~/.claude/agents/prompt-critic.md the adversarial reader
#   ~/.claude/tools/                 prompt_forge.py and its phrase list
#   ~/.local/bin/prompt-forge        so the command files can call it by name
#   ~/.local/bin/prompt-habits       the corpus auditor, likewise
#   ~/.local/bin/learn-rule          the learned-rule appender
#
# The installed copies of the markdown have `python3 tools/prompt_forge.py`
# rewritten to `prompt-forge`, because outside this repository that relative
# path does not exist.
#
# Usage
#   bash tools/install_prompt_system.sh [--dry-run] [--uninstall] [--prefix DIR] [--bin-dir DIR]
# Exit
#   0 installed (or nothing to do) · 1 verification failed · 2 could not run

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX="${HOME}/.claude"
BIN_DIR="${HOME}/.local/bin"
DRY=0
UNINSTALL=0

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run)   DRY=1 ;;
        --uninstall) UNINSTALL=1 ;;
        --prefix)    PREFIX="${2:?--prefix needs a directory}"; shift ;;
        --bin-dir)   BIN_DIR="${2:?--bin-dir needs a directory}"; shift ;;
        -h|--help)   sed -n '2,20p' "$0"; exit 0 ;;
        *)           echo "install_prompt_system: unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

say()  { printf '%s\n' "$*"; }
do_it() { if [ "$DRY" -eq 1 ]; then say "  would: $*"; else "$@" || return 1; fi; }

TARGETS=(
    "$PREFIX/skills/prompt-forge/SKILL.md"
    "$PREFIX/commands/prompt.md"
    "$PREFIX/commands/prompt-audit.md"
    "$PREFIX/commands/prompt-habits.md"
    "$PREFIX/agents/prompt-critic.md"
    "$PREFIX/tools/prompt_forge.py"
    "$PREFIX/tools/prompt_habits.py"
    "$PREFIX/tools/learn_rule.py"
    "$PREFIX/tools/_phrases.py"
    "$BIN_DIR/prompt-forge"
    "$BIN_DIR/prompt-habits"
    "$BIN_DIR/learn-rule"
)

if [ "$UNINSTALL" -eq 1 ]; then
    say "removing the prompt system from $PREFIX"
    for target in "${TARGETS[@]}"; do
        [ -e "$target" ] || continue
        do_it rm -f "$target" && say "  removed $target"
    done
    [ "$DRY" -eq 1 ] || rmdir "$PREFIX/skills/prompt-forge" 2>/dev/null
    say "done. Files this script did not create were left alone."
    exit 0
fi

# Refuse to install something that does not pass its own tests. An installer
# that ships a broken guard is worse than no installer: the guard's exit code
# is what everything downstream trusts.
if [ "$DRY" -eq 0 ]; then
    if ! python3 "$REPO/tests/test_prompt_forge.py" >/dev/null 2>&1; then
        say "install_prompt_system: the prompt forge test suite fails in this repository." >&2
        say "Refusing to install. Run: python3 tests/test_prompt_forge.py" >&2
        exit 1
    fi
fi

say "installing the prompt system"
say "  from: $REPO"
say "  into: $PREFIX  (binary: $BIN_DIR/prompt-forge)"

for dir in "$PREFIX/skills/prompt-forge" "$PREFIX/commands" "$PREFIX/agents" "$PREFIX/tools" "$BIN_DIR"; do
    do_it mkdir -p "$dir" || { say "could not create $dir" >&2; exit 2; }
done

install_rewritten() {
    # Copy a markdown file, pointing its commands at the installed binary.
    local src="$1" dst="$2"
    if [ "$DRY" -eq 1 ]; then say "  would: install $src -> $dst"; return 0; fi
    sed -e 's|python3 tools/prompt_forge\.py|prompt-forge|g' \
        -e 's|`\.claude/skills/prompt-forge/SKILL\.md`|`~/.claude/skills/prompt-forge/SKILL.md`|g' \
        "$src" > "$dst" || return 1
    say "  installed $dst"
}

install_rewritten "$REPO/.claude/skills/prompt-forge/SKILL.md" "$PREFIX/skills/prompt-forge/SKILL.md" || exit 2
install_rewritten "$REPO/.claude/commands/prompt.md"           "$PREFIX/commands/prompt.md" || exit 2
install_rewritten "$REPO/.claude/commands/prompt-audit.md"     "$PREFIX/commands/prompt-audit.md" || exit 2
install_rewritten "$REPO/.claude/commands/prompt-habits.md"    "$PREFIX/commands/prompt-habits.md" || exit 2
install_rewritten "$REPO/.claude/agents/prompt-critic.md"      "$PREFIX/agents/prompt-critic.md" || exit 2

for tool in prompt_forge.py prompt_habits.py learn_rule.py _phrases.py; do
    do_it cp "$REPO/tools/$tool" "$PREFIX/tools/$tool" || exit 2
    [ "$DRY" -eq 1 ] || say "  installed $PREFIX/tools/$tool"
done

for shim in prompt-forge:prompt_forge.py prompt-habits:prompt_habits.py learn-rule:learn_rule.py; do
    name="${shim%%:*}"; script="${shim#*:}"
    if [ "$DRY" -eq 1 ]; then
        say "  would: write $BIN_DIR/$name"
        continue
    fi
    cat > "$BIN_DIR/$name" <<SHIM
#!/usr/bin/env bash
# Installed by tools/install_prompt_system.sh from $REPO
exec python3 -B "$PREFIX/tools/$script" "\$@"
SHIM
    chmod +x "$BIN_DIR/$name" || exit 2
    say "  installed $BIN_DIR/$name"
done

if [ "$DRY" -eq 1 ]; then
    say "dry run: nothing was written."
    exit 0
fi

# Verify the thing that was just installed, from the installed path only.
say "verifying the installed copy"

# Every target exists. A silent write failure once shipped a command file that
# was never created, and the install still reported success.
missing=""
for target in "${TARGETS[@]}"; do
    [ -e "$target" ] || missing="$missing\n  $target"
done
if [ -n "$missing" ]; then
    say "  FAILED: these files were not installed:$(printf "$missing")" >&2
    exit 1
fi
say "  all ${#TARGETS[@]} files are in place"
tmp="$(mktemp)"
printf 'Fix the failing test and clean up all the modules.\n' > "$tmp"
if "$BIN_DIR/prompt-forge" lint "$tmp" >/dev/null 2>&1; then
    say "  FAILED: the installed linter passed a prompt it must reject" >&2
    rm -f "$tmp"; exit 1
fi
printf 'You are an engineer. Context: the repo is Python.\nWrite the parser at src/p.py.\nConstraints: no dependencies.\nOutput: a unified diff.\nAcceptance: tests/run_all.sh passes.\nIf the file is absent, say so and stop.\n' > "$tmp"
if ! "$BIN_DIR/prompt-forge" lint "$tmp" >/dev/null 2>&1; then
    say "  FAILED: the installed linter rejected a well-formed prompt" >&2
    "$BIN_DIR/prompt-forge" lint "$tmp" >&2
    rm -f "$tmp"; exit 1
fi
rm -f "$tmp"
say "  the installed linter rejects a bad prompt and passes a good one"

case ":${PATH}:" in
    *":${BIN_DIR}:"*) ;;
    *) say ""
       say "NOTE: $BIN_DIR is not on your PATH. Add it, or call the tool as"
       say "      python3 $PREFIX/tools/prompt_forge.py" ;;
esac

say ""
say "installed. In any terminal on this machine:"
say "  /prompt <a rough ask>        forge it into a checkable prompt"
say "  /prompt-audit <path>         audit prompts you already have"
say "  /prompt-habits              the habit costing most across your history"
say "  prompt-forge lint FILE       the linter on its own"
say ""
say "For chats that cannot read this machine, paste prompts/portable-preamble.md."
exit 0
