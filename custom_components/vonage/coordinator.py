"""DataUpdateCoordinator for the Vonage account balance sensor."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AccountBalance, VonageApiClient, VonageBalanceError
from .const import SCAN_INTERVAL_BALANCE

_LOGGER = logging.getLogger(__name__)


class VonageBalanceCoordinator(DataUpdateCoordinator[AccountBalance]):
    """Coordinator that polls Vonage for the account balance."""

    def __init__(self, hass: HomeAssistant, api_client: VonageApiClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Vonage account balance",
            update_interval=SCAN_INTERVAL_BALANCE,
        )
        self.api_client = api_client

    async def _async_update_data(self) -> AccountBalance:
        """Fetch the latest balance from Vonage."""
        try:
            return await self.api_client.async_get_balance()
        except ConfigEntryAuthFailed:
            # Propagate so HA core triggers re-authentication.
            raise
        except VonageBalanceError as err:
            # Wrap as UpdateFailed; do not propagate raw exception args that
            # could carry credentials.
            raise UpdateFailed(f"Vonage balance update failed: {type(err).__name__}") from err
        except Exception as err:  # noqa: BLE001 — defensive net
            raise UpdateFailed(
                f"Vonage balance update failed: {type(err).__name__}"
            ) from err
