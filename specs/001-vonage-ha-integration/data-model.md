# Data Model: Vonage Home Assistant Integration

**Feature**: 001-vonage-ha-integration  
**Date**: 2026-02-01  
**Input**: [spec.md](spec.md), [research.md](research.md)

## Entities Overview

This integration does not create persistent entities with state. It provides:
- **ConfigEntry**: Stores credentials and preferences
- **Services**: Stateless actions (send SMS, make call)

---

## ConfigEntry Data Schema

Stored in Home Assistant's `.storage/core.config_entries` (encrypted).

```python
# custom_components/vonage/const.py

DOMAIN = "vonage"

# Config keys (required for SMS)
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"
CONF_PHONE_NUMBER = "phone_number"  # Sender ID (E.164 format)

# Config keys (optional, enables Voice)
CONF_APPLICATION_ID = "application_id"
CONF_PRIVATE_KEY = "private_key"  # PEM content, not file path

# Config keys (Voice preferences)
CONF_DEFAULT_LANGUAGE = "default_language"  # e.g., "en-US"
CONF_DEFAULT_VOICE_STYLE = "default_voice_style"  # 0-5
```

### ConfigEntry.data Structure

```json
{
  "api_key": "abc12345",
  "api_secret": "xyz98765secret",
  "phone_number": "+14155550100",
  "application_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEv...",
  "default_language": "en-US",
  "default_voice_style": 0
}
```

### Validation Rules

| Field | Required | Format | Validation |
|-------|----------|--------|------------|
| `api_key` | Yes | 8 chars | Alphanumeric |
| `api_secret` | Yes | 16+ chars | Alphanumeric |
| `phone_number` | Yes | E.164 | Starts with `+`, 7-15 digits |
| `application_id` | No | UUID | 36 chars with hyphens |
| `private_key` | No | PEM | Contains `-----BEGIN` header |
| `default_language` | No | BCP 47 | Matches Vonage-supported list |
| `default_voice_style` | No | Integer | 0-5 |

---

## Service Schemas

### notify.vonage_sms

Standard Home Assistant notification service.

```yaml
service: notify.vonage_sms
data:
  message: "Alert: Motion detected at front door"
  target:
    - "+14155550101"
    - "+14155550102"
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | SMS text (max 1600 chars, auto-split) |
| `target` | list[string] | Yes | Phone numbers in E.164 format |

---

### vonage.make_call

Custom service for outbound voice calls with TTS.

```yaml
service: vonage.make_call
data:
  target: "+14155550101"
  message: "Fire alarm triggered. Please check your home."
  language: "en-US"
  style: 1
```

**Fields**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `target` | string | Yes | — | Phone number in E.164 format |
| `message` | string | Yes | — | Text to speak via TTS |
| `language` | string | No | ConfigEntry default | BCP 47 language code |
| `style` | integer | No | ConfigEntry default | Voice style (0-5) |

---

## API Client Data Classes

Internal Python dataclasses for type safety (not persisted).

```python
# custom_components/vonage/api.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class SmsRequest:
    to: str  # E.164 phone number
    text: str
    from_number: str  # Sender ID

@dataclass
class SmsResponse:
    message_id: str
    status: int  # 0 = success
    error_text: Optional[str] = None

@dataclass
class VoiceCallRequest:
    to: str  # E.164 phone number
    text: str  # TTS message
    from_number: str
    language: str = "en-US"
    style: int = 0

@dataclass
class VoiceCallResponse:
    uuid: str  # Call UUID
    status: str  # "started", "ringing", etc.
    error: Optional[str] = None
```

---

## State Transitions

Not applicable — this integration is stateless. Services fire-and-forget with success/error response.

---

## Relationships

```
ConfigEntry (1) ──────┬──────> VonageSmsNotificationService (1)
                      │
                      └──────> VonageVoiceService (0..1, if Voice configured)
                                      │
                                      ▼
                               VonageApiClient (1)
                                 ├── send_sms()
                                 └── make_call()
```

- **ConfigEntry** holds credentials, created once per integration setup
- **VonageSmsNotificationService** always available (requires SMS credentials)
- **VonageVoiceService** only available if Application ID + private key provided
- **VonageApiClient** singleton wrapper shared by both services
