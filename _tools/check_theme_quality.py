#!/usr/bin/env python3
from pathlib import Path
from rich.live import Live
from rich.spinner import Spinner
from rich.markup import escape
from rich.console import Console
from rich.padding import Padding
from rich.traceback import Traceback
from dataclasses import dataclass
import tempfile
import subprocess
from PIL import Image
import imagehash
from typing import Protocol, Generator
import sys
import lxml.etree
import re


@dataclass
class Success:
    file: Path


@dataclass
class Failure:
    file: Path
    reason: str


@dataclass
class Fix:
    file: Path
    reason: str


Result = Success | Failure | Fix


class CheckFunction(Protocol):
    __doc__: str

    def __call__(self) -> Generator[Result, None, None]: ...


def _base_dir() -> Path:
    """Return the root directory of the repository."""
    return Path(__file__).parent.parent


def _iter_files(folder_type: str):
    dir = _base_dir() / "_inc" / folder_type
    if not dir.exists():
        raise ValueError(f"Invalid folder: {folder_type}")
    for node in dir.iterdir():
        if not node.is_file():
            raise ValueError(f"Found unexpected non-file: {node}")
        if node.name.startswith("_"):
            continue
        yield node


def _find_files(ext: str):
    dir = _base_dir() / "_inc"
    yield from dir.glob(f"**/*.{ext.lstrip('.')}")


def _run_check(check: CheckFunction):
    description = escape(check.__doc__)
    spinner = Spinner("dots", style="blue", text=f"[blue]{description}[/]")

    successes: list[Success] = []
    fixes: list[Fix] = []
    failures: list[Failure] = []

    console = Console(highlighter=None)

    raised_exception: Exception | None = None

    with Live(spinner, console=console) as live:
        try:
            results = check() or []
            for result in results:
                if type(result) is Success:
                    successes.append(result)
                elif type(result) is Fix:
                    fixes.append(result)
                elif type(result) is Failure:
                    failures.append(result)
        except Exception as e:
            raised_exception = e

        total = len(successes) + len(fixes) + len(failures)

        if raised_exception or total == 0:
            live.update(f"[red][b]✘[/b] {description} [red bold]ERROR.[/]")
        elif not fixes and not failures:
            live.update(f"[green][b]✔[/b] {description} [green bold]PASS.[/]")
        elif not failures:
            live.update(f"[yellow][b]𝐢[/b] {description} [yellow bold]FIX.[/]")
        else:
            live.update(f"[red][b]✘[/b] {description} [red bold]FAIL.[/]")

    def inform(message: str):
        padding = Padding(f"➔ {message}", pad=(0, 4))
        console.print(padding)

    def ppath(path: Path):
        relpath_parents = path.parent.relative_to(_base_dir())
        return f"[dim]{relpath_parents}/[/dim][b]{path.name}[/b]"

    if raised_exception is not None:
        tb = Traceback.from_exception(
            type(raised_exception), raised_exception, raised_exception.__traceback__
        )
        padded_tb = Padding(tb, (0, 4))
        console.print(padded_tb)
        return False
    elif total == 0:
        inform("No files was checked, this must be an error.")
        return False
    elif not fixes and not failures:
        return True
    elif not failures:
        for fix in fixes:
            inform(f"{ppath(fix.file)}: {escape(fix.reason)}")
        return True
    else:
        for fix in fixes:
            inform(f"{ppath(fix.file)} (fixed): {escape(fix.reason)}")
        for fail in failures:
            inform(f"{ppath(fail.file)}: {escape(fail.reason)}")
        return False


def check_svg_formatting():
    """Check that SVG files are properly formatted."""
    for filepath in _find_files(".svg"):
        with open(filepath, "rb") as file:
            svg_content = file.read()

        parser = lxml.etree.XMLParser(
            remove_comments=False,
            no_network=True,
            remove_blank_text=False,
        )

        try:
            tree = lxml.etree.fromstring(svg_content, parser=parser)
        except Exception as e:
            yield Failure(filepath, f"Could not parse SVG file: {e}")
            continue

        svg = lxml.etree.ElementTree(tree)
        root = svg.getroot()

        for el in root.xpath(
            "//*[starts-with(name(), 'sodipodi:') or starts-with(name(), 'inkscape:')]"
        ):
            el.getparent().remove(el)

        for el in root.xpath("//*"):
            to_remove = [a for a in el.attrib if "inkscape" in a or "sodipodi" in a]
            for attr in to_remove:
                del el.attrib[attr]

        lxml.etree.cleanup_namespaces(root)

        inkscape_css_re = re.compile(r"-inkscape-[^;]+;?\s*")

        for el in root.xpath("//*[@style]"):
            style_text = el.get("style")

            new_style = inkscape_css_re.sub("", style_text).strip()

            new_style = new_style.rstrip(";")

            if new_style:
                el.set("style", new_style)
            else:
                del el.attrib["style"]

        lxml.etree.indent(root, space="    ")

        formatted = lxml.etree.tostring(
            root,
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=True,
        )
        formatted = formatted.rstrip(b"\n") + b"\n"

        if formatted == svg_content:
            yield Success(filepath)
            continue

        with open(filepath, "wb") as file:
            file.write(formatted)

        yield Fix(filepath, "Formatted SVG file")


