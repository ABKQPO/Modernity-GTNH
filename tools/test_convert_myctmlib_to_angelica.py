from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from convert_myctmlib_to_angelica import (
    MyCtmEntry,
    build_compact_tiles,
    build_full_ctm_tiles,
    classify_entry,
    discover_myctm_entries,
    remove_generated_source_textures,
    strip_myctmlib_metadata,
    write_properties,
)


def solid(color: tuple[int, int, int, int], size: tuple[int, int]) -> Image.Image:
    return Image.new("RGBA", size, color)


class ConvertMyCtmLibToAngelicaTest(unittest.TestCase):
    def test_classify_alt_as_manual(self) -> None:
        entry = MyCtmEntry(
            png_path=Path("assets/example/textures/blocks/base.png"),
            mcmeta_path=Path("assets/example/textures/blocks/base.png.mcmeta"),
            texture_path="assets/example/textures/blocks/base.png",
            texture_name="example:base",
            texture_rel_name="base",
            mod_namespace="example",
            config={"connection": "example:base_ctm", "alt": "example:base_alt"},
        )
        self.assertEqual(classify_entry(entry), [])

    def test_build_compact_tiles_uses_expected_quadrants(self) -> None:
        base = Image.new("RGBA", (16, 16))
        base.paste(solid((255, 0, 0, 255), (8, 8)), (0, 0))
        base.paste(solid((0, 255, 0, 255), (8, 8)), (8, 0))
        base.paste(solid((0, 0, 255, 255), (8, 8)), (8, 8))
        base.paste(solid((255, 255, 0, 255), (8, 8)), (0, 8))

        ctm = Image.new("RGBA", (32, 32))
        colors = {
            1: (1, 0, 0, 255),
            2: (2, 0, 0, 255),
            5: (5, 0, 0, 255),
            6: (6, 0, 0, 255),
            9: (9, 0, 0, 255),
            10: (10, 0, 0, 255),
            11: (11, 0, 0, 255),
            12: (12, 0, 0, 255),
            13: (13, 0, 0, 255),
            14: (14, 0, 0, 255),
            15: (15, 0, 0, 255),
            16: (16, 0, 0, 255),
            3: (3, 0, 0, 255),
            4: (4, 0, 0, 255),
            7: (7, 0, 0, 255),
            8: (8, 0, 0, 255),
        }
        for index, color in colors.items():
            row = (index - 1) // 4
            col = (index - 1) % 4
            ctm.paste(solid(color, (8, 8)), (col * 8, row * 8))

        compact_tiles = build_compact_tiles(base, ctm)
        self.assertEqual(compact_tiles[0].getpixel((4, 4)), (255, 0, 0, 255))
        self.assertEqual(compact_tiles[0].getpixel((12, 4)), (0, 255, 0, 255))
        self.assertEqual(compact_tiles[0].getpixel((12, 12)), (0, 0, 255, 255))
        self.assertEqual(compact_tiles[0].getpixel((4, 12)), (255, 255, 0, 255))

        self.assertEqual(compact_tiles[1].getpixel((4, 4)), (1, 0, 0, 255))
        self.assertEqual(compact_tiles[1].getpixel((12, 4)), (2, 0, 0, 255))
        self.assertEqual(compact_tiles[1].getpixel((12, 12)), (6, 0, 0, 255))
        self.assertEqual(compact_tiles[1].getpixel((4, 12)), (5, 0, 0, 255))

        self.assertEqual(compact_tiles[2].getpixel((4, 4)), (9, 0, 0, 255))
        self.assertEqual(compact_tiles[2].getpixel((12, 4)), (10, 0, 0, 255))
        self.assertEqual(compact_tiles[2].getpixel((12, 12)), (14, 0, 0, 255))
        self.assertEqual(compact_tiles[2].getpixel((4, 12)), (13, 0, 0, 255))

        self.assertEqual(compact_tiles[3].getpixel((4, 4)), (3, 0, 0, 255))
        self.assertEqual(compact_tiles[3].getpixel((12, 4)), (4, 0, 0, 255))
        self.assertEqual(compact_tiles[3].getpixel((12, 12)), (8, 0, 0, 255))
        self.assertEqual(compact_tiles[3].getpixel((4, 12)), (7, 0, 0, 255))

        self.assertEqual(compact_tiles[4].getpixel((4, 4)), (11, 0, 0, 255))
        self.assertEqual(compact_tiles[4].getpixel((12, 4)), (12, 0, 0, 255))
        self.assertEqual(compact_tiles[4].getpixel((12, 12)), (16, 0, 0, 255))
        self.assertEqual(compact_tiles[4].getpixel((4, 12)), (15, 0, 0, 255))

    def test_build_full_ctm_tiles_uses_alt_quadrants_for_partial_connections(self) -> None:
        base = Image.new("RGBA", (16, 16))
        for pos, color in [((0, 0), (10, 0, 0, 255)), ((8, 0), (20, 0, 0, 255)), ((8, 8), (30, 0, 0, 255)), ((0, 8), (40, 0, 0, 255))]:
            base.paste(solid(color, (8, 8)), pos)

        alt = Image.new("RGBA", (16, 16))
        for pos, color in [((0, 0), (110, 0, 0, 255)), ((8, 0), (120, 0, 0, 255)), ((8, 8), (130, 0, 0, 255)), ((0, 8), (140, 0, 0, 255))]:
            alt.paste(solid(color, (8, 8)), pos)

        ctm = Image.new("RGBA", (32, 32))
        for index, color in {
            1: (1, 0, 0, 255), 2: (2, 0, 0, 255), 3: (3, 0, 0, 255), 4: (4, 0, 0, 255),
            5: (5, 0, 0, 255), 6: (6, 0, 0, 255), 7: (7, 0, 0, 255), 8: (8, 0, 0, 255),
            9: (9, 0, 0, 255), 10: (10, 0, 0, 255), 11: (11, 0, 0, 255), 12: (12, 0, 0, 255),
            13: (13, 0, 0, 255), 14: (14, 0, 0, 255), 15: (15, 0, 0, 255), 16: (16, 0, 0, 255),
        }.items():
            row = (index - 1) // 4
            col = (index - 1) % 4
            ctm.paste(solid(color, (8, 8)), (col * 8, row * 8))

        full_tiles = build_full_ctm_tiles(base, ctm, alt)
        tile3 = full_tiles[3]
        self.assertEqual(tile3.getpixel((4, 4)), (3, 0, 0, 255))
        self.assertEqual(tile3.getpixel((12, 4)), (4, 0, 0, 255))
        self.assertEqual(tile3.getpixel((12, 12)), (130, 0, 0, 255))
        self.assertEqual(tile3.getpixel((4, 12)), (140, 0, 0, 255))

    def test_write_properties_includes_equivalents_in_match_tiles(self) -> None:
        entry = MyCtmEntry(
            png_path=Path("assets/example/textures/blocks/base.png"),
            mcmeta_path=Path("assets/example/textures/blocks/base.png.mcmeta"),
            texture_path="assets/example/textures/blocks/base.png",
            texture_name="example:base",
            texture_rel_name="base",
            mod_namespace="example",
            config={"connection": "example:base_ctm", "equivalents": ["example:peer", "minecraft:textures/blocks/foo.png"]},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "base.properties"
            write_properties(out, entry, entry.config["equivalents"], method="compact", tile_range="0-4")
            content = out.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("matchTiles=example:base example:peer foo\nmethod=compact\n"))
        self.assertNotIn("# Auto-generated", content)
        self.assertNotIn("ctm.0=", content)

    def test_strip_myctmlib_metadata_preserves_other_sections(self) -> None:
        entry = MyCtmEntry(
            png_path=Path("assets/example/textures/blocks/base.png"),
            mcmeta_path=Path("assets/example/textures/blocks/base.png.mcmeta"),
            texture_path="assets/example/textures/blocks/base.png",
            texture_name="example:base",
            texture_rel_name="base",
            mod_namespace="example",
            config={"connection": "example:base_ctm"},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "output"
            mcmeta = output / entry.mcmeta_path
            mcmeta.parent.mkdir(parents=True, exist_ok=True)
            mcmeta.write_text(
                json.dumps({"animation": {"interpolate": True}, "myctmlib": {"connection": "example:base_ctm"}}, indent=2),
                encoding="utf-8",
            )
            strip_myctmlib_metadata(root, output, entry)
            data = json.loads(mcmeta.read_text(encoding="utf-8"))
        self.assertEqual(data, {"animation": {"interpolate": True}})

    def test_remove_generated_source_textures_deletes_ctm_and_alt_outputs(self) -> None:
        entry = MyCtmEntry(
            png_path=Path("assets/example/textures/blocks/base.png"),
            mcmeta_path=Path("assets/example/textures/blocks/base.png.mcmeta"),
            texture_path="assets/example/textures/blocks/base.png",
            texture_name="example:base",
            texture_rel_name="base",
            mod_namespace="example",
            config={"connection": "example:base_ctm", "alt": "example:base_alt"},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo = root / "repo"
            out = root / "out"
            ctm = repo / "assets/example/textures/blocks/base_ctm.png"
            alt = repo / "assets/example/textures/blocks/base_alt.png"
            for path in [ctm, alt]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"x")
                out_path = out / path.relative_to(repo)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(b"x")
                (out_path.with_suffix(out_path.suffix + ".mcmeta")).write_text("{}", encoding="utf-8")
            remove_generated_source_textures(out, repo, entry)
            self.assertFalse((out / ctm.relative_to(repo)).exists())
            self.assertFalse((out / alt.relative_to(repo)).exists())
            self.assertFalse((out / ctm.relative_to(repo)).with_suffix(".png.mcmeta").exists())
            self.assertFalse((out / alt.relative_to(repo)).with_suffix(".png.mcmeta").exists())

    def test_discover_myctm_entries_resolves_block_alias_mcmeta(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            png = root / "assets/example/textures/blocks/fancy/base.png"
            png.parent.mkdir(parents=True, exist_ok=True)
            png.write_bytes(b"x")
            mcmeta = root / "assets/example/blocks/fancy/base.png.mcmeta"
            mcmeta.parent.mkdir(parents=True, exist_ok=True)
            mcmeta.write_text(
                json.dumps({"myctmlib": {"connection": "example:fancy/base_ctm"}}, indent=2),
                encoding="utf-8",
            )

            entries = discover_myctm_entries(root)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].png_path, png)
        self.assertEqual(entries[0].mcmeta_path, mcmeta)
        self.assertEqual(entries[0].texture_name, "example:fancy/base")

    def test_discover_myctm_entries_resolves_block_alias_non_png_mcmeta(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            png = root / "assets/example/textures/blocks/fancy/base_side.png"
            png.parent.mkdir(parents=True, exist_ok=True)
            png.write_bytes(b"x")
            mcmeta = root / "assets/example/blocks/fancy/base_side.mcmeta"
            mcmeta.parent.mkdir(parents=True, exist_ok=True)
            mcmeta.write_text(
                json.dumps({"myctmlib": {"connection": "example:fancy/base_side_ctm"}}, indent=2),
                encoding="utf-8",
            )

            entries = discover_myctm_entries(root)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].png_path, png)
        self.assertEqual(entries[0].mcmeta_path, mcmeta)
        self.assertEqual(entries[0].texture_name, "example:fancy/base_side")

    def test_discover_myctm_entries_accepts_non_strict_mcmeta_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            png = root / "assets/example/textures/blocks/base.png"
            png.parent.mkdir(parents=True, exist_ok=True)
            png.write_bytes(b"x")
            mcmeta = root / "assets/example/textures/blocks/base.png.mcmeta"
            mcmeta.write_text(
                '{ "animation": { "frames": [ { index: 0, time: 5 } ] }, "myctmlib": { "connection": "example:base_ctm" } }',
                encoding="utf-8",
            )

            entries = discover_myctm_entries(root)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].png_path, png)
        self.assertEqual(entries[0].config["connection"], "example:base_ctm")

    def test_discover_myctm_entries_accepts_non_png_mcmeta_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            png = root / "assets/example/textures/blocks/floor_side.png"
            png.parent.mkdir(parents=True, exist_ok=True)
            png.write_bytes(b"x")
            mcmeta = root / "assets/example/textures/blocks/floor_side.mcmeta"
            mcmeta.write_text(
                json.dumps({"myctmlib": {"connection": "example:floor_side_ctm"}}, indent=2),
                encoding="utf-8",
            )

            entries = discover_myctm_entries(root)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].png_path, png)
        self.assertEqual(entries[0].mcmeta_path, mcmeta)

    def test_discover_myctm_entries_resolves_light_blue_name_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            png = root / "assets/minecraft/textures/blocks/glass_light_blue.png"
            png.parent.mkdir(parents=True, exist_ok=True)
            png.write_bytes(b"x")
            mcmeta = root / "assets/minecraft/textures/blocks/glass_lightblue.png.mcmeta"
            mcmeta.write_text(
                json.dumps({"myctmlib": {"connection": "glass_lightblue_ctm"}}, indent=2),
                encoding="utf-8",
            )

            entries = discover_myctm_entries(root)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].png_path, png)
        self.assertEqual(entries[0].texture_name, "glass_light_blue")


if __name__ == "__main__":
    unittest.main()
