# Quickstart: DTMF Support for `vonage.make_call`

**Feature**: 002-dtmf-support  
**Date**: 2026-02-21

---

## What Changed

The `vonage.make_call` service now accepts an optional `dtmfAnswer` parameter. When provided, DTMF digits are automatically sent to the callee when the outbound call is answered — useful for navigating IVR menus, entering gate access codes, or disarming alarm panels.

---

## Quick Usage

### Basic: Bypass an IVR menu

```yaml
service: vonage.make_call
data:
  to: "+14155550101"
  text: "Gate access granted. Welcome home."
  dtmfAnswer: "p*123#"
```

This places a call, waits 500ms (the `p` pause), then sends `*123#` to the callee's phone system when answered.

### Without DTMF (unchanged)

```yaml
service: vonage.make_call
data:
  to: "+14155550101"
  text: "Hello from Home Assistant."
```

Works exactly as before — no DTMF digits sent.

---

## Files Modified

| File | Change |
|------|--------|
| `custom_components/vonage/services.yaml` | Added `dtmfAnswer` field metadata |
| `custom_components/vonage/services.py` | Added `dtmfAnswer` to schema; extract & pass in handler |
| `custom_components/vonage/api.py` | Added `dtmf_answer` to `VoiceCallRequest`, `_make_call_sync`, `make_call`; log redaction |
| `tests/test_api.py` | Tests for make_call with/without `dtmf_answer` |
| `tests/test_services.py` | Tests for service call with/without `dtmfAnswer` |
| `README.md` | Updated Voice Calls section with `dtmfAnswer` example |
| `specs/002-dtmf-support/contracts/services.md` | Updated service contract |

---

## DTMF Character Reference

| Character | Meaning |
|-----------|---------|
| `0-9` | Dial digits |
| `*` | Star key |
| `#` | Hash key |
| `p` | 500ms pause |

Example: `"p*123#"` = pause 500ms, press *, press 1, 2, 3, press #

---

## Key Implementation Detail

`dtmfAnswer` is placed **inside the `to[0]` phone endpoint object** (not at the root of the API payload):

```json
{
  "to": [{"type": "phone", "number": "14155550101", "dtmfAnswer": "p*123#"}],
  "from": {"type": "phone", "number": "14155550100"},
  "ncco": [{"action": "talk", "text": "Gate access granted.", "language": "en-US", "style": 0}]
}
```

This was confirmed via Vonage API documentation research — see [research.md](research.md).
