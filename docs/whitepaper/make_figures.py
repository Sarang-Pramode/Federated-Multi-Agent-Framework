#!/usr/bin/env python3
"""Generate the white paper figures as vector SVG.

    ./.venv/bin/python make_figures.py

One function per figure. Every figure is authored at W = 488 units, which is the
text-block width in points, so that a font size of 8 in here renders as 8 pt on
the page. Heights stay below ~600 so a figure plus caption fits one page.
"""

from __future__ import annotations

import os

from svgkit import C, FONT, MONO, Canvas, wrap

W = 488.0
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")

FIGURES: dict[str, callable] = {}


def figure(name):
    def wrapper(fn):
        FIGURES[name] = fn
        return fn
    return wrapper


# ==========================================================================
# 1. Reference architecture
# ==========================================================================


@figure("reference-architecture")
def reference_architecture() -> Canvas:
    c = Canvas(W)
    left_x, left_w = 8.0, 104.0
    main_x, main_w = 124.0, 240.0
    right_x, right_w = 376.0, 104.0

    c.text(left_x + 2, 16, "CONTROL PLANES", size=6.8, fill=C["faint"], weight="bold")
    c.text(main_x + 2, 16, "SYNCHRONOUS REQUEST PATH", size=6.8, fill=C["faint"], weight="bold")
    c.text(right_x + 2, 16, "MODEL PLANE", size=6.8, fill=C["faint"], weight="bold")

    # -- main column -------------------------------------------------------
    rows = [
        (26, 30, "Channels", "web, mobile, voice, internal apps", C["paper"], C["rule"], None),
        (68, 30, "API and agent gateway", "authn, quotas, correlation id", C["paper"], C["rule"], C["muted"]),
        (110, 30, "Input guardrail rails", "deterministic, then classifier", C["warn_soft"], C["warn_mid"], C["warn"]),
    ]
    for y, h, title, sub, fill, stroke, accent in rows:
        c.box(main_x, y, main_w, h, title=title, subtitle=sub, fill=fill,
              stroke=stroke, accent=accent, title_size=8.4, sub_size=6.8)

    # central runtime panel
    cy, ch = 152, 116
    c.rect(main_x, cy, main_w, ch, fill=C["accent_soft"], stroke=C["accent"], sw=1.3, rx=4)
    c.text(main_x + 8, cy + 13, "CENTRAL AGENT RUNTIME", size=6.8, fill=C["accent_dark"],
           weight="bold")
    c.text(main_x + 8, cy + 23.5, "platform team owns this box", size=6.4, fill=C["muted"])
    stages = [
        ("Classify task and risk", "deterministic first"),
        ("Discover eligible capabilities", "shortlist, not catalogue"),
        ("Plan, escalate only if needed", "fast tier by default"),
        ("Authorize, compose, output rails", "authority is not the model"),
    ]
    sy = cy + 30
    for label, note in stages:
        c.rect(main_x + 7, sy, main_w - 14, 19, fill=C["paper"], stroke=C["accent_mid"],
               sw=0.8, rx=2.5)
        c.text(main_x + 13, sy + 8.4, label, size=7.2, fill=C["ink"], weight="bold")
        c.text(main_x + 13, sy + 16.2, note, size=6.2, fill=C["muted"])
        sy += 21.5

    # domain plane
    dy, dh = 292, 92
    c.band(main_x - 4, dy, main_w + 8, dh, "DOMAIN PLANE - domain teams own these services",
           fill=C["teal_soft"], stroke=C["teal_mid"], label_colour=C["teal"])
    dom_w = (main_w - 6) / 3.0
    domains = [
        ("Rewards", ["4 skills", "3 tools", "policy index"]),
        ("Transactions", ["2 skills", "2 tools", "systems of record"]),
        ("Cards, ...", ["independently", "deployed", "and versioned"]),
    ]
    for index, (name, lines) in enumerate(domains):
        bx = main_x - 1 + index * (dom_w + 1)
        c.box(bx, dy + 19, dom_w - 2, dh - 27, title=name, lines=lines,
              fill=C["paper"], stroke=C["teal_mid"], accent=C["teal"],
              title_size=7.8, sub_size=6.2)

    c.box(main_x, 396, main_w, 28, title="Output rails and response composition",
          subtitle="groundedness, egress, schema, action assertion",
          fill=C["warn_soft"], stroke=C["warn_mid"], accent=C["warn"],
          title_size=8.0, sub_size=6.6)

    c.box(main_x, 436, main_w, 34, title="Durable execution",
          subtitle="queue, workflow engine, state store, workers",
          fill=C["violet_soft"], stroke=C["rule"], accent=C["violet"],
          title_size=8.0, sub_size=6.6)

    # vertical flow arrows in the main column
    for y1, y2 in [(56, 66), (98, 108), (140, 150), (268, 290), (384, 394), (424, 434)]:
        c.arrow(main_x + main_w / 2, y1, main_x + main_w / 2, y2, stroke=C["accent"],
                sw=1.1, head=5.4)

    # -- left rail ---------------------------------------------------------
    left_items = [
        ("Capability registry", "discovery index", C["accent"]),
        ("Session and context", "state outside replicas", C["accent"]),
        ("Policy and entitlement", "deterministic authority", C["danger"]),
        ("Trace and metrics", "one id, every hop", C["muted"]),
        ("Eval runner", "targeted suite selection", C["teal"]),
        ("Independent auditor", "rule based, not a model", C["violet"]),
    ]
    ly = 26
    for title, sub, accent in left_items:
        c.box(left_x, ly, left_w, 40, title=title, subtitle=sub, fill=C["paper"],
              stroke=C["rule"], accent=accent, title_size=7.0, sub_size=6.1,
              align="left", pad=8)
        c.line(left_x + left_w, ly + 20, main_x - 2, ly + 20, stroke=C["rule"],
               sw=0.8, dash="2,2")
        ly += 46

    # -- right rail --------------------------------------------------------
    right_items = [
        ("Model gateway", "quota, routing, audit", C["accent"], C["paper"]),
        ("Tier 1 on prem", "1-4B quantized, routing", C["teal"], C["teal_soft"]),
        ("Tier 2 on prem", "8-32B quantized, synthesis", C["teal"], C["teal_soft"]),
        ("Guard model pool", "input and output rails", C["warn"], C["warn_soft"]),
        ("Tier 3 frontier", "planning, hard reasoning", C["violet"], C["violet_soft"]),
        ("Judge pool", "asynchronous, own quota", C["muted"], C["wash2"]),
    ]
    ry = 26
    for title, sub, accent, fill in right_items:
        c.box(right_x, ry, right_w, 40, title=title, subtitle=sub, fill=fill,
              stroke=C["rule"], accent=accent, title_size=7.0, sub_size=6.1,
              align="left", pad=8)
        c.line(main_x + main_w + 2, ry + 20, right_x, ry + 20, stroke=C["rule"],
               sw=0.8, dash="2,2")
        ry += 46

    c.text(main_x + main_w / 2, 494, "Every hop carries one correlation id; the model never holds authority.",
           size=6.6, fill=C["faint"], anchor="middle", italic=True)
    c.text(main_x + main_w / 2, 506, "Domain services stay callable by other applications, not only by the agent.",
           size=6.6, fill=C["faint"], anchor="middle", italic=True)
    return c.finish()


# ==========================================================================
# 2. Three architectural patterns compared
# ==========================================================================


@figure("pattern-comparison")
def pattern_comparison() -> Canvas:
    c = Canvas(W)
    panel_w = (W - 4 * 8) / 3.0
    panels = [
        ("A. Single agent with skills", C["warn"], C["warn_soft"]),
        ("B. Peer to peer, no centre", C["danger"], C["danger_soft"]),
        ("C. Federated with a thin centre", C["teal"], C["teal_soft"]),
    ]
    for index, (title, accent, soft) in enumerate(panels):
        x = 8 + index * (panel_w + 8)
        c.rect(x, 10, panel_w, 234, fill=C["paper"], stroke=C["rule"], sw=1.0, rx=4)
        c.rect(x, 10, panel_w, 22, fill=soft, rx=4)
        c.rect(x, 26, panel_w, 6, fill=soft)
        c.text(x + panel_w / 2, 24.5, title, size=7.4, fill=accent, anchor="middle",
               weight="bold")

    # -- panel A: one model, many skills ----------------------------------
    ax = 8
    cx = ax + panel_w / 2
    c.box(cx - 52, 44, 104, 46, title="One agent", subtitle="one prompt, one context",
          fill=C["warn_soft"], stroke=C["warn"], title_size=8.0, sub_size=6.2)
    skill_y = 118
    for row in range(3):
        for col in range(4):
            sx = ax + 10 + col * ((panel_w - 20) / 4)
            c.rect(sx, skill_y + row * 26, (panel_w - 20) / 4 - 4, 18,
                   fill=C["wash2"], stroke=C["rule"], sw=0.7, rx=2)
            c.text(sx + ((panel_w - 20) / 4 - 4) / 2, skill_y + row * 26 + 11.6,
                   f"skill {row * 4 + col + 1}", size=5.6, fill=C["muted"], anchor="middle")
    for col in range(4):
        sx = ax + 10 + col * ((panel_w - 20) / 4) + ((panel_w - 20) / 4 - 4) / 2
        c.line(cx, 90, sx, skill_y - 2, stroke=C["warn_mid"], sw=0.7)
    c.text(cx, 208, "12 skills in one context", size=6.4, fill=C["ink"], anchor="middle",
           weight="bold")
    c.text(cx, 218, "every change is a system change", size=6.2, fill=C["muted"],
           anchor="middle")
    c.text(cx, 232, "prefill grows with the catalogue", size=6.2, fill=C["warn"],
           anchor="middle")

    # -- panel B: mesh -----------------------------------------------------
    bx = 8 + panel_w + 8
    bcx = bx + panel_w / 2
    nodes = [
        (bcx, 62), (bcx + 46, 96), (bcx + 32, 148),
        (bcx - 32, 148), (bcx - 46, 96),
    ]
    for i, (nx, ny) in enumerate(nodes):
        for j, (mx, my) in enumerate(nodes):
            if j <= i:
                continue
            c.line(nx, ny, mx, my, stroke=C["danger_mid"], sw=0.65)
    for i, (nx, ny) in enumerate(nodes):
        c.circle(nx, ny, 13, fill=C["danger_soft"], stroke=C["danger"], sw=1.0)
        c.text(nx, ny + 2.6, chr(65 + i), size=7.4, fill=C["danger"], anchor="middle",
               weight="bold")
    c.text(bcx, 186, "10 trust and compatibility edges", size=6.4, fill=C["ink"],
           anchor="middle", weight="bold")
    c.text(bcx, 196.5, "no owner of the end to end deadline", size=6.2, fill=C["muted"],
           anchor="middle")
    c.text(bcx, 207, "no closed world reachability proof", size=6.2, fill=C["muted"],
           anchor="middle")
    c.text(bcx, 221, "loops are emergent, not designed", size=6.2, fill=C["danger"],
           anchor="middle")

    # -- panel C: thin centre ---------------------------------------------
    ccx = 8 + 2 * (panel_w + 8) + panel_w / 2
    c.box(ccx - 48, 44, 96, 38, title="Thin centre", subtitle="route, gate, compose",
          fill=C["accent_soft"], stroke=C["accent"], title_size=7.8, sub_size=6.2)
    leaf_y = 122
    leaves = [("tool", C["wash2"]), ("agent", C["teal_soft"]), ("workflow", C["violet_soft"])]
    leaf_w = (panel_w - 24) / 3
    for index, (label, fill) in enumerate(leaves):
        lx = 8 + 2 * (panel_w + 8) + 12 + index * (leaf_w + 2)
        c.rect(lx, leaf_y, leaf_w - 2, 30, fill=fill, stroke=C["teal_mid"], sw=0.9, rx=2.5)
        c.text(lx + (leaf_w - 2) / 2, leaf_y + 13, label, size=6.8, fill=C["ink"],
               anchor="middle", weight="bold")
        c.text(lx + (leaf_w - 2) / 2, leaf_y + 23, "domain owned", size=5.8,
               fill=C["muted"], anchor="middle")
        c.arrow(ccx, 82, lx + (leaf_w - 2) / 2, leaf_y - 3, stroke=C["teal"], sw=0.9,
                head=4.6)
    c.rect(8 + 2 * (panel_w + 8) + 12, 162, panel_w - 24, 20, fill=C["paper"],
           stroke=C["rule"], sw=0.8, rx=2.5)
    c.text(ccx, 175, "registry decides what is reachable", size=6.2, fill=C["accent_dark"],
           anchor="middle")
    c.text(ccx, 196, "simplest sufficient execution unit", size=6.4, fill=C["ink"],
           anchor="middle", weight="bold")
    c.text(ccx, 206.5, "one deadline owner, one trace root", size=6.2, fill=C["muted"],
           anchor="middle")
    c.text(ccx, 221, "cost: a real control plane to run", size=6.2, fill=C["teal"],
           anchor="middle")

    c.line(8, 256, W - 8, 256, stroke=C["rule_soft"], sw=0.8)
    c.text(8, 270, "Selection rule", size=7.0, fill=C["ink"], weight="bold")
    c.text(8, 282, "Prefer the fewest reasoning hops that still preserve domain autonomy, enforceable authority and independent",
           size=6.6, fill=C["muted"])
    c.text(8, 292, "deployability. Pattern C is a superset: it can host A for a bounded domain and B between two consenting peers.",
           size=6.6, fill=C["muted"])
    return c.finish()


