NJOBS=${1:-12}
TOTAL=1
BUGGY_GEN_DIR="data/evosuite_buggy_regression_all"
FIXED_GEN_DIR="data/evosuite_fixed_regression_all"
BUGGY_TEST_DIR="data/evosuite_buggy_tests"
FIXED_TEST_DIR="data/evosuite_fixed_tests"

BUGGY_TEST_LLM_FILTER_DIR="../data/d4j_llm_prefix"

BUGGY_TEST_EVO_FILTER_DIR="../data/d4j_evo_prefix"


date

#  generate regression tests
# for i in `seq 1 ${TOTAL}`;do
#     python -m extractor.main gen_tests ${i} --out_dir ${FIXED_GEN_DIR}/${i}/generated --suffix f --n_jobs ${NJOBS}
# done

# for i in `seq 1 ${TOTAL}`;do
#     python -m extractor.main gen_tests ${i} --out_dir ${BUGGY_REACHING_BUGS}/${i}/generated --suffix b --n_jobs ${NJOBS}
# done

# rm -rf tmp/gen_tests.pl_*
# for i in `seq 1 ${TOTAL}`;do
# #     # python -m extractor.main prepare_tests ${FIXED_GEN_DIR}/${i}/generated
# #     # python -m extractor.main prepare_tests ${BUGGY_GEN_DIR}/${i}/generated
#     python -m extractor.main prepare_tests ${BUGGY_REACHING_BUGS}/${i}/generated
# done

# 
# for i in `seq 1 ${TOTAL}`;do
# #     # python -m extractor.main ex_tests ${FIXED_GEN_DIR}/${i} --output_dir ${FIXED_TEST_DIR}/${i}
# #     # python -m extractor.main ex_tests ${BUGGY_GEN_DIR}/${i} --output_dir ${BUGGY_TEST_DIR}/${i}
#     python -m extractor.main ex_tests ${BUGGY_REACHING_BUGS}/${i} --output_dir ${BUGGY_REACHING_BUGS_TEST_DIR}/${i}
# done

for i in `seq 1 ${TOTAL}`;do
#     # CUDA_VISIBLE_DEVICES=1 python toga.py ${FIXED_TEST_DIR}/${i}/inputs.csv ${FIXED_TEST_DIR}/${i}/meta.csv
#     # CUDA_VISIBLE_DEVICES=1 python toga.py ${BUGGY_TEST_DIR}/${i}/inputs.csv ${BUGGY_TEST_DIR}/${i}/meta.csv
    CUDA_VISIBLE_DEVICES=2 python toga.py ${BUGGY_TEST_EVO_FILTER_DIR}/toga/inputs.csv ${BUGGY_TEST_EVO_FILTER_DIR}/toga/meta.csv
done

# for i in `seq 1 ${TOTAL}`;do
#     python naive.py ${FIXED_TEST_DIR}/${i}/inputs.csv ${FIXED_TEST_DIR}/${i}/meta.csv
#     python naive.py ${BUGGY_TEST_DIR}/${i}/inputs.csv ${BUGGY_TEST_DIR}/${i}/meta.csv
# done

date