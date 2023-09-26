# AutoFL

## Python dependencies
Compatible with Python >= 3.10

```shell
python -m pip install pandas python-dotenv tqdm markdown2 tiktoken openai javalang-ext scipy numpy matplotlib
```

## OpenAI API setup
```shell
echo "OPENAI_API_KEY={YOUR_API_KEY}" > .env
echo "OPENAI_ORG_KEY={YOUR_ORG_KEY}" >> .env # optional
```

`.env` should look like:
```
OPENAI_API_KEY=<YOUR_API_KEY>
OPENAI_ORG_KEY<YOUR_ORG_KEY>
```

## Run AutoFL
```shell
sh runner.sh <expr_label> <num_repetitions> <dataset>

# examples
sh runner.sh D4J_AutoFL_ 5 defects4j
sh runner.sh BIP_AutoFL_ 5 bugsinpy
```

## Compute Scores
```
python compute_score.py results/D4J_AutoFL_*/gpt-3.5-turbo-0613 -l java -a -v -o results/D4J_scores.json
python compute_score.py results/BIP_AutoFL_*/gpt-3.5-turbo-0613 -l python -a -v -o results/BIP_scores.json
```