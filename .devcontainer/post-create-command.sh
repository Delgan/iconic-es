#!/usr/bin/env bash
set -e

mkdir -p ~/.emulationstation/themes

echo "Installing Python dependencies in virtual env..."
python3 -m venv ~/.venv
source ~/.venv/bin/activate
python3 -m pip install opencv-python requests rich pillow lxml imagehash piexif filetype

echo "Setting up EmulationStation configuration..."
python3 "$WORKSPACE_DIR/_tools/setup_es_config.py" /home/ubuntu/.emulationstation/es_systems.cfg  /home/ubuntu/.emulationstation/gamelists /opt/roms

cp -r "$WORKSPACE_DIR/.devcontainer/es_input.cfg" ~/.emulationstation/

ln -s "$WORKSPACE_DIR" ~/.emulationstation/themes/iconic-es
