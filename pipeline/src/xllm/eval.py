from enum import Enum

from regex import F
from torch import zero_
from src.xllm import variables
from datetime import datetime
from typing import List, Sequence, Set, Tuple, Dict, Any, get_args, get_origin
from numpy.typing import ArrayLike
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    f1_score,
    jaccard_score,
    cohen_kappa_score
)
from sklearn.preprocessing import MultiLabelBinarizer
from src.xllm.utils import normalize_date

def get_var_type(var_id):
    var_type = variables.LM_VARIABLES[var_id].type
    is_date = variables.LM_VARIABLES[var_id].is_date

    if var_type == bool:
      return "bool"
    elif var_type == str:
        if is_date:
            return "date"
    elif var_type == int:
        return "int"
    elif isinstance(var_type, type) and issubclass(var_type, Enum):
        return "enum"
    
    if not get_origin(var_type) == list:
        raise ValueError(f"Expected list type for {var_id}, got {var_type}, {get_origin(var_type)}")
    


    elif get_origin(var_type) == list:
        # is
        type_list = get_args(var_type)
        if len(type_list) == 1 and type_list[0] == str and is_date:
            return "list_string"
        elif len(type_list) == 1 and issubclass(type_list[0], Enum):
            return "list_enum"
        elif len(type_list) == 1 and isinstance(type_list[0], type):
            return "list_object"
        
    
    else:
        raise ValueError(f"Unknown type for {var_id}: {var_type}")

# evaluation.py

# ----------------------------- helpers --------------------------------- #
def _clf_metrics(y_true: ArrayLike, y_pred: ArrayLike, labels=None) -> Dict:
    """Precision, recall, F1, accuracy for a binary or multiclass task."""
    p, r, f, _ = precision_recall_fscore_support(
        # y_true, y_pred, labels=labels, average="macro", zero_division=1, 
        # y_true, y_pred, labels=labels, average="macro",
        y_true, y_pred, average="macro", zero_division=0
    )

    # if p, r or f are ndarray, error:
    if isinstance(p, np.ndarray) or isinstance(r, np.ndarray) or isinstance(f, np.ndarray):
        raise ValueError("Expected float, got ndarray")
      

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": p,
        "recall": r,
        "f1": f,
        "support": len(y_true), # type: ignore
    }


# ----------------------- 1. Boolean / Binary --------------------------- #

def norm_binary(y_true: Sequence[bool | None], y_pred: Sequence[bool | None]) -> Tuple[List[bool], List[bool]]:
    """ Normalize binary values to True/False, treating None as False."""
    y_true = [bool(x) if x is not None else False for x in y_true]
    y_pred = [bool(x) if x is not None else False for x in y_pred]
    return y_true, y_pred

def eval_binary(y_true: Sequence[bool], y_pred: Sequence[bool]) -> Dict[str, float]:
    """Boolean variables or any field already expressed as True/False."""
    return _clf_metrics(y_true, y_pred)

# ---------------------- 2. Enum (single label) ------------------------- #
def norm_multiclass(y_true: Sequence[str | None], y_pred: Sequence[str | None]) -> Tuple[List[str], List[str]]:
    """ Normalize enum values to strings, treating None as empty string."""
    y_true = [str(x) if x is not None else "" for x in y_true]
    y_pred = [str(x) if x is not None else "" for x in y_pred]
    return y_true, y_pred

def eval_multiclass(
    y_true: Sequence[str], y_pred: Sequence[str], class_labels: Sequence[str] | None = None
) -> Dict[str, float]:
    """
    Multi-class classification for enum variables.
    `class_labels` keeps metrics comparable even if some classes are missing in y_true.
    """
    # todo: sort

    return _clf_metrics(y_true, y_pred, labels=class_labels)


