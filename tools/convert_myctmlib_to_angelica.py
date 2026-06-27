from __future__ import annotations

import json
import os
import re
import stat
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image


DEFAULT_OUTPUT_DIR = Path("output")
MANUAL_DOC_PATH = Path("output") / "MANUAL_CTMS.md"
MCPATCHER_CTM_ROOT = Path("assets") / "minecraft" / "mcpatcher" / "ctm"


@dataclass(frozen=True)
class MyCtmEntry:
    png_path: Path
    mcmeta_path: Path
    texture_path: str
    texture_name: str
    texture_rel_name: str
    mod_namespace: str
    config: dict[str, Any]


@dataclass(frozen=True)
class ConversionResult:
    total_entries: int
    converted_entries: int
    manual_entries: int
    copied_files: int
    generated_files: int


def normalize_resource_name(resource_name: str) -> str:
    value = resource_name.replace("\\", "/")
    if value.startswith("minecraft:"):
        value = value[len("minecraft:") :]
    value = value.replace("textures/blocks/", "")
    if value.endswith(".png"):
        value = value[:-4]
    return value


def texture_path_to_resource_name(texture_path: str) -> str:
    path = Path(texture_path)
    parts = path.parts
    if len(parts) < 4 or parts[0] != "assets":
        raise ValueError(f"Unexpected texture path: {texture_path}")
    namespace = parts[1]
    start_index = 3
    if len(parts) >= 5 and parts[2] == "textures" and parts[3] == "blocks":
        start_index = 4
    relative = Path(*parts[start_index:]).with_suffix("")
    return f"{namespace}:{relative.as_posix()}"


def resource_relative_name(resource_name: str) -> str:
    normalized = normalize_resource_name(resource_name)
    if ":" in normalized:
        return normalized.split(":", 1)[1]
    return normalized


