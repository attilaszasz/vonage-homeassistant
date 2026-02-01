"""Test for Vonage API client."""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from homeassistant.exceptions import HomeAssistantError, ConfigEntryAuthFailed

from custom_components.vonage.api import VonageApiClient, SmsResponse, VoiceCallResponse


class TestVonageApiClient:
    """Test VonageApiClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = VonageApiClient(
            api_key="test_key",
            api_secret="test_secret", 
            phone_number="+14155550100",
            application_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            private_key="-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----"
        )

    @patch("custom_components.vonage.api.Vonage")
    @patch("custom_components.vonage.api.Auth")
    async def test_send_sms_success(self, mock_auth, mock_vonage):
        """Test successful SMS sending."""
        # Mock SDK response
        mock_vonage_instance = mock_vonage.return_value
        mock_vonage_instance.sms.send.return_value = {
            "status": "0",
            "message-id": "0A00000012345",
        }
        
        result = await self.client.send_sms("+14155550101", "Test message")
        
        assert isinstance(result, SmsResponse)
        assert result.message_id == "0A00000012345"
        assert result.status == "delivered"
        
        # Verify SDK was called correctly
        mock_auth.assert_called_once_with(api_key="test_key", api_secret="test_secret")
        mock_vonage_instance.sms.send.assert_called_once_with({
            "from": "+14155550100",
            "to": "+14155550101", 
            "text": "Test message"
        })

    @patch("custom_components.vonage.api.Vonage")
    @patch("custom_components.vonage.api.Auth")
    async def test_send_sms_invalid_credentials(self, mock_auth, mock_vonage):
        """Test SMS with invalid credentials."""
        mock_vonage_instance = mock_vonage.return_value
        mock_vonage_instance.sms.send.return_value = {
            "status": "4",
            "error-text": "Invalid credentials"
        }
        
        with pytest.raises(ConfigEntryAuthFailed):
            await self.client.send_sms("+14155550101", "Test message")

    @patch("custom_components.vonage.api.Vonage")
    @patch("custom_components.vonage.api.Auth")
    async def test_send_sms_rate_limit(self, mock_auth, mock_vonage):
        """Test SMS with rate limit exceeded."""
        mock_vonage_instance = mock_vonage.return_value
        mock_vonage_instance.sms.send.return_value = {
            "status": "1",
            "error-text": "Rate limit exceeded"
        }
        
        with pytest.raises(HomeAssistantError, match="Rate limit exceeded"):
            await self.client.send_sms("+14155550101", "Test message")

    @patch("custom_components.vonage.api.Vonage")
    @patch("custom_components.vonage.api.Auth")
    async def test_make_call_success(self, mock_auth, mock_vonage):
        """Test successful voice call."""
        mock_vonage_instance = mock_vonage.return_value
        mock_vonage_instance.voice.create_call.return_value = {
            "uuid": "aaaaaaaa-bbbb-cccc-dddd-000000000000",
            "status": "started"
        }
        
        result = await self.client.make_call("+14155550101", "Test message", "en-US", 0)
        
        assert isinstance(result, VoiceCallResponse)
        assert result.uuid == "aaaaaaaa-bbbb-cccc-dddd-000000000000"
        assert result.status == "started"
        
        # Verify SDK was called correctly
        mock_auth.assert_called_once_with(
            application_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            private_key="-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----"
        )
        expected_call_data = {
            "to": [{"type": "phone", "number": "+14155550101"}],
            "from": {"type": "phone", "number": "+14155550100"},
            "ncco": [{
                "action": "talk",
                "text": "Test message",
                "language": "en-US", 
                "style": 0
            }]
        }
        mock_vonage_instance.voice.create_call.assert_called_once_with(expected_call_data)

    async def test_make_call_voice_not_configured(self):
        """Test voice call when Voice not configured."""
        client_no_voice = VonageApiClient(
            api_key="test_key",
            api_secret="test_secret",
            phone_number="+14155550100"
        )
        
        with pytest.raises(HomeAssistantError, match="Voice API not configured"):
            await client_no_voice.make_call("+14155550101", "Test message")