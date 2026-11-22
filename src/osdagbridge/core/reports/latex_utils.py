"""
latex_utils.py -- helpers that make every multi-page table repeat its header.

Two entry points
----------------
make_longtable(...)          build a new table in the canonical, header-repeating form
normalize_longtables(tex)    upgrade every existing ``longtable`` in a finished
                             LaTeX string so the column header is repeated on each
                             page (\\endfirsthead / \\endhead / \\endfoot).

The normaliser is deliberately conservative.  An earlier attempt at automatic
post-processing mis-ordered captions and headings, so this parser

  * matches braces properly (captions/headers can contain nested ``{}``),
  * only rewrites a table when it recognises the exact shape
        \\begin{longtable}{spec} [\\caption{..}[\\\\]] \\hline <header row> \\hline
  * leaves a table untouched if it already defines \\endfirsthead/\\endhead or
    if anything unexpected is found (it never guesses),
  * returns statistics so callers/tests can see what was changed.
"""
import re
from . import styles

_UNESCAPED_AMP = re.compile(r"(?<!\\)&")


# ───────────────────────────── brace helpers ────────────────────────────────
def _match_brace(s, i):
    """s[i] must be '{'. Return index just past the matching '}' (or -1)."""
    if i >= len(s) or s[i] != "{":
        return -1
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == "\\":          # skip escaped char (\{ \} \\ ...)
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return -1


def _skip_ws(s, i):
    while i < len(s) and s[i] in " \t\r\n":
        i += 1
    return i


def _skip_comments_ws(s, i):
    """Skip whitespace and full-line % comments."""
    while True:
        i = _skip_ws(s, i)
        if i < len(s) and s[i] == "%":
            nl = s.find("\n", i)
            i = len(s) if nl < 0 else nl + 1
            continue
        return i


def _row_end(s, i):
    """From i, find the '\\\\' that ends the row at brace-depth 0.
    Returns (end_index_of_row_text, index_after_terminator, terminator_str)
    or None.  The terminator keeps an optional [..] spacing argument."""
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == "\\":
            if s.startswith("\\\\", j) and depth == 0:
                k = j + 2
                term = "\\\\"
                if k < len(s) and s[k] == "[":
                    close = s.find("]", k)
                    if close != -1:
                        term += s[k:close + 1]
                        k = close + 1
                return j, k, term
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        j += 1
    return None


# ───────────────────────────── canonical form ───────────────────────────────
def _ncols(header_row):
    return len(_UNESCAPED_AMP.findall(header_row)) + 1


def _canonical(colspec, caption, label, header_row, term, shade=True):
    """Return the opening part of a header-repeating longtable (everything up to
    and including \\endlastfoot).  The caller appends the body rows and
    \\end{longtable}."""
    n = _ncols(header_row)
    fill = styles.TABLE["header_fill"]
    head = (r"\rowcolor{" + fill + "} " if shade else "") + header_row.strip() + " " + term
    cont = styles.TABLE["continued_text"]
    foot = styles.TABLE["continued_footer"]
    cap = ""
    cap_cont = ""
    if caption is not None:
        cap = caption + (label or "") + "\\\\\n"
        cap_cont = (r"\multicolumn{" + str(n) + r"}{l}{\textit{\tablename\ \thetable\ " + cont + r"}}\\" + "\n")
    out = [r"\begin{longtable}{" + colspec + "}\n",
           cap,
           "\\hline\n", head, "\n\\hline\n",
           "\\endfirsthead\n",
           cap_cont,
           "\\hline\n", head, "\n\\hline\n",
           "\\endhead\n",
           r"\multicolumn{" + str(n) + r"}{r}{\footnotesize\textit{" + foot + r"}}\\" + "\n",
           "\\endfoot\n",
           "\\endlastfoot\n"]
    return "".join(out)


