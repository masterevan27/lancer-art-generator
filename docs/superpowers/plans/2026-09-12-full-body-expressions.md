# Full-body Expressions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate head-to-toe expression sprites by default, including from cropped portraits.

**Architecture:** Keep the original portrait as Qwen image-edit conditioning, but sample a tall empty latent instead of inheriting its crop. Preserve existing expression selection, identity anchors, transparency, persistence and GUI contracts.

**Tech Stack:** Python standard library, ComfyUI Qwen Image Edit / RMBG / WebP, unittest.

**Spec:** User-approved in-chat amendment on 2026-09-12: full-body sprites by default, head-to-toe framing, tall canvas, transparent backgrounds; infer unseen clothing and legs from cropped references. Existing sprites stay untouched until explicitly regenerated. This supersedes the bust/framing-preservation language in the original character-expressions spec.

## Global Constraints

- Every sprite is a separate edit of the original portrait, never another sprite.
- Preserve identity-safe appearance anchors and exclude Demeanor.
- Transparency stays the default; keep-background still works.
- No automatic regeneration or rewriting existing image files or metadata.
- No new CLI or GUI controls, dependencies, or unrelated refactoring.
- Retain variant, replace-after-success, exact-file redo, sidecar and path-safety behavior.

### Task 1: Change framing and output canvas

**Files:**
- Modify `generate-expressions.py`: prompt assembly and saved-prompt redo compatibility.
- Modify `workflows/api/Util_Expression_QwenEdit_RMBG_v1.json`: latent canvas.
- Modify `test/test_generate_expressions.py`: prompt/planning and graph regressions.
- Modify `docs/generate-expressions.md` and `prompts/expression-tables.md`: current behavior and regeneration guidance.

**Interfaces:** Keep existing function signatures and sidecar schema. The live server confirms `EmptySD3LatentImage` accepts width, height, batch_size. Use width 768, height 1344, batch_size 1; keep original LoadImage linked to positive encoder image1. Root orchestrator will independently render and inspect one disposable sample after code is ready.

- [ ] Write failing regressions before implementation. Extend the existing prompt boundary test to require head-to-toe/full-body instructions and prohibit preserving camera framing or asking for a bust. Exercise build_graph and follow KSampler.latent_image to verify a tall empty latent while positive.image1 still references the uploaded original. Example canvas assertion:

```python
graph = self.build()
_, sampler = only(graph, "KSampler")
latent = graph[sampler["inputs"]["latent_image"][0]]
self.assertEqual(latent["class_type"], "EmptySD3LatentImage")
self.assertEqual(latent["inputs"], {"width": 768, "height": 1344, "batch_size": 1})
```

- [ ] Cover exact-file redo of a legacy tableless custom sprite: only the exact known old generated preamble is replaced with the new preamble; preserve its appearance anchors and custom expression suffix. Unrecognized saved prompts remain verbatim. Existing current prompts must not gain duplicate preambles. Test literal old prompt input, preserved custom text and no legacy crop instruction. This is lazy prompt adaptation during explicit redo, not a disk migration.
- [ ] Run `python -m unittest discover -s test -p test_generate_expressions.py -q` and record expected failures.
- [ ] Change the prompt to preserve face, hair, outfit, colours, accessories and art style; request one front-facing standing full-body character, entire head, hands and both feet visible with margin, no cropping or text. Instruct coherent extension of unseen clothing/legs matching the reference. Do not keep the source camera framing or pose. Keep emotion and small body language. Keep an exact legacy preamble constant solely to recognize old generated saved prompts:

```python
if saved and saved.get("prompt"):
    prompt = saved["prompt"]
    if prompt.startswith(LEGACY_IDENTITY_PREAMBLE):
        return IDENTITY_PREAMBLE + prompt[len(LEGACY_IDENTITY_PREAMBLE):]
    return prompt
```

