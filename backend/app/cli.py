"""CLI entry point for Orbit Workbench diagram export.

Usage:
    orbit export --type architecture_azure --file spec.json --format svg --output diagram.svg
    orbit export --type treemap --file spec.json --format png --width 1920 --height 1080
    orbit batch-export --file batch.json --format pdf --output-dir ./exports
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.models.schemas import DiagramContent, DiagramTheme, DiagramType
from app.services.exporter import DiagramExporter, ExportFormat, get_exporter

app = typer.Typer(
    name="orbit",
    help="Orbit Workbench - Editorial diagram design and export CLI",
    add_completion=False,
)
console = Console()


def load_diagram_spec(file_path: Path) -> dict:
    """Load diagram specification from JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in {file_path}: {e}[/red]")
        sys.exit(1)


def validate_format(format_str: str) -> str:
    """Validate and normalize export format."""
    format_lower = format_str.lower()
    valid_formats = [ExportFormat.SVG, ExportFormat.HTML, ExportFormat.PNG, ExportFormat.PDF]
    if format_lower not in valid_formats:
        console.print(f"[red]Error: Unsupported format '{format_str}'. Supported: {', '.join(valid_formats)}[/red]")
        sys.exit(1)
    return format_lower


def validate_theme(theme_str: str) -> DiagramTheme:
    """Validate theme name."""
    valid_themes = list(DiagramTheme.__args__) if hasattr(DiagramTheme, "__args__") else ["editorial_light", "editorial_dark", "blueprint", "warm_paper"]
    if theme_str not in valid_themes:
        console.print(f"[yellow]Warning: Unknown theme '{theme_str}', using 'editorial_light'[/yellow]")
        return "editorial_light"
    return theme_str


