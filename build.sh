#!/usr/bin/env bash
set -o errexit

echo "--- Installing Backend Dependencies ---"
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "--- Building React Frontend Assets ---"
cd frontend
npm install
npm run build
cd ..

echo "--- Build Complete ---"
