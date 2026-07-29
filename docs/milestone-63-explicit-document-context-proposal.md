# Milestone 63 Proposal - Explicit Local Document Context

**Proposal date:** 30 July 2026

**Base release:** 0.59.0

**Status:** Complete on 30 July 2026; implemented, integrated through protected
`main`, installed, and accepted as release 0.63.0

## User outcome

In NOVA Chat, the owner can choose one currently indexed document and ask a
question about it. NOVA uses that document only for the selected turn and
shows the exact local source used.

Example:

1. select `sample-project.txt`;
2. ask, "What delivery date is listed in this document?";
3. receive a local answer with `[D1]`; and
4. open a source card showing the selected filename, title, and verified
   fingerprint evidence.

## In scope

- explicit selection of one ready intake document;
- safe metadata selector in the chat interface;
- current path and SHA-256 verification before use;
- maximum 8,000 UTF-8 bytes of extracted context;
- clear rejection before the turn is stored when validation fails;
- untrusted-reference prompt delimiters and `[D1]` citation instruction;
- persistent citation metadata for completed assistant responses;
- separate display of document and approved-personal-knowledge sources;
- ordered database migration and rollback-safe startup validation;
- backend, frontend, Windows, production, accessibility, privacy, backup, and
  restore verification; and
- owner acceptance on the Windows host.

## Out of scope

- automatic document selection;
- semantic search, embeddings, vector storage, or RAG frameworks;
- multiple documents in one turn;
- chunking or summarizing oversized documents;
- chat uploads;
- arbitrary host-folder browsing;
- indexing filed-library documents or `N:\Nova\Documents`;
- changing, moving, deleting, sharing, or uploading documents;
- web access, plugins, agents, tools, automation, voice, or remote access; and
- external AI or speech providers.

## Safety rules

1. Document selection is explicit and visible before send.
2. The selected source must remain under the configured intake root.
3. The source SHA-256 must still match the indexed record.
4. Only `ready` extracted text within the context limit may be used.
5. Validation happens before the user message is persisted.
6. Document text is untrusted reference data and cannot grant authority.
7. The model receives no file-action, tool, network, or autonomous capability.
8. Citation evidence is bound to the exact verified source fingerprint.
9. Full extracted text never appears in selector or citation API responses.
10. Existing behavior remains unchanged when no document is selected.

## Acceptance criteria

- all Milestone 62 engineering tests pass;
- backend coverage remains at least 90%;
- frontend lint, typing, tests, and production build pass;
- Windows controls and the isolated production workflow pass;
- repository hygiene and secret checks pass;
- API and dashboard remain loopback-only;
- no personal or document content enters Git;
- database and knowledge recovery checkpoints verify before installation;
- the installed version matches the accepted source;
- owner confirms document selection, question answering, citation display,
  failure messaging, and no-selection regression on Windows; and
- architecture and engineering completion reviews find no release blocker.

## Approval record

The owner explicitly approved:

> Milestone 63 - Explicit Local Document Context

That approval authorized only the scope above. It did not authorize semantic
search, broad document memory, voice, remote access, plugins, agents,
automation, or external providers.
