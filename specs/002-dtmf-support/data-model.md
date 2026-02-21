# Data Model: DTMF Support for `vonage.make_call`

**Feature**: 002-dtmf-support  
**Date**: 2026-02-21

---

## Entity Changes

### VoiceCallRequest (dataclass in `api.py`)

Extended with one new optional field. No new entities introduced.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `to` | `str` | *(required)* | E.164 phone number of the recipient |
| `text` | `str` | *(required)* | TTS message to speak during the call |
| `from_number` | `str` | *(required)* | Sender phone number |
| `language` | `str` | `"en-US"` | TTS language code |
| `style` | `int` | `0` | TTS voice style index |
| **`dtmf_answer`** | **`Optional[str]`** | **`None`** | **DTMF digits to send when the callee answers (e.g., `"p*123#"`)** |

**Validation rules**:
- `dtmf_answer` is optional. When `None` or empty string, no `dtmfAnswer` field is included in the API payload.
- Valid characters: `0-9`, `*`, `#`, `p` (500ms pause). Validation is delegated to the Vonage API.
- No maximum length enforced by the integration; the Vonage API enforces its own limits.

**State transitions**: N/A — `VoiceCallRequest` is a value object (fire-and-forget), not a stateful entity.

---

## Service Schema Changes

### MAKE_CALL_SCHEMA (voluptuous schema in `services.py`)

Extended with one new optional key.

| Key | Validator | Required | Description |
|-----|-----------|----------|-------------|
| `to` | `cv.string` | Yes | Target phone number |
| `text` | `cv.string` | No | TTS message (default: "Hello from Home Assistant") |
| `language` | `cv.string` | No | TTS language override |
| `style` | `vol.Coerce(int)` | No | TTS voice style override |
| **`dtmfAnswer`** | **`cv.string`** | **No** | **DTMF digits to send on answer** |

**Note**: The service schema key is `dtmfAnswer` (camelCase) to match the Vonage API field name. The Python dataclass field is `dtmf_answer` (snake_case) per Python convention.

---

## API Payload Changes

### `create_call` request body (`_make_call_sync` in `api.py`)

The `dtmfAnswer` field is conditionally inserted into the `to[0]` phone endpoint object.

**Without DTMF** (existing behavior, unchanged):
```json
{
  "to": [{"type": "phone", "number": "14155550101"}],
  "from": {"type": "phone", "number": "14155550100"},
  "ncco": [{"action": "talk", "text": "Hello", "language": "en-US", "style": 0}]
}
```

**With DTMF** (new behavior):
```json
{
  "to": [{"type": "phone", "number": "14155550101", "dtmfAnswer": "p*123#"}],
  "from": {"type": "phone", "number": "14155550100"},
  "ncco": [{"action": "talk", "text": "Hello", "language": "en-US", "style": 0}]
}
```

---

## Relationships

No new entity relationships. The `dtmf_answer` field is carried through:

```
ServiceCall.data["dtmfAnswer"] → async_handle_make_call() → api_client.make_call(dtmf_answer=...) → _make_call_sync() → call_data["to"][0]["dtmfAnswer"]
```
