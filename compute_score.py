import json
import os
import argparse
import re
import collections
from tqdm import tqdm
from copy import deepcopy
from lib.repo_interface import get_repo_interface

import ast
import javalang
from lib.name_utils import get_method_name

def file2bug(json_file):
    if not json_file.endswith(".json"):
        return None
    try:
        return os.path.basename(json_file).removeprefix('XFL-').removesuffix('.json')
    except:
        return None

def get_prediction_status(raw_prediction):
    if isinstance(raw_prediction, str): # buggy_methods = error message
        error_message = raw_prediction
        if "openai.error.InvalidRequestError" not in error_message:
            return "OtherError"
        else:
            return "InvalidRequestError"
    else:
        return "OK"

def parse_response(response):
    return [
        expr.removeprefix('`').removesuffix('`')
        for expr in response.strip().splitlines()
    ] if response else []

def print_divider():
    print("-"*50)

def compute_autofl_scores(result_dirs, project=None, verbose=False):
    json_status = {}
    score_results = {}
    no_pred_runs = {}
    for result_dir in result_dirs:
        file_iterator = sorted(os.listdir(result_dir))
        if verbose:
            print(f"Processing {result_dir}...")
            file_iterator = tqdm(file_iterator)
        for fname in file_iterator:
            bug_name = file2bug(fname)
            if bug_name is None:
                continue            
            if project and not bug_name.startswith(project):
                continue

            json_status[bug_name] = json_status.get(bug_name, {"OK": [], "OtherError": [], "InvalidRequestError": []}) # status -> list
            score_results[bug_name] = score_results.get(bug_name, {})   # method -> score info
            status_result, score_result = json_status[bug_name], score_results[bug_name]
    
            fpath = os.path.join(result_dir, fname)
            with open(fpath, 'r') as f:
                autofl_data = json.load(f)

            prediction = autofl_data["buggy_methods"]
            pred_status = get_prediction_status(prediction)

            status_result[pred_status] = status_result.get(pred_status, [])
            status_result[pred_status].append(fpath)

            if pred_status != "OK":
                """
                Status Check (Normal or Error)
                """
                if verbose and pred_status == "OtherError":
                    print(fpath)
                    print_divider()
                    print(prediction)
                    print_divider()

            """
            Get LLM answer
            """
            final_response = autofl_data["messages"][-1]["content"]
            pred_exprs = parse_response(final_response)

            """
            Scoring
            """

            # 1. Initialize
            ri = get_repo_interface(bug_name)

            # 2. Get mactching methods
            predicted_methods = {}
            for pred_expr in pred_exprs:
                for method in ri.get_matching_method_signatures(pred_expr):
                    predicted_methods[method] = predicted_methods.get(method, [])
                    predicted_methods[method].append(pred_expr)

            if not predicted_methods:
                no_pred_runs[bug_name] = no_pred_runs.get(bug_name, 0) + 1
                continue

            # 3. Assign scores
            # Evenly distribute the score "1" to all matching methods 
            for method in predicted_methods:
                if method not in score_result:
                    score_result[method] = {
                        "score": 0, "count": 0, "exprs": {},
                    }
                score_result[method]["count"] += 1
                score_result[method]["score"] += 1/len(predicted_methods)
                score_result[method]["exprs"][fpath] = predicted_methods[method]

    for bug_name in score_results:
        # If there are no methods that are matched with the predictions
        # Evenly distribute the score "1" to all methods 
        ri = get_repo_interface(bug_name)
        all_methods = ri.method_signatures
        score_result = score_results[bug_name]
        num_all_runs = sum([len(json_status[bug_name][s]) for s in json_status[bug_name]])
        #num_OK_runs = len(json_status[bug_name]["OK"])

        for method in sorted(all_methods): # lexical sort
            if method not in score_result:
                score_result[method] = {
                    "score": 0, "count": 0, "exprs": {},
                }
            score_result[method]["score"] /= num_all_runs
            # score_result[method]["score"] += num_error_runs/len(all_methods)

    if verbose:
        for bug_name in json_status:
            print(bug_name, {s: len(json_status[bug_name][s]) for s in json_status[bug_name]})

    return json_status, score_results

