# Milestone 38: Representative runtime acceptance

## Outcome

Nova 0.38.0 closes the final evidence gap identified by the Intake MVP
architecture review. The production-container workflow now verifies the guarded
pipeline with representative TXT, Markdown, DOCX, PDF, and image inputs rather
than relying on one text fixture.

## Isolated fixtures

The workflow creates deterministic synthetic documents containing unique search
references. It renders the image fixture with the Poppler tool already included
in Nova's backend image, then lets the running application process it with real
local Tesseract OCR.

No user document, live database, backup, secret, or persistent Docker volume is
available to this check.

## Acceptance evidence

The production workflow now proves:

- UTF-8 text and Markdown understanding;
- direct DOCX XML extraction;
- direct PDF text-layer extraction;
- real image OCR through the production Tesseract binary;
- filename, extracted-text, evidence-text, and metadata/status search;
- stable unfiltered summary counts;
- deterministic recommendations across representative formats;
- three confirmed moves activating a learned destination;
- undo invalidating that evidence and refreshing the pending recommendation;
- approval, separate execution, append-only audit, guarded undo, verified
  backup, guarded restore, and post-restore health.

## Safety boundary

The acceptance workflow remains disposable and local to GitHub Actions.
Learning changes only a recommendation. Every move still requires explicit
approval and a separate execution request. Automatic filing, chatbot behavior,
semantic retrieval, external AI providers, and user data are not introduced.
