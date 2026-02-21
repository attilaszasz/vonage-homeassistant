# Feature Specification: Add Optional DTMF Support to `vonage.make_call`

**Feature Branch**: `002-dtmf-support`  
**Created**: 2026-02-21  
**Status**: Draft  
**Input**: User description: "Add support for the dtmfAnswer field in the vonage.make_call service to allow Home Assistant to automatically send DTMF digits when an outbound call is answered (e.g., to bypass IVR menus with strings like p*123#). This should be an optional per-action service call parameter, not a global integration setting."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Send DTMF Digits on Call Answer (Priority: P1)

As a Home Assistant user, I want to include DTMF digits (e.g., `p*123#`) in my `vonage.make_call` service call so that when the outbound call is answered, the digits are automatically sent — allowing me to bypass IVR menus, enter access codes, or interact with automated phone systems without manual input.

**Why this priority**: This is the core and only feature being added. It enables fully automated dialing through IVR menus, which is the primary use case for DTMF support (e.g., gate access codes, alarm system disarm sequences, automated check-in systems).

**Independent Test**: Can be fully tested by calling the `vonage.make_call` service with a `dtmfAnswer` parameter set to a DTMF string (e.g., `"p*123#"`), verifying that the Vonage API receives the `dtmfAnswer` field in the outbound call payload, and confirming the recipient hears the DTMF tones after answering.

**Acceptance Scenarios**:

1. **Given** the Vonage integration is configured with valid Voice API credentials, **When** I call `vonage.make_call` with `to`, `text`, and `dtmfAnswer: "p*123#"`, **Then** the outbound call is placed and the DTMF digits `p*123#` are sent automatically when the call is answered
2. **Given** the Vonage integration is configured with valid Voice API credentials, **When** I call `vonage.make_call` with `to` and `text` but without `dtmfAnswer`, **Then** the call behaves exactly as before — no DTMF digits are sent, and no errors occur
3. **Given** the Vonage integration is configured with valid Voice API credentials, **When** I call `vonage.make_call` with `dtmfAnswer: ""` (empty string), **Then** the call is placed without DTMF digits (empty value is treated as absent)

---

### Edge Cases

- What happens when `dtmfAnswer` contains invalid characters (e.g., letters)? → The Vonage API validates the DTMF string; invalid characters result in an API error surfaced as a `HomeAssistantError` to the user
- What happens when `dtmfAnswer` is an empty string? → Treated as absent; no `dtmfAnswer` key is included in the API payload
- What happens when `dtmfAnswer` is provided but Voice API credentials are not configured? → The existing "Voice API not configured" error is raised before DTMF is relevant
- What happens when `dtmfAnswer` contains only pause characters (e.g., `"ppp"`)? → Valid DTMF string; Vonage API accepts it and introduces pauses before the call proceeds
- What happens when `dtmfAnswer` is very long? → Vonage API enforces its own length limits; excessively long strings result in an API error

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `vonage.make_call` service MUST accept an optional `dtmfAnswer` parameter as a text string
- **FR-002**: When `dtmfAnswer` is provided and non-empty, the integration MUST include it in the `to[0]` phone endpoint object of the Vonage Voice API `create_call` request payload (alongside `type` and `number`)
- **FR-003**: When `dtmfAnswer` is omitted or empty, the integration MUST NOT include a `dtmfAnswer` field in the phone endpoint object (preserving existing behavior)
- **FR-004**: The `dtmfAnswer` parameter MUST be a per-action (per-service-call) option, not a global integration setting
- **FR-005**: The service definition MUST describe the `dtmfAnswer` field with appropriate metadata (name, description, selector) for the Home Assistant UI
- **FR-006**: The integration MUST pass through any Vonage API errors related to invalid DTMF strings as user-facing error messages
- **FR-007**: The voice call request data model MUST be updated to carry the optional DTMF answer value from service call through to the API layer
- **FR-008**: Documentation (README) MUST be updated to describe the new parameter with a practical usage example
- **FR-009**: Service contracts and specs MUST be updated to reflect the new `dtmfAnswer` parameter
- **FR-010**: The integration MUST redact `dtmfAnswer` values from debug logs (e.g., log `"dtmfAnswer": "***"` instead of the actual value) because DTMF strings commonly contain sensitive data such as access codes and PINs

### Key Entities

- **VoiceCallRequest**: Extended to include an optional DTMF answer string alongside existing fields (recipient, TTS text, language, style)
- **Service Schema (make_call)**: Extended to accept the optional `dtmfAnswer` text field in addition to existing parameters

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can include a `dtmfAnswer` parameter in `vonage.make_call` service calls and the DTMF digits are sent when the call is answered
- **SC-002**: Existing `vonage.make_call` service calls without `dtmfAnswer` continue to work identically with no behavioral change
- **SC-003**: The `dtmfAnswer` field appears in the Home Assistant service call UI with a descriptive label and text input
- **SC-004**: All existing tests continue to pass, and new tests cover the DTMF parameter (present, absent, and empty cases)
- **SC-005**: README and spec documentation clearly describe the new parameter with at least one practical example

## Assumptions

- The Vonage Voice API `create_call` endpoint supports `dtmfAnswer` as a field inside the `to[0]` phone endpoint object (confirmed per Vonage API reference and NCCO reference; see [research.md](research.md))
- Valid DTMF strings consist of digits `0-9`, `*`, `#`, and `p` (pause); validation is delegated to the Vonage API
- The existing Voice API authentication (Application ID + private key) is sufficient — no additional credentials or permissions are needed for DTMF
- This feature does not require any changes to the config flow or integration setup
- DTMF string length limits are enforced by the Vonage API, not by the integration

## Clarifications

### Session 2026-02-21

- Q: Should `dtmfAnswer` values be redacted from debug logs, given they may contain sensitive access codes or PINs? → A: Yes — redact from debug logs (log `"***"` instead of actual value)
