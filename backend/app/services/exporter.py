"""Multi-format diagram export service.

Supports SVG, HTML, PNG (via headless browser), and PDF output formats.
Provides both programmatic API and CLI integration.
"""
import asyncio
import base64
import html
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from app.models.schemas import DiagramContent, DiagramType, DiagramTheme, RenderResponse
from app.services.engine import EditorialEngine, THEMES


class ExportFormat:
    SVG = "svg"
    HTML = "html"
    PNG = "png"
    PDF = "pdf"


class DiagramExporter:
    """Exports diagrams to multiple formats with configurable themes."""

    def __init__(self):
        self.engine_cache: Dict[DiagramTheme, EditorialEngine] = {}

    def _get_engine(self, theme: DiagramTheme) -> EditorialEngine:
        if theme not in self.engine_cache:
            self.engine_cache[theme] = EditorialEngine(theme_name=theme)
        return self.engine_cache[theme]

    def export_svg(
        self,
        diagram_type: DiagramType,
        content: DiagramContent,
        theme: DiagramTheme = "editorial_light",
    ) -> str:
        """Export diagram as raw SVG string."""
        engine = self._get_engine(theme)
        response: RenderResponse = engine.render(diagram_type, content)
        return response.svg

    def export_html(
        self,
        diagram_type: DiagramType,
        content: DiagramContent,
        theme: DiagramTheme = "editorial_light",
    ) -> str:
        """Export diagram as self-contained HTML document."""
        engine = self._get_engine(theme)
        response: RenderResponse = engine.render(diagram_type, content)
        return response.html

    async def export_png(
        self,
        diagram_type: DiagramType,
        content: DiagramContent,
        theme: DiagramTheme = "editorial_light",
        width: int = 1920,
        height: int = 1080,
        device_scale_factor: float = 2.0,
    ) -> bytes:
        """Export diagram as PNG using headless browser (playwright).

        Requires playwright to be installed: pip install playwright && playwright install chromium
        """
        html_content = self.export_html(diagram_type, content, theme)

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "PNG export requires playwright. Install with: pip install playwright && playwright install chromium"
            )

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": width, "height": height})
            await page.set_content(html_content, wait_until="networkidle")

            # Wait for any animations/transitions to complete
            await page.wait_for_timeout(500)

            png_bytes = await page.screenshot(
                type="png",
                full_page=True,
                scale="device",
            )
            await browser.close()

            return png_bytes

    async def export_pdf(
        self,
        diagram_type: DiagramType,
        content: DiagramContent,
        theme: DiagramTheme = "editorial_light",
        width: int = 1920,
        height: int = 1080,
        margin: Dict[str, str] = None,
    ) -> bytes:
        """Export diagram as PDF using headless browser (playwright).

        Requires playwright to be installed: pip install playwright && playwright install chromium
        """
        html_content = self.export_html(diagram_type, content, theme)

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "PDF export requires playwright. Install with: pip install playwright && playwright install chromium"
            )

        if margin is None:
            margin = {"top": "20mm", "right": "20mm", "bottom": "20mm", "left": "20mm"}

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": width, "height": height})
            await page.set_content(html_content, wait_until="networkidle")
            await page.wait_for_timeout(500)

            pdf_bytes = await page.pdf(
                format="A4",
                margin=margin,
                print_background=True,
                prefer_css_page_size=True,
            )
            await browser.close()

            return pdf_bytes

    def export(
        self,
        diagram_type: DiagramType,
        content: DiagramContent,
        format: str,
        theme: DiagramTheme = "editorial_light",
        **kwargs,
    ) -> Union[str, bytes]:
        """Export diagram to specified format (synchronous for svg/html, async for png/pdf)."""
        if format == ExportFormat.SVG:
            return self.export_svg(diagram_type, content, theme)
        elif format == ExportFormat.HTML:
            return self.export_html(diagram_type, content, theme)
        elif format == ExportFormat.PNG:
            return asyncio.run(self.export_png(diagram_type, content, theme, **kwargs))
        elif format == ExportFormat.PDF:
            return asyncio.run(self.export_pdf(diagram_type, content, theme, **kwargs))
        else:
            raise ValueError(f"Unsupported export format: {format}. Supported: {list(ExportFormat.__dict__.values())}")

    def batch_export(
        self,
        diagrams: List[Dict[str, Any]],
        format: str,
        theme: DiagramTheme = "editorial_light",
        output_dir: Optional[Path] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Export multiple diagrams in batch.

        Args:
            diagrams: List of dicts with keys: diagram_type, content, name (optional)
            format: Export format
            theme: Diagram theme
            output_dir: Optional directory to save files
            **kwargs: Additional format-specific options

        Returns:
            List of result dicts with keys: name, success, output_path/error, data
        """
        results = []

        for idx, diagram in enumerate(diagrams):
            diagram_type = diagram.get("diagram_type")
            content_data = diagram.get("content")
            name = diagram.get("name") or f"diagram_{idx}"

            try:
                if isinstance(content_data, dict):
                    content = DiagramContent(**content_data)
                else:
                    content = content_data

                if format in (ExportFormat.SVG, ExportFormat.HTML):
                    data = self.export(diagram_type, content, format, theme)
                    if output_dir:
                        ext = ".svg" if format == ExportFormat.SVG else ".html"
                        output_path = output_dir / f"{name}{ext}"
                        output_path.write_text(data)
                        results.append({"name": name, "success": True, "output_path": str(output_path)})
                    else:
                        results.append({"name": name, "success": True, "data": data})
                else:
                    # For async formats, run in event loop
                    data = self.export(diagram_type, content, format, theme, **kwargs)
                    if output_dir:
                        ext = ".png" if format == ExportFormat.PNG else ".pdf"
                        output_path = output_dir / f"{name}{ext}"
                        output_path.write_bytes(data)
                        results.append({"name": name, "success": True, "output_path": str(output_path)})
                    else:
                        # Encode binary as base64 for JSON serialization
                        results.append({
                            "name": name,
                            "success": True,
                            "data": base64.b64encode(data).decode("utf-8"),
                            "encoding": "base64",
                        })

            except Exception as e:
                results.append({"name": name, "success": False, "error": str(e)})

        return results


# Singleton instance for module-level use
_exporter_instance: Optional[DiagramExporter] = None


def get_exporter() -> DiagramExporter:
    """Get or create the singleton DiagramExporter instance."""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = DiagramExporter()
    return _exporter_instance
