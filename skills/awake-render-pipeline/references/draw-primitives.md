# Draw primitives and decorations

A border, ring, outline, or underline is the boundary of a shape. Use the existing stroke
primitive (StrokedPath and its shared tessellator) instead of assembling independently filled
rectangles. Filled strips cannot represent rounded corners reliably.

Before introducing a draw primitive or modifier, search the whole tree for an existing capability
by both name and behavior. Shared render:passes2d code should resolve the primitive before either
backend sees it; do not add backend-specific cases when the shared path already supports it.
