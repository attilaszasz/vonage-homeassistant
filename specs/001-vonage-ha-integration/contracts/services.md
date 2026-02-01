# Service Contracts: Vonage Home Assistant Integration

**Feature**: 001-vonage-ha-integration  
**Date**: 2026-02-01

This document defines the service contracts exposed by the Vonage integration.

---

## notify.vonage_sms

**Type**: Home Assistant Notification Platform  
**Registered By**: `notify` platform in `custom_components/vonage/notify.py`

### Request Schema (Voluptuous)

```python
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

NOTIFY_SCHEMA = vol.Schema({
    vol.Required("message"): cv.string,
    vol.Required("target"): vol.All(cv.ensure_list, [cv.string]),
})
```

### Example Service Call

```yaml
service: notify.vonage_sms
data:
  message: "Motion detected at front door"
  target:
    - "+14155550101"
```

### Response

No response data — fire-and-forget. Errors raised as `HomeAssistantError`.

### Error Conditions

| Condition | Error Type | Message |
|-----------|------------|---------|
| Missing target | `vol.Invalid` | "required key not provided" |
| Invalid phone format | `HomeAssistantError` | "Invalid phone number format" |
| Vonage auth failed | `ConfigEntryAuthFailed` | "Invalid Vonage credentials" |
| Vonage rate limit | `HomeAssistantError` | "Vonage rate limit exceeded" |
| Vonage internal error | `HomeAssistantError` | "Vonage service unavailable" |

---

## vonage.make_call

**Type**: Custom Domain Service  
**Registered By**: `hass.services.async_register()` in `custom_components/vonage/services.py`

### Request Schema (Voluptuous)

```python
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

MAKE_CALL_SCHEMA = vol.Schema({
    vol.Required("target"): cv.string,
    vol.Required("message"): cv.string,
    vol.Optional("language"): cv.string,  # Defaults to ConfigEntry value
    vol.Optional("style"): vol.Coerce(int),  # Defaults to ConfigEntry value
})
```

### Example Service Call

```yaml
service: vonage.make_call
data:
  target: "+14155550101"
  message: "Fire alarm triggered. Please check your home immediately."
  language: "en-US"
  style: 1
```

### Response

No response data — fire-and-forget. Call UUID logged for debugging.

### Error Conditions

| Condition | Error Type | Message |
|-----------|------------|---------|
| Voice not configured | `HomeAssistantError` | "Voice API not configured" |
| Missing target | `vol.Invalid` | "required key not provided" |
| Invalid phone format | `HomeAssistantError` | "Invalid phone number format" |
| Vonage auth failed | `ConfigEntryAuthFailed` | "Invalid Vonage credentials" |
| Vonage rate limit | `HomeAssistantError` | "Vonage rate limit exceeded" |
| Invalid language | `HomeAssistantError` | "Unsupported language code" |

---

## Supported Voice Languages

Subset of Vonage-supported languages for the `language` parameter:

| Code | Language |
|------|----------|
| `en-US` | English (US) |
| `en-GB` | English (UK) |
| `en-AU` | English (Australia) |
| `es-ES` | Spanish (Spain) |
| `es-MX` | Spanish (Mexico) |
| `fr-FR` | French (France) |
| `de-DE` | German |
| `it-IT` | Italian |
| `pt-BR` | Portuguese (Brazil) |
| `nl-NL` | Dutch |
| `pl-PL` | Polish |
| `ru-RU` | Russian |
| `ja-JP` | Japanese |
| `ko-KR` | Korean |
| `zh-CN` | Chinese (Mandarin) |

Full list: [Vonage TTS Languages](https://developer.vonage.com/en/voice/voice-api/concepts/text-to-speech#supported-languages)

---

## Config Flow Validation Endpoint (Internal)

Used during config flow to validate credentials before saving.

### SMS Validation

```python
async def validate_sms_credentials(api_key: str, api_secret: str) -> bool:
    """Return True if credentials are valid, False otherwise."""
    # Calls Vonage Account API to verify credentials
```

### Voice Validation

```python
async def validate_voice_credentials(app_id: str, private_key: str) -> bool:
    """Return True if Voice API credentials are valid, False otherwise."""
    # Attempts to generate JWT — if successful, credentials are valid
```
