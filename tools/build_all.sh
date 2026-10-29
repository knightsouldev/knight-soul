#!/bin/sh
# Regenera TODOS os assets procedurais e valida o projeto. Requer: python3, pillow, numpy, ffmpeg (com libvorbis).
set -e
cd "$(dirname "$0")/.."
python3 tools/gen_env.py
python3 tools/gen_chars.py
python3 tools/gen_ui.py
python3 tools/gen_audio.py
python3 tools/gen_level.py > /dev/null
python3 tools/check_project.py
