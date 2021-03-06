#!/usr/bin/env python
# coding: utf-8

from __future__ import division

from nipype.algorithms.metrics import FuzzyOverlap
from nilearn.image import resample_to_img
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
from collections import Counter
from nilearn import plotting
import nibabel as nib
import seaborn as sns
import pandas as pd
import progressbar
import numpy as np
import palettable
import json
import sys
import os

sys.path.append(os.path.join(os.environ.get("HOME"),"CNP_analysis"))
from utils import get_config

pipelines= ['fmriprep-1.0.3','fslfeat_5.0.9']

basedir = os.path.join(os.environ.get("PREPBASEDIR"),"fmriprep_vs_feat")

# Atlases and effect sizes in regions

def create_atlas():
    # 1: left STN
    # 2: right STN
    STN_05 = os.path.join(os.environ.get("FSLDIR"),'data/atlases/STN/STN-maxprob-thr0-0.5mm.nii.gz')
    # 4: Inferior Frontal Gyrus, pars triangularis
    # 25: Juxtapositional Lobule Cortex (formerly Supplementary Motor Cortex)
    # 7: Precentral gyrus (motor)
    HO = os.path.join(os.environ.get("FSLDIR"),'data/atlases/HarvardOxford/HarvardOxford-cort-maxprob-thr25-1mm.nii.gz')
    STN = resample_to_img(STN_05, HO, interpolation='nearest')
    STN_dat = STN.get_data()
    HO_dat = nib.load(HO).get_data()

    assert(len(np.where(np.logical_and(HO_dat!=0,STN_dat!=0))[0])==0)

    newat = np.zeros(STN.shape[:3])
    newat[np.where(HO_dat==7)] = 4
    newat[np.where(HO_dat==5)] = 3
    newat[np.where(HO_dat==26)] = 2
    newat[np.where(STN_dat>0)] = 1
    atlas = nib.Nifti1Image(newat,affine=STN.affine,header=STN.header)
    labels = {
        1:"STN",
        2:"preSMA",
        3:"IFG",
        4:"PCG"
    }
    return atlas,labels

# Overlap measures

def fdice(im1,im2):
    overlap = FuzzyOverlap()
    overlap.inputs.in_ref = [im1]
    overlap.inputs.in_tst = [im2]
    overlap.inputs.weighting = 'volume'
    res = overlap.run()
    return res.outputs.dice

def dice(im1,im2):
    binarised = []
    for sample in [im1,im2]:
        thres = nib.load(sample).get_data()
        flt = thres.flatten()
        binarised.append(np.array([1 if x > 0 else 0 for x in flt]))

    sm = binarised[0] + binarised[1]
    dice = np.sum(sm==2)*2/np.sum(sm>0)
    return dice

def cohen(tstat,atlas,labels):
    res = {}
    for k,v in labels.iteritems():
        indxs = np.where(atlas==k)
        T = tstat[indxs]
        CD = np.mean(T)/np.sqrt(samplesize)
        res[v] = CD
    return res

def get_file(samplesize,experiment,basedir,thres='FWE'):
    out = {}
    for pipeline in pipelines:
        out[pipeline] = {}

        for sample in range(2):
            prefix = os.path.join(basedir,pipeline,'task_group/samplesize_%i/experiment_%i'%(samplesize,experiment),
                         "stopsignal/sample_%i/cope11/OLS/"%(sample))
            out[pipeline][sample] = {}

            thressuf = 'thresh_vox_fwe_tstat1.nii.gz' if thres == 'FWE' else 'thresh_vox_fdr_pstat1.nii.gz'
            out[pipeline][sample]['thres'] = os.path.join(prefix,thressuf)
            out[pipeline][sample]['tfile'] = os.path.join(prefix,'tstat1.nii.gz')
            out[pipeline][sample]['pfile'] = os.path.join(prefix,'pstat1.nii.gz')

            if not os.path.exists(out[pipeline][sample]['tfile']):
                return False

            if False: #resample to other image, turned off

                thresrssuf = 'thresh_vox_fwe_tstat1_resampled.nii.gz' if thres == 'FWE' else 'thresh_vox_fdr_pstat1_resampled.nii.gz'
                out[pipeline][sample]['newthres'] = os.path.join(prefix,thresrssuf)
                out[pipeline][sample]['newtfile'] = os.path.join(prefix,'tstat1_resampled.nii.gz')
                out[pipeline][sample]['newpfile'] = os.path.join(prefix,'pstat1_resampled.nii.gz')

                for pipeline in pipelines:
                    if pipeline.startswith('fmriprep-1.0.3'):
                        for idx,kind in enumerate(['tfile','pfile','thres']):
                            newkind = ['newtfile','newpfile','newthres'][idx]
                            if not os.path.exists(out[pipeline][sample][newkind]):
                                newimg = resample_to_img(out[pipeline][sample][kind],out["fslfeat_5.0.9"][sample][kind],interpolation='nearest')
                                newimg.to_filename(out[pipeline][sample][newkind])
                            out[pipeline][sample][kind] = out[pipeline][sample][newkind]

    return out

# COLLECT

atlas,labels = create_atlas()

results = pd.DataFrame()
allT = {}

for pipeline in pipelines:
    allT[pipeline] = {}
    k = 0
    bar = progressbar.ProgressBar()
    for samplesize in bar(np.arange(10,101,5).tolist()):
        k += 1
        rng = range(0,100)
        allT[pipeline][samplesize] = []
        for experiment in rng:

            fls = get_file(samplesize,experiment
                           ,basedir,thres='FDR')
            if fls == False:
                continue

            # read in tvals
            tvals = [nib.load(fls[pipeline][x]['tfile']).get_data() for x in range(2)]

            # compute mask to have exactly same values
            tmpmask = np.where(np.logical_and(tvals[0]!=0,tvals[1]!=0))

            tvs = [x[tmpmask].tolist() for x in tvals]
            tvs = [x for sublist in tvs for x in sublist]
            sel = np.random.choice(tvs, 100).tolist()
            allT[pipeline][samplesize] += sel

            # prepare atlas
            if k==1:
                atlas_resampled = resample_to_img(atlas,fls[pipeline][0]['tfile'],interpolation='nearest')
                dat = atlas_resampled.get_data()

            res = cohen(tvals[0],dat,labels)

            # compute correlation
            res["correlation"] = pearsonr(tvals[0][tmpmask],tvals[1][tmpmask])[0]

            # compute fuzzy dice
            res["fdice"] = fdice(fls[pipeline][0]['pfile'],fls[pipeline][1]['pfile'])

            # compute dice
            res["dice"] = dice(fls[pipeline][0]['thres'],fls[pipeline][1]['thres'])

            res["samplesize"]=samplesize
            res["pipeline"]=pipeline
            res["experiment"]=experiment

            results = results.append(res,ignore_index=True)

            del tvals,tmpmask,res,fls

with open(os.path.join(basedir,"tvals.json"), 'w') as outfile:
    json.dump(allT, outfile)

results.to_csv(os.path.join(basedir,"results.csv"))
