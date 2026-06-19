from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ASSETS_PREFIX = "assets/"
DEFAULT_OUTPUT_DIR = Path("output")


@dataclass(frozen=True)
class AssetCandidate:
    jar_path: Path
    zip_name: str


def normalize_zip_name(zip_name: str) -> str:
    return zip_name.replace("\\", "/")


def is_asset_file(zip_name: str) -> bool:
    normalized = normalize_zip_name(zip_name)
    return normalized.startswith(ASSETS_PREFIX) and not normalized.endswith("/")


def is_gui_asset(zip_name: str) -> bool:
    normalized = normalize_zip_name(zip_name).lower()
    return "/textures/gui/" in normalized


def base_asset_name(zip_name: str) -> str:
    name = Path(normalize_zip_name(zip_name)).name
    if name.lower().endswith(".png.mcmeta"):
        return name[:-7]
    return name


def is_sidecar_mcmeta(zip_name: str) -> bool:
    return normalize_zip_name(zip_name).lower().endswith(".png.mcmeta")


def sidecar_owner_zip_name(zip_name: str) -> str:
    return normalize_zip_name(zip_name)[:-7]


def collect_modernity_file_names(assets_dir: Path) -> set[str]:
    if not assets_dir.is_dir():
        raise FileNotFoundError(f"Modernity assets directory not found: {assets_dir}")

    names: set[str] = set()
    for path in assets_dir.rglob("*"):
        if path.is_file():
            names.add(base_asset_name(path.name).lower())
    return names


def find_jars(mods_dir: Path) -> list[Path]:
    if not mods_dir.is_dir():
        raise FileNotFoundError(f"Mods directory not found: {mods_dir}")
    return sorted(path for path in mods_dir.rglob("*.jar") if path.is_file())


def collect_export_candidates(
    jar_paths: Iterable[Path],
    modernity_names: set[str],
    *,
    gui_only: bool,
) -> list[AssetCandidate]:
    exported_names: set[str] = set()
    candidates: list[AssetCandidate] = []

    for jar_path in jar_paths:
        with zipfile.ZipFile(jar_path) as jar:
            names = {normalize_zip_name(name) for name in jar.namelist()}
            pending_mcmeta: dict[str, str] = {}
            for info in jar.infolist():
                zip_name = normalize_zip_name(info.filename)
                if not is_asset_file(zip_name):
                    continue
                if gui_only and not is_gui_asset(zip_name):
                    continue

                file_name = base_asset_name(zip_name).lower()

                if is_sidecar_mcmeta(zip_name):
                    owner_name = sidecar_owner_zip_name(zip_name)
                    if owner_name in names and file_name not in modernity_names:
                        if file_name in exported_names:
                            candidates.append(AssetCandidate(jar_path=jar_path, zip_name=zip_name))
                        else:
                            pending_mcmeta[owner_name] = zip_name
                    continue

                if file_name in modernity_names or file_name in exported_names:
                    continue

                candidates.append(AssetCandidate(jar_path=jar_path, zip_name=zip_name))
                exported_names.add(file_name)

                mcmeta_name = pending_mcmeta.pop(zip_name, None)
                if mcmeta_name is not None:
                    candidates.append(AssetCandidate(jar_path=jar_path, zip_name=mcmeta_name))

            for owner_name, mcmeta_name in list(pending_mcmeta.items()):
                file_name = base_asset_name(owner_name).lower()
                if file_name not in exported_names:
                    continue
                candidates.append(AssetCandidate(jar_path=jar_path, zip_name=mcmeta_name))
                del pending_mcmeta[owner_name]

    return candidates


def export_candidates(candidates: Iterable[AssetCandidate], output_dir: Path) -> int:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    count = 0
    for candidate in candidates:
        destination = output_dir / Path(normalize_zip_name(candidate.zip_name))
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(candidate.jar_path) as jar:
            with jar.open(candidate.zip_name) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
        count += 1
    return count


def parse_yes_no(value: str) -> bool:
    return value.strip().lower() in {"y", "yes", "是", "true", "1"}


def main() -> int:
    mods_input = input("请输入 mods 文件夹路径: ").strip().strip('"')
    gui_input = input("是否只导出 GUI 资源？默认否，输入 是/y/yes 表示是: ")

    mods_dir = Path(mods_input).expanduser()
    repo_root = Path(__file__).resolve().parents[1]
    assets_dir = repo_root / "assets"
    output_dir = repo_root / DEFAULT_OUTPUT_DIR
    gui_only = parse_yes_no(gui_input)

    modernity_names = collect_modernity_file_names(assets_dir)
    jars = find_jars(mods_dir)
    candidates = collect_export_candidates(jars, modernity_names, gui_only=gui_only)
    exported_count = export_candidates(candidates, output_dir)

    print(f"扫描 jar 数量: {len(jars)}")
    print(f"Modernity 已有文件名数量: {len(modernity_names)}")
    print(f"导出文件数量: {exported_count}")
    print(f"输出目录: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
