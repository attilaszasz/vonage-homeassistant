"""Constants for the Vonage integration."""

DOMAIN = "vonage"

# Config keys (required for SMS)
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"
CONF_PHONE_NUMBER = "phone_number"  # Sender ID (E.164 format)

# Config keys (optional, enables Voice)
CONF_APPLICATION_ID = "application_id"
CONF_PRIVATE_KEY = "private_key"  # PEM content, not file path

# Config keys (Voice preferences)
CONF_DEFAULT_LANGUAGE = "default_language"  # e.g., "en-US"
CONF_DEFAULT_VOICE_STYLE = "default_voice_style"  # 0-5