"""Test for Vonage API client."""
import pytest
import types
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from homeassistant.exceptions import HomeAssistantError, ConfigEntryAuthFailed

from custom_components.vonage.api import (
    AccountBalance,
    SmsResponse,
    VoiceCallResponse,
    VonageApiClient,
    VonageBalanceError,
)


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

    def test_private_key_is_normalized_on_init(self):
        """Test private key outer whitespace is stripped during initialization."""
        client = VonageApiClient(
            api_key="test_key",
            api_secret="test_secret",
            phone_number="+14155550100",
            application_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            private_key="  -----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----\n",
        )

        assert client.private_key == "-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----"

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
            "from_": {"type": "phone", "number": "14155550100"},
            "ncco": [{
                "action": "talk",
                "text": "Test message",
                "language": "en-US", 
                "style": 0
            }]
        }
        fake_client.voice.create_call.assert_called_once_with(expected_call_data)

    async def test_make_call_uses_normalized_private_key(self):
        """Test runtime voice auth receives the normalized private key."""
        client = VonageApiClient(
            api_key="test_key",
            api_secret="test_secret",
            phone_number="+14155550100",
            application_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            private_key="-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----\n",
        )

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
            await client.make_call("+14155550101", "Test message", "en-US", 0)

        fake_auth_cls.assert_called_once_with(
            application_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            private_key="-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----",
        )

    async def test_test_voice_credentials_uses_normalized_private_key(self):
        """Test voice credential validation uses the normalized private key."""
        client = VonageApiClient(
            api_key="test_key",
            api_secret="test_secret",
            phone_number="+14155550100",
            application_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            private_key="-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----\n",
        )

        with patch("jwt.encode", return_value="token") as mock_encode:
            assert await client.test_voice_credentials() is True

        assert mock_encode.call_args.args[1] == "-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----"

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
        assert call_payload["to"][0]["dtmf_answer"] == "p*123#"

    def test_make_call_sync_omits_dtmf_answer_when_not_provided(self):
        """Test dtmf_answer is omitted from to endpoint when absent."""
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
        assert "dtmf_answer" not in call_payload["to"][0]

    def test_make_call_sync_omits_dtmf_answer_when_empty_string(self):
        """Test dtmf_answer is omitted from to endpoint when empty."""
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
        assert "dtmf_answer" not in call_payload["to"][0]


def _make_vonage_module(get_balance=None, raise_exc=None):
    """Build a fake `vonage` module exposing Vonage/Auth.

    `get_balance` is the value returned by `client.account.get_balance()`.
    `raise_exc` (if set) is raised by `client.account.get_balance()` instead.
    """
    fake_client = Mock()
    if raise_exc is not None:
        fake_client.account.get_balance.side_effect = raise_exc
    else:
        fake_client.account.get_balance.return_value = get_balance
    return types.SimpleNamespace(
        Vonage=Mock(return_value=fake_client),
        Auth=Mock(),
    ), fake_client