# ==========================================================================
# 3. Change surface and blast radius
# ==========================================================================


@figure("change-surface")
def change_surface() -> Canvas:
    c = Canvas(W)
    c.text(8, 18, "One domain team ships one prompt change. What must be re-verified?",
           size=7.6, fill=C["ink"], weight="bold")

    col_w = (W - 32) / 3.0
    columns = [
        ("Single agent with skills", C["warn"], C["warn_soft"], 12, 12,
         ["central prompt edited", "all 12 skills share context",
          "full regression suite", "release train couples teams"]),
        ("Peer to peer mesh", C["danger"], C["danger_soft"], 12, 6,
         ["peers hold private expectations", "no shared contract to test",
          "pairwise compatibility matrix", "attribution is a group exercise"]),
        ("Federated, thin centre", C["teal"], C["teal_soft"], 12, 1,
         ["one manifest changes", "auditor recomputes reachability",
          "targeted suite by change type", "domain deploys alone"]),
    ]

    for index, (title, accent, soft, total, affected, notes) in enumerate(columns):
        x = 8 + index * (col_w + 8)
        c.rect(x, 30, col_w, 214, fill=C["paper"], stroke=C["rule"], sw=1.0, rx=4)
        c.rect(x, 30, col_w, 20, fill=soft, rx=4)
        c.rect(x, 44, col_w, 6, fill=soft)
        c.text(x + col_w / 2, 43.5, title, size=7.2, fill=accent, anchor="middle",
               weight="bold")

        # 3 x 4 grid of components; shaded ones are in the blast radius
        grid_x = x + (col_w - 4 * 26) / 2
        for cell in range(total):
            row, col = divmod(cell, 4)
            gx = grid_x + col * 26
            gy = 60 + row * 24
            hot = cell < affected
            c.rect(gx, gy, 22, 19, fill=soft if hot else C["wash"],
                   stroke=accent if hot else C["rule_soft"], sw=1.0 if hot else 0.7, rx=2)
            if hot:
                c.circle(gx + 11, gy + 9.5, 3.1, fill=accent)
        c.text(x + col_w / 2, 148, f"{affected} of {total} components re-verified",
               size=7.0, fill=accent, anchor="middle", weight="bold")
        ny = 162
        for note in notes:
            for line_index, line in enumerate(wrap(note, 30)):
                if line_index == 0:
                    c.text(x + 10, ny, "\u2022", size=6.3, fill=accent)
                c.text(x + 16, ny, line, size=6.3, fill=C["muted"])
                ny += 9.2
            ny += 1.5

    c.line(8, 258, W - 8, 258, stroke=C["rule_soft"], sw=0.8)
    c.text(8, 272, "Why the difference is structural, not a matter of discipline",
           size=7.0, fill=C["ink"], weight="bold")
    c.text(8, 284, "A shared prompt is a shared mutable global. A mesh has no artefact that states what the system may do. A manifest plus",
           size=6.6, fill=C["muted"])
    c.text(8, 294, "an independent reachability check turns \u0022what changed\u0022 into a computable set, which is what makes targeted evaluation",
           size=6.6, fill=C["muted"])
    c.text(8, 304, "sound rather than merely cheaper.", size=6.6, fill=C["muted"])
    return c.finish()


# ==========================================================================
# 4. Central agent pipeline with latency budget
# ==========================================================================


@figure("central-pipeline")
def central_pipeline() -> Canvas:
    c = Canvas(W)
    c.text(8, 17, "Stage", size=6.8, fill=C["faint"], weight="bold")
    c.text(196, 17, "What it decides", size=6.8, fill=C["faint"], weight="bold")
    c.text(330, 17, "Budget p50", size=6.8, fill=C["faint"], weight="bold")
    c.text(392, 17, "Model tier", size=6.8, fill=C["faint"], weight="bold")
    c.line(8, 21, W - 8, 21, stroke=C["rule"], sw=0.8)

    scale = 0.30  # points per millisecond of budget
    stages = [
        ("Edge, identity, session", "who is asking, in what session", 40, "none", C["muted"]),
        ("Input rails, deterministic", "regex, DLP, allow lists, length", 8, "none", C["warn"]),
        ("Input rails, classifier", "injection and harm, 86M-class", 25, "T1", C["warn"]),
        ("Task and risk classification", "read, write, workflow, unknown", 18, "T1", C["accent"]),
        ("Discovery and shortlist", "which capabilities are eligible", 12, "none", C["accent"]),
        ("Plan", "one hop, or decompose", 55, "T1 or T2", C["accent"]),
        ("Escalation gate", "is the fast tier confident", 2, "none", C["violet"]),
        ("Domain execution", "the actual work, often parallel", 180, "domain", C["teal"]),
        ("Authorization and validation", "entitlement, limits, idempotency", 35, "none", C["danger"]),
        ("Compose", "structured template where possible", 45, "T1 or none", C["accent"]),
        ("Output rails", "groundedness, egress, schema", 40, "T1 or T2", C["warn"]),
    ]

    y = 30
    total = 0
    for label, decides, budget, tier, accent in stages:
        c.rect(8, y, 180, 22, fill=C["paper"], stroke=C["rule_soft"], sw=0.8, rx=2.5)
        c.rect(8, y + 1, 2.6, 20, fill=accent, rx=1.3)
        c.text(16, y + 14.4, label, size=7.2, fill=C["ink"])
        c.text(196, y + 14.4, decides, size=6.6, fill=C["muted"])
        c.hbar(330, y + 6, budget * scale, 10, accent, label=f"{budget}", 
               label_colour=C["paper"] if budget * scale > 26 else C["muted"])
        c.text(478, y + 14.4, tier, size=6.6, fill=C["muted"], anchor="end")
        total += budget
        y += 25

    c.line(8, y + 2, W - 8, y + 2, stroke=C["rule"], sw=0.8)
    c.text(16, y + 16, "Critical path total", size=7.4, fill=C["ink"], weight="bold")
    c.text(196, y + 16, "time to first token", size=6.6, fill=C["muted"])
    c.hbar(330, y + 8, total * scale, 11, C["ink"], label=f"{total} ms",
           label_colour=C["paper"])

    y += 32
    c.band(8, y, W - 16, 46, "OFF THE CRITICAL PATH - measured, never blocking",
           fill=C["wash"], stroke=C["rule_soft"])
    off_path = [
        "LLM as judge quality scoring",
        "groundedness sampling and drift",
        "trace and metric export",
        "regression corpus capture",
    ]
    ox = 16
    for item in off_path:
        width = c.chip(ox, y + 20, item, size=6.2, fill=C["accent_soft"],
                       text_colour=C["accent_dark"])
        ox += width + 6

    y += 56
    c.text(8, y + 10, "What the central agent must never own", size=7.2, fill=C["ink"],
           weight="bold")
    never = [
        "domain policy semantics",
        "write authority",
        "systems of record",
        "durable workflow state",
        "domain evaluation rubrics",
    ]
    nx = 8
    for item in never:
        width = c.chip(nx, y + 18, item, size=6.2, fill=C["danger_soft"],
                       text_colour=C["danger"])
        nx += width + 6
    return c.finish()


# ==========================================================================
# 5. Model tier ladder and escalation
# ==========================================================================


