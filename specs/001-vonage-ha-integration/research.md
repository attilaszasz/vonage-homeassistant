# Research: Vonage Home Assistant Integration

**Feature**: 001-vonage-ha-integration  
**Date**: 2026-02-01  
**Purpose**: Resolve technical unknowns before design phase

## 1. Vonage Python SDK for SMS

**Decision**: Use official `vonage` Python SDK (PyPI package `vonage`)

**Rationale**:
- Official SDK maintained by Vonage, handles authentication automatically
- SMS API uses simple API key + secret (Basic auth)
- SDK provides `vonage.Sms.send_message()` for outbound SMS
- Returns message ID, status, and error codes for proper error handling

**Alternatives Considered**:
- Raw HTTP requests via `aiohttp` — rejected because SDK handles auth, retries, and response parsing
- `vonage-python-sdk` (legacy) — rejected in favor of newer `vonage` package

**Code Pattern**:
```python
from vonage import Vonage, Auth
auth = Auth(api_key="KEY", api_secret="SECRET")
client = Vonage(auth=auth)
response = client.sms.send({"from": "14155550100", "to": "14155550101", "text": "Hello"})
```

---

## 2. Vonage Voice API for TTS Calls

**Decision**: Use `vonage` SDK with Application ID + private key (JWT auth)

**Rationale**:
- Voice API requires JWT authentication (different from SMS)
- SDK generates JWT from Application ID and private key content
- Uses NCCO (Nexmo Call Control Object) to define call flow
- TTS action in NCCO specifies text, language, and voice style

**Alternatives Considered**:
- Separate HTTP client with manual JWT generation — rejected because SDK handles JWT signing

**Code Pattern**:
```python
from vonage import Vonage, Auth
auth = Auth(application_id="APP_ID", private_key="-----BEGIN PRIVATE KEY-----\n...")
client = Vonage(auth=auth)
ncco = [{"action": "talk", "text": "Hello from Home Assistant", "language": "en-US", "style": 0}]
response = client.voice.create_call({
    "to": [{"type": "phone", "number": "14155550101"}],
    "from": {"type": "phone", "number": "14155550100"},
    "ncco": ncco
})
```

**Supported Languages/Voices**:
- Vonage supports 40+ languages with multiple voice styles (0-5)
- Common: `en-US`, `en-GB`, `es-ES`, `fr-FR`, `de-DE`, `it-IT`
- Style 0 = default female, Style 1 = male variant (varies by language)

---

## 3. Home Assistant Config Flow Best Practices

**Decision**: Multi-step config flow with credential validation

**Rationale**:
- HA 2024.1.0+ uses `ConfigFlow` with `async_step_user` entry point
- Credentials validated before `async_create_entry()` to prevent silent failures
- Optional fields (Voice API) handled with separate optional step or conditional display
- Private key pasted as multi-line text field (`vol.Optional` with `cv.string`)

**Pattern**:
```python
class VonageConfigFlow(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Validate SMS credentials
            if not await self._test_sms_credentials(user_input):
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(title="Vonage", data=user_input)
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)
```

---

## 4. Home Assistant Notification Platform

**Decision**: Implement `notify` platform with `BaseNotificationService`

**Rationale**:
- Standard HA pattern for SMS/messaging integrations
- Creates `notify.vonage_sms` service automatically
- Service data includes `target` (phone number) and `message` (text)
- Supports multiple targets in single call

**Pattern**:
```python
from homeassistant.components.notify import BaseNotificationService

class VonageSmsNotificationService(BaseNotificationService):
    async def async_send_message(self, message: str, **kwargs) -> None:
        targets = kwargs.get(ATTR_TARGET, [])
        for target in targets:
            await self.api.send_sms(target, message)
```

---

## 5. Home Assistant Custom Service Registration

**Decision**: Register `vonage.make_call` via `hass.services.async_register`

**Rationale**:
- Custom services use `vol` schema for typed parameters
- Service registered in `async_setup_entry` or dedicated `services.py`
- Service appears in Developer Tools → Services with auto-generated UI

**Schema Pattern**:
```python
MAKE_CALL_SCHEMA = vol.Schema({
    vol.Required("target"): cv.string,  # Phone number E.164
    vol.Required("message"): cv.string,  # TTS text
    vol.Optional("language", default="en-US"): cv.string,
    vol.Optional("style", default=0): vol.Coerce(int),
})
```

---

## 6. HACS Integration Requirements

**Decision**: Minimal `hacs.json` + complete `manifest.json`

**Rationale**:
- `hacs.json` only needs `name`, `homeassistant` constraint, `render_readme`
- `manifest.json` is the primary metadata source for HA
- Version in `manifest.json` must match Git tag for HACS updates

**hacs.json**:
```json
{
  "name": "Vonage",
  "homeassistant": "2024.1.0",
  "render_readme": true
}
```

**manifest.json**:
```json
{
  "domain": "vonage",
  "name": "Vonage",
  "version": "1.0.0",
  "documentation": "https://github.com/user/vonage-homeassistant",
  "dependencies": [],
  "codeowners": ["@username"],
  "requirements": ["vonage==3.0.0"],
  "iot_class": "cloud_push",
  "integration_type": "service"
}
```

---

## 7. Error Handling Strategy

**Decision**: Map Vonage error codes to HA-friendly messages

**Rationale**:
- Vonage returns status codes (0=success, 1=throttled, 2=missing params, etc.)
- Wrap in `HomeAssistantError` for service call failures
- Log with `_LOGGER.error()` for debugging; never log credentials

**Error Mapping**:
| Vonage Status | Meaning | HA Behavior |
|---------------|---------|-------------|
| 0 | Success | Return normally |
| 1 | Throttled | Raise `HomeAssistantError("Rate limit exceeded")` |
| 2 | Missing params | Raise `HomeAssistantError("Invalid request")` |
| 4 | Invalid credentials | Raise `ConfigEntryAuthFailed` → triggers reauth |
| 5 | Internal error | Raise `HomeAssistantError("Vonage service error")` |

---

## Summary

All technical unknowns resolved. No NEEDS CLARIFICATION items remain.

| Topic | Decision |
|-------|----------|
| SMS SDK | `vonage` package with API key/secret auth |
| Voice SDK | `vonage` package with Application ID + private key (JWT) |
| Config Flow | Multi-step with credential validation |
| Notification | `notify` platform via `BaseNotificationService` |
| Custom Service | `vonage.make_call` with `vol` schema |
| HACS | `hacs.json` + `manifest.json` with matching version |
| Errors | Map Vonage codes to `HomeAssistantError` |
