sh runner.sh d4j_chart_ 1 defects4j gemma Chart
sh runner.sh d4j_chart_ 1 defects4j codellama Chart
sh runner.sh d4j_chart_ 1 defects4j llama3 Chart

sh runner.sh d4j_time_ 1 defects4j gemma Time
sh runner.sh d4j_time_ 1 defects4j codellama Time
sh runner.sh d4j_time_ 1 defects4j llama3 Time

python compute_score.py results/d4j_chart_1/gemma -l java -a -v -o chart_gemma_baseline.json
python compute_score.py results/d4j_chart_1/codellama -l java -a -v -o chart_codellama_baseline.json
python compute_score.py results/d4j_chart_1/llama3 -l java -a -v -o chart_llama3_baseline.json

python compute_score.py results/d4j_time_1/gemma -l java -a -v -o time_gemma_baseline.json
python compute_score.py results/d4j_time_1/codellama -l java -a -v -o time_codellama_baseline.json
python compute_score.py results/d4j_time_1/llama3 -l java -a -v -o time_llama3_baseline.json
