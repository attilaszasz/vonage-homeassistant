# Research: Vonage Voice API `dtmfAnswer` Field

**Feature**: 002-dtmf-support  
**Date**: 2026-02-21  
**Purpose**: Confirm `dtmfAnswer` behavior, placement, valid characters, limits, and NCCO interaction before implementation

## Sources Consulted

- [Vonage Voice API Reference — Create an outbound call (`POST /v1/calls/`)](https://developer.vonage.com/en/api/voice#createCall)
- [Vonage NCCO Reference — Connect action, Phone endpoint](https://developer.vonage.com/en/voice/voice-api/ncco-reference#connect)
- [Vonage DTMF Concepts](https://developer.vonage.com/en/voice/voice-api/concepts/dtmf)
- Existing workspace code: `custom_components/vonage/api.py` (current `_make_call_sync` implementation)

---

## 1. Field Placement

**Decision**: `dtmfAnswer` is **nested inside the `to` phone endpoint object**, not a top-level field in the `create_call` request payload.

**Rationale**:
- The Vonage Voice API reference for `POST /v1/calls/` shows the request body structure as:
  ```json
  {
    "to": [{"type": "phone", "number": "14155550100", "dtmfAnswer": "p*123#"}],
    "from": {"type": "phone", "number": "14155550100"},
    "ncco": [...]
  }
  ```
- `dtmfAnswer` appears as a property of the phone endpoint object inside the `to` array, at the same level as `type` and `number`.
- This is confirmed in both:
  - The **API reference** (`create_call` request body → `to` → `Connect to a Phone (PSTN) number` → `dtmfAnswer`)
  - The **NCCO reference** (`connect` action → endpoint → Phone (PSTN) → `dtmfAnswer`)
- The same structure appears in the `connect` NCCO action's `endpoint` array, where `dtmfAnswer` is a property of the phone endpoint object.

**Correction to spec.md**: The spec states "include it as a top-level field in the Vonage Voice API `create_call` request payload" (FR-002). This is **technically imprecise** — `dtmfAnswer` is a field inside the `to[0]` endpoint object. The spec's intent is correct (the field goes in the `create_call` payload, not in the NCCO), but the wording "top-level" should be understood as "in the `create_call` payload's `to` endpoint object, not inside an NCCO action."

**Alternatives Considered**: None — the API documentation is unambiguous on placement.

---

## 2. Valid Characters

**Decision**: Valid characters are digits `0-9`, `*`, `#`, and `p` (500ms pause). **Confirmed.**

**Rationale**:
- The [DTMF Concepts page](https://developer.vonage.com/en/voice/voice-api/concepts/dtmf) states explicitly:
  > "You can use digits `0-9`, `*`, and `#`. A `p` indicates a pause of 500ms if you need to add a delay in sending the digits."
- The NCCO reference for the phone endpoint's `dtmfAnswer` field states:
  > "Set the digits that are sent to the user as soon as the Call is answered. The `*` and `#` digits are respected. You create pauses using `p`. Each pause is 500ms."
- The API reference example value is `p*123#`, which demonstrates all character types (pause, star, digits, hash).

**Not confirmed**: Whether lowercase `p` only or also uppercase `P` is accepted. Documentation only shows lowercase `p`. Recommend using lowercase only.

**Alternatives Considered**: None — documentation is consistent across all three sources.

---

## 3. Maximum Length

**Decision**: **No documented maximum length** for the `dtmfAnswer` string.

**Rationale**:
- The Vonage Voice API reference defines `dtmfAnswer` as type `string` with no `MIN`/`MAX` length constraints (unlike `number` which has `MIN 7` / `MAX 15`).
- The NCCO reference describes `dtmfAnswer` without mentioning any length limit.
- The DTMF Concepts page does not mention a length limit.
- The spec correctly states: "Vonage API enforces its own length limits; excessively long strings result in an API error" — this is a safe assumption but **no specific limit is documented**.

**Practical guidance**: Delegate length validation entirely to the Vonage API. Do not impose an artificial limit in the integration. If the API rejects an overly long string, surface the error to the user via `HomeAssistantError`.

**Alternatives Considered**: Imposing a conservative client-side limit (e.g., 50 characters). Rejected — no documented basis for a specific number, and the API will enforce its own constraints.

---

## 4. Behavior When Call Is Answered

**Decision**: DTMF tones are sent **automatically when the callee answers**. **Confirmed.**

**Rationale**:
- The API reference description for `dtmfAnswer` states:
  > "Provide [DTMF] to send when the call is answered"
- The NCCO reference states:
  > "Set the digits that are sent to the user **as soon as the Call is answered**."
- The DTMF Concepts page states:
  > "For an outbound call made either via the `create_call` endpoint, or via a `connect` action, you can set the `dtmfAnswer` parameter within the phone endpoint. This means that **when the call is answered, Vonage will automatically send the defined string of tones**."

**Key detail**: The DTMF sending is handled entirely by Vonage's infrastructure. The integration does not need to track call state or send a follow-up API request — just include `dtmfAnswer` in the payload and Vonage handles the rest.

**Alternatives Considered**: Sending DTMF manually via the `PUT /v1/calls/:uuid/dtmf` endpoint after call setup. Rejected — `dtmfAnswer` is simpler, atomic, and doesn't require tracking the call UUID or waiting for an `answered` webhook event.

---

## 5. Interaction with NCCO

**Decision**: `dtmfAnswer` works alongside `ncco`. The DTMF tones are sent to the **callee** when they answer; the NCCO controls the **caller's leg** of the call. They are independent concerns.

**Rationale**:
- `dtmfAnswer` is a property of the `to` phone endpoint — it defines what is sent to that endpoint when connected.
- `ncco` defines the call control flow for the calling leg (e.g., `talk` action to play TTS to the callee once connected).
- The NCCO connect action example in the documentation shows `dtmfAnswer` used inside the phone endpoint:
  ```json
  {
    "action": "connect",
    "endpoint": [{"type": "phone", "number": "447700900001", "dtmfAnswer": "2p02p"}]
  }
  ```
- For the `create_call` use case (outbound call with inline NCCO), the flow is:
  1. Call is initiated to the `to` phone number
  2. **When the callee answers**, Vonage sends the `dtmfAnswer` DTMF tones to the callee's phone line
  3. **Simultaneously/subsequently**, the NCCO actions execute on the call (e.g., `talk` plays TTS)
- The DTMF tones and NCCO actions are **not sequenced against each other** in any documented way. The `dtmfAnswer` fires on answer; the NCCO begins executing on the call. In practice, for our use case (outbound call with TTS + DTMF), the DTMF tones go to the callee's phone system (e.g., IVR) while the TTS plays to the callee once the call is connected.

**What could not be confirmed**: The exact timing/sequencing between `dtmfAnswer` and the first NCCO action execution. Documentation does not specify whether DTMF completes before NCCO starts, or whether they run in parallel. For our use case (bypass IVR then play TTS), this is acceptable — the DTMF navigates the IVR system and the TTS plays the message once through.

**Alternatives Considered**: Using a dedicated `input` NCCO action to send DTMF. Rejected — `input` is for **collecting** DTMF from the caller, not sending it to the callee. The `PUT /v1/calls/:uuid/dtmf` endpoint could be used for post-connection DTMF, but `dtmfAnswer` is the correct mechanism for on-answer DTMF.

---

## 6. Existing Code Pattern in `api.py`

**Decision**: The current `_make_call_sync` method builds the `call_data` dict with `to`, `from`, and `ncco`. Adding `dtmfAnswer` requires inserting it into the `to[0]` endpoint object.

**Rationale**:
- Current code ([api.py](../../custom_components/vonage/api.py) lines 164–177):
  ```python
  call_data = {
      "to": [{"type": "phone", "number": to_number}],
      "from": {"type": "phone", "number": from_number},
      "ncco": ncco
  }
  ```
- To add DTMF support, the `to[0]` dict should conditionally include `"dtmfAnswer": dtmf_answer` when the value is provided and non-empty.
- The `VoiceCallRequest` dataclass needs an optional `dtmf_answer: Optional[str] = None` field.
- The `_make_call_sync` and `make_call` method signatures need the optional parameter threaded through.

**Implementation sketch**:
```python
to_endpoint = {"type": "phone", "number": to_number}
if dtmf_answer:
    to_endpoint["dtmfAnswer"] = dtmf_answer

call_data = {
    "to": [to_endpoint],
    "from": {"type": "phone", "number": from_number},
    "ncco": ncco
}
```

---

## Summary

| Question | Answer | Confidence | Source |
|----------|--------|------------|--------|
| Field placement | Inside `to[0]` phone endpoint object (not top-level) | **Confirmed** | API reference, NCCO reference |
| Valid characters | `0-9`, `*`, `#`, `p` (500ms pause) | **Confirmed** | DTMF Concepts page, NCCO reference |
| Maximum length | Not documented; delegate to API | **Not documented** | API reference (no MAX constraint listed) |
| Behavior on answer | Vonage auto-sends DTMF when callee answers | **Confirmed** | DTMF Concepts page, API reference, NCCO reference |
| NCCO interaction | Independent — DTMF goes to callee, NCCO controls call flow | **Confirmed** (sequencing unspecified) | NCCO reference, DTMF Concepts page |
| Case sensitivity of `p` | Only lowercase `p` shown in docs | **Partially confirmed** | All examples use lowercase only |

**No NEEDS CLARIFICATION items remain.** All findings are sufficient to proceed with implementation.
