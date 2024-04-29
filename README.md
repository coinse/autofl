# AutoFL

<div align="center">
<img src="./assets/AutoFL_logo_DALLE.png" width="300px"/>
</div>

> This artifact accompanies the paper **_A Quantitative and Qualitative Evaluation of LLM-based Explainable Fault Localization_** accepted to FSE'24.

# Environmental Setup
## Python Dependencies
- Compatible with Python >= 3.10
- Compatible with `openai>=0.27.8,<=0.28.1` (not compatible with `openai>=1.0.0`)

Install the required dependencies using the following command:

```shell
python -m pip install pandas python-dotenv tqdm markdown2 tiktoken "openai>=0.27.8,<=0.28.1" javalang-ext scipy numpy matplotlib jupyter seaborn nbformat
```

## OpenAI API Setup
Before using AutoFL, set up your OpenAI API credentials by creating a `.env` file with the following content:

```shell
OPENAI_API_KEY={YOUR_API_KEY}
OPENAI_ORG_KEY={YOUR_ORG_KEY} # Optional
```
Replace `{YOUR_API_KEY}` with your OpenAI API key and `{YOUR_ORG_KEY}` with your organization's API key.

# Guide to Reproduction

## 0. Raw Data Files
- `./results/{label}/{model}/XFL-{bugname}.json`: the `AutoFL` results
- `./results/{label}/{model}/downstream_*`: the interaction data with LLM for the downstream tasks (APR and Test Generation)
  - The summary of the evaluation results can be found at `notebooks/resources/[APR|TestGen]_results.csv`.
- `./combined_fl_results`: minimized version of AutoFL + ablation results

## 1. Generate Detailed AutoFL Results Files

To obtain comprehensive AutoFL results files, please execute the following command:
```shell
sh compute_scores.sh
```
Running this command will generate complete score data files (`*_full.json`) within the `combined_fl_results` directory, utilizing the raw data sourced from the `results` directory.

## 2. Reproduce Results in the Paper

- After generating the comprehensive FL results files, the figures in the paper can be reproduced via the Jupyter notebook files within the directory [`./notebooks`](./notebooks/).
  - Any necessary files for the analysis are included in the directory [`./notebooks/resources`](./notebooks/resources/)
  - If you execute the notebooks, the figures will be saved to [`./notebooks/figures`](./notebooks/figures/).


# General Usage

## Run AutoFL

To run AutoFL, use the following command:
```shell
sh runner.sh {expr_label} {num_repetitions} {dataset}
```

Replace `{expr_label}` with a label for your experiment, `{num_repetitions}` with the number of repetitions (`R` in the paper), and `{dataset}` with the dataset you want to use (`defects4j` or `bugsinpy`).

## Compute Scores
```shell
python compute_score.py {result_directories} -l {java|python} -a -v -o {json_output_file}
```

`{result_directories}` should be the directories containing your AutoFL result files.
- `-l` specifies the language (either `java` or `python`).
- `-a` enables the use of auxiliary scores to break ties.
- `-v` enables verbose mode.
- `-o` specifies the path to the JSON output file.

## Examples

- Defects4J
    ```shell
    sh runner.sh my_d4j_autofl_ 5 defects4j
    python compute_score.py results/my_d4j_autofl_*/gpt-3.5-turbo-0613 -l java -a -v -o d4j_scores.json
    ```
- BugsInPy
    ```shell
    sh runner.sh my_bip_autofl_ 5 bugsinpy
    python compute_score.py results/my_bip_autofl_*/gpt-3.5-turbo-0613 -l python -a -v -o bip_scores.json
    ```
