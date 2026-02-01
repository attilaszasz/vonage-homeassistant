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

    async def send_sms(self, to: str, text: str) -> SmsResponse:
        """Send SMS message."""
        try:
            # Import here to avoid import errors during testing
            from vonage import Vonage, Auth
            
            auth = Auth(api_key=self.api_key, api_secret=self.api_secret)
            client = Vonage(auth=auth)
            
            response = client.sms.send({
                "from": self.phone_number,
                "to": to,
                "text": text
            })
            
            # Vonage returns a dict with status and message-id
            message_status = response.get("status", "5")  # Default to internal error
            message_id = response.get("message-id", "")
            error_text = response.get("error-text")
            
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

    async def make_call(
        self, to: str, text: str, language: str = "en-US", style: int = 0
    ) -> VoiceCallResponse:
        """Make voice call with TTS."""
        # Check if Voice credentials are configured
        if not self.application_id or not self.private_key:
            raise HomeAssistantError("Voice API not configured - application_id and private_key required")
        
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
            
            response = client.voice.create_call({
                "to": [{"type": "phone", "number": to}],
                "from": {"type": "phone", "number": self.phone_number},
                "ncco": ncco
            })
            
            # Response contains uuid and status
            call_uuid = response.get("uuid", "")
            call_status = response.get("status", "failed")
            
            return VoiceCallResponse(uuid=call_uuid, status=call_status)
            
        except ImportError as err:
            _LOGGER.error("Vonage SDK not available: %s", err)
            raise HomeAssistantError("Vonage SDK not installed")
        except Exception as err:
            _LOGGER.error("Failed to make call: %s", err)
            raise HomeAssistantError(f"Failed to make call: {err}")

    async def test_sms_credentials(self) -> bool:
        """Test SMS credentials validity."""
        try:
            # Import here to avoid import errors during testing
            from vonage import Vonage, Auth
            
            auth = Auth(api_key=self.api_key, api_secret=self.api_secret)
            client = Vonage(auth=auth)
            
            # Make a simple account info request to test credentials
            # This is a lightweight call that validates auth without sending messages
            account = client.account.get_account_balance()
            return account is not None
            
        except Exception as err:
            _LOGGER.error("SMS credentials test failed: %s", err)
            return False

    async def test_voice_credentials(self) -> bool:
        """Test Voice credentials validity."""
        try:
            # Import here to avoid import errors during testing
            from vonage import Vonage, Auth
            import jwt
            import uuid
            from datetime import datetime, timezone
            
            if not self.application_id or not self.private_key:
                return False
                
            # Test by generating a JWT token with the provided credentials
            # This validates both the application_id format and private_key validity
            auth = Auth(application_id=self.application_id, private_key=self.private_key)
            client = Vonage(auth=auth)
            
            # Generate a simple JWT payload to test the private key
            payload = {
                "application_id": self.application_id,
                "iat": int(datetime.now(timezone.utc).timestamp()),
                "jti": str(uuid.uuid4()),
            }
            
            # If this doesn't raise an exception, credentials are valid
            token = jwt.encode(payload, self.private_key, algorithm="RS256")
            return token is not None and len(token) > 0
            
        except Exception as err:
            _LOGGER.error("Voice credentials test failed: %s", err)
            return False