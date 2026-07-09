
import json
import math
import numpy as np
import matplotlib
matplotlib.use("TkAgg")                      # interactive GUI display
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as pe
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# 1.  DESIGN TOKENS  (mirrors student_life_ai_dashboard.css)
# ═══════════════════════════════════════════════════════════════════════

BG      = "#f8f7f4"
SURFACE = "#ffffff"
SURF2   = "#f1f0ec"
BORDER  = "#e5e4e0"
TEXT    = "#1a1a1a"
TEXT2   = "#6b6b6b"
TEXT3   = "#9a9a9a"
ACCENT  = "#1a1a2e"

# Target colours
C_RED    = "#ef4444"
C_BLUE   = "#3b82f6"
C_AMBER  = "#f59e0b"
C_PURPLE = "#8b5cf6"
C_GREEN  = "#22c55e"
C_INDIGO = "#6366f1"
C_TEAL   = "#14b8a6"

# Badge palettes  {bg, text}
BAD_GREEN  = ("#dcfce7", "#15803d")
BAD_YELLOW = ("#fef9c3", "#854d0e")
BAD_RED    = ("#fee2e2", "#991b1b")
BAD_BLUE   = ("#dbeafe", "#1e40af")

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "axes.facecolor":   SURFACE,
    "figure.facecolor": BG,
    "text.color":       TEXT,
    "axes.edgecolor":   BORDER,
    "axes.labelcolor":  TEXT2,
    "xtick.color":      TEXT3,
    "ytick.color":      TEXT3,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":        False,
})

# ═══════════════════════════════════════════════════════════════════════
# 2.  PREDICTION MODEL  (exact port of student_life_ai_dashboard.js)
# ═══════════════════════════════════════════════════════════════════════

def clamp(v: float) -> int:
    return max(0, min(100, int(round(v))))

def predict(s: dict) -> dict:
    burnout = clamp(
        s["stress"]*7 + s["pressure"]*4 + (10-s["sleep"])*3 + s["backlogs"]*4 +
        (100-s["att"])*0.3 + s["screen"]*1.5 + (10-s["motivation"])*4 +
        s["hostel"]*3 - s["exercise"]*2 - s["friends"]*1.5 - s["study"]*1 +
        (7-s["cgpa"])*2
    )
    placement = clamp(
        s["cgpa"]*6 + s["coding"]*3 + s["intern"]*8 + s["proj"]*3 + s["cert"]*2 +
        s["att"]*0.2 + s["motivation"]*1.5 - s["backlogs"]*2 + s["study"]*1
    )
    backlog_risk = clamp(
        s["backlogs"]*8 + (100-s["att"])*0.4 + (10-s["cgpa"])*4 + s["stress"]*3 +
        (100-s["asn"])*0.3 + (8-s["sleep"])*2 - s["study"]*2 - s["motivation"]*2
    )
    loneliness = clamp(
        (10-s["friends"])*6 + s["hostel"]*4 + s["stress"]*2 + s["screen"]*1.5 -
        s["club"]*4 - s["exercise"]*2 + (8-s["sleep"])*2
    )
    productivity = clamp(
        s["study"]*5 + s["motivation"]*4 + s["att"]*0.3 - s["stress"]*2 -
        s["screen"]*1.5 + s["exercise"]*2 + s["cgpa"]*2
    )
    return dict(burnout=burnout, placement=placement,
                backlogRisk=backlog_risk, loneliness=loneliness,
                productivity=productivity)

# ═══════════════════════════════════════════════════════════════════════
# 3.  DATASET
# ═══════════════════════════════════════════════════════════════════════