# ------------------ 3. Set of enums (multi‑label) ---------------------- #
def eval_multilabel(
    y_true: Sequence[Set[str]], y_pred: Sequence[Set[str]], label_space: Sequence[str]
) -> Dict:
    """
    Multi-label evaluation via Jaccard and micro/macro F1.
    `label_space` is the complete list of possible labels (needed for binarization).
    """
    y_true = [set(x) if x is not None else set([]) for x in y_true]
    y_pred = [set(x) if x is not None else set([]) for x in y_pred]



    mlb = MultiLabelBinarizer(classes=label_space)
    Y_true = mlb.fit_transform(y_true)
    Y_pred = mlb.transform(y_pred)

    jaccard = jaccard_score(Y_true, Y_pred, average="samples", zero_division=1)
    micro_f1 = f1_score(Y_true, Y_pred, average="micro", zero_division=1)
    macro_f1 = f1_score(Y_true, Y_pred, average="macro", zero_division=1)
    
    return {
        "jaccard_mean": jaccard,
        "f1_micro": micro_f1,
        "f1_macro": macro_f1,
        "support": len(y_true),
    }


# --------------- 4. Date fields (binary after tolerance) --------------- #

def norm_date(y_true: Sequence[str | None], y_pred: Sequence[str | None]) -> Tuple[List[str], List[str]]:
    """ Normalize date strings to ISO format, treating None as missing."""
    y_true = [normalize_date(x) or "" for x in y_true]
    y_pred = [normalize_date(x) or "" for x in y_pred]
    # normalize_date returns empty string for None, so we can keep it as is
    return y_true, y_pred


def eval_date(
    y_true: Sequence[str | None],
    y_pred: Sequence[str | None],
    tolerance_days: int = 30,
    date_format: str = "%Y-%m-%d",
) -> Dict[str, float]:
    """
    Date is counted correct if |Δ| ≤ tolerance_days.
    Missing predictions -> False negative; extraneous predictions -> False positive.
    """
    def _within_tol(gt: str | None, pr: str | None) -> bool:
        if gt is None and pr is None:
            return True  # treat “both missing” as correct for accuracy; drop if you prefer
        if gt and pr:
            try:
                dt_gt = datetime.strptime(gt, date_format)
                dt_pr = datetime.strptime(pr, date_format)
                return abs((dt_gt - dt_pr).days) <= tolerance_days
            except ValueError:
                return False
        return False

    y_bin_true = [gt is not None for gt in y_true]  # ground truth has a date?
    y_bin_pred = [pr is not None for pr in y_pred]  # model predicted a date?

    correct_mask = [_within_tol(gt, pr) for gt, pr in zip(y_true, y_pred)]
    accuracy_tol = sum(correct_mask) / len(correct_mask)

    cls_metrics = _clf_metrics(y_bin_true, y_bin_pred)
    cls_metrics.update({"accuracy_tol": accuracy_tol})
    return cls_metrics


# --------------- 5. Numeric fields (binary after tolerance) ------------ #
def eval_numeric(
    y_true: Sequence[float | None],
    y_pred: Sequence[float | None],
    tolerance: float = 2.0,
) -> Dict[str, float]:
    """
    Numeric field (e.g. age) correct if |Δ| ≤ tolerance.
    """
    def _within_tol(gt: float | None, pr: float | None) -> bool:
        if gt is None and pr is None:
            return True
        if gt is not None and pr is not None:
            return abs(gt - pr) <= tolerance
        return False

    y_bin_true = [gt is not None for gt in y_true]
    y_bin_pred = [pr is not None for pr in y_pred]

    correct_mask = [_within_tol(gt, pr) for gt, pr in zip(y_true, y_pred)]
    accuracy_tol = sum(correct_mask) / len(correct_mask)

    cls_metrics = _clf_metrics(y_bin_true, y_bin_pred)
    cls_metrics.update({"accuracy_tol": accuracy_tol})
    return cls_metrics


