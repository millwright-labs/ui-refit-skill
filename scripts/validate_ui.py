"""validate_ui.py -- stdlib-only static UI/CSS validator.

Usage:
    python scripts/validate_ui.py <path> [<path>...]

Each <path> is a .css/.html file or a directory (directories recurse and
glob *.css / *.html; .html files contribute the concatenated contents of
their <style>...</style> blocks). Prints one line per finding:

    FAIL [check-id] <file> · <selector> — <detail>
    WARN [check-id] <file> · <selector> — <detail>

followed by a summary line:

    RESULT: <n> FAIL, <n> WARN, <n> files checked

Exit code is 1 iff at least one FAIL was found, else 0. If no checkable CSS
was found across all inputs, prints `ABSTAIN: no checkable CSS found` and
exits 0 (abstain is neither pass nor fail -- stated honestly, never silent).

Checks (see docs/superpowers/specs/2026-08-19-ui-refit-skill-design.md
"Validator design" for the full table): contrast, transition-all,
layout-anim, focus-visible (all FAIL); reduced-motion, spacing-grid,
type-scale, cliche-color, parse (all WARN).

Parser behavior:
    - `@charset ...;` and `@import ...;` statements are stripped before
      block splitting (neither has a `{...}` body, so left in place they
      derail the following block's prelude/body split).
    - `@media` blocks are flattened up to two levels deep (@media nested
      inside @media), in addition to the plain one-level case.
    - If brace depth never returns to zero (malformed/truncated CSS), a
      `parse` WARN is emitted instead of silently reporting a clean result;
      recoverable declarations before the imbalance are still checked.

Font-size units: `px` is read directly; `rem`/`em` are converted to px
using a documented, fixed 16px root-font-size assumption (no actual
cascade/rem-root tracking); `pt` uses the fixed CSS conversion of
1pt = 4/3px. This only feeds the contrast check's large-text (>=24px or
>=18.66px-and-bold) 3:1 threshold.

Cliche-color rule: a color is flagged when its Euclidean RGB distance to a
known AI-default (see references/anti-defaults.md) is strictly less than
16 (cream matches additionally require a warm bias). Gradient values are
otherwise skipped by color parsing (not a single color), but are scanned
for this check specifically: every #hex stop inside a gradient value is
extracted and checked individually.

Out of scope (documented here, not silently guessed at):
    - computed-style cascade (only single-rule declarations are resolved,
      not full specificity/inheritance across the whole stylesheet)
    - layout-dependent checks such as touch target size
    - cross-file/cross-selector custom-property chains beyond one level
    - CSS-in-JS (template literals, styled-components, etc.)
    - inline style="" attributes on HTML elements
"""

import math
import re
import sys
from collections import namedtuple
from pathlib import Path

Finding = namedtuple("Finding", "severity check_id where detail")

# ---------------------------------------------------------------------------
# Named color subset (CSS Level 1/2 basics only -- out-of-scope names are
# simply unparsable and silently skipped, per the contrast check's rules).
# ---------------------------------------------------------------------------
NAMED_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "silver": (192, 192, 192),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "purple": (128, 0, 128),
    "navy": (0, 0, 128),
    "teal": (0, 128, 128),
}

# Reviewed: 2026-08-19 — mirror of references/anti-defaults.md
# Cream entries additionally require a warm bias (r >= g >= b, r-b >= 6):
# the cliché is the WARM off-white; cool/green-tinted papers within the same
# Euclidean radius are not it, and flagging them makes the check noise.
CLICHE_CREAMS = [
    "#F4F1EA",  # AI-default cream
    "#F5F1EA",  # AI-default cream (near-duplicate)
]
CLICHE_PURPLES = [
    "#8B5CF6",  # AI-default purple/violet gradient family
    "#7C3AED",
    "#6366F1",
    "#A855F7",
]
CLICHE_COLORS = CLICHE_CREAMS + CLICHE_PURPLES

LAYOUT_PROPS = {"top", "left", "right", "bottom", "width", "height"}
TRANSITION_PROPS = {"transition", "transition-property"}
CLICHE_SCAN_PROPS = {
    "color", "background", "background-color", "border", "border-color",
    "outline-color", "box-shadow", "fill", "stroke",
}

COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
AT_MEDIA_RE = re.compile(r"^@media\b", re.IGNORECASE)
AT_KEYFRAMES_RE = re.compile(r"^@(-\w+-)?keyframes\b", re.IGNORECASE)
AT_IMPORT_CHARSET_RE = re.compile(r"@(?:charset|import)\b[^;]*;", re.IGNORECASE)
VAR_RE = re.compile(r"^var\(\s*(--[\w-]+)\s*(?:,\s*(.*))?\)$", re.IGNORECASE)
OUTLINE_NONE_RE = re.compile(r"^(none|0)(\s*!important)?$", re.IGNORECASE)
SPACING_PROP_RE = re.compile(r"^(margin|padding)(-[\w-]+)?$|^(gap|row-gap|column-gap)$")
PX_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*px", re.IGNORECASE)
FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([\d.]+)\s*px", re.IGNORECASE)
FONT_SIZE_UNIT_RE = re.compile(r"^([\d.]+)\s*(px|rem|em|pt)$", re.IGNORECASE)
ANIM_DECL_RE = re.compile(r"\b(animation|transition)(-[\w-]+)?\s*:", re.IGNORECASE)
STYLE_BLOCK_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
GRADIENT_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")


# ---------------------------------------------------------------------------
# Color parsing
# ---------------------------------------------------------------------------

def parse_color(value):
    """Parse a single color token -> (r, g, b, a) or None if unparsable.

    Only hex (#rgb/#rrggbb/#rrggbbaa), rgb()/rgba(), the small named-color
    subset, and 'transparent' are supported. Gradients and url() are never
    valid single colors and return None.
    """
    v = (value or "").strip()
    if not v:
        return None
    low = v.lower()
    if "gradient" in low or "url(" in low:
        return None
    if low == "transparent":
        return (0, 0, 0, 0.0)
    if low in NAMED_COLORS:
        r, g, b = NAMED_COLORS[low]
        return (r, g, b, 1.0)

    m = re.fullmatch(r"#([0-9a-fA-F]{3})", v)
    if m:
        h = m.group(1)
        r, g, b = (int(c * 2, 16) for c in h)
        return (r, g, b, 1.0)

    m = re.fullmatch(r"#([0-9a-fA-F]{6})", v)
    if m:
        h = m.group(1)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r, g, b, 1.0)

    m = re.fullmatch(r"#([0-9a-fA-F]{8})", v)
    if m:
        h = m.group(1)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        a = int(h[6:8], 16) / 255.0
        return (r, g, b, a)

    m = re.fullmatch(
        r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)",
        v,
        re.IGNORECASE,
    )
    if m:
        r, g, b = float(m.group(1)), float(m.group(2)), float(m.group(3))
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        return (r, g, b, a)

    return None


CLICHE_CREAM_RGB = [parse_color(h)[:3] for h in CLICHE_CREAMS]
CLICHE_PURPLE_RGB = [parse_color(h)[:3] for h in CLICHE_PURPLES]


def _is_warm_offwhite(rgb):
    r, g, b = rgb
    return r >= g >= b and (r - b) >= 6


def _matches_cliche(rgb):
    for cref in CLICHE_PURPLE_RGB:
        if _euclid(rgb, cref) < 16:
            return True
    if _is_warm_offwhite(rgb):
        for cref in CLICHE_CREAM_RGB:
            if _euclid(rgb, cref) < 16:
                return True
    return False


def extract_any_color(value):
    """Like parse_color, but also digs a color out of a compound value such
    as `1px solid #8B5CF6` or `0 4px 6px rgba(0,0,0,.2)`. Returns None for
    gradients/url()/unparsable values (skipped silently)."""
    v = (value or "").strip()
    c = parse_color(v)
    if c is not None:
        return c
    low = v.lower()
    if "gradient" in low or "url(" in low:
        return None
    m = re.search(r"#[0-9a-fA-F]{3,8}\b", v)
    if m:
        return parse_color(m.group(0))
    m = re.search(r"rgba?\([^)]*\)", v, re.IGNORECASE)
    if m:
        return parse_color(m.group(0))
    for name in NAMED_COLORS:
        if re.search(r"\b" + name + r"\b", low):
            return parse_color(name)
    return None


