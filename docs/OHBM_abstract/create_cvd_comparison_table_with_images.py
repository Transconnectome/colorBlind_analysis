#!/usr/bin/env python3
"""
Create CVD comparison tables with cropped circular plots embedded
Compiles to PDF and optionally converts to PNG
"""

import os
import subprocess
from pathlib import Path
from PIL import Image
import numpy as np

# Base directories
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
INPUT_DIR = BASE_DIR / "docs/OHBM_abstract"
OUTPUT_DIR = BASE_DIR / "docs/OHBM_abstract/table_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Image files to crop (left circular graph only)
IMAGE_FILES = {
    ('Non-CVD', 'V1'): 'anova_circular_config32_determin_sub-06_V1_k50.png',
    ('Non-CVD', 'V2'): 'anova_circular_config32_determin_sub-06_V2_k50.png',
    ('Non-CVD', 'V3'): 'anova_circular_config32_determin_sub-06_V3_k8.png',
    ('Non-CVD', 'hV4'): 'anova_circular_config32_determin_sub-06_hV4_k50.png',
    ('CVD', 'V1'): 'anova_circular_config32_determin_sub-08_V1_k50.png',
    ('CVD', 'V2'): 'anova_circular_config32_determin_sub-08_V2_k50.png',
    ('CVD', 'V3'): 'anova_circular_config32_determin_sub-08_V3_k4.png',
    ('CVD', 'hV4'): 'anova_circular_config32_determin_sub-08_hV4_k11.png',
}

def crop_left_circular_plot(img_path, output_path):
    """Crop the left circular plot from the image"""
    img = Image.open(img_path)
    width, height = img.size

    # Assuming the image has two panels side by side
    # Crop left half with some margin
    left = 0
    top = 0
    right = width // 2  # Left half
    bottom = height

    # Fine-tune to get just the circular plot (adjust these values if needed)
    # Add some padding
    padding = 20
    left = padding
    right = width // 2 - padding
    top = padding
    bottom = height - padding

    cropped = img.crop((left, top, right, bottom))
    cropped.save(output_path, dpi=(300, 300))
    print(f"Cropped: {output_path.name}")

def create_cropped_images():
    """Crop all circular plot images"""
    cropped_dir = OUTPUT_DIR / "cropped"
    cropped_dir.mkdir(exist_ok=True)

    cropped_paths = {}
    for (group, roi), filename in IMAGE_FILES.items():
        input_path = INPUT_DIR / filename
        if not input_path.exists():
            print(f"Warning: {filename} not found, skipping")
            continue

        output_filename = f"cropped_{group.lower().replace('-', '')}_{roi}.png"
        output_path = cropped_dir / output_filename

        crop_left_circular_plot(input_path, output_path)
        cropped_paths[(group, roi)] = output_path

    return cropped_paths

def create_latex_document(cropped_paths):
    """Create LaTeX document with tables and embedded images"""

    latex_content = r"""\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{graphicx}
\usepackage{array}
\usepackage{xcolor}
\usepackage{colortbl}
\usepackage{adjustbox}

\begin{document}

% Table 1: Enhanced with Example Images
\begin{table}[htbp]
\centering
\caption{Reconstruction Error and Accuracy by ROI and Group with Representative Examples}
\label{tab:reconstruction_with_examples}
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{|c|c|c|c|c|}
\hline
\rowcolor{blue!30}
\textbf{ROI} & \textbf{Group} & \textbf{Mean Error} & \textbf{Acc@45° (\%)} & \textbf{Example} \\
\hline
\hline
"""

    # Add rows with data
    data = [
        ('V1', 'Non-CVD', '46.7° (SD 17.0°)', '59.6 (SD 25.1)'),
        ('V1', 'CVD', '42.4° (SD 4.9°)', '67.6 (SD 18.0)'),
        ('V2', 'Non-CVD', '56.9° (SD 16.8°)', '50.0 (SD 21.8)'),
        ('V2', 'CVD', '55.3° (SD 5.1°)', '40.9 (SD 3.8)'),
        ('V3', 'Non-CVD', '82.8° (SD 14.1°)', '27.9 (SD 5.1)'),
        ('V3', 'CVD', '78.9° (SD 7.5°)', '28.7 (SD 2.9)'),
        ('hV4', 'Non-CVD', '82.1° (SD 4.6°)', '27.5 (SD 1.5)'),
        ('hV4', 'CVD', '76.3° (SD 3.9°)', '29.6 (SD 1.5)'),
    ]

    for i, (roi, group, mean_error, acc45) in enumerate(data):
        # Check if this is the first of a pair (for multirow)
        if i % 2 == 0:
            roi_cell = f"\\multirow{{2}}{{*}}{{\\textbf{{{roi}}}}}"
        else:
            roi_cell = ""

        # Get image path
        img_key = (group, roi)
        if img_key in cropped_paths:
            rel_path = cropped_paths[img_key].relative_to(OUTPUT_DIR)
            img_cell = f"\\adjustbox{{valign=c}}{{\\includegraphics[width=2cm,height=2cm]{{{rel_path}}}}}"
        else:
            img_cell = "N/A"

        latex_content += f"{roi_cell} & \\textbf{{{group}}} & {mean_error} & {acc45} & {img_cell} \\\\\n"

        # Add cline between pairs
        if i % 2 == 0 and i < len(data) - 1:
            latex_content += "\\cline{2-5}\n"
        else:
            latex_content += "\\hline\n"

    latex_content += r"""
\end{tabular}
\begin{flushleft}
\scriptsize
\textit{Note: ANOVA config32\_determin analysis results. Non-CVD examples from Sub-06; CVD examples from Sub-08.}\\
\textit{Example images show cropped circular reconstruction plots (left panel only).}
\end{flushleft}
\end{table}

\newpage

% Table 2: K5 Permutation Validation Results
\begin{table}[htbp]
\centering
\caption{K5 Permutation Validation Results (k=5 ANOVA Feature Selection)}
\label{tab:k5_permutation}
\large
\begin{tabular}{|c|c|c|c|c|c|}
\hline
\rowcolor{green!30}
\textbf{Group} & \textbf{Before Permu} & \textbf{After Permu} & \textbf{Error Change} & \textbf{Effect Size (d)} & \textbf{p-value} \\
\hline
\hline
\textbf{Non-CVD} & 78.0° & 81.9° & +3.86° & 0.27 & \textcolor{blue}{\textbf{0.031*}} \\
\hline
\textbf{CVD} & 79.0° & 83.7° & +4.70° & 0.42 & \textcolor{green!60!black}{\textbf{0.011*}} \\
\hline
\end{tabular}
\begin{flushleft}
\small
\textit{* p < 0.05 (significant)}\\
\textit{Note: Both groups show significant validation (p < 0.05), indicating that the k=5 ANOVA}\\
\textit{feature selection successfully identifies informative voxels beyond chance.}
\end{flushleft}
\end{table}

\end{document}
"""

    # Write LaTeX file
    tex_path = OUTPUT_DIR / "cvd_comparison_tables.tex"
    with open(tex_path, 'w') as f:
        f.write(latex_content)

    print(f"\nLaTeX file created: {tex_path}")
    return tex_path

