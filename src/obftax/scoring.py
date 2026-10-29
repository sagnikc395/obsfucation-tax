"""Scoring, and the sandbox the program tracks need.

The mbpp and humaneval tracks EXECUTE MODEL-GENERATED CODE in a subprocess with CPU,
memory and wall-clock limits. Adequate on a disposable VM. Run them nowhere you care
about.
"""

import ast
import os
import subprocess
import sys
import tempfile

from .config import EXEC_MEM_MB, EXEC_TIMEOUT


def extract_code(text):
    """Strip a markdown fence if the model added one despite being told not to."""
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            first, _, rest = parts[1].partition("\n")
            return (rest if first.strip().lower() in ("python", "py", "") else parts[1]).strip()
    return text.strip()


def score_literal(answer, expected):
    """Compare parsed Python values, so `[1, 2]` and `[1,2]` agree."""
    a = extract_code(answer)
    a = next((ln for ln in a.split("\n") if ln.strip()), "").strip()
    a = a.strip("`").removeprefix("assert").strip().split("#")[0].strip()
    try:
        return ast.literal_eval(a) == ast.literal_eval(expected)
    except Exception:
        return a == expected.strip()


# The child sets its own rlimits. preexec_fn is not portable (it raises on macOS) and the
# failure mode there is every program scoring False, which is indistinguishable from a
# model that cannot code. A silently-zero score is worse than a crash.
LIMIT_PREAMBLE = "\n".join([
    "import resource as _r",
    "for _lim, _v in (('RLIMIT_CPU', ({cpu}, {cpu})), ('RLIMIT_AS', ({mem}, {mem}))):",
    "    try:",
    "        _r.setrlimit(getattr(_r, _lim), _v)",
    "    except Exception:",
    "        pass",
    "del _r",
    "",
])


def run_program(src, timeout=EXEC_TIMEOUT, mem_mb=EXEC_MEM_MB):
    """Run untrusted model output. Returns (passed, short_stderr)."""
    prog = LIMIT_PREAMBLE.format(cpu=timeout, mem=mem_mb * 1024 * 1024) + "\n" + src
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "prog.py"), "w") as f:
            f.write(prog)
        try:
            r = subprocess.run([sys.executable, "-I", "prog.py"], cwd=d, timeout=timeout + 2,
                               capture_output=True, text=True)
            return r.returncode == 0, (r.stderr or "").strip()[-300:]
        except subprocess.TimeoutExpired:
            return False, "timeout"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


def score(problem, raw_answer):
    """Returns (correct, syntax_ok, detail)."""
    if problem["kind"] == "literal":
        return bool(score_literal(raw_answer, problem["expected"])), True, ""
    code_str = extract_code(raw_answer)
    try:
        compile(code_str, "<cand>", "exec")
    except SyntaxError as e:
        return False, False, f"SyntaxError: {e}"
    src = "\n\n".join(x for x in [problem.get("prefix", ""), code_str, problem["test_src"]] if x)
    ok, err = run_program(src)
    return bool(ok), True, err


def check_harness():
    """A sandbox that fails to launch scores every solution wrong and still produces a
    full, plausible results table. So: assert, do not print."""
    assert score_literal("[1, 2]", "[1,2]")
    assert score_literal("```python\n'ab'\n```", '"ab"')
    assert not score_literal("3", "4")
    assert run_program("assert 1 + 1 == 2")[0], "sandbox cannot run a passing program"
    assert not run_program("assert 1 + 1 == 3")[0], "sandbox misses a failing assert"
    assert not run_program("while True: pass")[0], "sandbox does not stop a hang"
