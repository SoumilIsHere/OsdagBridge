"""
styles.py -- single source of truth for the OsdagBridge design-report look.

Every layout rule, colour, table setting, header/footer string and chart
setting used by the report generator lives in this module.  Chapter files and
``report_generator.py`` must *import* from here instead of hard-coding values.

To restyle the whole report, edit the constants below -- nothing else.

Sections
--------
1. PALETTE        colours (LaTeX HTML hex + matplotlib hex)
2. PAGE           paper, margins, header/footer geometry, base font
3. TABLE          cell padding, rule width, row height, header shading
4. HEADER_FOOTER  running header / footer text and rule widths
5. CHART          matplotlib theme used by charts.py
6. Builders       functions that turn the constants into LaTeX snippets
"""

# ═══════════════════════════════════════════════════════════════════════════
# 1. PALETTE  (hex without '#', as LaTeX \definecolor{..}{HTML}{..} expects)
# ═══════════════════════════════════════════════════════════════════════════
PALETTE = {
    "osdagGreen":   "91B014",   # brand colour: rules, accents
    "tableHeader":  "E8EFD0",   # light tint of osdagGreen for header rows
    "tableStripe":  "F7F9EE",   # optional zebra stripe
    "passGreen":    "5B8C1A",   # UR <= 1.0
    "failRed":      "C62828",   # UR > 1.0
    "steelBlue":    "37597D",   # steel quantities
    "concreteGrey": "8C8C8C",   # concrete quantities
    "rebarOrange":  "D9822B",   # reinforcement quantities
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. PAGE
# ═══════════════════════════════════════════════════════════════════════════
PAGE = {
    "document_class": "report",
    "font_size":      "12pt",
    "paper":          "a4paper",
    "margin":         "1in",
    # headheight/footskip give the footer room so the last table row can no
    # longer collide with it (the old default footskip was too tight when the
    # "* Software default value" note was printed).
    "headheight":     "16pt",
    "footskip":       "40pt",
    "line_stretch":   "1.15",
    # LaTeX will not stretch pages to the bottom edge; avoids huge gaps and
    # lets the footer keep its clearance.
    "raggedbottom":   True,
}

# ═══════════════════════════════════════════════════════════════════════════
# 3. TABLE
# ═══════════════════════════════════════════════════════════════════════════
TABLE = {
    "tabcolsep":        "6pt",
    "arraystretch":     "1.12",
    "extrarowheight":   "0.6pt",
    "arrayrulewidth":   "0.5pt",
    "lt_pre":           "0pt",
    "lt_post":          "6pt",
    # If fewer than this many baselines remain, start the table on a new page.
    "needspace_lines":  6,
    "header_fill":      "tableHeader",
    "continued_text":   "(continued)",
    "continued_footer": "Continued on next page",
}

# ═══════════════════════════════════════════════════════════════════════════
# 4. HEADER / FOOTER
# ═══════════════════════════════════════════════════════════════════════════
HEADER_FOOTER = {
    "footer_left":   r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay",
    "footer_right":  r"Page \thepage\ of \pageref{LastPage}",
    "head_rule_pt":  "1pt",
    "foot_rule_pt":  "1pt",
    "sd_note":       r"* Software default value",
    # Vertical offsets (pt) used when the software-default note is printed.
    # Kept small and positive-clearance so the note never climbs into the
    # table body (previously -20pt, which caused the footer overlap).
    "sd_note_raise": "-6pt",
    "sd_note_gap":   "3pt",
    "no_sd_raise":   "-4pt",
    "foot_rule_gap": "4pt",
}

# ═══════════════════════════════════════════════════════════════════════════
# 5. CHART (matplotlib)
# ═══════════════════════════════════════════════════════════════════════════
CHART = {
    "dpi":           200,
    "figsize":       (7.2, 3.6),   # inches; fits a 6.5in text width
    "font_family":   "DejaVu Sans",
    "font_size":     9,
    "title_size":    10,
    "bar_width":     0.62,
    "threshold_ur":  1.0,
    "threshold_style": {"color": "#" + PALETTE["failRed"], "linestyle": "--", "linewidth": 1.4},
    "pass_color":    "#" + PALETTE["passGreen"],
    "fail_color":    "#" + PALETTE["failRed"],
    "steel_color":   "#" + PALETTE["steelBlue"],
    "concrete_color": "#" + PALETTE["concreteGrey"],
    "rebar_color":   "#" + PALETTE["rebarOrange"],
    "grid_alpha":    0.25,
    "latex_width":   r"0.92\textwidth",
}

# Packages loaded in the preamble, in order.  (name, options)
PACKAGES = [
    ("geometry", None),   # configured separately in preamble_tex()
    ("graphicx", None), ("amsmath", None), ("amssymb", None), ("booktabs", None),
    ("array", None), ("tabularx", None), ("float", None), ("fancyhdr", None),
    ("hyperref", "hidelinks"), ("xcolor", "table"), ("setspace", None),
    ("enumitem", None), ("caption", None),
]
PACKAGES_AFTER_CAPTION = [
    ("subcaption", None), ("multirow", None), ("longtable", None),
    ("titlesec", None), ("titletoc", None), ("lastpage", None),
    ("makecell", None), ("etoolbox", None), ("needspace", None),
]


# ═══════════════════════════════════════════════════════════════════════════
# 6. BUILDERS
# ═══════════════════════════════════════════════════════════════════════════
def _usepackage(name, opts):
    return rf"\usepackage[{opts}]{{{name}}}" if opts else rf"\usepackage{{{name}}}"


def color_definitions():
    return "\n".join(rf"\definecolor{{{k}}}{{HTML}}{{{v}}}" for k, v in PALETTE.items())


def _geometry_line():
    return (rf"\usepackage[{PAGE['paper']}, margin={PAGE['margin']}, "
            rf"headheight={PAGE['headheight']}, footskip={PAGE['footskip']}]{{geometry}}")


def table_settings():
    t = TABLE
    return rf"""% Table layout (styles.TABLE)
\setlength{{\tabcolsep}}{{{t['tabcolsep']}}}
\renewcommand{{\arraystretch}}{{{t['arraystretch']}}}
\setlength{{\LTpre}}{{{t['lt_pre']}}}
\setlength{{\LTpost}}{{{t['lt_post']}}}
\setlength{{\arrayrulewidth}}{{{t['arrayrulewidth']}}}
\setlength{{\extrarowheight}}{{{t['extrarowheight']}}}
% Floating tables keep clearance at the page bottom. longtable is deliberately
% NOT given a needspace: with repeating headers it caused an orphan continued
% header and a stray footer note (found by a page-break position sweep).
\BeforeBeginEnvironment{{table}}{{\needspace{{{t['needspace_lines']}\baselineskip}}}}"""


def _footrule():
    h = HEADER_FOOTER
    return rf"""  \renewcommand{{\footrule}}{{%
    \ifbool{{hasSDonPage}}{{%
      \vspace{{{h['sd_note_raise']}}}%
      \hbox to \headwidth{{\textcolor{{black}}{{\footnotesize\textit{{{h['sd_note']}}}}}\hfil}}%
      \vspace{{{h['sd_note_gap']}}}%
    }}{{%
      \vspace{{{h['no_sd_raise']}}}%
    }}%
    \color{{osdagGreen}}\hrule width\headwidth height {h['foot_rule_pt']} \vspace{{{h['foot_rule_gap']}}}%
  }}"""


def pagestyles(pn, jn, rd, rv):
    """Header/footer page styles.  pn/jn/rd/rv are already LaTeX-escaped."""
    h = HEADER_FOOTER
    running = rf"""  \fancyhf{{}}
  \fancyhead[L]{{{pn} $|$ {jn}}}
  \fancyhead[R]{{{rd} $|$ {rv}}}
  \fancyfoot[L]{{{h['footer_left']}}}
  \fancyfoot[R]{{{h['footer_right']}}}
  \renewcommand{{\headrule}}{{\color{{osdagGreen}}\hrule width\headwidth height {h['head_rule_pt']} \vspace{{2pt}}}}
{_footrule()}"""
    return rf"""\fancypagestyle{{main}}{{
{running}
}}
\fancypagestyle{{plain}}{{
{running}
}}
\fancypagestyle{{firstpage}}{{
  \fancyhf{{}}
  \renewcommand{{\headrulewidth}}{{0pt}}
  \fancyfoot[L]{{{h['footer_left']}}}
  \fancyfoot[R]{{{h['footer_right']}}}
  \renewcommand{{\footrule}}{{\vspace{{-8pt}}\color{{osdagGreen}}\hrule width\headwidth height {h['foot_rule_pt']} \vspace{{6pt}}}}
}}"""


def preamble_tex(pn, jn, rd, rv):
    """Return the complete LaTeX preamble (up to and including \\begin{document}).

    pn, jn, rd, rv: project name, job number, date, version -- *already escaped*.
    """
    pk1 = "\n".join(_usepackage(n, o) if n != "geometry" else _geometry_line() for n, o in PACKAGES)
    pk2 = "\n".join(_usepackage(n, o) for n, o in PACKAGES_AFTER_CAPTION)
    raggedbottom = "\\raggedbottom" if PAGE["raggedbottom"] else ""
    return rf"""
\documentclass[{PAGE['font_size']},{PAGE['paper']}]{{{PAGE['document_class']}}}

% Packages (styles.PACKAGES)
{pk1}

\captionsetup{{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}}
{pk2}
\setlength{{\LTleft}}{{\fill}}
\setlength{{\LTright}}{{\fill}}

\numberwithin{{table}}{{chapter}}
\numberwithin{{figure}}{{chapter}}
{table_settings()}

% Colours (styles.PALETTE)
{color_definitions()}
{raggedbottom}

{pagestyles(pn, jn, rd, rv)}
\pagestyle{{main}}
\setstretch{{{PAGE['line_stretch']}}}

% Custom Commands
\newcommand{{\placeholder}}[1]{{\textit{{\textless #1\textgreater}}}}
\newcommand{{\todo}}[1]{{\colorbox{{yellow}}{{TODO: #1}}}}
\newcolumntype{{L}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\newcolumntype{{C}}[1]{{>{{\centering\arraybackslash}}p{{#1}}}}
\newcolumntype{{R}}[1]{{>{{\raggedleft\arraybackslash}}p{{#1}}}}

% Software-default asterisk
\newcommand{{\sdstar}}{{\textsuperscript{{*}}}}
\newbool{{hasSDonPage}}
\boolfalse{{hasSDonPage}}
\newcommand{{\markSD}}{{\global\booltrue{{hasSDonPage}}}}
\renewcommand{{\sdstar}}{{\textsuperscript{{*}}\markSD{{}}}}
\AddToHook{{shipout/before}}{{\global\boolfalse{{hasSDonPage}}}}

\title{{\Large\textbf{{OsdagBridge}} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{{2cm}} \large Design Report}}
\author{{}}
\date{{}}

\begin{{document}}
"""
