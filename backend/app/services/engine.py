"""Editorial diagram design engine.

Generates publication-quality, self-contained SVG + HTML diagrams with:
- Zero drop-shadows and zero gradient blurs
- Clean ink-opacity ramps and single-accent palettes
- Editorial typography (monospaced metrics, crisp labels)
- Sourced footnotes and structured eyebrows
- Deterministic geometric layouts for Cloud Architecture, Dataviz, and SBGN
"""
import html
import math
import time
from typing import Any, Dict, List, Optional, Tuple
from app.models.schemas import DiagramContent, DiagramTheme, DiagramType, RenderResponse

THEMES: Dict[str, Dict[str, str]] = {
    "editorial_light": {
        "bg": "#fbfbfb", "surface": "#ffffff", "ink": "#111827", "ink_muted": "#6b7280", "ink_faint": "#9ca3af",
        "border": "#e5e7eb", "border_dark": "#374151", "accent": "#0969da", "accent_bg": "#ddf4ff",
        "zone_l0": "#f3f4f6", "zone_l1": "#e5e7eb", "zone_l2": "#d1d5db", "zone_l3": "#ffffff",
    },
    "editorial_dark": {
        "bg": "#0f172a", "surface": "#1e293b", "ink": "#f8fafc", "ink_muted": "#94a3b8", "ink_faint": "#64748b",
        "border": "#334155", "border_dark": "#cbd5e1", "accent": "#38bdf8", "accent_bg": "#082f49",
        "zone_l0": "#111c30", "zone_l1": "#172540", "zone_l2": "#1e293b", "zone_l3": "#0f172a",
    },
    "blueprint": {
        "bg": "#0c2340", "surface": "#133560", "ink": "#f0f6fc", "ink_muted": "#8da4c4", "ink_faint": "#537299",
        "border": "#21538a", "border_dark": "#63a0e6", "accent": "#58a6ff", "accent_bg": "#1f426e",
        "zone_l0": "#0e294b", "zone_l1": "#12345e", "zone_l2": "#174277", "zone_l3": "#0c2340",
    },
    "warm_paper": {
        "bg": "#fcfbf7", "surface": "#f5f3ec", "ink": "#272421", "ink_muted": "#756f68", "ink_faint": "#aba59c",
        "border": "#e3dfd3", "border_dark": "#4a453e", "accent": "#9a3412", "accent_bg": "#ffedd5",
        "zone_l0": "#f3efe6", "zone_l1": "#eae4d7", "zone_l2": "#ded6c4", "zone_l3": "#fcfbf7",
    },
}


class EditorialEngine:
    def __init__(self, theme_name: DiagramTheme = "editorial_light"):
        self.theme_name = theme_name if theme_name in THEMES else "editorial_light"
        self.theme = THEMES[self.theme_name]

    def _rect(self, x, y, w, h, fill, stroke="", rx=0, extra="") -> str:
        s = f' stroke="{stroke}"' if stroke else ""
        r = f' rx="{rx}"' if rx else ""
        return f'<rect x="{round(x,1)}" y="{round(y,1)}" width="{round(w,1)}" height="{round(h,1)}"{r} fill="{fill}"{s} {extra}/>'

    def _text(self, x, y, txt, fill, sz=11, wt=400, mono=False, anchor="start") -> str:
        ff = "ui-monospace, monospace" if mono else "system-ui, sans-serif"
        anc = f' text-anchor="{anchor}"' if anchor != "start" else ""
        return f'<text x="{round(x,1)}" y="{round(y,1)}" font-family="{ff}" font-size="{sz}" font-weight="{wt}" fill="{fill}"{anc}>{html.escape(str(txt))}</text>'

    def render(self, diagram_type: DiagramType, content: DiagramContent) -> RenderResponse:
        t0 = time.perf_counter()
        if diagram_type in {"architecture_azure", "architecture_aws"}:
            svg, count = self._render_architecture(content, is_azure=(diagram_type == "architecture_azure"))
        elif diagram_type == "treemap":
            svg, count = self._render_treemap(content)
        elif diagram_type == "sankey":
            svg, count = self._render_sankey(content)
        elif diagram_type == "slopegraph":
            svg, count = self._render_slopegraph(content)
        elif diagram_type == "dumbbell":
            svg, count = self._render_dumbbell(content)
        elif diagram_type == "waffle":
            svg, count = self._render_waffle(content)
        elif diagram_type == "beeswarm":
            svg, count = self._render_beeswarm(content)
        elif diagram_type == "sbgn_pd":
            svg, count = self._render_sbgn(content)
        elif diagram_type == "rag_pipeline":
            svg, count = self._render_rag_pipeline(content)
        else:
            svg, count = self._render_fallback(content)

        res_html = self._wrap_html(svg, content)
        duration_ms = (time.perf_counter() - t0) * 1000.0

        return RenderResponse(
            diagram_type=diagram_type,
            theme=self.theme_name,
            svg=svg,
            html=res_html,
            element_count=count,
            render_time_ms=round(duration_ms, 2),
        )

    def _wrap_html(self, svg_code: str, content: DiagramContent) -> str:
        t = self.theme
        return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(content.title)} | Orbit</title>
