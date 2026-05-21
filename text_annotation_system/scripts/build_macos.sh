#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DIST_ROOT="$PROJECT_DIR/dist"
DIST_DIR="$DIST_ROOT/TextAnnotationSystem"
APP_BUNDLE="$DIST_ROOT/TextAnnotationSystem.app"
ZIP_PATH="$DIST_ROOT/TextAnnotationSystem-macos.zip"
ASYNC_LIB_DIR="$(dirname "$PROJECT_DIR")/async_batch_inference"

# ── Pre-flight checks ──────────────────────────────────────────────

if ! command -v npm &>/dev/null; then
  echo "ERROR: npm not found. Please install Node.js LTS and reopen terminal."
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Please activate the Python environment or add Python to PATH."
  exit 1
fi

if [ ! -d "$ASYNC_LIB_DIR" ]; then
  echo "ERROR: async_batch_inference core library not found at: $ASYNC_LIB_DIR"
  echo "Please place async_batch_inference alongside the project directory."
  echo "Expected: <parent>/text_annotation_system and <parent>/async_batch_inference"
  exit 1
fi

# ── Stop existing processes ─────────────────────────────────────────

echo "Stopping existing TextAnnotationSystem processes..."
pkill -f TextAnnotationSystem 2>/dev/null || true
sleep 1

# ── Build frontend ──────────────────────────────────────────────────

echo "Building frontend..."
cd "$FRONTEND_DIR"
npm install
npm run build

# ── Install Python dependencies ─────────────────────────────────────

echo "Installing Python dependencies..."
cd "$PROJECT_DIR"
python3 -m pip install -r requirements.txt

# ── Package macOS application ───────────────────────────────────────

echo "Packaging macOS application..."
python3 -m PyInstaller --clean --noconfirm text_annotation_system.spec

if [ ! -d "$DIST_DIR" ] && [ ! -d "$APP_BUNDLE" ]; then
  echo "ERROR: Package output not found: $DIST_DIR or $APP_BUNDLE"
  exit 1
fi

# ── Prepare runtime data directory ──────────────────────────────────

TARGET_DATA_DIR="${DIST_DIR:-}"
if [ ! -d "$TARGET_DATA_DIR" ] && [ -d "$APP_BUNDLE" ]; then
  TARGET_DATA_DIR="$APP_BUNDLE/Contents/MacOS"
fi

if [ -n "$TARGET_DATA_DIR" ] && [ -d "$TARGET_DATA_DIR" ]; then
  printf "data" > "$TARGET_DATA_DIR/data_dir.txt"
  mkdir -p "$TARGET_DATA_DIR/data"
fi

# ── Copy user guide ─────────────────────────────────────────────────

USER_GUIDE="$DIST_ROOT/使用说明.txt"
if [ -f "$USER_GUIDE" ] && [ -n "$TARGET_DATA_DIR" ]; then
  cp "$USER_GUIDE" "$TARGET_DATA_DIR/"
fi

# ── Create distributable zip ────────────────────────────────────────

ZIP_SOURCE=""
if [ -d "$APP_BUNDLE" ]; then
  ZIP_SOURCE="$APP_BUNDLE"
elif [ -d "$DIST_DIR" ]; then
  ZIP_SOURCE="$DIST_DIR"
fi

if [ -n "$ZIP_SOURCE" ]; then
  echo "Creating distributable zip..."
  rm -f "$ZIP_PATH"

  for i in 1 2 3 4 5; do
    sleep 2
    if cd "$(dirname "$ZIP_SOURCE")" && zip -r "$ZIP_PATH" "$(basename "$ZIP_SOURCE")" 2>/dev/null; then
      break
    fi
    if [ "$i" -eq 5 ]; then
      echo "ERROR: Zip failed after 5 attempts."
      exit 1
    fi
    echo "Zip failed because files are still locked. Retrying ($i/5)..."
  done
fi

echo ""
echo "Build complete."
if [ -d "$DIST_DIR" ]; then
  echo "Folder: $DIST_DIR"
fi
if [ -d "$APP_BUNDLE" ]; then
  echo "App:    $APP_BUNDLE"
fi
if [ -f "$ZIP_PATH" ]; then
  echo "Zip:    $ZIP_PATH"
fi
echo "Send the zip to users. They unzip it and run TextAnnotationSystem.app."