@app.command()
def export(
    type: DiagramType = typer.Option(..., "--type", "-t", help="Diagram type (e.g., architecture_azure, treemap, sankey)"),
    file: Path = typer.Option(..., "--file", "-f", help="Path to diagram specification JSON file", exists=True, readable=True),
    format: str = typer.Option(..., "--format", help="Export format: svg, html, png, pdf"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path (default: stdout for svg/html)"),
    theme: str = typer.Option("editorial_light", "--theme", help="Diagram theme"),
    width: int = typer.Option(1920, "--width", "-w", help="Viewport width for PNG/PDF"),
    height: int = typer.Option(1080, "--height", "-h", help="Viewport height for PNG/PDF"),
    scale: float = typer.Option(2.0, "--scale", help="Device scale factor for PNG"),
    margin_top: str = typer.Option("20mm", "--margin-top", help="Top margin for PDF"),
    margin_right: str = typer.Option("20mm", "--margin-right", help="Right margin for PDF"),
    margin_bottom: str = typer.Option("20mm", "--margin-bottom", help="Bottom margin for PDF"),
    margin_left: str = typer.Option("20mm", "--margin-left", help="Left margin for PDF"),
):
    """Export a single diagram from a specification file."""
    spec = load_diagram_spec(file)
    format_norm = validate_format(format)
    theme_norm = validate_theme(theme)

    # Extract content from spec
    content_data = spec.get("content", spec)
    content = DiagramContent(**content_data)

    exporter = get_exporter()

    kwargs = {}
    if format_norm in (ExportFormat.PNG, ExportFormat.PDF):
        kwargs.update({"width": width, "height": height})
    if format_norm == ExportFormat.PNG:
        kwargs["device_scale_factor"] = scale
    if format_norm == ExportFormat.PDF:
        kwargs["margin"] = {
            "top": margin_top,
            "right": margin_right,
            "bottom": margin_bottom,
            "left": margin_left,
        }

    console.print(f"[cyan]Exporting {type} diagram as {format_norm.upper()}...[/cyan]")

    try:
        result = exporter.export(type, content, format_norm, theme_norm, **kwargs)

        if format_norm in (ExportFormat.SVG, ExportFormat.HTML):
            if output:
                output.write_text(result)
                console.print(f"[green]Saved to {output}[/green]")
            else:
                # Print to stdout
                console.print(result)
        else:
            # Binary formats
            if not output:
                console.print("[red]Error: --output is required for PNG and PDF formats[/red]")
                sys.exit(1)
            output.write_bytes(result)
            console.print(f"[green]Saved to {output} ({len(result)} bytes)[/green]")

    except RuntimeError as e:
        if "playwright" in str(e).lower():
            console.print("[red]Error: PNG/PDF export requires playwright.[/red]")
            console.print("[yellow]Install with: pip install playwright && playwright install chromium[/yellow]")
        else:
            console.print(f"[red]Export failed: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")
        sys.exit(1)


@app.command("batch-export")
def batch_export(
    file: Path = typer.Option(..., "--file", "-f", help="Path to batch specification JSON file", exists=True, readable=True),
    format: str = typer.Option(..., "--format", help="Export format: svg, html, png, pdf"),
    output_dir: Path = typer.Option(..., "--output-dir", "-d", help="Output directory for exported files"),
    theme: str = typer.Option("editorial_light", "--theme", help="Diagram theme"),
    width: int = typer.Option(1920, "--width", "-w", help="Viewport width for PNG/PDF"),
    height: int = typer.Option(1080, "--height", "-h", help="Viewport height for PNG/PDF"),
    scale: float = typer.Option(2.0, "--scale", help="Device scale factor for PNG"),
    margin_top: str = typer.Option("20mm", "--margin-top", help="Top margin for PDF"),
    margin_right: str = typer.Option("20mm", "--margin-right", help="Right margin for PDF"),
    margin_bottom: str = typer.Option("20mm", "--margin-bottom", help="Bottom margin for PDF"),
    margin_left: str = typer.Option("20mm", "--margin-left", help="Left margin for PDF"),
):
    """Export multiple diagrams from a batch specification file.

    Batch file format:
    {
        "diagrams": [
            {"name": "diagram1", "diagram_type": "architecture_azure", "content": {...}},
            {"name": "diagram2", "diagram_type": "treemap", "content": {...}}
        ]
    }
    """
    spec = load_diagram_spec(file)
    format_norm = validate_format(format)
    theme_norm = validate_theme(theme)

    diagrams = spec.get("diagrams", [])
    if not diagrams:
        console.print("[red]Error: No diagrams found in batch file[/red]")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    kwargs = {}
    if format_norm in (ExportFormat.PNG, ExportFormat.PDF):
        kwargs.update({"width": width, "height": height})
    if format_norm == ExportFormat.PNG:
        kwargs["device_scale_factor"] = scale
    if format_norm == ExportFormat.PDF:
        kwargs["margin"] = {
            "top": margin_top,
            "right": margin_right,
            "bottom": margin_bottom,
            "left": margin_left,
        }

    console.print(f"[cyan]Batch exporting {len(diagrams)} diagrams as {format_norm.upper()}...[/cyan]")

    exporter = get_exporter()
    results = exporter.batch_export(diagrams, format_norm, theme_norm, output_dir=output_dir, **kwargs)

    # Print summary table
    table = Table(title=f"Batch Export Results ({format_norm.upper()})")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Output / Error")

    success_count = 0
    for r in results:
        if r["success"]:
            table.add_row(r["name"], "[green]Success[/green]", r.get("output_path", "N/A"))
            success_count += 1
        else:
            table.add_row(r["name"], "[red]Failed[/red]", r.get("error", "Unknown error"))

    console.print(table)
    console.print(f"\n[bold]{success_count}/{len(results)} succeeded[/bold]")

    if success_count < len(results):
        sys.exit(1)


@app.command()
def formats():
    """List supported export formats."""
    table = Table(title="Supported Export Formats")
    table.add_column("Format", style="cyan")
    table.add_column("Description")
    table.add_column("MIME Type")
    table.add_column("Requires Playwright")

    table.add_row("svg", "Scalable Vector Graphics - resolution independent", "image/svg+xml", "No")
    table.add_row("html", "Self-contained HTML document", "text/html", "No")
    table.add_row("png", "Raster image via headless browser", "image/png", "Yes")
    table.add_row("pdf", "Portable Document Format", "application/pdf", "Yes")

    console.print(table)


if __name__ == "__main__":
    app()
