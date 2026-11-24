#!/bin/sh
# Queue BM (BF's, reused): this repo's companion/, tools/, tests/ copied into the work copy. usage: sync.sh <repo> <work copy>
R="${1:?}"; W="${2:?}"
for d in companion tools tests; do rm -rf "${W:?}/${d:?}"; cp -a "$R/$d" "$W/$d"; find "$W/$d" -name __pycache__ -prune -exec rm -rf {} +; done
