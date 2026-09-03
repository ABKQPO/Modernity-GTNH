from __future__ import annotations

import argparse
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image


MATERIAL_ICON_DIRECTORY = Path("assets/gregtech/textures/items/materialicons")
HANDLE_TEXTURE = Path("assets/gregtech/textures/items/iconsets/HANDLE_SOLDERING_OVERLAY.png")
TOOL_HEAD_PATTERN = "toolHeadSoldering*.png"


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def collect_targets(root: Path) -> list[Path]:
    material_icon_directory = root / MATERIAL_ICON_DIRECTORY
    handle_texture = root / HANDLE_TEXTURE

    if not material_icon_directory.is_dir():
        raise FileNotFoundError(f"Material icon directory not found: {material_icon_directory}")
    if not handle_texture.is_file():
        raise FileNotFoundError(f"Handle texture not found: {handle_texture}")

    tool_heads = material_icon_directory.rglob(TOOL_HEAD_PATTERN)
    return sorted({*tool_heads, handle_texture}, key=lambda path: path.as_posix().lower())


def flip_horizontally(path: Path) -> None:
    with Image.open(path) as image:
        flipped = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        with NamedTemporaryFile(dir=path.parent, suffix=".png", delete=False) as temporary_file:
            temporary_path = Path(temporary_file.name)
        try:
            flipped.save(temporary_path, format="PNG")
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Horizontally flip soldering iron textures.")
    parser.add_argument(
        "--root",
        type=Path,
        default=repository_root(),
        help="Modernity-GTNH repository root. Defaults to this script's parent directory.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Replace the matched textures. Without this flag, the script only lists targets.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    root = arguments.root.resolve()
    targets = collect_targets(root)

    print(f"Found {len(targets)} texture(s).")
    for path in targets:
        print(path.relative_to(root))

    if not arguments.apply:
        print("Dry run complete. Re-run with --apply to flip these textures.")
        return

    for path in targets:
        flip_horizontally(path)
    print(f"Flipped {len(targets)} texture(s).")


if __name__ == "__main__":
    main()
