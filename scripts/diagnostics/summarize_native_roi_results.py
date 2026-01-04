#!/usr/bin/env python3
"""
Summarize Native Space ROI Results

Creates a comprehensive HTML report with all results, visualizations, and logs.
Perfect for offline review during travel.

Usage:
    python summarize_native_roi_results.py --output-dir native_roi_report

Author: Created for native space ROI validation
Date: 2025-01-04
"""

import argparse
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime


def collect_results(derivatives_dir, subjects, rois):
    """Collect all transformation results."""
    results = []

    for subject in subjects:
        for roi in rois:
            subj_dir = derivatives_dir / f"sub-{subject}"

            # Check for output files
            roi_t1w = subj_dir / f"sub-{subject}_{roi}_space-T1w.nii.gz"
            roi_bold = subj_dir / f"sub-{subject}_{roi}_space-bold_run-1.nii.gz"
            roi_mask = subj_dir / f"sub-{subject}_{roi}_space-bold_run-1_mask.nii.gz"

            # QC images
            qc_overlay = subj_dir / f"QC_sub-{subject}_{roi}_run-1_overlay.png"
            qc_detailed = subj_dir / f"QC_sub-{subject}_{roi}_run-1_detailed.png"
            qc_histogram = subj_dir / f"QC_sub-{subject}_{roi}_run-1_histogram.png"
            sanity_check = subj_dir / f"sanity_check_sub-{subject}_{roi}_run-1.png"

            # Check voxel count from mask
            voxel_count = "N/A"
            if roi_mask.exists():
                import nibabel as nib
                mask_data = nib.load(roi_mask).get_fdata()
                voxel_count = int(np.sum(mask_data > 0))

            result = {
                'subject': f"sub-{subject}",
                'roi': roi,
                'roi_t1w_exists': roi_t1w.exists(),
                'roi_bold_exists': roi_bold.exists(),
                'roi_mask_exists': roi_mask.exists(),
                'voxel_count': voxel_count,
                'qc_overlay_exists': qc_overlay.exists(),
                'qc_detailed_exists': qc_detailed.exists(),
                'qc_histogram_exists': qc_histogram.exists(),
                'sanity_check_exists': sanity_check.exists(),
                'status': 'Success' if (roi_bold.exists() and voxel_count != "N/A" and voxel_count > 0) else 'Failed'
            }

            results.append(result)

    return pd.DataFrame(results)


def parse_logs(log_dir):
    """Parse SLURM logs for errors and completion status."""
    log_info = []

    for log_file in log_dir.glob("native_roi_*.out"):
        with open(log_file, 'r') as f:
            content = f.read()

            # Extract job info from filename
            # Format: native_roi_JOBID_ARRAYID.out
            parts = log_file.stem.split('_')
            if len(parts) >= 3:
                array_id = parts[-1]
            else:
                array_id = "unknown"

            # Check for success/failure indicators
            has_error = "❌" in content or "ERROR" in content or "Failed" in content
            has_success = "✓ Complete" in content or "SUCCESS" in content

            log_info.append({
                'log_file': log_file.name,
                'array_id': array_id,
                'has_error': has_error,
                'has_success': has_success,
                'status': 'Failed' if has_error else ('Success' if has_success else 'Unknown')
            })

    return pd.DataFrame(log_info) if log_info else pd.DataFrame()


