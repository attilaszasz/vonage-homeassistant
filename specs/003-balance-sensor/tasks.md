---
description: "Task list for feature 003-balance-sensor (Vonage Account Balance Sensor)"
---

# Tasks: Vonage Account Balance Sensor

**Input**: Design documents from `/specs/003-balance-sensor/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/balance-api.md](contracts/balance-api.md), [quickstart.md](quickstart.md)

**Tests**: Included — Spec FR-016/FR-017 mandate unit and integration tests; project Constitution (Principle V) gates merges on tests + lint + types.

**Organization**: Tasks grouped by user story per the spec's P1/P2/P3 priorities.

## Path Conventions (this feature)

- Source: `custom_components/vonage/`
- Tests: `tests/`
- Specs/docs: `specs/003-balance-sensor/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Lightweight prep — branch, venv, baseline green.

- [X] T001 Confirm working tree is on branch `003-balance-sensor` and clean; if `.venv` is not active, activate it: `source .venv/bin/activate`.
- [X] T002 Install/refresh dev deps: `pip install -r requirements.txt -r requirements_test.txt` (verifies `pytest-homeassistant-custom-component` is available).
- [X] T003 Run baseline checks to capture pre-change green state: `pytest -q && ruff check custom_components/ tests/ && mypy custom_components/`. Record result in commit message of the first implementation commit.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared building blocks that ALL user stories depend on (constants, dataclass, refactor of `hass.data` shape, sensor platform registration scaffold). No story-specific behavior here.

**CRITICAL**: No US1/US2/US3 tasks may begin until this phase is complete.

- [X] T004 Add balance-related constants to [custom_components/vonage/const.py](custom_components/vonage/const.py): `SCAN_INTERVAL_BALANCE = timedelta(minutes=15)`, `ATTR_AUTO_RELOAD = "auto_reload"`, `ATTR_LAST_UPDATED = "last_updated"`. Add the `from datetime import timedelta` import.
- [X] T005 Add the `AccountBalance` frozen dataclass and a feature-local `VonageBalanceError(HomeAssistantError)` class to [custom_components/vonage/api.py](custom_components/vonage/api.py) per [data-model.md](specs/003-balance-sensor/data-model.md). Fields: `value: float`, `currency: str`, `auto_reload: bool | None`, `fetched_at: datetime`. No method bodies yet beyond the dataclass.
- [X] T006 Create [custom_components/vonage/coordinator.py](custom_components/vonage/coordinator.py) with `VonageBalanceCoordinator(DataUpdateCoordinator[AccountBalance])` skeleton: `__init__(hass, api_client)` storing `self.api_client`, `name="Vonage account balance"`, `update_interval=SCAN_INTERVAL_BALANCE`. `_async_update_data` body is a `raise NotImplementedError` placeholder filled in by US1/US2 tasks.
- [X] T007 Refactor per-entry runtime data shape in [custom_components/vonage/__init__.py](custom_components/vonage/__init__.py): change `hass.data[DOMAIN][entry.entry_id] = api_client` to a `VonageEntryData` TypedDict-style dict `{"api_client": api_client, "balance_coordinator": None}` (coordinator wired in T011). Keep behavior backward-compatible for existing call sites.
- [X] T008 [P] Update [custom_components/vonage/notify.py](custom_components/vonage/notify.py) call site to read `hass.data[DOMAIN][config_entry.entry_id]["api_client"]` instead of the bare client. Verify with a manual grep that no other code path is broken.
- [X] T009 [P] Update [custom_components/vonage/services.py](custom_components/vonage/services.py) any internal references that read `hass.data[DOMAIN][entry_id]` to use the new dict shape (`["api_client"]`).
- [X] T010 Add `Platform.SENSOR` to the `PLATFORMS` list in [custom_components/vonage/__init__.py](custom_components/vonage/__init__.py) so HA forwards setup to the new platform after coordinator first refresh.
- [X] T011 In [custom_components/vonage/__init__.py](custom_components/vonage/__init__.py) `async_setup_entry`, after instantiating `api_client` and BEFORE `async_forward_entry_setups`: instantiate `VonageBalanceCoordinator`, store it in `hass.data[DOMAIN][entry.entry_id]["balance_coordinator"]`, and call `await coordinator.async_config_entry_first_refresh()`. This will raise `ConfigEntryNotReady`/`ConfigEntryAuthFailed` on first-fetch failure per Spec Q5.
- [X] T012 Create empty [custom_components/vonage/sensor.py](custom_components/vonage/sensor.py) with the platform `async_setup_entry(hass, entry, async_add_entities)` function returning no entities yet (so platform forwarding succeeds). Real entity wiring happens in T015.
- [X] T013 Add the user-facing translation key for the new sensor to [custom_components/vonage/strings.json](custom_components/vonage/strings.json) under `entity.sensor.account_balance.name = "Account Balance"` (the device name "Vonage" is prepended automatically by Home Assistant when `_attr_has_entity_name = True`, producing the displayed friendly name "Vonage Account Balance" and the entity ID `sensor.vonage_account_balance` per FR-001). Mirror the change in [custom_components/vonage/translations/en.json](custom_components/vonage/translations/en.json).
- [X] T014 Update [tests/conftest.py](tests/conftest.py) with two reusable fixtures: `mock_balance_response_with_auto_reload` (returns an object with `value=12.345`, `currency="EUR"`, `auto_reload=True`) and `mock_balance_response_no_auto_reload` (no `auto_reload` attribute). These mock the SDK's `client.account.get_balance()` return value.

