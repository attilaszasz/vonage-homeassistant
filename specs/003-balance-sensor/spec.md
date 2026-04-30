# Feature Specification: Vonage Account Balance Sensor

**Feature Branch**: `003-balance-sensor`  
**Created**: 2026-04-30  
**Status**: Draft  
**Input**: User description: "Add a Vonage account balance sensor — exposes current account balance from the Vonage API as a Home Assistant sensor entity (`sensor.vonage_account_balance`) with currency unit, monetary device class, total state class, polling via DataUpdateCoordinator, and proper error handling for auth failures and transient errors."

## Clarifications

### Session 2026-04-30

- Q: How should the balance sensor's entity ID behave when multiple Vonage config entries are configured? → A: Per-entry uniqueness via stable `unique_id` derived from the config entry; first entry gets `sensor.vonage_account_balance`, additional entries get HA-suffixed IDs (e.g., `_2`).
- Q: Should the balance polling interval be user-configurable in this feature? → A: No — fixed 15-minute interval for this MVP; configurability is deferred to a later feature.
- Q: How should numeric precision of the balance state be handled? → A: Preserve the value returned by the Vonage API as-is; no rounding or truncation in the integration.
- Q: Which Vonage API responses should trigger Home Assistant re-authentication? → A: HTTP 401 only; all other 4xx/5xx responses are treated as transient/diagnostic and handled via the coordinator's standard failure path.
- Q: What should happen if the first balance fetch fails at integration setup time? → A: Raise `ConfigEntryNotReady` so Home Assistant retries setup with backoff; entities are created only once the first poll succeeds. Subsequent (post-setup) failures follow FR-010 (entity remains, becomes unavailable, recovers automatically).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Monitor Current Vonage Account Balance (Priority: P1)

As a Home Assistant user with the Vonage integration configured, I want to see my current Vonage account balance as a sensor in Home Assistant so that I always know how much credit I have available for outgoing SMS and voice calls without having to log into the Vonage dashboard.

**Why this priority**: This is the core value of the feature. Without it, the user has no visibility of their Vonage credit inside Home Assistant. It is the MVP and delivers immediate value on its own.

**Independent Test**: After completing the existing Vonage config flow, the user can open the Home Assistant UI and observe a `sensor.vonage_account_balance` entity that displays a numeric balance with the correct currency unit and updates over time. Fully testable end-to-end against a mocked Vonage API.

**Acceptance Scenarios**:

1. **Given** the Vonage integration is configured with valid API credentials, **When** Home Assistant finishes integration setup, **Then** a sensor entity `sensor.vonage_account_balance` is created with the friendly name "Vonage Account Balance", a numeric state matching the value returned by the Vonage account balance endpoint, and a unit of measurement equal to the currency code returned by that endpoint (e.g., `EUR`, `USD`).
2. **Given** the balance sensor exists and the integration is running, **When** the configured polling interval elapses, **Then** the sensor state refreshes to reflect the latest balance reported by the Vonage API.
3. **Given** the balance sensor exists, **When** a user views the sensor in Home Assistant, **Then** it is classified with device class `monetary` and state class `total` so that it is treated as a cumulative monetary value (not aggregated as a measurement) and displayed appropriately by HA UI components.

---

### User Story 2 - Detect and Recover From Backend Failures (Priority: P2)

As a Home Assistant user, I want the balance sensor to clearly indicate when the integration cannot reach the Vonage API or when my credentials are no longer valid, so that I can trust the displayed value and take action (e.g., re-authenticate) when needed.

**Why this priority**: Silent staleness or misleading values would erode trust in the sensor and could cause users to act on outdated information. Recovery behavior also keeps the integration robust over long uptimes.

**Independent Test**: Simulate API failure modes (transient error, rate limiting, HTTP 401) against a mocked backend and verify the sensor's availability and re-authentication behavior change accordingly, then restore the mock to a successful response and verify the sensor recovers automatically.

**Acceptance Scenarios**:

1. **Given** the balance sensor is working normally, **When** the next poll fails due to a transient error (timeout, 5xx, rate limit), **Then** the sensor's `available` property becomes `False` until a subsequent successful poll, and no exception is surfaced to the user beyond standard HA logs.
2. **Given** the sensor has previously become unavailable due to an API failure, **When** a later poll succeeds, **Then** the sensor automatically becomes available again and exposes the new balance value without requiring user intervention or a Home Assistant restart.
3. **Given** the integration's stored credentials are invalid (the Vonage API responds with HTTP 401), **When** the coordinator attempts to fetch the balance, **Then** the integration triggers Home Assistant's re-authentication flow (`ConfigEntryAuthFailed`) so the user is prompted to update credentials, and the sensor is marked unavailable until valid credentials are provided.
4. **Given** any failed balance fetch, **When** the failure is logged, **Then** the diagnostic log entry includes the HTTP status code and any Vonage request identifier returned, but it MUST NOT include the API secret or other credential material.

