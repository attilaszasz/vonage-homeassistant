# Tasks: Vonage Home Assistant Integration

**Input**: Design documents from `/specs/001-vonage-ha-integration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure per plan: `custom_components/vonage/` and `tests/`
- [x] T002 [P] Create `custom_components/vonage/const.py` with DOMAIN and config key constants from data-model.md
- [x] T003 [P] Create `custom_components/vonage/manifest.json` with domain "vonage", version "1.0.0", requirements ["vonage>=3.0.0"], iot_class "cloud_push", homeassistant "2024.1.0"
- [x] T004 [P] Create `hacs.json` at repo root with name "Vonage", homeassistant "2024.1.0", render_readme true
- [x] T005 [P] Create `requirements.txt` with vonage>=3.0.0
- [x] T006 [P] Create `requirements_test.txt` with pytest, pytest-homeassistant-custom-component, pytest-asyncio, pytest-cov
- [x] T007 Create empty `custom_components/vonage/__init__.py` (will be implemented in Phase 2)

**Checkpoint**: Project structure exists, can be recognized by HACS and hassfest.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Create `tests/conftest.py` with pytest-homeassistant-custom-component fixtures and mock Vonage client
- [x] T009 Create `custom_components/vonage/api.py` with VonageApiClient class skeleton:
  - Constructor takes api_key, api_secret, phone_number, optional application_id, optional private_key
  - Placeholder methods: `async send_sms(to, text)`, `async make_call(to, text, language, style)`
  - Dataclasses: SmsRequest, SmsResponse, VoiceCallRequest, VoiceCallResponse per data-model.md
- [x] T010 Implement VonageApiClient.send_sms() in `custom_components/vonage/api.py`:
  - Use vonage SDK with Auth(api_key, api_secret)
  - Map Vonage status codes to exceptions per research.md error mapping
  - Return SmsResponse with message_id and status
- [x] T011 Implement VonageApiClient.make_call() in `custom_components/vonage/api.py`:
  - Use vonage SDK with Auth(application_id, private_key)
  - Build NCCO with talk action per research.md pattern
  - Handle case where Voice credentials not configured (raise HomeAssistantError)
  - Return VoiceCallResponse with uuid and status
- [x] T012 Create `tests/test_api.py` with unit tests for VonageApiClient:
  - Test send_sms success with mocked SDK response
  - Test send_sms failure with invalid credentials (status 4)
  - Test send_sms failure with rate limit (status 1)
  - Test make_call success with mocked SDK response
  - Test make_call when Voice not configured raises error
- [x] T013 Create `custom_components/vonage/strings.json` with config flow strings:
  - step.user.title, step.user.description
  - step.user.data.api_key, step.user.data.api_secret, step.user.data.phone_number
  - step.user.data.application_id, step.user.data.private_key
  - step.user.data.default_language, step.user.data.default_voice_style
  - error.invalid_auth, error.cannot_connect
- [x] T014 [P] Create `custom_components/vonage/translations/en.json` as copy of strings.json

**Checkpoint**: API wrapper tested and working with mocked responses. Config flow strings ready.

---

## Phase 3: User Story 1 - Send SMS Notification (Priority: P1) 🎯 MVP

**Goal**: Users can configure the integration and send SMS notifications via `notify.vonage_sms`

**Independent Test**: Configure integration with Vonage credentials → call `notify.vonage_sms` → SMS delivered

### Implementation for User Story 1

- [x] T015 [US1] Create `custom_components/vonage/config_flow.py`:
  - VonageConfigFlow class with domain=DOMAIN
  - async_step_user with form for api_key, api_secret, phone_number (required)
  - Optional fields: application_id, private_key, default_language, default_voice_style
  - Validate SMS credentials by calling api.test_credentials() before creating entry
  - Use vol schema with cv.string validators per data-model.md validation rules
- [x] T016 [US1] Add credential validation helper to `custom_components/vonage/api.py`:
  - `async test_sms_credentials(api_key, api_secret) -> bool`
  - Attempt to create Vonage client and make account info request
  - Return True if successful, False if auth fails
- [x] T017 [US1] Create `tests/test_config_flow.py`:
  - Test successful config flow with valid credentials
  - Test config flow shows error with invalid credentials
  - Test config flow creates entry with correct data structure
  - Test optional Voice fields can be omitted
  - Test credentials (api_secret, private_key) are not present in logs
- [x] T018 [US1] Create `custom_components/vonage/notify.py`:
  - VonageSmsNotificationService extending BaseNotificationService
  - async_send_message implementation using self.api.send_sms()
  - Handle errors and raise HomeAssistantError with user-friendly messages
  - async_get_service factory function per HA notify platform pattern
- [x] T019 [US1] Create `tests/test_notify.py`:
  - Test send_message with single target
  - Test send_message with multiple targets
  - Test send_message error handling (invalid number, rate limit)
- [x] T020 [US1] Implement `custom_components/vonage/__init__.py`:
  - async_setup_entry: create VonageApiClient from config entry data
  - Store client in hass.data[DOMAIN][entry.entry_id]
  - Forward entry setup to notify platform
  - async_unload_entry: cleanup hass.data and unload platforms
- [x] T021 [US1] Run all tests and verify SMS flow works end-to-end with mocks

**Checkpoint**: User Story 1 complete. Integration can be configured and SMS can be sent. This is the MVP.

---

## Phase 4: User Story 2 - Make Voice Call with TTS (Priority: P2)

**Goal**: Users can make outbound voice calls that speak a message via `vonage.make_call` service

**Independent Test**: Configure integration with Voice credentials → call `vonage.make_call` → recipient hears TTS message

**Depends on**: Phase 3 complete (config flow and API wrapper exist)

### Implementation for User Story 2

- [x] T022 [US2] Create `custom_components/vonage/services.py`:
  - MAKE_CALL_SCHEMA per contracts/services.md
  - async_handle_make_call service handler
  - Get default language/style from config entry if not provided in service data
  - Call api.make_call() and handle errors
- [x] T023 [US2] Add Voice credential validation to `custom_components/vonage/api.py`:
  - `async test_voice_credentials(application_id, private_key) -> bool`
  - Attempt to generate JWT — success means credentials valid
- [x] T024 [US2] Update `custom_components/vonage/config_flow.py`:
  - If application_id and private_key provided, validate them before creating entry
  - Show specific error if Voice credentials invalid
- [x] T025 [US2] Register vonage.make_call service in `custom_components/vonage/__init__.py`:
  - Import and call async_setup_services() from services.py in async_setup_entry
  - Unregister service in async_unload_entry
- [x] T026 [US2] Create `tests/test_services.py`:
  - Test make_call service with valid Voice config
  - Test make_call service raises error when Voice not configured
  - Test make_call with language/style override
  - Test make_call error handling (invalid number, rate limit)
- [x] T027 [US2] Update config flow tests for Voice credential validation
- [x] T028 [US2] Run all tests and verify Voice flow works end-to-end with mocks

**Checkpoint**: User Story 2 complete. Voice calls can be made via service. Both user stories functional.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, CI/CD, and HACS compliance

- [ ] T029 [P] Create `README.md` at repo root:
  - Installation via HACS instructions
  - Configuration steps with screenshots placeholder
  - Service documentation for notify.vonage_sms and vonage.make_call
  - Example automations
  - Troubleshooting section
- [ ] T030 [P] Create `.github/workflows/validate.yml`:
  - Run hassfest on custom_components/vonage/
  - Run hacs/action for HACS validation
  - Run ruff check and mypy
  - Run pytest with coverage
- [ ] T031 [P] Create `.github/workflows/release.yml`:
  - Trigger on tag push (v*)
  - Create GitHub release with changelog
- [ ] T032 Add type hints throughout all Python files for mypy strict mode
- [ ] T033 Run ruff check and fix any linting issues
- [ ] T034 Run mypy and fix any type errors
- [ ] T035 Run hassfest validation and fix any manifest issues
- [ ] T036 Run hacs/action validation and fix any HACS compliance issues
- [ ] T037 Update manifest.json version to 1.0.0 and create Git tag v1.0.0

**Checkpoint**: Integration ready for HACS submission. All CI checks pass.

---

## Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundation: API wrapper, tests, strings)
    │
    ├──────────────────────────────┐
    ▼                              ▼
Phase 3 (US1: SMS)            [blocked until US1]
    │                              │
    ▼                              ▼
Phase 4 (US2: Voice)  ◄────────────┘
    │
    ▼
Phase 5 (Polish)
```

