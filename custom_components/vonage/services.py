"""Services for Vonage integration."""
import logging
from typing import Optional

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import VonageApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_MAKE_CALL = "make_call"

# Service schema for vonage.make_call
MAKE_CALL_SCHEMA = vol.Schema({
    vol.Required("to"): cv.string,
    vol.Optional("text"): cv.string,
    vol.Optional("language"): cv.string,
    vol.Optional("style"): vol.Coerce(int),
    vol.Optional("dtmf_answer"): cv.string,
    vol.Optional("dtmfAnswer"): cv.string,
})


async def async_setup_services(hass: HomeAssistant, api_client: VonageApiClient) -> None:
    """Set up services for Vonage integration."""
    
    async def async_handle_make_call(call: ServiceCall) -> None:
        """Handle the vonage.make_call service call."""
        to: str = call.data["to"]
        text: str = call.data.get("text", "Hello from Home Assistant")
        language: Optional[str] = call.data.get("language")
        style: Optional[int] = call.data.get("style")
        dtmf_answer: Optional[str] = call.data.get("dtmf_answer")
        if dtmf_answer is None:
            dtmf_answer = call.data.get("dtmfAnswer")
        
        # Check if Voice API is configured
        if not api_client.application_id or not api_client.private_key:
            raise HomeAssistantError(
                "Voice API not configured. Please add Application ID and Private Key in integration settings."
            )
        
        # Use defaults from config entry if not provided
        if language is None:
            # Get default from config entry stored in hass.data
            # Find the config entry for this API client
            for entry_id, client in hass.data.get(DOMAIN, {}).items():
                if client == api_client:
                    config_entry = hass.config_entries.async_get_entry(entry_id)
                    if config_entry:
                        language = config_entry.data.get("default_language", "en-US")
                    break
            else:
                language = "en-US"  # Fallback
        
        if style is None:
            # Get default from config entry
            for entry_id, client in hass.data.get(DOMAIN, {}).items():
                if client == api_client:
                    config_entry = hass.config_entries.async_get_entry(entry_id)
                    if config_entry:
                        style = config_entry.data.get("default_voice_style", 0)
                    break
            else:
                style = 0  # Fallback
        
        # Ensure we have valid values (should never be None at this point)
        final_language: str = language if language is not None else "en-US"
        final_style: int = style if style is not None else 0
        
        try:
            response = await api_client.make_call(
                to=to,
                text=text,
                language=final_language,
                style=final_style,
                dtmf_answer=dtmf_answer,
            )
            _LOGGER.info(
                "Voice call initiated successfully. Call UUID: %s, Status: %s",
                response.uuid,
                response.status
            )
        except Exception as err:
            _LOGGER.error("Failed to make voice call to %s: %s", to, err)
            raise
    
    # Register the service
    hass.services.async_register(
        DOMAIN,
        SERVICE_MAKE_CALL,
        async_handle_make_call,
        schema=MAKE_CALL_SCHEMA,
    )
    _LOGGER.debug("Registered vonage.make_call service")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for Vonage integration."""
    hass.services.async_remove(DOMAIN, SERVICE_MAKE_CALL)
    _LOGGER.debug("Unregistered vonage.make_call service")