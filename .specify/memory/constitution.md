<!--
Sync Impact Report
==================
Version change: 0.0.0 → 1.0.0 (MAJOR: initial constitution adoption)
Modified principles: N/A (new document)
Added sections: Core Principles (5), HACS & Home Assistant Compliance, Development Workflow, Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ⚠ pending (update Constitution Check section)
  - .specify/templates/spec-template.md ⚠ pending (update Requirements section for HA entities)
  - .specify/templates/tasks-template.md ⚠ pending (add HA-specific task phases)
Follow-up TODOs: None
-->

# Vonage Home Assistant Integration Constitution

## Core Principles

### I. Home Assistant Architecture Compliance

All code MUST follow Home Assistant custom component conventions:
- Integration lives in `custom_components/vonage/` with required files: `__init__.py`, `manifest.json`, `config_flow.py`
- Entity platforms (e.g., `sensor.py`, `switch.py`, `notify.py`) MUST subclass HA base entities
- Coordinator pattern MUST be used for API polling to respect HA's update lifecycle
- All user-facing strings MUST be defined in `strings.json` and `translations/` for i18n
- Configuration MUST use Config Flow (UI-based setup); YAML-only config is prohibited for new integrations

### II. HACS Distribution Requirements

The integration MUST remain HACS-installable at all times:
- `hacs.json` at repository root with valid `name`, `homeassistant` version constraint, and `render_readme: true`
- `manifest.json` MUST declare accurate `version`, `domain: "vonage"`, `integration_type`, and `iot_class`
- A `README.md` at repo root MUST include installation instructions, supported entities, and configuration steps
- Releases MUST use semantic versioning tags (e.g., `v1.2.3`) matching `manifest.json` version
- Breaking changes MUST be documented in release notes and increment MAJOR version

### III. Vonage API Encapsulation

Vonage SDK interactions MUST be isolated from Home Assistant glue code:
- A dedicated `api.py` (or `vonage_client.py`) module wraps all Vonage HTTP/SDK calls
- HA coordinators and entities MUST NOT import Vonage SDK directly; they call the wrapper
- Credentials (API key, secret, application ID) MUST be stored via HA's `ConfigEntry` and never logged
- Rate-limit handling and retry logic MUST live in the API wrapper, not in entity code

### IV. Entity & Service Design

Entities and services MUST be predictable and user-friendly:
- Entity IDs MUST follow `<platform>.vonage_<descriptive_name>` (e.g., `sensor.vonage_account_balance`)
- Services MUST be registered under the `vonage` domain with clear, typed parameters (use `vol` schemas)
- Device info MUST link entities to a logical Vonage "device" for grouping in the HA UI
- State attributes MUST be minimal; prefer dedicated entities over attribute bloat

### V. Test-First & CI Quality Gates

Automated testing MUST gate all merges:
- Unit tests (pytest) MUST cover the API wrapper and helper functions with mocked HTTP
- Integration tests MUST use `pytest-homeassistant-custom-component` fixtures to validate config flow, entity setup, and service calls
- `hassfest` and `hacs/action` MUST pass in CI before merge
- Code MUST pass `ruff` linting and `mypy` type checks with strict mode

## HACS & Home Assistant Compliance

| Requirement | File/Location | Validation |
|-------------|---------------|------------|
| HACS metadata | `hacs.json` | `hacs/action` CI check |
| Manifest | `custom_components/vonage/manifest.json` | `hassfest` CI check |
| Translations | `custom_components/vonage/translations/en.json` | `hassfest` CI check |
| README | `README.md` (repo root) | Manual review; HACS renders for users |
| Version tag | Git tag `vX.Y.Z` | CI release workflow |

## Development Workflow

1. **Branch naming**: `feat/<short-desc>`, `fix/<issue-id>`, `docs/<topic>`
2. **Local testing**: Use `pytest --cov` and a local HA dev container (`devcontainer.json` provided)
3. **Pre-commit hooks**: `ruff`, `mypy`, `hassfest` run automatically
4. **PR requirements**: All CI checks green, at least one approval, squash-merge only
5. **Release process**: Tag `vX.Y.Z` triggers GitHub Actions to publish release and notify HACS

## Governance

This constitution supersedes ad-hoc decisions. Amendments require:
1. A PR updating this file with rationale
2. Version bump (MAJOR for principle changes, MINOR for new sections, PATCH for clarifications)
3. Approval from at least one maintainer

All code reviews MUST verify compliance with the above principles. Deviations require documented justification in the PR description.

**Version**: 1.0.0 | **Ratified**: 2026-02-01 | **Last Amended**: 2026-02-01
