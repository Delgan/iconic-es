#!/usr/bin/env bash
set -e

mkdir -p ~/.emulationstation/themes

cp -r "$WORKSPACE_DIR/.devcontainer/es_systems.cfg" ~/.emulationstation/
cp -r "$WORKSPACE_DIR/.devcontainer/es_input.cfg" ~/.emulationstation/

python3 "$WORKSPACE_DIR/.devcontainer/generate_dummy_roms.py" "$WORKSPACE_DIR/.devcontainer/es_systems.cfg"

ln -s /opt/canvas-es ~/.emulationstation/themes/canvas-es
ln -s "$WORKSPACE_DIR" ~/.emulationstation/themes/iconic-es
