"""The Vonage integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import discovery

from .api import VonageApiClient
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_PHONE_NUMBER,
    CONF_APPLICATION_ID,
    CONF_PRIVATE_KEY,
)
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.NOTIFY]


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
    
    # Store API client in hass data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = api_client
    
    # Set up services (vonage.make_call)
    await async_setup_services(hass, api_client)
    
    # Set up notify platform with discovery
    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {"api_client": api_client},
            {"api_client": api_client},
        )
    )
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Vonage integration")
    
    # Unload services
    await async_unload_services(hass)
    
    # Remove stored data
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Remove domain data if no more config entries
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    
    return True