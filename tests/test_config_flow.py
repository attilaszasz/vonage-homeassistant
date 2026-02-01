"""Test the Vonage config flow."""
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.vonage.const import DOMAIN
from custom_components.vonage.config_flow import VonageConfigFlow


class TestVonageConfigFlow:
    """Test the Vonage config flow."""

    @pytest.fixture
    def mock_setup_entry(self):
        """Mock setting up a config entry."""
        with patch(f"custom_components.{DOMAIN}.async_setup_entry", return_value=True):
            yield

    async def test_form_user_success(self, hass, mock_setup_entry):
        """Test successful user form with valid credentials."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {}
        
        # Mock successful credential validation
        with patch(
            "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
            return_value=True
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "api_key": "test_key",
                    "api_secret": "test_secret",
                    "phone_number": "+14155550100",
                },
            )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Vonage"
        assert result["data"] == {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "phone_number": "+14155550100",
            "default_language": "en-US",
            "default_voice_style": 0,
        }

    async def test_form_user_invalid_credentials(self, hass):
        """Test user form with invalid credentials."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        # Mock failed credential validation
        with patch(
            "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
            return_value=False
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "api_key": "invalid_key",
                    "api_secret": "invalid_secret",
                    "phone_number": "+14155550100",
                },
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}

    async def test_form_user_with_voice_credentials(self, hass, mock_setup_entry):
        """Test user form with Voice credentials included."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        # Mock both SMS and Voice credential validation
        with patch(
            "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
            return_value=True
        ), patch(
            "custom_components.vonage.api.VonageApiClient.test_voice_credentials", 
            return_value=True
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "api_key": "test_key",
                    "api_secret": "test_secret",
                    "phone_number": "+14155550100",
                    "application_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
                    "default_language": "en-GB",
                    "default_voice_style": 1,
                },
            )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["application_id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        assert "-----BEGIN PRIVATE KEY-----" in result["data"]["private_key"]
        assert result["data"]["default_language"] == "en-GB"
        assert result["data"]["default_voice_style"] == 1

    async def test_form_user_voice_optional_omitted(self, hass, mock_setup_entry):
        """Test that Voice fields can be omitted."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        with patch(
            "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
            return_value=True
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "api_key": "test_key",
                    "api_secret": "test_secret",
                    "phone_number": "+14155550100",
                },
            )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        # Voice fields should not be in data if not provided
        assert "application_id" not in result["data"]
        assert "private_key" not in result["data"]

    async def test_credentials_not_in_logs(self, hass, caplog):
        """Test credentials are not logged."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        with patch(
            "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
            return_value=True
        ):
            await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "api_key": "secret_key_12345",
                    "api_secret": "secret_secret_67890", 
                    "phone_number": "+14155550100",
                    "private_key": "-----BEGIN PRIVATE KEY-----\nsecret_key_content\n-----END PRIVATE KEY-----",
                },
            )

        # Check that sensitive data is not in logs
        log_text = caplog.text
        assert "secret_key_12345" not in log_text
        assert "secret_secret_67890" not in log_text
        assert "secret_key_content" not in log_text

    async def test_form_user_voice_incomplete_app_id_only(self, hass):
        """Test error when only Application ID provided without Private Key."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        with patch(
            "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
            return_value=True
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "api_key": "test_key",
                    "api_secret": "test_secret",
                    "phone_number": "+14155550100",
                    "application_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    # Missing private_key
                },
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "voice_incomplete"}

    async def test_form_user_voice_incomplete_private_key_only(self, hass):
        """Test error when only Private Key provided without Application ID."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        with patch(
            "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
            return_value=True
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "api_key": "test_key",
                    "api_secret": "test_secret",
                    "phone_number": "+14155550100",
                    "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
                    # Missing application_id
                },
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "voice_incomplete"}

    async def test_form_user_voice_invalid_credentials(self, hass):
        """Test error when Voice credentials are invalid."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        # Mock SMS valid but Voice invalid
        with patch(
            "custom_components.vonage.api.VonageApiClient.test_sms_credentials",
            return_value=True
        ), patch(
            "custom_components.vonage.api.VonageApiClient.test_voice_credentials",
            return_value=False
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "api_key": "test_key",
                    "api_secret": "test_secret",
                    "phone_number": "+14155550100",
                    "application_id": "invalid-app-id",
                    "private_key": "-----BEGIN PRIVATE KEY-----\ninvalid_key\n-----END PRIVATE KEY-----",
                },
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}