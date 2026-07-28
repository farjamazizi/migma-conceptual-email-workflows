#!/usr/bin/env python3
"""Create two presentation-ready Migma workflow diagrams.

The SVG files are generated with Python's standard library only. PNG export is
optional and uses ImageMagick when its ``magick`` or ``convert`` command is
available on the system.

Examples:
    python draw_diagrams.py
    python draw_diagrams.py --format svg --output-dir build
    python draw_diagrams.py --format both
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape


WIDTH = 1920
HEIGHT = 1080
FONT_FAMILY = "DejaVu Sans, Arial, sans-serif"


@dataclass(frozen=True)
class Theme:
    background: str = "#F6F8FC"
    surface: str = "#FFFFFF"
    ink: str = "#172033"
    body: str = "#4E5A70"
    muted: str = "#7A859A"
    line: str = "#DDE3EE"
    connector: str = "#8B95AA"
    blue: str = "#3A67F7"
    purple: str = "#7956F6"
    cyan: str = "#20A4C8"
    green: str = "#2B9B78"
    amber: str = "#D88B27"


THEME = Theme()


class SVG:
    """Small SVG builder with presentation-oriented drawing helpers."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.items: list[str] = []

    @staticmethod
    def _attrs(**attrs: object) -> str:
        normalized: list[str] = []
        for key, value in attrs.items():
            if value is None:
                continue
            key = key.rstrip("_").replace("_", "-")
            normalized.append(f'{key}="{escape(str(value))}"')
        return " ".join(normalized)

    def raw(self, markup: str) -> None:
        self.items.append(markup)

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        rx: float = 0,
        fill: str = "none",
        stroke: str = "none",
        stroke_width: float = 0,
        filter_: str | None = None,
        opacity: float | None = None,
    ) -> None:
        attrs = self._attrs(
            x=x,
            y=y,
            width=width,
            height=height,
            rx=rx,
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_width,
            filter=filter_,
            opacity=opacity,
        )
        self.raw(f"<rect {attrs}/>")

    def circle(
        self,
        cx: float,
        cy: float,
        radius: float,
        *,
        fill: str = "none",
        stroke: str = "none",
        stroke_width: float = 0,
    ) -> None:
        attrs = self._attrs(
            cx=cx,
            cy=cy,
            r=radius,
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_width,
        )
        self.raw(f"<circle {attrs}/>")

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke: str,
        stroke_width: float = 2,
        dash: str | None = None,
        marker_end: str | None = None,
        linecap: str = "round",
    ) -> None:
        attrs = self._attrs(
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            stroke=stroke,
            stroke_width=stroke_width,
            stroke_dasharray=dash,
            marker_end=marker_end,
            stroke_linecap=linecap,
        )
        self.raw(f"<line {attrs}/>")

    def path(
        self,
        d: str,
        *,
        fill: str = "none",
        stroke: str = "none",
        stroke_width: float = 0,
        dash: str | None = None,
        marker_end: str | None = None,
        linecap: str = "round",
        linejoin: str = "round",
    ) -> None:
        attrs = self._attrs(
            d=d,
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_width,
            stroke_dasharray=dash,
            marker_end=marker_end,
            stroke_linecap=linecap,
            stroke_linejoin=linejoin,
        )
        self.raw(f"<path {attrs}/>")

    def text(
        self,
        x: float,
        y: float,
        content: str,
        *,
        size: float,
        fill: str,
        weight: int = 400,
        anchor: str = "start",
        letter_spacing: float | None = None,
        opacity: float | None = None,
    ) -> None:
        attrs = self._attrs(
            x=x,
            y=y,
            font_family=FONT_FAMILY,
            font_size=size,
            font_weight=weight,
            fill=fill,
            text_anchor=anchor,
            letter_spacing=letter_spacing,
            opacity=opacity,
        )
        self.raw(f"<text {attrs}>{escape(content)}</text>")

    def write(self, path: Path) -> None:
        defs = """
  <defs>
    <linearGradient id="backgroundGradient" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FBFCFE"/>
      <stop offset="100%" stop-color="#F1F4FA"/>
    </linearGradient>
    <linearGradient id="titleGradient" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#315FE8"/>
      <stop offset="100%" stop-color="#8059F5"/>
    </linearGradient>
    <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="7" stdDeviation="10"
                    flood-color="#172033" flood-opacity="0.08"/>
    </filter>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="150%">
      <feDropShadow dx="0" dy="4" stdDeviation="6"
                    flood-color="#172033" flood-opacity="0.10"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="8.5" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#8B95AA"/>
    </marker>
    <marker id="feedbackArrow" viewBox="0 0 10 10" refX="8.5" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#7956F6"/>
    </marker>
    <pattern id="dotGrid" width="32" height="32" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="1.5" fill="#CCD4E2" opacity="0.32"/>
    </pattern>
  </defs>
"""
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
            f'role="img" aria-labelledby="title desc">\n'
            f"  <title id=\"title\">{escape(self.title)}</title>\n"
            "  <desc id=\"desc\">Conceptual system diagram prepared for "
            "presentation.</desc>\n"
            f"{defs}"
            + "\n".join(f"  {item}" for item in self.items)
            + "\n</svg>\n"
        )
        path.write_text(svg, encoding="utf-8")


