# Implementation Plan: Add Optional DTMF Support to `vonage.make_call`

**Branch**: `002-dtmf-support` | **Date**: 2026-02-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-dtmf-support/spec.md`

## Summary

Add an optional `dtmfAnswer` parameter to the `vonage.make_call` service, allowing DTMF digits to be sent automatically when an outbound voice call is answered. The parameter threads through from the HA service schema → service handler → API client → Vonage Voice API `create_call` payload inside the `to[0]` phone endpoint object. No config flow changes. DTMF values are redacted from debug logs.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Home Assistant Core (2024.1+), Vonage Python SDK, voluptuous, homeassistant.helpers.config_validation  
**Storage**: N/A (no persistence changes)  
**Testing**: pytest + pytest-homeassistant-custom-component (mocked HTTP)  
**Target Platform**: Home Assistant (Linux/Docker/HassOS)  
**Project Type**: Single (HA custom component)  
**Performance Goals**: N/A (fire-and-forget service call; no latency/throughput concerns)  
**Constraints**: Vonage API 2 MB item limit (irrelevant at DTMF string scale); no config flow changes  
**Scale/Scope**: 4 source files modified, 2 spec files created/updated, 1 doc file updated; ~30 lines of new code + ~60 lines of new tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. HA Architecture Compliance** | PASS | No new platforms/entities; extends existing service under `vonage` domain with `vol` schema |
| **II. HACS Distribution Requirements** | PASS | README updated with new param; no version bump needed until release; no manifest changes |
| **III. Vonage API Encapsulation** | PASS | `dtmfAnswer` handled entirely in `api.py`; service layer passes value, never imports Vonage SDK directly |
| **IV. Entity & Service Design** | PASS | Optional parameter added to existing `vonage.make_call` with clear typed schema; no entity changes |
| **V. Test-First & CI Quality Gates** | PASS | New unit tests for DTMF present/absent/empty in both `test_api.py` and `test_services.py`; existing tests unmodified |

**Gate Result**: ALL PASS — no violations, no justifications needed.

## Project Structure

### Documentation (this feature)

```text
specs/002-dtmf-support/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── services.md      # Updated service contract for make_call
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (files touched)

```text
custom_components/vonage/
├── api.py               # Add dtmf_answer to VoiceCallRequest, _make_call_sync, make_call
├── services.py          # Add dtmfAnswer to MAKE_CALL_SCHEMA, extract & pass in handler
└── services.yaml        # Add dtmfAnswer field metadata for HA UI

tests/
├── test_api.py          # New tests: make_call with/without dtmf_answer
└── test_services.py     # New tests: service call with/without dtmfAnswer

README.md                # Update Voice Calls section with dtmfAnswer example
```

**Structure Decision**: Existing HA custom component structure. No new files; only modifications to existing source, test, and documentation files.
