from pathlib import Path
from rich.live import Live
from rich.spinner import Spinner
from rich.markup import escape
from rich.console import Console
from rich.padding import Padding
from rich.traceback import Traceback
from dataclasses import dataclass
from PIL import Image
from typing import Protocol, Generator
import sys
import lxml.etree
import traceback


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


def _iter_files(folder_type: str):
    dir = Path(__file__).parent.parent / "_inc" / folder_type
    if not dir.exists():
        raise ValueError(f"Invalid folder: {folder_type}")
    for node in dir.iterdir():
        if not node.is_file():
            raise ValueError(f"Found unexpected non-file: {node}")
        if node.name.startswith("_"):
            continue
        yield node


def _find_files(ext: str):
    dir = Path(__file__).parent.parent / "_inc"
    yield from dir.glob(f"**/*.{ext.lstrip('.')}")


def _run_check(check: CheckFunction):
    description = escape(check.__doc__)
    spinner = Spinner("dots", text=description)

    successes: list[Success] = []
    fixes: list[Fix] = []
    failures: list[Failure] = []

    console = Console(highlighter=None)

    raised_exception: Exception | None = None

    with Live(spinner, console=console) as live:
        try:
            for result in check():
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
        base = Path(__file__).parent.parent
        relpath_parents = path.parent.relative_to(base)
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


def check_image_dimensions():
    """Check that all backgrounds and overlays are FHD (1920x1080)."""
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
            yield Failure(system, "Missing controller")
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
    collections_file = Path(__file__).parent.parent / "collections.info"
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


def verify_theme_quality():
    checks: list[CheckFunction] = [
        check_xml_formatting,
        check_image_dimensions,
        check_systems_are_complete,
        check_all_images_have_system,
        check_file_extensions,
        check_metadata_is_complete,
        check_no_missing_collections,
    ]

    all_succeeded = True

    for check in checks:
        all_succeeded &= _run_check(check)

    return all_succeeded


if __name__ == "__main__":
    if not verify_theme_quality():
        sys.exit(1)