### Foundational verification (must pass before Phase 3)

- [X] T014a [P] [FOUND] Add `tests/test_integration.py::test_first_setup_failure_raises_config_entry_not_ready` — patch `VonageApiClient.async_get_balance` to raise `HomeAssistantError`/`VonageBalanceError` on first call; assert `async_setup_entry` raises `ConfigEntryNotReady` (Spec Q5) and no sensor entity is created. Verifies T011's first-refresh contract.
- [X] T014b [P] [FOUND] Add `tests/test_integration.py::test_first_setup_401_triggers_reauth` — patch `VonageApiClient.async_get_balance` to raise `ConfigEntryAuthFailed`; assert HA records the entry in re-auth state and no sensor entity is created. Verifies T011's auth-failure path.

**Checkpoint**: Foundation ready — coordinator scaffolded, sensor platform registered (empty), translations added, runtime data shape migrated. User story implementation may now begin.

---

## Phase 3: User Story 1 — Monitor Current Vonage Account Balance (Priority: P1) — MVP

**Goal**: A working `sensor.vonage_account_balance` entity per config entry that polls Vonage every 15 minutes, exposes the numeric balance with the correct currency unit, `monetary` device class, and `total` state class.

**Independent Test**: After config-entry setup with valid mocked credentials, the sensor entity exists with the correct `unique_id`, state, unit of measurement, device_class, state_class, and icon; polling refreshes the value.

### Tests for User Story 1 (write FIRST, ensure they FAIL)

- [X] T015 [P] [US1] Add `tests/test_api.py::test_async_get_balance_success_with_auto_reload` — patches `vonage.Vonage`/`vonage.Auth` so `client.account.get_balance()` returns the fixture; asserts the returned `AccountBalance` has `value=12.345` (raw, no rounding), `currency="EUR"` (uppercased), `auto_reload=True`, and `fetched_at` is tz-aware UTC.
- [X] T016 [P] [US1] Add `tests/test_api.py::test_async_get_balance_success_without_auto_reload` — same setup but using the no-auto-reload fixture; asserts `auto_reload is None`.
- [X] T017 [P] [US1] Create [tests/test_coordinator.py](tests/test_coordinator.py) with `test_balance_coordinator_first_refresh_success` — instantiates `VonageBalanceCoordinator` with a stub `api_client` whose `async_get_balance` returns an `AccountBalance`; calls `await coordinator.async_config_entry_first_refresh()`; asserts `coordinator.last_update_success is True` and `coordinator.data` matches.
- [X] T018 [P] [US1] Create [tests/test_balance_sensor.py](tests/test_balance_sensor.py) with `test_state_unit_device_class` using `pytest-homeassistant-custom-component` `MockConfigEntry` + a patched `VonageApiClient.async_get_balance`; asserts after setup: `state == "12.345"`, `unit_of_measurement == "EUR"`, `device_class == "monetary"`, `state_class == "total"`, `icon == "mdi:cash"`, `unique_id == f"{entry.entry_id}_account_balance"`.
- [X] T019 [P] [US1] Add `tests/test_balance_sensor.py::test_polling_refreshes_state` — advances time by 15 minutes via `async_fire_time_changed`, mutates the mocked `async_get_balance` return value, and asserts the sensor state updates accordingly.
- [X] T020 [P] [US1] Add `tests/test_balance_sensor.py::test_multi_config_entry_unique_ids` — sets up two `MockConfigEntry` instances; asserts both sensors are created with distinct `unique_id`s and that HA assigns suffixed entity IDs (e.g., `_2`) to the second.

