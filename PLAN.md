# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

route-table-next-hop-ip-validation

## Roadmap

### diagram-design-workbench — Editorial diagram design engine, cloud containment grammar, and agent evaluation suite

Status: done

Acceptance:
- Declarative specification compiler renders self-contained SVG/HTML for architecture, dataviz (treemap, sankey, slopegraph), and SBGN process diagrams with zero shadows and crisp typography
- Containment grammar validator enforces cloud hierarchy rules (VNet, subnet, PaaS private endpoints) and honest-data visual rules
- AI/ML evaluation runner measures agent diagram generation accuracy, containment compliance, and latency against labeled benchmarks
- OIDC bearer authentication with demo mode and role-based access control enforces endpoint security
- Interactive React UI provides diagram editor, live preview, validation inspector, benchmark runner, and artifact export workflows

Implementation: `backend/app/services/engine.py`, `backend/app/services/validator.py`, `backend/app/services/evaluator.py`, `backend/app/api/diagrams.py`, `backend/app/api/evaluation.py`, `backend/app/api/auth.py`, `backend/app/api/audit.py`, `backend/app/main.py`, `frontend/src/App.tsx`

Tests: `backend/tests/test_engine.py`, `backend/tests/test_validator.py`, `backend/tests/test_evaluation.py`, `backend/tests/test_api.py`, `frontend/src/App.test.tsx`

### cloud-containment-grammar-azure — Advanced Azure and AWS multi-tier network topology grammar with automatic routing layout

Status: done

Acceptance:
- Automatic orthogonal routing between sibling VNets and transitive hub-spoke peering connections
- Data-attribute validation for NSG flow rules and route tables

Implementation: `backend/app/services/engine.py`, `backend/app/services/validator.py`

Tests: `backend/tests/test_engine.py`, `backend/tests/test_validator.py`

### nsg-validation-test-coverage — Complete NSG flow rule validation test coverage for access and protocol fields

Status: done

Acceptance:
- NSG rule validation rejects invalid `access` values (must be Allow or Deny)
- NSG rule validation rejects invalid `protocol` values (must be Tcp, Udp, Icmp, or *)

Implementation: `backend/tests/test_validator.py`

Tests: `backend/tests/test_validator.py::test_cloud_containment_nsg_invalid_access`, `backend/tests/test_validator.py::test_cloud_containment_nsg_invalid_protocol`

### route-table-next-hop-ip-validation — Route table validation requires next_hop_ip for VirtualAppliance and VirtualNetworkGateway

Status: done

Acceptance:
- Route table validation rejects routes with `next_hop_type` VirtualAppliance or VirtualNetworkGateway missing `next_hop_ip`
- Validates Azure requirement that firewall and VPN gateway routes must specify the next hop IP address
- New validation rule: `containment.route_table_missing_next_hop_ip`

Implementation: `backend/app/services/validator.py`, `backend/tests/test_validator.py`

Tests: `backend/tests/test_validator.py::test_cloud_containment_route_table_missing_next_hop_ip`

### diagram-export-enhancements — Multi-format diagram export with CLI and programmatic API

Status: planned

Acceptance:
- CLI command `orbit export` to render diagrams from saved specs or JSON files
- Supports SVG, HTML, PNG (via headless browser), and PDF output formats
- Batch export of multiple diagrams with configurable themes
- Programmatic export API for integration into CI/CD pipelines

Implementation: `backend/app/services/exporter.py`, `backend/app/api/export.py`, `backend/app/cli.py`

Tests: `backend/tests/test_export.py`

