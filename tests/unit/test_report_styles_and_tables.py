"""Tests for the report generator's style module, header-repeating tables and charts."""
import os

from osdagbridge.core.reports import styles, charts
from osdagbridge.core.reports.latex_utils import make_longtable, normalize_longtables

TABLE = (
    "\\begin{longtable}{|L{5cm}|p{9cm}|}\n"
    "\\caption{\\textbf{Dead Load {nested}}}\n"
    "\\hline\n\\textbf{parameter} & \\textbf{value} \\\\\n\\hline\n"
    "a & b \\\\[6pt]\n\\hline\n\\end{longtable}"
)


def test_header_is_repeated_and_caption_ordered():
    out, st = normalize_longtables(TABLE, return_stats=True)
    assert st == {"found": 1, "rewritten": 1, "skipped": 0}
    assert out.count("\\textbf{parameter}") == 2            # first page + continuation
    assert out.index("\\endfirsthead") < out.index("\\endhead") < out.index("\\endfoot")
    # caption comes before the header row, and is terminated with \\
    assert out.index("\\caption") < out.index("\\textbf{parameter}")
    assert "\\caption{\\textbf{Dead Load {nested}}}\\\\" in out


def test_normalizer_is_idempotent():
    once = normalize_longtables(TABLE)
    assert normalize_longtables(once) == once


def test_unrecognised_table_is_left_untouched():
    odd = "\\begin{longtable}{|l|}\nplain & data \\\\\n\\end{longtable}"
    out, st = normalize_longtables(odd, return_stats=True)
    assert out == odd and st["skipped"] == 1


def test_make_longtable_has_header_on_both_pages():
    t = make_longtable("|l|l|", ["A", "B"], [["1", "2"]], caption="Cap")
    assert t.count("\\textbf{A}") == 2 and "\\endlastfoot" in t


def test_preamble_comes_from_styles():
    pre = styles.preamble_tex("P", "J", "D", "V")
    assert "\\definecolor{osdagGreen}{HTML}{" + styles.PALETTE["osdagGreen"] + "}" in pre
    assert "footskip=" + styles.PAGE["footskip"] in pre
    assert "\\begin{document}" in pre


def test_ur_chart_written_and_handles_bad_data(tmp_path):
    items = [("Steel Plate Girders", "Moment", 0.8), ("Concrete Deck Slab", "Shear", 1.2),
             ("Cross Bracing", "Tension", "N.A.")]
    p = charts.ur_summary_chart(items, str(tmp_path / "ur.png"))
    assert p and os.path.getsize(p) > 1000
    assert charts.ur_summary_chart([("Cross Bracing", "x", "---")], str(tmp_path / "n.png")) is None


def test_quantity_charts_skip_missing_data(tmp_path):
    q = {"steel_girders_wt_total": "10.5", "concrete_deck_vol_total": "30", "rebar_deck_wt_total": "N.A."}
    assert charts.steel_quantity_chart(q, str(tmp_path / "s.png"))
    assert charts.concrete_rebar_chart(q, str(tmp_path / "c.png"))
    assert charts.steel_quantity_chart({"steel_girders_wt_total": "N.A."}, str(tmp_path / "x.png")) is None


def test_no_needspace_before_longtable():
    """needspace before longtable + repeating headers produced an orphan
    '(continued)' header and stray footer note; it must stay out of the preamble."""
    pre = styles.preamble_tex("P", "J", "D", "V")
    assert "BeforeBeginEnvironment{longtable}" not in pre
