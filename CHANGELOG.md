# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-12

### Added
- **Core Editorial Diagram Engine**:
  - Declarative specification compiler generating self-contained SVG + HTML artifacts.
  - Zero drop-shadows, zero gradient slop, crisp mono numeric typography, and single-accent color palettes.
  - Supported diagram types: Hierarchical Cloud Architecture, Treemap (squarified), Sankey (conserved flow), Slopegraph, Dumbbell, Waffle, Beeswarm, and SBGN Process Description.
- **Geometric Containment Grammar & Honest-Data Rules**:
  - Azure/AWS cloud hierarchy verification (Subscription -> Resource Group -> VNet -> Subnet -> Nodes).
  - PaaS private endpoint isolation checks: verifying databases reside in Resource Groups and private endpoints in subnets.
  - Honest-data visual rules: area proportion verification, flow continuity, and skin linting.
- **AI/ML Evaluation Suite**:
  - Labeled dataset of 20 benchmark diagram prompts and schemas for coding agents (Claude Code, Cursor, Codex, Copilot, Factory Droid, Pi).
  - Benchmark evaluation runner computing Spec Validity, Containment Rule Compliance, Geometric Fidelity Score, and Render Latency.
  - Reproducible CLI evaluation entrypoint: `python3 -m app.services.evaluator`.
- **Backend API & Data Persistence**:
  - Modular FastAPI application with SQLite persistent storage, UTC timestamps, transactional mutations, and audit logging.
  - Full CRUD and rendering endpoints for diagram specs.
  - Pluggable LLM advisory adapter supporting OpenAI-compatible, Anthropic, Gemini, and Ollama providers with strict server-side keys.
  - OIDC Bearer authentication with Keycloak and SAML identity brokering architecture.
  - Local-only demo mode strictly barred in production.
- **Interactive Frontend Workbench**:
  - React + TypeScript + Vite application.
  - Real-time SVG preview with editorial themes (Light Editorial, Dark Editorial, Blueprint).
  - Interactive diagram specification editor with starter presets.
  - Live containment rule and skin lint inspector.
  - AI agent visual reasoning benchmark execution dashboard with metrics cards.
  - Audit trail viewer with pagination, action filtering, and detail modal.
- **DevOps & Packaging**:
  - Multi-stage Dockerfiles for backend and frontend with non-root security.
  - Local docker-compose configuration including Keycloak and persistent storage.
  - GitHub Actions CI workflow covering pytest, typechecks, frontend tests, and Docker builds on standard ubuntu-latest runners.

### Authored by
Ryan Vo <ryandtvo@gmail.com>
## [1.0.1] - 2026-10-14

### Added
- **Keycloak Realm Import Configuration**:
  - Complete realm `orbit` with client `orbit-frontend` configured for PKCE and SPA flow.
  - Hierarchical roles: `viewer` (read-only), `analyst` (create/update diagrams, run evaluations), `admin` (full access).
  - Test users for each role with temporary passwords requiring reset on first login.
  - SAML Identity Provider broker placeholder for enterprise upstream IdPs (Okta, Entra ID, PingFederate).
  - Attribute mappers for SAML assertion claims to Keycloak roles and user profile.
- **Docker Compose Integration**:
  - Mounted `keycloak/realm-orbit.json` for automatic realm import on Keycloak startup via `--import-realm`.
  - Updated healthcheck dependencies for proper service ordering.

### Fixed
- Keycloak OIDC endpoints now available at container startup for backend authentication integration.
- Resolved missing realm configuration that prevented SAML brokering setup.

### Authored by
Ryan Vo <ryandtvo@gmail.com>
