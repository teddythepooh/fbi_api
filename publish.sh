#!/usr/bin/bash

echo "Building package..."
rm -rf dist/
uv lock \
    && uv sync --dev \
    && uv build

if [[ $1 = "-y" ]]; then
    echo "Publishing package..."
    uv publish
    echo "Done."
fi
