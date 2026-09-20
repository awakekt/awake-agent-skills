# Render features and composition

## Feature dispatch

Both backends use an ordered RenderFeature list for features that share a render pass. A feature
depends on a narrow RenderFrameContext port, not Renderer; one adapter exposes only the access it
needs. Keep the depth pre-pass separate because it owns a different render pass and target.

Feature order is observable behavior: register dependencies explicitly (for example, a pass that
consumes a shadow map follows the pass that writes it). Preserve existing pipeline bind/destroy
ownership behind feature wrappers. Do not add per-pass nullable Renderer fields or hardcoded
dispatch branches.

Only features that share the scene pass join this list. The depth pre-pass remains its own
operation; do not invent a shared ownership abstraction for unrelated passes. Authored content
remains opt-in according to the render-extensibility rule, not a backend-specific nullable content
parameter.

## Material and batching

Material owns descriptor/uniform data and implements the shared RenderMaterial contract. It does
not know which pipeline uses it. VertexFormat selects a pipeline from mesh geometry; do not add a
material-to-pipeline back-reference.

Keep 3D draw calls grouped by pipeline so a pipeline binds once per group. Descriptor-set churn is
not currently optimized. Any future material sorting must be confined to 3D: UI draw order is
paint order and must never be reordered for batching.

## Application lifecycle

GameApplication mediates between the platform window, backend Renderer, and injected Game.
Games see only the backend-neutral Renderer interface; backend subclasses create hardware
resources and forward lifecycle callbacks without reaching into game state. One application
instance owns one Game and one Renderer for its lifecycle. New game-visible backend-neutral
capabilities belong on the shared Renderer contract, not a concrete-backend cast.
