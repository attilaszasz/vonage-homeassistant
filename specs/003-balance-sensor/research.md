# Phase 0 Research: Vonage Account Balance Sensor

**Feature**: 003-balance-sensor
**Date**: 2026-04-30

All `NEEDS CLARIFICATION` items in Technical Context are resolved (clarifications already captured in [spec.md](spec.md) §Clarifications). This document records decisions for the remaining design choices that drive Phase 1 artifacts.

---

## Decision 1: Vonage SDK call for balance retrieval

- **Decision**: Use `vonage.Vonage(auth=Auth(api_key, api_secret)).account.get_balance()` (synchronous SDK call, offloaded to the executor) inside `VonageApiClient.async_get_balance()`.
- **Rationale**:
  - The SDK call is already used in `_test_sms_credentials_sync` (api.py:255), proving credentials and connectivity. Reusing it keeps a single dependency surface.
  - The Vonage Python SDK v3 is synchronous; offloading via `loop.run_in_executor(None, ...)` matches the pattern already used for `send_sms`, `make_call`, and `test_sms_credentials`.
  - No new dependency, no `manifest.json` change, no new HACS validation risk.
- **Alternatives considered**:
  - Direct HTTP GET to `https://rest.nexmo.com/account/get-balance` with `aiohttp`: removes the SDK from the call path but introduces parallel auth handling, error mapping, and an extra dependency on the HA-managed `aiohttp` session. Rejected — duplication outweighs benefit.
  - Switching the entire integration to async HTTP: out of scope; would touch every method in `api.py`. Rejected.

## Decision 2: Mapping SDK responses and exceptions to outcomes

- **Decision**:
  - Success → return `AccountBalance(value: float, currency: str, auto_reload: bool | None)`.
  - SDK raises `AuthenticationError` (or any exception whose status is 401) → wrapper raises `ConfigEntryAuthFailed`.
  - SDK raises any other exception (network, 4xx ≠ 401, 5xx, rate limit) OR returns a payload missing `value`/`autoReload` shape with a usable currency → wrapper raises `HomeAssistantError` (or a feature-local `VonageBalanceError`) and the coordinator translates that to `UpdateFailed`.
  - Logging at `ERROR` level on failure includes: HTTP status (when available), Vonage `request_id` (when available), exception class. Logging MUST NOT include `api_secret`.
- **Rationale**:
  - Aligns with FR-011, FR-012, FR-013, and Spec §Clarifications Q4 (401-only re-auth).
  - Centralizes status-to-HA-exception mapping in the wrapper, so the coordinator only handles two outcomes (success / `UpdateFailed`).
- **Alternatives considered**:
  - Map 403 to `ConfigEntryAuthFailed` too: explicitly rejected by Q4.
  - Inspect Vonage error-body codes for finer mapping: rejected for MVP — increases complexity without changing user-visible behavior under current scope.

## Decision 3: Coordinator design (`VonageBalanceCoordinator`)

- **Decision**:
  - New module `custom_components/vonage/coordinator.py` defining `VonageBalanceCoordinator(DataUpdateCoordinator[AccountBalance])`.
  - `update_interval = timedelta(minutes=15)` (constant `SCAN_INTERVAL_BALANCE` in `const.py`).
  - `_async_update_data()` calls `self.api_client.async_get_balance()`. On `ConfigEntryAuthFailed` it re-raises (HA core handles re-auth). On any other exception it raises `UpdateFailed(...)` with a redacted message.
  - One coordinator instance per config entry, stored alongside the existing `api_client` under `hass.data[DOMAIN][entry_id]` as a small dict (e.g., `{"api_client": ..., "balance_coordinator": ...}`).
- **Rationale**:
  - Standard HA pattern (Constitution Principle I). One coordinator per entry preserves multi-entry behavior (Spec §Clarifications Q1).
  - Shared `hass.data` shape change is additive and backward-compatible if we read with `.get(...)`.
- **Alternatives considered**:
  - Reuse a single global coordinator: incompatible with multi-entry. Rejected.
  - Make the `VonageApiClient` itself a coordinator: violates HA's separation of concerns and Constitution Principle III. Rejected.

## Decision 4: Sensor entity design

