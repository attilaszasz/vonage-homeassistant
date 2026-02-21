# Tasks: Add Optional DTMF Support to `vonage.make_call`

**Input**: Design documents from `/specs/002-dtmf-support/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/services.md

**Tests**: Included — SC-004 requires new tests covering DTMF present, absent, and empty cases.

**Organization**: Single user story (US1). No setup or foundational phases needed — this extends an existing integration with no new dependencies or infrastructure.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US1]**: User Story 1 — Send DTMF Digits on Call Answer
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 — Send DTMF Digits on Call Answer (Priority: P1) 🎯 MVP

**Goal**: Add an optional `dtmfAnswer` parameter to the `vonage.make_call` service that sends DTMF digits automatically when an outbound call is answered.

**Independent Test**: Call `vonage.make_call` with `dtmfAnswer: "p*123#"` and verify the Vonage API receives the `dtmfAnswer` field in the `to[0]` phone endpoint object. Call without `dtmfAnswer` and verify existing behavior is unchanged.

### Data Model (FR-007)

- [x] T001 [US1] Add `dtmf_answer: Optional[str] = None` field to `VoiceCallRequest` dataclass in `custom_components/vonage/api.py`

### API Layer (FR-002, FR-003, FR-006, FR-010)

- [x] T002 [US1] Update `_make_call_sync()` signature to accept `dtmf_answer: Optional[str] = None` in `custom_components/vonage/api.py`
- [x] T003 [US1] Update `_make_call_sync()` payload construction to conditionally include `dtmfAnswer` in the `to[0]` phone endpoint object when `dtmf_answer` is provided and non-empty in `custom_components/vonage/api.py`
- [x] T004 [US1] Add debug log redaction for `dtmfAnswer` — log `"***"` instead of actual value in `custom_components/vonage/api.py`
- [x] T005 [US1] Update `make_call()` async method signature to accept and pass through `dtmf_answer: Optional[str] = None` in `custom_components/vonage/api.py`

### Service Layer (FR-001, FR-004, FR-005)

- [x] T006 [US1] Add `vol.Optional("dtmfAnswer"): cv.string` to `MAKE_CALL_SCHEMA` in `custom_components/vonage/services.py`
- [x] T007 [US1] Extract `dtmf_answer = call.data.get("dtmfAnswer")` in `async_handle_make_call()` and pass to `api_client.make_call()` in `custom_components/vonage/services.py`
- [x] T008 [P] [US1] Add `dtmfAnswer` field metadata (name, description, selector) to `make_call` service in `custom_components/vonage/services.yaml`
- [x] T008b [P] [US1] Add `dtmfAnswer` field name and description to `services.make_call.fields` in `custom_components/vonage/strings.json` and `custom_components/vonage/translations/en.json` (Constitution I — i18n requirement)

### Tests (SC-004)

- [x] T009 [P] [US1] Add test for `make_call` with `dtmf_answer` — verify `dtmfAnswer` appears in `to[0]` endpoint of `create_call` payload in `tests/test_api.py`
- [x] T010 [P] [US1] Add test for `make_call` without `dtmf_answer` — verify `to[0]` endpoint has no `dtmfAnswer` key in `tests/test_api.py`
- [x] T011 [P] [US1] Add test for `make_call` with empty string `dtmf_answer` — verify `to[0]` endpoint has no `dtmfAnswer` key in `tests/test_api.py`
- [x] T012 [P] [US1] Add test for service call with `dtmfAnswer` — verify it is passed through to `api_client.make_call()` in `tests/test_services.py`
- [x] T013 [P] [US1] Add test for service call without `dtmfAnswer` — verify existing behavior unchanged in `tests/test_services.py`

**Checkpoint**: At this point, the DTMF feature should be fully functional. Run `pytest` to verify all existing and new tests pass.

---

## Phase 2: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and spec updates

- [x] T014 [P] Update Voice Calls section in `README.md` with `dtmfAnswer` parameter description and practical YAML example (e.g., `dtmfAnswer: "p*123#"`)
- [x] T015 [P] Run `ruff check .` and `mypy custom_components/` to verify lint and type-check pass
- [x] T016 Run quickstart.md and contracts validation — manually verify service call examples from `specs/002-dtmf-support/quickstart.md` and schema in `specs/002-dtmf-support/contracts/services.md` match the implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: No dependencies — can start immediately (existing project, no new infra)
- **Phase 2 (Polish)**: Depends on Phase 1 completion

### Within Phase 1

- **T001** (dataclass) → **T002–T005** (API methods depend on dataclass field)
- **T002–T003** (sync method) → **T005** (async method wraps sync)
- **T006–T007** (service schema + handler) depend on **T005** (API signature must exist first)
- **T008** (services.yaml) and **T008b** (strings.json + translations) are independent — can run in parallel with any task
- **T009–T013** (tests) can all run in parallel with each other; depend on **T001–T007** being complete

### Parallel Opportunities

Within Phase 1, after T001–T007 are complete sequentially:
```
Parallel batch 1 (independent files):
  T008: services.yaml metadata
  T008b: strings.json + translations/en.json i18n
  T009: test_api.py — with dtmf
  T010: test_api.py — without dtmf
  T011: test_api.py — empty dtmf
  T012: test_services.py — with dtmf
  T013: test_services.py — without dtmf

Parallel batch 2 (polish):
  T014: README.md
  T015: lint/type-check
```

---

## Implementation Strategy

### MVP (Phase 1 Only)

1. Complete T001–T007 sequentially (data model → API → service)
2. Complete T008–T013 in parallel (yaml + tests)
3. **STOP and VALIDATE**: Run `pytest` — all tests must pass
4. Feature is usable

### Full Delivery

1. Complete Phase 1 (MVP)
2. Complete Phase 2 (documentation + validation)
3. Ready for PR

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 17 |
| **User Story 1 tasks** | 14 |
| **Polish tasks** | 3 |
| **Parallelizable tasks** | 9 (T008–T015 + T008b) |
| **Files modified** | 3 source + 2 i18n + 2 test + 1 doc |
| **New files** | 0 |

---

## Notes

- [P] tasks = different files or independent within same file, no ordering dependencies
- [US1] = maps to User Story 1 (Send DTMF Digits on Call Answer)
- T001–T005 modify the same file (`api.py`) sequentially; ordering matters
- T006–T007 modify the same file (`services.py`) sequentially
- T008 is the only task touching `services.yaml` — fully independent
- All test tasks (T009–T013) can be written after implementation is complete
- Commit after each logical group: dataclass, API methods, service layer, tests, docs
