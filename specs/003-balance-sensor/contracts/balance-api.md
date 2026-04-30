# Internal Contract: `VonageApiClient.async_get_balance`

**Feature**: 003-balance-sensor
**Module**: `custom_components/vonage/api.py`

This is an **internal Python contract**, not a public HTTP/REST contract. The Vonage HTTP/REST surface is consumed via the Vonage SDK and is not redefined here. Per Constitution Principle III, all Vonage SDK calls are isolated to this method.

## Signature

```python
async def async_get_balance(self) -> AccountBalance: ...
```

## Inputs

None beyond instance state. Uses `self.api_key` and `self.api_secret` (already present on `VonageApiClient`). Does not require `application_id` or `private_key` (the balance endpoint is part of the Account API, authenticated with the API key/secret pair).

## Output: `AccountBalance`

```python
@dataclass(frozen=True)
class AccountBalance:
    value: float
    currency: str
    auto_reload: bool | None
    fetched_at: datetime  # tz-aware UTC, set by the wrapper at success time
```

See [data-model.md](../data-model.md) for full field semantics.

## Exceptions

| Raised | Trigger | Caller behavior |
|---|---|---|
| `ConfigEntryAuthFailed` (from `homeassistant.exceptions`) | Vonage SDK indicates HTTP 401 / authentication failure (e.g., `vonage.errors.AuthenticationError`, or any exception with status code 401). | Coordinator re-raises; HA core triggers re-authentication flow. |
| `HomeAssistantError` (or feature-local `VonageBalanceError(HomeAssistantError)`) | Any other failure: timeouts, network errors, 5xx, rate limiting, 4xx ≠ 401, malformed payload (missing `value` or `currency`), SDK import failure. | Coordinator wraps as `UpdateFailed`; sensor becomes unavailable; recovers on next successful poll. |

The wrapper MUST NOT raise bare `Exception` to callers. Anything not classified as auth-failed is normalized to `HomeAssistantError`.

## Side effects

- Logs at `ERROR` level on failure with: HTTP status code (when available), Vonage `request_id` (when available), and the exception class name.
- Logs at `DEBUG` level on success with currency and a redacted/rounded value (never logs the API secret).
- No state mutation on `VonageApiClient`.

## Concurrency model

Implemented as `await asyncio.get_event_loop().run_in_executor(None, self._get_balance_sync)`, matching the existing `send_sms` / `make_call` / `test_sms_credentials` pattern in `api.py`. The wrapper itself is async-safe and safe to call from multiple coroutines, though in practice the coordinator serializes calls.

## Acceptance criteria (mapped to FRs)

| Criterion | Spec FR |
|---|---|
| Returns `AccountBalance` with `value` (float, raw precision) and `currency` (uppercased ISO code) on success | FR-002, FR-003, Clarif. Q3 |
| Returns `auto_reload=None` when upstream omits the field | FR-014 |
| Raises `ConfigEntryAuthFailed` only on HTTP 401 | FR-011, Clarif. Q4 |
| Raises `HomeAssistantError` on any other failure including 4xx ≠ 401, 5xx, timeouts, rate limit, malformed payload | FR-012, Edge Cases |
| Never logs the API secret | FR-013 |
| Logs HTTP status and request id when available | FR-013 |
| Does not block the event loop | FR-008 (coordinator), Constitution I |

## Test contract (mocked)

All scenarios MUST be covered by `tests/test_api.py` with `vonage.Vonage` and `vonage.Auth` patched. No live calls.

| Scenario | SDK behavior | Expected outcome |
|---|---|---|
| Happy path with auto-reload | `client.account.get_balance()` returns object with `value=12.345`, `currency="eur"`, `auto_reload=True` | Returns `AccountBalance(12.345, "EUR", True, fetched_at=<tz-aware utc>)` |
| Happy path without auto-reload | Same as above but no `auto_reload` attribute | Returns `AccountBalance(..., auto_reload=None)` |
| 401 / auth error | SDK raises an authentication error (or `Exception` with status 401) | Raises `ConfigEntryAuthFailed`; log line contains status code; secret absent |
| Generic HTTP error (500/429/timeout) | SDK raises a generic exception | Raises `HomeAssistantError`; log line contains exception class; secret absent |
| Malformed payload | `get_balance()` returns object missing `value` | Raises `HomeAssistantError`; secret absent |
| SDK import failure | `from vonage import Vonage, Auth` raises `ImportError` | Raises `HomeAssistantError("Vonage SDK not installed")` (mirrors existing code path in `_send_sms_sync`) |
