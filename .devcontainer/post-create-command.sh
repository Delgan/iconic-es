#!/usr/bin/env bash
set -e

mkdir -p ~/.emulationstation/themes

echo "Installing Python dependencies..."
python3 -m pip install --no-warn-script-location opencv-python requests rich pillow lxml imagehash

echo "Setting up EmulationStation configuration..."
python3 "$WORKSPACE_DIR/_tools/setup_es_config.py" /home/dev/.emulationstation/es_systems.cfg  /home/dev/.emulationstation/gamelists /opt/roms

cp -r "$WORKSPACE_DIR/.devcontainer/es_input.cfg" ~/.emulationstation/

ln -s "$WORKSPACE_DIR" ~/.emulationstation/themes/iconic-es
