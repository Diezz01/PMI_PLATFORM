"""Validate the exact calculation snapshot authorized for permanent storage."""
from app.schemas.pmi import PMISaveRequest
from app.schemas.pmi_median import PMIMedianSelection
from app.schemas.pmi_results import PMIMethodResult
from app.schemas.pmi_selection import PMIResultSelection
from app.services.pmi.median_service import PMIMedianService


def prepare_save(session: dict, request: PMISaveRequest) -> dict:
    selected = set(request.selected_methods)
    stored_selection = session.get("result_selection")
    source = session.get("source_draft") or {}
    if stored_selection:
        selection = PMIResultSelection.model_validate(stored_selection)
        if (selection.session_id != session["session_id"]
                or selection.source_draft_id != source.get("draft_id")
                or selection.source_draft_version != source.get("version")):
            raise ValueError("The selection does not belong to this calculation.")
        if selection.status != "selected" or selected != set(selection.selected_method_ids):
            raise ValueError("First complete and confirm the results to keep, including their warnings.")

    evaluated = [PMIMethodResult.model_validate(r) for r in session.get("evaluated_results") or []]
    by_id = {r.method_id: r for r in evaluated}
    if evaluated:
        if len(by_id) != len(evaluated):
            raise ValueError("Duplicate calculation results. Recalculate the case.")
        if any(m not in by_id or by_id[m].calculation_status != "calculated"
               or by_id[m].method_kind == "mock" for m in selected):
            raise ValueError("Only available calculated results can be saved.")
        if stored_selection:
            warned = {m for m in selected if any(c.outcome in {"failed", "unknown"}
                and not (by_id[m].method_kind == "henssge" and c.id == "scientific_applicability")
                for c in by_id[m].checks)}
            if warned != set(selection.acknowledged_warning_method_ids):
                raise ValueError("Confirm the warnings for the selected results before saving.")
        rows = [{"method_name": m, "pmi_value": by_id[m].pmi_hours,
                 "input_params": session["input_data"], "method_version": by_id[m].method_version}
                for m in request.selected_methods]
    else:
        # Sessions created by the legacy API have only numeric results.
        legacy = {r["method_name"]: r for r in session["results"]}
        if selected - legacy.keys():
            raise ValueError("One or more selected methods are not available in this session.")
        rows = [legacy[m] for m in request.selected_methods]

    median_selection = session.get("median_selection")
    if not request.omit_median:
        if ((median_selection and median_selection.get("status") == "awaiting_warning_confirmation")
                or session.get("median_decision") == "requested"):
            raise ValueError("Complete the median selection, or explicitly ask to save without a median.")
        median_ids = list(session.get("selected_median_methods") or [])
        if not set(median_ids) <= selected:
            raise ValueError("The median may only use results selected to keep.")
    else:
        median_ids = []

    if evaluated:
        stored_median = session.get("median_result") or {}
        if not request.omit_median and not median_ids and (
                stored_median.get("status") == "calculated"
                or (median_selection and median_selection.get("status") == "selected")):
            raise ValueError("The median changed. Calculate or skip it again before saving.")
        if median_ids and (stored_median.get("status") != "calculated"
                           or median_ids != stored_median.get("selected_method_ids")):
            raise ValueError("The median changed. Calculate or skip it again before saving.")
        if median_ids and median_selection:
            confirmed = PMIResultSelection.model_validate(median_selection)
            if (confirmed.status != "selected" or confirmed.selected_method_ids != median_ids
                    or confirmed.session_id != session["session_id"]
                    or confirmed.source_draft_id != source.get("draft_id")
                    or confirmed.source_draft_version != source.get("version")):
                raise ValueError("Confirm the current median selection before saving.")
        median = PMIMedianService().calculate(evaluated, PMIMedianSelection(
            selected_method_ids=median_ids,
            acknowledged_warning_method_ids=stored_median.get("acknowledged_warning_method_ids", []) if median_ids else [],
        ))
        if median_ids and median_selection and set(confirmed.acknowledged_warning_method_ids) != set(median.acknowledged_warning_method_ids):
            raise ValueError("The median warning confirmations changed. Confirm them again.")
        median_value = median.pmi_hours
        median_snapshot = median.model_dump(mode="json", exclude={"pmi_display"})
    else:
        median_value = session.get("median_pmi") if median_ids else None
        if median_ids and median_value is None:
            raise ValueError("Calculate the selected median before saving.")
        median_snapshot = session.get("median_result") if median_ids else None

    if request.omit_median and median_selection:
        median_selection = {**median_selection, "status": "empty", "selected_method_ids": [],
                            "acknowledged_warning_method_ids": [], "pending_method_ids": [],
                            "pending_warning_method_ids": []}
    snapshot = None if not evaluated else {
        "schema_version": 2, "session_version": session["version"],
        "saved_method_ids": request.selected_methods, "source_draft": session.get("source_draft"),
        "evaluated_results": [by_id[m].model_dump(mode="json", exclude={"pmi_display", "applicability"})
                              for m in request.selected_methods],
        "result_selection": stored_selection, "median_selection": median_selection,
        "median_result": median_snapshot,
        "median_decision": "calculated" if median_ids else "skipped",
    }
    return {"rows": rows, "median_pmi": median_value,
            "median_selected_methods": median_ids, "evaluation_snapshot": snapshot}
