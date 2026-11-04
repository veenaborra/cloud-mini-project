#!/usr/bin/env bash
# Download model-v1/v2 from GitHub Releases, verify checksums, upload to s3://models/<v>/.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$(git remote get-url origin | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')
mkdir -p build/release
for v in v1 v2; do
  ( cd build/release
    for f in model-$v.tar.gz model-$v.sha256; do
      [ -f $f ] || curl -fsSL --retry 5 -o $f "https://github.com/$REPO/releases/download/model-$v/$f"
    done
    sha256sum -c model-$v.sha256 )
  rm -rf build/model-$v && tar -xzf build/release/model-$v.tar.gz -C build
  .venv/bin/python training/package.py $v
done
