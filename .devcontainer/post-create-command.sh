set -e

folder="$(dirname "$0")"

mkdir -p ~/.emulationstation/themes

cp -r "$folder/es_systems.cfg" ~/.emulationstation/
cp -r "$folder/es_input.cfg" ~/.emulationstation/

ln -s /opt/canvas-es ~/.emulationstation/themes/canvas-es
#ln -s "$(dirname "$folder")" ~/.emulationstation/themes/iconic-es

python3 "$folder/generate_dummy_roms.py" "$folder/es_systems.cfg"
