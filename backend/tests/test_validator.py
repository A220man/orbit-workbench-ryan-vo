"""Unit tests for the containment grammar and honest-data validator."""
from app.models.schemas import DiagramContent
from app.services.validator import DiagramValidator


def test_skin_linter_rejects_shadows():
    svg_with_shadow = '<svg viewBox="0 0 100 100"><filter id="f1"><feDropShadow dx="2" dy="2"/></filter></svg>'
    content = DiagramContent(title="Test")
    report = DiagramValidator.validate("treemap", content, svg_with_shadow)
    assert not report.skin_compliant
    assert any(i.rule == "skin.no_drop_shadows" for i in report.issues)


def test_skin_linter_accepts_clean_svg():
    clean_svg = '<svg viewBox="0 0 100 100"><rect x="0" y="0" width="10" height="10" fill="#0969da"/></svg>'
    content = DiagramContent(title="Test")
    report = DiagramValidator.validate("rag_pipeline", content, clean_svg)
    assert report.skin_compliant


def test_cloud_containment_paas_isolation_rule():
    # Azure case study: PaaS service placed directly in subnet must be REJECTED!
    invalid_data = {
        "subscription": "Sub-01",
        "resource_group": "RG-01",
        "vnet": "VNet-01",
        "subnets": [
            {
                "name": "snet-data",
                "nodes": [{"id": "bad-db", "label": "Azure SQL Database", "type": "paas_service", "ip": "10.0.1.4"}],
            }
        ],
    }
    content = DiagramContent(title="Invalid PaaS Architecture", data=invalid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert not report.containment_compliant
    assert any(i.rule == "containment.paas_isolation" for i in report.issues)


def test_cloud_containment_valid_architecture():
    valid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnet": "Spoke VNet",
        "subnets": [
            {
                "name": "snet-compute",
                "nodes": [{"id": "pe-1", "label": "pe-sql", "type": "private_endpoint", "ip": "10.0.1.5"}],
            }
        ],
        "paas_services": [
            {"id": "sql-db", "label": "Azure SQL Managed", "target_pe": "pe-1", "tier": "vCore"}
        ],
    }
    content = DiagramContent(title="Valid PaaS Architecture", data=valid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert report.containment_compliant
    assert report.valid


def test_honest_data_treemap_rejects_negative_values():
    content = DiagramContent(
        title="Invalid Treemap",
        data={"items": [{"label": "Category A", "value": -15}]},
    )
    report = DiagramValidator.validate("treemap", content)
    assert not report.honest_data_compliant
    assert any(i.rule == "honest_data.treemap_positive_values" for i in report.issues)


def test_honest_data_sankey_unbalanced_warning():
    content = DiagramContent(
        title="Unbalanced Sankey",
        data={
            "left_nodes": [{"id": "in", "label": "Power In", "value": 100}],
            "right_nodes": [{"id": "out", "label": "Useful Out", "value": 50}],
        },
    )
    report = DiagramValidator.validate("sankey", content)
    # Should flag a warning for mass conservation
    assert any(i.rule == "honest_data.sankey_conservation_of_mass" for i in report.issues)
