---
type: "Reference"
title: "Versioning"
description: "Release version source, increment rules and automation for this repository."
---
# Versioning

A repository coordination version is stored in the root `VERSION` file.

Every completed change should update the project version once, including changes made directly on the default branch. Use patch/subversion increases for ordinary changes, minor increases for larger compatible changes, and reserve major increases for intentional breaking or owner-approved releases. Use conventional unpadded numeric versions where the existing project format permits it.

Canonical version source: [`VERSION`](../VERSION). Keep this file as the agent-facing explanation of that source; do not create a competing version field when release automation already owns the version.

Projects without a website still maintain version information in the repository so future tooling can discover it. For this project the initial repository coordination version is `0.1.0`; bump the root `VERSION` file with the same change when the project changes.