def add_slide_background(svg: SVG) -> None:
    svg.rect(0, 0, WIDTH, HEIGHT, fill="url(#backgroundGradient)")
    svg.rect(0, 0, WIDTH, HEIGHT, fill="url(#dotGrid)")
    svg.circle(1810, 25, 260, fill="#E9E5FF")
    svg.circle(1810, 25, 190, fill="#F0EDFF")
    svg.circle(70, 1050, 220, fill="#E8F2FF")


def add_header(svg: SVG, eyebrow: str, title: str, subtitle: str) -> None:
    svg.rect(92, 60, 7, 88, rx=3.5, fill="url(#titleGradient)")
    svg.text(
        122,
        74,
        eyebrow,
        size=16,
        fill=THEME.blue,
        weight=700,
        letter_spacing=2.2,
    )
    svg.text(122, 127, title, size=43, fill=THEME.ink, weight=700)
    svg.text(122, 161, subtitle, size=19, fill=THEME.muted, weight=400)


def add_authorship_footer(svg: SVG) -> None:
    svg.text(
        WIDTH / 2,
        1059,
        (
            "Prepared by Farjam Azizi  ·  Conceptual view based on Migma’s "
            "public documentation  ·  Internal implementation may differ"
        ),
        size=12.5,
        fill=THEME.muted,
        weight=400,
        anchor="middle",
        letter_spacing=0.15,
    )


def add_bullet(svg: SVG, x: float, y: float, label: str, color: str) -> None:
    svg.circle(x, y - 6, 3.5, fill=color)
    svg.text(x + 16, y, label, size=19, fill=THEME.body, weight=400)


def add_contract_card(
    svg: SVG,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    number: int,
    title: str,
    color: str,
    columns: list[list[str]],
) -> None:
    svg.rect(
        x,
        y,
        width,
        height,
        rx=18,
        fill=THEME.surface,
        stroke=THEME.line,
        stroke_width=1.2,
        filter_="url(#cardShadow)",
    )
    svg.rect(x, y, 9, height, rx=4.5, fill=color)
    svg.circle(x + 54, y + 42, 25, fill=color)
    svg.text(
        x + 54,
        y + 49,
        f"{number:02d}",
        size=17,
        fill="#FFFFFF",
        weight=700,
        anchor="middle",
        letter_spacing=0.5,
    )
    svg.text(
        x + 99,
        y + 50,
        title,
        size=21,
        fill=THEME.ink,
        weight=700,
        letter_spacing=0.9,
    )

    content_x = x + 99
    available_width = width - 133
    column_width = available_width / max(len(columns), 1)
    first_y = y + 84
    line_height = 27
    for column_index, labels in enumerate(columns):
        item_x = content_x + column_index * column_width
        for line_index, label in enumerate(labels):
            add_bullet(
                svg,
                item_x,
                first_y + line_index * line_height,
                label,
                color,
            )


