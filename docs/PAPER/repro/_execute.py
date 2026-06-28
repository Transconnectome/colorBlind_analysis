"""Lightweight notebook executor (no nbconvert/nbclient available in srm env).

Runs each notebook's code cells in one shared namespace, captures stdout, writes
it back as a stream output per cell (so the .ipynb is genuinely executed), and
prints a compact pass/fail tail for the reproduction report. Run under srm:
    conda run -n srm python _execute.py
"""
import io
import json
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
NBS = sorted(HERE.glob("[0-9][0-9]_*.ipynb"))


def run_nb(path):
    o = json.loads(path.read_text())
    ns = {"__name__": "__main__"}
    n = 0
    failed = False
    for cell in o["cells"]:
        if cell["cell_type"] != "code":
            continue
        n += 1
        src = "".join(cell["source"])
        buf = io.StringIO()
        out_text = ""
        try:
            with redirect_stdout(buf):
                exec(compile(src, f"{path.name}:cell{n}", "exec"), ns)
            out_text = buf.getvalue()
        except Exception:
            out_text = buf.getvalue() + "\n" + traceback.format_exc()
            failed = True
        cell["execution_count"] = n
        cell["outputs"] = [{
            "output_type": "stream", "name": "stdout", "text": out_text.splitlines(keepends=True)
        }] if out_text else []
        if failed:
            break
    path.write_text(json.dumps(o, indent=1))
    return failed


if __name__ == "__main__":
    for p in NBS:
        print("\n" + "=" * 70 + f"\nEXECUTE {p.name}\n" + "=" * 70)
        # re-read tail of last summary by capturing during run
        bad = run_nb(p)
        # print the executed last-cell output (summary) for the console report
        o = json.loads(p.read_text())
        for cell in o["cells"][::-1]:
            if cell["cell_type"] == "code" and cell.get("outputs"):
                print("".join(cell["outputs"][0]["text"])[-1500:])
                break
        print("STATUS:", "ERROR (halted)" if bad else "completed")
