#!/usr/bin/env python3
"""
데이터 구조 확인 스크립트

목적:
1. Events 파일 구조 분석
2. 자극 순서 동일성 검증
3. Hyperalignment (trial-aligned GPA) 가능성 확인

사용법:
    python 00_check_data_structure.py --subjects 02 03 05 06 07

Author: Neuroimaging Team
Date: 2025-12-28
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import json


def parse_args():
    """커맨드라인 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='데이터 구조 확인 및 자극 순서 동일성 검증'
    )
    parser.add_argument(
        '--subjects',
        nargs='+',
        default=['02', '03', '05', '06', '07'],
        help='분석할 피험자 ID (default: HC 5명)'
    )
    parser.add_argument(
        '--base_path',
        type=str,
        default='/storage/connectome/haba6030/colorBlind_data_deoblique',
        help='BIDS 데이터 루트 경로'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='../results/data_structure_check',
        help='결과 저장 경로'
    )

    return parser.parse_args()


def load_events(subject_id, run_id, base_path):
    """
    Events 파일 로드

    Parameters
    ----------
    subject_id : str
        피험자 ID (예: '02')
    run_id : int
        Run 번호 (1-6)
    base_path : str or Path
        BIDS 데이터 루트 경로

    Returns
    -------
    events_df : pd.DataFrame
        Events 데이터프레임
    """
    base_path = Path(base_path)
    events_file = base_path / f'sub-{subject_id}' / 'func' / \
                  f'sub-{subject_id}_task-rsvp_run-{run_id}_events.tsv'

    if not events_file.exists():
        print(f"⚠️ Warning: Events 파일 없음: {events_file}")
        return None

    try:
        events_df = pd.read_csv(events_file, sep='\t')
        return events_df
    except Exception as e:
        print(f"❌ Error loading {events_file}: {e}")
        return None


def analyze_events_structure(events_df, subject_id, run_id):
    """
    Events 파일 구조 분석

    Parameters
    ----------
    events_df : pd.DataFrame
        Events 데이터프레임
    subject_id : str
        피험자 ID
    run_id : int
        Run 번호

    Returns
    -------
    info : dict
        구조 정보
    """
    info = {
        'subject_id': subject_id,
        'run_id': run_id,
        'n_trials': len(events_df),
        'columns': list(events_df.columns),
        'trial_types': events_df['trial_type'].unique().tolist() if 'trial_type' in events_df.columns else None,
        'onset_range': (events_df['onset'].min(), events_df['onset'].max()) if 'onset' in events_df.columns else None,
        'duration': events_df['duration'].unique().tolist() if 'duration' in events_df.columns else None,
    }

    # Color trials만 필터링
    if 'trial_type' in events_df.columns:
        color_trials = events_df[events_df['trial_type'] != 'gray']
        info['n_color_trials'] = len(color_trials)

        # Trial type별 카운트
        trial_counts = events_df['trial_type'].value_counts().to_dict()
        info['trial_counts'] = trial_counts

    return info


def check_stimulus_order_consistency(all_events, subjects, runs):
    """
    자극 순서 동일성 검증

    Parameters
    ----------
    all_events : dict
        {(subject, run): events_df} 형태
    subjects : list
        피험자 ID 리스트
    runs : list
        Run 번호 리스트

    Returns
    -------
    is_consistent : bool
        순서 일치 여부
    order_info : dict
        순서 정보
    """
    print("\n" + "="*60)
    print("자극 순서 동일성 검증")
    print("="*60)

    # Reference: 첫 번째 subject의 첫 번째 run
    ref_subject = subjects[0]
    ref_run = runs[0]
    ref_key = (ref_subject, ref_run)

    if ref_key not in all_events or all_events[ref_key] is None:
        print(f"❌ Reference events 없음: sub-{ref_subject}, run-{ref_run}")
        return False, {}

    ref_events = all_events[ref_key]
    ref_sequence = ref_events['trial_type'].tolist()

    print(f"\nReference: sub-{ref_subject}, run-{ref_run}")
    print(f"  Total trials: {len(ref_sequence)}")
    print(f"  Trial types: {ref_events['trial_type'].unique()}")

    # 모든 subject-run pair와 비교
    consistency_results = {}
    all_consistent = True

    for subject_id in subjects:
        for run_id in runs:
            key = (subject_id, run_id)

            if key not in all_events or all_events[key] is None:
                print(f"  ⚠️ Missing: sub-{subject_id}, run-{run_id}")
                consistency_results[key] = False
                all_consistent = False
                continue

            events_df = all_events[key]
            sequence = events_df['trial_type'].tolist()

            # 순서 비교
            if sequence == ref_sequence:
                consistency_results[key] = True
                print(f"  ✅ sub-{subject_id}, run-{run_id}: IDENTICAL")
            else:
                consistency_results[key] = False
                all_consistent = False
                print(f"  ❌ sub-{subject_id}, run-{run_id}: DIFFERENT")

                # 차이점 출력
                if len(sequence) != len(ref_sequence):
                    print(f"      Length: {len(sequence)} vs {len(ref_sequence)}")
                else:
                    diff_indices = [i for i in range(len(sequence))
                                   if sequence[i] != ref_sequence[i]]
                    print(f"      Different positions: {len(diff_indices)}/{len(sequence)}")
                    if len(diff_indices) <= 10:
                        print(f"      Indices: {diff_indices[:10]}")

    order_info = {
        'reference': ref_key,
        'ref_sequence_length': len(ref_sequence),
        'consistency_results': consistency_results,
        'all_consistent': all_consistent,
    }

    print("\n" + "-"*60)
    if all_consistent:
        print("✅ 결론: 모든 subject-run에서 자극 순서 IDENTICAL")
        print("   → Hyperalignment (trial-aligned GPA) 가능!")
    else:
        print("❌ 결론: 자극 순서 불일치 발견")
        print("   → Hyperalignment (trial-aligned GPA) 불가")
        print("   → 대안: 조건 기반 GPA (8 colors)")

    print("="*60 + "\n")

    return all_consistent, order_info