def add_vertical_connector(svg: SVG, center_x: float, y1: float, y2: float) -> None:
    svg.line(
        center_x,
        y1,
        center_x,
        y2 - 11,
        stroke=THEME.connector,
        stroke_width=3,
    )
    svg.path(
        f"M {center_x - 7} {y2 - 12} L {center_x} {y2} "
        f"L {center_x + 7} {y2 - 12} Z",
        fill=THEME.connector,
    )


def build_contract_diagram(path: Path) -> None:
    """Draw the prompt-to-email contract as a five-stage vertical flow."""

    svg = SVG("Migma Prompt-to-Email Contract — Conceptual View")
    add_slide_background(svg)
    add_header(
        svg,
        "MIGMA • SYSTEM CONTRACT",
        "Migma Prompt-to-Email Contract — Conceptual View",
        "From entry point to an approved, production-ready email",
    )

    x = 410
    width = 1100
    cards = [
        {
            "y": 198,
            "height": 112,
            "title": "ENTRY CHANNELS",
            "color": THEME.blue,
            "columns": [
                ["Web  ·  API  ·  SDK  ·  CLI"],
                ["MCP / External Agent"],
            ],
        },
        {
            "y": 344,
            "height": 160,
            "title": "INPUT",
            "color": "#526FE8",
            "columns": [
                ["Brand / project", "Prompt and campaign goal", "Audience / persona"],
                ["Tone, CTA, language", "Optional references", "Email count / series"],
            ],
        },
        {
            "y": 538,
            "height": 128,
            "title": "ASYNC GENERATION",
            "color": THEME.purple,
            "columns": [
                [
                    "Immediate response: conversationId",
                    "Completion: status polling or webhook",
                ],
                ["status = pending"],
            ],
        },
        {
            "y": 700,
            "height": 145,
            "title": "COMPLETED RESULT",
            "color": THEME.cyan,
            "columns": [
                ["emailId", "Subject + preheader", "Production HTML"],
                ["Screenshot / thumbnail", "Series order"],
            ],
        },
        {
            "y": 879,
            "height": 145,
            "title": "NEXT ACTIONS",
            "color": THEME.green,
            "columns": [
                ["Edit with prompt", "Preview + Preflight", "Send test"],
                ["Export / create campaign", "Review / approval-gated send"],
            ],
        },
    ]

    for index, card in enumerate(cards, start=1):
        add_contract_card(
            svg,
            x=x,
            y=card["y"],
            width=width,
            height=card["height"],
            number=index,
            title=card["title"],
            color=card["color"],
            columns=card["columns"],
        )

    center_x = WIDTH / 2
    for current, following in zip(cards, cards[1:]):
        add_vertical_connector(
            svg,
            center_x,
            current["y"] + current["height"] + 6,
            following["y"] - 9,
        )

    add_authorship_footer(svg)
    svg.write(path)


def add_wrapped_bullet(
    svg: SVG,
    *,
    x: float,
    y: float,
    lines: list[str],
    color: str,
    size: float = 18,
    line_height: float = 24,
) -> float:
    svg.circle(x, y - 6, 3.3, fill=color)
    for index, line in enumerate(lines):
        svg.text(
            x + 16,
            y + index * line_height,
            line,
            size=size,
            fill=THEME.body,
            weight=400,
        )
    return y + max(1, len(lines)) * line_height + 7


def add_workflow_card(
    svg: SVG,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    number: int,
    title: str,
    bullets: list[list[str]],
    color: str,
    title_size: float = 18.5,
) -> None:
    svg.rect(
        x,
        y,
        width,
        height,
        rx=20,
        fill=THEME.surface,
        stroke=THEME.line,
        stroke_width=1.2,
        filter_="url(#cardShadow)",
    )
    svg.rect(x, y, width, 7, rx=3.5, fill=color)
    svg.circle(x + 39, y + 47, 22, fill=color)
    svg.text(
        x + 39,
        y + 54,
        str(number),
        size=18,
        fill="#FFFFFF",
        weight=700,
        anchor="middle",
    )
    svg.text(
        x + 74,
        y + 53,
        title,
        size=title_size,
        fill=THEME.ink,
        weight=700,
        letter_spacing=0.35,
    )
    svg.line(
        x + 25,
        y + 80,
        x + width - 25,
        y + 80,
        stroke=THEME.line,
        stroke_width=1,
    )
    bullet_y = y + 116
    for bullet_lines in bullets:
        bullet_y = add_wrapped_bullet(
            svg,
            x=x + 31,
            y=bullet_y,
            lines=bullet_lines,
            color=color,
        )


