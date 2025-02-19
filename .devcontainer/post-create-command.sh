#!/usr/bin/env bash
set -e

mkdir -p ~/.emulationstation/themes

python3 -m pip install opencv-python
python3 "$WORKSPACE_DIR/_tools/setup_es_config.py" /home/dev/.emulationstation/es_systems.cfg  /home/dev/.emulationstation/gamelists /opt/roms

cp -r "$WORKSPACE_DIR/.devcontainer/es_input.cfg" ~/.emulationstation/

ln -s "$WORKSPACE_DIR" ~/.emulationstation/themes/iconic-es
