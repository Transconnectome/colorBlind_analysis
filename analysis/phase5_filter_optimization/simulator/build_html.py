"""Inline machado_table.json into simulator.template.html → simulator.html.

This makes the HTML self-contained so it works under file:// (no fetch needed).
"""
from pathlib import Path

_THIS = Path(__file__).resolve().parent
template = (_THIS / 'simulator.template.html').read_text(encoding='utf-8')
table = (_THIS / 'machado_table.json').read_text(encoding='utf-8')

placeholder = '__MACHADO_TABLE_JSON__'
assert placeholder in template, 'placeholder not found in template'
out = template.replace(placeholder, table)

out_path = _THIS / 'simulator.html'
out_path.write_text(out, encoding='utf-8')
print(f'wrote {out_path}  ({out_path.stat().st_size / 1024:.1f} KB)')