@figure("model-tiers")
def model_tiers() -> Canvas:
    c = Canvas(W)
    tiers = [
        ("Tier 0", "Deterministic", "no model at all",
         ["exact and pattern intent match", "cached and templated answers",
          "rules, arithmetic, schema checks"],
         "0-5 ms", "60-75% of turns", C["muted"], C["wash2"]),
        ("Tier 1", "On prem, quantized, small", "1-4B, FP8 or INT4, on prem",
         ["task and risk classification", "capability shortlisting",
          "parameter extraction, rail scoring"],
         "15-40 ms", "20-30% of turns", C["teal"], C["teal_soft"]),
        ("Tier 2", "On prem, quantized, mid", "8-32B, FP8, on prem",
         ["multi-fact synthesis with citations", "ambiguous single domain routing",
          "output groundedness adjudication"],
         "120-400 ms", "5-12% of turns", C["accent"], C["accent_soft"]),
        ("Tier 3", "Frontier reasoning", "API or large on prem MoE",
         ["cross domain decomposition", "novel or contested policy reasoning",
          "plan repair after failed attempts"],
         "0.8-4 s", "1-4% of turns", C["violet"], C["violet_soft"]),
    ]

    y = 26
    c.text(8, 17, "TIER", size=6.6, fill=C["faint"], weight="bold")
    c.text(150, 17, "WHAT IT IS FOR", size=6.6, fill=C["faint"], weight="bold")
    c.text(376, 17, "LATENCY", size=6.6, fill=C["faint"], weight="bold")
    c.text(478, 17, "SHARE", size=6.6, fill=C["faint"], anchor="end", weight="bold")

    for tag, name, spec, uses, latency, share, accent, soft in tiers:
        h = 74
        c.rect(8, y, W - 16, h, fill=soft, stroke=accent, sw=1.1, rx=4)
        c.rect(8, y + 1.2, 3.2, h - 2.4, fill=accent, rx=1.6)
        c.text(20, y + 17, tag, size=8.6, fill=accent, weight="bold")
        c.text(20, y + 30, name, size=8.0, fill=C["ink"], weight="bold")
        c.text(20, y + 41, spec, size=6.6, fill=C["muted"])
        c.text(20, y + 58, "escalate only when the tier above cannot decide", size=6.2,
               fill=C["faint"], italic=True)
        uy = y + 17
        for use in uses:
            c.text(150, uy, "\u2022 " + use, size=6.8, fill=C["body"])
            uy += 11.5
        c.text(376, y + 20, latency, size=8.2, fill=accent, weight="bold")
        c.text(376, y + 31, "per call", size=6.2, fill=C["faint"])
        c.text(478, y + 20, share, size=7.4, fill=C["ink"], anchor="end", weight="bold")
        c.text(478, y + 31, "of production turns", size=6.2, fill=C["faint"], anchor="end")
        y += h + 8

    # escalation ladder on the far left
    c.text(8, y + 12, "Escalation is a decision with a cost, not a default",
           size=7.2, fill=C["ink"], weight="bold")
    gates = [
        ("Escalate when", ["classifier margin below threshold",
                           "two or more domains required",
                           "no capability matched the goal",
                           "previous attempt failed validation"], C["teal"], C["teal_soft"]),
        ("Do not escalate when", ["the answer is a lookup",
                                  "the tier below already agreed",
                                  "only phrasing is uncertain",
                                  "the budget is already spent"], C["danger"], C["danger_soft"]),
    ]
    gx = 8
    for title, items, accent, soft in gates:
        c.rect(gx, y + 20, (W - 22) / 2, 84, fill=soft, stroke=accent, sw=1.0, rx=3.5)
        c.text(gx + 9, y + 34, title, size=7.2, fill=accent, weight="bold")
        iy = y + 46
        for item in items:
            c.text(gx + 9, iy, "\u2022 " + item, size=6.4, fill=C["body"])
            iy += 10.4
        gx += (W - 22) / 2 + 6
    return c.finish()


# ==========================================================================
# 6. Latency waterfall: on prem fast tier vs frontier API centre
# ==========================================================================


@figure("latency-waterfall")
def latency_waterfall() -> Canvas:
    c = Canvas(W)
    segments_local = [
        ("edge and identity", 40, C["muted"]),
        ("input rails", 33, C["warn"]),
        ("classify and shortlist", 30, C["teal"]),
        ("plan, Tier 1 on prem", 55, C["teal"]),
        ("domain execution", 180, C["accent"]),
        ("authorize and validate", 35, C["danger"]),
        ("compose", 45, C["accent"]),
        ("output rails", 40, C["warn"]),
    ]
    segments_api = [
        ("edge and identity", 40, C["muted"]),
        ("input rails via API", 210, C["warn"]),
        ("classify, API round trip", 240, C["violet"]),
        ("plan, frontier API", 900, C["violet"]),
        ("domain execution", 180, C["accent"]),
        ("authorize and validate", 35, C["danger"]),
        ("compose, API round trip", 260, C["violet"]),
        ("output rails via API", 250, C["warn"]),
    ]

    total_local = sum(s[1] for s in segments_local)
    total_api = sum(s[1] for s in segments_api)

    x0 = 118.0
    avail = W - x0 - 58
    scale = avail / float(total_api)

    def draw_bar(y, label, sub, segments, total, tone):
        c.text(8, y + 13, label, size=7.8, fill=C["ink"], weight="bold")
        c.text(8, y + 23.5, sub, size=6.4, fill=C["muted"])
        cursor = x0
        for name, value, colour in segments:
            width = value * scale
            c.rect(cursor, y, width, 26, fill=colour, rx=1.4)
            if width > 30:
                c.text(cursor + width / 2, y + 16.6, str(value), size=6.4,
                       fill=C["paper"], anchor="middle")
            cursor += width + 0.7
        c.text(cursor + 6, y + 17, f"{total} ms", size=8.4, fill=tone, weight="bold")

    draw_bar(46, "On prem fast tier", "Tier 1 quantized, same rack", segments_local, total_local, C["teal"])
    draw_bar(96, "Frontier API centre", "every stage a network round trip", segments_api, total_api, C["danger"])

    c.text(8, 32, "Same journey, same domain work, two choices for the control-path model",
           size=7.4, fill=C["ink"], weight="bold")

    # difference callout
    c.rect(8, 140, W - 16, 34, fill=C["wash"], stroke=C["rule_soft"], sw=1.0, rx=3.5)
    delta = total_api - total_local
    c.text(16, 154, f"Identical domain work: 180 ms in both bars. The control path costs {total_local - 180} ms on prem and "
                    f"{total_api - 180} ms over the API.", size=6.9, fill=C["body"])
    c.text(16, 166, f"The architecture, not the domain, adds {delta} ms - a {total_api / total_local:.1f}x end to end regression on the same backend.",
           size=6.9, fill=C["danger"])

    # second order consequences
    c.line(8, 186, W - 8, 186, stroke=C["rule_soft"], sw=0.8)
    c.text(8, 200, "Second order consequences that latency alone does not show",
           size=7.2, fill=C["ink"], weight="bold")
    consequences = [
        ("Quota coupling", "user traffic, guard rails and judges draw on one provider limit; an eval burst throttles customers"),
        ("Availability inheritance", "the fast path is only as available as the vendor, and there is no local degraded mode"),
        ("Cost per turn", "four control-path calls per turn at frontier prices, on the 95% of turns that never needed reasoning"),
        ("Residency exposure", "raw utterances leave the estate on the classification hop, where capability was gained least"),
        ("Variance", "p99 is set by someone else's queue; retries land on the same saturated endpoint"),
    ]
    cy = 214
    for title, note in consequences:
        c.circle(13, cy - 2.6, 2.2, fill=C["danger"])
        c.text(21, cy, title, size=6.8, fill=C["ink"], weight="bold")
        c.text(126, cy, note, size=6.6, fill=C["muted"])
        cy += 13

    c.line(8, 288, W - 8, 288, stroke=C["rule_soft"], sw=0.8)
    c.text(8, 302, "The converse discipline", size=7.2, fill=C["ink"], weight="bold")
    c.text(8, 314, "None of this argues against frontier models. It argues against putting them on the path every turn takes. Tier 3 earns",
           size=6.7, fill=C["muted"])
    c.text(8, 325, "its latency on the 1-4% of turns that genuinely need cross domain decomposition or contested policy reasoning, where a",
           size=6.7, fill=C["muted"])
    c.text(8, 336, "quantized 3B model would produce a confident wrong plan. The design goal is to make that call rare and deliberate,",
           size=6.7, fill=C["muted"])
    c.text(8, 347, "and to keep a local fallback for the day the provider is unavailable.", size=6.7, fill=C["muted"])

    c.legend(8, 358, [(C["teal"], "on prem"), (C["violet"], "frontier API"),
                      (C["accent"], "domain work"), (C["warn"], "guardrails"),
                      (C["danger"], "deterministic authority")], size=6.2, columns=5,
             col_width=96)
    return c.finish()


# ==========================================================================
# Runner
# ==========================================================================


# ==========================================================================
# 7. Guardrail placement map
# ==========================================================================


