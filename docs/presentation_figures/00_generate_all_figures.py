#!/usr/bin/env python3
"""
Master script to generate all presentation figures for professor meeting.

Usage:
    python 00_generate_all_figures.py

Output:
    All figures saved to current directory as PNG and PDF files.
"""

import subprocess
import sys
import os

# List of all figure generation scripts
scripts = [
    '01_decoding_results_bar_chart.py',
    '02_procrustes_alignment_2d.py',
    '03_loss_function_3d.py',
    '04_rdm_heatmaps_comparison.py'
]

print("="*70)
print("GENERATING ALL PRESENTATION FIGURES")
print("="*70)
print(f"\nTotal scripts to run: {len(scripts)}")
print(f"Output directory: {os.getcwd()}\n")

failed_scripts = []

for i, script in enumerate(scripts, 1):
    print(f"\n[{i}/{len(scripts)}] Running: {script}")
    print("-" * 70)

    try:
        result = subprocess.run(
            [sys.executable, script],
            check=True,
            capture_output=True,
            text=True
        )

        # Print script output
        if result.stdout:
            print(result.stdout)

        print(f"✅ SUCCESS: {script}")

    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {script}")
        print(f"Error: {e.stderr}")
        failed_scripts.append(script)
    except FileNotFoundError:
        print(f"❌ SCRIPT NOT FOUND: {script}")
        failed_scripts.append(script)

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"\n✅ Successful: {len(scripts) - len(failed_scripts)}/{len(scripts)}")

if failed_scripts:
    print(f"❌ Failed: {len(failed_scripts)}/{len(scripts)}")
    print("\nFailed scripts:")
    for script in failed_scripts:
        print(f"  - {script}")
else:
    print("\n🎉 All figures generated successfully!")

print("\n" + "="*70)
print("OUTPUT FILES:")
print("="*70)

# List all generated PNG and PDF files
png_files = sorted([f for f in os.listdir('.') if f.endswith('.png') and f[0].isdigit()])
pdf_files = sorted([f for f in os.listdir('.') if f.endswith('.pdf') and f[0].isdigit()])

if png_files:
    print("\n📊 PNG files (for slides):")
    for f in png_files:
        size_mb = os.path.getsize(f) / (1024 * 1024)
        print(f"  ✓ {f} ({size_mb:.2f} MB)")

if pdf_files:
    print("\n📄 PDF files (for high-quality print):")
    for f in pdf_files:
        size_mb = os.path.getsize(f) / (1024 * 1024)
        print(f"  ✓ {f} ({size_mb:.2f} MB)")

print("\n" + "="*70)
print("NEXT STEPS:")
print("="*70)
print("""
1. Review all generated figures
2. Import PNG files into presentation slides
3. Adjust figure sizes if needed
4. Use PDF files for print/poster versions

For individual regeneration, run:
    python 01_decoding_results_bar_chart.py
    python 02_procrustes_alignment_2d.py
    python 03_loss_function_3d.py
    python 04_rdm_heatmaps_comparison.py
""")
print("="*70)
