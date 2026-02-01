"""Config flow for Vonage integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_PHONE_NUMBER,
    CONF_APPLICATION_ID,
    CONF_PRIVATE_KEY,
    CONF_DEFAULT_LANGUAGE,
    CONF_DEFAULT_VOICE_STYLE,
)
from .api import VonageApiClient

_LOGGER = logging.getLogger(__name__)

# Schema for user input
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_API_SECRET): cv.string,
    vol.Required(CONF_PHONE_NUMBER): cv.string,
    vol.Optional(CONF_APPLICATION_ID): cv.string,
    vol.Optional(CONF_PRIVATE_KEY): cv.string,
    vol.Optional(CONF_DEFAULT_LANGUAGE, default="en-US"): cv.string,
    vol.Optional(CONF_DEFAULT_VOICE_STYLE, default=0): vol.Coerce(int),
})


class VonageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]  # type: ignore[call-arg]
    """Handle a config flow for Vonage."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Validate SMS credentials (required)
            api_client = VonageApiClient(
                api_key=user_input[CONF_API_KEY],
                api_secret=user_input[CONF_API_SECRET],
                phone_number=user_input[CONF_PHONE_NUMBER],
                application_id=user_input.get(CONF_APPLICATION_ID),
                private_key=user_input.get(CONF_PRIVATE_KEY),
            )
            
            try:
                sms_valid = await api_client.test_sms_credentials()
                if not sms_valid:
                    errors["base"] = "invalid_auth"
                else:
                    # If Voice credentials provided, validate them too
                    if user_input.get(CONF_APPLICATION_ID) and user_input.get(CONF_PRIVATE_KEY):
                        voice_valid = await api_client.test_voice_credentials()
                        if not voice_valid:
                            errors["base"] = "invalid_auth"
                    # Validate that if one Voice credential is provided, both are provided
                    elif user_input.get(CONF_APPLICATION_ID) or user_input.get(CONF_PRIVATE_KEY):
                        errors["base"] = "voice_incomplete"
                    
                    if not errors:
                        # Create config entry
                        return self.async_create_entry(
                            title="Vonage",
                            data=user_input
                        )
            except Exception as err:
                _LOGGER.error("Error validating credentials: %s", err)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/attila-vonage/vonage-homeassistant"
            },
        )