def get_seen_methods_from_msgs(ri, messages, language):
    seen_method_sigs = list(map(
        lambda msg: json.loads(msg['function_call']['arguments'])['signature'],
        filter(
            lambda msg: 'function_call' in msg \
                and msg['function_call']['name'] in ('get_code_snippet', 'get_comments'), 
            messages
        )
    ))
    all_seen_method_names = []

    for msg in messages:
        if msg['role'] == 'user':
            content_data = msg['content']
            if f"```{language}" not in content_data:
                continue
        elif msg['role'] == 'function' and msg['name'] == 'get_code_snippet':
            content_data = json.loads(msg['content'])
        else:
            continue
    
        if type(content_data) != str:
            continue

        norm_content = ''
        for line in content_data.splitlines():
            norm_content += re.sub(r'^\s*\d+\s\:\s', '', line) + '\n'
        if '```' in norm_content:
            assert norm_content.count('```') % 2 == 0
            norm_content = norm_content.split('```')[1].lstrip(language)

        if language == "java":
            try:
                parsed_method = javalang.parse.parse(norm_content)
            except javalang.parser.JavaSyntaxError:
                continue
            method_call_nodes = [e[1] for e in parsed_method.filter(javalang.tree.MethodInvocation)]
            all_seen_method_names += [e.member for e in method_call_nodes]
        elif language == "python":
            try:
                parsed_method = ast.parse(norm_content)
            except SyntaxError:
                continue
            method_call_nodes = [e for e in ast.walk(parsed_method) if isinstance(e, ast.Call)]
            all_seen_method_names += [ast.unparse(e.func) for e in method_call_nodes]
        else:
            raise Exception()

    candidates = {}
    for seen_method in all_seen_method_names:
        # search for covered methods that match name
        seen_exact_match, seen_match_candidates = ri.get_matching_method_or_candidates(seen_method+'()')
        if seen_match_candidates is not None:
            candidates[seen_method] = candidates.get(
                seen_method,
                [m["signature"] for m in seen_match_candidates]
            )
        else:
            candidates[seen_method] = candidates.get(
                seen_method, seen_exact_match["signature"]
            )
        seen_method_sigs += [
            sig for sig in candidates[seen_method] if get_method_name(sig)==seen_method]
    return seen_method_sigs

def add_auxiliary_scores(json_files, autofl_scores, language, default_aux_score=None,
                         verbose=False):
    autofl_scores_aug = deepcopy(autofl_scores)

    bug_name_iterator = autofl_scores_aug.keys()
    if verbose:
        print("Computing auxiliary scores...")
        bug_name_iterator = tqdm(bug_name_iterator)

    for bug_name in bug_name_iterator:
        # Set up
        ri = get_repo_interface(bug_name)

        # 1. get num failing tests
        if language == 'java':
            snippet_path = f"data/defects4j/{bug_name}/snippet.json"
        elif language == 'python':
            snippet_path = f"data/bugsinpy/{bug_name}/snippet.json"
        else:
            raise ValueError(f'Unknown language {language}')

        with open(snippet_path, "r") as f:
            method_data = json.load(f)
            num_failing_tests = {
                m["signature"]: m["num_failing_tests"] if "num_failing_tests" in m else 0
                for m in method_data
            }

        # print(bug_name)
        # print(num_failing_tests)
        # 2. get seen messages
        seen_methods = []
        for fpath in json_files[bug_name]["OK"]:
            with open(fpath, 'r') as f:
                autofl_data = json.load(f)
            messages = autofl_data["messages"]
            seen_methods += get_seen_methods_from_msgs(ri, messages, language)
        seen_method_counter = collections.Counter(seen_methods)

        for method in autofl_scores_aug[bug_name]:
            if default_aux_score is None:
                if autofl_scores_aug[bug_name][method]["count"] > 0:
                    aux_score = (num_failing_tests[method], 0) #seen_method_counter[method])
                else:
                    aux_score = (
                        num_failing_tests[method],
                        seen_method_counter[method]
                    )
                autofl_scores_aug[bug_name][method]["aux_score"] = aux_score
            else:
                aux_score = default_aux_score
            assert isinstance(aux_score, tuple) or isinstance(aux_score, list) or isinstance(aux_score, float) or isinstance(aux_score, int)
            autofl_scores_aug[bug_name][method]["aux_score"] = aux_score
    return autofl_scores_aug

