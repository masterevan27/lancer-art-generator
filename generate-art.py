#!/usr/bin/env python3
"""Batch-generate art-prompt images through the ComfyUI HTTP API.

Reads an art-prompts markdown file (default: the mech catalogue), pulls every
prompt block out of it - fenced or blockquoted, whichever that file uses - and
queues one ComfyUI job per prompt using an API-format workflow as the template.
Images land in ComfyUI's own output folder under a subfolder path mirroring the
markdown headings, e.g.

    <comfy>/output/LancerMechs/Player-Frames/IPS-Northstar/Blackbeard_00001_.png

Stdlib only - no pip installs needed. Run with --list or --dry-run first.

Each result can then be chained through image -> image passes with --post, so a
mech can go text -> image -> transparent PNG in one run. Post-pass results land
under their own root (--post-prefix, default LancerFoundryTokens) rather than
beside the raw generations, so the finished transparent PNGs can be handed to
Foundry without dragging the source images along:

    <comfy>/output/LancerFoundryTokens/Player-Frames/IPS-Northstar/Blackbeard_rmbg_00001_.png

Examples:
  python generate-art.py --list
  python generate-art.py --dry-run
  python generate-art.py --filter blackbeard --variants 3
  python generate-art.py --steps 8 --post rmbg --resume
  python generate-art.py --post rmbg --post-only        # existing images only
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
COMFY_DIR = SCRIPT_DIR.parent

WORKFLOW_DIR = COMFY_DIR / "Workflows" / "ComfyUI API runnable"

DEFAULT_PROMPTS = COMFY_DIR / "Art Prompts" / "mech-catalogue-art-prompts.md"
DEFAULT_WORKFLOW = WORKFLOW_DIR / "Lancer_Scene_Workflow_v1.json"
DEFAULT_MANIFEST = SCRIPT_DIR / ".generated-manifest.json"

# Shorthands accepted by --post so the common chains stay typeable.
POST_ALIASES = {
    "rmbg": WORKFLOW_DIR / "Util_RemoveBackground_makeTransparent.json",
}

# Mirrors StackLauncher.ps1: Comfy Desktop defaults to 8000 and walks upward
# when that port is busy, so probe the same range when no --server is given.
DEFAULT_PORTS = range(8000, 8016)

# Headings that introduce settings/notes rather than an actual art prompt.
SKIP_HEADINGS = re.compile(
    r"^(shared\s+settings|settings|foundry\s+note|note\b|pipeline|workflow)", re.I
)

MIN_PROMPT_CHARS = 200  # settings blocks are short; real prompts are paragraphs


# --------------------------------------------------------------------------
# Markdown parsing
# --------------------------------------------------------------------------


@dataclass
class Entry:
    name: str            # "Blackbeard"
    label: str           # "Blackbeard", or "Blackbeard_Alternate-look-heavy-cavalry"
    path: list            # ["Player-Frames", "IPS-Northstar"]
    prompt: str
    line: int
    role: str = ""
    variant: str = ""    # "" for the primary block, else an alternate slug

    @property
    def key(self):
        return "/".join(self.path + [self.label])

    @property
    def prefix(self):
        """SaveImage filename_prefix - ComfyUI treats '/' as subfolders."""
        return "/".join(self.path + [self.label])


def _slug(text):
    text = re.sub(r"\(.*?\)", " ", text)              # drop parentheticals
    text = text.replace("&", " and ")
    text = re.sub(r"['’]", "", text)             # Death's Head -> Deaths-Head
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")


def _split_heading(text):
    """'Blackbeard - _Striker_' -> ('Blackbeard', 'Striker')."""
    parts = re.split(r"\s+[—–-]\s+", text, maxsplit=1)
    name = parts[0].strip()
    role = parts[1].strip().strip("_*") if len(parts) > 1 else ""
    return name, role


def parse_prompts(md_path):
    lines = md_path.read_text(encoding="utf-8").splitlines()

    entries = []
    headings = {}          # level -> raw heading text
    pending_variant = ""   # slug from an "**Alternate look ...:**" lead-in
    seen_at_heading = {}

    i = 0
    while i < len(lines):
        line = lines[i]

        h = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
        if h:
            level = len(h.group(1))
            headings[level] = h.group(2)
            for deeper in [lv for lv in list(headings) if lv > level]:
                del headings[deeper]
            pending_variant = ""
            i += 1
            continue

        alt = re.match(r"^\*\*(Alternate[^*]*?)\s*:?\*\*", line)
        if alt:
            pending_variant = _slug(alt.group(1))
            i += 1
            continue

        # The mech/equipment files fence their prompts; the battlemap and
        # scene-background files quote them with '>'. Accept either.
        block = None
        if line.startswith("```"):
            j = i + 1
            body = []
            while j < len(lines) and not lines[j].startswith("```"):
                body.append(lines[j])
                j += 1
            block = ("\n".join(body).strip(), i + 2, j + 1)
        elif line.startswith(">"):
            j = i
            body = []
            while j < len(lines) and lines[j].startswith(">"):
                body.append(re.sub(r"^>\s?", "", lines[j]))
                j += 1
            block = ("\n".join(body).strip(), i + 1, j)

        if block:
            content, start_line, i_next = block

            if not headings:
                i = i_next
                continue

            deepest = max(headings)
            raw_name = headings[deepest]
            name, role = _split_heading(raw_name)

            if SKIP_HEADINGS.match(name) or len(content) < MIN_PROMPT_CHARS:
                i = i_next
                pending_variant = ""
                continue

            # Ancestor headings, minus the document title (level 1).
            path = [
                _slug(re.sub(r"^Part\s*\d+\s*:\s*", "", headings[lv]))
                for lv in sorted(headings)
                if lv != deepest and lv != 1
            ]
            path = [p for p in path if p]

            count = seen_at_heading.get(raw_name, 0)
            seen_at_heading[raw_name] = count + 1
            variant = pending_variant if count else ""
            if count and not variant:
                variant = "Alt%d" % (count + 1)

            label = _slug(name) + ("_" + variant if variant else "")

            entries.append(
                Entry(
                    name=name,
                    label=label,
                    path=path,
                    prompt=content,
                    line=start_line,
                    role=role,
                    variant=variant,
                )
            )
            pending_variant = ""
            i = i_next
            continue

        i += 1

    return entries


# --------------------------------------------------------------------------
# Workflow patching
# --------------------------------------------------------------------------


class WorkflowError(RuntimeError):
    pass


def parse_set(spec):
    """'54.denoise=0.8' -> ('54', 'denoise', 0.8).

    The value goes through json.loads so numbers, booleans and null arrive as
    themselves; anything that isn't valid JSON is kept as plain text, which is
    what a checkpoint or LoRA filename needs.
    """
    target, sep, raw = spec.partition("=")
    node_id, _, key = target.rpartition(".")
    node_id, key = node_id.strip(), key.strip()
    if not sep or not node_id or not key:
        raise ValueError("expected NODE.input=value, got %r" % spec)
    try:
        return node_id, key, json.loads(raw)
    except json.JSONDecodeError:
        return node_id, key, raw


def describe(graph, tags):
    """One line per node, marking the inputs this script writes."""
    out = []
    for nid in sorted(graph, key=lambda n: (len(n), n)):
        node = graph[nid]
        title = node.get("_meta", {}).get("title", "")
        out.append(("  %4s  %-30s %-26s %s" % (
            nid,
            node.get("class_type", "?"),
            ("[%s]" % title[:24]) if title else "",
            ("<- " + ", ".join(tags[nid])) if nid in tags else "",
        )).rstrip())
    return "\n".join(out)


def _link(node, socket):
    """Return the upstream node id wired into `socket`, if any."""
    value = node.get("inputs", {}).get(socket)
    if isinstance(value, list) and value and isinstance(value[0], str):
        return value[0]
    return None


def _walk_back(graph, start, want):
    """Breadth-first walk upstream from `start` looking for a class_type."""
    seen, queue = set(), [start]
    while queue:
        nid = queue.pop(0)
        if nid in seen or nid not in graph:
            continue
        seen.add(nid)
        if graph[nid].get("class_type") == want:
            return nid
        for value in graph[nid].get("inputs", {}).values():
            if isinstance(value, list) and value and isinstance(value[0], str):
                queue.append(value[0])
    return None


@dataclass
class WorkflowSlots:
    """The node ids this script actually writes to."""

    save: str
    sampler: str
    positive: str
    latent: str = None


def locate_slots(graph):
    saves = [
        n for n, d in graph.items()
        if d.get("class_type") in ("SaveImage", "SaveImageWebsocket")
    ]
    if not saves:
        raise WorkflowError("no SaveImage node - nothing would be written to disk")
    save = saves[0]

    sampler = _walk_back(graph, save, "KSampler") or _walk_back(graph, save, "KSamplerAdvanced")
    if not sampler:
        raise WorkflowError("could not find a KSampler upstream of SaveImage")

    pos_id = _link(graph[sampler], "positive")
    positive = _walk_back(graph, pos_id, "CLIPTextEncode") if pos_id else None
    if not positive:
        raise WorkflowError("could not find a CLIPTextEncode on the sampler's positive input")

    lat_id = _link(graph[sampler], "latent_image")
    latent = None
    if lat_id and graph.get(lat_id, {}).get("class_type", "").startswith("EmptyLatent"):
        latent = lat_id

    return WorkflowSlots(save=save, sampler=sampler, positive=positive, latent=latent)


@dataclass
class PostSlots:
    """Node ids for an image -> image pass (background removal, refine, ...)."""

    load: str            # LoadImage node fed the previous stage's output
    output: str          # node whose images get written to disk
    promoted: bool       # True if `output` was a PreviewImage we turned into a SaveImage
    sampler: str = None  # KSampler node, if the pass has one
    drop: tuple = ()     # spare PreviewImage nodes stripped from the job


def _depth(graph, start, _seen=None):
    """How many nodes deep the upstream chain behind `start` runs."""
    _seen = _seen or set()
    if start in _seen or start not in graph:
        return 0
    _seen = _seen | {start}
    best = 0
    for value in graph[start].get("inputs", {}).values():
        if isinstance(value, list) and value and isinstance(value[0], str):
            best = max(best, 1 + _depth(graph, value[0], _seen))
    return best


def locate_post_slots(graph, forced_output=None):
    loads = [n for n, d in graph.items() if d.get("class_type") == "LoadImage"]
    if not loads:
        raise WorkflowError("no LoadImage node - a post pass needs one to receive the image")
    if len(loads) > 1:
        raise WorkflowError("expected one LoadImage node, found %s" % ", ".join(sorted(loads)))
    load = loads[0]

    saves = [n for n, d in graph.items() if d.get("class_type") == "SaveImage"]
    previews = [n for n, d in graph.items() if d.get("class_type") == "PreviewImage"]

    if forced_output:
        if forced_output not in graph:
            raise WorkflowError("--post-output node %s is not in this workflow" % forced_output)
        output, promoted = forced_output, forced_output not in saves
    elif saves:
        output, promoted = saves[0], False
    elif previews:
        # No SaveImage at all, only debug previews. The pass that ran through
        # the most nodes is the finished one; the rest are taps on intermediate
        # stages.
        output = max(previews, key=lambda n: (_depth(graph, n), int(n)))
        promoted = True
    else:
        raise WorkflowError("no SaveImage or PreviewImage node - nothing to capture")

    sampler = _walk_back(graph, output, "KSampler") or _walk_back(graph, output, "KSamplerAdvanced")
    drop = tuple(n for n in previews if n != output)
    return PostSlots(load=load, output=output, promoted=promoted,
                     sampler=sampler, drop=drop)


def image_ref(image):
    """ComfyUI's annotated-filepath form: 'subfolder/name.png [output]'."""
    subfolder = image.get("subfolder", "")
    name = "%s/%s" % (subfolder, image["filename"]) if subfolder else image["filename"]
    return "%s [%s]" % (name.replace("\\", "/"), image.get("type", "output"))