@figure("guardrail-placement")
def guardrail_placement() -> Canvas:
    c = Canvas(W)
    c.text(8, 17, "Guardrails are placed where the trust boundary is, not where they are convenient to add",
           size=7.4, fill=C["ink"], weight="bold")

    lane_y = 40
    lane_h = 30
    steps = [
        ("User\nutterance", C["wash2"], C["rule"]),
        ("Central\nagent", C["accent_soft"], C["accent"]),
        ("Domain\ncapability", C["teal_soft"], C["teal"]),
        ("Tool and\nretrieval", C["teal_soft"], C["teal"]),
        ("Compose", C["accent_soft"], C["accent"]),
        ("User\nresponse", C["wash2"], C["rule"]),
    ]
    step_w = 62.0
    gap = (W - 16 - len(steps) * step_w) / (len(steps) - 1)
    centres = []
    for index, (label, fill, stroke) in enumerate(steps):
        x = 8 + index * (step_w + gap)
        c.rect(x, lane_y, step_w, lane_h, fill=fill, stroke=stroke, sw=1.0, rx=3)
        parts = label.split("\n")
        c.text(x + step_w / 2, lane_y + (12.5 if len(parts) > 1 else 18.5), parts[0],
               size=6.8, fill=C["ink"], anchor="middle", weight="bold")
        if len(parts) > 1:
            c.text(x + step_w / 2, lane_y + 22.5, parts[1], size=6.8, fill=C["ink"],
                   anchor="middle", weight="bold")
        centres.append(x + step_w / 2)
        if index:
            c.arrow(x - gap + 1, lane_y + lane_h / 2, x - 3, lane_y + lane_h / 2,
                    stroke=C["muted"], sw=1.0, head=5)

    rails = [
        (0, "Input rails", C["warn"], C["warn_soft"], [
            "prompt injection and jailbreak",
            "PII and secret detection",
            "topic and scope allow list",
            "length, encoding, rate abuse",
        ], "blocking, fail closed"),
        (2, "Tool and retrieval rails", C["danger"], C["danger_soft"], [
            "treat retrieved text as hostile",
            "tool argument schema and range",
            "entitlement scope per call",
            "no instruction lifting from data",
        ], "blocking, fail closed"),
        (4, "Output rails", C["violet"], C["violet_soft"], [
            "groundedness against sources",
            "PII and data class egress",
            "action assertion matches receipt",
            "schema and refusal correctness",
        ], "blocking, fail closed"),
    ]

    # Three evenly spaced panels rather than one centred under each step, so
    # neighbouring panels cannot overlap.
    panel_w = (W - 16 - 2 * 6) / 3.0
    for slot, (index, title, accent, soft, items, mode) in enumerate(rails):
        x = 8 + slot * (panel_w + 6)
        y = 94
        c.arrow(centres[index], lane_y + lane_h + 2, x + panel_w / 2, y - 3,
                stroke=accent, sw=1.1, head=5)
        c.rect(x, y, panel_w, 92, fill=soft, stroke=accent, sw=1.1, rx=3.5)
        c.text(x + 8, y + 14, title, size=7.4, fill=accent, weight="bold")
        iy = y + 27
        for item in items:
            for line_index, line in enumerate(wrap(item, 32)):
                if line_index == 0:
                    c.text(x + 8, iy, "\u2022", size=6.3, fill=accent)
                c.text(x + 14, iy, line, size=6.3, fill=C["body"])
                iy += 9.0
        c.text(x + 8, y + 85, mode, size=6.2, fill=accent, italic=True)

    # asynchronous layer
    ay = 206
    c.band(8, ay, W - 16, 62, "ASYNCHRONOUS ASSURANCE - never blocks the user",
           fill=C["wash"], stroke=C["rule_soft"])
    async_items = [
        ("Quality judges", "LLM as judge on a sample, own quota and queue"),
        ("Groundedness audit", "deeper citation checking than the inline rail affords"),
        ("Drift and slice watch", "per domain, per journey, per release cohort"),
        ("Red team replay", "adversarial corpus against the current manifest"),
    ]
    ax = 16
    col = (W - 32) / 4
    for title, note in async_items:
        c.text(ax, ay + 30, title, size=6.9, fill=C["ink"], weight="bold")
        ny = ay + 40
        for line in wrap(note, 26):
            c.text(ax, ny, line, size=6.2, fill=C["muted"])
            ny += 8.6
        ax += col
    for cx in centres:
        c.line(cx, 190, cx, ay - 2, stroke=C["rule"], sw=0.7, dash="2,2")

    # fail open vs fail closed
    fy = 282
    c.text(8, fy, "Fail open or fail closed is a per control decision, and it must be written down",
           size=7.2, fill=C["ink"], weight="bold")
    matrix = [
        ("Authentication and entitlement", "fail closed", C["danger"], "no identity, no answer"),
        ("Write authorization", "fail closed", C["danger"], "never infer authority from text"),
        ("Injection classifier", "fail closed", C["danger"], "on a read path, degrade to templates"),
        ("Groundedness judge, inline", "fail open", C["teal"], "log, sample, do not block the read"),
        ("Async quality judge", "fail open", C["teal"], "assurance is not availability"),
        ("Telemetry export", "fail open", C["teal"], "observability must not gate service"),
    ]
    my = fy + 12
    c.rect(8, my, W - 16, 16, fill=C["wash2"], rx=2)
    c.text(16, my + 11, "Control", size=6.6, fill=C["faint"], weight="bold")
    c.text(210, my + 11, "Posture", size=6.6, fill=C["faint"], weight="bold")
    c.text(286, my + 11, "Why", size=6.6, fill=C["faint"], weight="bold")
    my += 16
    for control, posture, colour, why in matrix:
        c.line(8, my, W - 8, my, stroke=C["rule_soft"], sw=0.6)
        c.text(16, my + 12, control, size=6.5, fill=C["body"])
        c.chip(206, my + 3, posture, size=6.0, fill=C["danger_soft"] if posture == "fail closed" else C["teal_soft"],
               text_colour=colour, h=11.5, pad=4.5)
        c.text(286, my + 12, why, size=6.4, fill=C["muted"])
        my += 17
    c.line(8, my, W - 8, my, stroke=C["rule"], sw=0.7)
    return c.finish()


# ==========================================================================
# 8. Guardrail cascade
# ==========================================================================


@figure("guardrail-cascade")
def guardrail_cascade() -> Canvas:
    c = Canvas(W)
    c.text(8, 17, "A cascade buys coverage without paying for the deepest check on every turn",
           size=7.4, fill=C["ink"], weight="bold")

    stages = [
        ("Stage 0", "Deterministic", "regex, deny lists, length, encoding,\nschema, rate and entitlement checks",
         "0.2-2 ms", "no GPU", 100, 62, C["muted"], C["wash2"]),
        ("Stage 1", "Tiny classifier", "86M-class injection and harm scorer,\nquantized, batched, co-resident",
         "20-50 ms", "shared GPU slice", 38, 26, C["teal"], C["teal_soft"]),
        ("Stage 2", "Guard model", "8-12B guard model in no-think mode\nfor hazard category and adjudication",
         "40-90 ms", "dedicated pool", 12, 3, C["warn"], C["warn_soft"]),
        ("Stage 3", "Human or hard block", "queue for review, or refuse with an\nexplicit reason code and audit record",
         "seconds+", "no GPU", 3, 0, C["danger"], C["danger_soft"]),
    ]

    y = 34
    x_funnel = 8.0
    funnel_max = 148.0
    for tag, name, detail, latency, cost, enters, passes_on, accent, soft in stages:
        h = 62
        # funnel band proportional to traffic entering the stage
        width = funnel_max * (enters / 100.0)
        c.rect(x_funnel, y + 8, max(width, 10), h - 16, fill=soft, stroke=accent, sw=1.0, rx=2.5)
        c.text(x_funnel + 7, y + 26, f"{enters}%", size=10.5, fill=accent, weight="bold")
        c.text(x_funnel + 7, y + 38, "of turns reach here", size=6.0, fill=C["muted"])
        if passes_on:
            c.text(x_funnel + 7, y + 49, f"{passes_on}% escalate further", size=6.0,
                   fill=C["faint"])

        bx = 172.0
        c.text(bx, y + 18, tag, size=6.6, fill=accent, weight="bold")
        c.text(bx + 34, y + 18, name, size=8.0, fill=C["ink"], weight="bold")
        dy = y + 30
        for line in detail.split("\n"):
            c.text(bx, dy, line, size=6.4, fill=C["muted"])
            dy += 9.2
        c.text(410, y + 18, latency, size=7.8, fill=accent, weight="bold")
        c.text(410, y + 30, cost, size=6.2, fill=C["faint"])
        if y > 34:
            c.line(8, y + 2, W - 8, y + 2, stroke=C["rule_soft"], sw=0.6)
        y += h + 4

    y += 6
    c.rect(8, y, W - 16, 44, fill=C["accent_soft"], stroke=C["accent"], sw=1.0, rx=3.5)
    c.text(16, y + 15, "Expected added latency per turn", size=7.2, fill=C["accent_dark"],
           weight="bold")
    c.text(16, y + 28, "0.98 x 1 ms + 0.38 x 35 ms + 0.12 x 65 ms = about 22 ms mean, with a p99 near 120 ms on the escalating tail.",
           size=6.7, fill=C["body"])
    c.text(16, y + 38, "Running Stage 2 unconditionally would cost about 65 ms on every turn for the same coverage, a 3x rail tax.",
           size=6.7, fill=C["muted"])

    y += 54
    c.text(8, y, "Guardrails need their own evaluation, or they silently become a refusal machine",
           size=7.2, fill=C["ink"], weight="bold")
    metrics = [
        ("False negative rate", "by attack family, not in aggregate"),
        ("False positive rate", "per journey, on benign golden traffic"),
        ("Refusal correctness", "did it refuse for the stated reason"),
        ("Rail latency p99", "budgeted like any other dependency"),
    ]
    mx = 8
    for title, note in metrics:
        c.rect(mx, y + 8, (W - 34) / 4, 30, fill=C["paper"], stroke=C["rule"], sw=0.8, rx=2.5)
        c.text(mx + 7, y + 21, title, size=6.5, fill=C["ink"], weight="bold")
        c.text(mx + 7, y + 31, note, size=6.0, fill=C["muted"])
        mx += (W - 34) / 4 + 6
    return c.finish()


# ==========================================================================
# 9. Load conversion funnel
# ==========================================================================


@figure("load-funnel")
def load_funnel() -> Canvas:
    c = Canvas(W)
    c.text(8, 17, "From the number you have to the number that sizes the fleet",
           size=7.4, fill=C["ink"], weight="bold")
    c.text(8, 28, "Worked for the mid tier. Every arrow is an assumption you must replace with your own measurement.",
           size=6.6, fill=C["muted"])

    steps = [
        ("Registered users", "1,000,000", "the number in the business case", C["muted"]),
        ("Monthly actives", "400,000", "x 0.40 engagement", C["muted"]),
        ("Daily actives", "80,000", "x 0.20 of monthly", C["accent"]),
        ("Assisted sessions per day", "24,000", "x 0.30 use the agent", C["accent"]),
        ("Peak hour sessions", "4,800", "x 0.20 in the busiest hour", C["accent"]),
        ("Concurrent sessions", "3,000", "Little's law, 225 s mean session", C["teal"]),
        ("In flight requests", "260", "x 4.5 s per turn, 20 s think time", C["teal"]),
        ("Control path model calls per second", "310", "x 2.6 calls per turn, fast tier", C["violet"]),
        ("Control path tokens per second", "62,000", "x 200 output tokens per call", C["violet"]),
    ]

    y = 40
    row_h = 30
    max_bar = 210.0
    for index, (label, value, note, accent) in enumerate(steps):
        # log-ish bar so the small numbers remain visible
        magnitude = 1.0 - index / (len(steps) + 0.6)
        c.rect(8, y, max_bar * magnitude, row_h - 6, fill=C["wash2"], rx=2)
        c.rect(8, y, 2.6, row_h - 6, fill=accent, rx=1.3)
        c.text(16, y + 15.5, label, size=7.0, fill=C["ink"])
        c.text(232, y + 16, value, size=9.0, fill=accent, anchor="end", weight="bold")
        c.text(244, y + 15.5, note, size=6.4, fill=C["muted"])
        if index < len(steps) - 1:
            c.arrow(120, y + row_h - 6, 120, y + row_h + 1.5, stroke=C["rule"], sw=0.9,
                    head=4.4)
        y += row_h

    y += 6
    c.line(8, y, W - 8, y, stroke=C["rule"], sw=0.8)
    y += 14
    c.text(8, y, "The two multipliers that are always underestimated", size=7.2,
           fill=C["ink"], weight="bold")
    y += 12
    blocks = [
        ("Fan out per turn", C["accent"], [
            "control path model calls: 2-4",
            "domain API calls: 1-6",
            "database queries: 2-12",
            "retrieval requests: 0-3",
        ]),
        ("Amplification on top", C["danger"], [
            "retries under partial failure: 1.1-3x",
            "guardrail calls per turn: 1-3",
            "judge sampling: 0.02-0.2x",
            "shadow and canary traffic: 0-1x",
        ]),
    ]
    bx = 8
    for title, accent, items in blocks:
        c.rect(bx, y, (W - 22) / 2, 68, fill=C["paper"], stroke=C["rule"], sw=0.9, rx=3)
        c.rect(bx, y + 1, 2.6, 66, fill=accent, rx=1.3)
        c.text(bx + 10, y + 14, title, size=7.0, fill=accent, weight="bold")
        iy = y + 27
        for item in items:
            c.text(bx + 10, iy, "\u2022", size=6.3, fill=accent)
            c.text(bx + 16, iy, item, size=6.4, fill=C["body"])
            iy += 10
        bx += (W - 22) / 2 + 6

    y += 78
    c.rect(8, y, W - 16, 26, fill=C["warn_soft"], stroke=C["warn"], sw=1.0, rx=3)
    c.text(16, y + 11, "Capacity identity", size=6.9, fill=C["warn"], weight="bold")
    c.text(16, y + 21, "effective load = ingress rate x fan out per request x retry amplification x assurance multiplier, then x tokens per call",
           size=6.5, fill=C["body"])
    return c.finish()


