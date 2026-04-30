# Data Model: Vonage Account Balance Sensor

**Feature**: 003-balance-sensor
**Date**: 2026-04-30

This integration is stateless beyond Home Assistant's own state machine and recorder. The "data model" therefore captures the in-memory dataclass produced by the API wrapper and consumed by the coordinator and sensor entity, plus the shape of the per-config-entry runtime data dictionary.

## Entity: `AccountBalance`

Defined in `custom_components/vonage/api.py` as a `@dataclass(frozen=True)` (matching the style of existing `SmsRequest`, `VoiceCallResponse`).

| Field | Type | Required | Source | Notes |
|---|---|---|---|---|
| `value` | `float` | Yes | Vonage SDK `BalanceResponse.value` | Numeric balance, raw precision (no rounding — Spec Clarif. Q3). May be `0` or negative (Spec Edge Cases). |
| `currency` | `str` | Yes | Vonage SDK `BalanceResponse.currency` | ISO 4217 currency code, e.g., `"EUR"`. Used as `native_unit_of_measurement`. |
| `auto_reload` | `bool \| None` | No | Vonage SDK `BalanceResponse.auto_reload` | Optional. `None` if upstream omits it (Spec FR-014). |
| `fetched_at` | `datetime` | Yes | `dt_util.utcnow()` at successful fetch | Timezone-aware UTC. Used for the sensor's `last_updated` attribute (Spec FR-015). |

### Validation rules

- A response missing `value` OR `currency` is invalid → wrapper raises `VonageBalanceError` (mapped by coordinator to `UpdateFailed`). See Spec Edge Cases ("Partial payload").
- `value` MUST be coerced to `float` (the SDK may return `Decimal` or string-typed JSON in some versions); `currency` MUST be coerced to `str` and uppercased.
- `auto_reload` is coerced to `bool` only when the upstream attribute is present and not `None`; otherwise stored as `None`.

### State transitions

`AccountBalance` itself is immutable. Lifecycle is managed by the coordinator:

```
[no data] --first refresh success--> [AccountBalance(t0)]
[AccountBalance(tn)] --refresh success--> [AccountBalance(tn+1)]   # value/currency may change
[AccountBalance(tn)] --refresh failure (non-401)--> [AccountBalance(tn) retained, last_update_success=False]
[any]                --refresh failure (401)-----> ConfigEntryAuthFailed propagated; entry enters re-auth
```

## Per-Entry Runtime Data: `hass.data[DOMAIN][entry_id]`

Migrated from a bare `VonageApiClient` to a typed dict (see research §Decision 7).

```python
class VonageEntryData(TypedDict):
    api_client: VonageApiClient
    balance_coordinator: VonageBalanceCoordinator
```

| Key | Type | Lifecycle |
|---|---|---|
| `api_client` | `VonageApiClient` | Created in `async_setup_entry`; reused across all platforms and services. |
| `balance_coordinator` | `VonageBalanceCoordinator` | Created in `async_setup_entry`, after `api_client`. First refresh is awaited via `async_config_entry_first_refresh()` before `Platform.SENSOR` is forwarded. Disposed implicitly on `async_unload_entry`. |

## Coordinator: `VonageBalanceCoordinator`

A `DataUpdateCoordinator[AccountBalance]` (`coordinator.data` is `AccountBalance` after first success).

| Property | Value |
|---|---|
| `name` | `"Vonage account balance"` |
| `update_interval` | `timedelta(minutes=15)` (constant `SCAN_INTERVAL_BALANCE`) |
| `_async_update_data` | Calls `api_client.async_get_balance()`. Re-raises `ConfigEntryAuthFailed`. Wraps any other exception as `UpdateFailed`. |

## Sensor: `VonageAccountBalanceSensor`

| HA Attribute | Value |
|---|---|
| Platform | `sensor` |
| `_attr_has_entity_name` | `True` |
| `_attr_translation_key` | `"account_balance"` (translation string is `"Account Balance"`; HA prepends device name `"Vonage"` → displayed friendly name `"Vonage Account Balance"`, entity ID `sensor.vonage_account_balance` per Spec FR-001) |
| `_attr_unique_id` | `f"{config_entry.entry_id}_account_balance"` |
| `_attr_device_class` | `SensorDeviceClass.MONETARY` |
| `_attr_state_class` | `SensorStateClass.TOTAL` |
| `_attr_icon` | `"mdi:cash"` |
| `native_value` | `coordinator.data.value` |
| `native_unit_of_measurement` | `coordinator.data.currency` |
| `available` | Inherited from `CoordinatorEntity` (`coordinator.last_update_success` and `coordinator.data is not None`) |
| `extra_state_attributes` | `{"auto_reload": ...?, "last_updated": coordinator.data.fetched_at.isoformat()}` |
| `device_info` | `DeviceInfo(identifiers={(DOMAIN, config_entry.entry_id)}, name="Vonage", manufacturer="Vonage", entry_type=DeviceEntryType.SERVICE)` |

## Constants (added to `const.py`)

| Constant | Value | Use |
|---|---|---|
| `SCAN_INTERVAL_BALANCE` | `timedelta(minutes=15)` | Coordinator `update_interval` |
| `ATTR_AUTO_RELOAD` | `"auto_reload"` | Sensor attribute key |
| `ATTR_LAST_UPDATED` | `"last_updated"` | Sensor attribute key |

## Out of model

- Persistent storage of historical balances (HA recorder handles this).
- User-configurable poll interval (Spec Clarif. Q2 — deferred).
- Low-balance alerting (Spec FR-018).
