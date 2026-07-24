#!/bin/bash
set -e
# Goal: after a fresh clone or new machine, running this one script gets you to a
# "ready to develop, ready to verify" state.

<install deps>       # npm install / uv sync / pip install -r requirements.txt
<prepare local data/env>  # cp .env.example .env (if missing)
<smoke test>         # start once or run the minimal test to prove the env is alive

echo "init OK"
