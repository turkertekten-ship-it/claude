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
#   bash tools/install_prompt_system.sh [--check] [--dry-run] [--uninstall]
#                                      [--force] [--prefix DIR] [--bin-dir DIR]
#
# It will not overwrite a file it did not install. ~/.claude is the owner's own
# directory and may already hold a command of theirs at one of these names; an
# installer that clobbers it, and an uninstaller that then deletes it, would
# destroy work this repository never wrote. --force replaces such a file after
# copying it aside.
#
# --check compares what is installed against what this repository would install
# now, and exits 1 if any of it has drifted. Nothing else keeps the two in step:
# the installed copy is what runs in every other terminal, and a stale one looks
# identical while behaving differently.
# Exit
#   0 installed, or in sync, or not installed at all · 1 verification failed,
#   or the install has drifted · 2 could not run

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX="${HOME}/.claude"
BIN_DIR="${HOME}/.local/bin"
DRY=0
UNINSTALL=0
CHECK=0
FORCE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run)   DRY=1 ;;
        --uninstall) UNINSTALL=1 ;;
        --check)     CHECK=1 ;;
        --force)     FORCE=1 ;;
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
    "$PREFIX/tools/check_output.py"
    "$PREFIX/tools/_phrases.py"
    "$BIN_DIR/prompt-forge"
    "$BIN_DIR/prompt-habits"
    "$BIN_DIR/learn-rule"
    "$BIN_DIR/check-output"
)


MANIFEST="$PREFIX/.prompt-system-manifest"

ours() {
    # Is this path one we installed, according to the manifest?
    [ -f "$MANIFEST" ] && grep -Fxq "$1" "$MANIFEST"
}

source_for() {
    # The repository file a given installed path came from, if any.
    local dst="$1" src pair
    while IFS='|' read -r pair dst2; do
        [ "$dst2" = "$dst" ] && { printf '%s' "$pair"; return 0; }
    done < <(markdown_pairs)
    for tool in prompt_forge.py prompt_habits.py learn_rule.py check_output.py _phrases.py; do
        [ "$dst" = "$PREFIX/tools/$tool" ] && { printf '%s' "$REPO/tools/$tool"; return 0; }
    done
    return 1
}