def build_post_job(template, slots, ref, prefix, seed, args):
    graph = json.loads(json.dumps(template))

    graph[slots.load]["inputs"]["image"] = ref

    for nid in slots.drop:  # spare debug previews would each write a temp file
        graph.pop(nid, None)

    if slots.promoted:
        graph[slots.output]["class_type"] = "SaveImage"
        graph[slots.output].setdefault("_meta", {})["title"] = "Save Image"
    graph[slots.output]["inputs"]["filename_prefix"] = prefix

    if slots.sampler:
        graph[slots.sampler]["inputs"]["seed"] = seed

    prune_orphans(graph)
    return graph


def prune_orphans(graph):
    """Drop nodes nothing consumes and that produce no output.

    Exported workflows often carry spare, disconnected nodes (the scene
    workflow keeps three unused EmptyLatentImage nodes holding %width%/%height%
    placeholders). ComfyUI would ignore them, but stripping them keeps the
    submitted job honest and avoids any chance of a validation error.
    """
    removed = []
    while True:
        consumed = set()
        for node in graph.values():
            for value in node.get("inputs", {}).values():
                if isinstance(value, list) and value and isinstance(value[0], str):
                    consumed.add(value[0])
        dangling = [
            nid for nid, node in graph.items()
            if nid not in consumed
            and not re.search(r"Save|Preview|Output", node.get("class_type", ""))
        ]
        if not dangling:
            return removed
        for nid in dangling:
            removed.append(nid)
            del graph[nid]


