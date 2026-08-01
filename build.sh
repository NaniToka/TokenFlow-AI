#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- Installing Python Backend Dependencies ---"
pip install --upgrade pip || python3 -m pip install --upgrade pip
pip install -r backend/requirements.txt || python3 -m pip install -r backend/requirements.txt

echo "--- Building React Frontend Assets ---"
cd frontend
npm install
npm run build
cd ..

echo "--- Copying Built Assets for FastAPI SPA Mount ---"
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

echo "--- Build Completed Successfully ---"