def make_longtable(colspec, header_cells, rows, caption=None, label=None,
                   row_term=r"\\[6pt]", shade=True):
    """Build a complete header-repeating longtable.

    colspec      e.g. ``"|L{5cm}|p{9cm}|"``
    header_cells list of header strings (will be wrapped in \\textbf{})
    rows         list of rows; each row is a list of cell strings (already
                 LaTeX-safe).  ``\\hline`` is added after every row.
    caption      plain LaTeX caption text, or None
    """
    header_row = " & ".join(r"\textbf{" + c + "}" for c in header_cells)
    cap = (r"\caption{\textbf{" + caption + "}}") if caption else None
    lab = (r"\label{" + label + "}") if label else ""
    body = "".join(" & ".join(r) + " " + row_term + "\n\\hline\n" for r in rows)
    return _canonical(colspec, cap, lab, header_row, r"\\[6pt]", shade) + body + "\\end{longtable}\n"


# ───────────────────────────── normaliser ───────────────────────────────────
_BEGIN = "\\begin{longtable}"
_END = "\\end{longtable}"


def _rewrite_one(block):
    """block = text from \\begin{longtable} through \\end{longtable}.
    Return rewritten block, or None to leave unchanged."""
    if "\\endfirsthead" in block or "\\endhead" in block:
        return None                                    # already handled
    i = len(_BEGIN)
    i = _skip_ws(block, i)
    e = _match_brace(block, i)
    if e < 0:
        return None
    colspec = block[i + 1:e - 1]
    i = _skip_comments_ws(block, e)

    caption = label = None
    if block.startswith("\\caption", i):
        j = i + len("\\caption")
        if j < len(block) and block[j] == "[":          # \caption[short]{long}
            close = block.find("]", j)
            if close < 0:
                return None
            j = close + 1
        ce = _match_brace(block, j)
        if ce < 0:
            return None
        caption = block[i:ce]
        i = _skip_comments_ws(block, ce)
        if block.startswith("\\\\", i):                   # optional \\ after caption
            i = _skip_comments_ws(block, i + 2)
            if i < len(block) and block[i] == "[":        # \\[..]
                close = block.find("]", i)
                i = _skip_comments_ws(block, close + 1)
        if block.startswith("\\label", i):
            le = _match_brace(block, i + len("\\label"))
            if le < 0:
                return None
            label = block[i:le]
            i = _skip_comments_ws(block, le)

    if not block.startswith("\\hline", i):
        return None
    i = _skip_comments_ws(block, i + len("\\hline"))

    row = _row_end(block, i)
    if row is None:
        return None
    r_end, after, term = row
    header_row = block[i:r_end]
    # must look like a header: bold cell(s) and no nested environments
    if "\\textbf" not in header_row and "\\bfseries" not in header_row:
        return None
    if "\\begin{" in header_row or "\\end{" in header_row:
        return None

    i = _skip_comments_ws(block, after)
    if not block.startswith("\\hline", i):
        return None
    rest = block[i + len("\\hline"):]                   # body rows + \end{longtable}
    # shading only if header does not already colour itself
    shade = "\\rowcolor" not in header_row
    return _canonical(colspec, caption, label, header_row, term, shade) + rest.lstrip("\n")


def normalize_longtables(tex, return_stats=False):
    """Make every longtable in `tex` repeat its header on each page."""
    out, pos = [], 0
    stats = {"found": 0, "rewritten": 0, "skipped": 0}
    while True:
        b = tex.find(_BEGIN, pos)
        if b < 0:
            out.append(tex[pos:])
            break
        e = tex.find(_END, b)
        if e < 0:
            out.append(tex[pos:])
            break
        e_end = e + len(_END)
        out.append(tex[pos:b])
        block = tex[b:e_end]
        stats["found"] += 1
        new = _rewrite_one(block)
        if new is None:
            out.append(block)
            stats["skipped"] += 1
        else:
            out.append(new)
            stats["rewritten"] += 1
        pos = e_end
    result = "".join(out)
    return (result, stats) if return_stats else result
