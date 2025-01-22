#!/usr/bin/env python3
import argparse
from pathlib import Path
from xml.etree import ElementTree
import sys


def simplify_metadata_file(metadata: Path):
    tree = ElementTree.parse(metadata)
    root = tree.getroot()

    variables_node = root.find("variables")
    if variables_node is None:
        raise ValueError(f"Missing variables node in {metadata}")

    nodes = [
        "systemName",
        "systemDescription",
        "systemManufacturer",
        "systemReleaseYear",
        "systemHardwareType",
        "systemCoverSize",
        "systemCartSize",
    ]

    new_tree = ElementTree.ElementTree(ElementTree.Element("theme"))
    new_root = new_tree.getroot()
    new_variables_node = ElementTree.Element("variables")
    new_root.append(new_variables_node)

    for node_name in nodes:
        node = variables_node.find(node_name)
        if node is None:
            raise ValueError(f"Missing {node_name} node in {metadata}")

        if node.text is None:
            raise ValueError(f"Empty {node_name} node in {metadata}")

        new_variables_node.append(node)

    ElementTree.indent(new_root, level=0, space="  ")

    new_tree.write(
        metadata, encoding="utf-8", xml_declaration=False, short_empty_elements=False
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove fields from metadata files that are not used by this theme, "
        "and ensure the required one are present."
    )

    workspace = Path(__file__).resolve().parent.parent
    metadata = workspace / "_inc" / "metadata"

    has_incomplete = False

    for file in metadata.glob("*.xml"):
        if file.name == "_builtin.xml":
            continue

        try:
            simplify_metadata_file(file)
        except ValueError as err:
            has_incomplete = True
            print(f"Incomplete metadata '{file.stem}': {err}")

    if has_incomplete:
        sys.exit(1)