---

### User Story 3 - Inspect Balance Context via Attributes (Priority: P3)

As an advanced user building automations or dashboards, I want additional context about the balance (whether auto-reload is enabled and when it was last refreshed) exposed as attributes on the sensor so I can build smarter automations and verify data freshness.

**Why this priority**: This is a convenience enhancement layered on top of the core sensor. The integration is fully usable without it, but it improves observability and unlocks more automations.

**Independent Test**: Mock the Vonage account balance endpoint to return a payload that includes auto-reload information, refresh the coordinator, and verify the sensor exposes `auto_reload` and `last_updated` attributes with the expected values. Also verify graceful behavior when the upstream payload omits the auto-reload field.

**Acceptance Scenarios**:

1. **Given** the Vonage API returns auto-reload information in the balance payload, **When** the sensor state is updated, **Then** the sensor exposes an `auto_reload` attribute reflecting that value (boolean).
2. **Given** a successful balance refresh, **When** the user inspects the sensor, **Then** a `last_updated` attribute is present containing the ISO-8601 timestamp of the most recent successful fetch.
3. **Given** the Vonage API response omits the auto-reload field, **When** the sensor state is updated, **Then** the `auto_reload` attribute is absent or `None` and the sensor remains otherwise functional.

---

### Edge Cases

- **Zero or negative balance**: The sensor MUST display a balance of `0` or a negative value as-is (some accounts may go negative if post-paid). It MUST NOT clamp, hide, or treat these as errors.
- **Currency change**: If the currency code returned by the Vonage API changes between polls (rare, e.g., account migration), the sensor's unit of measurement MUST update on the next refresh. Historical recorder data with the old unit is left to Home Assistant's standard handling and is out of scope.
- **First poll fails at startup**: If the very first balance fetch during config-entry setup fails (transient error or 401), the integration MUST raise `ConfigEntryNotReady` (or `ConfigEntryAuthFailed` for 401) so Home Assistant retries setup with backoff or prompts re-authentication; the balance entity is created only after the first successful poll. Once the entity exists, later failures follow FR-010 (entity remains visible and becomes unavailable until the next successful poll).
- **Partial payload**: If the Vonage API returns a successful response but omits the balance value or currency, the coordinator MUST treat that poll as failed (sensor unavailable) rather than reporting `None` as the state.
- **Rate limiting**: When the API responds with rate-limit errors, the integration MUST rely on the coordinator's standard retry/backoff and not aggressively re-poll.
- **Long outages**: After an extended period of failures, the sensor MUST recover on the next successful poll without requiring restart or reconfiguration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The integration MUST create one balance sensor entity per Vonage config entry. Each entity MUST have a stable `unique_id` derived from its config entry so Home Assistant can persist identity across restarts and disambiguate multiple accounts. The first entry's default entity ID MUST be `sensor.vonage_account_balance`; additional entries MUST receive Home Assistant's standard suffixed IDs (e.g., `sensor.vonage_account_balance_2`). The friendly name MUST be "Vonage Account Balance" (per entry).
- **FR-002**: The sensor's state MUST be the current numeric account balance reported by the Vonage account balance endpoint, preserved as-is with the precision returned by the API (no rounding, truncation, or reformatting performed by the integration).
- **FR-003**: The sensor's unit of measurement MUST be the ISO currency code reported by the Vonage account balance endpoint (e.g., `EUR`, `USD`).
- **FR-004**: The sensor MUST declare device class `monetary` and state class `total`.
- **FR-005**: The sensor MUST provide a sensible default icon (e.g., `mdi:cash`) for cases where the device class does not produce one.
- **FR-006**: The integration MUST fetch the balance through the existing API wrapper module (`api.py`), adding a method (e.g., `async_get_balance()`) if one does not already exist; entity code MUST NOT call the Vonage SDK or HTTP layer directly.
- **FR-007**: Authentication for balance requests MUST reuse the API key/secret already stored by the existing config flow; no additional configuration MUST be required to enable the sensor.
- **FR-008**: Balance polling MUST be driven by a `DataUpdateCoordinator` (extending the existing coordinator if present, otherwise introducing one) so that all entities sharing the same data source share a single refresh.
- **FR-009**: The balance polling interval MUST be a fixed 15 minutes for this feature. The integration MUST NOT introduce an options flow or other UI for changing the interval as part of this feature.
- **FR-010**: After the entity has been created (i.e., post-initial-success), the sensor's `available` property MUST be `False` after a failed coordinator refresh and MUST automatically return to `True` after the next successful refresh, without user intervention. Initial-setup failure handling is governed by the Edge Cases section (entity is not created until first success; setup uses `ConfigEntryNotReady` / `ConfigEntryAuthFailed`).
- **FR-011**: When the Vonage API returns HTTP 401 (invalid credentials), the integration MUST raise `ConfigEntryAuthFailed` so Home Assistant initiates the standard re-authentication flow.
- **FR-012**: All non-401 failure responses (timeouts, network errors, 5xx, rate limiting, and any other 4xx including 403) MUST be handled via the coordinator's standard retry/backoff behavior, surfaced as sensor unavailability, and MUST NOT trigger re-authentication.
- **FR-013**: Failure log entries MUST include diagnostic context — at minimum the HTTP status code and any Vonage-provided request identifier — and MUST NOT include the API secret or other credential material.
- **FR-014**: When the upstream payload includes auto-reload information, the sensor MUST expose it as an `auto_reload` attribute. When absent, the attribute MUST be omitted or `None` and MUST NOT cause the sensor to fail.
- **FR-015**: The sensor MUST expose a `last_updated` attribute containing the ISO-8601 timestamp of the last successful balance fetch.
- **FR-016**: Unit tests MUST cover the new API wrapper method, including success, HTTP 401 (auth failure), and transient error responses, using mocked Vonage SDK / HTTP responses (no live API calls).
- **FR-017**: Integration tests MUST verify that the sensor entity is created with the correct state, unit of measurement, device class, state class, attributes, and that it transitions to unavailable on backend failures and recovers on the next success.
- **FR-018**: The feature MUST NOT introduce low-balance alerting, historical balance tracking beyond the standard HA recorder, or any auto-reload / top-up configuration UI; these are explicitly out of scope.