def calculate_trial_statistics(all_events):
    """
    Trial 통계 계산

    Parameters
    ----------
    all_events : dict
        {(subject, run): events_df} 형태

    Returns
    -------
    stats : dict
        통계 정보
    """
    all_isis = []
    all_durations = []
    all_trial_counts = []

    for (subject_id, run_id), events_df in all_events.items():
        if events_df is None:
            continue

        # ISI (Inter-Stimulus Interval)
        onsets = events_df['onset'].values
        isis = np.diff(onsets)
        all_isis.extend(isis)

        # Duration
        if 'duration' in events_df.columns:
            all_durations.extend(events_df['duration'].values)

        # Trial count
        all_trial_counts.append(len(events_df))

    stats = {
        'mean_isi': np.mean(all_isis) if all_isis else None,
        'std_isi': np.std(all_isis) if all_isis else None,
        'min_isi': np.min(all_isis) if all_isis else None,
        'mean_duration': np.mean(all_durations) if all_durations else None,
        'mean_trials_per_run': np.mean(all_trial_counts) if all_trial_counts else None,
        'total_trials': sum(all_trial_counts) if all_trial_counts else 0,
    }

    print("\n" + "="*60)
    print("Trial 통계")
    print("="*60)
    print(f"평균 ISI: {stats['mean_isi']:.2f}s ± {stats['std_isi']:.2f}s")
    print(f"최소 ISI: {stats['min_isi']:.2f}s")
    print(f"평균 Duration: {stats['mean_duration']:.2f}s")
    print(f"Run당 평균 trials: {stats['mean_trials_per_run']:.1f}")
    print(f"총 trials (all subjects/runs): {stats['total_trials']}")

    # HRF 겹침 체크
    if stats['min_isi'] is not None and stats['min_isi'] < 4.0:
        print(f"\n⚠️ WARNING: 최소 ISI ({stats['min_isi']:.2f}s) < 4s")
        print("   → HRF 겹침 가능성 있음")
        print("   → LS-S 또는 FIR deconvolution 권장")
    else:
        print(f"\n✅ 최소 ISI ({stats['min_isi']:.2f}s) ≥ 4s")
        print("   → HRF 겹침 최소화")

    print("="*60 + "\n")

    return stats


def main():
    """메인 함수"""
    args = parse_args()

    print("\n" + "="*80)
    print("데이터 구조 확인 및 자극 순서 동일성 검증")
    print("="*80)
    print(f"Subjects: {args.subjects}")
    print(f"Base path: {args.base_path}")
    print("="*80 + "\n")

    # 출력 디렉토리 생성
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 모든 events 로드
    all_events = {}
    runs = range(1, 7)  # Run 1-6

    for subject_id in args.subjects:
        print(f"\nLoading subject {subject_id}...")
        for run_id in runs:
            events_df = load_events(subject_id, run_id, args.base_path)
            all_events[(subject_id, run_id)] = events_df

            if events_df is not None:
                info = analyze_events_structure(events_df, subject_id, run_id)
                print(f"  Run {run_id}: {info['n_trials']} trials "
                      f"({info.get('n_color_trials', '?')} color trials)")

    # 자극 순서 동일성 검증
    is_consistent, order_info = check_stimulus_order_consistency(
        all_events, args.subjects, runs
    )

    # Trial 통계
    stats = calculate_trial_statistics(all_events)

    # 결과 저장
    summary = {
        'subjects': args.subjects,
        'n_runs': len(runs),
        'stimulus_order_consistent': is_consistent,
        'order_info': {k: str(v) for k, v in order_info.items()
                      if k != 'consistency_results'},
        'trial_statistics': stats,
        'recommendation': None,
    }

    # 권장 사항
    if is_consistent:
        if stats['min_isi'] >= 4.0:
            recommendation = "Hyperalignment (trial-aligned GPA) with LS-A (충분한 ISI, full voxel space)"
        else:
            recommendation = "Hyperalignment (trial-aligned GPA) with LS-S (HRF 겹침 고려, full voxel space)"
    else:
        recommendation = "조건 기반 GPA (자극 순서 불일치, 8 colors)"

    summary['recommendation'] = recommendation

    # JSON 저장
    output_file = output_dir / 'data_structure_summary.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"✅ 결과 저장: {output_file}\n")

    # 최종 권장 사항
    print("="*80)
    print("최종 권장 사항")
    print("="*80)
    print(f"✨ {recommendation}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
