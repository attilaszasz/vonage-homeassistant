"""Support for Vonage SMS notifications."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.notify import (
    ATTR_TARGET,
    BaseNotificationService,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .api import VonageApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> Optional[VonageSmsNotificationService]:
    """Get the Vonage SMS notification service."""
    if discovery_info is None:
        return None

    # Get the API client from the config entry data
    api_client = discovery_info.get("api_client")
    if api_client is None:
        _LOGGER.error("No API client found in discovery info")
        return None

    return VonageSmsNotificationService(api_client)


class VonageSmsNotificationService(BaseNotificationService):
    """Implementation of a notification service for Vonage SMS."""

    def __init__(self, api_client: VonageApiClient) -> None:
        """Initialize the service."""
        self.api_client = api_client

    async def async_send_message(
        self, message: str = "", **kwargs: Any
    ) -> None:
        """Send a message to specified targets via SMS."""
        targets = kwargs.get(ATTR_TARGET, [])
        
        # Ensure targets is a list
        if isinstance(targets, str):
            targets = [targets]
        
        if not targets:
            _LOGGER.error("No targets specified for SMS notification")
            raise HomeAssistantError("No targets specified for SMS notification")
        
        if not message:
            _LOGGER.error("Empty message not allowed for SMS notification")
            raise HomeAssistantError("Empty message not allowed for SMS notification")

        # Send SMS to each target
        for target in targets:
            try:
                await self.api_client.send_sms(to=target, text=message)
                _LOGGER.debug("SMS sent successfully to %s", target)
            except Exception as err:
                _LOGGER.error("Failed to send SMS to %s: %s", target, err)
                raise HomeAssistantError(f"Failed to send SMS to {target}: {err}")