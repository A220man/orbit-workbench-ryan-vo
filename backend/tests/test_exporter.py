"""Tests for diagram export service."""
import pytest
from app.models.schemas import DiagramContent, DiagramType, DiagramTheme
from app.services.exporter import DiagramExporter, ExportFormat, get_exporter


class TestDiagramExporter:
    """Test the DiagramExporter class."""

    def setup_method(self):
        self.exporter = DiagramExporter()

    def test_export_svg_architecture_azure(self):
        """Test SVG export for Azure architecture diagram."""
        content = DiagramContent(
            eyebrow="Test Architecture",
            title="Azure VNet",
            data={
                "subscription": "Test Sub",
                "resource_group": "Test RG",
                "vnets": [
                    {"name": "vnet-1", "subnets": [{"name": "snet-1", "nodes": []}]}
                ],
            },
        )
        svg = self.exporter.export_svg("architecture_azure", content)
        assert svg.startswith("<svg")
        assert "Test Architecture" in svg
        assert "Azure VNet" in svg

    def test_export_svg_treemap(self):
        """Test SVG export for treemap diagram."""
        content = DiagramContent(
            title="Test Treemap",
            data={"items": [{"label": "A", "value": 10}, {"label": "B", "value": 20}]},
        )
        svg = self.exporter.export_svg("treemap", content)
        assert svg.startswith("<svg")
        assert "Test Treemap" in svg

    def test_export_html_architecture_azure(self):
        """Test HTML export for Azure architecture diagram."""
        content = DiagramContent(
            title="Test HTML Export",
            data={
                "subscription": "Test Sub",
                "resource_group": "Test RG",
                "vnets": [{"name": "vnet-1", "subnets": [{"name": "snet-1", "nodes": []}]}],
            },
        )
        html = self.exporter.export_html("architecture_azure", content)
        assert html.startswith("<!DOCTYPE html>")
        assert "Test HTML Export" in html

    def test_export_svg_all_diagram_types(self):
        """Test SVG export works for all supported diagram types."""
        diagram_types: list[DiagramType] = [
            "architecture_azure",
            "architecture_aws",
            "treemap",
            "sankey",
            "slopegraph",
            "dumbbell",
            "waffle",
            "beeswarm",
            "sbgn_process",
            "rag_pipeline",
        ]
        for dtype in diagram_types:
            content = DiagramContent(title=f"Test {dtype}", data={})
            if dtype in {"architecture_azure", "architecture_aws"}:
                content.data = {
                    "subscription": "Sub",
                    "resource_group": "RG",
                    "vnets": [{"name": "vnet", "subnets": [{"name": "snet", "nodes": []}]}],
                }
            elif dtype == "treemap":
                content.data = {"items": [{"label": "A", "value": 10}]}
            elif dtype == "sankey":
                content.data = {"nodes": [{"id": "a"}, {"id": "b"}], "links": [{"source": "a", "target": "b", "value": 1}]}
            elif dtype == "slopegraph":
                content.data = {"series": [{"label": "A", "values": [1, 2]}]}
            elif dtype == "dumbbell":
                content.data = {"items": [{"label": "A", "before": 1, "after": 2}]}
            elif dtype == "waffle":
                content.data = {"items": [{"label": "A", "value": 5}], "rows": 5, "cols": 5}
            elif dtype == "beeswarm":
                content.data = {"items": [{"label": "A", "value": 1, "group": "G1"}]}
            elif dtype == "sbgn_process":
                content.data = {"nodes": [{"id": "n1", "type": "process"}], "edges": []}
            elif dtype == "rag_pipeline":
                content.data = {"stages": [{"name": "Retrieve", "items": 5}]}

            svg = self.exporter.export_svg(dtype, content)
            assert svg.startswith("<svg")
            assert f"Test {dtype}" in svg


class TestExportFormats:
    """Test export format constants."""

    def test_export_format_values(self):
        assert ExportFormat.SVG == "svg"
        assert ExportFormat.HTML == "html"
        assert ExportFormat.PNG == "png"
        assert ExportFormat.PDF == "pdf"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