def build_job(template, slots, entry, seed, args):
    graph = json.loads(json.dumps(template))  # deep copy per job

    graph[slots.positive]["inputs"]["text"] = entry.prompt
    prefix = (args.output_prefix + "/" + entry.prefix).strip("/")
    graph[slots.save]["inputs"]["filename_prefix"] = prefix

    sampler_inputs = graph[slots.sampler]["inputs"]
    sampler_inputs["seed"] = seed
    if args.steps is not None:
        sampler_inputs["steps"] = args.steps
    if args.cfg is not None:
        sampler_inputs["cfg"] = args.cfg
    if args.sampler is not None:
        sampler_inputs["sampler_name"] = args.sampler
    if args.scheduler is not None:
        sampler_inputs["scheduler"] = args.scheduler

    if slots.latent and (args.width or args.height):
        latent_inputs = graph[slots.latent]["inputs"]
        if args.width:
            latent_inputs["width"] = args.width
        if args.height:
            latent_inputs["height"] = args.height

    # Last, so an explicit --set beats anything modelled above.
    for node_id, key, value in args.set:
        if node_id not in graph:
            raise WorkflowError(
                "--set: node %s is not in this workflow (run --inspect to list nodes)" % node_id
            )
        graph[node_id].setdefault("inputs", {})[key] = value

    prune_orphans(graph)

    leftover = [
        "node %s.%s = %s" % (nid, socket, value)
        for nid, node in graph.items()
        for socket, value in node.get("inputs", {}).items()
        if isinstance(value, str) and re.fullmatch(r"%[a-z_]+%", value)
    ]
    if leftover:
        raise WorkflowError(
            "template still has unfilled placeholders this script does not "
            "know how to set: " + ", ".join(leftover)
        )

    return graph