def generate_html_report(results_df, log_df, output_dir, derivatives_dir):
    """Generate comprehensive HTML report."""

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Native Space ROI Analysis Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        .summary-box {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .success {{
            color: #27ae60;
            font-weight: bold;
        }}
        .failed {{
            color: #e74c3c;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .qc-gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .qc-item {{
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            background-color: #fafafa;
        }}
        .qc-item img {{
            width: 100%;
            height: auto;
            border-radius: 3px;
        }}
        .qc-item-title {{
            font-weight: bold;
            margin: 10px 0 5px 0;
            color: #2c3e50;
        }}
        .metric {{
            display: inline-block;
            padding: 5px 15px;
            margin: 5px;
            border-radius: 3px;
            background-color: #3498db;
            color: white;
        }}
        .metadata {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Native Space ROI Analysis Report</h1>

        <div class="metadata">
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Purpose:</strong> MNI-independent ROI validation in native BOLD space</p>
        </div>

        <h2>📊 Executive Summary</h2>
        <div class="summary-box">
"""

    # Calculate summary statistics
    total_analyses = len(results_df)
    successful = len(results_df[results_df['status'] == 'Success'])
    failed = total_analyses - successful
    success_rate = (successful / total_analyses * 100) if total_analyses > 0 else 0

    # By subject
    subjects_success = results_df.groupby('subject')['status'].apply(
        lambda x: (x == 'Success').sum()
    ).to_dict()

    # By ROI
    roi_success = results_df.groupby('roi')['status'].apply(
        lambda x: (x == 'Success').sum()
    ).to_dict()

    html_content += f"""
            <div class="metric">Total Analyses: {total_analyses}</div>
            <div class="metric">Successful: <span class="success">{successful}</span></div>
            <div class="metric">Failed: <span class="failed">{failed}</span></div>
            <div class="metric">Success Rate: {success_rate:.1f}%</div>
        </div>

        <h2>📋 Results by Subject</h2>
        <table>
            <thead>
                <tr>
                    <th>Subject</th>
                    <th>V1</th>
                    <th>V2</th>
                    <th>V3</th>
                    <th>hV4</th>
                    <th>Total Success</th>
                </tr>
            </thead>
            <tbody>
"""

    for subject in sorted(results_df['subject'].unique()):
        subj_data = results_df[results_df['subject'] == subject]
        html_content += f"<tr><td><strong>{subject}</strong></td>"

        for roi in ['V1', 'V2', 'V3', 'hV4']:
            roi_data = subj_data[subj_data['roi'] == roi]
            if len(roi_data) > 0:
                status = roi_data.iloc[0]['status']
                voxels = roi_data.iloc[0]['voxel_count']
                status_class = 'success' if status == 'Success' else 'failed'
                html_content += f'<td class="{status_class}">{status}<br>({voxels} voxels)</td>'
            else:
                html_content += '<td>-</td>'

        success_count = subjects_success.get(subject, 0)
        html_content += f'<td><strong>{success_count}/4</strong></td></tr>'

    html_content += """
            </tbody>
        </table>

        <h2>📋 Results by ROI</h2>
        <table>
            <thead>
                <tr>
                    <th>ROI</th>
                    <th>Success Count</th>
                    <th>Success Rate</th>
                    <th>Mean Voxels</th>
                </tr>
            </thead>
            <tbody>
"""

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        roi_data = results_df[results_df['roi'] == roi]
        success_count = (roi_data['status'] == 'Success').sum()
        success_rate = success_count / len(roi_data) * 100 if len(roi_data) > 0 else 0

        # Mean voxels (only successful)
        success_voxels = roi_data[roi_data['status'] == 'Success']['voxel_count']
        mean_voxels = success_voxels[success_voxels != "N/A"].astype(int).mean() if len(success_voxels) > 0 else 0

        html_content += f"""
                <tr>
                    <td><strong>{roi}</strong></td>
                    <td>{success_count}/{len(roi_data)}</td>
                    <td>{success_rate:.1f}%</td>
                    <td>{mean_voxels:.0f}</td>
                </tr>
"""

    html_content += """
            </tbody>
        </table>

        <h2>🖼️ Quality Control Images</h2>
        <p>Overlay visualizations showing ROI placement on native BOLD reference images.</p>
        <div class="qc-gallery">
"""

    # Add QC images
    for _, row in results_df.iterrows():
        if row['status'] == 'Success':
            subject = row['subject']
            roi = row['roi']

            # Copy images to report directory
            subj_dir = derivatives_dir / subject
            qc_detailed = subj_dir / f"QC_{subject}_{roi}_run-1_detailed.png"

            if qc_detailed.exists():
                # Copy to report directory
                img_name = f"{subject}_{roi}_overlay.png"
                dest_path = output_dir / "images" / img_name
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(qc_detailed, dest_path)

                html_content += f"""
        <div class="qc-item">
            <div class="qc-item-title">{subject} - {roi}</div>
            <img src="images/{img_name}" alt="{subject} {roi}">
            <p style="font-size: 0.9em; color: #7f8c8d;">Voxels: {row['voxel_count']}</p>
        </div>
"""

    html_content += """
        </div>

        <h2>📁 Detailed Results Table</h2>
        <table>
            <thead>
                <tr>
                    <th>Subject</th>
                    <th>ROI</th>
                    <th>Voxels</th>
                    <th>T1w ROI</th>
                    <th>BOLD ROI</th>
                    <th>Mask</th>
                    <th>QC Images</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""

    for _, row in results_df.iterrows():
        status_class = 'success' if row['status'] == 'Success' else 'failed'
        qc_count = sum([row['qc_overlay_exists'], row['qc_detailed_exists'],
                       row['qc_histogram_exists'], row['sanity_check_exists']])

        html_content += f"""
                <tr>
                    <td>{row['subject']}</td>
                    <td>{row['roi']}</td>
                    <td>{row['voxel_count']}</td>
                    <td>{'✓' if row['roi_t1w_exists'] else '✗'}</td>
                    <td>{'✓' if row['roi_bold_exists'] else '✗'}</td>
                    <td>{'✓' if row['roi_mask_exists'] else '✗'}</td>
                    <td>{qc_count}/4</td>
                    <td class="{status_class}">{row['status']}</td>
                </tr>
"""

    html_content += """
            </tbody>
        </table>
"""

    # Add log summary if available
    if not log_df.empty:
        html_content += """
        <h2>📜 Job Logs Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>Log File</th>
                    <th>Array ID</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
        for _, log_row in log_df.iterrows():
            status_class = 'success' if log_row['status'] == 'Success' else ('failed' if log_row['status'] == 'Failed' else '')
            html_content += f"""
                <tr>
                    <td>{log_row['log_file']}</td>
                    <td>{log_row['array_id']}</td>
                    <td class="{status_class}">{log_row['status']}</td>
                </tr>
"""
        html_content += """
            </tbody>
        </table>
"""

    html_content += """
        <h2>📝 Interpretation Guide</h2>
        <div class="summary-box">
            <h3>Success Criteria:</h3>
            <ul>
                <li><strong>ROI Transformation:</strong> MNI → T1w → BOLD native conversion completed</li>
                <li><strong>Voxel Count > 0:</strong> ROI contains voxels in native BOLD space</li>
                <li><strong>QC Images:</strong> Visual verification of ROI location</li>
            </ul>

            <h3>Next Steps:</h3>
            <ul>
                <li><strong>If Successful:</strong> Proceed with native space analysis (GLM, decoding, hyperalignment)</li>
                <li><strong>If Failed:</strong> Check QC images for registration issues or coverage problems</li>
                <li><strong>For Group Analysis:</strong> Use successful subjects for hyperalignment/Procrustes</li>
            </ul>

            <h3>Key Insight:</h3>
            <p><strong>MNI normalization is NOT required!</strong> Successful ROI fitting in native space means analysis can proceed with hyperalignment for group-level comparisons.</p>
        </div>

        <div class="metadata">
            <p><strong>Documentation:</strong> See NATIVE_SPACE_ROI_PIPELINE.md for full details</p>
            <p><strong>Contact:</strong> Review QC images offline and decide on next analysis steps</p>
        </div>
    </div>
</body>
</html>
"""

    # Save HTML report
    report_path = output_dir / "native_roi_report.html"
    with open(report_path, 'w') as f:
        f.write(html_content)

    print(f"✓ HTML report generated: {report_path}")

    return report_path


def main():
    parser = argparse.ArgumentParser(
        description='Generate comprehensive native space ROI analysis report'
    )
    parser.add_argument('--derivatives', type=str,
                        default='/scratch/connectome/haba6030/colorBlind/derivatives/native_space_roi',
                        help='Path to derivatives directory')
    parser.add_argument('--logs', type=str,
                        default='/scratch/connectome/haba6030/colorBlind/logs/native_roi',
                        help='Path to log directory')
    parser.add_argument('--output-dir', type=str,
                        default='./native_roi_report',
                        help='Output directory for report')
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07', '08'],
                        help='Subject IDs to include')
    parser.add_argument('--rois', type=str, nargs='+',
                        default=['V1', 'V2', 'V3', 'hV4'],
                        help='ROIs to include')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    derivatives_dir = Path(args.derivatives)
    log_dir = Path(args.logs)

    print("=" * 80)
    print("Native Space ROI Results Summary")
    print("=" * 80)
    print()

    # Collect results
    print("📊 Collecting results...")
    results_df = collect_results(derivatives_dir, args.subjects, args.rois)
    print(f"   Found {len(results_df)} analyses")

    # Parse logs
    print("📜 Parsing logs...")
    if log_dir.exists():
        log_df = parse_logs(log_dir)
        print(f"   Found {len(log_df)} log files")
    else:
        print(f"   ⚠ Log directory not found: {log_dir}")
        log_df = pd.DataFrame()

    # Save CSV summaries
    print("💾 Saving CSV summaries...")
    results_df.to_csv(output_dir / "results_summary.csv", index=False)
    if not log_df.empty:
        log_df.to_csv(output_dir / "logs_summary.csv", index=False)

    # Generate HTML report
    print("📝 Generating HTML report...")
    report_path = generate_html_report(results_df, log_df, output_dir, derivatives_dir)

    # Copy logs
    if log_dir.exists():
        print("📋 Copying log files...")
        log_dest = output_dir / "logs"
        log_dest.mkdir(exist_ok=True)
        for log_file in log_dir.glob("*.out"):
            shutil.copy(log_file, log_dest / log_file.name)
        for log_file in log_dir.glob("*.err"):
            shutil.copy(log_file, log_dest / log_file.name)

    print()
    print("=" * 80)
    print("✓ Report Generation Complete!")
    print("=" * 80)
    print()
    print(f"Output directory: {output_dir.absolute()}")
    print(f"HTML report: {report_path.absolute()}")
    print()
    print("Summary:")
    print(f"  Total analyses: {len(results_df)}")
    print(f"  Successful: {len(results_df[results_df['status'] == 'Success'])}")
    print(f"  Failed: {len(results_df[results_df['status'] == 'Failed'])}")
    print()
    print("To view:")
    print(f"  open {report_path.absolute()}")
    print()
    print("To download (from local machine):")
    print(f"  scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/{args.output_dir} ./")
    print()


if __name__ == '__main__':
    main()
