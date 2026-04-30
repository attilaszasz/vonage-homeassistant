"""Tests for VonageBalanceCoordinator."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.vonage.api import AccountBalance, VonageBalanceError
from custom_components.vonage.coordinator import VonageBalanceCoordinator


def _balance(value: float = 12.345) -> AccountBalance:
    return AccountBalance(
        value=value,
        currency="EUR",
        auto_reload=True,
        fetched_at=datetime.now(timezone.utc),
    )


async def test_balance_coordinator_first_refresh_success(hass):
    """Refresh populates `coordinator.data` and `last_update_success`."""
    api_client = AsyncMock()
    api_client.async_get_balance = AsyncMock(return_value=_balance())

    coordinator = VonageBalanceCoordinator(hass, api_client)
    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert coordinator.data is not None
    assert coordinator.data.value == 12.345
    api_client.async_get_balance.assert_awaited_once()


async def test_coordinator_propagates_auth_failed(hass):
    """ConfigEntryAuthFailed must propagate so HA core triggers re-auth."""
    api_client = AsyncMock()
    api_client.async_get_balance = AsyncMock(side_effect=ConfigEntryAuthFailed("401"))
    coordinator = VonageBalanceCoordinator(hass, api_client)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_coordinator_wraps_transient_as_update_failed(hass):
    """Transient/HA errors become UpdateFailed; last_update_success flips to False."""
    api_client = AsyncMock()
    api_client.async_get_balance = AsyncMock(
        side_effect=VonageBalanceError("transient")
    )
    coordinator = VonageBalanceCoordinator(hass, api_client)

    await coordinator.async_refresh()  # does not raise; sets last_update_success
    assert coordinator.last_update_success is False


async def test_coordinator_recovery_after_failure(hass):
    """After a failed refresh, the next successful refresh restores data."""
    api_client = AsyncMock()
    api_client.async_get_balance = AsyncMock(
        side_effect=[VonageBalanceError("nope"), _balance(99.0)]
    )
    coordinator = VonageBalanceCoordinator(hass, api_client)

    await coordinator.async_refresh()
    assert coordinator.last_update_success is False

    await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    assert coordinator.data is not None
    assert coordinator.data.value == 99.0


async def test_coordinator_redacts_exception_args_in_update_failed(hass):
    """UpdateFailed message must not echo raw exception args (e.g., credentials)."""
    api_client = AsyncMock()
    api_client.async_get_balance = AsyncMock(
        side_effect=VonageBalanceError("super-secret-do-not-leak in here")
    )
    coordinator = VonageBalanceCoordinator(hass, api_client)

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert "super-secret-do-not-leak" not in str(exc_info.value)
