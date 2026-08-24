#!/bin/bash
export FSLDIR=/usr/local/fsl; export PATH=$FSLDIR/bin:$PATH; source $FSLDIR/etc/fslconf/fsl.sh
export FREESURFER_HOME=/usr/local/freesurfer/7.2.0; export PATH=$FREESURFER_HOME/bin:$PATH
export FS_LICENSE=/storage/connectome/haba6030/fs_license.txt
R=/storage/connectome/haba6030; S=/scratch/connectome/haba6030/colorBlind
SUB=08; RUN=1
W=$R/pilot/hmc_check; rm -rf $W; mkdir -p $W/vols; cd $W
export SUBJECTS_DIR=$R/fmriprep_work_method3_sub-$SUB/freesurfer_subjects
BOLD=$R/bids_editted/sub-$SUB/func/sub-${SUB}_task-rsvp_run-${RUN}_bold.nii.gz
T=$R/fmriprep_out_method3_header_mi/sub-$SUB/transforms
MNI=$S/templates/MNI152NLin2009cAsym_res-2_T1_brain.nii.gz
NV=$(fslinfo $BOLD | awk "/^dim4/{print \$2}"); REF=$((NV/2))
echo "[1] mcflirt -mats (NV=$NV REF=$REF)"
mcflirt -in $BOLD -out mc -refvol $REF -mats -plots
echo "[2] boldref + b2t"
fslroi $BOLD boldref $REF 1
tkregister2 --mov boldref.nii.gz --targ $R/fmriprep_work_method3_sub-$SUB/sub-${SUB}_T1w_brain.nii.gz \
  --reg tmp.dat --lta $T/sub-${SUB}_run-${RUN}_bold_to_t1w.lta --noedit --fslregout b2t.mat >/dev/null 2>&1
echo "[3] per-volume compose + applywarp (보간 1회)"
for v in $(seq 0 $((NV-1))); do
  vv=$(printf "%04d" $v)
  convert_xfm -omat vols/M_$vv.mat -concat b2t.mat mc.mat/MAT_$vv
  fslroi $BOLD vols/v_$vv $v 1
  applywarp --in=vols/v_$vv --ref=$MNI --premat=vols/M_$vv.mat \
            --warp=$T/sub-${SUB}_t1w_to_mni_warp.nii.gz --interp=trilinear --out=vols/o_$vv
done
echo "[4] merge"
fslmerge -t bold_hmc_mni $(ls vols/o_*.nii.gz | sort)
fslcpgeom $MNI bold_hmc_mni -d 2>/dev/null
rm -rf vols
echo DONE > $W/.done