# --------------------------------------------------------------------------
# ComfyUI client
# --------------------------------------------------------------------------


class Comfy:
    def __init__(self, base, timeout=10.0):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())

    def _get(self, path, timeout=None):
        with urllib.request.urlopen(self.base + path, timeout=timeout or self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _get_bytes(self, path):
        with urllib.request.urlopen(self.base + path, timeout=120) as resp:
            return resp.read()

    def alive(self):
        try:
            self._get("/system_stats", timeout=2.0)
            return True
        except Exception:
            return False

    def _post(self, path, payload, timeout=30):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base + path, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}

    def queue(self, graph):
        try:
            reply = self._post("/prompt", {"prompt": graph, "client_id": self.client_id}, timeout=60)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError("ComfyUI rejected the job (%s): %s" % (exc.code, detail[:800]))
        # A job can be accepted and still carry per-node complaints; without
        # this they only ever show up as a bad image.
        if reply.get("node_errors"):
            print("    ! node_errors: %s" % json.dumps(reply["node_errors"])[:500],
                  file=sys.stderr)
        return reply["prompt_id"]

    def queued(self, prompt_id):
        """Is this job still running or waiting on the server?"""
        try:
            queue = self._get("/queue", timeout=5.0)
        except Exception:
            return True  # can't tell - assume it's alive rather than kill a live job
        for bucket in ("queue_running", "queue_pending"):
            for item in queue.get(bucket, []):
                if len(item) > 1 and item[1] == prompt_id:
                    return True
        return False

    def cancel_all(self):
        """Stop the running job and drop anything still queued."""
        for path, payload in (("/interrupt", {}), ("/queue", {"clear": True})):
            try:
                self._post(path, payload, timeout=10)
            except Exception:
                pass

    def wait(self, prompt_id, poll=1.5, timeout=1800):
        deadline = time.time() + timeout
        misses = 0
        while time.time() < deadline:
            try:
                history = self._get("/history/" + prompt_id)
            except Exception:
                time.sleep(poll)
                continue
            record = history.get(prompt_id)
            if record:
                status = record.get("status", {})
                if status.get("status_str") == "error":
                    messages = status.get("messages", [])
                    raise RuntimeError("job failed: " + json.dumps(messages)[:800])
                if status.get("completed", True):
                    return record
                misses = 0
            elif self.queued(prompt_id):
                misses = 0
            else:
                # In neither history nor the queue: the server restarted, or the
                # job was cancelled from the web UI. Waiting out the full
                # --timeout for a job that will never report back is 30 minutes
                # of nothing, so give up after a few polls - a couple of misses
                # can just be /history lagging the queue.
                misses += 1
                if misses >= 5:
                    raise RuntimeError(
                        "job %s left the queue without finishing (server restarted, "
                        "or it was cancelled)" % prompt_id
                    )
            time.sleep(poll)
        raise TimeoutError("job %s did not finish within %.0fs" % (prompt_id, timeout))

    @staticmethod
    def images(record):
        out = []
        for node_output in record.get("outputs", {}).values():
            out.extend(node_output.get("images", []))
        return out

    def download(self, image, dest_dir):
        query = urllib.parse.urlencode(
            {
                "filename": image["filename"],
                "subfolder": image.get("subfolder", ""),
                "type": image.get("type", "output"),
            }
        )
        data = self._get_bytes("/view?" + query)
        target = dest_dir / image.get("subfolder", "") / image["filename"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target


def find_server(explicit):
    if explicit:
        base = explicit if "://" in explicit else "http://" + explicit
        client = Comfy(base)
        if not client.alive():
            raise SystemExit("No ComfyUI answering at %s - is the server running?" % base)
        return client

    for port in DEFAULT_PORTS:
        client = Comfy("http://127.0.0.1:%d" % port)
        if client.alive():
            return client
    raise SystemExit(
        "No ComfyUI found on 127.0.0.1:%d-%d. Start it (Start Stack.cmd) "
        "or pass --server host:port." % (DEFAULT_PORTS.start, DEFAULT_PORTS.stop - 1)
    )


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------


def load_api_workflow(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "nodes" in data and "links" in data:
        raise SystemExit(
            "%s looks like a UI-format workflow. Re-export it with "
            "Workflow > Export (API) and point at that file instead." % Path(path).name
        )
    return data


def load_manifest(path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def save_manifest(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def manifest_images(manifest, entry):
    """Images from this entry's most recent run, for --post-only."""
    runs = manifest.get(entry.key, {}).get("runs") or []
    if not runs:
        return []
    # "source" is the stage-0 image; "images" also holds post-pass outputs, and
    # re-running a chain over its own output is never what you want.
    last = runs[-1]
    out = []
    for image in last.get("source") or last.get("images", []):
        if isinstance(image, dict):
            out.append(image)
        else:  # manifests written before the structured format
            subfolder, _, filename = str(image).replace("\\", "/").rpartition("/")
            out.append({"filename": filename, "subfolder": subfolder, "type": "output"})
    return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Generate images for every prompt in an art-prompts markdown file via the ComfyUI API.",
    )
    src = p.add_argument_group("sources")
    src.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS,
                     help="art-prompts markdown file (default: the mech catalogue)")
    src.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW,
                     help="API-format workflow JSON used as the template")

    sel = p.add_argument_group("selection")
    sel.add_argument("--filter", metavar="REGEX",
                     help="only entries whose name/section matches this (case-insensitive)")
    sel.add_argument("--exclude", metavar="REGEX", help="skip entries matching this")
    sel.add_argument("--skip-alternates", action="store_true", help="only the primary prompt per mech")
    sel.add_argument("--only-alternates", action="store_true", help="only the 'Alternate look' prompts")
    sel.add_argument("--limit", type=int, help="stop after N entries")
    sel.add_argument("--start-at", metavar="NAME", help="skip entries until one matches this")

    gen = p.add_argument_group("generation")
    gen.add_argument("--variants", type=int, default=1,
                     help="images per prompt, each with its own seed (default 1)")
    gen.add_argument("--seed", type=int, help="base seed; variants use seed, seed+1, ... (default: random)")
    gen.add_argument("--steps", type=int, help="override sampler steps (workflow default otherwise)")
    gen.add_argument("--cfg", type=float, help="override CFG")
    gen.add_argument("--sampler", help="override sampler_name, e.g. euler")
    gen.add_argument("--scheduler", help="override scheduler, e.g. simple")
    gen.add_argument("--width", type=int, help="override latent width")
    gen.add_argument("--height", type=int, help="override latent height")
    gen.add_argument("--set", action="append", default=[], metavar="NODE.input=value",
                     help="patch any input of the generation workflow, e.g. --set 54.denoise=0.8; "
                          "repeatable. Run --inspect for node ids")

    post = p.add_argument_group("post-processing")
    post.add_argument("--post", action="append", default=[], metavar="WORKFLOW",
                      help="run an image->image workflow on each result; repeatable, runs in order. "
                           "Accepts a path or a shorthand: %s" % ", ".join(sorted(POST_ALIASES)))
    post.add_argument("--post-only", action="store_true",
                      help="skip generation; run the --post chain over images already in the manifest")
    post.add_argument("--post-output", metavar="NODE",
                      help="node id to save from when a post workflow has no SaveImage")

    out = p.add_argument_group("output")
    out.add_argument("--output-prefix", default="LancerMechs",
                     help="top-level subfolder for generated images (default: LancerMechs)")
    out.add_argument("--post-prefix", default="LancerFoundryTokens",
                     help="top-level subfolder for --post results, kept separate from the raw "
                          "generations so it can be imported into Foundry as-is "
                          "(default: LancerFoundryTokens; pass LancerMechs for "
                          "the old side-by-side layout)")
    out.add_argument("--download-to", type=Path,
                     help="also copy finished images here (ComfyUI always keeps its own copy)")
    out.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST,
                     help="record of completed entries and their seeds")
    out.add_argument("--resume", action="store_true", help="skip entries already recorded in the manifest")

    run = p.add_argument_group("run mode")
    run.add_argument("--server", help="ComfyUI address, e.g. 127.0.0.1:8000 (default: probe 8000-8015)")
    run.add_argument("--list", action="store_true", help="list the entries that would run, then exit")
    run.add_argument("--inspect", action="store_true",
                     help="print each workflow's nodes and the inputs this script writes, then exit")
    run.add_argument("--dry-run", action="store_true", help="build and validate every job, but queue nothing")
    run.add_argument("--dump-job", type=Path,
                     help="with --dry-run, write the first built job here for inspection")
    run.add_argument("--timeout", type=float, default=1800,
                     help="per-image timeout in seconds (default 1800)")

    args = p.parse_args(argv)
    if args.skip_alternates and args.only_alternates:
        p.error("--skip-alternates and --only-alternates are mutually exclusive")
    if args.variants < 1:
        p.error("--variants must be at least 1")
    if args.post_only and not args.post:
        p.error("--post-only needs at least one --post workflow")
    if args.post_only and args.resume:
        p.error("--post-only reads the manifest; --resume would skip every entry in it")

    resolved_sets = []
    for spec in args.set:
        try:
            resolved_sets.append(parse_set(spec))
        except ValueError as exc:
            p.error("--set %s" % exc)
    args.set = resolved_sets

    # Keep the alias as the filename suffix - "Blackbeard_rmbg.png" beats
    # "Blackbeard_Util_RemoveBackground_makeTransparent.png".
    resolved = []
    for name in args.post:
        alias = name.lower()
        path = Path(POST_ALIASES.get(alias, name))
        if not path.exists():
            p.error("post workflow not found: %s" % path)
        resolved.append((alias if alias in POST_ALIASES else path.stem, path))
    args.post = resolved
    return args


