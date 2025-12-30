@echo off
REM Helper script to create initial git commit and tag (Windows)
REM Run this from repository root after reviewing files

git init
git add .
git commit -m "Initial commit: MVP binary editor"
git tag v0.1.0

echo "Initial commit created. Use 'gh repo create <owner>/BinaryBuild --public --source=. --remote=origin --push' to publish or add remote manually and push."