- **Decision**:
  - `VonageAccountBalanceSensor(CoordinatorEntity[VonageBalanceCoordinator], SensorEntity)` in `custom_components/vonage/sensor.py`.
  - `_attr_has_entity_name = True`, `_attr_translation_key = "account_balance"`, default name "Vonage Account Balance".
  - `_attr_device_class = SensorDeviceClass.MONETARY`, `_attr_state_class = SensorStateClass.TOTAL`, `_attr_icon = "mdi:cash"`.
  - `_attr_unique_id = f"{config_entry.entry_id}_account_balance"`.
  - `native_value` returns `self.coordinator.data.value` (float, raw precision).
  - `native_unit_of_measurement` returns `self.coordinator.data.currency`.
  - `available` returns `self.coordinator.last_update_success and self.coordinator.data is not None` (CoordinatorEntity default already covers this).
  - `extra_state_attributes` returns `{ "auto_reload": ..., "last_updated": <ISO-8601 of coordinator.last_update_success_time> }`, omitting `auto_reload` when `None`.
  - `device_info` returns a `DeviceInfo` keyed by `(DOMAIN, config_entry.entry_id)` with name "Vonage" so multi-entry users can tell devices apart.
- **Rationale**: Matches FR-001 through FR-005, FR-014, FR-015, and Q1 (per-entry uniqueness via `unique_id`).
- **Alternatives considered**:
  - Hardcoding the entity ID: would collide on second config entry. Rejected by Q1.
  - Putting balance value into attributes and currency into state: violates HA conventions for `SensorDeviceClass.MONETARY`. Rejected.

## Decision 5: Initial-setup failure handling

- **Decision**: In `__init__.py async_setup_entry`, after instantiating the coordinator, call `await coordinator.async_config_entry_first_refresh()`. This helper raises `ConfigEntryNotReady` automatically on `UpdateFailed` and propagates `ConfigEntryAuthFailed`. Sensor platform is forwarded only after this returns.
- **Rationale**: Spec §Clarifications Q5; matches existing `__init__.py` pattern and standard HA convention for first-refresh-required coordinators.
- **Alternatives considered**:
  - Forward platform first, handle setup failure in entity: leaks transient failures into the entity registry. Rejected by Q5.

## Decision 6: Test strategy

- **Decision**:
  - **Unit tests for `async_get_balance`** (`tests/test_api.py`): patch `vonage.Vonage` / `vonage.Auth`; cover (a) happy path returns `AccountBalance` with `auto_reload`, (b) happy path payload missing `auto_reload`, (c) SDK raises authentication error → `ConfigEntryAuthFailed`, (d) SDK raises generic error → `HomeAssistantError` / `VonageBalanceError`, (e) SDK returns malformed payload (missing `value` or `currency`) → raises, (f) credentials never appear in captured log records.
  - **Coordinator tests** (`tests/test_coordinator.py`): patch `VonageApiClient.async_get_balance` to (a) return success → `coordinator.data` populated and `last_update_success` True, (b) raise `ConfigEntryAuthFailed` → propagated, (c) raise `HomeAssistantError` → `UpdateFailed` → `last_update_success` False, (d) recovery cycle (fail then succeed) → success again.
  - **Sensor entity tests** (`tests/test_balance_sensor.py`): use `pytest-homeassistant-custom-component` `MockConfigEntry` + `setup_component`; verify entity registry entry, state, unit, device class, state class, icon, attributes including `last_updated`, availability transitions, and multi-config-entry suffixing.
- **Rationale**: Mirrors existing `tests/test_api.py` mocking pattern; satisfies FR-016 and FR-017 with no live calls (Constitution Principle V).
- **Alternatives considered**: VCR-style cassettes for replaying real responses — overkill for one endpoint. Rejected.

## Decision 7: Backward compatibility of `hass.data[DOMAIN][entry_id]`

- **Decision**: Migrate the per-entry value from `VonageApiClient` directly to a small typed dict `{"api_client": VonageApiClient, "balance_coordinator": VonageBalanceCoordinator}`. Update `notify.py` and `services.py` to read `hass.data[DOMAIN][entry_id]["api_client"]` (with a fallback to the legacy shape only if needed during the same release cycle).
- **Rationale**: Adds clarity for the new coordinator without introducing parallel data structures. All call sites are inside this repository (verified via grep), so the migration is a controlled refactor.
- **Alternatives considered**:
  - Keep `api_client` as the stored value and attach the coordinator as an attribute on the client: blurs separation of concerns (Principle III). Rejected.
  - Store coordinator in a parallel key (`hass.data[f"{DOMAIN}_balance_coordinator"]`): non-standard; harder to reason about during unload. Rejected.

---

## Open items

None. All NEEDS CLARIFICATION resolved via spec clarifications and the decisions above.
