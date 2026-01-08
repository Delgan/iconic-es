#!/usr/bin/env python3
"""Pull system metadata XML files from ES-DE GitLab repository and update local copies."""

import os
import tarfile
import tempfile
from pathlib import Path
import requests
import copy
import xml.etree.ElementTree as ET


def download_tar_gz(dest_path: Path) -> Path:
    branch = "master"
    base_url = "https://gitlab.com/es-de/themes/system-metadata"
    url = f"{base_url}/-/archive/{branch}/system-metadata-{branch}.tar.gz"
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return dest_path


def extract_tar(tar_path: Path, extract_to: Path) -> None:
    with tarfile.open(tar_path, "r:gz") as tf:
        tf.extractall(path=extract_to)


def find_xml_files(root: Path):
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.lower().endswith(".xml"):
                continue
            if fn.startswith("_"):
                continue
            yield Path(dirpath) / fn


def normalize_remote_filename(fn: str) -> str:
    base, ext = os.path.splitext(fn)

    aliases = {
        "n3ds": "3ds",
        "atarixe": "xegs",
        "pcenginecd": "pce-cd",
        "cdtv": "amigacdtv",
        "cdimono1": "cdi",
        "crvision": "creativision",
        "plus4": "cplus4",
        "vic20": "c20",
        "moto": "thomson",
    }

    mapped = aliases.get(base, base)
    return f"{mapped}{ext}"


def local_metadata_dir() -> Path:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    return (repo_root / "_inc" / "metadata").resolve()


def transform_theme_file(remote_path: Path, local_path: Path) -> str:
    remote_tree = ET.parse(remote_path).getroot()
    local_tree = ET.parse(local_path).getroot()

    remote_variables = remote_tree.find("variables")
    local_variables = local_tree.find("variables")

    new_theme = ET.Element("theme")
    new_variables = ET.Element("variables")

    for var in local_variables:
        tag = var.tag
        remote_var = remote_variables.find(tag)

        # These one would be overwritten with "Collection", but I like the distinctions
        # between "Auto" and "Custom" collections.
        is_hardware = tag == "systemHardwareType"
        is_collec = var.text in ["Auto Collection", "Custom Collection"]
        force_local = is_hardware and is_collec

        if force_local or remote_var is None:
            new_variables.append(copy.deepcopy(var))
        else:
            new_variables.append(copy.deepcopy(remote_var))

    new_theme.append(new_variables)

    lang_codes = set()

    for lang_elem in remote_tree.findall("language"):
        name = lang_elem.get("name")
        if not name:
            continue
        lang_code, *_ = name.split("_")

        # Mandatory to avoid duplicates such as "zh_CN / zh_TW" and "pt_BR / pt_PT".
        # EmlulationStation does not support regional lang variants (afaik).
        if lang_code in lang_codes:
            continue

        lang_codes.add(lang_code)

        vars_elem = lang_elem.find("variables")
        if vars_elem is None:
            continue

        localized_vars = ET.Element("variables")
        localized_vars.set("lang", lang_code)
        for child in vars_elem:
            localized_vars.append(copy.deepcopy(child))

        new_theme.append(localized_vars)

    ET.indent(new_theme, space="  ")
    text = ET.tostring(new_theme, encoding="utf-8").decode("utf-8")
    text = text.strip() + "\n"
    return text


def main():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tar_file = Path(tmp_dir) / "system-metadata.tar.gz"

        print("Downloading latest archive...")
        download_tar_gz(tar_file)
        extract_to = Path(tmp_dir) / "extracted"
        extract_to.mkdir()

        print("Extracting archive...")
        extract_tar(tar_file, extract_to)

        local_dir = local_metadata_dir()
        if not local_dir.exists():
            raise RuntimeError(f"Local metadata directory not found at: {local_dir}")

        skipped_count = 0
        unchanged_count = 0
        updated_count = 0

        remote_files = list(find_xml_files(extract_to))

        for remote_path in remote_files:
            remote_name = remote_path.name
            normalized = normalize_remote_filename(remote_name)
            local_path = local_dir / normalized

            if not local_path.exists():
                print(f"Skipping {remote_name}: (no local equivalent)")
                skipped_count += 1
                continue

            out_text = transform_theme_file(remote_path, local_path)

            with open(local_path, "r", encoding="utf-8") as f:
                data = f.read()

            if data == out_text:
                unchanged_count += 1
                continue

            with open(local_path, "w", encoding="utf-8") as f:
                f.write(out_text)

            print("Updated:", local_path.name)
            updated_count += 1

        missing_count = 0
        remotes = {normalize_remote_filename(f.name) for f in remote_files}
        for f in find_xml_files(local_dir):
            if normalize_remote_filename(f.name) not in remotes:
                print(f"Missing: {f.name} (no remote equivalent)")
                missing_count += 1

        print("\nSummary:")
        print(f"  Unchanged files: {unchanged_count}")
        print(f"  Updated files: {updated_count}")
        print(f"  Skipped files: {skipped_count}")
        print(f"  Missing files: {missing_count}")


if __name__ == "__main__":
    main()