RAW = [
    {"id":"STU001","name":"Aarav Mehta","sem":3,"branch":"CS","cgpa":8.2,"att":85,"backlogs":0,"asn":90,"study":5.0,"sleep":7.0,"screen":4.0,"exercise":4,"friends":8,"hostel":1,"stress":4,"pressure":5,"motivation":8,"club":2,"intern":1,"proj":3,"cert":2,"coding":8},
    {"id":"STU002","name":"Priya Sharma","sem":5,"branch":"CS","cgpa":6.1,"att":62,"backlogs":3,"asn":55,"study":2.0,"sleep":5.0,"screen":8.0,"exercise":1,"friends":2,"hostel":1,"stress":8,"pressure":8,"motivation":3,"club":0,"intern":0,"proj":1,"cert":0,"coding":4},
    {"id":"STU003","name":"Rohan Patel","sem":7,"branch":"Mech","cgpa":7.5,"att":78,"backlogs":1,"asn":75,"study":4.0,"sleep":6.5,"screen":5.0,"exercise":3,"friends":5,"hostel":1,"stress":5,"pressure":6,"motivation":6,"club":1,"intern":2,"proj":4,"cert":3,"coding":6},
    {"id":"STU004","name":"Sneha Gupta","sem":2,"branch":"ECE","cgpa":9.1,"att":95,"backlogs":0,"asn":98,"study":7.0,"sleep":8.0,"screen":3.0,"exercise":5,"friends":10,"hostel":0,"stress":2,"pressure":3,"motivation":9,"club":3,"intern":0,"proj":5,"cert":4,"coding":9},
    {"id":"STU005","name":"Karan Singh","sem":6,"branch":"CS","cgpa":5.8,"att":55,"backlogs":5,"asn":40,"study":1.0,"sleep":4.5,"screen":10.0,"exercise":0,"friends":1,"hostel":1,"stress":9,"pressure":9,"motivation":2,"club":0,"intern":0,"proj":0,"cert":0,"coding":3},
    {"id":"STU006","name":"Neha Joshi","sem":4,"branch":"DS","cgpa":7.9,"att":80,"backlogs":0,"asn":82,"study":5.0,"sleep":7.0,"screen":4.0,"exercise":3,"friends":6,"hostel":0,"stress":4,"pressure":5,"motivation":7,"club":2,"intern":1,"proj":3,"cert":3,"coding":7},
    {"id":"STU007","name":"Vikram Rao","sem":8,"branch":"CS","cgpa":8.7,"att":88,"backlogs":0,"asn":92,"study":6.0,"sleep":7.5,"screen":3.0,"exercise":5,"friends":7,"hostel":1,"stress":3,"pressure":4,"motivation":9,"club":3,"intern":2,"proj":3,"cert":5,"coding":9},
    {"id":"STU008","name":"Anjali Verma","sem":1,"branch":"Civil","cgpa":6.5,"att":70,"backlogs":2,"asn":60,"study":3.0,"sleep":6.0,"screen":6.0,"exercise":1,"friends":3,"hostel":1,"stress":7,"pressure":7,"motivation":4,"club":0,"intern":0,"proj":1,"cert":0,"coding":3},
    {"id":"STU009","name":"Arjun Kumar","sem":5,"branch":"CS","cgpa":7.2,"att":75,"backlogs":1,"asn":72,"study":4.0,"sleep":6.5,"screen":5.0,"exercise":2,"friends":5,"hostel":0,"stress":5,"pressure":6,"motivation":6,"club":1,"intern":1,"proj":3,"cert":2,"coding":6},
    {"id":"STU010","name":"Divya Nair","sem":3,"branch":"DS","cgpa":8.4,"att":87,"backlogs":0,"asn":88,"study":6.0,"sleep":7.5,"screen":3.0,"exercise":4,"friends":9,"hostel":0,"stress":3,"pressure":4,"motivation":8,"club":2,"intern":0,"proj":4,"cert":3,"coding":8},
    {"id":"STU011","name":"Rahul Tiwari","sem":6,"branch":"Mech","cgpa":5.5,"att":50,"backlogs":6,"asn":35,"study":1.0,"sleep":4.0,"screen":11.0,"exercise":0,"friends":1,"hostel":1,"stress":9,"pressure":8,"motivation":2,"club":0,"intern":0,"proj":0,"cert":0,"coding":2},
    {"id":"STU012","name":"Simran Kaur","sem":4,"branch":"CS","cgpa":8.0,"att":82,"backlogs":0,"asn":85,"study":5.0,"sleep":7.0,"screen":4.0,"exercise":3,"friends":7,"hostel":0,"stress":4,"pressure":5,"motivation":7,"club":2,"intern":1,"proj":1,"cert":3,"coding":7},
    {"id":"STU013","name":"Harsh Agarwal","sem":7,"branch":"ECE","cgpa":6.8,"att":68,"backlogs":2,"asn":65,"study":3.0,"sleep":5.5,"screen":7.0,"exercise":1,"friends":2,"hostel":1,"stress":7,"pressure":7,"motivation":4,"club":0,"intern":1,"proj":2,"cert":1,"coding":5},
    {"id":"STU014","name":"Pooja Reddy","sem":2,"branch":"DS","cgpa":9.3,"att":96,"backlogs":0,"asn":99,"study":8.0,"sleep":8.0,"screen":2.0,"exercise":6,"friends":11,"hostel":0,"stress":2,"pressure":2,"motivation":10,"club":4,"intern":0,"proj":5,"cert":5,"coding":10},
    {"id":"STU015","name":"Amit Bhatt","sem":5,"branch":"CS","cgpa":7.0,"att":72,"backlogs":1,"asn":70,"study":4.0,"sleep":6.0,"screen":5.0,"exercise":2,"friends":4,"hostel":1,"stress":6,"pressure":6,"motivation":5,"club":1,"intern":1,"proj":1,"cert":2,"coding":6},
    {"id":"STU016","name":"Ishaan Desai","sem":3,"branch":"Mech","cgpa":6.3,"att":64,"backlogs":3,"asn":55,"study":2.0,"sleep":5.0,"screen":8.0,"exercise":1,"friends":2,"hostel":1,"stress":8,"pressure":8,"motivation":3,"club":0,"intern":0,"proj":1,"cert":0,"coding":3},
    {"id":"STU017","name":"Meera Pillai","sem":8,"branch":"ECE","cgpa":8.6,"att":89,"backlogs":0,"asn":90,"study":6.0,"sleep":7.5,"screen":3.0,"exercise":5,"friends":8,"hostel":0,"stress":3,"pressure":3,"motivation":9,"club":3,"intern":2,"proj":2,"cert":4,"coding":8},
    {"id":"STU018","name":"Suresh Bhat","sem":6,"branch":"Civil","cgpa":5.2,"att":48,"backlogs":7,"asn":30,"study":1.0,"sleep":3.5,"screen":12.0,"exercise":0,"friends":0,"hostel":1,"stress":10,"pressure":9,"motivation":1,"club":0,"intern":0,"proj":0,"cert":0,"coding":1},
    {"id":"STU019","name":"Kritika Soni","sem":4,"branch":"DS","cgpa":7.7,"att":79,"backlogs":0,"asn":78,"study":5.0,"sleep":7.0,"screen":4.0,"exercise":3,"friends":6,"hostel":0,"stress":4,"pressure":5,"motivation":7,"club":2,"intern":1,"proj":0,"cert":3,"coding":7},
    {"id":"STU020","name":"Dev Malhotra","sem":1,"branch":"CS","cgpa":7.4,"att":74,"backlogs":0,"asn":73,"study":4.0,"sleep":6.5,"screen":5.0,"exercise":2,"friends":1,"hostel":0,"stress":5,"pressure":5,"motivation":6,"club":1,"intern":0,"proj":1,"cert":1,"coding":5},
]

DATA = [{**s, **predict(s)} for s in RAW]

# ═══════════════════════════════════════════════════════════════════════
# 4.  ANALYTICS HELPERS
# ═══════════════════════════════════════════════════════════════════════

def avg_field(key):
    return sum(s[key] for s in DATA) / len(DATA)

def averages():
    return {k: avg_field(k) for k in
            ["burnout","placement","backlogRisk","loneliness","productivity",
             "stress","sleep","cgpa","att","study","friends","coding"]}

def pseudo_rand(seed, i):
    return ((seed * 9301 + i * 49297) % 233280) / 233280

def trend_data(s):
    seed = s["burnout"] + s["productivity"]
    prod  = [clamp(round(s["productivity"] + (i-3.5)*1.5 + (pseudo_rand(seed,i)*8-4))) for i in range(8)]
    study = [round((s["study"] + pseudo_rand(seed,i+10)*2 - 1)*10)/10 for i in range(8)]
    return prod, study

def radar_vals(s):
    return [
        s["productivity"], s["placement"],
        clamp(round((s["sleep"]/10)*100)),
        clamp(round(s["friends"]*6 + s["club"]*7)),
        clamp(round(s["cgpa"]*10)),
        clamp(round(s["intern"]*15 + s["proj"]*7 + s["cert"]*6 + s["coding"]*3)),
    ]

def chip_color(v, invert=False):
    """Returns (face_color, text_color) tuple matching JS chipColors()."""
    if invert:
        if v > 65: return BAD_BLUE
        if v > 40: return BAD_YELLOW
        return BAD_RED
    if v < 35: return BAD_GREEN
    if v < 65: return BAD_YELLOW
    return BAD_RED

