---
name: awake-platform-capability-design
description: Design weakest-platform-first Awake APIs for asynchronous storage, handles, paths, browser persistence, and portable engine capabilities.
---

# Awake platform capability design

Design an Awake Core contract from the least capable supported target, especially Wasm.

- Make I/O `suspend`; never expose blocking common file access or nullable failure signals.
- Accept only normalized root-relative paths. Reject absolute paths, drive prefixes, traversal, and ambiguous handles.
- Keep bundled resources separate from project files and expose bytes through injected readers.
- Define atomicity, transaction visibility, watcher ordering, and failure semantics before writing platform adapters.
- Use platform APIs only in source-set adapters. Implement missing native behavior with journaling, polling, or virtual storage while preserving common semantics.
- Test the same contract against an in-memory implementation and every supported target.
