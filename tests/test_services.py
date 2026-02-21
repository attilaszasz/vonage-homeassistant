"""Test for Vonage services."""
import pytest
from unittest.mock import AsyncMock, Mock

from homeassistant.exceptions import HomeAssistantError

from custom_components.vonage.api import VonageApiClient, VoiceCallResponse
from custom_components.vonage.services import async_setup_services, SERVICE_MAKE_CALL
from custom_components.vonage.const import DOMAIN


class TestVonageServices:
    """Test Vonage services."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api_client = AsyncMock(spec=VonageApiClient)
        self.api_client.application_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        self.api_client.private_key = "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"

    async def test_make_call_service_setup(self, hass):
        """Test that make_call service is registered correctly."""
        await async_setup_services(hass, self.api_client)
        
        # Verify service is registered
        assert hass.services.has_service(DOMAIN, SERVICE_MAKE_CALL)

    async def test_make_call_success(self, hass):
        """Test successful make_call service call."""
        # Mock successful call response
        self.api_client.make_call.return_value = VoiceCallResponse(
            uuid="aaaaaaaa-bbbb-cccc-dddd-000000000000",
            status="started"
        )
        
        # Set up the service
        await async_setup_services(hass, self.api_client)
        
        # Store API client in hass.data for default language lookup
        hass.data[DOMAIN] = {"test_entry": self.api_client}
        
        # Mock config entry
        mock_entry = Mock()
        mock_entry.data = {"default_language": "en-GB", "default_voice_style": 1}
        hass.config_entries.async_get_entry = Mock(return_value=mock_entry)
        
        # Call the service
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MAKE_CALL,
            {
                "to": "+14155550101",
                "text": "Test voice message",
                "language": "en-US",
                "style": 0
            },
            blocking=True
        )
        
        # Verify API was called correctly
        self.api_client.make_call.assert_called_once_with(
            to="+14155550101",
            text="Test voice message",
            language="en-US",
            style=0,
            dtmf_answer=None,
        )

    async def test_make_call_with_defaults(self, hass):
        """Test make_call service using default language and style."""
        self.api_client.make_call.return_value = VoiceCallResponse(
            uuid="aaaaaaaa-bbbb-cccc-dddd-000000000000",
            status="started"
        )
        
        await async_setup_services(hass, self.api_client)
        
        # Store API client in hass.data
        hass.data[DOMAIN] = {"test_entry": self.api_client}
        
        # Mock config entry with defaults
        mock_entry = Mock()
        mock_entry.data = {"default_language": "es-ES", "default_voice_style": 2}
        hass.config_entries.async_get_entry = Mock(return_value=mock_entry)
        
        # Call service without language/style parameters
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MAKE_CALL,
            {
                "to": "+14155550101",
                "text": "Mensaje de prueba"
            },
            blocking=True
        )
        
        # Should use defaults from config entry
        self.api_client.make_call.assert_called_once_with(
            to="+14155550101",
            text="Mensaje de prueba",
            language="es-ES",
            style=2,
            dtmf_answer=None,
        )

    async def test_make_call_voice_not_configured(self, hass):
        """Test make_call service when Voice not configured."""
        # Create API client without Voice credentials
        api_client_no_voice = AsyncMock(spec=VonageApiClient)
        api_client_no_voice.application_id = None
        api_client_no_voice.private_key = None
        
        await async_setup_services(hass, api_client_no_voice)
        
        # Attempt to call the service
        with pytest.raises(HomeAssistantError, match="Voice API not configured"):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_MAKE_CALL,
                {
                    "to": "+14155550101",
                    "text": "Test message"
                },
                blocking=True
            )
        
        # API should not have been called
        api_client_no_voice.make_call.assert_not_called()

    async def test_make_call_api_error(self, hass):
        """Test make_call service when API call fails."""
        # Mock API error
        self.api_client.make_call.side_effect = HomeAssistantError("Rate limit exceeded")
        
        await async_setup_services(hass, self.api_client)
        
        # Store API client in hass.data
        hass.data[DOMAIN] = {"test_entry": self.api_client}
        
        # Mock config entry
        mock_entry = Mock()
        mock_entry.data = {"default_language": "en-US", "default_voice_style": 0}
        hass.config_entries.async_get_entry = Mock(return_value=mock_entry)
        
        # Attempt to call the service
        with pytest.raises(HomeAssistantError, match="Rate limit exceeded"):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_MAKE_CALL,
                {
                    "to": "+14155550101",
                    "text": "Test message"
                },
                blocking=True
            )
        
        # Verify API was called
        self.api_client.make_call.assert_called_once()

    async def test_make_call_language_override(self, hass):
        """Test make_call with language override."""
        self.api_client.make_call.return_value = VoiceCallResponse(
            uuid="aaaaaaaa-bbbb-cccc-dddd-000000000000",
            status="started"
        )
        
        await async_setup_services(hass, self.api_client)
        
        # Store API client in hass.data
        hass.data[DOMAIN] = {"test_entry": self.api_client}
        
        # Mock config entry with different defaults
        mock_entry = Mock()
        mock_entry.data = {"default_language": "en-US", "default_voice_style": 0}
        hass.config_entries.async_get_entry = Mock(return_value=mock_entry)
        
        # Call service with language override
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MAKE_CALL,
            {
                "to": "+14155550101",
                "text": "Bonjour, ceci est un test",
                "language": "fr-FR",  # Override default
                "style": 1  # Override default
            },
            blocking=True
        )
        
        # Should use overridden values
        self.api_client.make_call.assert_called_once_with(
            to="+14155550101",
            text="Bonjour, ceci est un test",
            language="fr-FR",
            style=1,
            dtmf_answer=None,
        )

    async def test_make_call_with_dtmf_answer(self, hass):
        """Test make_call service passes dtmfAnswer to API client."""
        self.api_client.make_call.return_value = VoiceCallResponse(
            uuid="aaaaaaaa-bbbb-cccc-dddd-000000000000",
            status="started"
        )

        await async_setup_services(hass, self.api_client)
        hass.data[DOMAIN] = {"test_entry": self.api_client}

        mock_entry = Mock()
        mock_entry.data = {"default_language": "en-US", "default_voice_style": 0}
        hass.config_entries.async_get_entry = Mock(return_value=mock_entry)

        await hass.services.async_call(
            DOMAIN,
            SERVICE_MAKE_CALL,
            {
                "to": "+14155550101",
                "text": "Test voice message",
                "dtmfAnswer": "p*123#",
            },
            blocking=True,
        )

        self.api_client.make_call.assert_called_once_with(
            to="+14155550101",
            text="Test voice message",
            language="en-US",
            style=0,
            dtmf_answer="p*123#",
        )

    async def test_make_call_without_dtmf_answer(self, hass):
        """Test make_call service sends None dtmf_answer when omitted."""
        self.api_client.make_call.return_value = VoiceCallResponse(
            uuid="aaaaaaaa-bbbb-cccc-dddd-000000000000",
            status="started"
        )

        await async_setup_services(hass, self.api_client)
        hass.data[DOMAIN] = {"test_entry": self.api_client}

        mock_entry = Mock()
        mock_entry.data = {"default_language": "en-US", "default_voice_style": 0}
        hass.config_entries.async_get_entry = Mock(return_value=mock_entry)

        await hass.services.async_call(
            DOMAIN,
            SERVICE_MAKE_CALL,
            {
                "to": "+14155550101",
                "text": "Test voice message",
            },
            blocking=True,
        )

        self.api_client.make_call.assert_called_once_with(
            to="+14155550101",
            text="Test voice message",
            language="en-US",
            style=0,
            dtmf_answer=None,
        )