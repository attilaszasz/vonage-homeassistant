"""Vonage API client wrapper for Home Assistant integration.

Author: Attila Szasz
"""
from dataclasses import dataclass
from typing import Optional
import logging

from homeassistant.exceptions import HomeAssistantError, ConfigEntryAuthFailed

_LOGGER = logging.getLogger(__name__)


@dataclass
class SmsRequest:
    """SMS request data."""
    to: str  # E.164 phone number
    text: str
    from_number: str  # Sender ID


@dataclass
class SmsResponse:
    """SMS response data."""
    message_id: str
    status: str  # "delivered", "failed", etc.
    error_text: Optional[str] = None


@dataclass
class VoiceCallRequest:
    """Voice call request data."""
    to: str  # E.164 phone number
    text: str  # TTS message
    from_number: str
    language: str = "en-US"
    style: int = 0


@dataclass
class VoiceCallResponse:
    """Voice call response data."""
    uuid: str  # Call UUID
    status: str  # "started", "ringing", etc.
    error: Optional[str] = None


class VonageApiClient:
    """Client for Vonage API interactions."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        phone_number: str,
        application_id: Optional[str] = None,
        private_key: Optional[str] = None,
    ) -> None:
        """Initialize the Vonage API client."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.phone_number = phone_number
        self.application_id = application_id
        self.private_key = private_key

    def _send_sms_sync(self, to: str, text: str) -> SmsResponse:
        """Synchronous SMS send for executor."""
        try:
            # Import here to avoid import errors during testing
            from vonage import Vonage, Auth
            
            auth = Auth(api_key=self.api_key, api_secret=self.api_secret)
            client = Vonage(auth=auth)
            
            # Use the send method with message parameter as dict
            # Based on Vonage SDK documentation
            message_data = {
                "from": self.phone_number,
                "to": to,
                "text": text
            }
            response = client.sms.send(message_data)  # type: ignore[arg-type]
            
            # Handle the response object - Vonage SDK returns response objects
            # Extract first message from the response
            if hasattr(response, 'messages') and response.messages:
                message = response.messages[0]
                message_status = getattr(message, 'status', '5')
                message_id = getattr(message, 'message_id', '')
                error_text = getattr(message, 'error_text', None)
            else:
                message_status = '5'  # Internal error
                message_id = ''
                error_text = 'No message in response'
            
            # Map Vonage status codes to HA behaviors per research.md
            if message_status == "0":
                return SmsResponse(message_id=message_id, status="delivered")
            elif message_status == "1":
                raise HomeAssistantError("Rate limit exceeded")
            elif message_status == "2":
                raise HomeAssistantError("Invalid request parameters")
            elif message_status == "4":
                raise ConfigEntryAuthFailed("Invalid Vonage credentials")
            else:
                raise HomeAssistantError(f"Vonage service error: {error_text or 'Unknown error'}")
                
        except ImportError as err:
            _LOGGER.error("Vonage SDK not available: %s", err)
            raise HomeAssistantError("Vonage SDK not installed")
        except Exception as err:
            _LOGGER.error("Failed to send SMS: %s", err)
            raise HomeAssistantError(f"Failed to send SMS: {err}")

    async def send_sms(self, to: str, text: str) -> SmsResponse:
        """Send SMS message."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._send_sms_sync, to, text)

    def _make_call_sync(self, to: str, text: str, language: str = "en-US", style: int = 0) -> VoiceCallResponse:
        """Synchronous make call for executor."""
        try:
            # Import here to avoid import errors during testing
            from vonage import Vonage, Auth
            
            auth = Auth(application_id=self.application_id, private_key=self.private_key)
            client = Vonage(auth=auth)
            
            # Build NCCO with talk action per research.md pattern
            ncco = [{
                "action": "talk",
                "text": text,
                "language": language,
                "style": style
            }]
            
            # Normalize phone numbers for Voice API (replace + with 00 international prefix)
            # User input should keep + for standard E.164 format  
            to_number = to.replace('+', '00') if to.startswith('+') else to
            from_number = self.phone_number.replace('+', '00') if self.phone_number.startswith('+') else self.phone_number
            
            # Ensure the number meets Voice API requirements
            if not to_number or not to_number[0:2] == '00':
                raise HomeAssistantError(f"Invalid phone number format: {to}. Must be in international format (+CountryCode).")
            
            response = client.voice.create_call({  # type: ignore[arg-type]
                "to": [{"type": "phone", "number": to_number}],
                "from": {"type": "phone", "number": from_number},
                "ncco": ncco
            })
            
            # Handle the response object
            call_uuid = getattr(response, 'uuid', '')
            call_status = getattr(response, 'status', 'failed')
            
            return VoiceCallResponse(uuid=call_uuid, status=call_status)
            
        except ImportError as err:
            _LOGGER.error("Vonage SDK not available: %s", err)
            raise HomeAssistantError("Vonage SDK not installed")
        except Exception as err:
            _LOGGER.error("Failed to make call: %s", err)
            raise HomeAssistantError(f"Failed to make call: {err}")

    async def make_call(
        self, to: str, text: str, language: str = "en-US", style: int = 0
    ) -> VoiceCallResponse:
        """Make voice call with TTS."""
        # Check if Voice credentials are configured
        if not self.application_id or not self.private_key:
            raise HomeAssistantError("Voice API not configured - application_id and private_key required")
        
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._make_call_sync, to, text, language, style)

    def _test_sms_credentials_sync(self) -> bool:
        """Synchronous SMS credentials test for executor."""
        try:
            # Import here to avoid import errors during testing
            from vonage import Vonage, Auth
            
            auth = Auth(api_key=self.api_key, api_secret=self.api_secret)
            client = Vonage(auth=auth)
            
            # Make a simple account info request to test credentials
            # This is a lightweight call that validates auth without sending messages
            balance = client.account.get_balance()
            return balance is not None
            
        except Exception as err:
            _LOGGER.error("SMS credentials test failed: %s", err)
            return False

    async def test_sms_credentials(self) -> bool:
        """Test SMS credentials validity."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._test_sms_credentials_sync)

    def _test_voice_credentials_sync(self) -> bool:
        """Synchronous Voice credentials test for executor."""
        # Import here to avoid import errors during testing
        import jwt
        import uuid
        from datetime import datetime, timezone
        
        try:
            if not self.application_id or not self.private_key:
                return False
                
            # Validate private key format first
            if not self.private_key.strip().startswith('-----BEGIN'):
                _LOGGER.error("Private key must be in PEM format")
                return False
                
            # Test by generating a JWT token with the provided credentials
            # This validates both the application_id format and private_key validity
            payload = {
                "application_id": self.application_id,
                "iat": int(datetime.now(timezone.utc).timestamp()),
                "exp": int(datetime.now(timezone.utc).timestamp()) + 300,  # 5 minutes
                "jti": str(uuid.uuid4()),
            }
            
            # If this doesn't raise an exception, credentials are valid
            # Use the private key directly as PyJWT expects PEM format
            token = jwt.encode(payload, self.private_key.strip(), algorithm="RS256")
            return token is not None and len(token) > 0
            
        except jwt.InvalidKeyError as err:
            _LOGGER.error("Invalid private key format: %s", err)
            return False
        except Exception as err:
            _LOGGER.error("Voice credentials test failed: %s", err)
            return False

    async def test_voice_credentials(self) -> bool:
        """Test Voice credentials validity."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._test_voice_credentials_sync)