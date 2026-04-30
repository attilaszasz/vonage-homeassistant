"""The Vonage integration.

Author: Attila Szasz
"""
import logging
from typing import TypedDict
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.components.notify import ATTR_TARGET, BaseNotificationService

from .api import VonageApiClient
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_PHONE_NUMBER,
    CONF_APPLICATION_ID,
    CONF_PRIVATE_KEY,
)
from .coordinator import VonageBalanceCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


class VonageEntryData(TypedDict):
    """Per-config-entry runtime data stored under hass.data[DOMAIN][entry_id]."""

    api_client: VonageApiClient
    balance_coordinator: VonageBalanceCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Vonage from a config entry."""
    _LOGGER.debug("Setting up Vonage integration")
    
    # Create API client from config entry data
    api_client = VonageApiClient(
        api_key=entry.data[CONF_API_KEY],
        api_secret=entry.data[CONF_API_SECRET],
        phone_number=entry.data[CONF_PHONE_NUMBER],
        application_id=entry.data.get(CONF_APPLICATION_ID),
        private_key=entry.data.get(CONF_PRIVATE_KEY),
    )
    
    # Test connectivity
    try:
        if not await api_client.test_sms_credentials():
            raise ConfigEntryNotReady("Unable to connect to Vonage API")
    except Exception as err:
        _LOGGER.error("Failed to connect to Vonage API: %s", err)
        raise ConfigEntryNotReady("Unable to connect to Vonage API") from err

    # Create the balance coordinator and perform first refresh. This will
    # raise ConfigEntryNotReady (from UpdateFailed) or ConfigEntryAuthFailed
    # if Vonage rejects the request, preventing entity creation until success.
    balance_coordinator = VonageBalanceCoordinator(hass, api_client)
    await balance_coordinator.async_config_entry_first_refresh()

    # Store API client + coordinator in hass data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api_client": api_client,
        "balance_coordinator": balance_coordinator,
    }
    
    # Set up services (vonage.make_call and notify.vonage_sms)
    await async_setup_services(hass, api_client)
    await async_setup_sms_notification(hass, api_client)
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Vonage integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Unload services
    await async_unload_services(hass)
    hass.services.async_remove("notify", "vonage_sms")
    
    # Remove stored data
    if unload_ok and DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Remove domain data if no more config entries
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    
    return unload_ok


async def async_setup_sms_notification(hass: HomeAssistant, api_client: VonageApiClient) -> None:
    """Set up SMS notification service."""
    
    class VonageSmsNotificationService(BaseNotificationService):
        """Implementation of a notification service for Vonage SMS."""

        def __init__(self, api_client: VonageApiClient) -> None:
            """Initialize the service."""
            self.api_client = api_client

        async def async_send_message(self, message: str = "", **kwargs) -> None:
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
                    await api_client.send_sms(to=target, text=message)
                    _LOGGER.debug("SMS sent successfully to %s", target)
                except Exception as err:
                    _LOGGER.error("Failed to send SMS to %s: %s", target, err)
                    raise HomeAssistantError(f"Failed to send SMS to {target}: {err}")
    
    # Create the notification service
    notify_service = VonageSmsNotificationService(api_client)
    
    # Register the service
    service_schema = {
        vol.Required("message"): str,
        vol.Optional(ATTR_TARGET): vol.Any(str, [str]),
    }
    
    async def vonage_sms_notify(service_call):
        """Handle notify service call."""
        message = service_call.data["message"]
        target = service_call.data.get(ATTR_TARGET, [])
        await notify_service.async_send_message(message, **{ATTR_TARGET: target})
    
    hass.services.async_register(
        "notify",
        "vonage_sms", 
        vonage_sms_notify,
        schema=vol.Schema(service_schema)
    )