# ==========================================================================
# 10-12. Deployment topologies by load tier
# ==========================================================================


def _topology(tier: str, headline: str, subhead: str, accent: str, nodes: list,
              notes: list, sizing: list) -> Canvas:
    c = Canvas(W)
    c.rect(8, 8, W - 16, 24, fill=accent, rx=3)
    c.text(18, 24, tier, size=9.0, fill=C["paper"], weight="bold")
    c.text(74, 24, headline, size=8.2, fill=C["paper"])
    c.text(W - 18, 24, subhead, size=7.0, fill=C["paper"], anchor="end")

    y = 42
    for group_name, boxes in nodes:
        c.text(8, y + 9, group_name, size=6.8, fill=C["faint"], weight="bold")
        y += 15
        box_w = (W - 16 - (len(boxes) - 1) * 6) / len(boxes)
        for index, (title, spec, lines, fill, stroke) in enumerate(boxes):
            x = 8 + index * (box_w + 6)
            h = 30 + len(lines) * 9.6
            c.rect(x, y, box_w, h, fill=fill, stroke=stroke, sw=1.0, rx=3)
            c.rect(x, y + 1, 2.6, h - 2, fill=stroke, rx=1.3)
            c.text(x + 9, y + 13, title, size=7.2, fill=C["ink"], weight="bold")
            c.text(x + 9, y + 23, spec, size=6.3, fill=C["muted"])
            ly = y + 34
            for line in lines:
                c.text(x + 9, ly, line, size=6.2, fill=C["body"])
                ly += 9.6
        y += 30 + max(len(b[2]) for b in boxes) * 9.6 + 10

    y += 2
    c.line(8, y, W - 8, y, stroke=C["rule_soft"], sw=0.8)
    y += 13
    c.text(8, y, "Sizing arithmetic", size=7.2, fill=C["ink"], weight="bold")
    y += 11
    for label, value in sizing:
        c.text(14, y, label, size=6.5, fill=C["muted"])
        c.text(W - 14, y, value, size=6.5, fill=C["ink"], anchor="end", weight="bold")
        c.line(14, y + 3.2, W - 14, y + 3.2, stroke=C["rule_soft"], sw=0.5)
        y += 12.5

    y += 6
    wrapped = [wrap(note, 126) for note in notes]
    box_h = 14 + sum(len(lines) * 9.6 + 2.4 for lines in wrapped)
    c.rect(8, y, W - 16, box_h, fill=C["wash"], stroke=C["rule_soft"], sw=0.9, rx=3)
    ny = y + 14
    for lines in wrapped:
        for line_index, line in enumerate(lines):
            if line_index == 0:
                c.text(15, ny, "\u2022", size=6.3, fill=accent)
            c.text(22, ny, line, size=6.4, fill=C["body"])
            ny += 9.6
        ny += 2.4
    return c.finish()


@figure("topology-tier-s")
def topology_tier_s() -> Canvas:
    return _topology(
        "TIER S", "Fewer than 10 customers", "pilot, design partner, internal beta",
        C["teal"],
        [
            ("Single inference node", [
                ("GPU 0", "1 x RTX PRO 6000 Blackwell, 96 GB", [
                    "Tier 1 router, 4B, FP8",
                    "guard classifier, 86M",
                    "Tier 2 synthesis, 8B, FP8",
                ], C["teal_soft"], C["teal"]),
                ("Host", "32 vCPU, 256 GB RAM, NVMe", [
                    "vLLM, two served models",
                    "registry and session in Postgres",
                    "traces to a local collector",
                ], C["paper"], C["rule"]),
            ]),
            ("Off node", [
                ("Frontier tier", "API, pay as you go", [
                    "Tier 3 planning only",
                    "no reserved capacity yet",
                ], C["violet_soft"], C["violet"]),
                ("Judges", "API, batch overnight", [
                    "eval runs, not live sampling",
                ], C["wash2"], C["muted"]),
                ("Domains", "existing services", [
                    "no new hardware",
                ], C["paper"], C["rule"]),
            ]),
        ],
        [
            "One GPU is a single point of failure. Accept it here, but write the degraded mode down: deterministic routing plus templated answers when the node is gone.",
            "Do not buy HBM-class hardware at this tier. You are buying the ability to measure your own workload, not throughput you cannot yet use.",
            "The expensive mistake at Tier S is skipping telemetry. Without per-stage traces you will size Tier M from guesses.",
        ],
        [
            ("Peak concurrent sessions", "under 40"),
            ("In flight requests at peak", "3 to 6"),
            ("Control path calls per second", "8 to 15"),
            ("Control path tokens per second", "1,500 to 3,000"),
            ("GPU count, steady state", "1"),
            ("Utilisation target", "20 to 35% - headroom is the point"),
        ],
    )


@figure("topology-tier-m")
def topology_tier_m() -> Canvas:
    return _topology(
        "TIER M", "1,000 to 5,000 concurrent sessions", "regional production",
        C["accent"],
        [
            ("Fast tier pool - latency critical, scaled for p99", [
                ("Router pool", "3 x L40S or RTX PRO 6000", [
                    "Tier 1, 4B, FP8",
                    "one node may fail",
                    "pinned, never preempted",
                ], C["teal_soft"], C["teal"]),
                ("Guard pool", "2 x L40S", [
                    "86M classifier, 8B guard",
                    "isolated from user traffic",
                ], C["warn_soft"], C["warn"]),
                ("Synthesis pool", "4 x H100 or H200", [
                    "Tier 2, 8-32B, FP8",
                    "continuous batching",
                ], C["accent_soft"], C["accent"]),
            ]),
            ("Assurance and durable tiers - throughput, not latency", [
                ("Judge pool", "2 x L40S, own quota", [
                    "async sampling at 5-20%",
                    "hard concurrency cap",
                ], C["wash2"], C["muted"]),
                ("Frontier tier", "API with reserved capacity", [
                    "Tier 3, 1-4% of turns",
                    "local fallback defined",
                ], C["violet_soft"], C["violet"]),
                ("Durable workers", "CPU only", [
                    "queue, workflow, retries",
                ], C["paper"], C["rule"]),
            ]),
        ],
        [
            "Separate pools exist to stop a judge burst or a guard-model retry storm from consuming the capacity the fast path needs. One shared pool re-couples what the architecture just separated.",
            "Size the fast tier on p99 under burst, not on mean throughput. A router at 85% utilisation has queue wait that dominates its own 20 ms service time.",
            "Reserve frontier capacity once escalation volume is predictable; pay-as-you-go quota becomes the binding constraint before your GPUs do.",
        ],
        [
            ("Peak concurrent sessions", "3,000"),
            ("In flight requests at peak", "about 260"),
            ("Control path calls per second", "about 310"),
            ("Control path tokens per second", "about 62,000"),
            ("Guard rail calls per second", "about 340"),
            ("GPU count, steady state", "11 plus 2 spare"),
            ("Utilisation target, fast tier", "45 to 60%"),
        ],
    )


@figure("topology-tier-l")
def topology_tier_l() -> Canvas:
    return _topology(
        "TIER L", "More than 50,000 concurrent sessions", "multi region, disaggregated",
        C["violet"],
        [
            ("Per region cell - the unit you replicate, not the thing you grow", [
                ("Prefill nodes", "8 x B200, NVFP4", [
                    "compute bound, long inputs",
                    "scales with prompt length",
                ], C["accent_soft"], C["accent"]),
                ("Decode nodes", "16 x H200 or B200", [
                    "bandwidth bound, KV resident",
                    "scales with concurrency",
                ], C["teal_soft"], C["teal"]),
                ("KV transfer", "NVLink and RDMA fabric", [
                    "prefill to decode handoff",
                    "the new failure domain",
                ], C["wash2"], C["muted"]),
            ]),
            ("Shared and global", [
                ("Guard fleet", "6 x L40S per region", [
                    "rails scale with turns",
                ], C["warn_soft"], C["warn"]),
                ("Judge fleet", "8 x L40S, global", [
                    "batch, off peak, own budget",
                ], C["wash2"], C["muted"]),
                ("Frontier tier", "provisioned throughput", [
                    "committed, not on demand",
                ], C["violet_soft"], C["violet"]),
                ("Control plane", "replicated, regional cache", [
                    "registry must survive a region",
                ], C["paper"], C["rule"]),
            ]),
        ],
        [
            "Disaggregating prefill from decode stops long prompts from stalling the decode queue. It is worth the fabric complexity only once one pool is clearly starving the other - measure before you split.",
            "At this scale the control plane, not the GPUs, is the availability risk. A registry outage that blocks routing takes every region down at once; regional last-known-good caches and static routes for critical journeys are mandatory.",
            "Capacity is bought in cells. Growth adds cells with known behaviour rather than enlarging one pool whose tail latency degrades non-linearly.",
            "Judge and shadow traffic must have a hard budget. At 50,000 concurrent sessions, 10% sampling is a larger workload than most Tier M deployments serve in total.",
        ],
        [
            ("Peak concurrent sessions", "50,000 plus"),
            ("In flight requests at peak", "about 4,300"),
            ("Control path calls per second", "about 5,200"),
            ("Control path tokens per second", "about 1,040,000"),
            ("Regions", "3, each sized for 2 of 3 surviving"),
            ("GPU count per region", "about 30 plus spares"),
            ("Utilisation target, decode", "60 to 75% with admission control"),
        ],
    )


