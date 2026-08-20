import os
import json
from datetime import datetime

from src.constants.constants import RESULTS_DIR
from data.golden_dataset import GOLDEN_DATASET
from src.model_schemas.output import OutputState

def evaluate_golden_dataset(predictions: list[OutputState], ground_truth: list[OutputState] = GOLDEN_DATASET, save_results: bool = True) -> float:
    """
    Evaluate the predictions against the ground truth.

    Args:
        predictions: list[Output], the predictions to evaluate.
        ground_truth: list[Output], the ground truth to evaluate against.
    """
    results = []
    # Build dicts keyed by invoice_number to allow de-duplication.
    pred_dict = {p.invoice_number: p for p in predictions}
    truth_dict = {t.invoice_number: t for t in ground_truth}
    joint_keys = set(pred_dict.keys()).intersection(set(truth_dict.keys()))

    print(f"Received predictions: {list(joint_keys)}")
    for invoice_number in joint_keys:
        prediction = pred_dict[invoice_number]
        truth = truth_dict[invoice_number]
        result_entry = {
            "invoice_number": invoice_number,
            "vendor_name": prediction.vendor_name,
            "amount": prediction.amount,
            "processing_result_accurate": prediction.processing_result == truth.processing_result,
            "processing_result_sublabel_accurate": prediction.processing_result_sublabel == truth.processing_result_sublabel or prediction.processing_result_sublabel in truth.processing_result_sublabel,
            "confidence_difference": prediction.confidence - truth.confidence,
        }
        results.append(result_entry)

    if save_results:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        today_str = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(RESULTS_DIR, f"golden_dataset_evals_{today_str}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)

    return results

def get_golden_dataset_results(results: dict) -> dict:
    accuracy = sum([result["processing_result_accurate"] for result in results]) / len(results)
    sublabel_accuracy = sum([result["processing_result_sublabel_accurate"] for result in results]) / len(results)
    confidence_difference = sum([result["confidence_difference"] for result in results]) / len(results)
    return {
        "accuracy": accuracy,
        "sublabel_accuracy": sublabel_accuracy,
        "confidence_difference": confidence_difference
    }