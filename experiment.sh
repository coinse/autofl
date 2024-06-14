sh runner.sh d4j_chart_single_prompt_ 1 defects4j llama3 Chart
sh runner.sh d4j_chart_single_prompt_ 1 defects4j codellama:13B Chart
sh runner.sh d4j_chart_single_prompt_ 1 defects4j codellama Chart

python compute_score.py results/d4j_chart_single_prompt_1/llama3 -l java -a -v -o combined_fl_results/chart_llama3_single_prompt.json
python compute_score.py results/d4j_chart_single_prompt_1/codellama:13B -l java -a -v -o combined_fl_results/chart_codellama13B_single_prompt.json
python compute_score.py results/d4j_chart_single_prompt_1/codellama -l java -a -v -o combined_fl_results/chart_codellama_single_prompt.json

python analyze_function_calls.py results/d4j_chart_single_prompt_1/llama3 -o function_call_patterns/chart_llama3_single_prompt
python analyze_function_calls.py results/d4j_chart_single_prompt_1/codellama:13B -o function_call_patterns/chart_codellama13b_single_prompt
python analyze_function_calls.py results/d4j_chart_single_prompt_1/codellama -o function_call_patterns/chart_codellama_single_prompt