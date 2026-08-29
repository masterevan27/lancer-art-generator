# Mech Catalogue Art Prompts (Krea 2 Turbo, ComfyUI)

Full-body token art prompts for every mech chassis in `lancermechcatalogue.md` — all 35 player frames and all 30 NPC mech classes. Built to match the same style already used for the party's own mechs, "Exchange of Affection" (Absolom's Everest) and "Foot in the Grave" (Naledi's Everest): a detailed painterly illustration style with fine grain texture and halftone dot shading, weathered worn-hardware plating in a restrained grey/olive/rust base, and a single glowing optic-sensor/weapon-glow accent color per mech. Every prompt is full-body, front-facing, and set on a flat white background for the same RMBG background-removal → Foundry token pipeline as the rest of the campaign's tokens.

The three non-mech NPC classes from Part 3 of the catalogue (Human, Squad, Monstrosity) are intentionally excluded — they're biological, not chassis, so a mech token prompt doesn't apply.

**Manufacturer/role visual identity, at a glance** (kept consistent across all entries so families read as related at the table):

- **GMS** — plain, unadorned, baseline. No signature accent beyond a simple amber optic.
- **IPS-Northstar** — boxy, riveted, nautical/anti-piracy industrial heritage. Brass/copper-rust accent tones.
- **Smith-Shimano Corpro** — sleek, precision-engineered, high-tech. Cool violet/silver-blue accent tones, sometimes the campaign's teal-green.
- **HORUS** — asymmetric, improvised, organic-mechanical hybrid, unsettling. A uniform sickly teal-green accent across the whole pattern-group family.
- **Harrison Armory** — imposing, imperial, energy-weapon-heavy. Crimson-red and dull-gold imperial trim over the restrained base.
- **NPC classes** (Artillery/Controller/Defender/Striker/Support) — no fixed manufacturer, so accent colors vary mech-to-mech within each role group to keep individual silhouettes distinguishable at the table.

### Shared settings

CFG 1.0, 8 steps, Euler, Simple scheduler, no negative prompt. Generate tall (1024×1280 or similar) for headroom/footroom margin, then run through the ComfyUI-RMBG node (or remove.bg) for background removal, square-crop centered and facing south for Foundry — identical pipeline to every other mech token in the campaign.

---

## Part 1: Player Frames

### General Massive Systems (GMS)

#### Everest — _Balanced_

```
A full-body illustration of a plain, unpretentious humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its proportions are simple and balanced — no exaggerated bulk or sleekness, just clean, functional lines and sturdy universal-standard joints built to mount almost any weapon system. A standard-issue rifle is held in one hand and a compact sidearm holstered at its hip, its stenciled hull marked only with a faded factory serial code rather than any unit heraldry. A single glowing amber optic sensor sits at its plain, unadorned head. The mech stands fully grounded on both feet, planted and fully visible, in a steady, neutral ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

---

### IPS-Northstar (IPS-N)

#### Blackbeard — _Striker_

```
A full-body illustration of a slim, low-profile humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its silhouette is noticeably narrower and more compact than a typical IPS-Northstar frame, angled surfaces designed to shed radar returns, built for sudden first-strike ambushes. A hydraulic grappling claw is mounted on one forearm, gripping a heavy boarding cutlass in the opposite hand, its edge glowing faint dull copper-rust. A single glowing brass-amber optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a low, coiled ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Drake — _Defender_

```
A full-body illustration of a massive, hulking humanoid combat mech with simian-inspired proportions, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Broad hunched shoulders, oversized forearms, and a bulkhead-thick torso evoke ancient armored infantry. A huge overarm kinetic-ablative shield, riveted and dented from impacts, is braced across one side, while the other arm cradles a heavy rotary fragment assault cannon, its barrels streaked with carbon scoring. A single glowing dull copper-brass optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, braced behind its shield in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Lancaster — _Support_

```
A full-body illustration of a lean, practical humanoid combat mech with an older, slightly dated civilian-transport silhouette, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Mismatched patch panels and visibly retrofitted joints show generations of field maintenance, while precision articulated manipulator arms fold neatly against its back alongside redundant coolant lines and cargo webbing for hauling wounded allies. A compact defensive sidearm is holstered at its hip. A single glowing dull copper optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a steady, watchful stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Nelson — _Striker_

```
A full-body illustration of a fast, rounded humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, beneath faded heraldic bands of white, gold, and red livery marking it as an Albatross peacekeeping order frame. Its hull is built from overlapping fractal-fold plates with a ceramic-like carbon-flake sheen that deflects impacts across its rounded silhouette. A long war pike is gripped two-handed at its side, its haft wrapped in worn leather cord. A single glowing brass-gold optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Raleigh — _Striker_

```
A full-body illustration of a stocky, hard-hitting humanoid combat mech with a distinctive, faintly ornamental silhouette, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. A heavy autocannon with a fat rotating ammo drum is gripped in both hands, its feed belts trailing down to a bulky reloader pack mounted low on its back, purpose-built for sustained close-range fire. Unusual finned shoulder plating and a tapered waist give it an agile, almost stylish profile rare among IPS-N line mechs. A single glowing copper-rust optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Tortuga — _Defender/Striker_

```
A full-body illustration of a broad, heavily plated humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Wide brachial armor plates sheath both forearms, angled and reinforced like a battering ram for breaching bulkhead doors and shielding advancing allies, scarred with deep dents from deck-clearing boarding actions. A compact close-range cannon is braced against one hip, ready to cover a corridor. A single glowing dull copper optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, forearms raised in a bracing, overwatch-ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Vlad — _Controller/Striker_

```
A full-body illustration of a heavily armored, thick-limbed humanoid combat mech descended from an old mining-frame lineage, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. A massive piston-driven spike driver, repurposed from anti-piracy mining tools, is mounted on one forearm, its long pneumatic nail-like ram capable of pinning a target in place, while heavy interlocking chain-link plating and a mounted pickaxe blade hang from its waist. A single glowing dull copper-rust optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, braced in a heavy, frontline-absorbing stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Caliban — _Striker/Controller_

```
A full-body illustration of a compact, densely armored humanoid combat mech built with no wasted space, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its proportions are tight and utilitarian, sized to move efficiently through cramped ship corridors, with no ornamentation or unit heraldry, only stenciled hazard markings. Twin short breaching blades fold flush against its forearms and a compact shotgun is holstered at its hip, alongside a cluster of matte-cased breaching charges. A single glowing dull red optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a tight, coiled ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Zheng — _Striker_

```
A full-body illustration of a scrappy, jury-rigged humanoid combat mech built from a heavily modified base frame, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Mismatched salvaged plating, welded patch-jobs, and stripped-down joints replace its factory-standard bulk, built by a desperate pilot for tumbling, claustrophobic close-quarters kills, now stenciled with rough Trunk Security markings. A modified sawn-down shotgun is gripped in one hand, a pair of scavenged combat knives strapped across its chest. A single glowing dull copper-rust optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a low, aggressive ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

---

### Smith-Shimano Corpro (SSC)

#### Black Witch — _Controller/Support_

```
A full-body illustration of a slim, poised humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. The SSC LUX-Iconic frame is built for area denial, its shoulders and forearms ringed with electromagnetic field emitters that throw a faint teal-green haze, disrupting hostile sensors and jamming incoming fire. A single glowing teal-green optic sensor sits at its head. Fine gilded trim and an engraved heraldic crest along its chest plate mark it as a favored personal-guard chassis among wealthy Karrakin houses. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Death's Head — _Artillery_

```
A full-body illustration of a lean, hexapedal combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. The SSC frame rests on six slender, articulated insectoid legs splayed low and wide for perfect stability, letting it reposition instantly without breaking aim. A massive railgun, its barrel wrapped in glowing pale violet capacitor coils, is braced across its shoulder and forelimbs, with a slimmer spotting scope mounted above the sensor housing. A single glowing pale violet optic sensor sits at its head. The mech stands fully grounded on all six legs, planted low and fully visible, in a ready firing stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Dusk Wing — _Controller/Support_

```
A full-body illustration of a tiny, sleek humanoid-suit combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Evolved from a deep-space EVA suit, its slim torso is ringed with a dozen small maneuvering thruster nozzles, faint cool silver-blue exhaust glow flickering at each vent for near-perfect flight control. A folding array of prismatic lens-panels along its forearms bends and redirects light to mask and support allies. A single glowing silver-blue optic sensor sits behind a rounded helmet-visor. The mech hovers just above the ground on faint thruster glow, body fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Metalmark — _Striker_

```
A full-body illustration of a lean, sturdy humanoid combat mech with an aquiline head, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Part of SSC's BELLA CIAO mil-spec line, its beaked, bird-of-prey head unit sits above layered, feather-like shoulder plating that folds back like wings, hiding redundant cloaking emitters that shimmer pale violet at the seams. Twin arcing shock-claws crackle with pale violet energy at its forearms. A single glowing pale violet optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Monarch — _Artillery_

```
A full-body illustration of a large, broad-shouldered combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Despite its bulk the frame is built for surprising agility, its thick shoulders and hips lined with stacked missile pods and racks bristling with ground-to-ground, ground-to-air, and ground-to-orbit ordnance. A rotating targeting dome studded with cool silver-blue sensor lenses crowns its head, feeding all-theater guidance data to every pod. A single glowing silver-blue optic sensor sits beneath the dome. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Mourning Cloak — _Striker_

```
A full-body illustration of a slender, blade-limbed combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. SSC's newest close-quarters prototype, it carries twin shielded monowire swords coiled at its hips, each blade a near-invisible filament that trails a faint pale violet shimmer when drawn. Long, draping cloak-like plating panels fall from its shoulders, etched with alien-derived circuitry that pulses faintly along the seams, hinting at its experimental short-range teleport systems. A single glowing pale violet optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Swallowtail — _Support_

```
A full-body illustration of a slim, birdlike scout combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Built for rapid, sustained long-range scouting, its back plating splits into a forked, swallowtail-shaped fin housing a retractable sensor mast and array of cool silver-blue targeting lenses. A slim designator rifle is holstered across its back, while faint cloaking emitters ripple along its limbs. A single glowing silver-blue optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Atlas — _Striker_

```
A full-body illustration of a small, form-fitting combat mech with a nearly human silhouette, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Descended from a Karrakin dueling frame, its skintight hardsuit-like plating carries a single power blade sheathed at its hip, edge glowing pale violet, drawing on the recorded techniques of past pilots. In its Sparri-favored configuration it is draped with tribal heirloom markings, carved saga discs, and rough pelts slung across one shoulder. A single glowing pale violet optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

---

### HORUS

#### Balor — _Striker/Defender_

```
A full-body illustration of a mech whose silhouette barely holds together, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its torso and limbs are only partly solid, undulating masses of sickly teal-green nanite swarm boiling and flickering where armor plates should be, like angry churning water given rough humanoid shape. Twin nanobot whips trail from its forearms, each a lashing coil of glowing teal particulate. A single teal optic flickers within the swarm where a head would sit. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance, its nanite mass pooling briefly solid beneath it. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Goblin — _Controller/Support_

```
A full-body illustration of a small, wiry mech barely larger than a piloted hardsuit, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered grey-olive armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its compact, hunched frame is the oldest HORUS pattern still fielded, thin limbed and quick, built for evasion rather than bulk. Intricate recursive circuitry traces across its plating in looping, inscrutable teal-green patterns, faintly pulsing like a living processing weave rather than printed wire. A single narrow teal optic slit sits low on its small angular head, and a compact data-spike weapon is mounted along one forearm. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Gorgon — _Defender_

```
A full-body illustration of a squat, heavily plated mech bristling with intercept weaponry, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its asymmetric torso mounts multiple stubby defense turrets and layered plate shields at odd, improvised angles rather than a matched set. A wide, lidless sensor array where its head should be projects a faint hyperfractal cone of shifting teal-green light, a stuttering basilisk-glow of impossible recursive geometry hanging in the air before it. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance, angled slightly to bring its projector to bear. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Hydra — _Striker/Controller_

```
A full-body illustration of a segmented mech built from clearly disarticulated parts, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Each limb, its torso, and its blocky head are visibly separate modules joined by exposed teal-glowing cabling and docking seams, hinting that any piece could detach and operate as its own drone. Anti-armor cannons and stubby blade mounts are built into the forearm and shin segments rather than held as separate weapons. Its silhouette deliberately gives no fixed impression of a single frame. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance, segments aligned as if freshly reassembled. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Manticore — _Striker_

```
A full-body illustration of a jagged, spine-crowned mech wreathed in crackling plasma, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered rust-streaked grey armor plating with scuffed paint and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, its surface pocked with melted, resolidified metal from repeated heat overload. Tall heat-dispersal spines fan from a humped lightning generator on its back, venting faint teal-white sparking arcs. Bright nets of crackling plasma cling loosely around its forearms and shoulders, feeding a heavy discharge cannon braced across one arm. Its single optic burns a hot ember-orange. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance, arcs of stray lightning grounding through its feet. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Minotaur — _Controller_

```
A full-body illustration of a bulky, boxy mech whose proportions feel subtly wrong, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its torso is oversized and slightly too deep for its frame, seams and vents along its flanks glowing faint teal and revealing glimpses of impossibly dense, folded interior systems that seem to hold more machinery than the exterior could contain. Twin heavy interdiction claws jut from its forearms, humming with a warping teal shimmer that bends the air around them. Its blunt head bears a single flat, unblinking optic band. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Pegasus — _Artillery_

```
A full-body illustration of a slender, long-limbed sniper mech built around a single massive shoulder-mounted weapon, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its frame is refined and precise compared to other HORUS chassis, built around top-tier targeting optics banked across its narrow head in a glowing teal array. The Ushabti, its signature paracausal cannon, is racked along its back and one shoulder, the air around its barrel visibly warping and rippling with faint gravitational and radiological distortion that bends the mech's own silhouette at the edges. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Kobold — _Controller_

```
A full-body illustration of a crude, cobbled-together mech clearly repurposed from mining equipment, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered rust-orange and grey armor plating with heavy rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its frame is an ugly patchwork of drill housings, ore-scoops, and hydraulic mining limbs bolted into a rough combat shape, hissing steam and shuddering at every joint. A repurposed drill-arm has been retooled into a weapon that spits molten, plural-state particulate in a glowing teal-white spray, and crude sigil-like liturgicode markings are scratched across its housing. Its single sensor eye burns dull teal beneath a battered visor-plate. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Lich — _Support_

```
A full-body illustration of a lean, angular mech that looks subtly out of place in time, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered pale-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, its edges faintly flickering and double-exposed as if not fully anchored to the present moment. Its smooth, unfamiliar plate geometry reads as hardware from a future that shouldn't exist yet. A small crystalline "soul vessel" module is mounted at its chest, pulsing with a slow teal-green glow, trailing faint afterimages of itself a half-second behind its own motion. Its single optic strobes erratically between dim and bright teal. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance, its outline faintly doubled as though caught between two moments. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

---

### Harrison Armory (HA)

#### Barbarossa — _Artillery_

```
A full-body illustration of an immense, hulking humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, towering far above a typical battlefield frame with thick, over-scaled proportions, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, worked through with controlled crimson-red imperial striping across its heavy chassis. A single glowing dull-gold optic sensor is set into its blunt, helmet-like head. Both arms and a reinforced shoulder cradle support an enormous ship-killing cannon barrel long enough to trail past its knees, its muzzle glowing faint red-gold with heat bleed, while thick recoil-dampening struts brace its oversized legs. The mech stands fully grounded on both feet, planted in a wide, immovable stance built to absorb its own recoil. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Genghis — _Striker_

```
A full-body illustration of a lean, aggressive humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, with thin crimson-red imperial trim striping its shoulders and forearms. A single glowing dull-gold optic sensor burns beneath its angular brow. Twin flame-projector nozzles are mounted along its forearms, fed by bulky heat-blackened fuel tanks slung across its back, their scorched and pitted surfaces betraying constant use, with faint orange embers glowing at the vent slits along its spine. A short incendiary sidearm is holstered at its hip. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Iskander — _Controller_

```
A full-body illustration of a bulky, heavily instrumented humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, laced with dull-gold imperial accent striping across its broad torso. A single glowing crimson-red optic sensor is recessed into its wide, sensor-studded head. Segmented gravity-manipulation emitters ring its shoulders and forearms, faintly warping the air around them, while a dense array of scanning dishes and antenna clusters bristles across its back for locating buried ordnance. A compact sidearm rides at its hip. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Napoleon — _Defender/Controller_

```
A full-body illustration of a squat, compact humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, its proportions dense and low rather than tall, densely packed with hardware, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, trimmed with narrow dull-gold imperial banding across its stocky chassis. A single glowing crimson-red optic sensor sits low in its compact head. One arm grips the Displacer, a heavy, oddly-barreled weapon ringed with exotic lensing rings that pulse with a faint violet-white blinkspace glow, while its opposite forearm houses a stasis-projection emitter studded with fine antenna spines. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Saladin — _Defender_

```
A full-body illustration of a massive, broad-shouldered humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, its bulk reassuringly solid and wide rather than sleek, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, banded with dull-gold imperial trim across its heavy shoulder plates. A single glowing crimson-red optic sensor is set into its broad, squared-off head. Large shield-projector housings are mounted across both forearms and shoulders, faint blue-white energy shimmer flickering at their emitter rings, while a reinforced ammunition drum and support-beacon array are strapped across its wide back. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Sherman — _Striker/Artillery_

```
A full-body illustration of a tall, rugged humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, its proportions sturdy and versatile in the classic Armory battle-line silhouette, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, striped with controlled crimson-red imperial banding down its chest and limbs. A single glowing dull-gold optic sensor sits beneath its angular brow. One hand grips an oversized laser lance nearly as long as the mech is tall, its crystalline focusing core glowing hot crimson-red, while a secondary energy rifle is holstered across its back. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Tokugawa — _Striker_

```
A full-body illustration of a heavily built, imposing humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, its frame thick and unsubtle with an aggressive forward-leaning silhouette, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, ringed with dull-gold imperial trim around its chest and pauldrons. A single glowing crimson-red optic sensor burns in its heavy head. An exposed reactor core is set into its chest behind vented, heat-warped grating, glowing pulsing crimson-red and venting bright plasma flare along its shoulders and forearms, feeding a massive cleaving energy blade gripped two-handed and crackling with overcharged power. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Sunzi — _Support/Controller_

```
A full-body illustration of a small, compact humanoid combat mech barely taller than a person, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, its proportions squat yet bristling with oversized, ill-fitting hardware, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows, faintly striped with dull-gold imperial trim that looks bolted onto older, stranger material beneath. A single glowing violet-white optic sensor sits within a smooth, non-human-derived faceplate of rippling recursive-mesh substrate. Faint blinkspace distortion shimmers around its shoulders and the outsized space-warping emitter array mounted across its back, oversized relative to its small frame. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

---

## Part 2: NPC Mech Classes

### Artillery

#### Bombard — _Artillery_

```
A full-body illustration of a heavy, squat combat mech with a low, wide-legged stance and thick, over-built proportions, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Built for staying power in fortified positions, its bulky torso carries a massive shoulder-mounted area-effect ordnance launcher with a cluster of thick barrel tubes, and a secondary rack of heavy mortar shells is fixed across its back. Reinforced hydraulic support struts brace its thick legs against recoil. A single glowing amber optic sensor sits deep-set in its blunt, armored head. The mech stands fully grounded on both feet, planted and fully visible, in a wide, braced stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Operator — _Artillery_

```
A full-body illustration of a sleek, tech-heavy combat mech with slender limbs and a compact torso dense with exposed circuitry conduits, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Despite its artillery role it reads agile and advanced, with a compact short-range blink-teleport array built into its spine and shoulder housings, faint sickly-green energy arcing across exposed capacitor coils. A long-barreled precision artillery cannon is mounted along one forearm. A single glowing sickly-green optic sensor sits at its head, and scorched, self-immolation scarring darkens the seams of its chassis. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Rainmaker — _Artillery_

```
A full-body illustration of a mid-weight combat mech with broad shoulders and a sturdy, balanced frame built to carry heavy ordnance, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-drab armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Prominent rocket pod arrays are mounted across both shoulders and stacked along its back, each tube stenciled with warning markings and loaded with delayed-impact rockets, a faint red targeting glow visible deep in the launch tubes. A stabilizing targeting mast rises from one shoulder. A single glowing red optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Sniper — _Artillery_

```
A full-body illustration of a lean, elongated combat mech built for stability over mobility, narrow torso set atop reinforced, wide-braced legs with visible stabilizing struts, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. An exceptionally long, precision kinetic cannon rests across a folded bipod mount at its side, its barrel extending well past its own height, and a compact rangefinding array juts from one shoulder. A single glowing teal-green optic sensor sits at its head, faint and narrow. The mech stands fully grounded on both feet, planted and fully visible, in a stable, braced firing stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

---

### Controller

#### Archer — _Controller_

```
A full-body illustration of a lightly armored, precise combat mech with a slim, agile build and refined, high-tech joint housings, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its sacrificed armor plating is thin over dense superpositional maneuvering thrusters at its hips and shoulders, and an advanced targeting-array visor wraps across the front of its head, lensed segments glowing amber. A precision rifle with an integrated targeting scope is held level in both hands. A single glowing amber optic sensor pulses at the center of the visor array. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Barricade — _Controller_

```
A full-body illustration of a blocky, heavily armored combat mech built like a mobile fortification, broad flat-plated torso and thick reinforced limbs, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Large deployable cover panels fold flat against its forearms and back, hinged and stenciled with hazard markings, ready to unfold into barrier walls, and a compact barrier-projection emitter is mounted on one shoulder, faint red warning lights tracing its edge. A single glowing red optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a wide, bracing stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Hive — _Controller_

```
A full-body illustration of a broad-backed combat mech built to carry a drone swarm, its torso studded with rows of small drone-launch ports along its shoulders and spine, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. A handful of small support drones hover docked at its shoulders and hips, each glowing with a faint teal-green running light matching its paired hive-nexus coordination array mounted on its back. A short-barreled coordination cannon is held at its side. A single glowing teal-green optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Hornet — _Controller_

```
A full-body illustration of a sleek, aerodynamic combat mech with narrow, streamlined limbs and smooth-flowing panel lines carried over from its civilian racing-chassis origins, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Faded racing stripe decals still trace its flanks beneath the military overpaint, and compact speed-boost thrusters are mounted at its calves and lower back, faint sickly-green exhaust glow at the vents. A short, quick-draw sidearm is holstered at its hip. A single glowing sickly-green optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a light, ready-to-spring stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Seeder — _Controller_

```
A full-body illustration of a utilitarian, heavily laden combat mech with a boxy torso built around bulky equipment housings, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-drab armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Racks of deployable mines and trap canisters line its lower back and hips, each stenciled with red hazard markings, and a folding sensor-suite mast studded with small dish arrays rises from one shoulder. A stubby deployment launcher is gripped in one hand. A single glowing red optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Witch — _Controller_

```
A full-body illustration of an eerie, angular combat mech cluttered with mismatched antenna and sensor arrays sprouting from its shoulders, back, and head, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Thin cabling links its head-mounted array to a cluster of small NHP data-cores nested at its collar, faint amber static crawling across their casings as if two signals were speaking at once, and heat-vents along its forearms glow faintly from thermal weapon systems. A compact heat-lance is gripped in one hand. A single glowing amber optic sensor sits at its head, flickering unevenly. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

---

### Defender

#### Bastion — _Defender_

```
A full-body illustration of a broad-shouldered, heavily plated humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. A single glowing amber optic sensor sits at its head. Its left arm carries a massive riot-style ballistic shield etched with unit markings, while its shoulder mounts a tall segmented communication and coordination antenna array bristling with sensor dishes. A stubby suppression cannon is holstered at its hip. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Demolisher — _Defender_

```
A full-body illustration of a hulking, slow-moving humanoid combat mech with a massive barrel chest and thick hydraulic-braced legs, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered dark olive armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. A single glowing orange optic sensor sits at its head. Both hands grip an oversized concussion maul, its massive hammerhead etched with old battle scoring and faint orange energy crackling along its striking face, while heavy stabilizer struts and reinforced footpads anchor its legs. The mech stands fully grounded on both feet, planted and fully visible, in a wide braced stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Goliath — _Defender_

```
A full-body illustration of an enormous, thickly plated humanoid combat mech with the widest, most physically imposing frame of its kind, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered slate-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. A single glowing cyan optic sensor sits at its head. Its oversized forearms end in reinforced knuckle plating built for grappling and close brawling, layered slab armor bulking its torso and shoulders far beyond a normal frame, with a heavy retractable ram-spike folded along one forearm. The mech stands fully grounded on both feet, planted and fully visible, in a wide-legged brawler's stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Pyro — _Defender_

```
A full-body illustration of a bulky, well-insulated humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered ash-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. A single glowing red-orange optic sensor sits at its head. A heavy chemical-flame projector is mounted along one forearm with a fuel canister rig strapped across its back, its armor scorched black in streaks from its own weapon's backwash, and rows of heat-venting slats glow faint orange along its torso where excess heat bleeds off. A compact shield-emitter module sits on its opposite shoulder. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Sentinel — _Defender_

```
A full-body illustration of a leaner, more mobile humanoid combat mech, lighter-framed than heavier defender chassis but still solidly built, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered grey-green armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. A single glowing teal optic sensor sits at its head. A compact forearm-mounted riot shield folds flush against one arm, paired with a slim technical sidearm holstered at its hip for preemptive suppressive fire, and a small defensive-tech relay unit is mounted on its shoulder with a faint teal signal glow. The mech stands fully grounded on both feet, planted and fully visible, in an alert, forward-leaning ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

---

### Striker

#### Ace — _Striker_

```
A full-body illustration of a sleek, aerodynamic humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered slate-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. This Striker's frame is built for high-speed strafing runs, with swept wing-like flight stabilizers and a pair of oversized dorsal thrusters trailing a bright cyan-blue exhaust glow. A single glowing cyan optic sensor sits at its narrow, raked-back head, giving it a cocky, dueling-ace posture. A twin-linked light cannon is mounted along its forearm. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Assassin — _Striker_

```
A full-body illustration of a slim, minimal humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered dark gunmetal armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its silhouette is stripped-down and predatory, limbs narrow and cabling exposed where bulky life-support housing has been cut away in favor of processing cores and stealth coating. A single glowing violet optic sensor narrows at its low-slung head. A compact suppressed rifle is held low in one hand, with a thin monofilament blade sheathed along its forearm. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Assault — _Striker_

```
A full-body illustration of a sturdy, well-proportioned humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-drab armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its build is deliberately unremarkable and dependable, the most common battle frame in the galaxy, balanced and boxy with reinforced targeting sensors along its shoulders. A single glowing amber optic sensor sits centered in its blunt head. A heavy rifle is gripped in both hands, a sidearm holstered at its hip. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Berserker — _Striker_

```
A full-body illustration of a hulking, forward-hunched humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered scorched-charcoal armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Exposed heat-cycling vents run along its forearms and spine, glowing a fierce red-orange as they shunt built-up heat into raw offensive force, wisps of heat-shimmer rising off the plating. A single glowing red-orange optic sensor burns beneath a hunched brow. Massive clawed knuckle-guards and a heavy vibro-hammer are held ready for close combat. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Breacher — _Striker_

```
A full-body illustration of a blunt, battering-ram humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered heavy-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its torso and forearms carry oversized, reinforced frontal plating scarred and dented from repeated impacts, built for smashing through hulls and armor in boarding operations. A single glowing yellow optic sensor sits behind a narrow visor slit. A massive hydraulic ram-fist is mounted over one arm, a stubby short-range breaching cannon slung across its back. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Cataphract — _Striker_

```
A full-body illustration of a lean, angular humanoid combat mech built for rapid shock assaults, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-black armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its legs are heavily articulated for sudden bursts of speed meant to punch through defensive lines, and a massive barrel-shaped Ram Cannon is mounted across one shoulder, its muzzle ringed with a glowing deep-blue charge. A single glowing deep-blue optic sensor sits at its narrow head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Engineer — _Striker_

```
A full-body illustration of a broad-shouldered humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. A rack of folded deployable turret modules is mounted across its back and shoulders, cabling and deployment rails visible, built to hang back mid-line and coordinate asset placement across the field. A single glowing green optic sensor sits at its head, matched by a soft green status glow along the turret rack's charging ports. A mid-weight support rifle is held at its side. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Ronin — _Striker_

```
A full-body illustration of a lean, poised humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered lacquered dark-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Built by boutique fabricators in an antique, traditional style favored by martial cultures, its frame carries subtle armor fluting reminiscent of lamellar plating. A single glowing crimson optic sensor sits beneath a narrow, helm-like brow. An elegant single-edged energy blade is held two-handed in a duelist's stance, its edge tracing a thin crimson glow, with a smaller companion blade sheathed at its hip. The mech stands fully grounded on both feet, planted and fully visible, in a poised dueling stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Scourer — _Striker_

```
A full-body illustration of a heavier, deliberate humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered rust-heavy grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its broad back houses a massive recursive power plant, vented sections glowing hot and venting faint magenta-tinged haze, feeding a huge shoulder-mounted beam-cannon built to support ground troops with sustained fire. A single glowing magenta optic sensor sits at its heavy, squared head. The stance is wide and stable rather than agile, built to plant and unleash sustained beam fire. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Specter — _Striker_

```
A full-body illustration of a sleek, angular humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered pale grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Sections of its armor are worked with faceted optical-camouflage panels that shimmer and flicker semi-transparent, edges dissolving softly into the surrounding white as if caught mid-phase between visible and cloaked. A single glowing pale ghostly blue-white optic sensor is the only fixed point of light on its otherwise dissolving silhouette. A slim precision rifle is held low and close to the body. The mech stands fully grounded on both feet, planted and fully visible, in a low, watchful ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

---

### Support

#### Aegis — _Support_

```
A full-body illustration of a stocky, broad-shouldered humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered gunmetal-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its silhouette is thick and squat, built for holding ground, with reinforced double-layer plating across its torso and forearms. A large collapsible shield-projection array is mounted along one forearm, its emitter ring glowing steady amber, ready to unfurl into a broad energy bulwark. A single glowing amber optic sensor sits at its head, and a stubby suppression cannon is holstered at its hip. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Mirage — _Support_

```
A full-body illustration of a sleek, slender humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered pale-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its frame is narrow and elegant, with tapered limbs and smooth, minimal plating etched with faint liturgicode script. A shimmering violet distortion ripples faintly across its surface, sensor-warping veils of illusion bending the air around its shoulders and trailing off its cloak-like rear vents. A single glowing violet optic sensor sits at its head, half-obscured by a haze of refracted light. The mech stands fully grounded on both feet, planted and fully visible, in a poised, watchful stance, faint afterimages flickering at its edges. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Priest — _Support_

```
A full-body illustration of a tall, gaunt humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered ash-grey armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its frame is wrapped in dense bundles of data-cable and coiled antenna wire, with a crown of thin relay spires rising from its shoulders and a ring of interface ports studding its chest like a ritual collar. A single glowing cyan optic sensor sits at its head, pulsing in rhythm with faint cyan light traveling along its cabling. Its posture carries an almost cultish stillness, arms hanging loose beside trailing cable-lengths. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Scout — _Support_

```
A full-body illustration of a lean, long-limbed humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered olive-drab armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its silhouette is narrow and sensor-heavy, with a prominent segmented scanner dome rising above its head housing a battery of targeting optics, and folding antenna vanes mounted along its back. A single glowing green optic sensor sits beneath the dome, sweeping light briefly visible. A slim designator rifle is holstered across its back, built more for marking targets than close combat. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```

#### Support — _Support_

```
A full-body illustration of a sturdy, boxy humanoid combat mech, standing and facing directly forward, entire body visible from the top of its head to the base of its feet with clear empty space above and below, rendered in a detailed painterly illustration style matching worn military hardware: weathered off-white armor plating with rust streaks, scuffed paint, and stenciled panel markings, fine grain texture, halftone dot shading in the shadows. Its build reads as field-medic utility rather than combat, with a folding repair-arm tipped in a flash-weld torch mounted on one shoulder and a second arm ending in a broad structural-clamp tool. Rows of nanite canisters and whitewash slurry tanks are strapped across its back and waist, one torch tip glowing faint orange. A single glowing orange optic sensor sits at its head. The mech stands fully grounded on both feet, planted and fully visible, in a ready stance. The background is a solid flat plain white, no texture, no gradient, no shadow, no environment. Centered composition, even lighting, isolated illustration, clean silhouette.
```