### Implementation for User Story 1

- [X] T021 [US1] Implement `VonageApiClient._get_balance_sync` and `async_get_balance` in [custom_components/vonage/api.py](custom_components/vonage/api.py) per [contracts/balance-api.md](specs/003-balance-sensor/contracts/balance-api.md): call `client.account.get_balance()`, coerce `value` to `float`, `currency` to uppercase `str`, read `auto_reload` if present (else `None`), set `fetched_at = dt_util.utcnow()`, return `AccountBalance`. On malformed payload (missing `value` or `currency`) raise `VonageBalanceError`. Use `loop.run_in_executor` like other methods in this file. Do NOT log `self.api_secret`.
- [X] T022 [US1] Implement `VonageBalanceCoordinator._async_update_data` in [custom_components/vonage/coordinator.py](custom_components/vonage/coordinator.py): `await self.api_client.async_get_balance()` and return its result. Auth/transient handling is added in US2 (T028).
- [X] T023 [US1] Implement `VonageAccountBalanceSensor(CoordinatorEntity[VonageBalanceCoordinator], SensorEntity)` in [custom_components/vonage/sensor.py](custom_components/vonage/sensor.py): set `_attr_has_entity_name = True`, `_attr_translation_key = "account_balance"`, `_attr_device_class = SensorDeviceClass.MONETARY`, `_attr_state_class = SensorStateClass.TOTAL`, `_attr_icon = "mdi:cash"`, `_attr_unique_id = f"{config_entry.entry_id}_account_balance"`. Implement `native_value` returning `self.coordinator.data.value` and `native_unit_of_measurement` returning `self.coordinator.data.currency`. Set `device_info` via `DeviceInfo(identifiers={(DOMAIN, config_entry.entry_id)}, name="Vonage", manufacturer="Vonage", entry_type=DeviceEntryType.SERVICE)`.
- [X] T024 [US1] In [custom_components/vonage/sensor.py](custom_components/vonage/sensor.py)'s `async_setup_entry`, fetch the coordinator from `hass.data[DOMAIN][entry.entry_id]["balance_coordinator"]` and call `async_add_entities([VonageAccountBalanceSensor(coordinator, entry)])`.
- [X] T025 [US1] Run the US1 tests (T015–T020) and iterate until green. Confirm no live SDK call occurs by inspecting captured `_LOGGER` records.

**Checkpoint**: User Story 1 (MVP) is complete and independently demonstrable. Sensor reports balance with currency unit and refreshes every 15 minutes.

---

## Phase 4: User Story 2 — Detect and Recover From Backend Failures (Priority: P2)

**Goal**: 401 → re-authentication; transient/5xx/4xx≠401/timeout → sensor unavailable with auto-recovery on next success; logs are diagnostic but never include the API secret.

**Independent Test**: With the entity already set up via US1, simulate each failure mode against the mocked `async_get_balance` and verify behavior: re-auth flow on 401; `available=False` then auto-recovery on transient errors; log records carry status/request id but no secret.

### Tests for User Story 2 (write FIRST, ensure they FAIL)

