# Visual parity and baselines

## Evidence authority

For each registered component/state/theme, use the pinned reference capture and its computed-style
JSON together with the source file at the same upstream revision. A screenshot alone cannot
establish why a value is present. Confirm that reference and Awake artifacts represent the same
component, state, theme, viewport, and content before comparing them.

Keep the questions separate:

- Geometry and declared layout relationships need semantic or browser-geometry evidence.
- Normalized style values need their matching computed-style oracle.
- Pixel diffs are diagnostic for paint; rasterizers, fonts, anti-aliasing, and color management
  prevent them from being a universal correctness score.
- Behavior and motion need interaction tests; static images do not cover them.

Report scoped results with both score and coverage. A scope at 100% with incomplete coverage is
not complete parity. Do not average unrelated dimensions into one parity percentage.

## Required comparison loop

1. Capture reference and Awake artifacts before editing; inspect the source crop, Awake crop, and
   heatmap.
2. Triage correspondence first, then geometry, padding/spacing, layout intent, computed style,
   paint, and behavior/motion. Missing, partial, or unmeasured evidence is not a pass.
3. Read the pinned source and captured values; do not infer current shadcn behavior from memory.
4. Fix the lowest reusable owner. Keep generic measurement/input/rendering fixes in the engine
   layer and recipe-only rules in the design system.
5. Add a focused regression at that owner, recapture, inspect fresh artifacts, and report the
   before/after facts plus remaining coverage gaps.

## Updating snapshots

1. Run the test without recording and let it fail.
2. Open the diff image and state a predictive rule for which cases should move and why.
3. Audit all moved and unmoved cases against that rule. An unexplained change is a bug to
   investigate, not a reason to accept the baseline.
4. Only after the result is explained, record once at the end of the visual change set.
5. Update separate signature maps by hand as well; the snapshot record flag does not update them.

Keep untouched-test results distinct from re-recorded snapshot results. A passing newly recorded
golden is not independent evidence of correctness.