def check_xml_formatting():
    """Check that XML files are properly formatted."""
    for filepath in _find_files(".xml"):
        with open(filepath, "rb") as file:
            xml_content = file.read()

        # Using `lxml` over `xml` built-in module because it can preserve root comments.
        parser = lxml.etree.XMLParser(remove_comments=False, no_network=True)

        try:
            tree = lxml.etree.fromstring(xml_content, parser=parser)
        except Exception as e:
            yield Failure(filepath, f"Could not parse XML file: {e}")
            continue

        root = lxml.etree.ElementTree(tree)

        lxml.etree.indent(root, space="  ")

        formatted = lxml.etree.tostring(
            root,
            encoding="utf-8",
            xml_declaration=False,
            pretty_print=True,
        )
        formatted = formatted.rstrip(b"\n") + b"\n"

        if formatted == xml_content:
            yield Success(filepath)
            continue

        with open(filepath, "wb") as file:
            file.write(formatted)

        yield Fix(filepath, "Formatted XML file")


def check_vector_image_dimensions():
    """Check that all SVG logos have correct dimensions."""
    for filepath in _iter_files("logos-svg"):
        with open(filepath, "rb") as file:
            svg_content = file.read()

        parser = lxml.etree.XMLParser(
            remove_comments=False,
            no_network=True,
            remove_blank_text=False,
        )

        try:
            tree = lxml.etree.fromstring(svg_content, parser=parser)
        except Exception as e:
            yield Failure(filepath, f"Could not parse SVG file: {e}")
            continue

        svg = lxml.etree.ElementTree(tree)

        root = svg.getroot()

        def num_unit(v):
            m = re.match(r"([\d.]+)([a-z%]*)", v.strip())
            return float(m.group(1)), m.group(2)

        def conv_unit(v, unit):
            if unit == "px" or unit == "":
                return float(v)
            elif unit == "pt":
                return float(v) * 1.25
            elif unit == "pc":
                return float(v) * 15
            elif unit == "in":
                return float(v) * 96
            elif unit == "cm":
                return float(v) * 96 / 2.54
            elif unit == "mm":
                return float(v) * 96 / 25.4
            else:
                raise ValueError(f"Unsupported unit: {unit}")

        view_box = root.get("viewBox")
        width = root.get("width")
        height = root.get("height")
        fixed = False

        if not view_box and (not width or not height):
            yield Failure(filepath, "SVG must have a viewBox or both width and height")
            continue

        if not width or not height:
            _, _, w, h = map(float, view_box.replace(",", " ").split())
        else:
            w = conv_unit(*num_unit(width))
            h = conv_unit(*num_unit(height))

        if not view_box:
            root.set("viewBox", f"0 0 {w} {h}")
            fixed = True

        target_w, target_h = 600, 300

        if w / h > target_w / target_h:
            if w != target_w:
                root.set("width", str(target_w))
                root.set("height", str(h * target_w / w))
                fixed = True
        else:
            if h != target_h:
                root.set("height", str(target_h))
                root.set("width", str(w * target_h / h))
                fixed = True

        if not fixed:
            yield Success(filepath)
            continue

        lxml.etree.indent(root, space="    ")

        formatted = lxml.etree.tostring(
            root,
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=True,
        )
        formatted = formatted.rstrip(b"\n") + b"\n"

        if formatted == svg_content:
            yield Success(filepath)
            continue

        with open(filepath, "wb") as file:
            file.write(formatted)

        yield Fix(filepath, "Rescaled SVG")