<style>
:root {{ --bg: {t['bg']}; --ink: {t['ink']}; --border: {t['border']}; --accent: {t['accent']}; }}
body {{ margin: 0; padding: 24px; background: var(--bg); color: var(--ink); font-family: system-ui, sans-serif; display: flex; justify-content: center; }}
.wrap {{ max-width: 1000px; width: 100%; display: flex; flex-direction: column; gap: 14px; }}
.head {{ border-bottom: 1px solid var(--border); padding-bottom: 10px; }}
.eyebrow {{ font-size: 11px; font-weight: 600; font-family: monospace; color: var(--accent); }}
.title {{ font-size: 24px; margin: 4px 0; }}
.sub {{ font-size: 13px; color: #6b7280; }}
.foot {{ display: flex; justify-content: space-between; font-size: 11px; font-family: monospace; border-top: 1px solid var(--border); padding-top: 8px; color: #6b7280; }}
</style></head>
<body><div class="wrap"><div class="head">
{f'<div class="eyebrow">{html.escape(content.eyebrow)}</div>' if content.eyebrow else ''}
<h1 class="title">{html.escape(content.title)}</h1>
{f'<div class="sub">{html.escape(content.subtitle)}</div>' if content.subtitle else ''}
</div>{svg_code}<div class="foot"><span>{html.escape(content.footnote or '')}</span><span>{f'Source: {html.escape(content.source)}' if content.source else ''}</span></div></div></body></html>"""

    def _render_architecture(self, content: DiagramContent, is_azure: bool = True) -> Tuple[str, int]:
        t = self.theme
        w, h = 1120, 640
        elems = 0
        pname = "AZURE" if is_azure else "AWS"
        d = content.data

        sub_t = d.get("subscription", "Production Subscription")
        rg_t = d.get("resource_group", "Core Infrastructure RG")

        # Support both legacy single VNet and new multi-VNet format
        vnet_list = d.get("vnets", [])
        if not vnet_list:
            # Backward compatibility: wrap legacy single VNet
            vnet_list = [{
                "name": d.get("vnet", "Hub VNet [10.200.0.0/16]"),
                "subnets": d.get("subnets", [{"name": "snet-compute", "nodes": [{"id": "vm1", "label": "Worker", "type": "compute", "ip": "10.200.1.4"}]}]),
                "peers": []
            }]

        paas = d.get("paas_services", [{"id": "db", "label": "Azure SQL", "tier": "vCore"}])
        peerings = d.get("peerings", [])

        p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">',
             self._rect(0, 0, w, h, t["bg"]),
             self._rect(20, 20, w - 40, h - 40, t["zone_l0"], t["border"], 6),
             self._text(36, 44, f"{pname} TENANT / {sub_t}", t["accent"], 11, 600, True),
             self._text(36, 58, rg_t, t["ink"], 11, 400, True)]
        elems += 5

        # Resource group area
        rg_w, rg_h = w - 80, h - 90
        p += [self._rect(40, 72, rg_w, rg_h, t["zone_l1"], t["border"], 4)]
        elems += 1

        # Multi-VNet layout with orthogonal sibling routing
        # Sibling VNets run on perpendicular axes: first horizontal, second vertical, alternating
        num_vnets = len(vnet_list)
        vnet_positions = []  # List of (vnet_x, vnet_y, vnet_w, vnet_h, vnet_data)

        if num_vnets == 1:
            # Single VNet: centered
            vnet_w, vnet_h = rg_w - 80, rg_h - 60
            vnet_x, vnet_y = 60, 90
            vnet_positions.append((vnet_x, vnet_y, vnet_w, vnet_h, vnet_list[0]))
        elif num_vnets == 2:
            # Two sibling VNets: side by side horizontally (perpendicular to subnet vertical flow)
            vnet_w = (rg_w - 100) // 2
            vnet_h = rg_h - 60
            vnet_positions.append((60, 90, vnet_w, vnet_h, vnet_list[0]))
            vnet_positions.append((70 + vnet_w, 90, vnet_w, vnet_h, vnet_list[1]))
        elif num_vnets == 3:
            # Three VNets: two horizontal, one below (hub-spoke pattern)
            vnet_w = (rg_w - 100) // 2
            vnet_h = (rg_h - 100) // 2
            vnet_positions.append((60, 90, vnet_w, vnet_h, vnet_list[0]))  # Hub left
            vnet_positions.append((70 + vnet_w, 90, vnet_w, vnet_h, vnet_list[1]))  # Hub right
            vnet_positions.append((60, 100 + vnet_h, rg_w - 80, vnet_h, vnet_list[2]))  # Spoke below spanning both
        else:
            # 4+: grid layout, alternating axis per row
            cols = 2
            rows = (num_vnets + 1) // 2
            vnet_w = (rg_w - 100) // cols
            vnet_h = (rg_h - 100) // rows
            for i, vnet in enumerate(vnet_list):
                row = i // cols
                col = i % cols
                vnet_positions.append((60 + col * (vnet_w + 20), 90 + row * (vnet_h + 20), vnet_w, vnet_h, vnet))

        # Store VNet center points for peering connections
        vnet_centers = {}  # name -> (cx, cy)

        # Render each VNet
        for vnet_x, vnet_y, vnet_w, vnet_h, vnet in vnet_positions:
            vnet_name = vnet.get("name", "VNet")
            subnets = vnet.get("subnets", [])

            # VNet boundary (dashed stroke)
            p += [self._rect(vnet_x, vnet_y, vnet_w, vnet_h, t["zone_l2"], t["border_dark"], 4, 'stroke-dasharray="4,2"'),
                  self._text(vnet_x + 16, vnet_y + 22, vnet_name, t["accent"], 11, 600, True)]
            elems += 2

            vnet_centers[vnet_name] = (vnet_x + vnet_w // 2, vnet_y + vnet_h // 2)

            # Subnets - vertical stack within VNet
            snet_y = vnet_y + 36
            snet_h = (vnet_h - 60) // max(len(subnets), 1)
            pe_pos: Dict[str, Tuple[int, int]] = {}

            for i, snet in enumerate(subnets):
                cy = snet_y + (i * (snet_h + 10))
                sw = vnet_w - 32
                p += [self._rect(vnet_x + 16, cy, sw, snet_h, t["zone_l3"], t["border"], 3),
                      self._text(vnet_x + 30, cy + 18, snet.get("name", "Subnet"), t["ink_muted"], 10, 600, True)]
                elems += 2

                # Render NSG indicator for this subnet
                nsg_rules = d.get("nsg_rules", {}).get(f"{vnet_name}/{snet.get('name')}", [])
                if nsg_rules:
                    nsg_x, nsg_y = vnet_x + 16, cy + snet_h - 24
                    nsg_w, nsg_h = 120, 20
                    p += [self._rect(nsg_x, nsg_y, nsg_w, nsg_h, t["accent_bg"], t["accent"], 3, f'data-azure-nsg="{vnet_name}/{snet.get("name")}"'),
                          self._text(nsg_x + 60, nsg_y + 13, f"NSG: {len(nsg_rules)} rules", t["accent"], 8, 600, True, "middle")]
                    elems += 2

                # Render Route Table indicator for this subnet
                route_tables = d.get("route_tables", {}).get(f"{vnet_name}/{snet.get('name')}", [])
                if route_tables:
                    rt_x, rt_y = vnet_x + 16, cy + snet_h - 48 if nsg_rules else cy + snet_h - 24
                    rt_w, rt_h = 120, 20
                    p += [self._rect(rt_x, rt_y, rt_w, rt_h, t["accent_bg"], t["accent"], 3, f'data-azure-route-table="{vnet_name}/{snet.get("name")}"'),
                          self._text(rt_x + 60, rt_y + 13, f"RT: {len(route_tables)} routes", t["accent"], 8, 600, True, "middle")]
                    elems += 2

                nx = vnet_x + 30
                for n in snet.get("nodes", []):
                    nw, nh, ny = 260, 48, cy + 28
                    is_pe = n.get("type") == "private_endpoint"
                    sc = t["accent"] if is_pe else t["border"]
                    fc = t["accent_bg"] if is_pe else t["surface"]
                    node_id = f'{vnet_name}/{snet.get("name")}/{n.get("id")}'
                    p += [self._rect(nx, ny, nw, nh, fc, sc, 3, f'data-azure-node="{node_id}"'),
                          self._text(nx + 12, ny + 20, n.get("label", ""), t["ink"], 11, 600),
                          self._text(nx + 12, ny + 36, n.get("ip", ""), t["ink_faint"], 9.5, 400, True)]
                    elems += 3
                    if is_pe and "id" in n:
                        pe_pos[n["id"]] = (nx + nw, ny + (nh // 2))
                    nx += nw + 20

            # PaaS services for this VNet (placed to the right)
            vnet_paas = vnet.get("paas_services", paas if vnet == vnet_list[0] else [])
            px, py = vnet_x + vnet_w + 20, vnet_y + 36
            for ps in vnet_paas:
                pw, ph = 180, 70
                paas_id = f'{vnet_name}/{ps.get("id")}'
                p += [self._rect(px, py, pw, ph, t["surface"], t["accent"], 4, f'data-azure-paas="{paas_id}"'),
                      self._text(px + 12, py + 18, "PAAS SERVICE", t["accent"], 9, 600, True),
                      self._text(px + 12, py + 36, ps.get("label", ""), t["ink"], 11, 600),
                      self._text(px + 12, py + 52, ps.get("tier", ""), t["ink_muted"], 9, 400, True)]
                elems += 4

                pe_tgt = ps.get("target_pe")
                if pe_tgt and pe_tgt in pe_pos:
                    tx, ty = pe_pos[pe_tgt]
                    p += [f'<path d="M {tx} {ty} C {tx+40} {ty}, {px-30} {py+35}, {px} {py+35}" fill="none" stroke="{t["accent"]}" stroke-width="1.5" stroke-dasharray="3,3" data-azure-pe-connection="true"/>',
                          f'<circle cx="{tx}" cy="{ty}" r="3" fill="{t["accent"]}"/>',
                          f'<circle cx="{px}" cy="{py+35}" r="3" fill="{t["accent"]}"/>']
                    elems += 3
                py += ph + 20

        # Render peering connections between VNets (orthogonal routing)
        for peering in peerings:
            src = peering.get("source_vnet")
            dst = peering.get("target_vnet")
            if src in vnet_centers and dst in vnet_centers:
                sx, sy = vnet_centers[src]
                dx, dy = vnet_centers[dst]

                # Determine routing axis based on relative positions (orthogonal)
                # Sibling VNets horizontally aligned -> route vertically then horizontally
                # Hub-spoke vertically aligned -> route horizontally then vertically
                if abs(sy - dy) < 50:  # Same row (sibling VNets)
                    # Vertical detour then horizontal
                    mid_y = min(sy, dy) - 60
                    path = f'M {sx} {sy} V {mid_y} H {dx} V {dy}'
                else:  # Different rows (hub-spoke)
                    # Horizontal detour then vertical
                    mid_x = max(sx, dx) + 80
                    path = f'M {sx} {sy} H {mid_x} V {dy} H {dx}'

                p += [f'<path d="{path}" fill="none" stroke="{t["accent"]}" stroke-width="2" stroke-dasharray="6,4" data-azure-peering="{src}-{dst}" data-azure-peering-type="vnet-peering"/>']
                elems += 1

                # Peering label at midpoint
                mx, my = (sx + dx) // 2, (sy + dy) // 2
                p += [self._text(mx, my - 12, "VNet Peering", t["accent"], 9, 600, True, "middle")]
                elems += 1

        # Global PaaS services (legacy, outside any specific VNet)
        if num_vnets == 1:
            # Only render global PaaS if using legacy single VNet mode
            px, py = w - 250, 100
            for ps in paas:
                pw, ph = 180, 70
                p += [self._rect(px, py, pw, ph, t["surface"], t["accent"], 4, f'data-azure-paas="{ps.get("id")}"'),
                      self._text(px + 12, py + 18, "PAAS SERVICE", t["accent"], 9, 600, True),
                      self._text(px + 12, py + 36, ps.get("label", ""), t["ink"], 11, 600),
                      self._text(px + 12, py + 52, ps.get("tier", ""), t["ink_muted"], 9, 400, True)]
                elems += 4

                pe_tgt = ps.get("target_pe")
                # Note: in multi-VNet mode, PEs are resolved within each VNet
                py += ph + 20

        p.append("</svg>")
        return "\n".join(p), elems

    def _render_treemap(self, content: DiagramContent) -> Tuple[str, int]:
        t = self.theme
        w, h = 960, 480
        elems = 0
        items = content.data.get("items", [{"label": "Default", "value": 100}])
        total = sum(i.get("value", 0) for i in items) or 1.0

        p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">',
             self._rect(0, 0, w, h, t["bg"])]
        elems += 2

        cx, cy, rw, rh, rval = 4, 4, w - 8, h - 8, total
        for i, item in enumerate(items):
            val = item.get("value", 0)
            if rval <= 0: break
            share = val / rval
            alpha = item.get("color_alpha", max(0.25, 0.95 - (i * 0.15)))

            if rw >= rh:
                cw, ch, rx, ry = max(40.0, rw * share), rh, cx, cy
                cx += cw; rw -= cw
            else:
                cw, ch, rx, ry = rw, max(30.0, rh * share), cx, cy
                cy += ch; rh -= ch
            rval -= val

            p.append(f'<rect x="{round(rx,1)}" y="{round(ry,1)}" width="{round(cw-2,1)}" height="{round(ch-2,1)}" rx="3" fill="{t["accent"]}" fill-opacity="{alpha}" stroke="{t["border"]}" stroke-width="1" data-val="{val}"/>')
            lbl_color = "#ffffff" if alpha > 0.55 else t["ink"]
            pct = (val / total) * 100.0
            if cw > 60 and ch > 40:
                p += [self._text(rx + 10, ry + 24, item.get("label", ""), lbl_color, 12, 600),
                      self._text(rx + 10, ry + 42, f"{val} ({pct:.1f}%)", lbl_color, 11, 400, True)]
                elems += 3
            else:
                elems += 1

        p.append("</svg>")
        return "\n".join(p), elems

    def _render_sankey(self, content: DiagramContent) -> Tuple[str, int]:
        t = self.theme
        w, h = 960, 480
        elems = 0
        d = content.data
        lefts = d.get("left_nodes", [{"id": "in", "label": "Input", "value": 100}])
        rights = d.get("right_nodes", [{"id": "out", "label": "Output", "value": 100}])
        tot_l, tot_r = sum(n.get("value", 0) for n in lefts) or 1, sum(n.get("value", 0) for n in rights) or 1

        col_w, lx, rx, uh = 18, 120, w - 138, h - 100
        p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">',
             self._rect(0, 0, w, h, t["bg"])]
        elems += 2

        ly, gap = 50, 16
        sc_l = (uh - (gap * (len(lefts) - 1))) / tot_l
        l_layout = []
        for n in lefts:
            nh = max(12, n.get("value", 0) * sc_l)
            l_layout.append((n, ly, nh))
            p += [self._rect(lx, ly, col_w, nh, t["accent"], t["border_dark"], 2),
                  self._text(lx - 12, ly + (nh / 2) + 4, n.get("label", ""), t["ink"], 11, 500, False, "end"),
                  self._text(lx - 12, ly + (nh / 2) + 18, f"{n.get('value')} MW", t["ink_muted"], 9.5, 400, True, "end")]
            elems += 3
            ly += nh + gap

        ry = 50
        sc_r = (uh - (gap * (len(rights) - 1))) / tot_r
        r_layout = []
        for n in rights:
            nh = max(12, n.get("value", 0) * sc_r)
            r_layout.append((n, ry, nh))
            p += [self._rect(rx, ry, col_w, nh, t["border_dark"], t["ink"], 2),
                  self._text(rx + col_w + 12, ry + (nh / 2) + 4, n.get("label", ""), t["ink"], 11, 500),
                  self._text(rx + col_w + 12, ry + (nh / 2) + 18, f"{n.get('value')} MW", t["ink_muted"], 9.5, 400, True)]
            elems += 3
            ry += nh + gap

        for l_node, l_y, l_h in l_layout:
            for r_node, r_y, r_h in r_layout:
                fval = (l_node.get("value", 0) * r_node.get("value", 0)) / tot_l
                bh = max(2, (fval / tot_l) * uh * 0.4)
                sy = l_y + (l_h / 2)
                dy = r_y + (r_h / 2)
                x0, x1, cx = lx + col_w, rx, (lx + col_w + rx) / 2
                p.append(f'<path d="M {x0} {sy-(bh/2)} C {cx} {sy-(bh/2)}, {cx} {dy-(bh/2)}, {x1} {dy-(bh/2)} L {x1} {dy+(bh/2)} C {cx} {dy+(bh/2)}, {cx} {sy+(bh/2)}, {x0} {sy+(bh/2)} Z" fill="{t["accent"]}" fill-opacity="0.25" stroke="{t["accent"]}" stroke-opacity="0.4" stroke-width="0.5"/>')
                elems += 1

        p.append("</svg>")
        return "\n".join(p), elems

    def _render_slopegraph(self, content: DiagramContent) -> Tuple[str, int]:
        t = self.theme
        w, h = 960, 480
        elems = 0
        d = content.data
        ma, mb = d.get("moment_a_label", "Before"), d.get("moment_b_label", "After")
        items = d.get("items", [{"label": "Metric", "a": 40, "b": 80, "highlight": True}])
        xl, xr, yt, yb = 280, w - 280, 80, h - 60

        p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">',
             self._rect(0, 0, w, h, t["bg"]),
             self._text(xl, 50, ma, t["accent"], 13, 600, True, "middle"),
             self._text(xr, 50, mb, t["accent"], 13, 600, True, "middle"),
             f'<line x1="{xl}" y1="{yt}" x2="{xl}" y2="{yb}" stroke="{t["border"]}" stroke-width="1.5"/>',
             f'<line x1="{xr}" y1="{yt}" x2="{xr}" y2="{yb}" stroke="{t["border"]}" stroke-width="1.5"/>']
        elems += 6

        for item in items:
            va, vb = item.get("a", 50), item.get("b", 50)
            ya = yb - ((va / 100.0) * (yb - yt))
            yb_pos = yb - ((vb / 100.0) * (yb - yt))
            hl = item.get("highlight", False)
            col = t["accent"] if hl else t["ink_faint"]
            lw = "2.5" if hl else "1.2"
            op = "1" if hl else "0.45"

            p += [f'<line x1="{xl}" y1="{ya}" x2="{xr}" y2="{yb_pos}" stroke="{col}" stroke-width="{lw}" opacity="{op}"/>',
                  f'<circle cx="{xl}" cy="{ya}" r="4" fill="{col}"/>',
                  f'<circle cx="{xr}" cy="{yb_pos}" r="4" fill="{col}"/>',
                  self._text(xl - 16, ya + 4, f"{item.get('label')} {va}", t["ink"], 11, 600 if hl else 400, False, "end"),
                  self._text(xr + 16, yb_pos + 4, f"{vb} {item.get('label')}", t["accent"] if hl else t["ink"], 11, 600 if hl else 400, True)]
            elems += 5

        p.append("</svg>")
        return "\n".join(p), elems

    def _render_dumbbell(self, content: DiagramContent) -> Tuple[str, int]:
        t = self.theme
        w, h = 960, 480
        elems = 0
        items = content.data.get("items", [{"label": "Metric", "point_a": 30, "point_b": 80}])
        xs, xe = 240, w - 80
        scale = xe - xs
        rh = (h - 80) // max(len(items), 1)

        p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">',
             self._rect(0, 0, w, h, t["bg"])]
        elems += 2

        cy = 60
        for item in items:
            pa, pb = item.get("point_a", 0), item.get("point_b", 0)
            xa, xb = xs + ((pa / 100.0) * scale), xs + ((pb / 100.0) * scale)
            p += [self._text(xs - 24, cy + 4, item.get("label", ""), t["ink"], 12, 600, False, "end"),
                  f'<line x1="{min(xa, xb)}" y1="{cy}" x2="{max(xa, xb)}" y2="{cy}" stroke="{t["border_dark"]}" stroke-width="2"/>',
                  f'<circle cx="{xa}" cy="{cy}" r="6" fill="{t["surface"]}" stroke="{t["border_dark"]}" stroke-width="2"/>',
                  self._text(xa, cy - 10, str(pa), t["ink_muted"], 10, 400, True, "middle"),
                  f'<circle cx="{xb}" cy="{cy}" r="6" fill="{t["accent"]}" stroke="{t["accent"]}" stroke-width="2"/>',
                  self._text(xb, cy + 20, str(pb), t["accent"], 10, 600, True, "middle")]
            elems += 6
            cy += rh

        p.append("</svg>")
        return "\n".join(p), elems

    def _render_waffle(self, content: DiagramContent) -> Tuple[str, int]:
        t = self.theme
        w, h = 960, 480
        elems = 0
        cats = content.data.get("categories", [{"label": "Category", "count": 100, "color": t["accent"]}])
        tot = sum(c.get("count", 0) for c in cats) or 100
        cols, rows, sz, gap = 10, 10, 28, 6
        gw = (cols * sz) + ((cols - 1) * gap)
        sx, sy = 100, 60

        p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">',
             self._rect(0, 0, w, h, t["bg"])]
        elems += 2

        cell_colors = []
        for c in cats:
            cnt = int(round((c.get("count", 0) / tot) * 100))
            for _ in range(cnt):
                if len(cell_colors) < 100: cell_colors.append(c.get("color", t["accent"]))
        while len(cell_colors) < 100: cell_colors.append(t["border"])

        for idx, col in enumerate(cell_colors):
            r, c = idx // cols, idx % cols
            p.append(self._rect(sx + (c * (sz + gap)), sy + (r * (sz + gap)), sz, sz, col, "", 3))
            elems += 1

        lx, ly = sx + gw + 60, sy + 40
        for c in cats:
            p += [self._rect(lx, ly, 16, 16, c.get("color", t["accent"]), "", 2),
                  self._text(lx + 28, ly + 13, c.get("label", ""), t["ink"], 12, 600),
                  self._text(lx + 28, ly + 28, f"{c.get('count')} / {tot}", t["ink_muted"], 11, 400, True)]
            elems += 3
            ly += 54

        p.append("</svg>")
        return "\n".join(p), elems

    def _render_beeswarm(self, content: DiagramContent) -> Tuple[str, int]:
        t = self.theme
        w, h = 960, 480
        elems = 0
        samples = content.data.get("samples", [{"val": 50, "label": "Model"}])
        mx, ay = 80, h // 2
        alen = w - (mx * 2)

        p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">',
             self._rect(0, 0, w, h, t["bg"]),
             f'<line x1="{mx}" y1="{ay}" x2="{w - mx}" y2="{ay}" stroke="{t["border_dark"]}" stroke-width="1.5"/>']
        elems += 3

        for tick in [0, 25, 50, 75, 100]:
            tx = mx + ((tick / 100.0) * alen)
            p += [f'<line x1="{tx}" y1="{ay-6}" x2="{tx}" y2="{ay+6}" stroke="{t["border_dark"]}" stroke-width="1.5"/>',
                  self._text(tx, ay + 24, str(tick), t["ink_muted"], 10, 400, True, "middle")]
            elems += 2

        for i, s in enumerate(samples):
            v = s.get("val", 50)
            cx = mx + ((v / 100.0) * alen)
            cy = ay + (math.sin(i * 2.3) * 36)
            p += [f'<circle cx="{cx}" cy="{cy}" r="7" fill="{t["accent"]}" fill-opacity="0.8" stroke="{t["bg"]}" stroke-width="1.5"/>',
                  self._text(cx, cy - 12, s.get("label", ""), t["ink"], 10, 500, False, "middle")]
            elems += 2

        p.append("</svg>")
        return "\n".join(p), elems

    def _render_sbgn(self, content: DiagramContent) -> Tuple[str, int]:
        t = self.theme
        w, h = 960, 480
        elems = 0
        d = content.data
        macros = d.get("macromolecules", [{"id": "m1", "label": "Protein", "x": 100, "y": 140}])
        comps = d.get("complexes", [{"id": "c1", "label": "Complex", "x": 340, "y": 180, "w": 180, "h": 100}])

        p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">',
             self._rect(0, 0, w, h, t["bg"])]
        elems += 2

        for c in comps:
            cx, cy, cw, ch = c["x"], c["y"], c["w"], c["h"]
            p += [self._rect(cx, cy, cw, ch, t["zone_l1"], t["border_dark"], 14, 'data-sbgn-class="complex"'),
                  self._text(cx + 14, cy + 24, "COMPLEX", t["accent"], 10, 600, True),
                  self._text(cx + 14, cy + 46, c.get("label", ""), t["ink"], 12, 600)]
            elems += 3

        for m in macros:
            mx, my = m["x"], m["y"]
            p += [self._rect(mx, my, 140, 52, t["surface"], t["accent"], 8, 'data-sbgn-class="macromolecule"'),
                  self._text(mx + 70, my + 30, m.get("label", ""), t["ink"], 12, 600, False, "middle")]
            elems += 2

        tx, ty = 280, 230
        p += [self._rect(tx - 8, ty - 8, 16, 16, t["ink"], t["border_dark"], 0, 'data-sbgn-class="transition"'),
              f'<line x1="240" y1="166" x2="{tx}" y2="{ty}" stroke="{t["ink"]}" stroke-width="1.5"/>',
              f'<line x1="{tx}" y1="{ty}" x2="340" y2="230" stroke="{t["ink"]}" stroke-width="1.5"/>']
        elems += 3

        p.append("</svg>")
        return "\n".join(p), elems

    def _render_rag_pipeline(self, content: DiagramContent) -> Tuple[str, int]:
        t = self.theme
        w, h = 960, 480
        elems = 0
        stages = [
            {"title": "User Query", "sub": "Raw prompt", "x": 60, "w": 120},
            {"title": "Query Rewriter", "sub": "HyDE / HyPO", "x": 220, "w": 140},
            {"title": "Hybrid Retrieval", "sub": "Vector + BM25", "x": 400, "w": 150},
            {"title": "Cross-Encoder", "sub": "Reranking", "x": 590, "w": 140},
            {"title": "Generator", "sub": "Grounded LLM", "x": 770, "w": 130},
        ]

        p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">',
             self._rect(0, 0, w, h, t["bg"])]
        elems += 2

        sy, sh = 190, 70
        for i, s in enumerate(stages):
            sx, sw = s["x"], s["w"]
            is_acc = i in {2, 4}
            fc = t["accent_bg"] if is_acc else t["surface"]
            sc = t["accent"] if is_acc else t["border"]
            p += [self._rect(sx, sy, sw, sh, fc, sc, 4),
                  self._text(sx + 12, sy + 26, s["title"], t["ink"], 11, 600),
                  self._text(sx + 12, sy + 46, s["sub"], t["ink_muted"], 9, 400, True)]
            elems += 3

            if i < len(stages) - 1:
                nx = stages[i + 1]["x"]
                p += [f'<line x1="{sx+sw}" y1="{sy+(sh//2)}" x2="{nx}" y2="{sy+(sh//2)}" stroke="{t["accent"]}" stroke-width="1.5"/>',
                      f'<polygon points="{nx},{sy+(sh//2)} {nx-6},{sy+(sh//2)-3} {nx-6},{sy+(sh//2)+3}" fill="{t["accent"]}"/>']
                elems += 2

        p.append("</svg>")
        return "\n".join(p), elems

    def _render_fallback(self, content: DiagramContent) -> Tuple[str, int]:
        t = self.theme
        w, h = 960, 400
        p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">',
             self._rect(0, 0, w, h, t["bg"]),
             self._rect(40, 40, w - 80, h - 80, t["surface"], t["border"], 6),
             self._text(w // 2, h // 2, content.title, t["ink"], 14, 600, False, "middle"),
             "</svg>"]
        return "\n".join(p), 3
