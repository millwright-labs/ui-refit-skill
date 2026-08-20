import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Make `import validate_ui` work no matter what directory this is run from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validate_ui as v

REPO_ROOT = Path(__file__).resolve().parent.parent


def run(css: str):
    return v.validate_text(css, "test.css")  # returns list of Finding(severity, check_id, where, detail)


def ids(findings, sev=None):
    return [f.check_id for f in findings if sev is None or f.severity == sev]


# contrast
assert "contrast" in ids(run(".a{color:#777;background:#888;}"), "FAIL")
assert "contrast" not in ids(run(".a{color:#111;background:#fff;}"))
# var resolution, one level
assert "contrast" in ids(run(":root{--fg:#777;--bg:#888;} .a{color:var(--fg);background:var(--bg);}"), "FAIL")
# large text threshold: #8A8A8A on #fff ~= 3.45:1 -> passes at >=24px, FAILs at body size
assert "contrast" not in ids(run(".h{color:#8A8A8A;background:#fff;font-size:32px;}"), "FAIL")
assert "contrast" in ids(run(".p{color:#8A8A8A;background:#fff;}"), "FAIL")
# alpha -> skip (no finding either way)
assert "contrast" not in ids(run(".a{color:rgba(0,0,0,.5);background:#fff;}"))
# transition-all
assert "transition-all" in ids(run(".a{transition: all .2s;}"), "FAIL")
assert "transition-all" not in ids(run(".a{transition: opacity .2s, transform .2s;}"))
# layout-anim
assert "layout-anim" in ids(run(".a{transition: width .3s;}"), "FAIL")
assert "layout-anim" not in ids(run(".a{transition: min-width .3s;}"))  # control: word boundary
assert "layout-anim" in ids(run("@keyframes slide{from{left:0}to{left:100px}}"), "FAIL")
# focus-visible
assert "focus-visible" in ids(run("button{outline:none;}"), "FAIL")
assert "focus-visible" not in ids(run("button{outline:none;} button:focus-visible{outline:2px solid #000;}"))
# reduced-motion
assert "reduced-motion" in ids(run(".a{animation: spin 1s linear infinite;}"), "WARN")
assert "reduced-motion" not in ids(run(".a{animation: spin 1s;} @media (prefers-reduced-motion: reduce){.a{animation:none;}}"))
# spacing-grid
assert "spacing-grid" in ids(run(".a{padding: 13px;}"), "WARN")
assert "spacing-grid" not in ids(run(".a{padding: 16px 8px; margin: 2px;}"))
# type-scale: 9 distinct sizes fires, 3 doesn't
many = "".join(f".s{i}{{font-size:{10+i}px;}}" for i in range(9))
assert "type-scale" in ids(run(many), "WARN")
assert "type-scale" not in ids(run(".a{font-size:16px;}.b{font-size:20px;}"))
# cliche-color
assert "cliche-color" in ids(run(".hero{background:#8B5CF6;}"), "WARN")
assert "cliche-color" not in ids(run(".hero{background:#0E6B5C;}"))
# abstain: unparsable/no css
assert v.validate_text("<p>no styles here</p>", "x.html") == []

# --- additional control/edge cases (kept as a superset of the plan's contract) ---
# contrast: high-weight large-ish text also gets the relaxed 3.0 threshold
assert "contrast" not in ids(run(".h{color:#8A8A8A;background:#fff;font-size:19px;font-weight:700;}"), "FAIL")
assert "contrast" in ids(run(".h{color:#8A8A8A;background:#fff;font-size:19px;font-weight:400;}"), "FAIL")
# contrast: background-color takes precedence and is checked the same way
assert "contrast" in ids(run(".a{color:#777;background-color:#888;}"), "FAIL")
# contrast: gradients/url() backgrounds are skipped silently
assert "contrast" not in ids(run(".a{color:#111;background:linear-gradient(#fff,#000);}"))
# contrast: ambiguous (conflicting) custom prop definitions -> skip the pair
assert "contrast" not in ids(
    run(":root{--fg:#777;} [data-theme='dark']{--fg:#eee;} .a{color:var(--fg);background:#888;}")
)
# transition-property (not just transition shorthand) is also checked
assert "transition-all" in ids(run(".a{transition-property: all;}"), "FAIL")
# layout-anim: unrelated transition properties don't fire
assert "layout-anim" not in ids(run(".a{transition: opacity .2s, color .2s;}"))
# focus-visible: box-shadow on :focus counts as an alternative
assert "focus-visible" not in ids(
    run("button{outline:none;} button:focus{box-shadow: 0 0 0 2px #000;}")
)
# spacing-grid: gap/row-gap/column-gap are scanned too
assert "spacing-grid" in ids(run(".a{gap: 7px;}"), "WARN")
# cliche-color: near-miss within Euclidean distance 16 still fires
assert "cliche-color" in ids(run(".a{color:#8A5DF5;}"), "WARN")

# --- review-fix regression tests ---

