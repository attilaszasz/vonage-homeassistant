# Quickstart: Vonage Account Balance Sensor

**Feature**: 003-balance-sensor
**Audience**: Developers verifying the implementation locally before opening a PR.

## Prerequisites

- Repo bootstrapped: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt -r requirements_test.txt`.
- Working on branch `003-balance-sensor`.
- No live Vonage credentials required — all tests mock the SDK.

## 1. Run the new unit tests

```bash
pytest tests/test_api.py::test_async_get_balance_success -v
pytest tests/test_api.py -k "balance" -v
pytest tests/test_coordinator.py -v
pytest tests/test_balance_sensor.py -v
```

Expected: all new tests pass; no existing tests regress.

## 2. Run the full suite with coverage

```bash
pytest --cov=custom_components/vonage --cov-report=term-missing
```

Expected: coverage on `api.py`, `coordinator.py`, and `sensor.py` for the balance code paths matches or exceeds the existing repo standard (per FR-016, FR-017, SC-006).

## 3. Lint and type-check

```bash
ruff check custom_components/ tests/
mypy custom_components/
```

Expected: clean.

## 4. HACS / hassfest sanity (CI parity)

These run in CI; locally they require an HA core checkout. Skipped here unless reproducing a CI failure.

## 5. Manual smoke (optional, against HA dev container)

1. Start HA in the devcontainer with the integration loaded.
2. Add a Vonage config entry with valid API key/secret.
3. Confirm `sensor.vonage_account_balance` appears in Developer Tools → States with:
   - A numeric state matching your real balance.
   - `unit_of_measurement` equal to your account currency code.
   - `device_class: monetary`, `state_class: total`.
   - Attributes include `last_updated` (ISO-8601) and, if the API returns it, `auto_reload`.
4. Add a second config entry with another Vonage account; confirm the second sensor is created with a `_2` suffix and its own state.
5. Temporarily revoke or alter the API secret for one entry; on the next 15-minute poll (or after `homeassistant.update_entity` service call to force refresh), confirm the integration triggers re-authentication for that entry only.
6. Restore valid credentials; confirm the sensor returns to available on the next successful poll without restarting HA.

## 6. Acceptance mapping

- Story P1 (basic balance) → tests in `test_balance_sensor.py::test_state_unit_device_class` + step 3 above.
- Story P2 (failure / recovery / re-auth) → `test_coordinator.py` failure-recovery + `test_api.py::test_async_get_balance_auth_failed` + step 5.
- Story P3 (attributes) → `test_balance_sensor.py::test_attributes_with_auto_reload` and `test_attributes_without_auto_reload`.
- Multi-entry → `test_balance_sensor.py::test_multi_config_entry_unique_ids` + step 4.

## 7. Done criteria

- [ ] All tests above green.
- [ ] `ruff` and `mypy` clean.
- [ ] No `_LOGGER` call in new code paths includes `self.api_secret` (verified by a dedicated test).
- [ ] README updated with the new sensor under "Entities".
- [ ] No changes to `manifest.json` version (release workflow handles that on tag).