def post_prefix(args, entry, label):
    """filename_prefix for a post-pass result.

    Post outputs get their own root so the finished, background-free PNGs form
    a self-contained tree Foundry can ingest; the heading subfolders are kept
    underneath, and the stage label stays on the filename.
    """
    return ("%s/%s_%s" % (args.post_prefix, entry.prefix, label)).strip("/")


def select(entries, args):
    out = entries

    if args.skip_alternates:
        out = [e for e in out if not e.variant]
    if args.only_alternates:
        out = [e for e in out if e.variant]
    if args.filter:
        rx = re.compile(args.filter, re.I)
        out = [e for e in out if rx.search(e.key) or rx.search(e.name)]
    if args.exclude:
        rx = re.compile(args.exclude, re.I)
        out = [e for e in out if not (rx.search(e.key) or rx.search(e.name))]
    if args.start_at:
        rx = re.compile(args.start_at, re.I)
        for idx, e in enumerate(out):
            if rx.search(e.key) or rx.search(e.name):
                out = out[idx:]
                break
        else:
            out = []
    if args.limit:
        out = out[: args.limit]
    return out


def inspect(args):
    """Dump every workflow this run would use, and what gets written where."""
    if not args.post_only:
        graph = load_api_workflow(args.workflow)
        try:
            slots = locate_slots(graph)
        except WorkflowError as exc:
            raise SystemExit("%s: %s" % (args.workflow.name, exc))
        tags = {
            slots.positive: ["prompt text"],
            slots.sampler: ["seed, steps, cfg, sampler_name, scheduler"],
            slots.save: ["filename_prefix"],
        }
        if slots.latent:
            tags.setdefault(slots.latent, []).append("width, height")
        print("%s  (generation, --workflow)" % args.workflow.name)
        print(describe(graph, tags))

    for label, path in args.post:
        graph = load_api_workflow(path)
        try:
            post_slots = locate_post_slots(graph, args.post_output)
        except WorkflowError as exc:
            raise SystemExit("%s: %s" % (path.name, exc))
        tags = {
            post_slots.load: ["the previous stage's image"],
            post_slots.output: ["filename_prefix"
                                + (", promoted to SaveImage" if post_slots.promoted else "")],
        }
        if post_slots.sampler:
            tags.setdefault(post_slots.sampler, []).append("seed")
        for nid in post_slots.drop:
            tags.setdefault(nid, []).append("dropped: spare preview")
        print("%s%s  (--post %s)" % ("\n", path.name, label))
        print(describe(graph, tags))

    print("%sPatch any of these with --set NODE.input=value (generation workflow only)."
          % "\n")
    return 0