def compile_to_pdf(tex_path):
    """Compile LaTeX to PDF using pdflatex"""
    print("\nCompiling LaTeX to PDF...")

    # Run pdflatex twice for proper references
    for i in range(2):
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory',
             str(OUTPUT_DIR), str(tex_path)],
            capture_output=True,
            text=True,
            cwd=str(OUTPUT_DIR)
        )

        if result.returncode != 0:
            print(f"Error compiling LaTeX (run {i+1}):")
            print(result.stdout[-500:])  # Last 500 chars
            return None

    pdf_path = OUTPUT_DIR / "cvd_comparison_tables.pdf"
    if pdf_path.exists():
        print(f"PDF created successfully: {pdf_path}")
        return pdf_path
    else:
        print("PDF compilation failed")
        return None

def convert_pdf_to_png(pdf_path, dpi=300):
    """Convert PDF to high-resolution PNG"""
    print("\nConverting PDF to PNG...")

    png_path = pdf_path.with_suffix('.png')

    # Using ImageMagick convert
    result = subprocess.run(
        ['convert', '-density', str(dpi), '-quality', '100',
         str(pdf_path), str(png_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Error converting to PNG (trying alternative method):")
        # Try sips (macOS built-in)
        result = subprocess.run(
            ['sips', '-s', 'format', 'png', str(pdf_path), '--out', str(png_path)],
            capture_output=True,
            text=True
        )

    if png_path.exists():
        print(f"PNG created: {png_path}")
        return png_path
    else:
        print("PNG conversion failed (ImageMagick may not be installed)")
        return None

def main():
    print("=" * 70)
    print("Creating CVD Comparison Tables with Embedded Images")
    print("=" * 70)

    # Step 1: Crop circular plots
    print("\n[Step 1] Cropping circular plot images...")
    cropped_paths = create_cropped_images()
    print(f"Cropped {len(cropped_paths)} images")

    # Step 2: Create LaTeX document
    print("\n[Step 2] Creating LaTeX document...")
    tex_path = create_latex_document(cropped_paths)

    # Step 3: Compile to PDF
    print("\n[Step 3] Compiling to PDF...")
    pdf_path = compile_to_pdf(tex_path)

    if pdf_path:
        # Step 4: Convert to PNG (optional)
        print("\n[Step 4] Converting to PNG (optional)...")
        png_path = convert_pdf_to_png(pdf_path)

        print("\n" + "=" * 70)
        print("SUCCESS! Files created:")
        print(f"  - LaTeX: {tex_path}")
        print(f"  - PDF:   {pdf_path}")
        if png_path:
            print(f"  - PNG:   {png_path}")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("PDF compilation failed. Check LaTeX installation.")
        print(f"LaTeX file is available at: {tex_path}")
        print("=" * 70)

if __name__ == "__main__":
    main()