# -------- 6. Structured tuple list (e.g. fam_cancer_hx) --------------- #
TupleSet = Set[Tuple[str, str]]  # (relationship, type)

def eval_structured_set(
    y_true: Sequence[TupleSet],
    y_pred: Sequence[TupleSet],
    jaccard_threshold: float = 0.75,
) -> Dict:
    """
    Evaluate complex set-of-tuples variables.
    Returns mean Jaccard, exact-match rate, and thresholded F1.
    """
    jaccards = []
    bin_true, bin_pred = [], []

    # normalize None to empty set
    y_true = [set(tuple(y.items()) for y in x) if x is not None else set([]) for x in y_true]
    y_pred = [set(tuple(y.items()) for y in x) if x is not None else set([]) for x in y_pred]


    for gt_set, pr_set in zip(y_true, y_pred):
        inter = len(gt_set & pr_set)
        union = len(gt_set | pr_set)
        jac = inter / union if union else 1.0
        jaccards.append(jac)

        # binary label using threshold
        bin_true.append(bool(gt_set))
        bin_pred.append(jac >= jaccard_threshold)

    mean_jac = float(np.mean(jaccards))
    exact_match = float(np.mean([jac == 1.0 for jac in jaccards]))

    f1_thresh = f1_score(bin_true, bin_pred, zero_division=0)
    return {
        "jaccard_mean": mean_jac,
        "exact_match_rate": exact_match,
        "f1_thresh": f1_thresh,
        "support": len(y_true),
    }

# ---------------------- 7. List of Dates ------------------------------- #
def eval_date_list(
    y_true: Sequence[List[str]],
    y_pred: Sequence[List[str]],
    tolerance_days: int = 30,
) -> Dict[str, float]:
    """
    Evaluates lists of dates based on a matching algorithm with tolerance.

    For each record, it performs a greedy match between true and predicted dates.
    A match is valid if the dates are within `tolerance_days`. It then calculates
    corpus-level micro-averaged precision, recall, and F1-score.

    Metrics:
    - precision_micro: Overall precision = (Total TP) / (Total TP + Total FP)
    - recall_micro: Overall recall = (Total TP) / (Total TP + Total FN)
    - f1_micro: Overall F1-score.
    - jaccard_mean: The mean of the Jaccard similarity scores for each record.
      Jaccard for a record = |matched| / |union of true and pred sets|.
    - exact_match_rate: Fraction of records where the predicted set of dates
      perfectly matches the true set (after tolerance-based matching).
    """
    total_tp, total_fp, total_fn = 0, 0, 0
    jaccards = []
    exact_matches = 0

    if not y_true:
        return {
            "precision_micro": 0.0, "recall_micro": 0.0, "f1_micro": 0.0,
            "jaccard_mean": 0.0, "exact_match_rate": 0.0, "support": 0
        }

    def _parse_dates(date_list: List[str]) -> List[datetime]:
        parsed = []
        if not date_list:
            return []
        for d_str in date_list:
            parsed.append(datetime.fromisoformat(normalize_date(d_str) or "1970-01-01"))
        return sorted(parsed)

    for gt_list, pr_list in zip(y_true, y_pred):
        gt_dates = _parse_dates(gt_list or [])
        pr_dates = _parse_dates(pr_list or [])

        if not gt_dates and not pr_dates:
            jaccards.append(1.0)
            exact_matches += 1
            continue

        # Greedy matching to find True Positives (TP)
        matched_pr_indices = set()
        tp = 0
        
        for gt_date in gt_dates:
            best_match_idx = -1
            min_delta = float('inf')

            for i, pr_date in enumerate(pr_dates):
                if i in matched_pr_indices:
                    continue
                
                delta = abs((gt_date - pr_date).days)
                if delta <= tolerance_days and delta < min_delta:
                    min_delta = delta
                    best_match_idx = i
            
            if best_match_idx != -1:
                tp += 1
                matched_pr_indices.add(best_match_idx)

        # Calculate metrics for the current record
        fp = len(pr_dates) - tp
        fn = len(gt_dates) - tp
        
        total_tp += tp
        total_fp += fp
        total_fn += fn

        union = tp + fp + fn
        jaccard = tp / union if union > 0 else 1.0
        jaccards.append(jaccard)

        if fp == 0 and fn == 0:
            exact_matches += 1

    # Calculate final micro-averaged metrics
    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (2 * micro_precision * micro_recall / (micro_precision + micro_recall)) if (micro_precision + micro_recall) > 0 else 0.0

    mean_jaccard = float(np.mean(jaccards)) if jaccards else 0.0
    exact_match_rate = exact_matches / len(y_true)

    return {
        "precision_micro": micro_precision,
        "recall_micro": micro_recall,
        "f1_micro": micro_f1,
        "jaccard_mean": mean_jaccard,
        "exact_match_rate": exact_match_rate,
        "support": len(y_true),
    }




