# Quickstart: Vonage Home Assistant Integration

**Feature**: 001-vonage-ha-integration  
**Date**: 2026-02-01  
**Audience**: Developers implementing this integration

---

## Prerequisites

1. **Home Assistant 2024.1.0+** development environment
2. **Vonage account** with:
   - API key and secret (Dashboard → API Settings)
   - Virtual phone number (Dashboard → Numbers)
   - Application with Voice capability (optional, for voice calls)
   - Private key file from Application creation

---

## Project Setup

```bash
# Clone and enter repository
cd vonage-homeassistant

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_test.txt

# Install pre-commit hooks
pre-commit install
```

---

## Local Development with Home Assistant

### Option A: Dev Container (Recommended)

```bash
# Open in VS Code with Dev Containers extension
code .
# Select "Reopen in Container" when prompted
```

### Option B: Manual HA Core Setup

```bash
# Clone HA core for testing fixtures
git clone https://github.com/home-assistant/core.git ../ha-core
cd ../ha-core
script/setup

# Link custom component
ln -s $(pwd)/../vonage-homeassistant/custom_components/vonage homeassistant/components/vonage
```

---

## File Creation Order

For implementing this integration, create files in this order:

### Phase 1: Foundation

1. `custom_components/vonage/__init__.py` — empty, marks package
2. `custom_components/vonage/const.py` — domain and config constants
3. `custom_components/vonage/manifest.json` — integration metadata

### Phase 2: API Layer

4. `custom_components/vonage/api.py` — Vonage SDK wrapper

### Phase 3: Config Flow

5. `custom_components/vonage/config_flow.py` — UI setup flow
6. `custom_components/vonage/strings.json` — English UI strings
7. `custom_components/vonage/translations/en.json` — copy of strings.json

### Phase 4: Services

8. `custom_components/vonage/notify.py` — SMS notification platform
9. `custom_components/vonage/services.py` — voice call service
10. Update `__init__.py` — wire up entry setup

### Phase 5: Distribution

11. `hacs.json` — HACS metadata
12. `README.md` — user documentation

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=custom_components/vonage --cov-report=html

# Run specific test file
pytest tests/test_config_flow.py -v
```

---

## Validation Commands

```bash
# Lint with ruff
ruff check custom_components/vonage/

# Type check with mypy
mypy custom_components/vonage/

# HA manifest validation (requires HA core checkout)
python -m script.hassfest --integration-path custom_components/vonage

# HACS validation (in CI or local with act)
act -j hacs
```

---

## Testing in Live Home Assistant

1. Copy `custom_components/vonage/` to your HA config directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration → "Vonage"
4. Enter credentials and complete setup
5. Test via Developer Tools → Services:

```yaml
service: notify.vonage_sms
data:
  message: "Test from Home Assistant"
  target:
    - "+14155550101"
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| [spec.md](spec.md) | Feature requirements |
| [research.md](research.md) | Technical decisions |
| [data-model.md](data-model.md) | Config and data structures |
| [contracts/services.md](contracts/services.md) | Service schemas |
| [plan.md](plan.md) | Implementation plan |

---

## Next Steps

After implementation:

1. Run full test suite with coverage
2. Run `hassfest` and `hacs/action` validation
3. Update `manifest.json` version
4. Create Git tag matching version (e.g., `v1.0.0`)
5. Push to GitHub for HACS discovery
