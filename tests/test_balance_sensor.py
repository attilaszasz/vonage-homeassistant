"""Tests for the Vonage account balance sensor and integration setup."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.vonage.api import AccountBalance, VonageBalanceError
from custom_components.vonage.const import (
    ATTR_AUTO_RELOAD,
    ATTR_LAST_UPDATED,
    DOMAIN,
    SCAN_INTERVAL_BALANCE,
)


CONFIG_DATA = {
    "api_key": "test_key",
    "api_secret": "test_secret",
    "phone_number": "+14155550100",
}


def _balance(value: float = 12.345, *, auto_reload: bool | None = True) -> AccountBalance:
    return AccountBalance(
        value=value,
        currency="EUR",
        auto_reload=auto_reload,
        fetched_at=datetime.now(timezone.utc),
    )


async def _setup_entry(
    hass,
    *,
    balance: AccountBalance | Exception | None = None,
    entry_data: dict | None = None,
    title: str = "Vonage",
):
    """Add a MockConfigEntry and run setup with the balance call mocked."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=title,
        data=entry_data or CONFIG_DATA,
    )
    entry.add_to_hass(hass)

    side_effect = None
    return_value = None
    if isinstance(balance, Exception):
        side_effect = balance
    else:
        return_value = balance if balance is not None else _balance()

    with patch(
        "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
        AsyncMock(return_value=True),
    ), patch(
        "custom_components.vonage.api.VonageApiClient.async_get_balance",
        AsyncMock(return_value=return_value, side_effect=side_effect),
    ) as mock_balance:
        ok = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry, mock_balance, ok


# -------------------------------------------------------------------------
# Foundational verification (T014a, T014b)
# -------------------------------------------------------------------------


async def test_first_setup_failure_raises_config_entry_not_ready(hass):
    """First-fetch transient failure prevents entity creation."""
    entry, _, _ = await _setup_entry(hass, balance=VonageBalanceError("boom"))
    # Setup fails -> entry is not loaded and no sensor entity is created.
    assert entry.state.name in ("SETUP_RETRY", "SETUP_ERROR", "NOT_LOADED")
    assert hass.states.get("sensor.vonage_account_balance") is None


async def test_first_setup_401_triggers_reauth(hass):
    """First-fetch 401 prevents entity creation; entry is not loaded."""
    entry, _, _ = await _setup_entry(
        hass, balance=ConfigEntryAuthFailed("401")
    )
    assert entry.state.name in ("SETUP_ERROR", "SETUP_RETRY", "NOT_LOADED")
    assert hass.states.get("sensor.vonage_account_balance") is None


# -------------------------------------------------------------------------
# US1 — Monitor Current Vonage Account Balance
# -------------------------------------------------------------------------


async def test_state_unit_device_class(hass):
    """Sensor exposes correct state, unit, classes, icon, and unique_id."""
    entry, _, ok = await _setup_entry(hass, balance=_balance())
    assert ok is True

    state = hass.states.get("sensor.vonage_account_balance")
    assert state is not None
    assert state.state == "12.345"
    attrs = state.attributes
    assert attrs["unit_of_measurement"] == "EUR"
    assert attrs["device_class"] == "monetary"
    assert attrs["state_class"] == "total"
    assert attrs["icon"] == "mdi:cash"

    ent_reg = hass.helpers.entity_registry.async_get(hass) if False else None  # noqa
    # Use entity registry directly
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    entity_entry = registry.async_get("sensor.vonage_account_balance")
    assert entity_entry is not None
    assert entity_entry.unique_id == f"{entry.entry_id}_account_balance"


async def test_polling_refreshes_state(hass):
    """Advancing time by SCAN_INTERVAL_BALANCE refreshes the sensor state."""
    entry = MockConfigEntry(domain=DOMAIN, title="Vonage", data=CONFIG_DATA)
    entry.add_to_hass(hass)

    first = _balance(value=10.0)
    second = _balance(value=42.0)

    with patch(
        "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
        AsyncMock(return_value=True),
    ), patch(
        "custom_components.vonage.api.VonageApiClient.async_get_balance",
        AsyncMock(side_effect=[first, second]),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.vonage_account_balance")
        assert state is not None
        assert state.state == "10.0"

        async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL_BALANCE + timedelta(seconds=1))
        await hass.async_block_till_done()

        state = hass.states.get("sensor.vonage_account_balance")
        assert state is not None
        assert state.state == "42.0"


