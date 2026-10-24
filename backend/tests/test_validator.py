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


def test_cloud_containment_multi_vnet_valid():
    """Test multi-VNet architecture with peering passes validation."""
    valid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {
                "name": "vnet-hub",
                "subnets": [
                    {"name": "snet-gateway", "nodes": [{"id": "fw", "label": "Firewall", "type": "compute", "ip": "10.0.0.4"}]},
                ],
            },
            {
                "name": "vnet-spoke1",
                "subnets": [
                    {"name": "snet-app", "nodes": [{"id": "pe-1", "label": "pe-sql", "type": "private_endpoint", "ip": "10.1.1.5"}]},
                ],
                "paas_services": [
                    {"id": "sql-db", "label": "Azure SQL Managed", "target_pe": "pe-1", "tier": "vCore"}
                ],
            },
        ],
        "peerings": [
            {"source_vnet": "vnet-hub", "target_vnet": "vnet-spoke1"},
        ],
    }
    content = DiagramContent(title="Valid Multi-VNet Architecture", data=valid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert report.containment_compliant
    assert report.valid
    assert any("peering_valid" in r for r in report.passed_rules)


def test_cloud_containment_multi_vnet_invalid_peering():
    """Test peering to non-existent VNet fails validation."""
    invalid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {"name": "vnet-hub", "subnets": []},
        ],
        "peerings": [
            {"source_vnet": "vnet-hub", "target_vnet": "vnet-nonexistent"},
        ],
    }
    content = DiagramContent(title="Invalid Peering", data=invalid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert not report.containment_compliant
    assert any(i.rule == "containment.peering_invalid_target" for i in report.issues)


def test_cloud_containment_multi_vnet_self_peering():
    """Test self-referencing peering fails validation."""
    invalid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {"name": "vnet-hub", "subnets": []},
        ],
        "peerings": [
            {"source_vnet": "vnet-hub", "target_vnet": "vnet-hub"},
        ],
    }
    content = DiagramContent(title="Self Peering", data=invalid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert not report.containment_compliant
    assert any(i.rule == "containment.peering_self_reference" for i in report.issues)


def test_cloud_containment_multi_vnet_cross_vnet_pe_linkage():
    """Test PaaS in one VNet can reference PE in another VNet."""
    valid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {
                "name": "vnet-hub",
                "subnets": [],
            },
            {
                "name": "vnet-spoke",
                "subnets": [
                    {"name": "snet-data", "nodes": [{"id": "pe-1", "label": "pe-sql", "type": "private_endpoint", "ip": "10.1.1.5"}]},
                ],
            },
            {
                "name": "vnet-app",
                "subnets": [],
                "paas_services": [
                    {"id": "sql-db", "label": "Azure SQL", "target_pe": "pe-1", "tier": "vCore"}
                ],
            },
        ],
        "peerings": [
            {"source_vnet": "vnet-hub", "target_vnet": "vnet-spoke"},
            {"source_vnet": "vnet-hub", "target_vnet": "vnet-app"},
        ],
    }
    content = DiagramContent(title="Cross-VNet PE Linkage", data=valid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert report.containment_compliant
    assert report.valid
    assert any("private_endpoint_linkage" in r for r in report.passed_rules)


def test_cloud_containment_nsg_valid_rules():
    """Test valid NSG flow rules pass validation."""
    valid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {
                "name": "vnet-hub",
                "subnets": [
                    {"name": "snet-gateway", "nodes": [{"id": "fw", "label": "Firewall", "type": "compute", "ip": "10.0.0.4"}]},
                ],
            },
        ],
        "nsg_rules": {
            "vnet-hub/snet-gateway": [
                {
                    "name": "AllowInboundHTTPS",
                    "priority": 100,
                    "direction": "Inbound",
                    "access": "Allow",
                    "protocol": "Tcp",
                    "source_port_range": "*",
                    "destination_port_range": "443",
                    "source_address_prefix": "*",
                    "destination_address_prefix": "*",
                },
                {
                    "name": "DenyInboundSSH",
                    "priority": 200,
                    "direction": "Inbound",
                    "access": "Deny",
                    "protocol": "Tcp",
                    "source_port_range": "*",
                    "destination_port_range": "22",
                    "source_address_prefix": "*",
                    "destination_address_prefix": "*",
                },
            ],
        },
    }
    content = DiagramContent(title="Valid NSG Rules", data=valid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert report.containment_compliant
    assert report.valid
    assert any("nsg_rules_valid" in r for r in report.passed_rules)


def test_cloud_containment_nsg_invalid_subnet_reference():
    """Test NSG rules referencing non-existent subnet fails validation."""
    invalid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {"name": "vnet-hub", "subnets": []},
        ],
        "nsg_rules": {
            "vnet-hub/non-existent": [
                {"name": "TestRule", "priority": 100, "direction": "Inbound", "access": "Allow", "protocol": "Tcp"},
            ],
        },
    }
    content = DiagramContent(title="Invalid NSG Subnet", data=invalid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert not report.containment_compliant
    assert not report.valid
    assert any(i.rule == "containment.nsg_invalid_subnet_reference" for i in report.issues)


def test_cloud_containment_nsg_invalid_priority():
    """Test NSG rule with invalid priority fails validation."""
    invalid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {"name": "vnet-hub", "subnets": [{"name": "snet-gateway", "nodes": []}]},
        ],
        "nsg_rules": {
            "vnet-hub/snet-gateway": [
                {"name": "BadPriority", "priority": 50, "direction": "Inbound", "access": "Allow", "protocol": "Tcp"},
            ],
        },
    }
    content = DiagramContent(title="Invalid NSG Priority", data=invalid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert not report.containment_compliant
    assert not report.valid
    assert any(i.rule == "containment.nsg_invalid_priority" for i in report.issues)


def test_cloud_containment_nsg_invalid_direction():
    """Test NSG rule with invalid direction fails validation."""
    invalid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {"name": "vnet-hub", "subnets": [{"name": "snet-gateway", "nodes": []}]},
        ],
        "nsg_rules": {
            "vnet-hub/snet-gateway": [
                {"name": "BadDirection", "priority": 100, "direction": "Both", "access": "Allow", "protocol": "Tcp"},
            ],
        },
    }
    content = DiagramContent(title="Invalid NSG Direction", data=invalid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert not report.containment_compliant
    assert not report.valid
    assert any(i.rule == "containment.nsg_invalid_direction" for i in report.issues)


def test_cloud_containment_nsg_missing_field():
    """Test NSG rule missing required field fails validation."""
    invalid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {"name": "vnet-hub", "subnets": [{"name": "snet-gateway", "nodes": []}]},
        ],
        "nsg_rules": {
            "vnet-hub/snet-gateway": [
                {"name": "MissingProtocol", "priority": 100, "direction": "Inbound", "access": "Allow"},
            ],
        },
    }
    content = DiagramContent(title="Missing NSG Field", data=invalid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert not report.containment_compliant
    assert not report.valid
    assert any(i.rule == "containment.nsg_missing_field" for i in report.issues)


def test_cloud_containment_route_table_valid():
    """Test valid route table passes validation."""
    valid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {
                "name": "vnet-hub",
                "subnets": [
                    {"name": "snet-gateway", "nodes": [{"id": "fw", "label": "Firewall", "type": "compute", "ip": "10.0.0.4"}]},
                ],
            },
        ],
        "route_tables": {
            "vnet-hub/snet-gateway": [
                {
                    "name": "DefaultRoute",
                    "address_prefix": "0.0.0.0/0",
                    "next_hop_type": "VirtualAppliance",
                    "next_hop_ip": "10.0.0.4",
                },
                {
                    "name": "LocalVNet",
                    "address_prefix": "10.0.0.0/16",
                    "next_hop_type": "VnetLocal",
                },
            ],
        },
    }
    content = DiagramContent(title="Valid Route Table", data=valid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert report.containment_compliant
    assert report.valid
    assert any("route_tables_valid" in r for r in report.passed_rules)


def test_cloud_containment_route_table_invalid_subnet_reference():
    """Test route table referencing non-existent subnet fails validation."""
    invalid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {"name": "vnet-hub", "subnets": []},
        ],
        "route_tables": {
            "vnet-hub/non-existent": [
                {"name": "DefaultRoute", "address_prefix": "0.0.0.0/0", "next_hop_type": "Internet"},
            ],
        },
    }
    content = DiagramContent(title="Invalid Route Table Subnet", data=invalid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert not report.containment_compliant
    assert not report.valid
    assert any(i.rule == "containment.route_table_invalid_subnet_reference" for i in report.issues)


def test_cloud_containment_route_table_missing_field():
    """Test route missing required field fails validation."""
    invalid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {"name": "vnet-hub", "subnets": [{"name": "snet-gateway", "nodes": []}]},
        ],
        "route_tables": {
            "vnet-hub/snet-gateway": [
                {"name": "MissingNextHop", "address_prefix": "0.0.0.0/0"},
            ],
        },
    }
    content = DiagramContent(title="Missing Route Field", data=invalid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert not report.containment_compliant
    assert not report.valid
    assert any(i.rule == "containment.route_table_missing_field" for i in report.issues)


def test_cloud_containment_route_table_invalid_next_hop_type():
    """Test route with invalid next_hop_type fails validation."""
    invalid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {"name": "vnet-hub", "subnets": [{"name": "snet-gateway", "nodes": []}]},
        ],
        "route_tables": {
            "vnet-hub/snet-gateway": [
                {"name": "BadNextHop", "address_prefix": "0.0.0.0/0", "next_hop_type": "InvalidType"},
            ],
        },
    }
    content = DiagramContent(title="Invalid Next Hop", data=invalid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    assert not report.containment_compliant
    assert not report.valid
    assert any(i.rule == "containment.route_table_invalid_next_hop_type" for i in report.issues)


def test_cloud_containment_route_table_missing_default_route_warning():
    """Test route table without default route produces warning."""
    valid_data = {
        "subscription": "Enterprise Sub",
        "resource_group": "Core RG",
        "vnets": [
            {
                "name": "vnet-hub",
                "subnets": [
                    {"name": "snet-gateway", "nodes": [{"id": "fw", "label": "Firewall", "type": "compute", "ip": "10.0.0.4"}]},
                ],
            },
        ],
        "route_tables": {
            "vnet-hub/snet-gateway": [
                {
                    "name": "LocalVNet",
                    "address_prefix": "10.0.0.0/16",
                    "next_hop_type": "VnetLocal",
                },
            ],
        },
    }
    content = DiagramContent(title="Missing Default Route", data=valid_data)
    report = DiagramValidator.validate("architecture_azure", content)
    # Warning doesn't make containment_compliant false
    assert report.containment_compliant
    assert report.valid
    assert any(i.rule == "containment.route_table_missing_default_route" and i.severity == "warning" for i in report.issues)