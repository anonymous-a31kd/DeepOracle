#!/bin/bash
set -u -e -x


DATA_DIR=$1
REG_DIR=$2
N_JOBS=$3
GENERATOR=$4

if [ ! -d ${DATA_DIR} ]
then
    mkdir ${DATA_DIR}
fi
BASE_DIR=$(dirname "${DATA_DIR}")
SYSTEM_NAME=$(basename "${DATA_DIR}")

OUT_DIR=${DATA_DIR}/${GENERATOR}_generated
D4J_PATH=/home/program/defects4j
# D4J_PATH=/home/program/GrowingBugRepository

python eval/gen_tests_from_metadata_LLM.py ${DATA_DIR}/oracle_preds.csv ${REG_DIR} ${OUT_DIR} --test_harness data/test_harness --d4j_path ${D4J_PATH} --generator ${GENERATOR}
python eval/aggregate_test_cases_LLM.py ${OUT_DIR} --generator ${GENERATOR}
python eval/eval_tests.py ${OUT_DIR}/aggregated_d4j_tests/ -o ${OUT_DIR}/results/ -n ${N_JOBS}
python eval/fix_failed_tests_LLM.py ${OUT_DIR}/aggregated_d4j_tests ${OUT_DIR}/results ${OUT_DIR}/fixed_d4j_tests -m ${GENERATOR}
python eval/eval_tests.py ${OUT_DIR}/fixed_d4j_tests/ -o ${OUT_DIR}/fixed_results/ -n ${N_JOBS}
python eval/merge_results.py ${OUT_DIR}/results ${OUT_DIR}/fixed_results ${OUT_DIR}/merged_results

# collect both old results and merged results 
python eval/collect_test_results.py ${OUT_DIR} results --d4j_path ${D4J_PATH}
python eval/collect_test_results.py ${OUT_DIR} merged_results --d4j_path ${D4J_PATH}
python -m eval.postprocess_test_results ${OUT_DIR} results
python -m eval.postprocess_test_results ${OUT_DIR} merged_results
python -m rqs.rq1_2 cal_result --data_dir ${BASE_DIR} --system ${SYSTEM_NAME}
# remove all temp directories
rm -rf /tmp/run_bug_detection.pl_*
