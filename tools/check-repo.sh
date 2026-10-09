#!/usr/bin/env bash
# Rejects what must never be committed to this public library:
#  - a complete game page (index.html / *backup* / zips), credentials, private keys, tokens.
set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || dirname "$0"/..)"
bad=0
files=$(git ls-files; git ls-files --others --exclude-standard)
while IFS= read -r f; do
  [ -f "$f" ] || continue
  case "$f" in
    */index.html|index.html) echo "FORBIDDEN: complete game page: $f"; bad=1;;
    *backup*|*.bak|*.zip|*.7z|*.tar|*.tar.gz|*.env|.env|*.pem|*.key) echo "FORBIDDEN: backup/archive/secret-like file: $f"; bad=1;;
  esac
  size=$(wc -c < "$f"); if [ "$size" -gt 1500000 ]; then echo "TOO LARGE (>1.5 MB): $f"; bad=1; fi
  [ "$f" = "tools/check-repo.sh" ] && continue
  if grep -IlE '(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gh[ousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9]{32,})' "$f" >/dev/null 2>&1; then echo "SECRET-LIKE TOKEN in: $f"; bad=1; fi
  # a full game page contains the main script header + many features; flag any html with a <canvas id="cv0"
  case "$f" in *.html) grep -q 'id="cv0"' "$f" && { echo "LOOKS LIKE A FULL GAME PAGE (canvas cv0): $f"; bad=1; };; esac
done <<< "$files"
[ "$bad" = 0 ] && echo "repo-guard: OK" || { echo "repo-guard: FAILED"; exit 1; }
