# Service Contracts: DTMF Support for `vonage.make_call`

**Feature**: 002-dtmf-support  
**Date**: 2026-02-21  
**Extends**: [001-vonage-ha-integration/contracts/services.md](../../001-vonage-ha-integration/contracts/services.md)

This document defines the contract changes to the `vonage.make_call` service.

---

## vonage.make_call (Updated)

**Type**: Custom Domain Service  
**Registered By**: `hass.services.async_register()` in `custom_components/vonage/services.py`

### Request Schema (Voluptuous) — Updated

```python
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

MAKE_CALL_SCHEMA = vol.Schema({
    vol.Required("to"): cv.string,
    vol.Optional("text"): cv.string,
    vol.Optional("language"): cv.string,       # Defaults to ConfigEntry value
    vol.Optional("style"): vol.Coerce(int),    # Defaults to ConfigEntry value
    vol.Optional("dtmfAnswer"): cv.string,     # NEW: DTMF digits sent on answer
})
```

### New Field: `dtmfAnswer`

| Property | Value |
|----------|-------|
| **Key** | `dtmfAnswer` |
| **Type** | `string` |
| **Required** | No |
| **Default** | Not included in API payload when absent or empty |
| **Valid characters** | `0-9`, `*`, `#`, `p` (500ms pause) |
| **Max length** | Not enforced (delegated to Vonage API) |
| **Placement in API payload** | `to[0]` phone endpoint object: `{"type": "phone", "number": "...", "dtmfAnswer": "..."}` |
| **Logging** | Redacted in debug logs (`"***"`) per FR-010 |

### Example Service Calls

**With DTMF (new)**:
```yaml
service: vonage.make_call
data:
  to: "+14155550101"
  text: "Gate access granted."
  dtmfAnswer: "p*123#"
```

**Without DTMF (unchanged)**:
```yaml
service: vonage.make_call
data:
  to: "+14155550101"
  text: "Fire alarm triggered. Please check your home immediately."
  language: "en-US"
  style: 1
```

### Response

No change — fire-and-forget. Call UUID logged for debugging.

### Error Conditions (additions)

| Condition | Error Type | Message |
|-----------|------------|---------|
| Invalid DTMF characters | `HomeAssistantError` | Vonage API error message (passthrough) |

All existing error conditions from 001 remain unchanged.

---

## services.yaml Changes

New field added to `make_call`:

```yaml
dtmfAnswer:
  name: DTMF Answer
  description: Send DTMF digits when the call is answered (e.g., p*123#)
  required: false
  example: "p*123#"
  selector:
    text:
```

---

## API Method Signatures (Updated)

### `VonageApiClient.make_call()`

```python
async def make_call(
    self, to: str, text: str, language: str = "en-US", style: int = 0,
    dtmf_answer: Optional[str] = None,
) -> VoiceCallResponse:
```

### `VonageApiClient._make_call_sync()`

```python
def _make_call_sync(
    self, to: str, text: str, language: str = "en-US", style: int = 0,
    dtmf_answer: Optional[str] = None,
) -> VoiceCallResponse:
```

### Payload Construction

```python
to_endpoint: dict[str, str] = {"type": "phone", "number": to_number}
if dtmf_answer:
    to_endpoint["dtmfAnswer"] = dtmf_answer

call_data = {
    "to": [to_endpoint],
    "from": {"type": "phone", "number": from_number},
    "ncco": ncco
}
```

### Debug Log Redaction

```python
log_data = dict(call_data)
if "dtmfAnswer" in log_data.get("to", [{}])[0]:
    log_data["to"] = [dict(log_data["to"][0])]
    log_data["to"][0]["dtmfAnswer"] = "***"
_LOGGER.debug("Voice call data: %s", log_data)
```