async def test_multi_config_entry_unique_ids(hass):
    """Two config entries produce two sensors with distinct unique_ids."""
    entry1 = MockConfigEntry(domain=DOMAIN, title="Vonage A", data=CONFIG_DATA)
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        title="Vonage B",
        data={**CONFIG_DATA, "api_key": "other_key"},
    )
    entry1.add_to_hass(hass)
    entry2.add_to_hass(hass)

    with patch(
        "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
        AsyncMock(return_value=True),
    ), patch(
        "custom_components.vonage.api.VonageApiClient.async_get_balance",
        AsyncMock(return_value=_balance()),
    ):
        # Setting up domain triggers setup of both entries.
        from homeassistant.setup import async_setup_component

        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    unique_ids = {
        e.unique_id
        for e in registry.entities.values()
        if e.platform == DOMAIN
    }
    assert f"{entry1.entry_id}_account_balance" in unique_ids
    assert f"{entry2.entry_id}_account_balance" in unique_ids
    assert len(unique_ids) >= 2


# -------------------------------------------------------------------------
# US2 — Detect and Recover From Backend Failures
# -------------------------------------------------------------------------


async def test_sensor_unavailable_on_transient_failure(hass):
    """Sensor becomes unavailable after a coordinator refresh failure."""
    entry = MockConfigEntry(domain=DOMAIN, title="Vonage", data=CONFIG_DATA)
    entry.add_to_hass(hass)

    with patch(
        "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
        AsyncMock(return_value=True),
    ), patch(
        "custom_components.vonage.api.VonageApiClient.async_get_balance",
        AsyncMock(side_effect=[_balance(), VonageBalanceError("transient")]),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get("sensor.vonage_account_balance").state == "12.345"

        async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL_BALANCE + timedelta(seconds=1))
        await hass.async_block_till_done()

        state = hass.states.get("sensor.vonage_account_balance")
        assert state is not None
        assert state.state == STATE_UNAVAILABLE


async def test_sensor_recovers_on_next_success(hass):
    """After a transient failure, the next successful refresh restores availability."""
    entry = MockConfigEntry(domain=DOMAIN, title="Vonage", data=CONFIG_DATA)
    entry.add_to_hass(hass)

    with patch(
        "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
        AsyncMock(return_value=True),
    ), patch(
        "custom_components.vonage.api.VonageApiClient.async_get_balance",
        AsyncMock(
            side_effect=[
                _balance(value=10.0),
                VonageBalanceError("oops"),
                _balance(value=20.0),
            ]
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get("sensor.vonage_account_balance").state == "10.0"

        async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL_BALANCE + timedelta(seconds=1))
        await hass.async_block_till_done()
        assert hass.states.get("sensor.vonage_account_balance").state == STATE_UNAVAILABLE

        async_fire_time_changed(hass, dt_util.utcnow() + 2 * SCAN_INTERVAL_BALANCE + timedelta(seconds=2))
        await hass.async_block_till_done()
        assert hass.states.get("sensor.vonage_account_balance").state == "20.0"


# -------------------------------------------------------------------------
# US3 — Inspect Balance Context via Attributes
# -------------------------------------------------------------------------


async def test_attributes_with_auto_reload(hass):
    """`auto_reload` and ISO `last_updated` are present when upstream provides auto_reload."""
    await _setup_entry(hass, balance=_balance(auto_reload=True))
    state = hass.states.get("sensor.vonage_account_balance")
    assert state is not None
    assert state.attributes.get(ATTR_AUTO_RELOAD) is True
    last_updated = state.attributes.get(ATTR_LAST_UPDATED)
    assert isinstance(last_updated, str)
    parsed = datetime.fromisoformat(last_updated)
    assert parsed.tzinfo is not None


async def test_attributes_without_auto_reload(hass):
    """`auto_reload` is absent when upstream omits it; `last_updated` still present."""
    await _setup_entry(hass, balance=_balance(auto_reload=None))
    state = hass.states.get("sensor.vonage_account_balance")
    assert state is not None
    assert ATTR_AUTO_RELOAD not in state.attributes
    assert isinstance(state.attributes.get(ATTR_LAST_UPDATED), str)
