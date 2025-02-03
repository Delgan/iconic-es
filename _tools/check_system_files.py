#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify that system resources (metadata / images) are complete, "
        "ensuring no file is missing in any of the source folders."
    )

    workspace = Path(__file__).resolve().parent.parent
    resources = workspace / "_inc"

    metadata = resources / "metadata"
    background_art = resources / "backgrounds"
    logo = resources / "logos"
    controller = resources / "controllers"

    folders = [metadata, background_art, logo, controller]
    files = [(folder, [file.stem for file in folder.glob("*")]) for folder in folders]

    all_systems = {file for _, filenames in files for file in filenames}

    has_missing = False

    for system in all_systems:
        if system in ["_default", "_builtin"]:
            continue
        if any(system not in filenames for _, filenames in files):
            has_missing = True
            print(f"Incomplete system: {system}", file=sys.stderr)
            for folder, filenames in files:
                print(f"    In {folder.stem}: {system in filenames}")

    if has_missing:
        sys.exit(1)
