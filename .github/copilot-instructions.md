# Copilot Instructions for vonage-homeassistant

## Overview

This is a **Home Assistant custom component** for Vonage integration, distributed via **HACS**. It follows HA custom component conventions and the project constitution at `.specify/memory/constitution.md`.

## Project Structure

```
custom_components/vonage/
├── __init__.py          # Integration setup, async_setup_entry
├── manifest.json        # HA integration metadata
├── config_flow.py       # UI-based configuration
├── coordinator.py       # DataUpdateCoordinator for API polling
├── api.py               # Vonage SDK wrapper (all API calls here)
├── sensor.py            # Sensor entities (e.g., account balance)
├── notify.py            # Notification service (send SMS)
├── strings.json         # UI strings (English source)
└── translations/        # Localized strings
```

## Key Conventions

- **Config Flow only**: No YAML configuration; use `config_flow.py` for setup
- **Coordinator pattern**: API polling via `DataUpdateCoordinator` subclass
- **API isolation**: All Vonage SDK calls in `api.py`; entities call the wrapper
- **Entity naming**: `sensor.vonage_<name>`, `notify.vonage_<name>`
- **Services**: Register under `vonage` domain with `vol` schemas

## Commands

```bash
# Run tests
pytest --cov=custom_components/vonage

# Lint & type check
ruff check . && mypy custom_components/

# Validate manifest
python -m homeassistant.scripts.check_config -c tests/fixtures/config

# hassfest validation (requires HA core checkout or container)
python -m script.hassfest
```

## HACS Requirements

- `hacs.json` at repo root with `name`, `homeassistant` constraint
- `manifest.json` version MUST match Git tag (e.g., `v1.2.3`)
- README.md MUST include installation and configuration instructions

## Testing

- Use `pytest-homeassistant-custom-component` for integration tests
- Mock Vonage API responses; never call live API in tests
- CI runs: `ruff`, `mypy`, `hassfest`, `hacs/action`

## See Also

- [Constitution](../.specify/memory/constitution.md) — non-negotiable principles
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [HACS Documentation](https://hacs.xyz/)