def check_raster_image_dimensions():
    """Check that all background and overlays have correct dimensions."""
    for dir in ["backgrounds", "overlays"]:
        for f in _iter_files(dir):
            with Image.open(f) as img:
                if img.size != (1920, 1080):
                    yield Failure(f, f"Invalid dimensions: {img.size}")
                else:
                    yield Success(f)


def check_systems_are_complete():
    """Check that each system with metadata also has all required images."""
    backgrounds = {file.stem for file in _iter_files("backgrounds")}
    controllers = {file.stem for file in _iter_files("controllers")}
    logos = {file.stem for file in _iter_files("logos")}

    for system in _iter_files("metadata"):
        if system.stem not in backgrounds:
            yield Failure(system, "Missing background")
        elif system.stem not in controllers:
            yield Failure(system, "Missing controller")
        elif system.stem not in logos:
            yield Failure(system, "Missing logo")
        else:
            yield Success(system)


def check_all_images_have_system():
    """Check that all images also have an associated system metadata."""
    systems = {file.stem for file in _iter_files("metadata")}

    for dir in ["backgrounds", "overlays", "logos", "controllers", "logos-svg"]:
        for f in _iter_files(dir):
            if f.stem not in systems:
                yield Failure(f, "No associated system metadata")
            else:
                yield Success(f)


def check_file_extensions():
    """Check that all files have the appropriate extension."""
    expected_extensions = {
        "backgrounds": ".webp",
        "controllers": ".webp",
        "logos": ".webp",
        "overlays": ".webp",
        "logos-svg": ".svg",
        "metadata": ".xml",
    }
    for dir, ext in expected_extensions.items():
        for file in _iter_files(dir):
            if file.suffix != ext:
                yield Failure(file, f"Expected a {ext} file but got: {file.suffix}")
            else:
                yield Success(file)


def check_metadata_is_complete():
    """Check that all required variables in systems metadata are present."""

    tags = [
        "systemName",
        "systemDescription",
        "systemManufacturer",
        "systemReleaseYear",
        "systemHardwareType",
        "systemCoverSize",
        "systemCartSize",
    ]

    for filepath in _iter_files("metadata"):
        tree = lxml.etree.parse(filepath)
        variables = tree.find("variables")

        if variables is None:
            yield Failure(filepath, "Missing primary <variables> tag")
            continue

        for tag in tags:
            data = variables.find(tag)

            if data is None:
                yield Failure(filepath, f"Missing <{tag}> tag in primary variables")
                continue

            if data.text is None or not data.text.strip():
                yield Failure(filepath, f"Empty <{tag}> tag in primary variables")
                continue
        else:
            yield Success(filepath)


def check_all_variables_fully_translated():
    """Check that all theme variables are translated."""

    theme_lang = _base_dir() / "_inc" / "ui-components" / "theme-lang.xml"

    tree = lxml.etree.parse(theme_lang)

    def get_child_tags(tree) -> set[str]:
        required_tags: set[str] = set()
        for child in tree.findall("*"):
            required_tags.add(child.tag)
        return required_tags

    variables = tree.find("variables")
    required_tags = get_child_tags(variables)

    for var in tree.findall(".//variables"):
        lang = var.get("lang")

        if lang is None:
            continue

        lang = lang.strip().lower()

        lang_tags = get_child_tags(var)

        for tag in required_tags:
            try:
                lang_tags.remove(tag)
            except KeyError:
                yield Failure(theme_lang, f"Missing <{tag}> in language: {lang}")

        if lang_tags:
            unexpected = ", ".join(lang_tags)
            yield Failure(
                theme_lang, f"Unexpected tags in language {lang}: {unexpected}"
            )

    yield Success(theme_lang)


def check_all_systems_fully_translated():
    """Check that all metadata files have translations for all required languages."""

    theme_lang = _base_dir() / "_inc" / "ui-components" / "theme-lang.xml"

    tree = lxml.etree.parse(theme_lang)

    required_langs: set[str] = set()

    for var in tree.findall(".//variables"):
        lang = var.get("lang")
        if lang is None:
            continue
        required_langs.add(lang.strip().lower())

    if not required_langs:
        yield Failure(theme_lang, "No languages found")
        return

    for filepath in _iter_files("metadata"):
        tree = lxml.etree.parse(filepath)
        variables = tree.findall("variables")

        expected_langs = required_langs.copy()

        for var in variables:
            lang = var.get("lang")

            if lang is None:
                continue

            lang = lang.strip().lower()

            try:
                expected_langs.remove(lang)
            except KeyError:
                yield Failure(filepath, f"Unexpected language: {lang}")

        if expected_langs:
            missing = ", ".join(sorted(expected_langs))
            yield Failure(filepath, f"Missing translations: {missing}")
        else:
            yield Success(filepath)