## Parallel Execution Opportunities

| Phase | Parallelizable Tasks |
|-------|---------------------|
| Phase 1 | T002, T003, T004, T005, T006 (all can run simultaneously) |
| Phase 2 | T013, T014 (strings files) |
| Phase 5 | T029, T030, T031 (docs and CI can parallelize) |

## Implementation Strategy

1. **MVP First**: Complete Phase 1-3 for functional SMS notifications
2. **Voice Next**: Add Phase 4 for voice call capability
3. **Polish Last**: Phase 5 ensures quality and HACS compliance

**Estimated effort**:
- Phase 1: 30 minutes
- Phase 2: 2 hours
- Phase 3: 3 hours
- Phase 4: 2 hours
- Phase 5: 2 hours
- **Total**: ~9.5 hours

---

## Summary

| Phase | Tasks | User Story | MVP? |
|-------|-------|------------|------|
| 1 | T001-T007 | — | — |
| 2 | T008-T014 | — | — |
| 3 | T015-T021 | US1 (SMS) | ✅ |
| 4 | T022-T028 | US2 (Voice) | — |
| 5 | T029-T037 | — | — |

**Total tasks**: 37  
**Per user story**: US1 = 7 tasks, US2 = 7 tasks  
**Parallel opportunities**: 11 tasks can run in parallel  
**MVP scope**: Phases 1-3 (21 tasks)
