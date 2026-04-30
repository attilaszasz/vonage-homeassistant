# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-04-30

### Fixed
- **Account balance setup retry loop**: The real Vonage Account SDK balance
  response includes `value` and `auto_reload`, but does not include a currency
  field. The balance sensor now defaults the unit to `EUR` when the SDK omits
  currency, matching the Account API balance model and preventing setup from
  failing with `Vonage balance update failed: VonageBalanceError`.
- Improved balance coordinator setup diagnostics while redacting configured API
  credentials from error messages.

## [1.1.0] - 2026-04-30

### Added
- **Account balance sensor**: `sensor.vonage_account_balance` per config entry,
  polled every 15 minutes. `device_class: monetary`, `state_class: total`, unit
  of measurement = account currency. Attributes: `last_updated` (ISO-8601) and
  optional `auto_reload`. First-fetch failures raise `ConfigEntryNotReady`;
  HTTP 401 triggers re-authentication; transient failures mark the sensor
  unavailable and recover automatically on the next successful poll.

## [1.0.3] - 2026-02-28

### Fixed
- **DTMF tones not sent during voice calls**: The Vonage Python SDK v4.x uses Pydantic
  `@validate_call` which coerces dicts into models using Python field names, not
  serialization aliases. The `dtmfAnswer` key was silently dropped because the SDK model
  expects `dtmf_answer` as the input key (serialized to `dtmfAnswer` in the HTTP request).
  Same fix applied to the `from`/`from_` field, removing an unreliable retry fallback.

## [1.0.0] - 2026-02-01

### Added
- Initial release of Vonage Home Assistant integration
- SMS notification service (`notify.vonage_sms`)
- Voice call service (`vonage.make_call`) with text-to-speech
- UI-based configuration flow with credential validation
- Support for 15+ languages for voice calls
- Comprehensive error handling and logging
- HACS compatibility
- Complete documentation and examples

### Features
- **SMS Notifications**: Send SMS messages via the `notify.vonage_sms` service
- **Voice Calls**: Make outbound voice calls with text-to-speech
- **Easy Configuration**: UI-based setup with credential validation
- **Multiple Languages**: Support for voice calls in various languages
- **Error Handling**: Comprehensive error reporting and logging
- **Security**: No credentials stored in logs, proper authentication handling

### Technical Details
- Compatible with Home Assistant 2024.1.0+
- Follows Home Assistant integration standards
- Uses official Vonage Python SDK
- Includes comprehensive test suite
- CI/CD automation with GitHub Actions