- [X] T026 [P] [US2] Add `tests/test_api.py::test_async_get_balance_auth_failed` — mock SDK to raise an authentication error (e.g., `vonage.errors.AuthenticationError` or generic `Exception` with status 401); asserts `async_get_balance` raises `ConfigEntryAuthFailed`.
- [X] T027 [P] [US2] Add `tests/test_api.py::test_async_get_balance_transient_error` — mock SDK to raise a generic `Exception` (simulating 5xx/timeout/network); asserts `async_get_balance` raises `HomeAssistantError`/`VonageBalanceError` (NOT `ConfigEntryAuthFailed`).
- [X] T028 [P] [US2] Add `tests/test_api.py::test_async_get_balance_malformed_payload` — mock SDK to return an object missing `value`; asserts `VonageBalanceError` is raised.
- [X] T029 [P] [US2] Add `tests/test_api.py::test_async_get_balance_logging_redacts_secret` — capture `_LOGGER` records under `caplog`; trigger a transient failure; assert the `api_secret` value never appears in any captured log message.
- [X] T030 [P] [US2] Add `tests/test_coordinator.py::test_coordinator_propagates_auth_failed` — stub `api_client.async_get_balance` to raise `ConfigEntryAuthFailed`; assert `coordinator._async_update_data` re-raises it (so HA core triggers re-auth).
- [X] T031 [P] [US2] Add `tests/test_coordinator.py::test_coordinator_wraps_transient_as_update_failed` — stub to raise `HomeAssistantError`; assert `_async_update_data` raises `UpdateFailed` and `coordinator.last_update_success` becomes `False`.
- [X] T032 [P] [US2] Add `tests/test_coordinator.py::test_coordinator_recovery_after_failure` — first call raises, second call succeeds; assert `last_update_success` flips back to `True` and `coordinator.data` is populated.
- [X] T033 [P] [US2] Add `tests/test_balance_sensor.py::test_sensor_unavailable_on_transient_failure` — set up the sensor; force a coordinator refresh that fails; assert `sensor.available is False` and `state == "unavailable"`.
- [X] T034 [P] [US2] Add `tests/test_balance_sensor.py::test_sensor_recovers_on_next_success` — extends the previous test with a subsequent successful refresh; assert sensor returns to available with the new value, no restart needed.

### Implementation for User Story 2

- [X] T037 [US2] Extend `VonageApiClient.async_get_balance` (and its sync counterpart) in [custom_components/vonage/api.py](custom_components/vonage/api.py) to catch authentication errors and re-raise as `ConfigEntryAuthFailed`; map any other exception (including `ImportError` for the SDK) to `VonageBalanceError`. Add diagnostic `_LOGGER.error` lines that include status code and Vonage `request_id` if available, and explicitly never include `self.api_secret` in formatted strings.
- [X] T038 [US2] Update `VonageBalanceCoordinator._async_update_data` in [custom_components/vonage/coordinator.py](custom_components/vonage/coordinator.py) to: re-raise `ConfigEntryAuthFailed` as-is; wrap any other exception in `UpdateFailed(redacted_message)` (do not propagate raw exception args that might contain credentials).
- [X] T039 [US2] Verify [custom_components/vonage/__init__.py](custom_components/vonage/__init__.py) `async_setup_entry` correctly surfaces both `ConfigEntryNotReady` (from `UpdateFailed` via `async_config_entry_first_refresh`) and `ConfigEntryAuthFailed`. No change expected if T011 was implemented correctly; this task is a deliberate review checkpoint.
- [X] T040 [US2] Run all US2 tests (T026–T034). Iterate on log redaction (T029) until the assertion passes. Do not leave any `_LOGGER.debug("...%s", self.api_secret)` style lines anywhere in the new code.

**Checkpoint**: User Story 2 complete. Failure modes behave correctly; no credential leakage; sensor recovers automatically.

---

## Phase 5: User Story 3 — Inspect Balance Context via Attributes (Priority: P3)

**Goal**: Expose `auto_reload` and `last_updated` attributes on the sensor, gracefully handling missing `auto_reload`.

**Independent Test**: With the sensor set up and a successful refresh, inspect `extra_state_attributes` and assert `last_updated` is present (ISO-8601) and `auto_reload` is present iff the upstream payload included it.

### Tests for User Story 3 (write FIRST, ensure they FAIL)

- [X] T041 [P] [US3] Add `tests/test_balance_sensor.py::test_attributes_with_auto_reload` — uses the with-auto-reload fixture; asserts `extra_state_attributes["auto_reload"] is True` and `extra_state_attributes["last_updated"]` parses as a tz-aware ISO-8601 timestamp.
- [X] T042 [P] [US3] Add `tests/test_balance_sensor.py::test_attributes_without_auto_reload` — uses the no-auto-reload fixture; asserts `"auto_reload"` is NOT a key in `extra_state_attributes` (or is `None`) and `last_updated` is still present.

### Implementation for User Story 3

- [X] T043 [US3] Implement `extra_state_attributes` on `VonageAccountBalanceSensor` in [custom_components/vonage/sensor.py](custom_components/vonage/sensor.py): build a dict starting with `{ATTR_LAST_UPDATED: self.coordinator.data.fetched_at.isoformat()}`; include `ATTR_AUTO_RELOAD` only when `self.coordinator.data.auto_reload is not None`.
- [X] T044 [US3] Run T041–T042 and iterate until green.

