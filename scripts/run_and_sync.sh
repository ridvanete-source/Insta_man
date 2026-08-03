#!/bin/bash
# VPS fallback runner (systemd timer insta-man-run.timer, offset from GitHub
# Actions cron so at least one of the two publishes even if the other is
# delayed/skipped - see CLAUDE.md "İki paylaşım yöntemi" / reliability notes).
set -e
cd /home/ubuntu/insta_man

git pull --rebase --autostash

.venv/bin/python -m insta_man.cli run

git add content_library/queue.yaml
if ! git diff --cached --quiet; then
  git commit -m "chore: update queue status (vps run) [skip ci]"
  git push
fi

# Safe, ToS-compliant visibility actions (engagement logging + occasional
# story reshare of an old post) - see scripts/boost_visibility.py docstring
# for why this never does follow/like/comment automation.
.venv/bin/python scripts/boost_visibility.py || true

git add content_library/visibility_state.json
if ! git diff --cached --quiet; then
  git commit -m "chore: update visibility state (vps run) [skip ci]"
  git push
fi