# ==========================================================================
# 13. GPU selection decision tree
# ==========================================================================


@figure("gpu-decision")
def gpu_decision() -> Canvas:
    c = Canvas(W)

    c.text(8, 17, "Pick the GPU from the constraint that actually binds, not from the top of the price list",
           size=7.4, fill=C["ink"], weight="bold")

    y = 32
    questions = [
        ("Does the model fit in 48 GB at FP8, and is the pool latency critical?",
         "L40S, 48 GB, 0.86 TB/s", "cheapest per served token for small routers and guard models; no NVLink, no FP4",
         C["teal"], C["teal_soft"]),
        ("Do you need one card to hold several models with isolated KV caches?",
         "RTX PRO 6000 Blackwell, 96 GB, 1.79 TB/s", "air cooled PCIe, NVFP4 capable; the pragmatic single node choice",
         C["teal"], C["teal_soft"]),
        ("Is decode throughput on an 8 to 70B model the binding constraint?",
         "H100, 80 GB, 3.35 TB/s", "proven FP8 path and mature kernels; no FP4",
         C["accent"], C["accent_soft"]),
        ("Is the constraint KV cache capacity from long context or high concurrency?",
         "H200, 141 GB, 4.8 TB/s", "you are buying memory and bandwidth, not compute; same compute as H100",
         C["accent"], C["accent_soft"]),
        ("Is cost per million tokens at very high volume the deciding factor?",
         "B200, about 180 GB, about 7.7 TB/s", "native FP4 changes the economics on 70B class models; power and cooling are real constraints",
         C["violet"], C["violet_soft"]),
        ("Is a single model larger than one node, needing one NVLink domain?",
         "GB200 NVL72 class, rack scale", "liquid cooled, long lead time; justify with a workload you have already measured",
         C["violet"], C["violet_soft"]),
    ]
    for question, answer, note, accent, soft in questions:
        c.rect(8, y, W - 16, 40, fill=soft, stroke=accent, sw=1.0, rx=3)
        c.rect(8, y + 1, 2.6, 38, fill=accent, rx=1.3)
        c.text(16, y + 14, question, size=7.0, fill=C["ink"])
        c.text(16, y + 26, answer, size=7.4, fill=accent, weight="bold")
        c.text(16, y + 35, note, size=6.2, fill=C["muted"])
        y += 44

    y += 4
    c.rect(8, y, W - 16, 58, fill=C["danger_soft"], stroke=C["danger"], sw=1.0, rx=3)
    c.text(16, y + 14, "The three sizing errors that actually cost money", size=7.2,
           fill=C["danger"], weight="bold")
    errors = [
        "Sizing decode capacity from FLOPS. Decode reads the whole model per token, so bandwidth sets the ceiling; an A100 loses roughly half its modern throughput because it has no FP8 path at all.",
        "Forgetting the KV cache. Weights are the easy part of the budget; concurrency times context length decides whether the card is usable at your batch size.",
        "Buying the frontier card for a router. A 4B classifier on a B200 wastes the asset that only a 70B decode pool can monetise.",
    ]
    ey = y + 26
    for error in errors:
        for line_index, line in enumerate(wrap(error, 118)):
            if line_index == 0:
                c.text(16, ey, "\u2022", size=6.3, fill=C["danger"])
            c.text(23, ey, line, size=6.4, fill=C["body"])
            ey += 9.4
    return c.finish()


# ==========================================================================
# 14. Quantization tradeoff
# ==========================================================================


@figure("quantization-tradeoff")
def quantization_tradeoff() -> Canvas:
    c = Canvas(W)

    c.text(8, 17, "Quantization format is a workload decision, and the honest cost is accuracy",
           size=7.4, fill=C["ink"], weight="bold")
    c.text(8, 28, "Published Qwen3-8B figures on a single H100 with vLLM. Re-measure on your own prompt and output mix before committing.",
           size=6.5, fill=C["muted"])

    # -- accuracy panel ----------------------------------------------------
    panel_w = (W - 22) / 2
    c.rect(8, 38, panel_w, 148, fill=C["paper"], stroke=C["rule"], sw=1.0, rx=3)
    c.text(18, 53, "Accuracy, MMLU", size=7.2, fill=C["ink"], weight="bold")
    c.text(18, 63, "lower is a real capability loss, not a rounding error", size=6.2,
           fill=C["muted"])

    formats = [
        ("BF16", 74.78, C["muted"]),
        ("FP8 static", 74.79, C["teal"]),
        ("FP8 dynamic", 74.75, C["teal"]),
        ("INT8 dynamic", 74.84, C["accent"]),
        ("INT4 AWQ", 73.59, C["warn"]),
        ("INT4 GPTQ", 73.26, C["danger"]),
    ]
    base = 72.8
    span = 2.4
    bar_x = 84.0
    bar_max = panel_w - 84 - 34
    y = 76
    for label, value, colour in formats:
        c.text(18, y + 8, label, size=6.6, fill=C["body"])
        width = bar_max * (value - base) / span
        c.rect(bar_x, y, max(width, 1.5), 11, fill=colour, rx=1.4)
        c.text(bar_x + bar_max + 4, y + 8, f"{value:.2f}", size=6.6, fill=colour,
               weight="bold")
        y += 17
    c.text(18, y + 6, "Axis starts at 72.8 to make the INT4 gap visible.", size=6.0,
           fill=C["faint"], italic=True)

    # -- throughput panel --------------------------------------------------
    px = 8 + panel_w + 6
    c.rect(px, 38, panel_w, 148, fill=C["paper"], stroke=C["rule"], sw=1.0, rx=3)
    c.text(px + 10, 53, "Saturated throughput, tokens per second", size=7.2, fill=C["ink"],
           weight="bold")
    c.text(px + 10, 63, "aggregate under load, H100, ShareGPT-shaped traffic", size=6.2,
           fill=C["muted"])

    throughput = [
        ("FP8 static", 16452, C["teal"]),
        ("FP8 dynamic", 15276, C["teal"]),
        ("INT4 W4A16", 13605, C["warn"]),
        ("BF16", 13305, C["muted"]),
        ("INT4 AWQ", 9756, C["danger"]),
    ]
    tmax = 17000.0
    bar_x2 = px + 76
    bar_max2 = panel_w - 76 - 44
    y = 78
    for label, value, colour in throughput:
        c.text(px + 10, y + 8, label, size=6.6, fill=C["body"])
        c.rect(bar_x2, y, bar_max2 * value / tmax, 11, fill=colour, rx=1.4)
        c.text(px + panel_w - 10, y + 8, f"{value:,}", size=6.6, fill=colour,
               anchor="end", weight="bold")
        y += 17
    c.text(px + 10, y + 6, "FP8 wins here because Hopper has native FP8 tensor cores.",
           size=6.0, fill=C["faint"], italic=True)

    # -- regime rule -------------------------------------------------------
    y = 196
    c.text(8, y, "The rule that reconciles the two panels", size=7.2, fill=C["ink"],
           weight="bold")
    y += 10
    regimes = [
        ("Batch size 1, latency critical", C["teal"], [
            "the limiter is weight traffic through memory",
            "4-bit moves less, so it wins single stream",
            "use for interactive routers and classifiers",
        ]),
        ("Saturated, throughput critical", C["accent"], [
            "the limiter is tensor core occupancy",
            "FP8 W8A8 wins on Hopper and newer",
            "use for synthesis pools and batch work",
        ]),
    ]
    rx = 8
    for title, accent, items in regimes:
        c.rect(rx, y, panel_w, 58, fill=C["paper"], stroke=accent, sw=1.0, rx=3)
        c.text(rx + 10, y + 14, title, size=7.0, fill=accent, weight="bold")
        iy = y + 27
        for item in items:
            c.text(rx + 10, iy, "\u2022", size=6.3, fill=accent)
            c.text(rx + 16, iy, item, size=6.3, fill=C["body"])
            iy += 9.6
        rx += panel_w + 6

    y += 68
    c.rect(8, y, W - 16, 46, fill=C["warn_soft"], stroke=C["warn"], sw=1.0, rx=3)
    c.text(16, y + 14, "Where quantization loss actually shows up in an agent",
           size=7.0, fill=C["warn"], weight="bold")
    c.text(16, y + 26, "Aggregate benchmarks hide the failures that matter. A 1.2 point MMLU drop can appear as a 6 point drop in strict",
           size=6.4, fill=C["body"])
    c.text(16, y + 35, "tool-argument correctness or a measurable rise in over-refusal. Evaluate the quantized model on your own routing,",
           size=6.4, fill=C["body"])
    c.text(16, y + 44, "parameter extraction and refusal suites before it goes anywhere near the fast path.",
           size=6.4, fill=C["body"])
    return c.finish()


# ==========================================================================
# 15. Failure isolation
# ==========================================================================


