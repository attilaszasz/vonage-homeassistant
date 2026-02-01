"""Test the complete Vonage integration setup."""
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant.setup import async_setup_component

from custom_components.vonage.const import DOMAIN
from custom_components.vonage.api import VoiceCallResponse


async def test_vonage_integration_setup(hass):
    """Test the full integration setup and SMS flow."""
    # Mock the Vonage API client
    with patch("custom_components.vonage.api.VonageApiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.test_sms_credentials.return_value = True
        mock_client_class.return_value = mock_client
        
        # Set up the integration with a config entry
        config_entry_data = {
            "api_key": "test_key", 
            "api_secret": "test_secret",
            "phone_number": "+14155550100",
        }
        
        # Mock config entry
        from homeassistant.config_entries import ConfigEntry
        config_entry = ConfigEntry(
            domain=DOMAIN,
            title="Vonage",
            data=config_entry_data,
            entry_id="test_entry",
        )
        
        # Add config entry to hass
        hass.config_entries._entries[config_entry.entry_id] = config_entry
        
        # Set up the component
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        
        # Verify the integration is set up correctly
        assert DOMAIN in hass.data
        assert config_entry.entry_id in hass.data[DOMAIN]
        assert hass.data[DOMAIN][config_entry.entry_id] == mock_client
        
        # Verify API client was created with correct parameters
        mock_client_class.assert_called_once_with(
            api_key="test_key",
            api_secret="test_secret", 
            phone_number="+14155550100",
            application_id=None,
            private_key=None,
        )
        
        # Verify credentials were tested
        mock_client.test_sms_credentials.assert_called_once()


async def test_vonage_integration_setup_with_voice(hass):
    """Test the full integration setup with Voice credentials."""
    with patch("custom_components.vonage.api.VonageApiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.test_sms_credentials.return_value = True
        mock_client_class.return_value = mock_client
        
        config_entry_data = {
            "api_key": "test_key",
            "api_secret": "test_secret", 
            "phone_number": "+14155550100",
            "application_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            "default_language": "en-GB",
            "default_voice_style": 1,
        }
        
        from homeassistant.config_entries import ConfigEntry
        config_entry = ConfigEntry(
            domain=DOMAIN,
            title="Vonage",
            data=config_entry_data, 
            entry_id="test_entry",
        )
        
        hass.config_entries._entries[config_entry.entry_id] = config_entry
        
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        
        # Verify API client was created with Voice credentials
        mock_client_class.assert_called_once_with(
            api_key="test_key",
            api_secret="test_secret",
            phone_number="+14155550100", 
            application_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            private_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        )


async def test_vonage_voice_service_call(hass):
    """Test the complete Voice service call flow."""
    with patch("custom_components.vonage.api.VonageApiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.test_sms_credentials.return_value = True
        mock_client.application_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        mock_client.private_key = "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
        mock_client.make_call.return_value = VoiceCallResponse(
            uuid="call-uuid-12345",
            status="started"
        )
        mock_client_class.return_value = mock_client
        
        # Set up config entry with Voice credentials
        config_entry_data = {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "phone_number": "+14155550100",
            "application_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            "default_language": "en-US",
            "default_voice_style": 0,
        }
        
        from homeassistant.config_entries import ConfigEntry
        config_entry = ConfigEntry(
            domain=DOMAIN,
            title="Vonage",
            data=config_entry_data,
            entry_id="test_entry",
        )
        
        hass.config_entries._entries[config_entry.entry_id] = config_entry
        
        # Set up the component
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        
        # Verify the voice service is available
        from custom_components.vonage.services import SERVICE_MAKE_CALL
        assert hass.services.has_service(DOMAIN, SERVICE_MAKE_CALL)
        
        # Call the voice service
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MAKE_CALL,
            {
                "target": "+14155550101",
                "message": "Test voice message from Home Assistant",
                "language": "en-GB",
                "style": 1
            },
            blocking=True
        )
        
        # Verify the API was called correctly
        mock_client.make_call.assert_called_once_with(
            to="+14155550101",
            text="Test voice message from Home Assistant",
            language="en-GB",
            style=1
        )