def parse_mcmeta(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        sanitized = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', text)
        try:
            data = json.loads(sanitized)
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def strip_mcmeta_suffix(path: Path) -> Path:
    return path.with_suffix("") if path.suffix == ".mcmeta" else path


def resolve_entry_png(repo_root: Path, mcmeta_path: Path) -> Path | None:
    direct_png = strip_mcmeta_suffix(mcmeta_path)
    if direct_png.is_file():
        return direct_png
    if direct_png.suffix != ".png":
        direct_png_with_ext = direct_png.with_suffix(".png")
        if direct_png_with_ext.is_file():
            return direct_png_with_ext

    relative_mcmeta = mcmeta_path.relative_to(repo_root)
    if len(relative_mcmeta.parts) >= 4 and relative_mcmeta.parts[0] == "assets":
        namespace = relative_mcmeta.parts[1]
        tail = relative_mcmeta.parts[2:]
        if tail and tail[0] == "blocks":
            candidate = repo_root / "assets" / namespace / "textures" / Path(*tail)
            candidate = strip_mcmeta_suffix(candidate)
            if candidate.is_file():
                return candidate
            if candidate.suffix != ".png":
                candidate_with_ext = candidate.with_suffix(".png")
                if candidate_with_ext.is_file():
                    return candidate_with_ext
        if tail and tail[0] == "textures":
            candidate = repo_root / "assets" / namespace / Path(*tail)
            candidate = strip_mcmeta_suffix(candidate)
            if candidate.is_file():
                return candidate
            stem = strip_mcmeta_suffix(Path(*tail)).stem
            if stem.endswith("lightblue"):
                aliased_stem = stem[:-9] + "light_blue"
                candidate = repo_root / "assets" / namespace / "textures" / Path(*tail[1:]).with_name(aliased_stem + ".png")
                if candidate.is_file():
                    return candidate
    return None


def candidate_mcmeta_relatives(entry: MyCtmEntry, repo_root: Path) -> list[Path]:
    candidates: list[Path] = []
    if entry.mcmeta_path.is_absolute():
        candidates.append(entry.mcmeta_path.relative_to(repo_root))
    else:
        candidates.append(entry.mcmeta_path)

    if entry.png_path.is_absolute():
        png_relative = entry.png_path.relative_to(repo_root)
    else:
        png_relative = entry.png_path
    candidates.append(Path(str(png_relative) + ".mcmeta"))
    candidates.append(png_relative.with_suffix(".mcmeta"))

    if len(png_relative.parts) >= 4 and png_relative.parts[0] == "assets" and png_relative.parts[2] == "textures":
        namespace = png_relative.parts[1]
        tail = png_relative.parts[3:]
        if tail and tail[0] == "blocks":
            block_alias = Path("assets") / namespace / Path(*tail)
            candidates.append(Path(str(block_alias) + ".mcmeta"))
            candidates.append(block_alias.with_suffix(".mcmeta"))

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.as_posix()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def discover_myctm_entries(repo_root: Path) -> list[MyCtmEntry]:
    entries: list[MyCtmEntry] = []
    for mcmeta_path in sorted(repo_root.joinpath("assets").rglob("*.mcmeta")):
        data = parse_mcmeta(mcmeta_path)
        if data is None:
            continue
        config = data.get("myctmlib")
        if not isinstance(config, dict):
            continue
        png_path = resolve_entry_png(repo_root, mcmeta_path)
        if png_path is None:
            continue
        relative = png_path.relative_to(repo_root).as_posix()
        resource_name = texture_path_to_resource_name(relative)
        entries.append(
            MyCtmEntry(
                png_path=png_path,
                mcmeta_path=mcmeta_path,
                texture_path=relative,
                texture_name=normalize_resource_name(resource_name),
                texture_rel_name=resource_relative_name(resource_name),
                mod_namespace=relative.split("/")[1],
                config=config,
            )
        )
    return entries


def classify_entry(entry: MyCtmEntry) -> list[str]:
    reasons: list[str] = []
    config = entry.config
    if "connection" not in config or not isinstance(config["connection"], str) or not config["connection"].strip():
        reasons.append("missing connection texture")
    if "random" in config:
        reasons.append("uses random texture variants")
    return reasons


def resolve_texture_png(repo_root: Path, resource_name: str, default_namespace: str) -> Path:
    normalized = resource_name.replace("\\", "/").strip()
    namespace = default_namespace
    relative = normalized
    if ":" in normalized:
        namespace, relative = normalized.split(":", 1)
    relative_path = Path(relative + ".png")
    candidates = [
        repo_root / "assets" / namespace / "textures" / relative_path,
        repo_root / "assets" / namespace / relative_path,
        repo_root / "assets" / namespace / "textures" / "blocks" / relative_path,
        repo_root / "assets" / namespace / "blocks" / relative_path,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def split_grid(image: Image.Image, columns: int, rows: int, col: int, row: int) -> Image.Image:
    tile_width = image.width // columns
    tile_height = image.height // rows
    left = col * tile_width
    top = row * tile_height
    return image.crop((left, top, left + tile_width, top + tile_height))


def make_quadrant_sprite(quadrants: tuple[Image.Image, Image.Image, Image.Image, Image.Image]) -> Image.Image:
    top_left, top_right, bottom_right, bottom_left = quadrants
    width = top_left.width + top_right.width
    height = top_left.height + bottom_left.height
    result = Image.new("RGBA", (width, height))
    result.paste(top_left, (0, 0))
    result.paste(top_right, (top_left.width, 0))
    result.paste(bottom_right, (top_left.width, top_left.height))
    result.paste(bottom_left, (0, top_left.height))
    return result


def build_compact_tiles(base_image: Image.Image, ctm_image: Image.Image) -> list[Image.Image]:
    base_quads = (
        split_grid(base_image, 2, 2, 0, 0),
        split_grid(base_image, 2, 2, 1, 0),
        split_grid(base_image, 2, 2, 1, 1),
        split_grid(base_image, 2, 2, 0, 1),
    )
    ctm_quads: dict[int, Image.Image] = {}
    for index in range(1, 17):
        row = (index - 1) // 4
        col = (index - 1) % 4
        ctm_quads[index] = split_grid(ctm_image, 4, 4, col, row)

    default_sprite = make_quadrant_sprite(base_quads)
    all_sprite = make_quadrant_sprite((ctm_quads[1], ctm_quads[2], ctm_quads[6], ctm_quads[5]))
    horizontal_sprite = make_quadrant_sprite((ctm_quads[9], ctm_quads[10], ctm_quads[14], ctm_quads[13]))
    vertical_sprite = make_quadrant_sprite((ctm_quads[3], ctm_quads[4], ctm_quads[8], ctm_quads[7]))
    mixed_sprite = make_quadrant_sprite((ctm_quads[11], ctm_quads[12], ctm_quads[16], ctm_quads[15]))
    return [default_sprite, all_sprite, horizontal_sprite, vertical_sprite, mixed_sprite]


CTM_NEIGHBOR_MAP = (
    0, 3, 0, 3, 12, 5, 12, 15, 0, 3, 0, 3, 12, 5, 12, 15,
    1, 2, 1, 2, 4, 7, 4, 29, 1, 2, 1, 2, 13, 31, 13, 14,
    0, 3, 0, 3, 12, 5, 12, 15, 0, 3, 0, 3, 12, 5, 12, 15,
    1, 2, 1, 2, 4, 7, 4, 29, 1, 2, 1, 2, 13, 31, 13, 14,
    36, 17, 36, 17, 24, 19, 24, 43, 36, 17, 36, 17, 24, 19, 24, 43,
    16, 18, 16, 18, 6, 46, 6, 21, 16, 18, 16, 18, 28, 9, 28, 22,
    36, 17, 36, 17, 24, 19, 24, 43, 36, 17, 36, 17, 24, 19, 24, 43,
    37, 40, 37, 40, 30, 8, 30, 34, 37, 40, 37, 40, 25, 23, 25, 45,
    0, 3, 0, 3, 12, 5, 12, 15, 0, 3, 0, 3, 12, 5, 12, 15,
    1, 2, 1, 2, 4, 7, 4, 29, 1, 2, 1, 2, 13, 31, 13, 14,
    0, 3, 0, 3, 12, 5, 12, 15, 0, 3, 0, 3, 12, 5, 12, 15,
    1, 2, 1, 2, 4, 7, 4, 29, 1, 2, 1, 2, 13, 31, 13, 14,
    36, 39, 36, 39, 24, 41, 24, 27, 36, 39, 36, 39, 24, 41, 24, 27,
    16, 42, 16, 42, 6, 20, 6, 10, 16, 42, 16, 42, 28, 35, 28, 44,
    36, 39, 36, 39, 24, 41, 24, 27, 36, 39, 36, 39, 24, 41, 24, 27,
    37, 38, 37, 38, 30, 11, 30, 32, 37, 38, 37, 38, 25, 33, 25, 26,
)


def build_full_ctm_tiles(base_image: Image.Image, ctm_image: Image.Image, alt_image: Image.Image) -> list[Image.Image]:
    base_quads = {
        17: split_grid(base_image, 2, 2, 0, 0),
        18: split_grid(base_image, 2, 2, 1, 0),
        19: split_grid(base_image, 2, 2, 1, 1),
        20: split_grid(base_image, 2, 2, 0, 1),
    }
    alt_quads = {
        21: split_grid(alt_image, 2, 2, 0, 0),
        22: split_grid(alt_image, 2, 2, 1, 0),
        23: split_grid(alt_image, 2, 2, 1, 1),
        24: split_grid(alt_image, 2, 2, 0, 1),
    }
    ctm_quads: dict[int, Image.Image] = {}
    for index in range(1, 17):
        row = (index - 1) // 4
        col = (index - 1) % 4
        ctm_quads[index] = split_grid(ctm_image, 4, 4, col, row)

    result: list[Image.Image] = []
    for ctm_index in range(47):
        quadrants = tuple(resolve_full_ctm_quadrant(icon_idx, ctm_quads, base_quads, alt_quads) for icon_idx in full_ctm_icon_indexes(ctm_index))
        result.append(make_quadrant_sprite(quadrants))
    return result


def resolve_full_ctm_quadrant(
    icon_index: int,
    ctm_quads: dict[int, Image.Image],
    base_quads: dict[int, Image.Image],
    alt_quads: dict[int, Image.Image],
) -> Image.Image:
    if icon_index in ctm_quads:
        return ctm_quads[icon_index]
    if icon_index in alt_quads:
        return alt_quads[icon_index]
    return base_quads[icon_index]


def full_ctm_icon_indexes(ctm_index: int) -> tuple[int, int, int, int]:
    neighbor_bits = next(bits for bits, mapped in enumerate(CTM_NEIGHBOR_MAP) if mapped == ctm_index)
    connections = [(neighbor_bits & (1 << bit)) != 0 for bit in range(8)]

    indices = [17, 18, 19, 20]
    if connections[7]:
        indices[0] = 1
    elif connections[3] and connections[0]:
        indices[0] = 11
    elif connections[3]:
        indices[0] = 9
    elif connections[0]:
        indices[0] = 3

    if connections[4]:
        indices[1] = 2
    elif connections[0] and connections[1]:
        indices[1] = 12
    elif connections[0]:
        indices[1] = 4
    elif connections[1]:
        indices[1] = 10

    if connections[6]:
        indices[2] = 5
    elif connections[2] and connections[3]:
        indices[2] = 15
    elif connections[2]:
        indices[2] = 7
    elif connections[3]:
        indices[2] = 13

    if connections[5]:
        indices[3] = 6
    elif connections[1] and connections[2]:
        indices[3] = 16
    elif connections[1]:
        indices[3] = 14
    elif connections[2]:
        indices[3] = 8

    if not all(17 <= value <= 20 for value in indices):
        indices = [
            21 if value == 17 else 22 if value == 18 else 23 if value == 19 else 24 if value == 20 else value
            for value in indices
        ]
    return tuple(indices)


def write_properties(
    output_path: Path,
    entry: MyCtmEntry,
    equivalents: list[str],
    *,
    method: str,
    tile_range: str,
) -> None:
    match_tiles = [entry.texture_name]
    match_tiles.extend(normalize_resource_name(value) for value in equivalents)
    lines = [
        f"matchTiles={' '.join(match_tiles)}",
        f"method={method}",
        f"tiles={tile_range}",
        "connect=tile",
    ]
    ensure_parent(output_path)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_repo_to_output(repo_root: Path, output_root: Path) -> int:
    if output_root.exists():
        shutil.rmtree(output_root, onerror=handle_remove_readonly)
    output_root.mkdir(parents=True)
    copied = 0
    for path in repo_root.rglob("*"):
        if path == output_root or output_root in path.parents:
            continue
        if ".git" in path.parts:
            continue
        relative = path.relative_to(repo_root)
        destination = output_root / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        ensure_parent(destination)
        shutil.copy2(path, destination)
        copied += 1
    return copied


def handle_remove_readonly(func: Any, path: str, _: Any) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def strip_myctmlib_metadata(repo_root: Path, output_root: Path, entry: MyCtmEntry) -> None:
    for relative_mcmeta in candidate_mcmeta_relatives(entry, repo_root):
        output_mcmeta = output_root / relative_mcmeta
        if not output_mcmeta.is_file():
            continue
        data = parse_mcmeta(output_mcmeta)
        if not isinstance(data, dict) or "myctmlib" not in data:
            continue
        data.pop("myctmlib", None)
        if data:
            output_mcmeta.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            output_mcmeta.unlink()


def remove_generated_source_textures(output_root: Path, repo_root: Path, entry: MyCtmEntry) -> None:
    connection_name = normalize_resource_name(entry.config["connection"])
    connection_png = resolve_texture_png(repo_root, connection_name, entry.mod_namespace)
    output_connection_png = output_root / connection_png.relative_to(repo_root)
    if output_connection_png.is_file():
        output_connection_png.unlink()
    output_connection_mcmeta = output_connection_png.with_suffix(output_connection_png.suffix + ".mcmeta")
    if output_connection_mcmeta.is_file():
        output_connection_mcmeta.unlink()

    alt_name = entry.config.get("alt")
    if isinstance(alt_name, str) and alt_name.strip():
        alt_png = resolve_texture_png(repo_root, normalize_resource_name(alt_name), entry.mod_namespace)
        output_alt_png = output_root / alt_png.relative_to(repo_root)
        if output_alt_png.is_file():
            output_alt_png.unlink()
        output_alt_mcmeta = output_alt_png.with_suffix(output_alt_png.suffix + ".mcmeta")
        if output_alt_mcmeta.is_file():
            output_alt_mcmeta.unlink()


def convert_entry(repo_root: Path, output_root: Path, entry: MyCtmEntry) -> int:
    connection_name = normalize_resource_name(entry.config["connection"])
    connection_png = resolve_texture_png(repo_root, connection_name, entry.mod_namespace)
    if not connection_png.is_file():
        raise FileNotFoundError(f"Missing connection texture for {entry.texture_path}: {connection_png}")

    alt_name = entry.config.get("alt")
    alt_png = None
    if isinstance(alt_name, str) and alt_name.strip():
        alt_png = resolve_texture_png(repo_root, normalize_resource_name(alt_name), entry.mod_namespace)
        if not alt_png.is_file():
            raise FileNotFoundError(f"Missing alt texture for {entry.texture_path}: {alt_png}")

    with Image.open(entry.png_path) as base_image_raw, Image.open(connection_png) as ctm_image_raw:
        base_image = base_image_raw.convert("RGBA")
        ctm_image = ctm_image_raw.convert("RGBA")
        if alt_png is None:
            generated_tiles = build_compact_tiles(base_image, ctm_image)
            method = "compact"
            tile_range = "0-4"
        else:
            with Image.open(alt_png) as alt_image_raw:
                alt_image = alt_image_raw.convert("RGBA")
                generated_tiles = build_full_ctm_tiles(base_image, ctm_image, alt_image)
            method = "ctm"
            tile_range = "0-46"

    ctm_dir = output_root / MCPATCHER_CTM_ROOT / entry.mod_namespace / Path(entry.texture_rel_name)
    generated = 0
    for index, tile in enumerate(generated_tiles):
        tile_path = ctm_dir / f"{index}.png"
        ensure_parent(tile_path)
        tile.save(tile_path)
        generated += 1

    write_properties(
        ctm_dir / f"{Path(entry.texture_name).name}.properties",
        entry,
        [value for value in entry.config.get("equivalents", []) if isinstance(value, str)],
        method=method,
        tile_range=tile_range,
    )
    generated += 1
    strip_myctmlib_metadata(repo_root, output_root, entry)
    remove_generated_source_textures(output_root, repo_root, entry)
    return generated


def write_manual_doc(
    output_root: Path,
    manual_entries: list[tuple[MyCtmEntry, list[str]]],
) -> None:
    lines = [
        "# Manual CTM Follow-up",
        "",
        "These entries need manual review or follow-up after compact CTM generation.",
        "",
        "## Reasons",
        "",
        "- `random`: MyCTMLib can select per-block random variants. This needs a separate non-compact CTM strategy if you want to preserve exact behavior.",
        "",
        "## Not Converted Automatically",
        "",
    ]
    if not manual_entries:
        lines.append("No manual follow-up entries.")
    else:
        for entry, reasons in manual_entries:
            lines.append(f"- `{entry.texture_path}`")
            lines.append(f"  Reasons: {', '.join(reasons)}")
            lines.append(f"  Connection: `{entry.config.get('connection', '')}`")
            if "alt" in entry.config:
                lines.append(f"  Alt: `{entry.config['alt']}`")
            if "random" in entry.config:
                lines.append(f"  Random: `{entry.config['random']}`")
            if "equivalents" in entry.config:
                lines.append(f"  Equivalents: `{entry.config['equivalents']}`")
            lines.append("")
    (output_root / MANUAL_DOC_PATH.relative_to(Path("output"))).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def run_conversion(repo_root: Path, output_root: Path) -> ConversionResult:
    copied_files = copy_repo_to_output(repo_root, output_root)
    entries = discover_myctm_entries(repo_root)

    manual_entries: list[tuple[MyCtmEntry, list[str]]] = []
    converted_entries = 0
    generated_files = 0

    for entry in entries:
        reasons = classify_entry(entry)
        if reasons:
            manual_entries.append((entry, reasons))
            continue
        generated_files += convert_entry(repo_root, output_root, entry)
        converted_entries += 1

    write_manual_doc(output_root, manual_entries)
    generated_files += 1

    return ConversionResult(
        total_entries=len(entries),
        converted_entries=converted_entries,
        manual_entries=len(manual_entries),
        copied_files=copied_files,
        generated_files=generated_files,
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    output_root = repo_root / DEFAULT_OUTPUT_DIR
    result = run_conversion(repo_root, output_root)
    print(f"Total MyCTMLib entries: {result.total_entries}")
    print(f"Converted to compact CTM: {result.converted_entries}")
    print(f"Manual follow-up entries: {result.manual_entries}")
    print(f"Copied files: {result.copied_files}")
    print(f"Generated files: {result.generated_files}")
    print(f"Output directory: {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
