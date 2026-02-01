# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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