- [ ] Replace workflow source VAEEncode with `EmptySD3LatentImage`, inputs `{"width": 768, "height": 1344, "batch_size": 1}` and accurate title. Preserve sampler link, conditioning image, models, sampler parameters and alpha pipeline.
- [ ] Update current documentation: full-body 768x1344 default, cropped references require invented unseen details, inspect head/feet and identity, existing sprites remain unchanged until Redo/Replace. Clarify recognized legacy custom prompt redo updates its framing, unrecognized saved prompts remain verbatim; --describe can supply a fresh instruction. Remove stale present-tense bust/square smoke-result wording; do not claim a new smoke result until verified.
- [ ] Run focused tests, full suite once (`python -m unittest discover -s test -q`), `git diff --check`, self-review and commit. Report RED/GREEN evidence, changed files and concerns. Do not render on ComfyUI: orchestrator owns that check.

### Task 2: Preserve reference art style

**Spec amendment:** User explicitly approved on 2026-09-12: reuse only style wording from the original NPC portrait prompt, excluding old expression, pose and square framing. Arbitrary images should more closely match their reference's linework, shading, texture and palette.

**Files:** Modify `generate-expressions.py`, `test/test_generate_expressions.py`, `docs/generate-expressions.md`, `README.md`.

**Interfaces:** Task 1 provides full-body framing and legacy preamble adaptation. Add a defaulted string field `style_prompt` to Source, and optional trailing `style_prompt=""` parameters through make_plans / _expression_prompt / assemble_prompt. Read only NPC manifest `portraitPrompt`, not tokenPrompt or the current generator template. Image mode and missing/unrecognized/non-string portraitPrompt use no textual house style.

- [ ] Add RED regressions at observable prompt boundaries. Use a temporary real manifest and portrait fixture; `main(... --manifest ... --id ... -e joy --dry-run)` must emit the saved distinctive style clause but no old demeanor, camera framing, stance or backdrop. Use literal historical fixture like:

```python
original = (
    "A half-body character portrait of a pilot, rendered in a loose charcoal "
    "illustration style with rough crosshatching, soft side lighting. "
    "Her face carries a permanent scowl. She sits in a cockpit. "
    "Shallow depth of field, square framing, high detail, atmospheric sci-fi "
    "character portrait, painterly brushwork with violet grain in every shadow."
)
```

- [ ] Cover missing and non-string/unrecognized portraitPrompt fallback; image mode must request faithful style matching without injecting NPC painterly/halftone keywords. Cover style propagation for custom, --describe and exact-file redo paths and preserve existing target emotion/identity anchors.
- [ ] Run focused expression tests and record failures before implementation.
- [ ] Extract only recognizable style clauses from stored NPC portrait prompts. Preserve their wording: the complete sentence fragment beginning `rendered in ` through its sentence terminator, and the final `painterly brushwork ...` style clause when present. Use anchored/template-context boundaries so appearance/backdrop prose containing these words cannot accidentally become style. No generic sentence-keyword scraping, copying entire prompts, regenerating descriptions from today's tables, or new dependencies. Unrecognized templates fall back to reference-only matching. Example known opening style boundary:

```python
opening = re.search(r", (rendered in [^.!?]+[.!?])", portrait_prompt)
```

Keep the extractor conservative: recognize an opening generator portrait description before that clause, and the known `atmospheric sci-fi character portrait, ` context for the closing clause, not matching arbitrary embedded mentions. Validate/handle empty and non-string inputs without crashing.

- [ ] Strengthen the common edit instruction: reproduce the reference's rendering medium, linework, brushwork, texture/grain, shading, colour palette, contrast, detail level and stylized proportions; newly invented full-body areas use the same style. Do not force painterly, anime, photorealistic or other new aesthetics for arbitrary images. Retain full-body/target emotion as requested changes and original image conditioning. Append extracted NPC wording labeled as original portrait style. Preserve style during saved generated custom redo without duplicating style blocks; unknown arbitrary saved prompts remain verbatim as the existing compatibility contract specifies.
- [ ] Thread style context only in NPC source resolution and planning; preserve function compatibility with defaulted trailing arguments and unchanged sidecar schema. No GUI changes needed because GUI invokes the CLI's NPC mode.
- [ ] Update current docs and README: full-body output, image-derived style matching, exact recognized saved NPC style wording, reference fallback for legacy manifests, no guarantee of perfect matching, redo/replace existing sprites to opt in. Keep historical plan/spec clearly historical.
- [ ] Run focused tests, full suite once, diff checks, self-review and commit. Report RED/GREEN commands and evidence. Controller owns live ComfyUI sample verification, do not render yourself.