def _euclid(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ---------------------------------------------------------------------------
# WCAG contrast
# ---------------------------------------------------------------------------

def relative_luminance(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(rgb_a, rgb_b):
    la = relative_luminance(rgb_a)
    lb = relative_luminance(rgb_b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# CSS parsing: brace-depth block splitter. @keyframes needs one level of
# nesting (stops); @media is flattened up to two levels (@media in @media)
# via _flatten_media_body below.
# ---------------------------------------------------------------------------

def _strip_comments(text):
    return COMMENT_RE.sub("", text)


def _split_blocks(text):
    """Split text into (prelude, body) pairs for each top-level {...} block,
    where body is the raw text between the matching braces (brace-depth
    aware, so nested braces inside body don't terminate the block early).

    Returns (blocks, unbalanced): unbalanced is True if any block's opening
    brace never found its matching close before the end of input."""
    blocks = []
    unbalanced = False
    n = len(text)
    i = 0
    start = 0
    while i < n:
        c = text[i]
        if c == "{":
            prelude = text[start:i].strip()
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1
            if depth != 0:
                unbalanced = True
            body = text[i + 1:j - 1] if depth == 0 else text[i + 1:j]
            blocks.append((prelude, body))
            i = j
            start = j
        else:
            i += 1
    return blocks, unbalanced


def _parse_decls(body):
    decls = []
    for part in body.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        prop, _, val = part.partition(":")
        prop = prop.strip()
        # Custom-property names are case-sensitive in CSS (--FG != --fg);
        # every other property name is matched case-insensitively, so it's
        # safe (and required, for the checks below) to lowercase those.
        if not prop.startswith("--"):
            prop = prop.lower()
        val = val.strip()
        if prop and val:
            decls.append((prop, val))
    return decls


def _is_root_scope(selector):
    for part in selector.split(","):
        p = part.strip().lower()
        if p in (":root", "html", "body"):
            return True
        if "data-theme" in p:
            return True
    return False


def _maybe_collect_custom_props(selector, decls, custom_props):
    if not _is_root_scope(selector):
        return
    for prop, val in decls:
        if prop.startswith("--"):
            custom_props.setdefault(prop, []).append(val)


def _flatten_media_body(body, custom_props, rules, remaining_depth):
    """Walk the body of an @media block, adding ordinary selector blocks to
    `rules` and recursing into a further-nested @media block (up to
    `remaining_depth` extra levels -- @media within @media). Returns True if
    any brace imbalance was found within this body."""
    blocks, unbalanced = _split_blocks(body)
    for sel, sbody in blocks:
        if not sel:
            continue
        if AT_MEDIA_RE.match(sel):
            if remaining_depth > 0:
                nested_unbalanced = _flatten_media_body(
                    sbody, custom_props, rules, remaining_depth - 1
                )
                unbalanced = unbalanced or nested_unbalanced
            continue
        if sel.startswith("@"):
            continue
        decls = _parse_decls(sbody)
        rules.append({"selector": sel, "decls": decls})
        _maybe_collect_custom_props(sel, decls, custom_props)
    return unbalanced


def parse_css(text):
    """Parse comment-stripped CSS text.

    Returns (rules, custom_props, keyframe_props, unbalanced):
      - rules: list of {'selector': str, 'decls': [(prop, val), ...]} for
        every ordinary selector block, including those nested up to two
        levels under @media (@media within @media -- keyframe stops are NOT
        included here -- no contrast/spacing/etc. checks run inside
        @keyframes).
      - custom_props: dict of `--name` -> list of raw value strings seen in
        :root/html/body/[data-theme...] blocks (for one-level var()
        resolution; multiple different values means "ambiguous"). Custom
        property names keep their original case (CSS custom properties are
        case-sensitive); every other property name is lowercased.
      - keyframe_props: list of (keyframes_prelude, set_of_declared_props)
        for each @keyframes block, used only by the layout-anim check.
      - unbalanced: True if brace depth never returned to zero somewhere in
        the input (malformed CSS) -- callers surface this as a WARN rather
        than silently reporting a clean result.

    `@charset ...;` and `@import ...;` statements are stripped before block
    splitting -- neither has a `{...}` body, so left in place they would
    derail the very next block's prelude/body split.
    """
    text = AT_IMPORT_CHARSET_RE.sub("", text)

    rules = []
    custom_props = {}
    keyframe_props = []

    top_blocks, unbalanced = _split_blocks(text)

    for prelude, body in top_blocks:
        if not prelude:
            continue
        if AT_KEYFRAMES_RE.match(prelude):
            props_seen = set()
            stop_blocks, stop_unbalanced = _split_blocks(body)
            unbalanced = unbalanced or stop_unbalanced
            for _stop_sel, stop_body in stop_blocks:
                for prop, _val in _parse_decls(stop_body):
                    props_seen.add(prop)
            keyframe_props.append((prelude, props_seen))
            continue
        if AT_MEDIA_RE.match(prelude):
            media_unbalanced = _flatten_media_body(body, custom_props, rules, 1)
            unbalanced = unbalanced or media_unbalanced
            continue
        if prelude.startswith("@"):
            # Other at-rules (@font-face, @supports, @page, ...) are out of
            # scope -- skip rather than misparse their body as a selector.
            continue
        decls = _parse_decls(body)
        rules.append({"selector": prelude, "decls": decls})
        _maybe_collect_custom_props(prelude, decls, custom_props)

    return rules, custom_props, keyframe_props, unbalanced


def _resolve(value, custom_props):
    """Resolve a single var(--x[, fallback]) reference one level deep.
    Returns the resolved literal string, or None if it should be skipped
    (ambiguous custom prop, or unresolvable var with no fallback)."""
    v = value.strip()
    m = VAR_RE.match(v)
    if not m:
        return v
    name, fallback = m.group(1), m.group(2)
    vals = custom_props.get(name)
    if vals:
        uniq = {x.strip() for x in vals}
        if len(uniq) == 1:
            return next(iter(uniq))
        return None  # conflicting definitions -> ambiguous, skip
    if fallback is not None:
        return fallback.strip()
    return None


def _fmt_num(v):
    return str(int(v)) if v == int(v) else str(v)


# ---------------------------------------------------------------------------
# Individual checks (each takes already-parsed data, returns list[Finding])
# ---------------------------------------------------------------------------

def _font_size_to_px(value):
    """Convert a single font-size value to px, or None if unparsable/not a
    recognized unit. rem/em use a documented 16px root-font-size assumption
    (no cascade tracking); pt uses the fixed 1pt = 4/3px CSS conversion."""
    m = FONT_SIZE_UNIT_RE.match((value or "").strip())
    if not m:
        return None
    num = float(m.group(1))
    unit = m.group(2).lower()
    if unit == "px":
        return num
    if unit in ("rem", "em"):
        return num * 16.0
    if unit == "pt":
        return num * (4.0 / 3.0)
    return None


def _contrast_threshold(decls):
    threshold = 4.5
    bold = False
    fw = decls.get("font-weight")
    if fw:
        fw_s = fw.strip().lower()
        if fw_s == "bold":
            bold = True
        else:
            try:
                if float(fw_s) >= 700:
                    bold = True
            except ValueError:
                pass
    fs = decls.get("font-size")
    if fs:
        px = _font_size_to_px(fs)
        if px is not None:
            if px >= 24:
                threshold = 3.0
            elif px >= 18.66 and bold:
                threshold = 3.0
    return threshold


def _check_contrast(rule, custom_props):
    decls = dict(rule["decls"])
    if "color" not in decls:
        return []

    # Later declaration wins in CSS: among background/background-color in
    # this rule, the effective background is the LAST one written, not
    # whichever of the two names happens to be more specific. If that last
    # declaration's value doesn't parse to a color (e.g. a gradient), the
    # pair is unresolvable -- skip rather than falling back to an earlier
    # declaration, which would misreport the actual effective background.
    bg_decls = [(p, v) for p, v in rule["decls"] if p in ("background", "background-color")]
    if not bg_decls:
        return []
    bg_prop, bg_val = bg_decls[-1]

    color_raw = _resolve(decls["color"], custom_props)
    bg_raw = _resolve(bg_val, custom_props)
    if color_raw is None or bg_raw is None:
        return []
    if "gradient" in bg_raw.lower() or "url(" in bg_raw.lower():
        return []

    c1 = parse_color(color_raw)
    c2 = parse_color(bg_raw)
    if c1 is None or c2 is None:
        return []
    if c1[3] < 1 or c2[3] < 1:
        return []

    ratio = contrast_ratio(c1[:3], c2[:3])
    threshold = _contrast_threshold(decls)
    if ratio < threshold:
        detail = (
            f"color {decls['color']} on {bg_prop}:{bg_val} "
            f"= {ratio:.2f}:1, needs {threshold}:1"
        )
        return [Finding("FAIL", "contrast", rule["selector"], detail)]
    return []


def _check_transition(rule):
    findings = []
    for prop, val in rule["decls"]:
        if prop not in TRANSITION_PROPS:
            continue
        if re.search(r"\ball\b", val, re.IGNORECASE):
            findings.append(
                Finding("FAIL", "transition-all", rule["selector"], f"{prop}: {val}")
            )
        offending = set()
        for part in val.split(","):
            tokens = part.strip().split()
            if tokens and tokens[0].lower() in LAYOUT_PROPS:
                offending.add(tokens[0].lower())
        if offending:
            findings.append(
                Finding(
                    "FAIL",
                    "layout-anim",
                    rule["selector"],
                    f"{prop} animates layout property: {', '.join(sorted(offending))}",
                )
            )
    return findings


def _check_keyframe_layout_anim(keyframe_props):
    findings = []
    for kf_selector, props in keyframe_props:
        offending = props & LAYOUT_PROPS
        if offending:
            findings.append(
                Finding(
                    "FAIL",
                    "layout-anim",
                    kf_selector,
                    f"@keyframes animates layout property: {', '.join(sorted(offending))}",
                )
            )
    return findings


def _has_visible_focus_indicator(decls):
    """True if decls declares an outline that isn't none/0, or a box-shadow
    that isn't none -- i.e. an actually-visible focus replacement, not just
    the presence of a :focus/:focus-visible rule (which might itself say
    outline:none, suppressing the removed-outline FAIL for nothing)."""
    outline_val = decls.get("outline", "").strip()
    if outline_val and not OUTLINE_NONE_RE.match(outline_val):
        return True
    box_shadow_val = decls.get("box-shadow", "").strip()
    if box_shadow_val and box_shadow_val.lower() != "none":
        return True
    return False


def _check_focus_visible(rules):
    offending = []
    safety_net = False
    for rule in rules:
        sel_low = rule["selector"].lower()
        decls = dict(rule["decls"])
        if "outline" in decls and OUTLINE_NONE_RE.match(decls["outline"].strip()):
            offending.append(rule["selector"])
        if ":focus-visible" in sel_low or ":focus" in sel_low:
            if _has_visible_focus_indicator(decls):
                safety_net = True
    if offending and not safety_net:
        return [
            Finding(
                "FAIL",
                "focus-visible",
                sel,
                "outline removed with no :focus-visible/:focus alternative in scope",
            )
            for sel in offending
        ]
    return []


def _check_reduced_motion(text):
    if ANIM_DECL_RE.search(text) and "prefers-reduced-motion" not in text.lower():
        return [
            Finding(
                "WARN",
                "reduced-motion",
                "(file)",
                "animation/transition present without a prefers-reduced-motion guard",
            )
        ]
    return []


def _check_spacing(rules):
    offenders = set()
    for rule in rules:
        for prop, val in rule["decls"]:
            if not SPACING_PROP_RE.match(prop):
                continue
            for m in PX_RE.finditer(val):
                v = float(m.group(1))
                if v > 2 and v % 4 != 0:
                    offenders.add(_fmt_num(v))
    if offenders:
        vals = ", ".join(sorted(offenders, key=float))
        return [
            Finding(
                "WARN",
                "spacing-grid",
                "(file)",
                f"off-grid spacing values (not multiples of 4px): {vals}px",
            )
        ]
    return []


def _collect_font_sizes(text):
    return set(m.group(1) for m in FONT_SIZE_RE.finditer(text))


def _check_type_scale(text):
    sizes = _collect_font_sizes(text)
    if len(sizes) > 8:
        return [
            Finding(
                "WARN",
                "type-scale",
                "(global)",
                f"{len(sizes)} distinct font-size values in scope (>8) -- consolidate onto a type scale",
            )
        ]
    return []


def _check_cliche_color(rules):
    findings = []
    seen = set()
    for rule in rules:
        for prop, val in rule["decls"]:
            # custom properties count too: token-based sheets define their
            # whole palette in --vars, which would otherwise evade this scan
            if prop not in CLICHE_SCAN_PROPS and not prop.startswith("--"):
                continue

            colors = []
            if "gradient" in val.lower():
                # Regular color parsing skips gradients entirely (they're
                # not a single color), but the purple-gradient-hero cliche
                # lives exactly here -- pull every #hex stop out and check
                # each one individually instead of the whole value.
                for m in GRADIENT_HEX_RE.finditer(val):
                    c = parse_color(m.group(0))
                    if c is not None:
                        colors.append(c)
            else:
                c = extract_any_color(val)
                if c is not None:
                    colors.append(c)

            for r, g, b, a in colors:
                if a < 1:
                    continue
                if _matches_cliche((r, g, b)):
                    key = (rule["selector"], prop, val)
                    if key not in seen:
                        seen.add(key)
                        findings.append(
                            Finding(
                                "WARN",
                                "cliche-color",
                                rule["selector"],
                                f"{prop}: {val} is close to a common AI-default color "
                                "(see references/anti-defaults.md) -- fine if deliberately chosen",
                            )
                        )
                    break
    return findings


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def validate_text(text, name):
    """Run all checks over a single blob of CSS text (already extracted
    from a .css file or an .html file's <style> blocks). `name` identifies
    the source for callers that want to attribute findings to a file; it is
    not embedded in Finding.where (which is always the selector, or the
    fixed "(file)"/"(global)" markers for file-/scope-level checks)."""
    del name  # not needed for finding construction; kept for API clarity
    findings = []
    stripped = _strip_comments(text)
    rules, custom_props, keyframe_props, unbalanced = parse_css(stripped)

    if unbalanced:
        findings.append(
            Finding(
                "WARN",
                "parse",
                "(file)",
                "unbalanced braces; results may be incomplete",
            )
        )

    for rule in rules:
        findings.extend(_check_contrast(rule, custom_props))
    for rule in rules:
        findings.extend(_check_transition(rule))
    findings.extend(_check_keyframe_layout_anim(keyframe_props))
    findings.extend(_check_focus_visible(rules))
    findings.extend(_check_reduced_motion(stripped))
    findings.extend(_check_spacing(rules))
    findings.extend(_check_type_scale(stripped))
    findings.extend(_check_cliche_color(rules))

    return findings


def _has_checkable_css(text):
    stripped = _strip_comments(text)
    rules, _custom_props, keyframe_props, _unbalanced = parse_css(stripped)
    return bool(rules) or bool(keyframe_props)


def _iter_target_files(paths):
    files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.css")))
            files.extend(sorted(path.rglob("*.html")))
        elif path.is_file():
            files.append(path)
        # nonexistent paths are silently skipped
    return files


def _extract_text_for_file(path):
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if path.suffix.lower() == ".html":
        return "\n".join(m.group(1) for m in STYLE_BLOCK_RE.finditer(raw))
    return raw


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if not argv:
        print("usage: validate_ui.py <path> [<path>...]")
        return 1

    files = _iter_target_files(argv)
    texts = []
    for f in files:
        text = _extract_text_for_file(f)
        if text.strip():
            texts.append((f, text))

    if not texts:
        print("ABSTAIN: no checkable CSS found")
        return 0

    any_checkable = any(_has_checkable_css(text) for _f, text in texts)
    if not any_checkable:
        print("ABSTAIN: no checkable CSS found")
        return 0

    all_sizes = set()
    per_file_findings = []
    for f, text in texts:
        stripped = _strip_comments(text)
        all_sizes |= _collect_font_sizes(stripped)
        findings = [fnd for fnd in validate_text(text, str(f)) if fnd.check_id != "type-scale"]
        per_file_findings.append((f, findings))

    global_findings = []
    if len(all_sizes) > 8:
        global_findings.append(
            Finding(
                "WARN",
                "type-scale",
                "(global)",
                f"{len(all_sizes)} distinct font-size values across scanned files (>8) "
                "-- consolidate onto a type scale",
            )
        )

    fail_count = 0
    warn_count = 0
    for f, findings in per_file_findings:
        for fnd in findings:
            print(f"{fnd.severity} [{fnd.check_id}] {f} · {fnd.where} — {fnd.detail}")
            if fnd.severity == "FAIL":
                fail_count += 1
            else:
                warn_count += 1
    for fnd in global_findings:
        print(f"{fnd.severity} [{fnd.check_id}] (all files) · {fnd.where} — {fnd.detail}")
        warn_count += 1

    print(f"RESULT: {fail_count} FAIL, {warn_count} WARN, {len(texts)} files checked")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