def main(argv=None):
    args = parse_args(argv)

    if not args.prompts.exists():
        raise SystemExit("Prompts file not found: %s" % args.prompts)
    if not args.workflow.exists():
        raise SystemExit("Workflow not found: %s" % args.workflow)

    if args.inspect:
        return inspect(args)

    entries = parse_prompts(args.prompts)
    if not entries:
        raise SystemExit("No prompt blocks found in %s" % args.prompts)

    selected = select(entries, args)
    manifest = load_manifest(args.manifest)
    if args.resume:
        before = len(selected)
        selected = [e for e in selected if e.key not in manifest]
        skipped = before - len(selected)
        if skipped:
            print("--resume: skipping %d entries already in the manifest" % skipped)

    print("%s: %d prompts found, %d selected%s" % (
        args.prompts.name, len(entries), len(selected),
        (" x %d variants" % args.variants) if args.variants > 1 else "",
    ))

    if args.list:
        for e in selected:
            print("  %-58s %-20s line %-5d (%d chars)" % (e.prefix, e.role, e.line, len(e.prompt)))
        return 0

    if not selected:
        print("Nothing to do.")
        return 0

    template = slots = None
    if not args.post_only:
        template = load_api_workflow(args.workflow)
        try:
            slots = locate_slots(template)
        except WorkflowError as exc:
            raise SystemExit("%s: %s" % (args.workflow.name, exc))

        sampler_inputs = template[slots.sampler]["inputs"]
        latent_inputs = template[slots.latent]["inputs"] if slots.latent else {}
        print("workflow: %s  (prompt -> node %s, sampler node %s, save node %s%s)" % (
            args.workflow.name, slots.positive, slots.sampler, slots.save,
            (", latent node " + slots.latent) if slots.latent else "",
        ))
        print("settings: steps=%s cfg=%s sampler=%s scheduler=%s size=%sx%s" % (
            args.steps if args.steps is not None else sampler_inputs.get("steps"),
            args.cfg if args.cfg is not None else sampler_inputs.get("cfg"),
            args.sampler or sampler_inputs.get("sampler_name"),
            args.scheduler or sampler_inputs.get("scheduler"),
            args.width or latent_inputs.get("width", "?"),
            args.height or latent_inputs.get("height", "?"),
        ))

        try:  # fail fast on a template this script cannot fully fill in
            build_job(template, slots, selected[0], 0, args)
        except WorkflowError as exc:
            raise SystemExit("%s: %s" % (args.workflow.name, exc))

    posts = []
    for label, path in args.post:
        post_template = load_api_workflow(path)
        try:
            post_slots = locate_post_slots(post_template, args.post_output)
        except WorkflowError as exc:
            raise SystemExit("%s: %s" % (path.name, exc))
        posts.append((label, path, post_template, post_slots))

        note = ""
        if post_slots.promoted:
            feeds = post_template[post_slots.output]["inputs"].get("images", ["?"])[0]
            note = " (no SaveImage: saving node %s, the preview of node %s)" % (
                post_slots.output, feeds)
        print("post: %s  load node %s -> save node %s%s" % (
            path.name, post_slots.load, post_slots.output, note))

    if args.dry_run:
        first = None
        for e in selected:
            if template:
                job = build_job(template, slots, e, args.seed or 0, args)
                first = first or job
                print("  [dry] %s" % job[slots.save]["inputs"]["filename_prefix"])
            for label, path, post_template, post_slots in posts:
                stage = build_post_job(
                    post_template, post_slots, "<previous stage>",
                    post_prefix(args, e, label), 0, args,
                )
                first = first or stage
                print("       + %-8s -> %s" % (
                    label, stage[post_slots.output]["inputs"]["filename_prefix"]))
        if args.dump_job and first:
            args.dump_job.write_text(json.dumps(first, indent=2), encoding="utf-8")
            print("wrote sample job to %s" % args.dump_job)
        stages = (0 if args.post_only else 1) + len(posts)
        print("dry run OK - %d job(s) would be queued" % (len(selected) * args.variants * stages))
        return 0

    comfy = find_server(args.server)
    print("ComfyUI: %s" % comfy.base)
    if args.download_to:
        args.download_to.mkdir(parents=True, exist_ok=True)

    total = len(selected) * args.variants
    done = failed = 0
    started = time.time()

    def collect(record, indent="    "):
        """Report, optionally download, and return the images a job produced."""
        out = []
        for image in comfy.images(record):
            out.append(image)
            print("%s-> %s" % (indent, os.path.join(image.get("subfolder", ""), image["filename"])))
            if args.download_to:
                try:
                    comfy.download(image, args.download_to)
                except Exception as exc:
                    print("%s! download failed: %s" % (indent, exc), file=sys.stderr)
        return out

    def run_posts(images, entry, seed):
        """Feed each image through the --post chain, stage by stage."""
        produced = []
        for image in images:
            current = image
            for label, path, post_template, post_slots in posts:
                job = build_post_job(
                    post_template, post_slots, image_ref(current),
                    post_prefix(args, entry, label), seed, args,
                )
                print("      + %s" % label, flush=True)
                record = comfy.wait(comfy.queue(job), timeout=args.timeout)
                staged = collect(record, indent="        ")
                if not staged:
                    raise RuntimeError("%s produced no image to pass on" % path.name)
                current = staged[0]
                produced.extend(staged)
        return produced

    for index, entry in enumerate(selected, 1):
        for variant in range(args.variants):
            seed = (args.seed + variant) if args.seed is not None else random.randint(0, 2 ** 32 - 1)
            tag = "[%d/%d]" % (index, len(selected))
            if args.variants > 1:
                tag += " v%d" % (variant + 1)

            if args.post_only:
                sources = manifest_images(manifest, entry)
                if not sources:
                    print("%s %s  - no manifest images to post-process, skipping" % (tag, entry.prefix))
                    continue
                print("%s %s  post-only (%d image(s))" % (tag, entry.prefix, len(sources)), flush=True)
            else:
                print("%s %s  seed=%d" % (tag, entry.prefix, seed), flush=True)

            try:
                if args.post_only:
                    images = sources
                    saved_images = []
                else:
                    job = build_job(template, slots, entry, seed, args)
                    record = comfy.wait(comfy.queue(job), timeout=args.timeout)
                    images = collect(record)
                    saved_images = list(images)
                saved_images += run_posts(images, entry, seed)
            except KeyboardInterrupt:
                # Without this the job ComfyUI is mid-way through - and anything
                # else already queued - keeps running after the script exits.
                print("\ninterrupted - cancelling the running job and clearing the queue")
                comfy.cancel_all()
                save_manifest(args.manifest, manifest)
                print("manifest saved; rerun with --resume to continue")
                return 130
            except Exception as exc:
                failed += 1
                print("    ! %s" % exc, file=sys.stderr)
                continue

            done += 1

            record_entry = manifest.setdefault(entry.key, {
                "name": entry.name,
                "role": entry.role,
                "prefix": entry.prefix,
                "runs": [],
            })
            record_entry["runs"].append({
                "seed": seed,
                "source": [
                    {
                        "filename": i["filename"],
                        "subfolder": i.get("subfolder", ""),
                        "type": i.get("type", "output"),
                    }
                    for i in images
                ],
                # Structured so --post-only can hand these straight back to a
                # LoadImage node without re-deriving the subfolder split.
                "images": [
                    {
                        "filename": i["filename"],
                        "subfolder": i.get("subfolder", ""),
                        "type": i.get("type", "output"),
                    }
                    for i in saved_images
                ],
                "when": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            save_manifest(args.manifest, manifest)

    elapsed = time.time() - started
    print("\ndone: %d/%d generated, %d failed, %.1f min\nmanifest: %s" % (
        done, total, failed, elapsed / 60, args.manifest,
    ))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