def check_no_missing_collections():
    """Check that no collections are missing from the collections metadata file."""

    system_collections: list[Path] = []
    for filepath in _iter_files("metadata"):
        tree = lxml.etree.parse(filepath)
        variables = tree.find("variables")
        hardware = variables.find("systemHardwareType")

        if hardware.text in ["${i18n.custom-collection}", "${i18n.auto-collection}"]:
            system_collections.append(filepath)

    theme_collections: set[str] = set()
    collections_file = _base_dir() / "collections.info"
    with open(collections_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            theme_collections.add(line.strip())

    for system in system_collections:
        try:
            theme_collections.remove(system.stem)
        except KeyError:
            yield Failure(system, "Collection not referenced")
        else:
            yield Success(system)

    if theme_collections:
        unexpected = ", ".join(theme_collections)
        yield Failure(
            collections_file, f"Collections file has extra entries: {unexpected}"
        )


def check_duplicated_backgrounds():
    """Check that no two background images are visually the same."""
    hash_dict: dict[imagehash.ImageHash, Path] = {}

    for filepath in _iter_files("backgrounds"):
        with Image.open(filepath) as img:
            img_hash = imagehash.phash(img)

        if img_hash in hash_dict:
            other_file = hash_dict[img_hash]
            yield Failure(
                filepath,
                f"Visually identical to {other_file.name!r}",
            )
        else:
            hash_dict[img_hash] = filepath
            yield Success(filepath)


def check_overlays_match_their_backgrounds():
    """Check that overlay images match their corresponding background images."""
    for overlay_file in _iter_files("overlays"):
        background_file = _base_dir() / "_inc" / "backgrounds" / overlay_file.name

        if not background_file.exists():
            yield Failure(overlay_file, "Missing background")
            continue

        with Image.open(overlay_file).convert("RGBA") as overlay_image:
            overlay_alpha = overlay_image.split()[-1]
            overlay_mask = overlay_alpha.point(lambda p: 255 if p == 255 else 0)

            overlay_masked = Image.new("RGB", overlay_image.size, (255, 255, 255))
            overlay_masked.paste(overlay_image, mask=overlay_mask)

        with Image.open(background_file).convert("RGBA") as background_image:
            background_masked = Image.new("RGB", background_image.size, (255, 255, 255))
            background_masked.paste(background_image, mask=overlay_mask)

        width, height = overlay_image.size
        block_distances = []

        for y in range(0, height, 256):
            for x in range(0, width, 256):
                box = (x, y, x + 256, y + 256)

                mask_block = overlay_mask.crop(box)

                # Blocks that are fully transparent must be ignored.
                if not any(mask_block.get_flattened_data()):
                    continue

                overlay_block = overlay_masked.crop(box)
                background_block = background_masked.crop(box)

                overlay_hash = imagehash.phash(overlay_block)
                background_hash = imagehash.phash(background_block)

                block_distances.append(background_hash - overlay_hash)

        if max(block_distances) > 5:
            yield Failure(overlay_file, "Overlay does not match background visually")
        else:
            yield Success(overlay_file)


def verify_theme_quality():
    checks: list[CheckFunction] = [
        check_vector_image_dimensions,
        check_raster_image_dimensions,
        check_svg_formatting,
        check_xml_formatting,
        check_systems_are_complete,
        check_all_images_have_system,
        check_file_extensions,
        check_metadata_is_complete,
        check_all_variables_fully_translated,
        check_all_systems_fully_translated,
        check_no_missing_collections,
        check_duplicated_backgrounds,
        check_overlays_match_their_backgrounds,
    ]

    console = Console(highlighter=None)
    succeeded_count = 0

    for check in checks:
        succeeded_count += _run_check(check)

    if succeeded_count != len(checks):
        console.print(
            f"[bold]Final result:[/] [red bold]FAILURE[/] "
            f"({succeeded_count} out of {len(checks)} checks passed)."
        )
        return False

    console.print(
        f"[bold]Final result:[/] [green bold]SUCCESS[/] "
        f"({succeeded_count} out of {len(checks)} checks passed)."
    )
    return True


if __name__ == "__main__":
    if not verify_theme_quality():
        sys.exit(1)