@figure("failure-isolation")
def failure_isolation() -> Canvas:
    c = Canvas(W)

    c.text(8, 17, "One domain fails. The question is whether the platform notices or the user does.",
           size=7.4, fill=C["ink"], weight="bold")

    panel_w = (W - 22) / 2

    # -- federated ---------------------------------------------------------
    c.rect(8, 28, panel_w, 196, fill=C["paper"], stroke=C["teal"], sw=1.1, rx=3.5)
    c.rect(8, 28, panel_w, 20, fill=C["teal_soft"], rx=3.5)
    c.rect(8, 42, panel_w, 6, fill=C["teal_soft"])
    c.text(8 + panel_w / 2, 42, "Federated with fault containment", size=7.2,
           fill=C["teal"], anchor="middle", weight="bold")

    cx = 8 + panel_w / 2
    c.box(cx - 54, 58, 108, 26, title="Central agent", subtitle="deadline owner",
          fill=C["accent_soft"], stroke=C["accent"], title_size=7.0, sub_size=6.0)
    doms = [("Rewards", C["danger"], C["danger_soft"], "open, 12 ms"),
            ("Transactions", C["teal"], C["teal_soft"], "healthy"),
            ("Cards", C["teal"], C["teal_soft"], "healthy")]
    dw = (panel_w - 26) / 3
    for index, (name, accent, soft, state) in enumerate(doms):
        dx = 8 + 13 + index * dw
        c.rect(dx, 108, dw - 5, 34, fill=soft, stroke=accent, sw=1.0, rx=2.5)
        c.text(dx + (dw - 5) / 2, 121, name, size=6.6, fill=C["ink"], anchor="middle",
               weight="bold")
        c.text(dx + (dw - 5) / 2, 131, state, size=5.8, fill=accent, anchor="middle")
        c.arrow(cx, 84, dx + (dw - 5) / 2, 105, stroke=accent, sw=0.9, head=4.4,
                dash="2,2" if index == 0 else None)
        if index == 0:
            c.text(dx + (dw - 5) / 2, 152, "breaker open", size=5.8, fill=C["danger"],
                   anchor="middle", weight="bold")
    c.rect(8 + 13, 162, panel_w - 26, 50, fill=C["wash"], stroke=C["rule_soft"], sw=0.9,
           rx=2.5)
    c.text(8 + 20, 175, "What the user gets", size=6.6, fill=C["ink"], weight="bold")
    outcomes = [
        "the two healthy domains answer normally",
        "the failed domain returns a named partial",
        "the trace shows one red span, not a mystery",
    ]
    oy = 186
    for item in outcomes:
        c.text(8 + 20, oy, "\u2022", size=6.2, fill=C["teal"])
        c.text(8 + 26, oy, item, size=6.2, fill=C["body"])
        oy += 9.4

    # -- coupled -----------------------------------------------------------
    px = 8 + panel_w + 6
    c.rect(px, 28, panel_w, 196, fill=C["paper"], stroke=C["danger"], sw=1.1, rx=3.5)
    c.rect(px, 28, panel_w, 20, fill=C["danger_soft"], rx=3.5)
    c.rect(px, 42, panel_w, 6, fill=C["danger_soft"])
    c.text(px + panel_w / 2, 42, "Monolith or in-process orchestration", size=7.2,
           fill=C["danger"], anchor="middle", weight="bold")

    pcx = px + panel_w / 2
    c.rect(px + 16, 58, panel_w - 32, 84, fill=C["danger_soft"], stroke=C["danger"],
           sw=1.1, rx=3)
    c.text(pcx, 72, "One process, one deployable", size=7.0, fill=C["danger"],
           anchor="middle", weight="bold")
    for index, name in enumerate(["Rewards", "Transactions", "Cards"]):
        mx = px + 24 + index * ((panel_w - 48) / 3)
        c.rect(mx, 82, (panel_w - 48) / 3 - 4, 26, fill=C["paper"], stroke=C["danger_mid"],
               sw=0.9, rx=2)
        c.text(mx + ((panel_w - 48) / 3 - 4) / 2, 94, name, size=6.2, fill=C["ink"],
               anchor="middle")
        c.text(mx + ((panel_w - 48) / 3 - 4) / 2, 103, "module", size=5.6,
               fill=C["muted"], anchor="middle")
    c.text(pcx, 122, "shared heap, shared thread pool, shared GC pause", size=6.0,
           fill=C["danger"], anchor="middle")
    c.text(pcx, 133, "shared release train, shared blast radius", size=6.0,
           fill=C["danger"], anchor="middle")

    c.rect(px + 16, 162, panel_w - 32, 50, fill=C["danger_soft"], stroke=C["danger_mid"],
           sw=0.9, rx=2.5)
    c.text(px + 23, 175, "What the user gets", size=6.6, fill=C["ink"], weight="bold")
    bad = [
        "one leaking module degrades every journey",
        "no per domain breaker to open",
        "rollback reverts unrelated teams' work",
    ]
    by = 186
    for item in bad:
        c.text(px + 23, by, "\u2022", size=6.2, fill=C["danger"])
        c.text(px + 29, by, item, size=6.2, fill=C["body"])
        by += 9.4

    # -- containment requirements -----------------------------------------
    y = 238
    c.text(8, y, "Containment is a set of mechanisms, not a diagram property", size=7.2,
           fill=C["ink"], weight="bold")
    y += 10
    mechanisms = [
        ("Per dependency budget", "a timeout shorter than the caller's remaining deadline, not a global default"),
        ("Circuit breaker per domain", "opened on error rate and latency, with a defined half-open probe"),
        ("Bulkheaded pools", "a saturated domain cannot consume the connections another domain needs"),
        ("Named partial results", "the response states what is missing, so the user is not silently misinformed"),
        ("Idempotency on writes", "a retry after an ambiguous timeout must not double-post"),
        ("Degraded mode, pre-agreed", "deterministic routing and templated answers when the model tier is unavailable"),
    ]
    for title, note in mechanisms:
        c.rect(8, y, W - 16, 17, fill=C["wash"] if mechanisms.index((title, note)) % 2 == 0 else C["paper"],
               rx=2)
        c.text(15, y + 11.5, title, size=6.6, fill=C["ink"], weight="bold")
        c.text(154, y + 11.5, note, size=6.4, fill=C["muted"])
        y += 18
    return c.finish()


# ==========================================================================
# 16. Evaluation lifecycle
# ==========================================================================


@figure("evaluation-lifecycle")
def evaluation_lifecycle() -> Canvas:
    c = Canvas(W)

    c.text(8, 17, "Evaluation is a release gate computed from the change, not a suite someone remembers to run",
           size=7.4, fill=C["ink"], weight="bold")

    steps = [
        ("1", "Change lands", "prompt, tool, skill,\nmodel, or manifest", C["muted"], C["wash2"]),
        ("2", "Classify change", "the change type picks\nthe suite, by rule", C["accent"], C["accent_soft"]),
        ("3", "Auditor runs", "reachability, manifest\nand hash integrity", C["violet"], C["violet_soft"]),
        ("4", "Suites run", "golden set, safety,\ncontract, latency", C["teal"], C["teal_soft"]),
        ("5", "Gate decides", "block, allow, or a\nnamed exception", C["danger"], C["danger_soft"]),
        ("6", "Prod sampling", "async judges and\ndrift by slice", C["warn"], C["warn_soft"]),
    ]
    box_w = (W - 16 - 5 * 5) / 6
    box_h = 74
    y = 30
    for index, (num, title, detail, accent, soft) in enumerate(steps):
        x = 8 + index * (box_w + 5)
        c.rect(x, y, box_w, box_h, fill=soft, stroke=accent, sw=1.0, rx=3)
        c.circle(x + 12, y + 13, 6.6, fill=accent)
        c.text(x + 12, y + 15.4, num, size=6.8, fill=C["paper"], anchor="middle",
               weight="bold")
        c.text(x + 7, y + 34, title, size=6.5, fill=C["ink"], weight="bold")
        dy = y + 47
        for line in detail.split("\n"):
            c.text(x + 7, dy, line, size=5.8, fill=C["muted"])
            dy += 8.4
        if index:
            c.arrow(x - 5, y + 13, x - 1, y + 13, stroke=C["rule"], sw=1.0, head=4.2)
    # feedback loop from 6 back to 1
    loop_y = y + box_h
    c.polyline([(W - 8 - box_w / 2, loop_y), (W - 8 - box_w / 2, loop_y + 13),
                (8 + box_w / 2, loop_y + 13), (8 + box_w / 2, loop_y + 4)],
               stroke=C["warn"], sw=1.0, dash="3,2")
    c.polygon([(8 + box_w / 2, loop_y), (8 + box_w / 2 - 3.2, loop_y + 6),
               (8 + box_w / 2 + 3.2, loop_y + 6)], fill=C["warn"])
    c.text(W / 2, loop_y + 24, "failures become regression cases; the corpus grows from production, not from imagination",
           size=6.3, fill=C["warn"], anchor="middle", italic=True)

    # -- change type to suite matrix ---------------------------------------
    y = 138
    c.text(8, y, "Which suites a change type triggers", size=7.2, fill=C["ink"],
           weight="bold")
    y += 10
    cols = ["Domain golden", "Contract", "Safety rails", "Latency budget", "Cross domain"]
    col_x = 168.0
    col_w = (W - 16 - (col_x - 8)) / len(cols)
    c.rect(8, y, W - 16, 18, fill=C["wash2"], rx=2)
    c.text(15, y + 12, "Change type", size=6.4, fill=C["faint"], weight="bold")
    for index, col in enumerate(cols):
        c.text(col_x + index * col_w + col_w / 2, y + 12, col, size=6.1, fill=C["faint"],
               anchor="middle", weight="bold")
    y += 18
    rows = [
        ("Domain prompt edit", [2, 1, 2, 0, 0]),
        ("New tool added", [2, 2, 2, 1, 0]),
        ("New skill added", [2, 2, 1, 1, 1]),
        ("Model or quantization swap", [2, 1, 2, 2, 1]),
        ("Central routing policy change", [1, 1, 1, 2, 2]),
        ("Guardrail threshold change", [1, 0, 2, 1, 0]),
        ("Manifest version bump", [1, 2, 1, 0, 2]),
    ]
    for label, marks in rows:
        c.line(8, y, W - 8, y, stroke=C["rule_soft"], sw=0.6)
        c.text(15, y + 12, label, size=6.4, fill=C["body"])
        for index, mark in enumerate(marks):
            mx = col_x + index * col_w + col_w / 2
            if mark == 2:
                c.circle(mx, y + 8.6, 4.0, fill=C["accent"])
            elif mark == 1:
                c.circle(mx, y + 8.6, 4.0, fill=C["paper"], stroke=C["accent"], sw=1.2)
            else:
                c.line(mx - 3, y + 8.6, mx + 3, y + 8.6, stroke=C["rule"], sw=1.0)
        y += 17
    c.line(8, y, W - 8, y, stroke=C["rule"], sw=0.7)
    y += 14
    # Hand-drawn so the legend uses the same glyphs as the matrix.
    c.circle(14, y, 4.0, fill=C["accent"])
    c.text(23, y + 2.2, "required to pass", size=6.2, fill=C["muted"])
    c.circle(138, y, 4.0, fill=C["paper"], stroke=C["accent"], sw=1.2)
    c.text(147, y + 2.2, "run and review", size=6.2, fill=C["muted"])
    c.line(259, y, 265, y, stroke=C["rule"], sw=1.0)
    c.text(271, y + 2.2, "not triggered", size=6.2, fill=C["muted"])

    y += 20
    c.rect(8, y, W - 16, 40, fill=C["danger_soft"], stroke=C["danger"], sw=1.0, rx=3)
    c.text(16, y + 14, "Why the auditor must not be the team that changed the code",
           size=7.0, fill=C["danger"], weight="bold")
    c.text(16, y + 26, "A team that selects its own evidence will select evidence that passes. The auditor is deliberately rule-based rather than",
           size=6.4, fill=C["body"])
    c.text(16, y + 35, "model-based so its verdict is reproducible, cheap to run on every change, and impossible to argue with after the fact.",
           size=6.4, fill=C["body"])
    return c.finish()


# ==========================================================================
# 17. AI engineering capability model
# ==========================================================================