### Key Entities

- **Vonage Account Balance**: Represents the current monetary balance on the Vonage account associated with the configured API credentials. Key attributes: numeric balance value, ISO currency code, optional auto-reload flag, timestamp of last successful refresh.
- **Vonage Credentials (existing)**: API key and secret already managed by the existing config flow; this feature consumes them but does not modify their lifecycle.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After configuring the Vonage integration with valid credentials, a user can locate the account balance sensor in the Home Assistant UI within 1 minute and see a balance value with a currency unit displayed.
- **SC-002**: The balance sensor's reported value reflects the current Vonage account balance with no more than 15 minutes of staleness under default settings.
- **SC-003**: 100% of Vonage API failure modes covered by tests (transient error, rate limit, HTTP 401, malformed payload) result in the sensor either becoming unavailable or triggering re-authentication — never displaying a stale or fabricated value as the current state.
- **SC-004**: After any transient backend outage shorter than the user's tolerance, the sensor returns to the available state on the first successful poll without requiring a Home Assistant restart, integration reload, or any user action.
- **SC-005**: No log entry produced by the balance feature contains the API secret or any other credential material, verified by automated tests asserting on log output during failure scenarios.
- **SC-006**: Test coverage for the new API wrapper method and balance sensor (unit + integration) is at least equivalent to the existing coverage standard of the repository, with all new code paths exercised by mocked tests and zero live API calls in CI.

## Assumptions

- The Vonage Account API exposes a balance endpoint reachable with the same API key/secret already collected by the existing config flow, and its response includes at least a numeric balance and an ISO currency code. Auto-reload information may or may not be present and is treated as optional.
- A `DataUpdateCoordinator` is the appropriate polling mechanism for this integration, consistent with existing Home Assistant custom-component conventions referenced in the project's Copilot instructions.
- A 15-minute default poll interval is acceptable for account balance freshness; making this user-configurable via the integration's options flow is desirable but not required for the MVP and may be deferred.- HTTP 401 from the balance endpoint reliably indicates invalid credentials (rather than a transient authorization hiccup), justifying immediate re-authentication. Other 4xx responses are treated as transient/diagnostic and surfaced via standard coordinator failure handling.
- Standard Home Assistant UI handling of `device_class: monetary` + `state_class: total` is sufficient for displaying and recording the value; no custom frontend work is required.
