# Vonage Home Assistant Integration

[![hacs][hacs-shield]][hacs-url]
[![GitHub Release][release-shield]][release-url]
[![GitHub Activity][commits-shield]][commits-url]
[![License][license-shield]][license-url]

Home Assistant integration for sending SMS notifications and making voice calls using the Vonage API.

## Features

- **SMS Notifications**: Send SMS messages via the `notify.vonage_sms` service
- **Voice Calls**: Make outbound voice calls with text-to-speech via the `vonage.make_call` service
- **Easy Configuration**: UI-based setup with credential validation
- **Multiple Languages**: Support for 15+ languages for voice calls
- **Error Handling**: Comprehensive error reporting and logging

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations" 
3. Click the "+" button
4. Search for "Vonage"
5. Install the integration
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/vonage` folder to your Home Assistant config directory
2. Restart Home Assistant
3. Go to Settings > Devices & Services
4. Click "Add Integration" and search for "Vonage"

## Configuration

### Prerequisites

You need a Vonage account with:

1. **For SMS**: API Key and API Secret (required)
2. **For Voice**: Vonage Application with Application ID and Private Key (optional)
3. **Phone Number**: A Vonage phone number to use as sender ID

### Setup Steps

1. Go to Settings > Devices & Services in Home Assistant
2. Click "Add Integration" and search for "Vonage"
3. Enter your credentials:
   - **API Key**: Your Vonage API key
   - **API Secret**: Your Vonage API secret  
   - **Phone Number**: Your Vonage phone number (E.164 format, e.g., +14155550100)
   - **Application ID**: (Optional) For voice calls
   - **Private Key**: (Optional) For voice calls, paste the entire PEM content
   - **Default Language**: (Optional) Default language for voice calls (default: en-US)
   - **Default Voice Style**: (Optional) Default voice style 0-5 (default: 0)

4. Click "Submit" - credentials will be validated before saving

## Usage

### SMS Notifications

The integration automatically creates a `notify.vonage_sms` service:

```yaml
service: notify.vonage_sms
data:
  message: "Alert: Motion detected at front door"
  target:
    - "+14155550101"
    - "+14155550102"
```

**Example Automation**:
```yaml
automation:
  - alias: "Motion Alert via SMS"
    trigger:
      platform: state
      entity_id: binary_sensor.front_door_motion
      to: "on"
    action:
      service: notify.vonage_sms
      data:
        message: "Motion detected at {{ trigger.to_state.attributes.friendly_name }}"
        target: "+14155550101"
```

### Voice Calls

If you configured Voice API credentials, use the `vonage.make_call` service:

```yaml
service: vonage.make_call
data:
  target: "+14155550101"
  message: "Fire alarm triggered. Please check your home immediately."
  language: "en-US"  # Optional, uses default if not specified
  style: 1           # Optional, uses default if not specified
```

**Example Automation**:
```yaml
automation:
  - alias: "Fire Alarm Voice Alert"
    trigger:
      platform: state
      entity_id: binary_sensor.smoke_detector
      to: "on"
    action:
      service: vonage.make_call
      data:
        target: "+14155550101"
        message: >
          Emergency: Fire alarm activated in the {{ trigger.to_state.attributes.friendly_name }}.
          Please evacuate immediately and call 911.
        language: "en-US"
        style: 0
```

## Supported Voice Languages

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en-US` | English (US) | `fr-FR` | French (France) |
| `en-GB` | English (UK) | `de-DE` | German |
| `en-AU` | English (Australia) | `it-IT` | Italian |
| `es-ES` | Spanish (Spain) | `pt-BR` | Portuguese (Brazil) |
| `es-MX` | Spanish (Mexico) | `nl-NL` | Dutch |

[Full list of supported languages](https://developer.vonage.com/en/voice/voice-api/concepts/text-to-speech#supported-languages)

## Troubleshooting

### Common Issues

**"Invalid Vonage credentials" error**:
- Verify your API key and secret are correct
- Check that your Vonage account is active
- For Voice: Ensure Application ID and Private Key match your Vonage application

**SMS not delivered**:
- Verify phone numbers are in E.164 format (e.g., +14155550101)
- Check Vonage account balance
- Review logs for rate limiting or other API errors

**Voice calls not working**:
- Ensure you have configured both Application ID and Private Key
- Verify your Vonage application has Voice capabilities enabled
- Check that your phone number supports outbound calls

### Debugging

Enable debug logging by adding to `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.vonage: debug
```

Logs will show API requests/responses (credentials are never logged).

## Support

- [Home Assistant Community Forum](https://community.home-assistant.io/)
- [GitHub Issues](https://github.com/attilaszasz/vonage-homeassistant/issues)
- [Vonage API Documentation](https://developer.vonage.com/)

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) first.

## Author

Created and maintained by **Attila Szasz**.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://github.com/hacs/integration
[release-shield]: https://img.shields.io/github/v/release/attilaszasz/vonage-homeassistant
[release-url]: https://github.com/attilaszasz/vonage-homeassistant/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/attilaszasz/vonage-homeassistant
[commits-url]: https://github.com/attilaszasz/vonage-homeassistant/graphs/commit-activity
[license-shield]: https://img.shields.io/github/license/attilaszasz/vonage-homeassistant
[license-url]: https://github.com/attilaszasz/vonage-homeassistant/blob/main/LICENSE