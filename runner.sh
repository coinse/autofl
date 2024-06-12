LABEL_PREFIX=$1
if [ -z  "$1" ]; then
    echo "Please provide an experiment label."
    exit 0
fi
REPETITION=$2
DATASET=$3 # defects4j or bugsinpy
MODEL=$4
PROJECT=$5

DATA_DIR=./data/${DATASET}/
ENDPOINT="http://localhost:11434/v1"
PROMPT_FILE="prompts/system_msg_expbug_with_funcs.txt"
BUDGET="10"
NUM_TESTS="1"

trap 'echo interrupted; exit 1' INT

for rep in $(seq 1 "$REPETITION"); do
    label="${LABEL_PREFIX}${rep}"
    save_dir="results/${label}/${MODEL}"
    mkdir -p "${save_dir}"
    for bugname in $(ls -d ${DATA_DIR}/*/ | xargs -n1 basename | grep ${PROJECT}); do
        save_file="${save_dir}/XFL-${bugname}.json"
        if [ -f ${save_file} ]; then
            echo "${save_file} exists"
            continue
        fi
        if [ -f "${DATA_DIR}/${bugname}/snippet.json" ]; then
            cmd="python autofl.py -m ${MODEL} -e ${ENDPOINT} -b ${bugname} -p ${PROMPT_FILE} -o ${save_file} --max_budget ${BUDGET} --max_num_tests ${NUM_TESTS} --show_line_number --postprocess_test_snippet --allow_multi_predictions --test_offset $((rep - 1))"
            echo ${cmd}
            ${cmd}
        fi
    done
done
