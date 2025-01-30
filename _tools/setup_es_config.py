#!/usr/bin/env python3
import argparse
from pathlib import Path
from xml.etree import ElementTree
from dataclasses import dataclass
import numpy
import cv2
import random
import datetime


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


def _generate_dummy_game_cover(game_name: str, cover_size: tuple[int, int]):
    cover_width, cover_height = cover_size

    scale = min(200 / cover_width, 200 / cover_height)

    width = int(cover_width * scale)
    height = int(cover_height * scale)

    background_color = numpy.random.randint(50, 200, size=(3,), dtype=numpy.uint8)
    image = numpy.full((height, width, 3), background_color, dtype=numpy.uint8)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = min(width, height) / 300
    font_thickness = 1
    text_color = (255, 255, 255)

    text_size = cv2.getTextSize(game_name, font, font_scale, font_thickness)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2

    cv2.putText(
        image,
        game_name,
        (text_x, text_y),
        font,
        font_scale,
        text_color,
        font_thickness,
        cv2.LINE_AA,
    )

    return image


def _generate_dummy_game_image():
    width, height = 200, 200
    image = numpy.random.randint(0, 256, size=(height, width, 3), dtype=numpy.uint8)
    return image


def _generate_dummy_game_markee(game_name: str):
    width, height = 200, 50
    image = numpy.full((height, width, 4), 0, dtype=numpy.uint8)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    font_thickness = 2

    text_size = cv2.getTextSize(game_name, font, font_scale, font_thickness)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2

    cv2.putText(
        image,
        game_name,
        (text_x, text_y),
        font,
        font_scale,
        (0, 0, 0, 255),
        font_thickness + 5,
        cv2.LINE_AA,
    )
    cv2.putText(
        image,
        game_name,
        (text_x, text_y),
        font,
        font_scale,
        (255, 255, 255, 255),
        font_thickness,
        cv2.LINE_AA,
    )

    return image


def _make_game_node(roms_directory: Path, game_title: str, cover_size: tuple[int, int]):
    game_node = ElementTree.Element("game")

    def add_node(name, value):
        node = ElementTree.Element(name)
        node.text = value
        game_node.append(node)

    game_name = game_title.lower().replace(" ", "_")

    rom_path = roms_directory / f"{game_name}.txt"
    image_path = roms_directory / f"{game_name}_image.png"
    markee_path = roms_directory / f"{game_name}_markee.png"
    thumbnail_path = roms_directory / f"{game_name}_thumbnail.png"

    rom_path.touch()
    cv2.imwrite(str(image_path), _generate_dummy_game_image())
    cv2.imwrite(str(markee_path), _generate_dummy_game_markee(game_title))
    cv2.imwrite(str(thumbnail_path), _generate_dummy_game_cover(game_title, cover_size))

    add_node("path", str(rom_path))
    add_node("name", game_title)
    add_node("releasedate", _generate_random_date(datetime.datetime(1990, 1, 1)))
    add_node("players", "1-8")
    add_node("genre", "Action")
    add_node("developer", "Dummy Developer")
    add_node("publisher", "Dummy Publisher")
    add_node("lastplayed", _generate_random_date(datetime.datetime(2024, 1, 1)))
    add_node("gametime", str(random.randint(0, 100000)))
    add_node("rating", str(random.random()))
    add_node("desc", f"Dummy description for the game '{game_name}'. " * 20)
    add_node("image", str(image_path))
    add_node("marquee", str(markee_path))
    add_node("thumbnail", str(thumbnail_path))

    return game_node


def _generate_random_date(start: datetime.datetime):
    end = datetime.datetime(2025, 1, 1)
    timestamp = random.randint(int(start.timestamp()), int(end.timestamp()))
    dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    return dt.strftime("%Y%m%dT000000")


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

        cover_size = tuple(map(int, system_metadata.cover_size.split("-")))
        assert len(cover_size) == 2

        for i in range(random.randint(1, 20)):
            game_node = _make_game_node(
                system_roms_path, f"Dummy Game {i:02d}", cover_size
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
