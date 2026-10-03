---
name: awake-platform-capability-design
description: Design, extract and test a portable Awake Core capability (storage, paths, handles, codecs, asset sources, browser persistence), weakest platform first. Use before adding a Core contract, writing a codec, moving a capability between Studio and Core, or writing its conformance tests.
---

# Awake platform capability design

## Design from the weakest target

Design an Awake Core contract from the least capable supported target, especially Wasm.

- Make I/O `suspend`; never expose blocking common file access or nullable failure signals.
- Accept only normalized root-relative paths. Reject absolute paths, drive prefixes, traversal, and ambiguous handles.
- Keep bundled resources separate from project files and expose bytes through injected readers.
- Define atomicity, transaction visibility, watcher ordering, and failure semantics before writing platform adapters.
- Use platform APIs only in source-set adapters. Implement missing native behavior with journaling, polling, or virtual storage while preserving common semantics.

## Codecs and asset sources

Codecs accept bytes and return typed values; they do not select directories, download files,
install plugins, or persist documents. Use `AssetSource` for asynchronous `.bin`, image, resource,
and project reads, resolve sidecars relative to the containing asset, then pass the fetched bytes
to a synchronous parser. Use the shared bounds-checked `BinaryReader` for binary formats. Preserve
existing serialized JSON shapes, and add round-trip and malformed-input tests before removing a
product-specific reader.

## Conformance tests

Define behavior once as common tests and run it against an in-memory reference implementation
plus each platform adapter. Cover valid and invalid paths, CRUD, metadata, chunk boundaries,
atomic commit and rollback, transaction visibility, ordered watcher events, and structured
failures. Keep tests independent of desktop paths, wall-clock timing, and platform-specific
exception classes. Add deterministic fakes for unsupported native features rather than weakening
the contract.

## Extracting a capability from Studio or a game

Decide the owner with `awake-framework-boundary` first. Then:

1. Search Core and Studio for equivalent readers, writers, codecs, path types, and adapters.
2. Extract the smallest common API, add its in-memory reference implementation and conformance
   tests, and migrate one consumer before deleting a duplicate.
3. Keep the dependency direction `Studio -> Core`; Core never imports Studio packages or
   authoring policy.
4. Publish Core before starting the Studio migration. Use `feat/*` for the Core capability and
   `refactor/*` for the consumer migration.
