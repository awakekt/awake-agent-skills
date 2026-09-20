# UI verification tools

Use the repository's product commands and manifests as the source of truth. For registered
shadcn cases, the compact loop is:

    scripts/awake ui inspect --component <component> --state <state> --theme both
    scripts/awake ui report

The inspect command captures paired official and Awake evidence, validates it, writes a report and
contact sheet, and records artifact provenance. Open the contact sheet and underlying crops; the
report does not replace visual review.

For focused work, the command family is reference, preview, validate, report, and performance.
Use the commands documented by scripts/awake ui --help; do not invent an unregistered
component/state/theme pair. The parity manifest is the correspondence source of truth and carries
semantic IDs, relationships, and any declared comparison threshold.

For focused test coverage, run the owning module's desktopTest task, such as the Compose
foundation, UI headless, or UI showcase test task. Run scripts/awake verify for the full product
gate when making a completion or merge claim.

The standalone audits remain available for targeted checks:

    python3 tools/shadcn/audit_ui_render_quality.py --project .
    python3 tools/shadcn/theme_contrast_audit.py
    python3 tools/shadcn/ui_visual_diff.py --ref <reference.png> --actual <awake.png>

Useful artifact rules:

- The official source crop is captured from the pinned reference app.
- Awake component crops are generated from semantic IDs in preview metadata; do not manually crop
  screenshots to make frames appear aligned. The maintained helpers are
  tools/shadcn/capture_shadcn_local.py and tools/shadcn/compare_component_crops.py.
- A comparison with missing artifacts, poor overlap, or REVIEW status is unmeasured. Do not add a
  threshold until the crop and heatmap have been reviewed.
- A parity report should state the source rule, expected/actual/delta, lowest owner changed,
  relevant tests, artifact locations, and anything still unmeasured.
- Report every observed drift, REVIEW result, behavior failure, or blocking unmeasured field even
  if the work stops before a fix. Include absolute paths to the source crop, Awake crop, and
  heatmap, plus component/state/viewport, semantic IDs, expected/actual/delta, likely owner,
  remaining uncertainty, and the next verification command.

For product tool ownership and failure behavior, see the Awake repository's
[tools catalogue](https://github.com/awakekt/awake/blob/main/tools/README.md) and
[UI parity procedure](https://github.com/awakekt/awake/blob/main/docs/reference/ui-parity-tool.md).