def badge_text(v, invert=False):
    if invert:
        return "Strong" if v > 65 else ("Moderate" if v > 40 else "Weak")
    return "Low" if v < 35 else ("Medium" if v < 65 else "High")

def advice_lines(p):
    lines = []
    if p["burnout"] > 65:      lines.append("High burnout — counselling & workload adjustment recommended")
    elif p["burnout"] > 40:    lines.append("Moderate burnout risk — encourage stress management")
    if p["backlogRisk"] > 65:  lines.append("Backlog risk high — academic mentorship needed")
    if p["loneliness"] > 65:   lines.append("Social isolation — encourage clubs & peer groups")
    if p["placement"] < 40:    lines.append("Placement readiness low — internships & coding focus")
    if p["productivity"] < 40: lines.append("Low productivity — reduce screen time, improve sleep")
    if not lines:              lines.append("Performing well across all dimensions!")
    return lines

# ═══════════════════════════════════════════════════════════════════════
# 5.  DRAWING HELPERS
# ═══════════════════════════════════════════════════════════════════════

def rounded_box(ax, x, y, w, h, color=SURFACE, edge=BORDER, radius=0.015, lw=0.8, zorder=1):
    box = FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=color, edgecolor=edge, linewidth=lw, zorder=zorder,
        transform=ax.transAxes, clip_on=False)
    ax.add_patch(box)
    return box

def bar_track(ax, x, y, w, h=0.012, fill_pct=0.7, fill_color=C_RED, bg=SURF2):
    """Horizontal progress bar in axes-fraction coords."""
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.003",
        facecolor=bg, edgecolor="none", zorder=3, transform=ax.transAxes, clip_on=False))
    ax.add_patch(FancyBboxPatch((x, y), w * fill_pct, h,
        boxstyle="round,pad=0,rounding_size=0.003",
        facecolor=fill_color, edgecolor="none", zorder=4, transform=ax.transAxes, clip_on=False))

def page_header(fig, title, subtitle="", page_num=1, total_pages=5):
    fig.text(0.04, 0.97, "STUDENT · LIFE · AI",
             fontsize=10, fontweight="bold", color=ACCENT,
             fontfamily="monospace", va="top")
    fig.text(0.04, 0.945, title,
             fontsize=18, fontweight="bold", color=TEXT, va="top")
    if subtitle:
        fig.text(0.04, 0.918, subtitle,
                 fontsize=10, color=TEXT3, va="top")
    fig.text(0.96, 0.97, f"Page {page_num} / {total_pages}",
             fontsize=9, color=TEXT3, ha="right", va="top")
    fig.add_artist(plt.Line2D([0.04, 0.96], [0.905, 0.905],
                              color=BORDER, lw=0.8, transform=fig.transFigure))

def draw_metric_card(ax, x, y, w, h, label, value_str, fill_pct, bar_color,
                     badge_str, badge_bg, badge_fg, hint_str):
    """Draw a single KPI metric card in axes-fraction coordinates."""
    pad = 0.012
    rounded_box(ax, x+pad, y+pad, w-2*pad, h-2*pad, color=SURFACE, radius=0.01)

    # Label (top-left)
    ax.text(x+pad*2.5, y+h-pad*2.2, label.upper(),
            fontsize=6, fontweight="bold", color=TEXT3,
            transform=ax.transAxes, va="top", clip_on=False)

    # Badge (top-right)
    bx, by = x+w-pad*2.5, y+h-pad*2.2
    ax.text(bx, by, badge_str,
            fontsize=6.5, fontweight="bold", color=badge_fg,
            transform=ax.transAxes, va="top", ha="right", clip_on=False,
            bbox=dict(boxstyle="round,pad=0.25", facecolor=badge_bg, edgecolor="none"))

    # Value
    ax.text(x+pad*2.5, y+h*0.52, value_str,
            fontsize=20, fontweight="bold", color=TEXT,
            fontfamily="monospace", transform=ax.transAxes, va="center", clip_on=False)

    # Progress bar
    bar_x, bar_y = x+pad*2, y+h*0.25
    bar_w = w - pad*4
    bar_track(ax, bar_x, bar_y, bar_w, 0.009, fill_pct/100, bar_color)

    # Hint
    ax.text(x+pad*2.5, y+pad*1.8, hint_str,
            fontsize=6, color=TEXT3, transform=ax.transAxes, va="bottom", clip_on=False)

# ═══════════════════════════════════════════════════════════════════════
# 6.  PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════

