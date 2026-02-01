"""Test for Vonage notify platform."""
import pytest
from unittest.mock import AsyncMock

from homeassistant.exceptions import HomeAssistantError

from custom_components.vonage.api import VonageApiClient, SmsResponse
from custom_components.vonage.notify import VonageSmsNotificationService


class TestVonageSmsNotificationService:
    """Test VonageSmsNotificationService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api_client = AsyncMock(spec=VonageApiClient)
        self.service = VonageSmsNotificationService(self.api_client)

    async def test_send_message_single_target(self):
        """Test sending message to single target."""
        # Mock successful SMS response
        self.api_client.send_sms.return_value = SmsResponse(
            message_id="0A00000012345",
            status="delivered"
        )
        
        await self.service.async_send_message(
            message="Test message",
            target="+14155550101"
        )
        
        self.api_client.send_sms.assert_called_once_with(
            to="+14155550101",
            text="Test message"
        )

    async def test_send_message_multiple_targets(self):
        """Test sending message to multiple targets."""
        # Mock successful SMS responses
        self.api_client.send_sms.return_value = SmsResponse(
            message_id="0A00000012345",
            status="delivered"
        )
        
        targets = ["+14155550101", "+14155550102"]
        await self.service.async_send_message(
            message="Test message",
            target=targets
        )
        
        assert self.api_client.send_sms.call_count == 2
        self.api_client.send_sms.assert_any_call(
            to="+14155550101",
            text="Test message"
        )
        self.api_client.send_sms.assert_any_call(
            to="+14155550102", 
            text="Test message"
        )

    async def test_send_message_string_target(self):
        """Test sending message with target as string instead of list."""
        self.api_client.send_sms.return_value = SmsResponse(
            message_id="0A00000012345",
            status="delivered"
        )
        
        await self.service.async_send_message(
            message="Test message",
            target="+14155550101"  # String, not list
        )
        
        self.api_client.send_sms.assert_called_once_with(
            to="+14155550101",
            text="Test message"
        )

    async def test_send_message_no_targets(self):
        """Test error when no targets provided."""
        with pytest.raises(HomeAssistantError, match="No targets specified"):
            await self.service.async_send_message(
                message="Test message"
                # No target provided
            )
        
        self.api_client.send_sms.assert_not_called()

    async def test_send_message_empty_targets(self):
        """Test error when empty targets list provided."""
        with pytest.raises(HomeAssistantError, match="No targets specified"):
            await self.service.async_send_message(
                message="Test message",
                target=[]  # Empty list
            )
        
        self.api_client.send_sms.assert_not_called()

    async def test_send_message_empty_message(self):
        """Test error when empty message provided."""
        with pytest.raises(HomeAssistantError, match="Empty message not allowed"):
            await self.service.async_send_message(
                message="",  # Empty message
                target="+14155550101"
            )
        
        self.api_client.send_sms.assert_not_called()

    async def test_send_message_api_error(self):
        """Test error handling when API call fails."""
        # Mock API error
        self.api_client.send_sms.side_effect = HomeAssistantError("Rate limit exceeded")
        
        with pytest.raises(HomeAssistantError, match="Failed to send SMS to \\+14155550101: Rate limit exceeded"):
            await self.service.async_send_message(
                message="Test message",
                target="+14155550101"
            )
        
        self.api_client.send_sms.assert_called_once_with(
            to="+14155550101",
            text="Test message"
        )

    async def test_send_message_partial_failure(self):
        """Test partial failure with multiple targets."""
        # First call succeeds, second fails
        self.api_client.send_sms.side_effect = [
            SmsResponse(message_id="0A00000012345", status="delivered"),
            HomeAssistantError("Invalid number")
        ]
        
        with pytest.raises(HomeAssistantError, match="Failed to send SMS to \\+14155550102"):
            await self.service.async_send_message(
                message="Test message",
                target=["+14155550101", "+14155550102"]
            )
        
        # Both calls should have been attempted
        assert self.api_client.send_sms.call_count == 2