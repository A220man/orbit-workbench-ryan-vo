# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

diagram-design-workbench

## Roadmap

### diagram-design-workbench — Editorial diagram design engine, cloud containment grammar, and agent evaluation suite

Status: done

Acceptance:
- Declarative specification compiler renders self-contained SVG/HTML for architecture, dataviz (treemap, sankey, slopegraph), and SBGN process diagrams with zero shadows and crisp typography
- Containment grammar validator enforces cloud hierarchy rules (VNet, subnet, PaaS private endpoints) and honest-data visual rules
- AI/ML evaluation runner measures agent diagram generation accuracy, containment compliance, and latency against labeled benchmarks
- OIDC bearer authentication with demo mode and role-based access control enforces endpoint security
- Interactive React UI provides diagram editor, live preview, validation inspector, benchmark runner, and artifact export workflows

Implementation: `backend/app/main.py`, `backend/app/api/diagrams.py`, `backend/app/services/engine.py`, `backend/app/services/validator.py`, `backend/app/services/evaluator.py`, `frontend/src/App.tsx`

Tests: `backend/tests/test_engine.py`, `backend/tests/test_validator.py`, `backend/tests/test_evaluation.py`, `backend/tests/test_api.py`, `frontend/src/App.test.tsx`

### cloud-containment-grammar-azure — Advanced Azure and AWS multi-tier network topology grammar with automatic routing layout

Status: planned

Acceptance:
- Automatic orthogonal routing between sibling VNets and transitive hub-spoke peering connections
- Data-attribute validation for NSG flow rules and route tables

### sbgn-systems-biology-notation — Extended SBGN Process Description glyphs and SBML biological network importer

Status: planned

Acceptance:
- Import SBML XML files directly into Orbit declarative diagram specs
- Render reversible reaction nodes, catalytic effectors, and logic operators

### multi-tenant-saml-federation — Enterprise multi-tenant Keycloak SAML IdP broker automated realm sync

Status: planned

Acceptance:
- Automated SAML assertion attribute mapping for organization-level diagram libraries
- SCIM group synchronization for engineering and security team roles

