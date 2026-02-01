# Feature Specification: Vonage Home Assistant Integration

**Feature Branch**: `001-vonage-ha-integration`  
**Created**: 2026-02-01  
**Status**: Draft  
**Input**: User description: "Home Assistant custom integration for Vonage Voice and SMS API - send SMS messages and make voice calls with text-to-speech"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Send SMS Notification (Priority: P1)

As a Home Assistant user, I want to send SMS notifications via Vonage so that I can receive alerts about important home events (e.g., security alerts, temperature warnings) on my phone even when I don't have internet access.

**Why this priority**: SMS is the most common and simplest use case for Vonage integration. It provides immediate value and establishes the core integration infrastructure (config flow, API wrapper, credentials handling) that other features will build upon.

**Independent Test**: Can be fully tested by configuring the integration with Vonage credentials and calling the `notify.vonage_sms` service with a phone number and message text.

**Acceptance Scenarios**:

1. **Given** the Vonage integration is configured with valid API credentials, **When** I call the `notify.vonage_sms` service with a target phone number and message, **Then** the recipient receives the SMS within 30 seconds
2. **Given** the Vonage integration is configured, **When** I use the notification service in an automation (e.g., "send SMS when motion detected"), **Then** the SMS is delivered when the automation triggers
3. **Given** invalid API credentials are entered, **When** I attempt to configure the integration, **Then** the config flow displays an authentication error and does not complete setup

---

### User Story 2 - Make Voice Call with Text-to-Speech (Priority: P2)

As a Home Assistant user, I want to make an outbound voice call that speaks a message using text-to-speech so that I can receive urgent audio alerts when SMS alone isn't sufficient (e.g., fire alarm, intrusion detection).

**Why this priority**: Voice calls are more intrusive and attention-grabbing than SMS, making them ideal for critical alerts. This builds on the API infrastructure from Story 1 but requires additional Voice API integration.

**Independent Test**: Can be fully tested by calling the `vonage.make_call` service with a phone number and message text, then verifying the recipient receives a call that speaks the message.

**Acceptance Scenarios**:

1. **Given** the Vonage integration is configured with a valid Application ID and private key, **When** I call the `vonage.make_call` service with a target number and message, **Then** the recipient receives a voice call that speaks the message using TTS
2. **Given** a voice call is initiated, **When** the recipient answers, **Then** they hear the text-to-speech message in the configured language/voice
3. **Given** a voice call is initiated, **When** the recipient does not answer, **Then** the call ends gracefully without error

---

### Edge Cases

- What happens when the Vonage API rate limit is exceeded? → Vonage SDK handles retries with exponential backoff internally; integration surfaces final error if retries exhausted
- What happens when the API credentials are revoked mid-session? → Integration logs error, entities become unavailable, user prompted to reconfigure
- What happens when the target phone number is invalid? → Service call fails with descriptive error message
- What happens when the message text exceeds SMS character limits? → Vonage automatically splits into multiple SMS (integration should document this behavior)
- What happens when the voice call NCCO (call script) fails to render? → Service call fails with descriptive error

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Integration MUST authenticate with Vonage using API key + secret for SMS API
- **FR-002**: Integration MUST authenticate with Vonage using Application ID + private key (pasted into config flow) for Voice API (JWT-based auth)
- **FR-003**: Integration MUST provide a single unified Config Flow for UI-based setup; API key/secret required, Application ID/private key optional (enables voice if provided)
- **FR-004**: Integration MUST expose a notification service (`notify.vonage_sms`) that sends SMS messages
- **FR-005**: Integration MUST expose a service (`vonage.make_call`) that initiates outbound voice calls with TTS
- **FR-005a**: Voice calls MUST use a configurable default language/style set during config flow, with optional per-call override via service data
- **FR-006**: Integration MUST store credentials securely via Home Assistant's ConfigEntry (never logged)
- **FR-007**: Integration MUST handle Vonage API errors gracefully with user-friendly error messages
- **FR-008**: Integration MUST be installable via HACS

### Key Entities

- **VonageAccount**: Represents the user's Vonage account; holds API key, secret, application ID, private key, and phone number
- **SMS**: Represents an outbound SMS message; includes recipient phone number, message text, and sender ID
- **VoiceCall**: Represents an outbound voice call; includes recipient phone number, TTS message, language/voice preference

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can send an SMS notification within 2 minutes of installing the integration
- **SC-002**: SMS messages are delivered to recipients within 60 seconds of service call (Vonage SLA dependent)
- **SC-003**: Voice calls connect and play TTS message within 30 seconds of service call initiation
- **SC-004**: Config flow validates credentials before completing setup (no silent failures)
- **SC-005**: Integration passes HACS validation (`hacs/action`) and hassfest checks
- **SC-006**: Integration works on Home Assistant 2024.1.0 or later

## Assumptions

- User has an active Vonage account with sufficient credit
- User has created a Vonage Application with Voice capability enabled (for voice calls)
- User has a Vonage virtual phone number to use as sender ID
- User is familiar with Home Assistant service calls and automations
- Vonage API rate limits are sufficient for typical home automation use (few messages/calls per day)

## Clarifications

### Session 2026-02-01

- Q: Should voice calls support configurable language/voice options or use a single default? → A: Configurable default during setup, with optional per-call override in service data
- Q: Should integration include account balance tracking sensor? → A: No — users can check balance in Vonage portal; removes complexity
- Q: How should private key for Voice API be provided? → A: User pastes private key content directly into config flow (stored encrypted in ConfigEntry)
- Q: Should SMS and Voice require separate config steps? → A: Single unified config flow — API key/secret required; Application ID/private key optional (enables voice if provided)
- Q: What minimum Home Assistant version should be supported? → A: HA 2024.1.0 — modern APIs, covers most HACS users