unmodified() {
    # A shim is generated rather than copied; it is ours if it says so.
    local dst="$1" src
    case "$dst" in
        "$BIN_DIR"/*) grep -q "Installed by tools/install_prompt_system.sh" "$dst" && return 0
                      return 1 ;;
    esac
    src="$(source_for "$dst")" || return 1
    would_write "$src" "$dst" | cmp -s - "$dst"
}

would_write() {
    # The content this installer would put at $2, for comparison.
    case "$2" in
        *.md) rendered "$1" ;;
        *)    cat "$1" ;;
    esac
}

rendered() {
    # What the installed copy of a markdown file should contain: the source,
    # with its commands pointed at the installed binary.
    sed -e 's|python3 tools/prompt_forge\.py|prompt-forge|g' \
        -e 's|`\.claude/skills/prompt-forge/SKILL\.md`|`~/.claude/skills/prompt-forge/SKILL.md`|g' \
        "$1"
}


# Source -> destination for every file the installer writes, in one place so
# --check and the install itself cannot drift apart.
markdown_pairs() {
    printf '%s\n' \
        "$REPO/.claude/skills/prompt-forge/SKILL.md|$PREFIX/skills/prompt-forge/SKILL.md" \
        "$REPO/.claude/commands/prompt.md|$PREFIX/commands/prompt.md" \
        "$REPO/.claude/commands/prompt-audit.md|$PREFIX/commands/prompt-audit.md" \
        "$REPO/.claude/commands/prompt-habits.md|$PREFIX/commands/prompt-habits.md" \
        "$REPO/.claude/agents/prompt-critic.md|$PREFIX/agents/prompt-critic.md"
}

if [ "$UNINSTALL" -eq 1 ]; then
    say "removing the prompt system from $PREFIX"
    kept=0
    for target in "${TARGETS[@]}"; do
        [ -e "$target" ] || continue
        if ! ours "$target"; then
            say "  kept $target — not installed by this script"
            kept=$((kept + 1)); continue
        fi
        if ! unmodified "$target"; then
            say "  kept $target — you have edited it since it was installed"
            kept=$((kept + 1)); continue
        fi
        do_it rm -f "$target" && say "  removed $target"
    done
    if [ "$DRY" -eq 0 ]; then
        rm -f "$MANIFEST"
        rmdir "$PREFIX/skills/prompt-forge" 2>/dev/null
    fi
    say "done. $kept file(s) this script did not write were left alone."
    exit 0
fi

# Refuse to install something that does not pass its own tests. An installer
# that ships a broken guard is worse than no installer: the guard's exit code
# is what everything downstream trusts.
if [ "$CHECK" -eq 1 ]; then
    installed=0
    drifted=0
    for target in "${TARGETS[@]}"; do
        [ -e "$target" ] && installed=$((installed + 1))
    done
    if [ "$installed" -eq 0 ]; then
        say "nothing is installed at $PREFIX — nothing to be stale."
        say "Run: bash tools/install_prompt_system.sh"
        exit 0
    fi

    say "comparing $PREFIX against this repository"
    while IFS='|' read -r src dst; do
        if [ ! -f "$dst" ]; then
            say "  MISSING  ${dst#$PREFIX/}"; drifted=$((drifted + 1)); continue
        fi
        if rendered "$src" | cmp -s - "$dst"; then
            say "  same     ${dst#$PREFIX/}"
        else
            say "  DRIFTED  ${dst#$PREFIX/}"; drifted=$((drifted + 1))
        fi
    done < <(markdown_pairs)

    for tool in prompt_forge.py prompt_habits.py learn_rule.py check_output.py _phrases.py; do
        if [ ! -f "$PREFIX/tools/$tool" ]; then
            say "  MISSING  tools/$tool"; drifted=$((drifted + 1))
        elif cmp -s "$REPO/tools/$tool" "$PREFIX/tools/$tool"; then
            say "  same     tools/$tool"
        else
            say "  DRIFTED  tools/$tool"; drifted=$((drifted + 1))
        fi
    done

    if [ "$drifted" -eq 0 ]; then
        say ""
        say "in sync. What runs in your other terminals is what is in this repository."
        exit 0
    fi
    say ""
    say "$drifted file(s) differ. Every terminal on this machine is running the old"
    say "copy, which looks identical and does not behave identically."
    say "Run: bash tools/install_prompt_system.sh"
    exit 1
fi

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

guard_target() {
    # 0 to proceed, 1 to refuse. A file we installed, or one already identical
    # to what we would write, is ours to replace. Anything else is the owner's.
    local src="$1" dst="$2"
    [ -e "$dst" ] || return 0
    ours "$dst" && return 0
    would_write "$src" "$dst" | cmp -s - "$dst" && return 0
    if [ "$FORCE" -eq 1 ]; then
        local backup="$dst.replaced-$(date +%Y-%m-%d)"
        cp "$dst" "$backup" || return 1
        say "  kept your version at $backup"
        return 0
    fi
    say "  REFUSING to overwrite $dst" >&2
    say "    It is not a file this installer wrote, and it is not identical to" >&2
    say "    what would be written. Move it, or re-run with --force to have it" >&2
    say "    copied aside first." >&2
    return 1
}

record() {
    [ "$DRY" -eq 1 ] && return 0
    ours "$1" || printf '%s\n' "$1" >> "$MANIFEST"
}

install_rewritten() {
    local src="$1" dst="$2"
    if [ "$DRY" -eq 1 ]; then say "  would: install $src -> $dst"; return 0; fi
    guard_target "$src" "$dst" || return 1
    rendered "$src" > "$dst" || return 1
    record "$dst"
    say "  installed $dst"
}


while IFS='|' read -r src dst; do
    install_rewritten "$src" "$dst" || exit 1
done < <(markdown_pairs)

for tool in prompt_forge.py prompt_habits.py learn_rule.py check_output.py _phrases.py; do
    if [ "$DRY" -eq 0 ]; then
        guard_target "$REPO/tools/$tool" "$PREFIX/tools/$tool" || exit 1
    fi
    do_it cp "$REPO/tools/$tool" "$PREFIX/tools/$tool" || exit 2
    if [ "$DRY" -eq 0 ]; then record "$PREFIX/tools/$tool"; say "  installed $PREFIX/tools/$tool"; fi
done

for shim in prompt-forge:prompt_forge.py prompt-habits:prompt_habits.py learn-rule:learn_rule.py check-output:check_output.py; do
    name="${shim%%:*}"; script="${shim#*:}"
    if [ "$DRY" -eq 1 ]; then
        say "  would: write $BIN_DIR/$name"
        continue
    fi
    # Generated rather than copied, but guarded the same way: `check-output` is
    # a name somebody may already have on their PATH, and the previous version
    # of this loop wrote over it without looking.
    candidate="$(mktemp)"
    cat > "$candidate" <<SHIM
#!/usr/bin/env bash
# Installed by tools/install_prompt_system.sh from $REPO
exec python3 -B "$PREFIX/tools/$script" "\$@"
SHIM
    if ! guard_target "$candidate" "$BIN_DIR/$name"; then
        rm -f "$candidate"; exit 1
    fi
    cp "$candidate" "$BIN_DIR/$name" || { rm -f "$candidate"; exit 2; }
    rm -f "$candidate"
    chmod +x "$BIN_DIR/$name" || exit 2
    record "$BIN_DIR/$name"
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
