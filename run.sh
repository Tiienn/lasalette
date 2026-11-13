#!/bin/bash
# Full pipeline on the Mac. Usage:  ./run.sh            (everything)
#                                   ./run.sh test       (model + plan view + 3 quick check views)
set -e
cd "$(dirname "$0")"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
command -v "$BLENDER" >/dev/null 2>&1 || BLENDER=blender

"$BLENDER" -b -P src/build.py
"$BLENDER" -b -P src/fitout.py
"$BLENDER" -b -P src/render.py -- --mode top
if [ "$1" = "test" ]; then
  "$BLENDER" -b -P src/render.py -- --mode test --nodes living,bedroom,pool --variant day
  echo "Check images: build/top.png and build/test/"
  exit 0
fi
"$BLENDER" -b -P src/render.py -- --mode pano --size 2048 --samples 128     # resumable: finished faces are skipped
python3 src/grade.py
echo "Done. Preview:  cd web && python3 -m http.server 8000   then open http://localhost:8000"