# fix 1: custom-property case sensitivity (--FG != --fg)
assert "contrast" in ids(
    run(":root{--FG:#777;--BG:#888;} .a{color:var(--FG);background:var(--BG);}"), "FAIL"
)  # fire: uppercase names must not be silently lowercased away from their usage
assert "contrast" in ids(
    run(":root{--Fg:#777;--Bg:#888;} .a{color:var(--Fg);background:var(--Bg);}"), "FAIL"
)  # control: mixed-case defined/used consistently still resolves
assert "contrast" not in ids(
    run(":root{--FG:#777;} .a{color:var(--fg);background:#888;}")
)  # control: var(--fg) with only --FG defined is unresolvable -> skip, no finding

# fix 2: background vs background-color -- later declaration wins
assert "contrast" in ids(
    run(".a{background-color:#fff;background:#888;color:#777}"), "FAIL"
)  # fire: background written last -> effective bg is #888
assert "contrast" not in ids(
    run(".a{background:#888;background-color:#fff;color:#111}")
)  # control: background-color written last -> effective bg is #fff

# fix 3: font-size units beyond px for the large-text 3:1 threshold
assert "contrast" not in ids(
    run(".h{color:#8A8A8A;background:#fff;font-size:2rem;}"), "FAIL"
)  # control: 2rem = 32px @ 16px base -> large-text threshold applies, passes
assert "contrast" in ids(
    run(".h{color:#8A8A8A;background:#fff;font-size:1rem;}"), "FAIL"
)  # fire: 1rem = 16px -> body-size threshold (4.5:1), fails

# fix 4: focus-visible replacement must itself be visible
assert "focus-visible" in ids(
    run("button{outline:none;} button:focus-visible{outline:none;}"), "FAIL"
)  # fire: the "safety net" rule also removes the outline -- not a real replacement
assert "focus-visible" not in ids(
    run("button{outline:none;} button:focus{outline:2px solid #000;}")
)  # control: :focus (not just :focus-visible) with a real outline still counts

# fix 5a: @charset / @import statements are stripped, not misparsed
assert "transition-all" in ids(
    run("@import url(x.css); .a{transition:all .2s}"), "FAIL"
)  # fire: leading @import must not derail parsing of the following rule
assert run('@charset "UTF-8"; .a{color:#111;background:#fff}') == []
# control: @charset + a clean rule -> no findings at all (no parse WARN, no misparse)

# fix 5b: @media nested one level deeper (media within media) is flattened
assert "transition-all" in ids(
    run("@media screen{@media (min-width:600px){.a{transition:all .2s}}}"), "FAIL"
)  # fire: doubly-nested @media rule must still be checked
assert run(
    "@media screen{@media (min-width:600px){.a{color:#111;background:#fff;}}}"
) == []  # control: doubly-nested @media with passing colors -> no findings

# fix 5c: unbalanced braces surface a parse WARN instead of a silent clean pass
assert "parse" in ids(run(".a{color:#777;background:#888"), "WARN")
# fire: unclosed rule
assert "parse" not in ids(run(".a{color:#111;background:#fff;}"))
# control: balanced input never gets the parse WARN

# fix 6: gradient stops join the cliche-color scan
assert "cliche-color" in ids(
    run(".hero{background:linear-gradient(135deg,#8B5CF6,#6366F1);}"), "WARN"
)  # fire: the exact purple-gradient-hero cliche
assert "cliche-color" not in ids(
    run(".hero{background:linear-gradient(#1E6B41,#165231);}")
)  # control: an unrelated green gradient must not fire

# CLI exit codes via subprocess on temp files
with tempfile.TemporaryDirectory() as d:
    bad = Path(d, "bad.css")
    bad.write_text(".a{transition:all .2s}", encoding="utf-8")
    ok = Path(d, "ok.css")
    ok.write_text(".a{color:#111;background:#fff}", encoding="utf-8")
    assert subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_ui.py"), str(bad)]
    ).returncode == 1
    assert subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_ui.py"), str(ok)]
    ).returncode == 0
    # ABSTAIN: a directory with no .css/.html in it
    assert subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_ui.py"), d + "_does_not_exist"]
    ).returncode == 0

# cliche-color also scans custom-property definitions (token sheets)
assert "cliche-color" in ids(run(":root{--hero:#8B5CF6;}"), "WARN")
assert "cliche-color" not in ids(run(":root{--brand:#0E6B5C;}"))

# warm-bias gate: cool/green off-whites near cream are NOT the cliche
assert "cliche-color" in ids(run(".hero{background:#F4F1EA;}"), "WARN")
assert "cliche-color" not in ids(run(":root{--bg:#F7F7F5;}"))
assert "cliche-color" not in ids(run(":root{--ink:#F2F4F8;}"))
assert "cliche-color" not in ids(run(":root{--paper:#F2F5EC;}"))

# Every assert in this file has run by this point -- print the single
# success line last, not before earlier sections' asserts had a chance to
# fail (previously this printed right after the CLI subprocess block, with
# more asserts still to come below it).
print("all validator tests passed")