# ----- Eval function ----------------- #


def eval_gt_pred(gt_pred_dict: Dict[str, Dict[str, List[Any]]]) -> Dict[str, Any]:
    evaluated_vars = {}
    for var_id, values in gt_pred_dict.items():
        var_type = variables.LM_VARIABLES[var_id].type
        # is_date = variables.LM_VARIABLES[var_id].is_date

        match get_var_type(var_id):
            case "bool":
                y_true, y_pred = norm_binary(values["gt"], values["pred"])
                evaluated_vars[var_id] = eval_binary(y_true, y_pred)
            case "date":
                y_true, y_pred = norm_date(values["gt"], values["pred"])
                evaluated_vars[var_id] = eval_date(values["gt"], values["pred"])
            case "int":
                evaluated_vars[var_id] = eval_numeric(values["gt"], values["pred"])
            case "enum":
                # if any(value is None for value in values["gt"]):
                #     # TODO: fix this!!!
                #     print(f"Warning: {var_id} has None values in ground truth, skipping evaluation.", values["gt"])
                enum_value_numbers = [member.value for member in var_type] # type: ignore

                y_true, y_pred = norm_multiclass(values["gt"], values["pred"])
                evaluated_vars[var_id] = eval_multiclass(y_true, y_pred, enum_value_numbers)
            case "list_string":
                evaluated_vars[var_id] = eval_date_list(values["gt"], values["pred"])
            case "list_enum":
                type_list = get_args(var_type)
                # print("dasd", [member.value for member in type_list[0]])
                evaluated_vars[var_id] = eval_multilabel(values["gt"], values["pred"], [member.value for member in type_list[0]])
            case "list_object":
                evaluated_vars[var_id] = eval_structured_set(values["gt"], values["pred"])
            case _:
                print(f"🚨 WARN: {var_id} has unknown type {var_type}, skipping evaluation.", values["gt"], values["pred"])
    return evaluated_vars

