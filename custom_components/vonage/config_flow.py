"""Config flow for Vonage integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
try:
    from homeassistant.config_entries import ConfigFlowResult  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - HA < 2024.4 fallback
    from homeassistant.data_entry_flow import FlowResult as ConfigFlowResult  # type: ignore[assignment]
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


class VonageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Vonage."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def _async_validate_user_input(
        self, user_input: Dict[str, Any]
    ) -> dict[str, str]:
        """Validate Vonage SMS and optional Voice credentials."""
        errors: dict[str, str] = {}

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
            elif user_input.get(CONF_APPLICATION_ID) and user_input.get(CONF_PRIVATE_KEY):
                voice_valid = await api_client.test_voice_credentials()
                if not voice_valid:
                    errors["base"] = "invalid_auth"
            elif user_input.get(CONF_APPLICATION_ID) or user_input.get(CONF_PRIVATE_KEY):
                errors["base"] = "voice_incomplete"
        except Exception as err:
            _LOGGER.error("Error validating credentials: %s", err)
            errors["base"] = "cannot_connect"

        return errors

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            errors = await self._async_validate_user_input(user_input)
            if not errors:
                return self.async_create_entry(
                    title="Vonage",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/attila-vonage/vonage-homeassistant"
            },
        )

    async def async_step_reauth(
        self, entry_data: Dict[str, Any]
    ) -> ConfigFlowResult:
        """Trigger re-authentication flow when credentials become invalid."""
        self._reauth_entry_id = self.context.get("entry_id")
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> ConfigFlowResult:
        """Re-authentication confirmation step.

        Re-uses the user-input form so the user can update API key/secret.
        """
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={},
            )

        errors = await self._async_validate_user_input(user_input)
        if errors:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
            )

        entry_id = getattr(self, "_reauth_entry_id", None) or self.context.get("entry_id")
        if entry_id is None:
            return self.async_abort(reason="reauth_failed")

        entry = self.hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            return self.async_abort(reason="reauth_failed")

        self.hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, **user_input},
        )
        await self.hass.config_entries.async_reload(entry.entry_id)
        return self.async_abort(reason="reauth_successful")
