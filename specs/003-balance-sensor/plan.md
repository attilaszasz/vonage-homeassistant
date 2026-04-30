# Implementation Plan: Vonage Account Balance Sensor

**Branch**: `003-balance-sensor` | **Date**: 2026-04-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-balance-sensor/spec.md`

## Summary

Add a Home Assistant `sensor` platform to the Vonage custom component that exposes the Vonage account balance as `sensor.vonage_account_balance` (per config entry, with HA-suffixed IDs for additional entries). Polling is handled by a new `VonageBalanceCoordinator` (subclass of `DataUpdateCoordinator`) running on a fixed 15-minute interval. The coordinator delegates to a new `async_get_balance()` method on the existing `VonageApiClient`, which wraps the Vonage SDK's `client.account.get_balance()` call (already used today for credential testing) and normalizes its result into a typed dataclass. HTTP 401 raises `ConfigEntryAuthFailed`; all other failures raise `UpdateFailed` and surface as sensor unavailability with auto-recovery on the next successful poll. Initial-setup failures use `ConfigEntryNotReady` (or `ConfigEntryAuthFailed` for 401), consistent with the existing `__init__.py` pattern. No live API calls in tests; all SDK interactions are mocked.

## Technical Context

**Language/Version**: Python 3.12 (matches CI; `manifest.json` requires `homeassistant` constraint)
**Primary Dependencies**: `homeassistant` (core), `vonage>=3.0.0` (already declared in `manifest.json`)
**Storage**: Home Assistant `ConfigEntry` (existing credentials); HA recorder persists sensor state by default
**Testing**: `pytest`, `pytest-asyncio`, `pytest-homeassistant-custom-component`, `unittest.mock` for SDK mocking
**Target Platform**: Home Assistant (custom component, HACS-distributed)
**Project Type**: Single project — Home Assistant custom component (`custom_components/vonage/`)
**Performance Goals**: One Vonage API call per 15 minutes per config entry; polling MUST not block the event loop (executor offload, as already done in `api.py`)
**Constraints**: No live API calls in tests; no API secret in logs; entity must be HACS-compliant; `hassfest`/`hacs/action`/`ruff`/`mypy` must pass
**Scale/Scope**: Small — one new entity platform (`sensor.py`), one new coordinator (`coordinator.py`), one new API method (`async_get_balance`), associated tests and translations

## Constitution Check

Constitution v1.0.0 — `.specify/memory/constitution.md`.

| Principle | Compliance | Notes |
|---|---|---|
| I. HA Architecture Compliance | PASS | New `sensor.py` platform forwarded via `async_forward_entry_setups`; `DataUpdateCoordinator` for polling; user-facing strings added to `strings.json` and `translations/en.json`; config flow unchanged (no new config). |
| II. HACS Distribution Requirements | PASS | No `manifest.json` schema change required (no new dependency; `vonage` already declared). Version bump (e.g., to `1.1.0`) will accompany the release tag, handled by the release workflow — not part of this plan's source diff. README will be updated to list the new sensor. |
| III. Vonage API Encapsulation | PASS | New `async_get_balance()` on `VonageApiClient` wraps the SDK call. Coordinator and sensor entity import only from `api.py` and `coordinator.py`; never from `vonage` directly. |
| IV. Entity & Service Design | PASS | Entity ID `sensor.vonage_account_balance` follows `<platform>.vonage_<descriptive_name>`; per-entry `unique_id` derived from `config_entry.entry_id`; minimal attributes (`auto_reload`, `last_updated`); device info groups the entity under a logical Vonage device. |
| V. Test-First & CI Quality Gates | PASS | New tests added in `tests/test_api.py` (wrapper) and `tests/test_balance_sensor.py` (entity + coordinator). All scenarios use mocks; CI checks (`ruff`, `mypy`, `hassfest`, `hacs/action`, `pytest --cov`) remain authoritative. |

**Result**: PASS — no violations. Complexity Tracking section is N/A.

## Project Structure

### Documentation (this feature)

```text
specs/003-balance-sensor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── balance-api.md   # Internal API contract for VonageApiClient.async_get_balance
├── checklists/
│   └── requirements.md  # Spec quality checklist (existing)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
custom_components/vonage/
├── __init__.py            # Modified: instantiate VonageBalanceCoordinator; store under hass.data[DOMAIN][entry_id]; add Platform.SENSOR
├── api.py                 # Modified: add AccountBalance dataclass + async_get_balance()
├── coordinator.py         # NEW: VonageBalanceCoordinator(DataUpdateCoordinator[AccountBalance])
├── sensor.py              # NEW: VonageAccountBalanceSensor(CoordinatorEntity, SensorEntity)
├── const.py               # Modified: add SCAN_INTERVAL_BALANCE, ATTR_AUTO_RELOAD, ATTR_LAST_UPDATED
├── strings.json           # Modified: add sensor.vonage_account_balance friendly name
├── translations/en.json   # Modified: matching translation
├── config_flow.py         # Unchanged
├── notify.py              # Unchanged
├── services.py            # Unchanged
└── manifest.json          # Unchanged in this feature (version bump deferred to release)

tests/
├── test_api.py            # Modified: add tests for async_get_balance (success, 401, transient, malformed)
├── test_coordinator.py    # NEW: tests for VonageBalanceCoordinator (refresh, auth-failed, update-failed, recovery)
├── test_balance_sensor.py # NEW: tests for sensor entity (state, unit, device_class, attributes, availability, multi-entry)
├── test_integration.py    # Modified (if needed): cover Platform.SENSOR setup path
└── conftest.py            # Modified (if needed): add balance-payload fixtures
```

**Structure Decision**: Single-project HA custom component. Source under `custom_components/vonage/`, tests under `tests/`. The `coordinator.py` module is new but conventional for HA integrations and explicitly required by Constitution Principle I.

## Complexity Tracking

N/A — no Constitution violations to justify.
