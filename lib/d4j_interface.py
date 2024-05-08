import os
import re
import json
from difflib import SequenceMatcher
from collections import defaultdict

from lib import sequence_utils, name_utils

BUG_INFO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data/defects4j/")

class D4JRepositoryInterface():
    RANGE_REGEX = "\(line (?P<beginline>\d+),col (?P<begincol>\d+)\)-\(line (?P<endline>\d+),col (?P<endcol>\d+)\)"
    FUNCTION_DESCRIPTIONS = [
        {
            "name": "get_failing_tests_covered_classes",
            "description": "This function retrieves a set of classes covered by failing tests and groups them by their package names.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "return": {
                "type": "object",
                "additionalProperties": {
                    "type": "dictionary",
                    "items": {
                        "type": "string",
                        "description": "The simple class name belonging to the package."
                    }
                },
                "description": "A dictionary where keys are package names, and values are lists of simple class names belonging to that package."
            }
        },
        {
            "name": "get_failing_tests_covered_methods_for_class",
            "description": "This function takes a class_name as input and returns a list of method names covered by failing tests for the specified class in the program under test.",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "The method name of the class in the program under test, e.g., \"com.example.myapp.MyClass\"."
                    }
                },
                "required": ["class_name"]
            },
            "return": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "The method signature."
                }
            }
        },
        {
            "name": "get_code_snippet",
            "description": "This function takes a signature as input and returns the corresponding code snippet for the method or field.",
            "parameters": {
                "type": "object",
                "properties": {
                "signature": {
                    "type": "string",
                    "description": "The signature of the method/field to retrieve the code snippet for. e.g. \"com.example.myapp.MyClass.MyMethod(com.example.myapp.MyArgClass)\" or \"com.example.myapp.MyClass.MyField\""
                }
                },
                "required": ["signature"]
            },
            "return": {
                "type": "string",
                "description": "The code snippet for the specified method or field, or the error message if the signature is not found."
            }
        },
        {
            "name": "get_comments",
            "description": "This function takes a signature as input and returns JavaDoc documentation (if available) for the method or field.",
            "parameters": {
                "type": "object",
                "properties": {
                "signature": {
                    "type": "string",
                    "description": "The signature of the method/field to retrieve the documentation for."
                }
                },
                "required": ["signature"]
            },
            "return": {
                "type": "string",
                "description": "The comment/documentation for the specified method or field, or the error message if the signature is not found."
            }
        }
    ]

    def __init__(self, bug_name, show_line_number=True, postprocess_test_snippet=True, max_repetition_in_stack=5):
        self._method_lists = self._load_method_lists(bug_name)
        self._buggy_methods = [
            method["signature"] for method in self._method_lists if method["is_bug"]
        ]
        self._show_line_number = show_line_number
        self._postprocess_test_snippet = postprocess_test_snippet
        self._max_repetition_in_stack = max_repetition_in_stack
        self._fail_info = self._load_fail_info(bug_name)   # dict(test_signature: error message and stack trace)
        self._test_lists = self._load_test_lists(bug_name) # list of dict
        self._field_lists = self._load_field_lists(bug_name) # list of dict
        self.language = 'java'
        self.initial_coverage_getter = "get_failing_tests_covered_classes"


    def _load_fail_info(self, bug_name):
        fail_info = dict()
        with open(os.path.join(BUG_INFO_DIR, bug_name, "failing_tests")) as f:
            for l in f:
                if l.startswith("--- "):
                    tc_name = l.split()[-1]
                    tc_signature = tc_name.replace("::", ".") + "()"
                    fail_info[tc_signature] = {"error_message": "", "stack_trace": ""}
                else:
                    fail_info[tc_signature][
                        "stack_trace" if l.startswith("\tat") else "error_message"] += l
        return fail_info

    def _load_method_lists(self, bug_name):
        with open(os.path.join(BUG_INFO_DIR, bug_name, "snippet.json")) as f:
            method_list = json.load(f)
        return method_list

    def _load_test_lists(self, bug_name):
        with open(os.path.join(BUG_INFO_DIR, bug_name, "test_snippet.json")) as f:
            test_list = json.load(f)
        return test_list

    def _load_field_lists(self, bug_name):
        with open(os.path.join(BUG_INFO_DIR, bug_name, "field_snippet.json")) as f:
            field_list = json.load(f)
        return field_list

    @property
    def method_signatures(self):
        return [method['signature'] for method in self._method_lists]

    @property
    def field_signatures(self):
        return [field['signature'] for field in self._field_lists]

    @property
    def test_signatures(self):
        return [test['signature'] for test in self._test_lists]

    @property
    def buggy_method_signatures(self):
        return self._buggy_methods

    @property
    def failing_test_signatures(self):
        return list(self._fail_info.keys())

    def get_matching_method_signatures(self, pred_expr, matcher=name_utils.lenient_matcher):
        return [
            signature for signature in self.method_signatures
            if matcher(pred_expr, signature)
        ]

    def get_method_info(self, method_signature):
        for method in self._method_lists:
            if method_signature == method["signature"]:
                return method
        return None

    def get_fail_info(self, tc_signature, minimize=False, verbose=False):
        def _clean_error_message(error_message, max_lines=5, verbose=False):
            error_message = "\n".join(error_message.splitlines()[:max_lines])
            return error_message

        def _clean_stack_trace(stack_trace, verbose=False):
            '''Returns cleaned stack that does not contain:
            (1) stack entries that start with junit.framework
            (2) stack entries below the sun.reflect.NativeMethodAccessorImpl.invoke0'''

            raw_stack = stack_trace.splitlines()

            cleaned_stack = []
            for line in raw_stack:
                if 'sun.reflect.NativeMethodAccessorImpl.invoke0' in line:
                    break
                if not ('junit.framework' in line):
                    cleaned_stack.append(line)

            # reduce repeated subsequences
            repeated_subseq = sequence_utils.repeated_subsequences(cleaned_stack,
                min_repetition=self._max_repetition_in_stack + 1)
            while repeated_subseq:
                maxlen_subseq = repeated_subseq[0]
                if verbose:
                    print(f"{maxlen_subseq['subsequence']} repeated {maxlen_subseq['num_repetition']} times")

                reduced_stack = cleaned_stack[:maxlen_subseq["start"]]
                reduced_stack += maxlen_subseq['subsequence']
                reduced_stack += [f'... (same pattern repeats {maxlen_subseq["num_repetition"]-2} more times) ...']
                reduced_stack += maxlen_subseq['subsequence']
                if maxlen_subseq["end"]+1 < len(cleaned_stack):
                    reduced_stack += cleaned_stack[maxlen_subseq["end"]+1:]
                cleaned_stack = reduced_stack
                repeated_subseq = sequence_utils.repeated_subsequences(cleaned_stack, min_repetition=self._max_repetition_in_stack+1)

            return "\n".join(cleaned_stack)

        error_message = self._fail_info[tc_signature]["error_message"].rstrip()
        stack_trace = self._fail_info[tc_signature]["stack_trace"].rstrip()

        if minimize:
            error_message = _clean_error_message(error_message, verbose=verbose)
            stack_trace = _clean_stack_trace(stack_trace, verbose=verbose)

        return error_message + "\n" + stack_trace

    ################################################################################################
    #                                        DEBUG API                                             #
    ################################################################################################

    @staticmethod
    def get_highest_priority_candidates(pred_expr: str, candidates: list,
                                        num_max_candidates:int=None):
        def _compute_similarity(method_name_1, arg_types_1, method_name_2, arg_types_2):
            # (method name similarity , short name matching, arg type similarity)
            return (
                SequenceMatcher(None, method_name_1, method_name_2).ratio(),
                method_name_1[-1] == method_name_2[-1],
                SequenceMatcher(None, arg_types_1, arg_types_2).ratio()
            )

        def _get_priority(method_similarity: float, short_name_match: bool,
                          arg_type_similarity: float):
            if method_similarity == 1.0:
                assert short_name_match
                priority = 0 if arg_type_similarity == 1.0 else 1
            else:
                priority = 2 if short_name_match else 3
            return priority

        assert len(candidates) > 0

        pred_method_name, pred_arg_types = name_utils.get_method_name_and_argument_types(pred_expr)
        similarities = defaultdict(list)
        for candidate in candidates:
            cand_method_name, cand_arg_types = name_utils.get_method_name_and_argument_types(candidate)
            similarity = _compute_similarity(pred_method_name, pred_arg_types,
                                            cand_method_name, cand_arg_types)
            priority = _get_priority(*similarity)
            similarities[priority].append((similarity, candidate))
        assert sum(len(v) for v in similarities.values()) == len(candidates)
        assert len(similarities) > 0

        highest_priority = min(similarities.keys())
        candidates = list(map(lambda t: t[1],
                              sorted(similarities[highest_priority], key=lambda t: t[0], reverse=True)))
        if num_max_candidates is not None:
            candidates = candidates[:num_max_candidates]
        return highest_priority, candidates

    def get_matching_method_or_candidates(self, pred_expr: str,
                                                include_methods:bool=True,
                                                include_tests:bool=False,
                                                num_max_candidates:int=None) -> tuple:
        # return (method, None) or (None, list of high_priority_candidates)
        assert include_methods or include_tests
        candidates = {}

        short_method_name = name_utils.get_method_name(pred_expr)

        search_lists = []
        if include_methods:
            search_lists += self._method_lists
        if include_tests:
            search_lists += self._test_lists

        for method in search_lists:
            if name_utils.lenient_matcher(pred_expr, method['signature']):
                return (method, None)
            if short_method_name in method["signature"]:
                candidates[method["signature"]] = method

        if len(candidates) == 0:
            return None, []

        # get highest priority candidates
        priority, candidate_signatures = self.__class__.get_highest_priority_candidates(
            pred_expr, list(candidates.keys()), num_max_candidates=num_max_candidates)

        assert (num_max_candidates is None or
                len(candidate_signatures) <= num_max_candidates)

        if priority == 0 and len(candidate_signatures) == 1:
            # exact match
            return (candidates[candidate_signatures[0]], None)
        else:
            return (None, [candidates[sig] for sig in candidate_signatures])

    def get_failing_tests_covered_classes(self):
        classes = set([m["class_name"] for m in self._method_lists])
        grouped_by_packages = defaultdict(list)
        for cls in classes:
            grouped_by_packages[name_utils.drop_base_name(cls)].append(name_utils.get_base_name(cls))
        return grouped_by_packages

    def get_failing_tests_covered_methods_for_class(self, class_name):
        methods = [
            method["signature"].removeprefix(class_name)
            for method in self._method_lists if method["class_name"] == class_name
        ]

        if methods:
            return methods
        elif any(class_name in test['signature'] for test in self._test_lists):
            return {'error_message': 'You can obtain test-related information via the `get_code_snippet()` function.'}
        else:
            return {"error_message": f"No method information available for the class: {class_name}. The available class names can be found by calling get_failing_tests_covered_classes()."}

    def get_code_snippet(self, signature, num_max_candidates=5):
        def _display_snippet(component): # either field or method/constructor in SUT
            if self._show_line_number:
                line_numbers = range(int(component["begin_line"]), int(component["end_line"])+1)
                lines_with_lineno = sequence_utils.concat_strings(
                    line_numbers, component["snippet"].splitlines(), sep=" : ", align=True)
                return "\n".join(lines_with_lineno)
            else:
                return component["snippet"]

        if signature in self.field_signatures:
            return _display_snippet(self._field_lists[self.field_signatures.index(signature)])

        method, candidates = self.get_matching_method_or_candidates(
            signature, include_methods=True, include_tests=True,
            num_max_candidates=num_max_candidates
        )

        if method:
            if method['signature'] in self.test_signatures:
                # redirect
                return self.get_test_snippet(method['signature'])
            else:
                return _display_snippet(method)

        if len(candidates) == 0 and not name_utils.is_method_signature(signature):
            # add field candidates if exists
            candidates = [field for field in self._field_lists if name_utils.get_base_name(signature) in field["signature"]][:num_max_candidates]

        if len(candidates) == 0:
            return {"error_message": f"No components with the name {name_utils.get_method_name(signature)} were found. It may not be covered by the failing tests. Please try something else."}
        elif len(candidates) == 1:
            unique_candidate = candidates[0]
            if unique_candidate['signature'] in self.test_signatures:
                snippet = self.get_test_snippet(unique_candidate['signature'])
            else:
                snippet = _display_snippet(unique_candidate)
            return f"You probably mean {unique_candidate['signature']}. It looks like:\n```java\n{snippet}\n```"
        else:
            func_calls = set([f'get_code_snippet({method["signature"]})' for method in candidates])
            return {"error_message": f"There are multiple matches to that query. Do you mean any of the following: {func_calls}?"}

    def get_comments(self, signature, num_max_candidates=5):
        if signature in self.field_signatures:
            return self._field_lists[self.field_signatures.index(signature)]["comment"]

        method, candidates = self.get_matching_method_or_candidates(
            signature, include_tests=True, num_max_candidates=num_max_candidates
        )

        if method:
            return method["comment"]

        if len(candidates) == 0 and not name_utils.is_method_signature(signature):
            # add field candidates if exists
            candidates = [field for field in self._field_lists if name_utils.get_base_name(signature) in field["signature"]][:num_max_candidates]

        if len(candidates) == 0:
            return {"error_message": f"No methods with the name {name_utils.get_method_name(signature)} were found. Please try something else."}
        elif len(candidates) == 1:
            unique_candidate = candidates[0]
            return f"You probably mean {unique_candidate['signature']}. It looks like:\n```java\n{unique_candidate['comment']}\n```"
        else:
            func_calls = set([f'get_comments({method["signature"]})' for method in candidates])
            return {"error_message": f"There are multiple matches to that query. Do you mean any of the following: {func_calls}?"}

    def get_test_snippet(self, signature):
        def _get_error_location(signature, fail_info):
            """
            Extracts the line number from the provided failure information related to a test case.

            Parameters:
                signature (str): The name of the test case in the format 'package.ClassName.test_method()'.
                fail_info (str): The failure information containing the stack trace with error details.

            Returns:
                int: The line number where the error occurred within the test method.

            Example:
                signature = 'org.jfree.data.general.junit.DatasetUtilitiesTests.testBug2849731_2()'
                fail_info = 'java.lang.NullPointerException\n\tat org.jfree.data.general.junit.DatasetUtilitiesTests.testBug2849731_2(DatasetUtilitiesTests.java:1276)'
                _get_error_location(signature, fail_info)
                Output: 1276

            Note:
                This function assumes that the provided 'fail_info' follows the standard Java stack trace format,
                where each line starts with '\tat' followed by the method name and file location in parentheses.
                It specifically looks for lines starting with '\tat' followed by the test method's fully-qualified name
                (obtained from 'signature') and extracts the line number from that line using regular expressions.
            """
            method_name = name_utils.get_method_name(signature, simple_name=False)
            for line in fail_info.splitlines():
                if not line.startswith("\tat"):
                    continue
                m = re.match(f"\tat (.*)\(.*:(\d+)\)", line)
                """
                line: '\tat org.jfree.data.general.junit.DatasetUtilitiesTests.testBug2849731_2(DatasetUtilitiesTests.java:1276)'
                group(0): org.jfree.data.general.junit.DatasetUtilitiesTests.testBug2849731_2
                group(1): 1276
                """
                if m is None or m.group(1) != method_name:
                    continue
                line_number = m.group(2)
                return int(line_number)
            return None # not found

        parents = list()
        matching_test_case = None
        test_class_name = name_utils.drop_base_name(
            name_utils.get_method_name(signature, simple_name=False))
        for test_case in self._test_lists:
            if signature == test_case["signature"]: # exact matching
                matching_test_case = test_case
                break
            if name_utils.get_method_name(signature) == name_utils.get_method_name(test_case["signature"]): # short method name matching
                if test_class_name in test_case["child_classes"]:
                    parents.append((len(test_case["child_classes"]), test_case)) # tuple(# childs, classname)

        if matching_test_case is None: # when the signature is not available
            if parents:
                matching_test_case = sorted(parents)[0][1]
            else:
                return None # not found

        test_case = matching_test_case
        snippet = test_case["snippet"]
        begin_lineno = int(test_case["begin_line"])

        if signature in self._fail_info and self._postprocess_test_snippet:
            # if the test is failed and the postprocessing is on,
            # find and annotate error location
            error_lineno = _get_error_location(test_case["signature"], # name of actual matching test case
                                               self.get_fail_info(signature, minimize=False))
            annotate_error_location = error_lineno is not None
        else:
            annotate_error_location = False

        if annotate_error_location:
            # find line ranges containing the error location and previous assertions
            assertion_line_numbers = []
            snippet_raw_lines = snippet.splitlines()

            for child_range in test_case["child_ranges"]:
                m = re.match(self.__class__.RANGE_REGEX, child_range)
                range_info = m.groupdict()
                child_begin_lineno, child_end_lineno = int(range_info["beginline"]), int(range_info["endline"])
                range_statement = "\n".join(
                    snippet_raw_lines[child_begin_lineno-begin_lineno:child_end_lineno-begin_lineno+1]
                )
                if child_begin_lineno <= error_lineno <= child_end_lineno:
                    error_end_lineno = child_end_lineno
                if (range_statement.lstrip().startswith('assert') and
                    child_end_lineno < error_lineno): # save previous assertion locs
                    assertion_line_numbers += list(range(child_begin_lineno, child_end_lineno+1))
                last_lineno = child_end_lineno # actual last line of test

            # 1. trim (1) - remove lines that come after failure location
            snippet_lines = snippet_raw_lines[:error_end_lineno-begin_lineno+1]
            #    trim (2) - remove previous assertion statements
            line_numbers = [lineno
                            for lineno in range(begin_lineno, begin_lineno + len(snippet_lines))
                            if lineno not in assertion_line_numbers]
            removed_count = len(assertion_line_numbers)
            snippet_lines = [snippet_lines[lineno-begin_lineno] for lineno in line_numbers]
            # 2. annotate
            error_index = error_lineno-begin_lineno-removed_count
            snippet_lines[error_index] = snippet_lines[error_index] + " // error occurred here"
            # 3. closing
            snippet_lines += snippet_raw_lines[last_lineno-begin_lineno+1:]
            line_numbers += list(range(last_lineno+1,len(snippet_raw_lines)+begin_lineno))
        else:
            snippet_lines = snippet.splitlines()
            line_numbers = range(begin_lineno, begin_lineno + len(snippet_lines))

        # append line numbers
        if self._show_line_number:
            snippet_lines = sequence_utils.concat_strings(
                line_numbers, snippet_lines, sep=" : ", align=True)

        return "\n".join(snippet_lines)
    
    ## Meta Functions
    @property
    def function_descriptions(self):
        return self.__class__.FUNCTION_DESCRIPTIONS
    
    @property
    def fname2func(self):
        fname2func = {
            "get_failing_tests_covered_classes": self.get_failing_tests_covered_classes,
            "get_failing_tests_covered_methods_for_class": self.get_failing_tests_covered_methods_for_class,
            "get_code_snippet": self.get_code_snippet,
            "get_comments": self.get_comments,
        }
        assert len(self.function_descriptions) == len(fname2func)
        return fname2func