def assign_rank(autofl_scores):
    autofl_scores_rank = deepcopy(autofl_scores)
    for bug_name in autofl_scores_rank:
        sort_keys = [] # (-score, -aux, index) 
        for i, method in enumerate(autofl_scores_rank[bug_name]):
            score = autofl_scores_rank[bug_name][method]["score"]
            sort_key = [-score]
            aux_score = autofl_scores_rank[bug_name][method]["aux_score"]
            if isinstance(aux_score, tuple) or isinstance(aux_score, list):
                sort_key += list([-s for s in aux_score])
            elif isinstance(aux_score, float) or isinstance(aux_score, int):
                sort_key.append(-aux_score)
            else:
                raise Exception(f"Unsupported aux score type: {aux_score}")
            sort_key += [i, method]
            sort_keys.append(tuple(sort_key))
        for r, sort_item in enumerate(sorted(sort_keys)):
            method = sort_item[-1]
            autofl_scores_rank[bug_name][method]["rank"] = r + 1
    return autofl_scores_rank

def get_buggy_method_ranks(method_scores, key="autofl_rank"):
    buggy_method_ranks = {}
    for bug_name in method_scores:
        ri = get_repo_interface(bug_name)
        buggy_method_ranks[bug_name] = {}
        for method in ri.buggy_method_signatures:
            rank = method_scores[bug_name][method]["rank"] if method in method_scores[bug_name] else None
            buggy_method_ranks[bug_name][method] = {key: rank}
    return buggy_method_ranks

def calculate_acc(buggy_method_ranks, key="autofl_rank", n=1):
    acc = 0
    for bug_name in buggy_method_ranks:
        ranks = [
            buggy_method_ranks[bug_name][method][key]
            for method in buggy_method_ranks[bug_name]
        ]
        assert None not in ranks
        if any([r <= n for r in ranks]):
            acc += 1
    return acc

def calculate_confidence(method_scores):
    confidence = {}
    for bug_name in method_scores:
        scores = [
            method_scores[bug_name][method]["score"]
            for method in method_scores[bug_name]
        ]
        if scores:
            confidence[bug_name] = max(scores)
        else:
            confidence[bug_name] = None
    return confidence

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('result_dirs', nargs="+", type=str)
    parser.add_argument('--output', '-o', type=str, default="scores.json")
    parser.add_argument('--project', '-p', type=str, default=None)
    parser.add_argument('--language', '-l', type=str, default="java")
    parser.add_argument('--verbose', '-v', action="store_true")
    parser.add_argument('--minimize', '-m', action="store_true")
    parser.add_argument('--aux', '-a', action="store_true")
    args = parser.parse_args()
    assert args.language in ["java", "python"]

    json_files, autofl_scores = compute_autofl_scores(args.result_dirs, args.project, args.verbose)

    if args.aux:
        method_scores = add_auxiliary_scores(json_files, autofl_scores, args.language,
                                             verbose=args.verbose)
    else:
        method_scores = add_auxiliary_scores(json_files, autofl_scores, args.language, 
                                             default_aux_score=0, verbose=args.verbose)
    
    method_scores = assign_rank(method_scores)

    buggy_method_ranks = get_buggy_method_ranks(method_scores, key="autofl_rank")

    confidence = calculate_confidence(method_scores)

    # summarize the results
    summary = {"total": len(method_scores)}
    for n in range(1, 11):
        summary[f"acc@{n}"] = calculate_acc(buggy_method_ranks, key="autofl_rank", n=n)
    print(json.dumps(summary, indent=4))


    data = {
        "summary": summary,
        "buggy_methods": buggy_method_ranks,
        "confidence": confidence,
    }
    if not args.minimize:
        data["predictions"] = method_scores

    with open(args.output, "w") as f:
        json.dump(data, f, indent=4)
