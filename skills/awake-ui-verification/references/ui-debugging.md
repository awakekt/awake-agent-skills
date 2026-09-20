# UI debugging

## Interaction failures

Reproduce “nothing happens” in composeTestSession before diagnosing the native window; headless
tests remove OS event delivery as a variable. Render a before frame, send the input, render after,
and compare observable state or pixels.

1. Confirm the target has a stable test tag and that the event reaches its handler.
2. If the handler runs but output does not change, inspect where state is read: a value captured
   during composition may need to be read during measurement or drawing.
3. Reduce the failing UI to a minimal test and add real composition elements back until one
   change reproduces the failure.
4. A layout overlay proves placement, not hit-testing. Awake hit-testing can cover the union of a
   node's own and content bounds; a large gap may intercept a sibling event. Inspect the actual
   hit-test path when bounds look correct but input is swallowed.
5. If needed, instrument the exact dispatcher or measure policy, inspect the test output, and
   remove the temporary instrumentation before finishing.

Prove the fix at the smallest regression test and the production composition that exposed it.

## Proving rendered output

Use composeFrame for single-frame measurements and composeTestSession for input/state changes.
Inspect an actual generated image when the claim is visual. Use the CPU rasterizer for fast,
deterministic diagnosis; use offscreen Vulkan/WebGPU capture when backend paint, shader behavior,
blending, sampling, frame pacing, or anti-aliasing is the question.

The CPU rasterizer must mirror the shared renderer's primitive handling. In particular, translucent
primitives use the same source-over blend path, and FilledPath uses the backend-matching
anti-aliased tessellation. StrokedPath remains un-antialiased because that is also how the shared
backend path currently renders it. When adding a primitive, follow the coalescer's tessellator and
pin the behavior in the rasterizer tests.