class TestVonageApiClientBalance:
    """Tests for `VonageApiClient.async_get_balance` (feature 003)."""

    def setup_method(self):
        self.client = VonageApiClient(
            api_key="test_key",
            api_secret="super-secret-do-not-leak",
            phone_number="+14155550100",
        )

    async def test_async_get_balance_success_with_auto_reload(
        self, mock_balance_response_with_auto_reload
    ):
        """Returns AccountBalance with raw value, uppercased currency, and auto_reload."""
        # Mutate currency to lowercase to verify normalization.
        mock_balance_response_with_auto_reload.currency = "eur"
        fake_module, _ = _make_vonage_module(
            get_balance=mock_balance_response_with_auto_reload
        )

        with patch.dict("sys.modules", {"vonage": fake_module}):
            result = await self.client.async_get_balance()

        assert isinstance(result, AccountBalance)
        assert result.value == 12.345  # raw, no rounding
        assert result.currency == "EUR"
        assert result.auto_reload is True
        assert isinstance(result.fetched_at, datetime)
        assert result.fetched_at.tzinfo is not None
        assert result.fetched_at.utcoffset() == timezone.utc.utcoffset(result.fetched_at)

    async def test_async_get_balance_success_without_auto_reload(
        self, mock_balance_response_no_auto_reload
    ):
        """auto_reload is None when upstream omits the field."""
        fake_module, _ = _make_vonage_module(
            get_balance=mock_balance_response_no_auto_reload
        )

        with patch.dict("sys.modules", {"vonage": fake_module}):
            result = await self.client.async_get_balance()

        assert result.auto_reload is None
        assert result.value == 12.345
        assert result.currency == "EUR"

    async def test_async_get_balance_success_with_sdk_balance_shape_no_currency(self):
        """Real Vonage Account Balance responses omit currency; default it to EUR."""
        fake_balance = types.SimpleNamespace(value=12.345, auto_reload=True)
        fake_module, _ = _make_vonage_module(get_balance=fake_balance)

        with patch.dict("sys.modules", {"vonage": fake_module}):
            result = await self.client.async_get_balance()

        assert result.value == 12.345
        assert result.currency == "EUR"
        assert result.auto_reload is True

    async def test_async_get_balance_auth_failed(self):
        """HTTP 401 / authentication errors raise ConfigEntryAuthFailed."""

        class _AuthErr(Exception):
            status_code = 401

        fake_module, _ = _make_vonage_module(raise_exc=_AuthErr("unauthorized"))

        with patch.dict("sys.modules", {"vonage": fake_module}):
            with pytest.raises(ConfigEntryAuthFailed):
                await self.client.async_get_balance()

    async def test_async_get_balance_auth_failed_by_class_name(self):
        """Auth errors detected by exception class name (no status code)."""

        class AuthenticationError(Exception):
            pass

        fake_module, _ = _make_vonage_module(raise_exc=AuthenticationError("nope"))

        with patch.dict("sys.modules", {"vonage": fake_module}):
            with pytest.raises(ConfigEntryAuthFailed):
                await self.client.async_get_balance()

    async def test_async_get_balance_transient_error(self):
        """Generic exceptions (5xx, timeout, network) raise VonageBalanceError."""
        fake_module, _ = _make_vonage_module(raise_exc=RuntimeError("boom"))

        with patch.dict("sys.modules", {"vonage": fake_module}):
            with pytest.raises(VonageBalanceError):
                await self.client.async_get_balance()

    async def test_async_get_balance_malformed_payload_missing_value(self):
        """Payload missing `value` raises VonageBalanceError."""
        bad = types.SimpleNamespace(currency="EUR")
        fake_module, _ = _make_vonage_module(get_balance=bad)

        with patch.dict("sys.modules", {"vonage": fake_module}):
            with pytest.raises(VonageBalanceError):
                await self.client.async_get_balance()

    async def test_async_get_balance_null_currency_defaults_to_eur(self):
        """Payload with null currency defaults to EUR."""
        bad = types.SimpleNamespace(value=10.0, currency=None)
        fake_module, _ = _make_vonage_module(get_balance=bad)

        with patch.dict("sys.modules", {"vonage": fake_module}):
            result = await self.client.async_get_balance()

        assert result.value == 10.0
        assert result.currency == "EUR"

    async def test_async_get_balance_sdk_import_failure(self):
        """ImportError on `from vonage import ...` raises VonageBalanceError."""
        # Force the import inside _get_balance_sync to fail.
        with patch.dict("sys.modules", {"vonage": None}):
            with pytest.raises(VonageBalanceError):
                await self.client.async_get_balance()

    async def test_async_get_balance_logging_redacts_secret(self, caplog):
        """API secret must never appear in any log output, even on failure."""
        fake_module, _ = _make_vonage_module(raise_exc=RuntimeError("boom"))

        with caplog.at_level("DEBUG"), patch.dict(
            "sys.modules", {"vonage": fake_module}
        ):
            with pytest.raises(VonageBalanceError):
                await self.client.async_get_balance()

        for record in caplog.records:
            assert "super-secret-do-not-leak" not in record.getMessage()

    async def test_async_get_balance_success_logging_redacts_secret(
        self, caplog, mock_balance_response_with_auto_reload
    ):
        """Secret must not appear in success-path debug logs."""
        fake_module, _ = _make_vonage_module(
            get_balance=mock_balance_response_with_auto_reload
        )

        with caplog.at_level("DEBUG"), patch.dict(
            "sys.modules", {"vonage": fake_module}
        ):
            await self.client.async_get_balance()

        for record in caplog.records:
            assert "super-secret-do-not-leak" not in record.getMessage()