def add_horizontal_connector(
    svg: SVG, x1: float, y: float, x2: float
) -> None:
    direction = 1 if x2 > x1 else -1
    line_end = x2 - direction * 12
    svg.line(
        x1,
        y,
        line_end,
        y,
        stroke=THEME.connector,
        stroke_width=3,
    )
    svg.path(
        f"M {x2} {y} L {x2 - direction * 13} {y - 7} "
        f"L {x2 - direction * 13} {y + 7} Z",
        fill=THEME.connector,
    )


def build_workflow_diagram(path: Path) -> None:
    """Draw the eight-stage end-to-end workflow as a snake flow."""

    svg = SVG("Conceptual Migma End-to-End Email Workflow")
    add_slide_background(svg)
    add_header(
        svg,
        "MIGMA • END-TO-END WORKFLOW",
        "Conceptual Migma End-to-End Email Workflow",
        "Eight stages from governance and intent to measurable improvement",
    )

    margin_x = 112
    gap = 34
    card_width = 398
    card_height = 286
    top_y = 210
    bottom_y = 576
    x_positions = [margin_x + i * (card_width + gap) for i in range(4)]

    stages = [
        {
            "number": 1,
            "title": "CONFIGURE & GOVERN",
            "bullets": [
                ["Permission-based sending"],
                ["Brand import"],
                ["Sender / domain setup"],
            ],
            "color": "#3769E8",
            "x": x_positions[0],
            "y": top_y,
        },
        {
            "number": 2,
            "title": "CAPTURE INTENT",
            "bullets": [
                ["Campaign goal"],
                ["Audience"],
                ["CTA, tone and language"],
                ["Optional reference"],
            ],
            "color": "#4C74E8",
            "x": x_positions[1],
            "y": top_y,
        },
        {
            "number": 3,
            "title": "ENRICH WITH CONTEXT",
            "bullets": [
                ["Brand voice and design"],
                ["Approved knowledge"],
                ["Products and audience data"],
            ],
            "color": "#6471DF",
            "x": x_positions[2],
            "y": top_y,
        },
        {
            "number": 4,
            "title": "AI CREATIVE GENERATION",
            "bullets": [
                ["Campaign plan"],
                ["Copy and subject"],
                ["Structured email blueprint"],
            ],
            "color": THEME.purple,
            "x": x_positions[3],
            "y": top_y,
        },
        {
            "number": 5,
            "title": "DETERMINISTIC COMPILATION",
            "bullets": [
                ["Email-safe HTML"],
                ["Responsive layout"],
                ["Personalization variables"],
            ],
            "color": "#5D72D9",
            "x": x_positions[3],
            "y": bottom_y,
        },
        {
            "number": 6,
            "title": "REFINE & PREFLIGHT",
            "bullets": [
                ["Chat or visual edit"],
                ["Cross-client preview"],
                ["Links, content, spam and", "compliance checks"],
            ],
            "color": THEME.cyan,
            "x": x_positions[2],
            "y": bottom_y,
        },
        {
            "number": 7,
            "title": "REVIEW, APPROVAL & PUBLISH",
            "title_size": 17,
            "bullets": [
                ["Test send"],
                ["Human or policy-based approval"],
                ["Send / schedule / export"],
            ],
            "color": THEME.green,
            "x": x_positions[1],
            "y": bottom_y,
        },
        {
            "number": 8,
            "title": "EVENTS & IMPROVEMENT",
            "bullets": [
                ["Delivery logs"],
                ["Clicks, bounces, complaints", "and unsubscribes"],
                ["Evaluation and product iteration"],
            ],
            "color": THEME.amber,
            "x": x_positions[0],
            "y": bottom_y,
        },
    ]

    for stage in stages:
        add_workflow_card(
            svg,
            x=stage["x"],
            y=stage["y"],
            width=card_width,
            height=card_height,
            number=stage["number"],
            title=stage["title"],
            bullets=stage["bullets"],
            color=stage["color"],
            title_size=stage.get("title_size", 18.5),
        )

    top_mid_y = top_y + card_height / 2
    for index in range(3):
        add_horizontal_connector(
            svg,
            x_positions[index] + card_width + 7,
            top_mid_y,
            x_positions[index + 1] - 10,
        )

    # Stage 4 flows downward to stage 5.
    down_x = x_positions[3] + card_width / 2
    svg.line(
        down_x,
        top_y + card_height + 7,
        down_x,
        bottom_y - 21,
        stroke=THEME.connector,
        stroke_width=3,
    )
    svg.path(
        f"M {down_x - 7} {bottom_y - 22} L {down_x} {bottom_y - 10} "
        f"L {down_x + 7} {bottom_y - 22} Z",
        fill=THEME.connector,
    )

    bottom_mid_y = bottom_y + card_height / 2
    for index in (3, 2, 1):
        add_horizontal_connector(
            svg,
            x_positions[index] - 7,
            bottom_mid_y,
            x_positions[index - 1] + card_width + 10,
        )

    # Dotted feedback arrow visibly emerges from Stage 8.
    source_x = x_positions[0] + card_width / 2
    source_y = bottom_y + card_height + 5
    feedback_y = 950
    pill_x = 548
    pill_width = 742
    pill_height = 82
    svg.path(
        f"M {source_x} {source_y} V {feedback_y} H {pill_x - 28}",
        stroke=THEME.purple,
        stroke_width=3,
        dash="4 12",
    )
    svg.path(
        f"M {pill_x - 14} {feedback_y} L {pill_x - 28} {feedback_y - 8} "
        f"L {pill_x - 28} {feedback_y + 8} Z",
        fill=THEME.purple,
    )
    svg.rect(
        pill_x,
        feedback_y - pill_height / 2,
        pill_width,
        pill_height,
        rx=34,
        fill="#F0ECFF",
        stroke="#CFC4FA",
        stroke_width=1.2,
        filter_="url(#softShadow)",
    )
    svg.text(
        pill_x + 31,
        feedback_y - 10,
        "MEASURED FEEDBACK TO",
        size=13,
        fill=THEME.purple,
        weight=700,
        letter_spacing=1.5,
    )
    svg.text(
        pill_x + 31,
        feedback_y + 22,
        "Brand context  ·  Prompts  ·  Evaluation set",
        size=21,
        fill=THEME.ink,
        weight=700,
    )

    # Compact legend explains the architectural meaning of the card colors.
    legend_x = 1360
    legend_y = 893
    legend_width = 448
    legend_height = 111
    svg.rect(
        legend_x,
        legend_y,
        legend_width,
        legend_height,
        rx=16,
        fill=THEME.surface,
        stroke=THEME.line,
        stroke_width=1.2,
        filter_="url(#softShadow)",
    )
    svg.text(
        legend_x + 22,
        legend_y + 27,
        "COLOR KEY",
        size=12.5,
        fill=THEME.muted,
        weight=700,
        letter_spacing=1.4,
    )
    legend_items = [
        (THEME.purple, "AI-assisted", 0, 0),
        (THEME.blue, "Deterministic logic", 1, 0),
        (THEME.green, "Review & publishing", 0, 1),
        (THEME.amber, "Feedback & measurement", 1, 1),
    ]
    for color, label, column, row in legend_items:
        item_x = legend_x + 22 + column * 208
        item_y = legend_y + 57 + row * 30
        svg.circle(item_x + 5, item_y - 5, 5, fill=color)
        svg.text(
            item_x + 19,
            item_y,
            label,
            size=14.5,
            fill=THEME.body,
            weight=500,
        )

    svg.text(
        WIDTH / 2,
        1026,
        (
            "Cross-cutting controls:  Scoped authorization  ·  Async jobs  ·  "
            "Webhooks  ·  Idempotency  ·  Observability"
        ),
        size=13,
        fill=THEME.body,
        weight=600,
        anchor="middle",
        letter_spacing=0.15,
    )
    add_authorship_footer(svg)
    svg.write(path)


