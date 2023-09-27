[ ! -d combined_fl_results ] && mkdir combined_fl_results

# Defects4J (AUTOFL-GPT-3.5)
python compute_score.py \
    results/d4j_autofl_1/gpt-3.5-turbo-0613 \
    -l java -a -v -o combined_fl_results/d4j_gpt3_results_R1_full.json

python compute_score.py \
    results/d4j_autofl_1/gpt-3.5-turbo-0613 \
    results/d4j_autofl_2/gpt-3.5-turbo-0613 \
    -l java -a -v -o combined_fl_results/d4j_gpt3_results_R2_full.json

python compute_score.py \
    results/d4j_autofl_1/gpt-3.5-turbo-0613 \
    results/d4j_autofl_2/gpt-3.5-turbo-0613 \
    results/d4j_autofl_3/gpt-3.5-turbo-0613 \
    -l java -a -v -o combined_fl_results/d4j_gpt3_results_R3_full.json

python compute_score.py \
    results/d4j_autofl_1/gpt-3.5-turbo-0613 \
    results/d4j_autofl_2/gpt-3.5-turbo-0613 \
    results/d4j_autofl_3/gpt-3.5-turbo-0613 \
    results/d4j_autofl_4/gpt-3.5-turbo-0613 \
    -l java -a -v -o combined_fl_results/d4j_gpt3_results_R4_full.json

python compute_score.py \
    results/d4j_autofl_1/gpt-3.5-turbo-0613 \
    results/d4j_autofl_2/gpt-3.5-turbo-0613 \
    results/d4j_autofl_3/gpt-3.5-turbo-0613 \
    results/d4j_autofl_4/gpt-3.5-turbo-0613 \
    results/d4j_autofl_5/gpt-3.5-turbo-0613 \
    -l java -a -v -o combined_fl_results/d4j_gpt3_results_R5_full.json

# Defects4J (AUTOFL-GPT-4)
python compute_score.py \
    results/d4j_autofl_1/gpt-4-0613 \
    -l java -a -v -o combined_fl_results/d4j_gpt4_results_R1_full.json

python compute_score.py \
    results/d4j_autofl_1/gpt-4-0613 \
    results/d4j_autofl_2/gpt-4-0613 \
    -l java -a -v -o combined_fl_results/d4j_gpt4_results_R2_full.json

# Defects4J (LLM-Test)
python compute_score.py \
    results/d4j_llmtest_1/gpt-3.5-turbo-0613 \
    results/d4j_llmtest_2/gpt-3.5-turbo-0613 \
    results/d4j_llmtest_3/gpt-3.5-turbo-0613 \
    results/d4j_llmtest_4/gpt-3.5-turbo-0613 \
    results/d4j_llmtest_5/gpt-3.5-turbo-0613 \
    -l java -a -v -o combined_fl_results/d4j_llmtest_results_full.json

# BugsInPy (AUTOFL-GPT-3.5)
python compute_score.py \
    results/bip_autofl_1/gpt-3.5-turbo-0613 \
    -l python -a -v -o combined_fl_results/bip_gpt3_results_R1_full.json

python compute_score.py \
    results/bip_autofl_1/gpt-3.5-turbo-0613 \
    results/bip_autofl_2/gpt-3.5-turbo-0613 \
    -l python -a -v -o combined_fl_results/bip_gpt3_results_R2_full.json

python compute_score.py \
    results/bip_autofl_1/gpt-3.5-turbo-0613 \
    results/bip_autofl_2/gpt-3.5-turbo-0613 \
    results/bip_autofl_3/gpt-3.5-turbo-0613 \
    -l python -a -v -o combined_fl_results/bip_gpt3_results_R3_full.json

python compute_score.py \
    results/bip_autofl_1/gpt-3.5-turbo-0613 \
    results/bip_autofl_2/gpt-3.5-turbo-0613 \
    results/bip_autofl_3/gpt-3.5-turbo-0613 \
    results/bip_autofl_4/gpt-3.5-turbo-0613 \
    -l python -a -v -o combined_fl_results/bip_gpt3_results_R4_full.json

python compute_score.py \
    results/bip_autofl_1/gpt-3.5-turbo-0613 \
    results/bip_autofl_2/gpt-3.5-turbo-0613 \
    results/bip_autofl_3/gpt-3.5-turbo-0613 \
    results/bip_autofl_4/gpt-3.5-turbo-0613 \
    results/bip_autofl_5/gpt-3.5-turbo-0613 \
    -l python -a -v -o combined_fl_results/bip_gpt3_results_R5_full.json

# BugsInPy (AUTOFL-GPT-4)
python compute_score.py \
    results/bip_autofl_1/gpt-4-0613 \
    -l python -a -v -o combined_fl_results/bip_gpt4_results_R1_full.json

python compute_score.py \
    results/bip_autofl_1/gpt-4-0613 \
    results/bip_autofl_2/gpt-4-0613 \
    -l python -a -v -o combined_fl_results/bip_gpt4_results_R2_full.json

# BugsInPy (LLM-Test)
python compute_score.py \
    results/bip_llmtest_1/gpt-3.5-turbo-0613 \
    results/bip_llmtest_2/gpt-3.5-turbo-0613 \
    results/bip_llmtest_3/gpt-3.5-turbo-0613 \
    results/bip_llmtest_4/gpt-3.5-turbo-0613 \
    results/bip_llmtest_5/gpt-3.5-turbo-0613 \
    -l python -a -v -o combined_fl_results/bip_llmtest_results_full.json