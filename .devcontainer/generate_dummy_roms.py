#!/usr/bin/env python3

import argparse
from pathlib import Path
from xml.etree import ElementTree
from dataclasses import dataclass


@dataclass
class System:
    roms_path: Path
    extension: str


def list_systems(config: Path):
    tree = ElementTree.parse(config)
    root = tree.getroot()

    for system in root.findall("system"):
        path_node = system.find("path")
        if path_node is None or path_node.text is None:
            continue

        extension_node = system.find("extension")
        if extension_node is None or extension_node.text is None:
            continue

        system_roms = Path(path_node.text)
        extension, *_ = extension_node.text.split()

        yield System(system_roms, extension[1:])


def create_dummy_rom(system: System):
    system.roms_path.mkdir()
    rom = system.roms_path / f"dummy.{system.extension}"
    rom.touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dummy ROMs for all systems")
    parser.add_argument(
        "systems_config",
        type=str,
        help="Path to the list of systems as XML config file for EmulationStation",
    )
    args = parser.parse_args()

    # List of systems retrieved from https://github.com/batocera-linux/batocera.linux/blob/master/package/batocera/emulationstation/batocera-es-system/es_systems.yml

    for system in list_systems(args.systems_config):
        create_dummy_rom(system)
