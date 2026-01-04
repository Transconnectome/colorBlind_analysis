# Group-Level Analysis 실행 가이드
This docs illustrates guide for finding out how brain mapping of color is different between HC and CVD. 

- Previous Results in `OHBM_abstract`
HC group and CVD group were able to distinguish color stimuli with their voxel responses. 
CVD **could** distinguish green and red, also other colors in primary voxel.
So, for designing filter to modify their behavioural deficit in distinguishing color, we will try to move CVD's neural response toward that of HC. 
In this motivation, we should **enumerate how they differ**, for future step of designing deep-learning based color adjustment filter.

- Upcoming Progress
[] Find out in which domain HC and CVD differ and how they differ
    [] Voxel domain
    [] Mapping domain
    [] Channel domain
[] Fit common model of color decoding for HC and test whether it is applicable to CVD
    [] If common model for HC is designed, apply to HC
    [] If hard, try cross validation by training part of HC and apply to remaining HC and CVD

## Objective
1. Find out whether HC share common system of color perception (in any domains)
2. Find out in which domain HC and CVD differ (actually whether they do differ).  
3. Enumerate such difference for future filter designing (to apply as loss function)

## Plan (1): Can we apply HC's common perception system to CVD?
1. Find out common system of HC, related to current encoding-decoding mechanism
2. Check whether such system can reproduce each HC individuals' decoding process
3. Check whether application of such model to CVD can cause problematic result compared to individually optimized results. 

### Voxel domain
Does voxel activation are shared within HC group and differ between HC and CVD group? 
- Does using significant voxel number in feature selection of HC impairs reconstruction accuracy of CVD group?
- Does common voxel of significance differ between HC and CVD group? 


### Mapping domain (Not Now)

### Channel domain
Does color channel design are shared within HC group and differ between HC and CVD group? 
We currently assume identical interval between 6 channels, which can be not the case
1. HC group share predicted channel structure?
2. CVD group show difference channel structure?
3. Such can explain difference in voxel level
    - Or, does using HC group's channel design impair reconstruction of CVD group? 

## Plan (2): Can HC-based model be applied to other HC and CVD?
- Make common reconstruction model of part of HC
- Apply to other remaining HC and CVD.
- Compare the difference of reconstruction result. 
