#!/usr/bin/env python3
import argparse
from pathlib import Path
from xml.etree import ElementTree
import sys
from dataclasses import dataclass


@dataclass
class SystemMetadata:
    identifier: str
    name: str
    description: str
    manufacturer: str
    release_year: str
    hardware_type: str
    cover_size: str
    cart_size: str


def _parse_system_metadata(file: Path):
    tree = ElementTree.parse(file)
    root = tree.getroot()

    variables_node = root.find("variables")
    if variables_node is None:
        raise ValueError(f"Missing variables node in {file}")

    def get_variable_value(name):
        node = variables_node.find(name)
        if node is None:
            raise ValueError(f"Missing {name} node in {file}")

        if node.text is None:
            raise ValueError(f"Empty {name} node in {file}")

        return node.text

    return SystemMetadata(
        identifier=file.stem,
        name=get_variable_value("systemName"),
        description=get_variable_value("systemDescription"),
        manufacturer=get_variable_value("systemManufacturer"),
        release_year=get_variable_value("systemReleaseYear"),
        hardware_type=get_variable_value("systemHardwareType"),
        cover_size=get_variable_value("systemCoverSize"),
        cart_size=get_variable_value("systemCartSize"),
    )


def _make_system_node(system_metadata: SystemMetadata, roms_path: Path):
    system_node = ElementTree.Element("system")

    def add_node(name, value):
        node = ElementTree.Element(name)
        node.text = value
        system_node.append(node)

    add_node("name", system_metadata.identifier)
    add_node("fullname", system_metadata.name)
    add_node("manufacturer", system_metadata.manufacturer)
    add_node("release", system_metadata.release_year)
    add_node("hardware", system_metadata.hardware_type)
    add_node("theme", system_metadata.identifier)
    add_node("path", str(roms_path / system_metadata.identifier))
    add_node("extension", ".txt")
    add_node(
        "command",
        "emulatorlauncher %CONTROLLERSCONFIG% -system %SYSTEM% -rom %ROM% -gameinfoxml %GAMEINFOXML% -systemname %SYSTEMNAME%",
    )

    return system_node


def _make_game_node(rom_path: Path, rom_image: Path, game_name: str):
    game_node = ElementTree.Element("game")

    def add_node(name, value):
        node = ElementTree.Element(name)
        node.text = value
        game_node.append(node)

    add_node("path", str(rom_path))
    add_node("name", game_name)
    add_node("desc", f"Dummy description for the game '{game_name}'.")
    add_node("image", str(rom_image))

    return game_node


def _is_collection(system_metadata: SystemMetadata, collections: list[str]):
    name = system_metadata.identifier
    if name.startswith("auto-"):
        return True
    if name.endswith("-collections"):
        return True
    if name in collections:
        return True
    if system_metadata.hardware_type.lower() == "collection":
        return True
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Generate ES configuration files and dummy ROM for testing the theme."
    )
    parser.add_argument("dest_es_config", type=Path, help="Path to the ES config file")
    parser.add_argument(
        "dest_gamelists", type=Path, help="Path to the ES gamelists file"
    )
    parser.add_argument("dest_roms", type=Path, help="Path to the ROMs directory")
    args = parser.parse_args()

    workspace = Path(__file__).resolve().parent.parent
    metadata = workspace / "_inc" / "metadata"

    collections = [
        line.strip()
        for line in (workspace / "collections.info").read_text().splitlines()
    ]

    config_tree = ElementTree.ElementTree(ElementTree.Element("systemList"))
    config_root = config_tree.getroot()

    for system in metadata.glob("*.xml"):
        if system.name == "_builtin.xml":
            continue

        system_metadata = _parse_system_metadata(system)

        if _is_collection(system_metadata, collections):
            continue

        system_node = _make_system_node(system_metadata, args.dest_roms)
        config_root.append(system_node)

        system_roms_path = args.dest_roms / system_metadata.identifier
        system_roms_path.mkdir(parents=True, exist_ok=True)

        gamelists_tree = ElementTree.ElementTree(ElementTree.Element("gameList"))
        gamelists_root = gamelists_tree.getroot()

        for i in range(20):
            dummy_rom_path = system_roms_path / f"dummy_{i:02d}.txt"
            dummy_rom_path.touch()
            dummy_rom_image = workspace / "_inc" / "controllers/_default.webp"
            game_node = _make_game_node(
                dummy_rom_path, dummy_rom_image, f"Dummy Game {i}"
            )
            gamelists_root.append(game_node)

        ElementTree.indent(gamelists_tree, level=0, space="  ")

        system_gameslists_path = args.dest_gamelists / system_metadata.identifier
        system_gameslists_path.mkdir(parents=True, exist_ok=True)

        with open(system_gameslists_path / "gamelist.xml", "wb") as f:
            gamelists_tree.write(f, encoding="utf8", xml_declaration=True)

    ElementTree.indent(config_tree, level=0, space="  ")

    with open(args.dest_es_config, "wb") as f:
        config_tree.write(f, encoding="utf8", xml_declaration=True)