@figure("skills-matrix")
def skills_matrix() -> Canvas:
    c = Canvas(W)

    c.text(8, 17, "The capabilities you must be able to hire, keep, or knowingly outsource",
           size=7.4, fill=C["ink"], weight="bold")
    c.text(8, 28, "Intensity is the depth of skill needed at that scale, not headcount.", size=6.5,
           fill=C["muted"])

    label_w = 178.0
    tiers = ["Tier S", "Tier M", "Tier L"]
    col_w = 44.0
    role_x = label_w + 8 + len(tiers) * col_w + 12

    y = 38
    c.rect(8, y, W - 16, 20, fill=C["wash2"], rx=2)
    c.text(15, y + 13.5, "Capability", size=6.5, fill=C["faint"], weight="bold")
    for index, tier in enumerate(tiers):
        c.text(label_w + 8 + index * col_w + col_w / 2, y + 13.5, tier, size=6.5,
               fill=C["faint"], anchor="middle", weight="bold")
    c.text(role_x, y + 13.5, "Where it usually sits", size=6.5, fill=C["faint"],
           weight="bold")
    y += 20

    groups = [
        ("Serving and operations", [
            ("Inference serving: vLLM or SGLang operation", [2, 3, 3], "Platform or ML infra"),
            ("Capacity modelling and load testing", [1, 3, 3], "Platform"),
            ("GPU scheduling, MIG and multi-tenancy", [1, 2, 3], "ML infra"),
            ("Rollout, canary and rollback of weights", [1, 2, 3], "ML infra"),
        ]),
        ("Model work", [
            ("Quantization and calibration set design", [2, 3, 3], "ML engineer"),
            ("Distillation of routers and classifiers", [1, 2, 3], "ML engineer"),
            ("Task fine-tuning, LoRA and adapters", [1, 2, 3], "ML engineer"),
            ("Tokenizer, context and prompt budgeting", [2, 2, 2], "Shared"),
        ]),
        ("Assurance", [
            ("Eval engineering and golden set curation", [3, 3, 3], "Domain plus platform"),
            ("LLM-as-judge calibration against humans", [1, 3, 3], "Eval owner"),
            ("Safety, red teaming and rail tuning", [2, 3, 3], "Security plus ML"),
            ("Regression corpus and drift monitoring", [1, 2, 3], "Platform"),
        ]),
        ("Runtime engineering", [
            ("Distributed tracing and AgentOps", [2, 3, 3], "Platform"),
            ("Contract and manifest tooling", [2, 2, 3], "Platform"),
            ("Cost attribution per journey", [1, 2, 3], "Platform plus finance"),
        ]),
    ]

    for group_name, items in groups:
        c.rect(8, y, W - 16, 15, fill=C["accent_soft"], rx=1.6)
        c.text(15, y + 10.6, group_name, size=6.4, fill=C["accent_dark"], weight="bold")
        y += 15
        for label, marks, owner in items:
            c.line(8, y, W - 8, y, stroke=C["rule_soft"], sw=0.55)
            c.text(15, y + 12, label, size=6.4, fill=C["body"])
            for index, mark in enumerate(marks):
                bx = label_w + 8 + index * col_w + col_w / 2 - 13
                shades = {1: C["accent_mid"], 2: C["accent"], 3: C["accent_dark"]}
                for pip in range(3):
                    filled = pip < mark
                    c.rect(bx + pip * 9, y + 5.4, 7, 7,
                           fill=shades[mark] if filled else C["rule_soft"], rx=1.2)
            c.text(role_x, y + 12, owner, size=6.2, fill=C["muted"])
            y += 17
    c.line(8, y, W - 8, y, stroke=C["rule"], sw=0.7)

    y += 12
    c.legend(8, y, [(C["accent_mid"], "aware: can follow a runbook"),
                    (C["accent"], "capable: can operate and tune"),
                    (C["accent_dark"], "deep: can diagnose and extend")],
             size=6.2, columns=3, col_width=152)

    y += 26
    c.rect(8, y, (W - 22) / 2, 70, fill=C["danger_soft"], stroke=C["danger"], sw=1.0, rx=3)
    c.text(16, y + 14, "The staffing anti-pattern", size=7.0, fill=C["danger"],
           weight="bold")
    for line_index, line in enumerate(wrap(
            "One ML generalist owning serving, quantization, evals, safety and cost. "
            "It works in the pilot, becomes the bus factor in production, and the "
            "first thing dropped is always evaluation.", 62)):
        c.text(16, y + 27 + line_index * 9.4, line, size=6.4, fill=C["body"])

    px = 8 + (W - 22) / 2 + 6
    c.rect(px, y, (W - 22) / 2, 70, fill=C["teal_soft"], stroke=C["teal"], sw=1.0, rx=3)
    c.text(px + 8, y + 14, "A defensible build order", size=7.0, fill=C["teal"],
           weight="bold")
    order = [
        "1. eval engineering, before any model choice",
        "2. serving and observability, then quantization",
        "3. safety and rail tuning as traffic grows",
        "4. distillation and fine-tuning last, when the",
        "    workload is stable enough to be worth it",
    ]
    for line_index, line in enumerate(order):
        c.text(px + 8, y + 27 + line_index * 8.6, line, size=6.3, fill=C["body"])
    return c.finish()


# ==========================================================================
# 18. Reference implementation: the 12 demo steps
# ==========================================================================


@figure("demo-steps")
def demo_steps() -> Canvas:
    c = Canvas(W)

    c.text(8, 17, "The twelve demonstration steps, and the architectural claim each one makes falsifiable",
           size=7.4, fill=C["ink"], weight="bold")

    steps = [
        (1, "Domain discovery", "two domains register and are discovered",
         "capability is declared, not hard-coded", C["accent"]),
        (2, "Agent cards", "A2A v1.0 over JSON-RPC, versioned",
         "a contract exists that can be validated", C["accent"]),
        (3, "Central prompt change", "prompt hash 8ab1 to 91fd",
         "central behaviour is versioned and auditable", C["accent"]),
        (4, "Tool added to a domain", "domain bundle m-rew-10 to m-rew-11",
         "the domain changes without a platform release", C["teal"]),
        (5, "Skill added to a domain", "bundle m-rew-11 to m-rew-12",
         "capability grows without touching the centre", C["teal"]),
        (6, "Targeted evaluation", "suite selected from the change type",
         "evidence is chosen by rule, not by the author", C["violet"]),
        (7, "Regression caught", "restaurant 3x read as grocery 2x; 300 points seen as 200",
         "a real semantic bug is caught before release", C["danger"]),
        (8, "Auditor verdict", "closed world reachability recomputed",
         "governance is independent of the changing team", C["violet"]),
        (9, "Delegation trace", "one correlation id across every hop",
         "attribution survives federation", C["warn"]),
        (10, "Model call accounting", "tier, tokens and latency per span",
         "cost and latency are attributable per journey", C["warn"]),
        (11, "Domain isolation", "Rewards fails in 12 ms; Transactions stays healthy",
         "failure is contained, not systemic", C["danger"]),
        (12, "Governed release", "gate passes with a named owner",
         "release is a decision with evidence attached", C["teal"]),
    ]

    y = 28
    c.rect(8, y, W - 16, 17, fill=C["wash2"], rx=2)
    c.text(15, y + 11.6, "Step", size=6.4, fill=C["faint"], weight="bold")
    c.text(46, y + 11.6, "What the demo shows", size=6.4, fill=C["faint"], weight="bold")
    c.text(162, y + 11.6, "Concrete artefact in the prototype", size=6.4, fill=C["faint"],
           weight="bold")
    c.text(322, y + 11.6, "The claim it makes testable", size=6.4, fill=C["faint"],
           weight="bold")
    y += 17

    for number, title, artefact, claim, accent in steps:
        h = 21
        c.rect(8, y, W - 16, h, fill=C["paper"] if number % 2 else C["wash"], rx=1.6)
        c.rect(8, y + 1, 2.4, h - 2, fill=accent, rx=1.2)
        c.circle(24, y + 10.5, 6.2, fill=accent)
        c.text(24, y + 13, str(number), size=6.4, fill=C["paper"], anchor="middle",
               weight="bold")
        c.text(38, y + 13, title, size=6.5, fill=C["ink"], weight="bold")
        c.text(162, y + 13, artefact, size=6.2, fill=C["muted"])
        c.text(322, y + 13, claim, size=6.2, fill=C["body"])
        y += h

    y += 10
    c.rect(8, y, W - 16, 46, fill=C["accent_soft"], stroke=C["accent"], sw=1.0, rx=3)
    c.text(16, y + 14, "What the prototype does not prove", size=7.0, fill=C["accent_dark"],
           weight="bold")
    c.text(16, y + 26, "The demonstration is a deterministic replay of recorded events, not a load test. It establishes that the control surfaces exist",
           size=6.4, fill=C["body"])
    c.text(16, y + 35, "and that the seams are in the right places. Every latency and throughput figure in Part IV is third-party or modelled, and",
           size=6.4, fill=C["body"])
    c.text(16, y + 44, "must be re-measured against your own workload before it is used to buy hardware.", size=6.4, fill=C["body"])
    return c.finish()


PREVIEW_HEADER = """---
title: Figure Proof Sheet
subtitle: Every generated diagram, one per page, at final size
kicker: Build artifact
author: Sarang Pramode
version: Proof sheet
date: August 2026
status: Not for distribution
running_title: Figure proof sheet
footer_left: Figure proof sheet
---

# Proof Sheet {-}

Each figure below is rendered at the width it will occupy in the document.

"""


def write_preview(names: list[str]) -> str:
    """Emit a Markdown proof sheet so every figure can be eyeballed at size."""
    tmp = os.path.join(os.path.dirname(OUT), "tmp")
    os.makedirs(tmp, exist_ok=True)
    path = os.path.join(tmp, "figures.md")
    chunks = [PREVIEW_HEADER]
    for name in names:
        chunks.append(f"## {name} {{-}}\n\n::: figure src={name}.svg width=full\n"
                      f"Proof of `{name}.svg`.\n:::\n\n::: pagebreak\n")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(chunks))
    return path


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true",
                    help="also write tmp/figures.md as a proof sheet")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    written = []
    for name, fn in FIGURES.items():
        canvas = fn()
        path = os.path.join(OUT, f"{name}.svg")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(canvas.render())
        written.append((name, canvas.width, canvas.height, canvas.overflow))
    width = max(len(n) for n, _, _, _ in written)
    problems = 0
    for name, w, h, overflow in written:
        flag = "  TOO TALL FOR ONE PAGE" if h > 600 else ""
        print(f"  {name.ljust(width)}  {w:g} x {h:g}{flag}")
        if flag:
            problems += 1
        for note in dict.fromkeys(overflow):
            print(f"    overflow: {note}")
            problems += 1
    print(f"{len(written)} figures written to {OUT}")
    if problems:
        print(f"{problems} layout problem(s) reported above")
    if args.preview:
        print(f"proof sheet: {write_preview([n for n, _, _, _ in written])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
