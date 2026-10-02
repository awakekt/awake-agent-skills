---
name: awake-capability-extraction
description: Audit reusable capabilities across Awake Core and Awake Pro, define ownership, and prevent duplicate platform utilities.
---

# Awake capability extraction

Use this skill when moving code between `awakekt/awake` and `awake-pro`.

1. Search both repositories for equivalent readers, writers, codecs, path types, and platform adapters.
2. Record one owner for each capability. Core owns generic contracts, adapters, codecs, asset
   bytes, the public editor/plugin contracts, and every runtime a shipped game needs, including the
   runtime that reads data a Studio tool emits. Pro owns the editor library and app, authoring
   tools, cloud, the plugin loader, and entitlement-gated commercial editor-plugins. Runtime is
   never commercial. Game rules and template values belong to neither; they stay in the game or
   template.
3. Keep the dependency direction `Studio -> Core`; Core must not import Studio packages or authoring policy.
4. When moving code from Studio into Core, apply the promotion steps in `awake-framework-boundary`
   first: move the mechanism, leave the values as scene data. Extract the smallest common API, add
   an in-memory reference implementation, and migrate one consumer before deleting a duplicate.
5. Add a boundary check and a contract test for every extracted capability.

Use `feat/*` for new Core capability work and `refactor/*` for consumer migration. Start Core work from the latest `main`, publish Core before beginning a Pro migration, and keep unrelated dirty checkouts untouched.