def convert_to_png(svg_path: Path, png_path: Path) -> bool:
    """Convert SVG to PNG with ImageMagick if a converter is available."""

    converter = shutil.which("magick") or shutil.which("convert")
    if converter is None:
        return False

    command = [
        converter,
        "-background",
        "none",
        "-density",
        "144",
        str(svg_path),
        "-resize",
        f"{WIDTH}x{HEIGHT}!",
        str(png_path),
    ]
    subprocess.run(command, check=True)
    return True


def convert_to_pdf(png_paths: list[Path], pdf_path: Path) -> bool:
    """Create a two-page presentation PDF without extra Python packages.

    ImageMagick prepares high-quality JPEG page images, then Ghostscript embeds
    them on 16:9 PDF pages. This avoids ImageMagick installations that disable
    direct PDF writing in their security policy.
    """

    converter = shutil.which("magick") or shutil.which("convert")
    ghostscript = shutil.which("gs")
    if converter is None or ghostscript is None or not png_paths:
        return False

    with tempfile.TemporaryDirectory(prefix="migma_pdf_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        jpeg_paths: list[Path] = []
        for index, png_path in enumerate(png_paths, start=1):
            jpeg_path = temp_dir / f"page_{index}.jpg"
            subprocess.run(
                [
                    converter,
                    str(png_path),
                    "-background",
                    "#F6F8FC",
                    "-alpha",
                    "remove",
                    "-quality",
                    "96",
                    str(jpeg_path),
                ],
                check=True,
            )
            jpeg_paths.append(jpeg_path)

        page_commands = " ".join(
            f"({path}) viewJPEG showpage" for path in jpeg_paths
        )
        postscript = (
            "[ /Title (Migma Conceptual Email Workflow) "
            "/Author (Farjam Azizi) /DOCINFO pdfmark "
            "<</PageSize [960 540]>> setpagedevice "
            f"{page_commands}"
        )
        subprocess.run(
            [
                ghostscript,
                "-q",
                "-dSAFER",
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.7",
                f"-sOutputFile={pdf_path}",
                "viewjpeg.ps",
                "-c",
                postscript,
            ],
            check=True,
        )
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Draw two presentation-ready Migma conceptual diagrams."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for generated files (default: output).",
    )
    parser.add_argument(
        "--format",
        choices=("svg", "png", "both"),
        default="both",
        help="Output format (default: both). SVG is always generated internally.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    diagrams = [
        (
            "migma_prompt_to_email_contract",
            build_contract_diagram,
        ),
        (
            "migma_end_to_end_email_workflow",
            build_workflow_diagram,
        ),
    ]

    generated: list[Path] = []
    generated_pngs: list[Path] = []
    for filename, builder in diagrams:
        svg_path = output_dir / f"{filename}.svg"
        builder(svg_path)
        png_created = False

        if args.format in ("svg", "both"):
            generated.append(svg_path)

        if args.format in ("png", "both"):
            png_path = output_dir / f"{filename}.png"
            if convert_to_png(svg_path, png_path):
                png_created = True
                generated.append(png_path)
                generated_pngs.append(png_path)
            else:
                print(
                    "PNG export skipped: ImageMagick was not found. "
                    f"The SVG remains available at {svg_path}."
                )
                if args.format == "png":
                    generated.append(svg_path)

        if args.format == "png" and png_created:
            # The SVG is an implementation detail for PNG-only mode.
            svg_path.unlink(missing_ok=True)

    if args.format in ("png", "both") and len(generated_pngs) == len(diagrams):
        pdf_path = output_dir / "Farjam_Azizi_Migma_Conceptual_Email_Workflow.pdf"
        if convert_to_pdf(generated_pngs, pdf_path):
            generated.append(pdf_path)
        else:
            print(
                "Combined PDF export skipped: ImageMagick and Ghostscript "
                "are both required."
            )

    print("Generated:")
    for path in generated:
        print(f"  {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