def build_page1(avgs):
    fig = plt.figure(figsize=(16, 11.5), facecolor=BG)
    page_header(fig, "Class Overview Dashboard",
                f"Dataset average across {len(DATA)} students  ·  ML v2.1", 1, 5)

    gs = GridSpec(3, 1, figure=fig, top=0.88, bottom=0.04,
                  left=0.04, right=0.96, hspace=0.28)

    # ── Row 1: 5 KPI metric cards ─────────────────────────────────────
    ax_kpi = fig.add_subplot(gs[0])
    ax_kpi.set_xlim(0, 1); ax_kpi.set_ylim(0, 1)
    ax_kpi.axis("off")

    metrics = [
        ("Burnout Risk",    f"{avgs['burnout']:.0f}%",    avgs["burnout"],    C_RED,
         badge_text(avgs["burnout"]), *chip_color(avgs["burnout"]),
         f"Avg Stress {avgs['stress']:.1f}/10 · Sleep {avgs['sleep']:.1f}h"),
        ("Placement Score", f"{avgs['placement']:.0f}%",  avgs["placement"],  C_BLUE,
         badge_text(avgs["placement"], True), *chip_color(avgs["placement"], True),
         f"Avg CGPA {avgs['cgpa']:.2f}"),
        ("Backlog Risk",    f"{avgs['backlogRisk']:.0f}%",avgs["backlogRisk"],C_AMBER,
         badge_text(avgs["backlogRisk"]), *chip_color(avgs["backlogRisk"]),
         f"Avg Attendance {avgs['att']:.0f}%"),
        ("Loneliness",      f"{avgs['loneliness']:.0f}%", avgs["loneliness"], C_PURPLE,
         badge_text(avgs["loneliness"]), *chip_color(avgs["loneliness"]),
         f"Avg Friends {avgs['friends']:.0f}"),
        ("Productivity",    f"{avgs['productivity']:.0f}%",avgs["productivity"],C_GREEN,
         badge_text(avgs["productivity"], True), *chip_color(avgs["productivity"], True),
         f"Avg Study {avgs['study']:.1f}h/day"),
    ]

    cw = 0.186
    for i, (lbl, val, fill, bar, bdg, bbg, bfg, hint) in enumerate(metrics):
        draw_metric_card(ax_kpi, i*0.202, 0.06, cw, 0.88,
                         lbl, val, fill, bar, bdg, bbg, bfg, hint)

    # ── Row 2: Burnout distribution bar chart ─────────────────────────
    ax_dist = fig.add_subplot(gs[1])
    buckets = [0]*5
    for s in DATA:
        buckets[min(4, s["burnout"]//20)] += 1

    bucket_labels = ["0–20\n(Low)", "20–40", "40–60\n(Med)", "60–80", "80–100\n(High)"]
    colors_dist   = ["#4ade80","#facc15","#fb923c","#f87171","#ef4444"]
    bars = ax_dist.bar(bucket_labels, buckets, color=colors_dist,
                       edgecolor="white", linewidth=1.2, width=0.55, zorder=3)

    for bar_obj, val in zip(bars, buckets):
        if val > 0:
            ax_dist.text(bar_obj.get_x() + bar_obj.get_width()/2,
                         bar_obj.get_height() + 0.08, str(val),
                         ha="center", va="bottom", fontsize=10,
                         fontweight="bold", color=TEXT)

    ax_dist.set_facecolor(SURFACE)
    ax_dist.set_ylim(0, max(buckets)+1.5)
    ax_dist.set_title("Burnout Risk Distribution — all students",
                       fontsize=12, fontweight="bold", color=TEXT, pad=8, loc="left")
    ax_dist.set_ylabel("Number of students", fontsize=9, color=TEXT2)
    ax_dist.tick_params(colors=TEXT3, labelsize=9)
    for spine in ax_dist.spines.values():
        spine.set_edgecolor(BORDER)
    ax_dist.yaxis.grid(True, color=BORDER, lw=0.6, zorder=0)
    ax_dist.set_axisbelow(True)

    # ── Row 3: Class overview table ───────────────────────────────────
    ax_tbl = fig.add_subplot(gs[2])
    ax_tbl.axis("off")
    ax_tbl.set_title("Class Overview — sorted by Burnout Risk ↓",
                      fontsize=12, fontweight="bold", color=TEXT, pad=6, loc="left")

    sorted_data = sorted(DATA, key=lambda s: s["burnout"], reverse=True)
    col_labels  = ["Student", "Sem", "Branch", "Burnout", "Placement", "Backlog Risk",
                   "Loneliness", "Productivity"]
    col_widths  = [0.20, 0.06, 0.12, 0.10, 0.12, 0.12, 0.12, 0.13]
    row_h = 0.083
    hdr_y = 0.93

    # Header row
    cx = 0.0
    for label, cw2 in zip(col_labels, col_widths):
        ax_tbl.add_patch(Rectangle((cx, hdr_y-0.04), cw2, 0.07,
            facecolor=SURF2, edgecolor=BORDER, lw=0.5, transform=ax_tbl.transAxes))
        ax_tbl.text(cx + cw2/2, hdr_y - 0.005, label.upper(),
            ha="center", va="center", fontsize=6.5, fontweight="bold",
            color=TEXT3, transform=ax_tbl.transAxes)
        cx += cw2

    # Data rows
    for row_i, s in enumerate(sorted_data[:16]):  # show top 16 rows
        y0 = hdr_y - 0.04 - (row_i+1)*row_h
        bg = SURF2 if row_i % 2 == 0 else SURFACE
        cx = 0.0
        cells = [
            s["name"], f"Sem {s['sem']}", s["branch"],
            s["burnout"], s["placement"], s["backlogRisk"],
            s["loneliness"], s["productivity"]
        ]
        for ci, (cell, cw2) in enumerate(zip(cells, col_widths)):
            ax_tbl.add_patch(Rectangle((cx, y0), cw2, row_h,
                facecolor=bg, edgecolor=BORDER, lw=0.3, transform=ax_tbl.transAxes))
            if ci >= 3:  # score columns — coloured chip
                invert = (ci == 4)  # placement is "good-high"
                face, fg = chip_color(cell, invert)
                ax_tbl.add_patch(FancyBboxPatch(
                    (cx + cw2/2 - 0.033, y0 + row_h*0.2), 0.066, row_h*0.6,
                    boxstyle="round,pad=0,rounding_size=0.003",
                    facecolor=face, edgecolor="none", transform=ax_tbl.transAxes))
                ax_tbl.text(cx + cw2/2, y0 + row_h/2, str(cell),
                    ha="center", va="center", fontsize=7.5, fontweight="bold",
                    color=fg, transform=ax_tbl.transAxes, fontfamily="monospace")
            else:
                ax_tbl.text(cx + 0.008, y0 + row_h/2, str(cell),
                    ha="left", va="center", fontsize=8,
                    color=TEXT, transform=ax_tbl.transAxes)
            cx += cw2

    return fig

# ═══════════════════════════════════════════════════════════════════════
# 7.  PAGE 2 — TREND & RADAR
# ═══════════════════════════════════════════════════════════════════════

def build_page2(avgs):
    fig = plt.figure(figsize=(16, 11.5), facecolor=BG)
    page_header(fig, "Wellness & Productivity Analysis",
                "Dataset averages — weekly trend and multidimensional radar", 2, 5)

    gs = GridSpec(2, 2, figure=fig, top=0.88, bottom=0.06,
                  left=0.06, right=0.96, hspace=0.35, wspace=0.30)

    # ── Weekly Productivity Trend ─────────────────────────────────────
    ax_trend = fig.add_subplot(gs[0, 0])
    prod_vals, study_vals = trend_data(avgs)
    weeks = [f"W{i+1}" for i in range(8)]

    ax_trend.fill_between(range(8), prod_vals, alpha=0.07, color=C_INDIGO)
    ax_trend.plot(range(8), prod_vals, "o-", color=C_INDIGO, linewidth=2.5,
                  markersize=5, label="Productivity %", zorder=4)

    ax2 = ax_trend.twinx()
    ax2.plot(range(8), study_vals, "--", color=C_GREEN, linewidth=1.8,
             label="Study hrs", zorder=3)
    ax2.set_ylim(0, 14)
    ax2.set_ylabel("Study hrs", fontsize=9, color=C_GREEN)
    ax2.tick_params(axis="y", colors=C_GREEN, labelsize=8)
    ax2.spines["right"].set_edgecolor(C_GREEN)

    ax_trend.set_xticks(range(8)); ax_trend.set_xticklabels(weeks, fontsize=9)
    ax_trend.set_ylim(0, 100)
    ax_trend.set_ylabel("Productivity %", fontsize=9, color=C_INDIGO)
    ax_trend.tick_params(axis="y", colors=C_INDIGO, labelsize=8)
    ax_trend.yaxis.grid(True, color=BORDER, lw=0.5, zorder=0)
    ax_trend.set_axisbelow(True)
    ax_trend.set_facecolor(SURFACE)
    ax_trend.set_title("Weekly Productivity Trend (avg)", fontsize=11,
                        fontweight="bold", color=TEXT, pad=8, loc="left")
    lines1, labs1 = ax_trend.get_legend_handles_labels()
    lines2, labs2 = ax2.get_legend_handles_labels()
    ax_trend.legend(lines1+lines2, labs1+labs2, fontsize=8,
                    loc="lower right", framealpha=0.8)

    # ── Radar / Spider Chart ──────────────────────────────────────────
    ax_radar = fig.add_subplot(gs[0, 1], polar=True)
    radar_labels = ["Productivity","Placement","Sleep","Social","Academic","Career"]
    N = len(radar_labels)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    avg_radar = [
        avgs["productivity"], avgs["placement"],
        clamp(round((avgs["sleep"]/10)*100)),
        clamp(round(avgs["friends"]*6)),
        clamp(round(avgs["cgpa"]*15)),
        clamp(round(avgs["coding"]*8)),
    ]
    values = avg_radar + avg_radar[:1]

    ax_radar.set_facecolor(SURFACE)
    ax_radar.plot(angles, values, "o-", color=C_INDIGO, linewidth=2, markersize=5)
    ax_radar.fill(angles, values, alpha=0.12, color=C_INDIGO)
    ax_radar.set_xticks(angles[:-1])
    ax_radar.set_xticklabels(radar_labels, fontsize=9, color=TEXT2)
    ax_radar.set_ylim(0, 100)
    ax_radar.set_yticks([20, 40, 60, 80, 100])
    ax_radar.set_yticklabels(["20","40","60","80","100"], fontsize=7, color=TEXT3)
    ax_radar.grid(color=BORDER, lw=0.7)
    ax_radar.spines["polar"].set_edgecolor(BORDER)
    ax_radar.set_title("Wellness Radar (dataset avg)",
                        fontsize=11, fontweight="bold", color=TEXT, pad=16, loc="center")

    # ── Per-metric bar chart (all students) ──────────────────────────
    ax_bars = fig.add_subplot(gs[1, :])
    targets     = ["burnout", "placement", "backlogRisk", "loneliness", "productivity"]
    target_lbls = ["Burnout Risk", "Placement Score", "Backlog Risk", "Loneliness", "Productivity"]
    colors_m    = [C_RED, C_BLUE, C_AMBER, C_PURPLE, C_GREEN]
    n_students  = len(DATA)
    x_pos       = np.arange(n_students)
    bar_w       = 0.15
    names       = [s["name"].split()[0] for s in DATA]

    for ti, (tgt, lbl, col) in enumerate(zip(targets, target_lbls, colors_m)):
        vals = [s[tgt] for s in DATA]
        offset = (ti - 2) * bar_w
        ax_bars.bar(x_pos + offset, vals, bar_w, label=lbl, color=col,
                    alpha=0.82, edgecolor="white", lw=0.5, zorder=3)

    ax_bars.set_xticks(x_pos)
    ax_bars.set_xticklabels(names, rotation=35, ha="right", fontsize=8)
    ax_bars.set_ylabel("Score (0–100)", fontsize=9, color=TEXT2)
    ax_bars.set_ylim(0, 115)
    ax_bars.yaxis.grid(True, color=BORDER, lw=0.5, zorder=0)
    ax_bars.set_axisbelow(True)
    ax_bars.set_facecolor(SURFACE)
    ax_bars.set_title("All 5 Prediction Scores — Every Student",
                       fontsize=11, fontweight="bold", color=TEXT, pad=8, loc="left")
    ax_bars.legend(fontsize=8.5, loc="upper right", framealpha=0.85,
                   ncol=5, columnspacing=1)
    for spine in ax_bars.spines.values():
        spine.set_edgecolor(BORDER)

    return fig

# ═══════════════════════════════════════════════════════════════════════
# 8.  PAGE 3 — HEATMAP + MODEL WEIGHTS
# ═══════════════════════════════════════════════════════════════════════

def build_page3():
    fig = plt.figure(figsize=(16, 11.5), facecolor=BG)
    page_header(fig, "Feature Importance & Model Architecture",
                "Heatmap of feature contributions + weight chart per prediction target", 3, 5)

    gs = GridSpec(1, 2, figure=fig, top=0.88, bottom=0.08,
                  left=0.06, right=0.96, wspace=0.35)

    # ── Feature Importance Heatmap ────────────────────────────────────
    ax_heat = fig.add_subplot(gs[0])
    features = ["CGPA","Attendance","Sleep","Study hrs","Stress",
                "Backlogs","Friends","Exercise","Screen","Coding"]
    targets  = ["Burnout","Placement","Backlog\nRisk","Loneliness","Productivity"]
    imp      = np.array([
        [15, 8,18,10,28,15,12,10,14, 5],
        [30,12, 5,10, 5,12, 8, 5, 4,35],
        [20,22,12,18,15,30, 5, 5, 5, 8],
        [ 5, 4,12, 5,15, 5,40,12,18, 4],
        [12,12, 8,28,18, 6, 8,12,20,10],
    ], dtype=float)

    cmap = LinearSegmentedColormap.from_list(
        "ind", ["#eef2ff","#c7d2fe","#818cf8","#4338ca","#1e1b4b"])
    im = ax_heat.imshow(imp, cmap=cmap, aspect="auto", vmin=0, vmax=40)

    ax_heat.set_xticks(range(10)); ax_heat.set_xticklabels(features, rotation=35,
                                                            ha="right", fontsize=9)
    ax_heat.set_yticks(range(5));  ax_heat.set_yticklabels(targets, fontsize=9)
    ax_heat.set_title("Feature Importance Heatmap",
                       fontsize=12, fontweight="bold", color=TEXT, pad=10, loc="left")

    for ti in range(5):
        for fi in range(10):
            v = imp[ti, fi]
            txt_col = "white" if v > 20 else "#4338ca"
            ax_heat.text(fi, ti, f"{v:.0f}%", ha="center", va="center",
                         fontsize=8.5, fontweight="bold", color=txt_col)

    plt.colorbar(im, ax=ax_heat, shrink=0.8, label="Importance weight (%)")
    for spine in ax_heat.spines.values():
        spine.set_visible(False)

    # ── Model Weights Grouped Bar ─────────────────────────────────────
    ax_model = fig.add_subplot(gs[1])
    feat_lbl = ["Stress","Sleep","Motivation","Backlogs","CGPA",
                "Coding","Internships","Friends","Exercise","Screen\ntime"]
    burnout_w     = [28,18,15,15,10, 0, 0,12,10,14]
    placement_w   = [ 0, 5,10,12,30,35,20, 8, 5, 4]
    productivity_w= [18, 8,25, 6,12,10, 0, 8,12,20]

    x = np.arange(len(feat_lbl))
    bw = 0.26
    ax_model.bar(x - bw, burnout_w,     bw, label="Burnout",      color=C_RED,    alpha=0.8)
    ax_model.bar(x,      placement_w,   bw, label="Placement",    color=C_BLUE,   alpha=0.8)
    ax_model.bar(x + bw, productivity_w,bw, label="Productivity", color=C_GREEN,  alpha=0.8)

    ax_model.set_xticks(x)
    ax_model.set_xticklabels(feat_lbl, fontsize=8.5, rotation=20, ha="right")
    ax_model.set_ylabel("Feature weight", fontsize=9, color=TEXT2)
    ax_model.yaxis.grid(True, color=BORDER, lw=0.5, zorder=0)
    ax_model.set_axisbelow(True)
    ax_model.set_facecolor(SURFACE)
    ax_model.set_title("Model Feature Weights per Target",
                        fontsize=12, fontweight="bold", color=TEXT, pad=10, loc="left")
    ax_model.legend(fontsize=9, loc="upper right", framealpha=0.85)
    for spine in ax_model.spines.values():
        spine.set_edgecolor(BORDER)

    return fig

# ═══════════════════════════════════════════════════════════════════════
# 9.  PAGE 4 — PER-STUDENT DEEP-DIVE (6 highlighted students)
# ═══════════════════════════════════════════════════════════════════════

def build_page4():
    fig = plt.figure(figsize=(16, 11.5), facecolor=BG)
    page_header(fig, "Per-Student Deep-Dive",
                "Individual radar profiles, trend lines, and AI recommendations", 4, 5)

    # Pick 6 representative students: best, worst, and 4 mid-tier
    sorted_by_burnout = sorted(DATA, key=lambda s: s["burnout"], reverse=True)
    highlight = [
        sorted_by_burnout[0],   # highest burnout
        sorted_by_burnout[1],
        sorted_by_burnout[9],   # mid
        sorted_by_burnout[10],  # mid
        sorted_by_burnout[-2],  # low burnout
        sorted_by_burnout[-1],  # lowest burnout
    ]

    gs = GridSpec(3, 2, figure=fig, top=0.88, bottom=0.04,
                  left=0.05, right=0.97, hspace=0.52, wspace=0.30)
    radar_labels = ["Prod","Place","Sleep","Social","Acad","Career"]
    N = 6
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist() + [0]

    for idx, s in enumerate(highlight):
        row, col = divmod(idx, 2)
        inner = GridSpecFromSubplotSpec(1, 2,
                    subplot_spec=gs[row, col], wspace=0.08)

        # Left: radar
        ax_r = fig.add_subplot(inner[0], polar=True)
        vals = radar_vals(s) + [radar_vals(s)[0]]
        ax_r.plot(angles, vals, "o-", color=C_INDIGO, lw=1.8, markersize=4)
        ax_r.fill(angles, vals, alpha=0.12, color=C_INDIGO)
        ax_r.set_xticks(angles[:-1])
        ax_r.set_xticklabels(radar_labels, fontsize=7, color=TEXT2)
        ax_r.set_ylim(0, 100)
        ax_r.set_yticks([]); ax_r.grid(color=BORDER, lw=0.5)
        ax_r.spines["polar"].set_edgecolor(BORDER)
        ax_r.set_facecolor(SURFACE)
        ax_r.set_title(f"{s['name']}\n{s['branch']} · Sem {s['sem']}",
                        fontsize=8.5, fontweight="bold", color=TEXT, pad=6)

        # Right: metric bars + advice
        ax_m = fig.add_subplot(inner[1])
        ax_m.axis("off")
        tgts = [("Burnout",  s["burnout"],    C_RED,    False),
                ("Placement",s["placement"],  C_BLUE,   True),
                ("Backlog",  s["backlogRisk"],C_AMBER,  False),
                ("Lonely",   s["loneliness"], C_PURPLE, False),
                ("Product.", s["productivity"],C_GREEN, True)]
        for ti, (lbl, val, col, inv) in enumerate(tgts):
            y = 0.85 - ti*0.165
            face, fg = chip_color(val, inv)
            # label
            ax_m.text(0.0, y, lbl, fontsize=7, color=TEXT3,
                       transform=ax_m.transAxes, va="center")
            # bar track
            ax_m.add_patch(FancyBboxPatch((0.38, y-0.04), 0.44, 0.07,
                boxstyle="round,pad=0,rounding_size=0.01",
                facecolor=SURF2, edgecolor="none",
                transform=ax_m.transAxes, zorder=2))
            ax_m.add_patch(FancyBboxPatch((0.38, y-0.04), 0.44*(val/100), 0.07,
                boxstyle="round,pad=0,rounding_size=0.01",
                facecolor=col, edgecolor="none", alpha=0.75,
                transform=ax_m.transAxes, zorder=3))
            # value chip
            ax_m.add_patch(FancyBboxPatch((0.84, y-0.045), 0.155, 0.08,
                boxstyle="round,pad=0,rounding_size=0.01",
                facecolor=face, edgecolor="none",
                transform=ax_m.transAxes, zorder=4))
            ax_m.text(0.918, y, str(val), fontsize=7, fontweight="bold",
                       color=fg, ha="center", va="center",
                       transform=ax_m.transAxes, fontfamily="monospace", zorder=5)

        # AI advice
        adv = advice_lines(s)
        y_adv = 0.85 - 5*0.165 - 0.06
        for ai, line in enumerate(adv[:2]):
            ax_m.text(0.0, y_adv - ai*0.11, f"• {line}",
                       fontsize=6.2, color=TEXT2, wrap=True,
                       transform=ax_m.transAxes, va="top")

    return fig

# ═══════════════════════════════════════════════════════════════════════
# 10.  PAGE 5 — MODEL FORMULAS REFERENCE
# ═══════════════════════════════════════════════════════════════════════

def build_page5():
    fig = plt.figure(figsize=(16, 11.5), facecolor=BG)
    page_header(fig, "Model Architecture & Formula Reference",
                "Weighted linear scoring model — fully interpretable, zero black-box", 5, 5)

    ax = fig.add_axes([0.04, 0.04, 0.92, 0.84])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_facecolor(BG)

    formulas = [
        ("Burnout Risk", C_RED,
         "burnout = clamp(\n"
         "  stress×7  + pressure×4  + (10–sleep)×3  + backlogs×4\n"
         "  + (100–att)×0.3  + screen×1.5  + (10–motivation)×4\n"
         "  + hostel×3  – exercise×2  – friends×1.5  – study×1\n"
         "  + (7–cgpa)×2\n)"),
        ("Placement Score", C_BLUE,
         "placement = clamp(\n"
         "  cgpa×6  + coding×3  + intern×8  + proj×3  + cert×2\n"
         "  + att×0.2  + motivation×1.5  – backlogs×2  + study×1\n)"),
        ("Backlog Risk", C_AMBER,
         "backlog_risk = clamp(\n"
         "  backlogs×8  + (100–att)×0.4  + (10–cgpa)×4  + stress×3\n"
         "  + (100–asn)×0.3  + (8–sleep)×2  – study×2  – motivation×2\n)"),
        ("Loneliness Score", C_PURPLE,
         "loneliness = clamp(\n"
         "  (10–friends)×6  + hostel×4  + stress×2  + screen×1.5\n"
         "  – club×4  – exercise×2  + (8–sleep)×2\n)"),
        ("Productivity", C_GREEN,
         "productivity = clamp(\n"
         "  study×5  + motivation×4  + att×0.3\n"
         "  – stress×2  – screen×1.5  + exercise×2  + cgpa×2\n)"),
    ]

    row_h = 0.175
    for i, (title, color, formula) in enumerate(formulas):
        y = 0.93 - i * (row_h + 0.015)
        # Card background
        ax.add_patch(FancyBboxPatch((0.01, y - row_h + 0.01), 0.98, row_h,
            boxstyle="round,pad=0,rounding_size=0.01",
            facecolor=SURFACE, edgecolor=BORDER, lw=0.8))
        # Left colour accent bar
        ax.add_patch(Rectangle((0.01, y - row_h + 0.01), 0.004, row_h,
            facecolor=color, edgecolor="none"))
        # Title
        ax.text(0.022, y - 0.012, title,
                fontsize=11, fontweight="bold", color=TEXT,
                va="top", ha="left")
        # Formula monospace block
        ax.text(0.022, y - 0.048, formula,
                fontsize=8.2, color=TEXT2, va="top", ha="left",
                fontfamily="monospace", linespacing=1.6)
        # "Higher = …" note
        note = ("Higher = more burnout risk" if "burnout" in title.lower() else
                "Higher = better placement" if "placement" in title.lower() else
                "Higher = more backlog likelihood" if "backlog" in title.lower() else
                "Higher = more social isolation" if "loneliness" in title.lower() else
                "Higher = more productive student")
        ax.text(0.975, y - 0.012, note,
                fontsize=7.5, color=color, va="top", ha="right", style="italic")

    # Footer note
    ax.text(0.5, 0.01,
            "clamp(v) = max(0, min(100, round(v)))  ·  All scores are in range [0, 100]  "
            "·  Weekly trend simulated with deterministic pseudo-random walk around base score",
            fontsize=7.5, color=TEXT3, ha="center", va="bottom", style="italic")

    return fig

# ═══════════════════════════════════════════════════════════════════════
# 11.  INTERACTIVE DASHBOARD GUI
# ═══════════════════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import random

class DashboardApp:
    def __init__(self, root, avgs, data):
        self.root = root
        self.avgs = avgs
        self.data = data
        self.current_page = 0
        
        self.page_titles = [
            "📊 Class Overview Dashboard",
            "📈 Wellness & Productivity Analysis",
            "🔥 Feature Importance & Model Architecture",
            "👤 Per-Student Deep-Dive",
            "📋 Model Architecture & Formula Reference",
            "➕ Add New Student Entry"
        ]
        
        self.pages = [
            build_page1(avgs),
            build_page2(avgs),
            build_page3(),
            build_page4(),
            build_page5(),
            None  # Form page (created dynamically)
        ]
        
        # Set window properties
        self.root.title("Student Life AI Dashboard")
        self.root.geometry("1700x1000")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        
        # Create header frame
        header_frame = tk.Frame(self.root, bg=ACCENT, height=70)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="STUDENT · LIFE · AI DASHBOARD",
            font=("DejaVu Sans", 20, "bold"),
            bg=ACCENT,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Page indicator
        self.page_label = tk.Label(
            header_frame,
            text=self.page_titles[0],
            font=("DejaVu Sans", 14),
            bg=ACCENT,
            fg="#e5e4e0"
        )
        self.page_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Create control frame with better layout
        control_frame = tk.Frame(self.root, bg=SURFACE, height=80)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        control_frame.pack_propagate(False)
        
        # Row 1: Navigation buttons
        nav_frame = tk.Frame(control_frame, bg=SURFACE)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        btn_width = 12
        btn_font = ("DejaVu Sans", 9, "bold")
        
        prev_btn = tk.Button(
            nav_frame,
            text="◀ Previous",
            command=self.prev_page,
            font=btn_font,
            bg=C_BLUE,
            fg="white",
            width=btn_width,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2
        )
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        # Page counter
        self.counter_label = tk.Label(
            nav_frame,
            text=f"Page 1 / 6",
            font=("DejaVu Sans", 10, "bold"),
            bg=SURFACE,
            fg=TEXT
        )
        self.counter_label.pack(side=tk.LEFT, padx=15)
        
        next_btn = tk.Button(
            nav_frame,
            text="Next ▶",
            command=self.next_page,
            font=btn_font,
            bg=C_GREEN,
            fg="white",
            width=btn_width,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2
        )
        next_btn.pack(side=tk.LEFT, padx=5)
        
        # Row 2: Quick jump buttons
        jump_frame = tk.Frame(control_frame, bg=SURFACE)
        jump_frame.pack(fill=tk.X, padx=10, pady=5)
        
        jump_label = tk.Label(
            jump_frame,
            text="Jump to page:",
            font=("DejaVu Sans", 9),
            bg=SURFACE,
            fg=TEXT2
        )
        jump_label.pack(side=tk.LEFT, padx=5)
        
        for i in range(6):
            jump_btn = tk.Button(
                jump_frame,
                text=str(i+1),
                command=lambda p=i: self.goto_page(p),
                font=("DejaVu Sans", 8, "bold"),
                bg=SURF2,
                fg=TEXT,
                width=3,
                cursor="hand2",
                relief=tk.RAISED,
                bd=1
            )
            jump_btn.pack(side=tk.LEFT, padx=2)
        
        # Create canvas frame
        canvas_frame = tk.Frame(self.root, bg="white")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas_frame = canvas_frame
        
        # Display initial page
        self.display_page(0)
    
    def display_page(self, page_idx):
        # Clear previous canvas
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        if page_idx == 5:  # Form page
            self.display_form_page()
        else:
            # Create new canvas with the figure
            fig = self.pages[page_idx]
            canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Update labels
        self.page_label.config(text=self.page_titles[page_idx])
        self.counter_label.config(text=f"Page {page_idx + 1} / 6")
        self.current_page = page_idx
    
    def display_form_page(self):
        """Display the form for adding new student entries"""
        # Create scrollable form
        main_frame = tk.Frame(self.canvas_frame, bg=SURFACE)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(main_frame, text="Add New Student Entry",
                        font=("DejaVu Sans", 14, "bold"), bg=SURFACE, fg=TEXT)
        title.pack(pady=10)
        
        # Create scrollable area
        canvas = tk.Canvas(main_frame, bg=SURFACE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=SURFACE)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Form fields
        fields = {
            "Student ID": "STU",
            "Name": "",
            "Semester": "1",
            "Branch": "CS",
            "CGPA": "7.0",
            "Attendance": "80",
            "Backlogs": "0",
            "Assignments": "80",
            "Study Hours": "5.0",
            "Sleep Hours": "7.0",
            "Screen Time": "4.0",
            "Exercise": "3",
            "Friends": "5",
            "Hostel": "1",
            "Stress (1-10)": "5",
            "Pressure (1-10)": "5",
            "Motivation (1-10)": "6",
            "Club Activities": "1",
            "Internships": "0",
            "Projects": "2",
            "Certifications": "1",
            "Coding Skills (1-10)": "6"
        }
        
        entries = {}
        for label_text, default_val in fields.items():
            frame = tk.Frame(scrollable_frame, bg=SURFACE)
            frame.pack(fill=tk.X, padx=15, pady=5)
            
            label = tk.Label(frame, text=label_text + ":", font=("DejaVu Sans", 9),
                           bg=SURFACE, fg=TEXT2, width=20, anchor="w")
            label.pack(side=tk.LEFT)
            
            entry = tk.Entry(frame, font=("DejaVu Sans", 9), width=25)
            entry.insert(0, default_val)
            entry.pack(side=tk.LEFT, padx=5)
            entries[label_text] = entry
        
        # Button frame
        btn_frame = tk.Frame(scrollable_frame, bg=SURFACE)
        btn_frame.pack(fill=tk.X, padx=15, pady=20)
        
        def save_student():
            try:
                student_data = {
                    "id": entries["Student ID"].get() + str(len(self.data) + 1),
                    "name": entries["Name"].get(),
                    "sem": int(entries["Semester"].get()),
                    "branch": entries["Branch"].get(),
                    "cgpa": float(entries["CGPA"].get()),
                    "att": int(entries["Attendance"].get()),
                    "backlogs": int(entries["Backlogs"].get()),
                    "asn": int(entries["Assignments"].get()),
                    "study": float(entries["Study Hours"].get()),
                    "sleep": float(entries["Sleep Hours"].get()),
                    "screen": float(entries["Screen Time"].get()),
                    "exercise": int(entries["Exercise"].get()),
                    "friends": int(entries["Friends"].get()),
                    "hostel": int(entries["Hostel"].get()),
                    "stress": int(entries["Stress (1-10)"].get()),
                    "pressure": int(entries["Pressure (1-10)"].get()),
                    "motivation": int(entries["Motivation (1-10)"].get()),
                    "club": int(entries["Club Activities"].get()),
                    "intern": int(entries["Internships"].get()),
                    "proj": int(entries["Projects"].get()),
                    "cert": int(entries["Certifications"].get()),
                    "coding": int(entries["Coding Skills (1-10)"].get())
                }
                
                # Calculate predictions
                predictions = predict(student_data)
                student_data.update(predictions)
                
                # Add to global DATA
                global DATA
                DATA.append(student_data)
                
                messagebox.showinfo("Success", f"Student {student_data['name']} added successfully!\nID: {student_data['id']}")
                
                # Reset form
                for entry in entries.values():
                    entry.delete(0, tk.END)
                entries["Student ID"].insert(0, "STU")
                
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: Please check your values. {str(e)}")
        
        save_btn = tk.Button(btn_frame, text="✓ Save Student", font=("DejaVu Sans", 10, "bold"),
                            bg=C_GREEN, fg="white", command=save_student, cursor="hand2",
                            relief=tk.RAISED, bd=2, padx=20, pady=8)
        save_btn.pack(side=tk.LEFT, padx=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.display_page(self.current_page + 1)
    
    def prev_page(self):
        if self.current_page > 0:
            self.display_page(self.current_page - 1)
    
    def goto_page(self, page_idx):
        if 0 <= page_idx < len(self.pages):
            self.display_page(page_idx)


def main():
    print("Building Student Life AI Dashboard (pure Python / matplotlib)…")
    avgs = averages()
    print(f"  Dataset    : {len(DATA)} students")
    print(f"  Avg burnout: {avgs['burnout']:.1f}%")
    print(f"  Avg place. : {avgs['placement']:.1f}%")
    print(f"  Avg prod.  : {avgs['productivity']:.1f}%")
    
    # Create root window
    root = tk.Tk()
    
    # Create dashboard app with data reference
    app = DashboardApp(root, avgs, DATA)
    
    print("\n✓ Dashboard loaded! Single interactive window is now active.")
    print("  Navigate using Previous/Next buttons or click page numbers.")
    print("  Go to page 6 to add new student entries.\n")
    
    # Run the GUI
    root.mainloop()


if __name__ == "__main__":
    main()