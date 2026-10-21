"""Unit tests for the editorial vector diagram layout engine."""
from app.models.schemas import DiagramContent
from app.services.engine import EditorialEngine


def test_render_cloud_architecture_azure():
    engine = EditorialEngine(theme_name="editorial_light")
    content = DiagramContent(
        eyebrow="CLOUD TOPOLOGY",
        title="Azure Production Topology",
        data={
            "subscription": "Enterprise Sub",
            "resource_group": "rg-network",
            "vnet": "vnet-hub-10.0.0.0/16",
            "subnets": [
                {
                    "name": "snet-app",
                    "nodes": [{"id": "vm1", "label": "Worker VM", "type": "compute", "ip": "10.0.1.4"}],
                }
            ],
            "paas_services": [
                {"id": "db1", "label": "Azure SQL", "tier": "General Purpose"}
            ],
        },
    )
    res = engine.render("architecture_azure", content)
    assert res.diagram_type == "architecture_azure"
    assert "<svg" in res.svg
    assert "Enterprise Sub" in res.svg
    assert "Worker VM" in res.svg
    assert "feDropShadow" not in res.svg  # Zero shadows rule
    assert res.element_count > 5
    assert res.render_time_ms >= 0


def test_render_treemap_honest_encoding():
    engine = EditorialEngine(theme_name="warm_paper")
    content = DiagramContent(
        title="Energy Sources",
        data={
            "items": [
                {"label": "Solar", "value": 50},
                {"label": "Wind", "value": 30},
                {"label": "Hydro", "value": 20},
            ]
        },
    )
    res = engine.render("treemap", content)
    assert "<svg" in res.svg
    assert "Solar" in res.svg
    assert 'data-val="50"' in res.svg
    assert "50 (50.0%)" in res.svg


def test_render_sankey_flow():
    engine = EditorialEngine(theme_name="editorial_dark")
    content = DiagramContent(
        title="Energy Flow",
        data={
            "left_nodes": [{"id": "solar", "label": "Solar Farm", "value": 100}],
            "right_nodes": [{"id": "grid", "label": "Power Grid", "value": 100}],
        },
    )
    res = engine.render("sankey", content)
    assert "<svg" in res.svg
    assert "Solar Farm" in res.svg
    assert "Power Grid" in res.svg
    assert "<path d=\"M" in res.svg  # Cubic bezier band


def test_render_slopegraph():
    engine = EditorialEngine()
    content = DiagramContent(
        title="Model Accuracy Shift",
        data={
            "moment_a_label": "Pre-training",
            "moment_b_label": "RLHF",
            "items": [{"label": "Helpfulness", "a": 40, "b": 90, "highlight": True}],
        },
    )
    res = engine.render("slopegraph", content)
    assert "Pre-training" in res.svg
    assert "RLHF" in res.svg
    assert "Helpfulness" in res.svg


def test_render_sbgn_process_description():
    engine = EditorialEngine()
    content = DiagramContent(
        title="Biochemical Cascade",
        data={
            "macromolecules": [{"id": "prot_a", "label": "Protein A", "x": 100, "y": 100}],
            "complexes": [{"id": "comp_1", "label": "Active Complex", "x": 300, "y": 100, "w": 180, "h": 90}],
        },
    )
    res = engine.render("sbgn_pd", content)
    assert 'data-sbgn-class="macromolecule"' in res.svg
    assert 'data-sbgn-class="complex"' in res.svg
    assert "Protein A" in res.svg


def test_render_dumbbell_and_waffle():
    engine = EditorialEngine()
    content_db = DiagramContent(
        title="Dumbbell Evaluation",
        data={"items": [{"label": "Precision", "point_a": 30, "point_b": 80}]},
    )
    res_db = engine.render("dumbbell", content_db)
    assert "Precision" in res_db.svg

    content_wf = DiagramContent(
        title="Waffle Alignment",
        data={"categories": [{"label": "Compliant", "count": 80, "color": "#0969da"}]},
    )
    res_wf = engine.render("waffle", content_wf)
    assert "<rect" in res_wf.svg
    assert "Compliant" in res_wf.svg


def test_render_multi_vnet_architecture_with_peering():
    engine = EditorialEngine(theme_name="editorial_light")
    content = DiagramContent(
        eyebrow="MULTI-VNET TOPOLOGY",
        title="Hub-Spoke Azure Architecture with Peering",
        data={
            "subscription": "Enterprise Sub",
            "resource_group": "rg-network",
            "vnets": [
                {
                    "name": "vnet-hub",
                    "subnets": [
                        {"name": "snet-gateway", "nodes": [{"id": "fw", "label": "Firewall", "type": "compute", "ip": "10.0.0.4"}]},
                        {"name": "snet-shared", "nodes": [{"id": "lb", "label": "Load Balancer", "type": "compute", "ip": "10.0.1.4"}]},
                    ],
                    "peers": ["vnet-spoke1", "vnet-spoke2"],
                },
                {
                    "name": "vnet-spoke1",
                    "subnets": [
                        {"name": "snet-app", "nodes": [{"id": "vm1", "label": "App VM", "type": "compute", "ip": "10.1.1.4"}]},
                    ],
                    "paas_services": [
                        {"id": "db1", "label": "App SQL", "tier": "General Purpose", "target_pe": "sql-pe"}
                    ],
                },
                {
                    "name": "vnet-spoke2",
                    "subnets": [
                        {"name": "snet-data", "nodes": [
                            {"id": "vm2", "label": "Data VM", "type": "compute", "ip": "10.2.1.4"},
                            {"id": "sql-pe", "label": "SQL Private Endpoint", "type": "private_endpoint", "ip": "10.2.2.5"},
                        ]},
                    ],
                    "paas_services": [
                        {"id": "db2", "label": "Data SQL", "tier": "Business Critical", "target_pe": "sql-pe"}
                    ],
                },
            ],
            "peerings": [
                {"source_vnet": "vnet-hub", "target_vnet": "vnet-spoke1"},
                {"source_vnet": "vnet-hub", "target_vnet": "vnet-spoke2"},
            ],
        },
    )
    res = engine.render("architecture_azure", content)
    assert res.diagram_type == "architecture_azure"
    assert "<svg" in res.svg
    assert "Enterprise Sub" in res.svg  # Subscription in SVG
    assert "MULTI-VNET TOPOLOGY" in res.html  # Eyebrow in HTML wrapper
    assert "Hub-Spoke Azure Architecture with Peering" in res.html  # Title in HTML wrapper
    assert "vnet-hub" in res.svg
    assert "vnet-spoke1" in res.svg
    assert "vnet-spoke2" in res.svg
    assert "VNet Peering" in res.svg
    assert 'data-azure-peering="vnet-hub-vnet-spoke1"' in res.svg
    assert 'data-azure-peering="vnet-hub-vnet-spoke2"' in res.svg
    assert 'data-azure-node="vnet-hub/snet-gateway/fw"' in res.svg
    assert 'data-azure-node="vnet-spoke1/snet-app/vm1"' in res.svg
    assert 'data-azure-pe-connection="true"' in res.svg  # PaaS to private endpoint (at least one)
    assert "feDropShadow" not in res.svg
    assert res.element_count > 20
    assert res.render_time_ms >= 0