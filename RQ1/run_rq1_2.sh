#!/bin/bash
N_JOBS=$1
START=${2:-1}
END=1
g=togs
project_base=/home/program/DeepOracle

for i in `seq ${START} ${END}`;do
    echo ${i}
    for t in buggy;do
        echo ${t}
        echo ${g}
        echo ${project_base}
        # d4j_evo_prefix
        bash run_exp.sh ${project_base}/data/d4j_evo_prefix/toga data/evosuite_${t}_regression_all/${i} ${N_JOBS} toga
        bash run_exp.sh ${project_base}/data/d4j_evo_prefix/togll data/evosuite_${t}_regression_all/${i} ${N_JOBS} togll
        bash run_exp.sh ${project_base}/data/d4j_evo_prefix/llm_direct data/evosuite_${t}_regression_all/${i} ${N_JOBS} togs
        bash run_exp.sh ${project_base}/data/d4j_evo_prefix/deeporacle data/evosuite_${t}_regression_all/${i} ${N_JOBS} togs

        # d4j_llm_prefix
        bash run_exp_llm.sh ${project_base}/data/d4j_llm_prefix/toga data/llm_${t}_d4j_patch/${i} ${N_JOBS} toga
        bash run_exp_llm.sh ${project_base}/data/d4j_llm_prefix/togll data/llm_${t}_d4j_patch/${i} ${N_JOBS} togll
        bash run_exp_llm.sh ${project_base}/data/d4j_llm_prefix/llm_direct data/llm_${t}_d4j_patch/${i} ${N_JOBS} togs
        bash run_exp_llm.sh ${project_base}/data/d4j_llm_prefix/deeporacle data/llm_${t}_d4j_patch/${i} ${N_JOBS} togs

        # gb_evo_prefix
        bash run_exp.sh ${project_base}/data/gb_evo_prefix/toga data/evosuite_${t}_GBR/${i} ${N_JOBS} toga
        bash run_exp.sh ${project_base}/data/gb_evo_prefix/togll data/evosuite_${t}_GBR/${i} ${N_JOBS} togll
        bash run_exp.sh ${project_base}/data/gb_evo_prefix/llm_direct data/evosuite_${t}_GBR/${i} ${N_JOBS} togs
        bash run_exp.sh ${project_base}/data/gb_evo_prefix/deeporacle data/evosuite_${t}_GBR/${i} ${N_JOBS} togs

        # gb_llm_prefix
        bash run_exp_llm.sh ${project_base}/data/gb_llm_prefix/toga data/llm_${t}_GBR_new_bugs_patch/${i} ${N_JOBS} toga
        bash run_exp_llm.sh ${project_base}/data/gb_llm_prefix/togll data/llm_${t}_GBR_new_bugs_patch/${i} ${N_JOBS} togll
        bash run_exp_llm.sh ${project_base}/data/gb_llm_prefix/llm_direct data/llm_${t}_GBR_new_bugs_patch/${i} ${N_JOBS} togs
        bash run_exp_llm.sh ${project_base}/data/gb_llm_prefix/deeporacle data/llm_${t}_GBR_new_bugs_patch/${i} ${N_JOBS} togs
    
    done
    rm -rf ~/tmp/run_bug_detection.pl_*
done

