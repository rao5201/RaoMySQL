#!/bin/bash
# Cloudflare Pages Build Script for RaoMySQL
# Builds React frontend and merges with landing page

set -e
echo "=== Building RaoMySQL for Cloudflare Pages ==="

# 1. Install frontend dependencies and build
echo "[1/3] Installing frontend dependencies..."
cd frontend
npm install

echo "[2/3] Building React app..."
npm run build
cd ..

# 2. dist/ now contains React build (index.html + assets/)
#    Rename React's index.html to app.html
echo "[3/3] Merging landing page with React app..."
mv dist/index.html dist/app.html

# 3. Copy landing page as the main index.html
cp index.html dist/index.html

echo "=== Build complete! Output: dist/ ==="
echo "  index.html  -> Landing page (marketing)"
echo "  app.html    -> React SPA (admin panel)"
echo "  assets/     -> React JS/CSS bundles"
ls -la dist/
