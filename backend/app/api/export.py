"""Diagram export API endpoints.

Provides programmatic export API for integration into CI/CD pipelines.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from app.models.schemas import DiagramContent, DiagramTheme, DiagramType
from app.services.exporter import DiagramExporter, ExportFormat, get_exporter

router = APIRouter(prefix="/export", tags=["Export"])


class ExportRequest(BaseModel):
    """Single diagram export request."""

    diagram_type: DiagramType = Field(..., description="Type of diagram to export")
    content: DiagramContent = Field(..., description="Diagram content specification")
    format: str = Field(
        ...,
        description=f"Export format. Supported: {', '.join([ExportFormat.SVG, ExportFormat.HTML, ExportFormat.PNG, ExportFormat.PDF])}",
    )
    theme: DiagramTheme = Field("editorial_light", description="Diagram theme")
    # PNG/PDF specific options
    width: int = Field(1920, ge=100, le=8000, description="Viewport width for PNG/PDF")
    height: int = Field(1080, ge=100, le=8000, description="Viewport height for PNG/PDF")
    device_scale_factor: float = Field(2.0, ge=0.5, le=4.0, description="Device scale factor for PNG")
    margin: Optional[Dict[str, str]] = Field(
        None, description="Page margins for PDF (e.g., {'top': '20mm', 'bottom': '20mm'})"
    )


class BatchExportRequest(BaseModel):
    """Batch export request for multiple diagrams."""

    diagrams: List[Dict[str, Any]] = Field(
        ...,
        description="List of diagrams to export. Each item: {diagram_type, content, name?, ...}",
        min_items=1,
        max_items=50,
    )
    format: str = Field(
        ...,
        description=f"Export format. Supported: {', '.join([ExportFormat.SVG, ExportFormat.HTML, ExportFormat.PNG, ExportFormat.PDF])}",
    )
    theme: DiagramTheme = Field("editorial_light", description="Diagram theme")
    # PNG/PDF specific options
    width: int = Field(1920, ge=100, le=8000)
    height: int = Field(1080, ge=100, le=8000)
    device_scale_factor: float = Field(2.0, ge=0.5, le=4.0)
    margin: Optional[Dict[str, str]] = Field(None)


@router.post(
    "",
    responses={
        200: {
            "content": {"image/svg+xml": {}, "text/html": {}, "image/png": {}, "application/pdf": {}},
            "description": "Exported diagram in requested format",
        },
        400: {"description": "Invalid request or unsupported format"},
        500: {"description": "Export failed (e.g., missing playwright for PNG/PDF)"},
    },
)
async def export_diagram(request: ExportRequest):
    """Export a single diagram to the specified format.

    Returns the exported file directly with appropriate Content-Type header.
    For PNG/PDF, requires playwright to be installed.
    """
    exporter = get_exporter()
    format_lower = request.format.lower()

    # Validate format
    valid_formats = [ExportFormat.SVG, ExportFormat.HTML, ExportFormat.PNG, ExportFormat.PDF]
    if format_lower not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{request.format}'. Supported: {', '.join(valid_formats)}",
        )

    try:
        # Prepare format-specific kwargs
        kwargs = {}
        if format_lower in (ExportFormat.PNG, ExportFormat.PDF):
            kwargs.update(
                {
                    "width": request.width,
                    "height": request.height,
                }
            )
        if format_lower == ExportFormat.PNG:
            kwargs["device_scale_factor"] = request.device_scale_factor
        if format_lower == ExportFormat.PDF:
            kwargs["margin"] = request.margin

        result = exporter.export(
            request.diagram_type,
            request.content,
            format_lower,
            request.theme,
            **kwargs,
        )

        # Return appropriate response based on format
        if format_lower == ExportFormat.SVG:
            return Response(content=result, media_type="image/svg+xml")
        elif format_lower == ExportFormat.HTML:
            return Response(content=result, media_type="text/html")
        elif format_lower == ExportFormat.PNG:
            return Response(content=result, media_type="image/png")
        elif format_lower == ExportFormat.PDF:
            return Response(content=result, media_type="application/pdf")

    except RuntimeError as e:
        if "playwright" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PNG/PDF export requires playwright. Install with: pip install playwright && playwright install chromium",
            )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {str(e)}")


@router.post("/batch", response_model=List[Dict[str, Any]])
async def batch_export_diagrams(request: BatchExportRequest):
    """Export multiple diagrams in batch.

    Returns a list of results with success status and either output data or error.
    For binary formats (PNG/PDF), data is returned as base64-encoded strings.
    """
    exporter = get_exporter()
    format_lower = request.format.lower()

    valid_formats = [ExportFormat.SVG, ExportFormat.HTML, ExportFormat.PNG, ExportFormat.PDF]
    if format_lower not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{request.format}'. Supported: {', '.join(valid_formats)}",
        )

    kwargs = {}
    if format_lower in (ExportFormat.PNG, ExportFormat.PDF):
        kwargs.update({"width": request.width, "height": request.height})
    if format_lower == ExportFormat.PNG:
        kwargs["device_scale_factor"] = request.device_scale_factor
    if format_lower == ExportFormat.PDF:
        kwargs["margin"] = request.margin

    try:
        results = exporter.batch_export(
            request.diagrams,
            format_lower,
            request.theme,
            output_dir=None,  # Return data in response, not saved to disk
            **kwargs,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Batch export failed: {str(e)}")


@router.get("/formats")
async def list_export_formats():
    """List supported export formats."""
    return {
        "formats": [
            {
                "id": ExportFormat.SVG,
                "name": "SVG",
                "description": "Scalable Vector Graphics - resolution independent, ideal for web and print",
                "mime_type": "image/svg+xml",
                "requires_playwright": False,
            },
            {
                "id": ExportFormat.HTML,
                "name": "HTML",
                "description": "Self-contained HTML document with embedded styles and scripts",
                "mime_type": "text/html",
                "requires_playwright": False,
            },
            {
                "id": ExportFormat.PNG,
                "name": "PNG",
                "description": "Raster image via headless browser rendering",
                "mime_type": "image/png",
                "requires_playwright": True,
            },
            {
                "id": ExportFormat.PDF,
                "name": "PDF",
                "description": "Portable Document Format via headless browser printing",
                "mime_type": "application/pdf",
                "requires_playwright": True,
            },
        ]
    }