def kappa_gt_pred(gt_pred_dict: Dict[str, Dict[str, List[Any]]]) -> Dict[str, float]:
    """
    Calculate Cohen's Kappa for each variable in the ground truth and predicted values.
    Returns a dictionary with variable IDs as keys and Kappa values as values.
    """
    kappa_scores = {}
    for var_id, values in gt_pred_dict.items():
        y_true, y_pred = values["gt"], values["pred"]

        try:
            match get_var_type(var_id):
                case "bool":
                    y_true, y_pred = norm_binary(y_true, y_pred)
                case "date":
                    y_true, y_pred = norm_date(y_true, y_pred)
                case "enum":
                    y_true, y_pred = norm_multiclass(y_true, y_pred)
                case "list_string":
                    # y_true is a list of lists of str. normalize by running normalize_date on each string and sorting each list:
                    y_true = [sorted(normalize_date(x) or "" for x in lst) for lst in y_true]
                    y_pred = [sorted(normalize_date(x) or "" for x in lst) for lst in y_pred]
                case "list_enum":
                    # y_true is a list of lists of enums. normalize by sorting each list:
                    y_true = [sorted(x) if x is not None else [] for x in y_true]
                    y_pred = [sorted(x) if x is not None else [] for x in y_pred]
                case "list_object":
                    print("skipping kappa for list_object", var_id)
                    continue

            if len(set(y_true)) <= 1 or len(set(y_pred)) <= 1:
                print(f"Skipping Kappa for {var_id}: not enough variability in either ground truth or prediction.")
                print(y_true,"\n", y_pred)
                print(set(y_true), "\n", set(y_pred))
                # kappa_scores[var_id] = None  # Not enough variability to calculate Kappa
                continue
            kappa = cohen_kappa_score(y_true, y_pred)
            kappa_scores[var_id] = kappa
        except Exception as e:
            print(f"Error calculating Kappa for {var_id}: {e}")
            # kappa_scores[var_id] = None  # In case of error, set Kappa to None
    return kappa_scores


def percentage_agreement(gt_pred_dict: Dict[str, Dict[str, List[Any]]]) -> Dict[str, Tuple[float, int]]:
    percentage_agreement: Dict[str, Tuple[float, int]] = {}
    for var_id, values in gt_pred_dict.items():
        y_true, y_pred = values["gt"], values["pred"]
        cases  = max(len(y_true), len(y_pred))

        match get_var_type(var_id):
            case "bool":
                y_true, y_pred = norm_binary(y_true, y_pred)
            case "enum":
                y_true, y_pred = norm_multiclass(y_true, y_pred)
            case "date":
                y_true, y_pred = norm_date(y_true, y_pred)
            case "list_string":
                # each prediction is a list of dates. we can calculate the overlap % for each gt, and pred, then average to get the percentage agreement
                
                # todo: check if lst is not None
                y_true = [ set(normalize_date(x) for x in lst) for lst in y_true if lst is not None ]
                y_pred = [ set(normalize_date(x) for x in lst) for lst in y_pred if lst is not None ]

                # print(var_id)
                # print(y_true)
                # print(y_pred)
                agreement = []
                for gt, pred in zip(y_true, y_pred):
                    if not gt and not pred:
                        agreement.append(1.0)  # both empty, perfect agreement
                    elif not gt or not pred:
                        agreement.append(0.0)  # one is empty, no agreement
                    else:
                        intersection = len(gt & pred)
                        union = len(gt | pred)
                        agreement.append(intersection / union if union > 0 else 0.0)
                percentage_agreement[var_id] = (sum(agreement) / len(agreement) if agreement else 0.0, cases)
                continue
            case "list_enum":
                # each prediction is a list of enums. we can calculate the overlap % for each gt, and pred, then average to get the percentage agreement
                y_true = [set(x) if x is not None else set([]) for x in y_true]
                y_pred = [set(x) if x is not None else set([]) for x in y_pred]
                agreement = []
                for gt, pred in zip(y_true, y_pred):
                    if not gt and not pred:
                        agreement.append(1.0)  # both empty, perfect agreement
                    elif not gt or not pred:
                        agreement.append(0.0)  # one is empty, no agreement
                    else:
                        intersection = len(gt & pred)
                        union = len(gt | pred)
                        agreement.append(intersection / union if union > 0 else 0.0)
                percentage_agreement[var_id] = (sum(agreement) / len(agreement) if agreement else 0.0, cases)
                continue
            case _:
                continue
        
        if len(y_true) == 0:
            continue

        agreement = sum(1 for gt, pred in zip(y_true, y_pred) if gt == pred) / len(y_true)
        percentage_agreement[var_id] = (agreement, cases)
    return percentage_agreement


# calculate percentage agreement across 2+ annotators per variable
# e.g.
# appendectomy:
# patient 1 
# values
# true true false None _> 2
# true true None None


# varId: value