"""Test for Vonage API client."""
import pytest
import types
from unittest.mock import Mock, patch

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

    async def test_send_sms_success(self):
        """Test successful SMS sending."""
        fake_message = types.SimpleNamespace(status="0", message_id="0A00000012345", error_text=None)
        fake_response = types.SimpleNamespace(messages=[fake_message])
        fake_client = Mock()
        fake_client.sms.send.return_value = fake_response
        fake_vonage_cls = Mock(return_value=fake_client)
        fake_auth_cls = Mock()
        fake_vonage_module = types.SimpleNamespace(Vonage=fake_vonage_cls, Auth=fake_auth_cls)
        
        with patch.dict("sys.modules", {"vonage": fake_vonage_module}):
            result = await self.client.send_sms("+14155550101", "Test message")
        
        assert isinstance(result, SmsResponse)
        assert result.message_id == "0A00000012345"
        assert result.status == "delivered"
        
        # Verify SDK was called correctly
        fake_auth_cls.assert_called_once_with(api_key="test_key", api_secret="test_secret")
        fake_client.sms.send.assert_called_once_with({
            "from_": "+14155550100",
            "to": "+14155550101", 
            "text": "Test message"
        })

    async def test_send_sms_invalid_credentials(self):
        """Test SMS with invalid credentials."""
        fake_message = types.SimpleNamespace(status="4", message_id="", error_text="Invalid credentials")
        fake_response = types.SimpleNamespace(messages=[fake_message])
        fake_client = Mock()
        fake_client.sms.send.return_value = fake_response
        fake_vonage_cls = Mock(return_value=fake_client)
        fake_auth_cls = Mock()
        fake_vonage_module = types.SimpleNamespace(Vonage=fake_vonage_cls, Auth=fake_auth_cls)
        
        with patch.dict("sys.modules", {"vonage": fake_vonage_module}):
            with pytest.raises(ConfigEntryAuthFailed):
                await self.client.send_sms("+14155550101", "Test message")

    async def test_send_sms_rate_limit(self):
        """Test SMS with rate limit exceeded."""
        fake_message = types.SimpleNamespace(status="1", message_id="", error_text="Rate limit exceeded")
        fake_response = types.SimpleNamespace(messages=[fake_message])
        fake_client = Mock()
        fake_client.sms.send.return_value = fake_response
        fake_vonage_cls = Mock(return_value=fake_client)
        fake_auth_cls = Mock()
        fake_vonage_module = types.SimpleNamespace(Vonage=fake_vonage_cls, Auth=fake_auth_cls)
        
        with patch.dict("sys.modules", {"vonage": fake_vonage_module}):
            with pytest.raises(HomeAssistantError, match="Rate limit exceeded"):
                await self.client.send_sms("+14155550101", "Test message")

    async def test_make_call_success(self):
        """Test successful voice call."""
        fake_response = types.SimpleNamespace(
            uuid="aaaaaaaa-bbbb-cccc-dddd-000000000000",
            status="started"
        )
        fake_client = Mock()
        fake_client.voice.create_call.return_value = fake_response
        fake_vonage_cls = Mock(return_value=fake_client)
        fake_auth_cls = Mock()
        fake_vonage_module = types.SimpleNamespace(Vonage=fake_vonage_cls, Auth=fake_auth_cls)
        
        with patch.dict("sys.modules", {"vonage": fake_vonage_module}):
            result = await self.client.make_call("+14155550101", "Test message", "en-US", 0)
        
        assert isinstance(result, VoiceCallResponse)
        assert result.uuid == "aaaaaaaa-bbbb-cccc-dddd-000000000000"
        assert result.status == "started"
        
        # Verify SDK was called correctly
        fake_auth_cls.assert_called_once_with(
            application_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            private_key="-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----"
        )
        expected_call_data = {
            "to": [{"type": "phone", "number": "14155550101"}],
            "from": {"type": "phone", "number": "14155550100"},
            "ncco": [{
                "action": "talk",
                "text": "Test message",
                "language": "en-US", 
                "style": 0
            }]
        }
        fake_client.voice.create_call.assert_called_once_with(expected_call_data)

    async def test_make_call_voice_not_configured(self):
        """Test voice call when Voice not configured."""
        client_no_voice = VonageApiClient(
            api_key="test_key",
            api_secret="test_secret",
            phone_number="+14155550100"
        )
        
        with pytest.raises(HomeAssistantError, match="Voice API not configured"):
            await client_no_voice.make_call("+14155550101", "Test message")

    def test_make_call_sync_includes_dtmf_answer_in_to_endpoint(self):
        """Test dtmfAnswer is included in to endpoint when provided."""
        fake_response = Mock()
        fake_response.uuid = "aaaaaaaa-bbbb-cccc-dddd-000000000000"
        fake_response.status = "started"

        fake_client = Mock()
        fake_client.voice.create_call.return_value = fake_response
        fake_vonage_cls = Mock(return_value=fake_client)
        fake_auth_cls = Mock()
        fake_vonage_module = types.SimpleNamespace(Vonage=fake_vonage_cls, Auth=fake_auth_cls)

        with patch.dict("sys.modules", {"vonage": fake_vonage_module}):
            self.client._make_call_sync("+14155550101", "Test message", "en-US", 0, "p*123#")

        call_payload = fake_client.voice.create_call.call_args.args[0]
        assert call_payload["to"][0]["dtmfAnswer"] == "p*123#"

    def test_make_call_sync_omits_dtmf_answer_when_not_provided(self):
        """Test dtmfAnswer is omitted from to endpoint when absent."""
        fake_response = Mock()
        fake_response.uuid = "aaaaaaaa-bbbb-cccc-dddd-000000000000"
        fake_response.status = "started"

        fake_client = Mock()
        fake_client.voice.create_call.return_value = fake_response
        fake_vonage_cls = Mock(return_value=fake_client)
        fake_auth_cls = Mock()
        fake_vonage_module = types.SimpleNamespace(Vonage=fake_vonage_cls, Auth=fake_auth_cls)

        with patch.dict("sys.modules", {"vonage": fake_vonage_module}):
            self.client._make_call_sync("+14155550101", "Test message", "en-US", 0)

        call_payload = fake_client.voice.create_call.call_args.args[0]
        assert "dtmfAnswer" not in call_payload["to"][0]

    def test_make_call_sync_omits_dtmf_answer_when_empty_string(self):
        """Test dtmfAnswer is omitted from to endpoint when empty."""
        fake_response = Mock()
        fake_response.uuid = "aaaaaaaa-bbbb-cccc-dddd-000000000000"
        fake_response.status = "started"

        fake_client = Mock()
        fake_client.voice.create_call.return_value = fake_response
        fake_vonage_cls = Mock(return_value=fake_client)
        fake_auth_cls = Mock()
        fake_vonage_module = types.SimpleNamespace(Vonage=fake_vonage_cls, Auth=fake_auth_cls)

        with patch.dict("sys.modules", {"vonage": fake_vonage_module}):
            self.client._make_call_sync("+14155550101", "Test message", "en-US", 0, "")

        call_payload = fake_client.voice.create_call.call_args.args[0]
        assert "dtmfAnswer" not in call_payload["to"][0]