**Checkpoint**: All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T045 [P] Update [README.md](README.md) "Entities" / features section to list `sensor.vonage_account_balance` with its device_class, state_class, unit (account currency), poll interval (15 min), and attributes.
- [X] T046 [P] Update [CHANGELOG.md](CHANGELOG.md) under an `[Unreleased]` section with a short note: "Added: Vonage account balance sensor (per config entry, 15-min polling, monetary device class)."
- [X] T047 Run `pytest --cov=custom_components/vonage --cov-report=term-missing` and confirm coverage on `api.py` (new code paths), `coordinator.py`, and `sensor.py` meets or exceeds the existing repo standard (Spec SC-006).
- [X] T048 Run `ruff check custom_components/ tests/` and `mypy custom_components/`; fix any new lint/type errors introduced by this feature.
- [X] T049 Walk through [quickstart.md](specs/003-balance-sensor/quickstart.md) §1–§4 end to end (skip §5 manual smoke unless real credentials are available); confirm all acceptance mappings pass.
- [X] T050 Commit and push branch `003-balance-sensor`. Do NOT bump `manifest.json` version — the release workflow handles that on tag.
- [X] T051 Confirm the release process owns `manifest.json` version-bump-and-tag together (Constitution II). Inspect [.github/workflows/release.yml](.github/workflows/release.yml): the workflow already verifies that `manifest.json` matches the tag but does NOT bump it. Add a release-checklist note to the PR description / CHANGELOG that the maintainer must update `manifest.json` (e.g., to `1.1.0`) in the same commit that creates the release tag. No source change required in this feature branch.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1. BLOCKS all user stories. T004–T006 must complete before T011/T012/T014. T007 must complete before T008/T009. T010 must complete before T011. T011 depends on T006 + T007.
- **Phase 3 (US1)**: Depends on Phase 2 complete.
- **Phase 4 (US2)**: Depends on Phase 3 (extends the same `async_get_balance` and coordinator).
- **Phase 5 (US3)**: Depends on Phase 3 (sensor entity must exist). Independent of Phase 4 in principle but conventionally implemented after.
- **Phase 6 (Polish)**: Depends on all desired user stories.

### Within-Story Dependencies

- US1: T015–T020 [P] before T021–T024; T025 last.
- US2: T026–T034 [P] before T037–T039; T040 last.
- US3: T041–T042 [P] before T043; T044 last.

### Parallel Opportunities

- Phase 2: T008 and T009 in parallel after T007.
- US1 tests T015, T016, T017, T018, T019, T020 — all [P], different test functions/files.
- US2 tests T026–T034 — all [P].
- US3 tests T041–T042 — both [P].
- Polish T045–T046 — both [P].

---

## Parallel Example: User Story 1 tests

```text
# All US1 test scaffolds can be drafted in parallel before any US1 implementation:
T015 [P] [US1] tests/test_api.py::test_async_get_balance_success_with_auto_reload
T016 [P] [US1] tests/test_api.py::test_async_get_balance_success_without_auto_reload
T017 [P] [US1] tests/test_coordinator.py::test_balance_coordinator_first_refresh_success
T018 [P] [US1] tests/test_balance_sensor.py::test_state_unit_device_class
T019 [P] [US1] tests/test_balance_sensor.py::test_polling_refreshes_state
T020 [P] [US1] tests/test_balance_sensor.py::test_multi_config_entry_unique_ids
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 (Setup): T001–T003.
2. Phase 2 (Foundational): T004–T014.
3. Phase 3 (US1): T015–T025.
4. **STOP & VALIDATE**: Run quickstart §1–§3, confirm a single Vonage entry produces a working `sensor.vonage_account_balance`. Demoable.

### Incremental Delivery

1. MVP (above) → first deployable slice.
2. US2: T026–T040 → resilient/recoverable behavior, re-auth on 401.
3. US3: T041–T044 → richer attributes for power users.
4. Polish: T045–T050 → docs, coverage, lint, final commit.

---

## Notes

- All Vonage SDK interactions remain inside `api.py` (Constitution Principle III).
- No live API calls in tests (Spec FR-016, Constitution Principle V).
- Per-entry `unique_id` ensures multi-account safety (Spec Q1).
- Fixed 15-minute interval; configurability is deliberately deferred (Spec Q2).
- No rounding of the balance value (Spec Q3).
- Only HTTP 401 triggers re-auth (Spec Q4).
- First-fetch failure raises `ConfigEntryNotReady`/`ConfigEntryAuthFailed` so entities are not created until the first successful poll (Spec Q5).
