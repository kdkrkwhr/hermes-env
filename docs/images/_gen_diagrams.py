"""Generate flow.png and architecture.png for hermes-env README."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
BG = (2, 6, 23)  # slate-950
GRID = (30, 41, 59)
TEXT = (226, 232, 240)
MUTED = (148, 163, 184)
CYAN = (34, 211, 238)
EMERALD = (52, 211, 153)
VIOLET = (167, 139, 250)
AMBER = (251, 191, 36)
SLATE = (148, 163, 184)
BOX_BG = (15, 23, 42)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # malgun: Hangul glyphs required for Korean labels
    candidates = [
        r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\NotoSansKR-VF.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    if bold:
        candidates = [
            r"C:\Windows\Fonts\malgunbd.ttf",
            r"C:\Windows\Fonts\malgun.ttf",
        ] + candidates
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def draw_grid(draw: ImageDraw.ImageDraw, w: int, h: int, step: int = 40) -> None:
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=GRID, width=1)
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=GRID, width=1)


def rounded_box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    stroke: tuple[int, int, int],
    fill_rgba: tuple[int, int, int, int] | None = None,
    radius: int = 10,
) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=BOX_BG, outline=None)
    # semi overlay via solid approx
    if fill_rgba:
        overlay = Image.new("RGBA", (x1 - x0 + 1, y1 - y0 + 1), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle(
            [0, 0, x1 - x0, y1 - y0],
            radius=radius,
            fill=fill_rgba,
            outline=stroke + (255,),
            width=2,
        )
        # caller composites; here just stroke on main
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=stroke, width=2)


def center_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    lines: list[str],
    f: ImageFont.ImageFont,
    fill=TEXT,
    gap: int = 4,
) -> None:
    x0, y0, x1, y1 = box
    heights = []
    widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=f)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    total_h = sum(heights) + gap * (len(lines) - 1)
    y = y0 + (y1 - y0 - total_h) // 2
    for i, line in enumerate(lines):
        x = x0 + (x1 - x0 - widths[i]) // 2
        draw.text((x, y), line, font=f, fill=fill)
        y += heights[i] + gap


def arrow(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, color=MUTED) -> None:
    draw.line([(x0, y0), (x1, y1)], fill=color, width=2)
    # arrow head
    if abs(x1 - x0) >= abs(y1 - y0):
        # horizontal
        direction = 1 if x1 > x0 else -1
        draw.polygon(
            [(x1, y1), (x1 - 10 * direction, y1 - 6), (x1 - 10 * direction, y1 + 6)],
            fill=color,
        )
    else:
        direction = 1 if y1 > y0 else -1
        draw.polygon(
            [(x1, y1), (x1 - 6, y1 - 10 * direction), (x1 + 6, y1 - 10 * direction)],
            fill=color,
        )


def make_flow() -> None:
    w, h = 1400, 520
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    draw_grid(draw, w, h)
    title_f = font(22, bold=True)
    box_f = font(16, bold=True)
    sub_f = font(13)
    draw.text((40, 28), "hermes-env — bootstrap flow", font=title_f, fill=TEXT)
    draw.text((40, 58), "clone once → tell the agent → paths asked → setup → report", font=sub_f, fill=MUTED)

    steps = [
        ("1. git clone", "repo → local", CYAN, (40, 140, 280, 280)),
        ("2. tell agent", "AGENT_BOOTSTRAP.md\n읽고 세팅해줘", EMERALD, (320, 140, 560, 280)),
        ("3. ask paths", "PROJECT_ROOT\nE2E_ROOT\nHERMES_HOME", AMBER, (600, 140, 840, 280)),
        ("4. setup", "dirs · config\nskills · env", VIOLET, (880, 140, 1120, 280)),
        ("5. done", "검증 통과\n완료 보고", EMERALD, (1160, 140, 1360, 280)),
    ]

    for label, sub, color, box in steps:
        x0, y0, x1, y1 = box
        draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=BOX_BG, outline=color, width=2)
        # tint strip
        draw.rounded_rectangle([x0, y0, x1, y0 + 8], radius=4, fill=color)
        center_text(draw, (x0, y0 + 24, x1, y0 + 70), [label], box_f, fill=color)
        center_text(draw, (x0 + 8, y0 + 78, x1 - 8, y1 - 12), sub.split("\n"), sub_f, fill=TEXT, gap=6)

    # arrows between boxes
    centers_y = 210
    for i in range(len(steps) - 1):
        x0 = steps[i][3][2]
        x1 = steps[i + 1][3][0]
        arrow(draw, x0 + 4, centers_y, x1 - 4, centers_y, MUTED)

    note = "0단계에서 경로 3개를 사용자에게 묻기 전에 세팅을 시작하면 안 됨"
    draw.text((40, 340), note, font=sub_f, fill=SLATE)
    note2 = "SSoT 클론은 선택 (6단계) — setup의 dirs·config·skills·env 이후에 해당"
    draw.text((40, 368), note2, font=sub_f, fill=SLATE)

    # legend boxes
    legend = [
        (CYAN, "repo / clone"),
        (EMERALD, "agent action"),
        (AMBER, "user input"),
        (VIOLET, "machine write"),
    ]
    lx = 40
    for color, label in legend:
        draw.rounded_rectangle([lx, 430, lx + 18, 448], radius=3, fill=color)
        draw.text((lx + 26, 430), label, font=sub_f, fill=MUTED)
        lx += 200

    img.save(OUT / "flow.png", "PNG", optimize=True)
    print("wrote", OUT / "flow.png")


def box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    lines: list[str],
    stroke: tuple[int, int, int],
    title_f: ImageFont.ImageFont,
    body_f: ImageFont.ImageFont,
) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=BOX_BG, outline=stroke, width=2)
    draw.text((x0 + 14, y0 + 12), title, font=title_f, fill=stroke)
    y = y0 + 42
    for line in lines:
        draw.text((x0 + 14, y), line, font=body_f, fill=TEXT)
        y += 22


def make_architecture() -> None:
    w, h = 1400, 780
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    draw_grid(draw, w, h)
    title_f = font(22, bold=True)
    h_f = font(15, bold=True)
    body_f = font(13)
    tiny_f = font(12)

    draw.text((40, 24), "hermes-env — repo → machine layout", font=title_f, fill=TEXT)
    draw.text(
        (40, 54),
        "bootstrap repo ships templates; agent copies them into HERMES_HOME / E2E_ROOT",
        font=tiny_f,
        fill=MUTED,
    )

    # left: repo boundary
    draw.rounded_rectangle([30, 100, 560, 720], radius=16, outline=CYAN, width=2)
    draw.text((48, 114), "bootstrap repo (git clone)", font=h_f, fill=CYAN)

    box(
        draw,
        (50, 150, 540, 230),
        "AGENT_BOOTSTRAP.md",
        ["0~7 step checklist", "asks 3 paths first"],
        AMBER,
        h_f,
        body_f,
    )
    box(
        draw,
        (50, 250, 540, 330),
        "README.md + docs/",
        ["conventions.md", "docs/images/*"],
        SLATE,
        h_f,
        body_f,
    )
    box(
        draw,
        (50, 350, 540, 470),
        "hermes/",
        ["config.yaml.template", "skills/ (portable set)"],
        EMERALD,
        h_f,
        body_f,
    )
    box(
        draw,
        (50, 490, 540, 580),
        ".env.example",
        ["secret names only — no values"],
        VIOLET,
        h_f,
        body_f,
    )
    draw.text((50, 620), "not shipped: project code, SSoT body,", font=tiny_f, fill=MUTED)
    draw.text((50, 642), "agent memory, real .env values", font=tiny_f, fill=MUTED)

    # arrows to right
    for y in (190, 410, 530):
        arrow(draw, 560, y, 640, y, MUTED)

    # right: machine
    draw.rounded_rectangle([640, 100, 1370, 720], radius=16, outline=EMERALD, width=2)
    draw.text((660, 114), "local machine after bootstrap", font=h_f, fill=EMERALD)

    box(
        draw,
        (660, 150, 1000, 290),
        "$HERMES_HOME",
        ["config.yaml", "skills/ ← copied", "profiles/", "state.db"],
        EMERALD,
        h_f,
        body_f,
    )
    box(
        draw,
        (1020, 150, 1350, 290),
        "$E2E_ROOT",
        ["ssot/", "reports/", ".env.local", "hermes/ (optional)"],
        CYAN,
        h_f,
        body_f,
    )
    box(
        draw,
        (660, 320, 1350, 430),
        "$PROJECT_ROOT",
        ["<repo>/ … product code lives here — agent reports stay out"],
        AMBER,
        h_f,
        body_f,
    )
    box(
        draw,
        (660, 460, 1350, 600),
        "mapping",
        [
            "hermes/config.yaml.template  →  $HERMES_HOME/config.yaml",
            "hermes/skills/*              →  $HERMES_HOME/skills/",
            ".env.example                 →  $E2E_ROOT/.env.local (fill values)",
            "docs/conventions.md          →  agent working rules (read, not copy)",
        ],
        VIOLET,
        h_f,
        body_f,
    )
    draw.text(
        (660, 640),
        "paths come from step 0 answers — never hard-coded to one PC",
        font=tiny_f,
        fill=MUTED,
    )

    img.save(OUT / "architecture.png", "PNG", optimize=True)
    print("wrote", OUT / "architecture.png")


if __name__ == "__main__":
    make_flow()
    make_architecture()
