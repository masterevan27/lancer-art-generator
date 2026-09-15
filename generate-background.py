#!/usr/bin/env python3
"""Preview reproducible backgrounds and render scenes or reference battlemaps."""
import argparse
import art_styles
import contextlib
import json
from pathlib import Path
import sys
import urllib.parse
import uuid

import background_scene as scene


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--catalogue", action="store_true")
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--render", action="store_true")
    mode.add_argument("--battlemap", type=Path, metavar="IMAGE")
    parser.add_argument("--request-stdin", action="store_true")
    parser.add_argument("--tables", type=Path, default=scene.DEFAULT_TABLES)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--server", help="ComfyUI address; otherwise probe localhost ports 8000-8015")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--notes", default="")
    parser.add_argument("--timeout", type=int, default=1800)
    art_styles.add_arguments(parser)
    args = parser.parse_args(argv)
    try:
        art_styles.configure(args, "backgrounds", "output_dir")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    if (args.preview or args.render) and not args.request_stdin:
        parser.error("--preview and --render require --request-stdin")
    if args.render and not args.output_dir:
        parser.error("--render requires --output-dir")
    scene.integer(args.timeout, "timeout", 1, 86400)
    return args


def _request():
    content = sys.stdin.read(2_000_001)
    if len(content) > 2_000_000:
        raise ValueError("JSON request is too large")
    return json.loads(content)


def _render_graph(comfy, graph, timeout):
    record = comfy.wait(comfy.queue(graph), timeout=timeout)
    save_nodes = [key for key, node in graph.items() if node["class_type"] == "SaveImage"]
    images = [image for key in save_nodes for image in record.get("outputs", {}).get(key, {}).get("images", [])
              if image.get("filename", "").lower().endswith(".png")]
    if not images:
        raise RuntimeError("ComfyUI completed without a PNG at the requested SaveImage node")
    image = images[0]
    query = urllib.parse.urlencode({"filename": image["filename"], "subfolder": image.get("subfolder", ""), "type": image.get("type", "output")})
    data = comfy._get_bytes("/view?" + query)
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("ComfyUI returned invalid PNG image data")
    return data


def _event(path):
    print("BACKGROUND_RESULT " + json.dumps({"path": str(path.resolve())}), flush=True)


def main(argv=None):
    try:
        args = parse_args(argv)
        if args.catalogue:
            print(json.dumps(scene.load_catalogue(args.tables), ensure_ascii=False))
            return 0
        if args.preview:
            result = scene.preview(_request(), scene.load_catalogue(args.tables))
            for plan in result["plans"]:
                plan["prompt"] = art_styles.apply_style(plan["prompt"], args.selected_style)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        if args.render:
            plans = scene.validate_plans(_request(), scene.load_catalogue(args.tables))
        else:
            art_styles.check_source(args, args.battlemap)
            metadata = scene.battlemap_metadata(args.battlemap, args.width, args.height, args.seed, args.notes)
            metadata["prompt"] = art_styles.apply_style(metadata["prompt"], args.selected_style)
            metadata.update(art_styles.metadata(args))
        # Existing ComfyUI utilities sometimes log to stdout; reserve it for events.
        with contextlib.redirect_stdout(sys.stderr):
            comfy = scene.art_module().find_server(args.server)
        if args.render:
            for plan in plans:
                plan["prompt"] = art_styles.apply_style(plan["prompt"], args.selected_style)
                with contextlib.redirect_stdout(sys.stderr):
                    graph = scene.build_scene_graph(plan, art_styles.private_prefix(args, "LancerBackgrounds/" + uuid.uuid4().hex))
                    data = _render_graph(comfy, art_styles.protect_graph(graph, args), args.timeout)
                    path = scene.save_result(args.output_dir, f"Background-{plan['environment']}-{plan['seed']}", data, dict(plan, kind="background", **art_styles.metadata(args)))
                _event(path)
        else:
            source = args.battlemap.resolve()
            with contextlib.redirect_stdout(sys.stderr):
                expressions = scene._load_module("generate-expressions.py", "lancer_background_expressions")
                image_ref = expressions.upload_image(comfy, source, art_styles.private_prefix(args, "lancer-backgrounds/" + uuid.uuid4().hex))
                graph = scene.build_battlemap_graph(image_ref, metadata["prompt"], args.seed, args.width, args.height, art_styles.private_prefix(args, "LancerBattlemaps/" + uuid.uuid4().hex))
                data = _render_graph(comfy, art_styles.protect_graph(graph, args), args.timeout)
                path = scene.save_result(args.output_dir or source.parent, source.stem + " Battlemap", data, metadata)
            _event(path)
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        print(f"Background generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8-sig")
    raise SystemExit(main())
