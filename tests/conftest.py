"""Test fixtures for Vonage integration."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.vonage.const import DOMAIN


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Return a mock config entry."""
    return ConfigEntry(
        domain=DOMAIN,
        title="Vonage",
        data={
            "api_key": "test_key",
            "api_secret": "test_secret",
            "phone_number": "+14155550100",
            "application_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest_key_content\n-----END PRIVATE KEY-----",
            "default_language": "en-US",
            "default_voice_style": 0,
        },
    )


@pytest.fixture
def mock_vonage_client():
    """Return a mock Vonage API client."""
    client = AsyncMock()
    client.send_sms = AsyncMock()
    client.make_call = AsyncMock()
    client.test_sms_credentials = AsyncMock(return_value=True)
    client.test_voice_credentials = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_vonage_sms_response():
    """Return a mock SMS response."""
    from custom_components.vonage.api import SmsResponse
    return SmsResponse(
        message_id="0A00000012345",
        status="delivered"
    )


@pytest.fixture
def mock_vonage_voice_response():
    """Return a mock Voice response."""
    from custom_components.vonage.api import VoiceCallResponse
    return VoiceCallResponse(
        uuid="aaaaaaaa-bbbb-cccc-dddd-000000000000",
        status="started"
    )