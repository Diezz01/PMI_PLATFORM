"""Optional median dialogue; calculation uses the existing median service."""
from app.schemas.pmi_median import PMIMedianResult, PMIMedianSelection
from app.schemas.pmi_selection import PMIResultSelection
from app.services.pmi.median_service import PMIMedianService


def median_offer(italian):
    return ("Vuoi calcolare anche la mediana? È facoltativa: puoi rispondere no."
            if italian else "Would you also like to calculate the median? It is optional: you can say no.")


def median_candidates(results, keep_selection):
    by_id = {r.method_id: r for r in results}
    return [by_id[m] for m in keep_selection.selected_method_ids if m in by_id
            and by_id[m].method_kind == "biochemical"
            and by_id[m].calculation_status == "calculated" and by_id[m].pmi_hours is not None]


def median_question(available, italian):
    if not available:
        return ("Tra i risultati conservati non ci sono formule biologiche calcolate per la mediana. "
                "Puoi modificare i risultati da conservare oppure proseguire senza mediana."
                if italian else "There are no calculated biological methods among the results kept. "
                "You can change the results to keep or continue without a median.")
    question = ("Quali formule, tra i risultati conservati, vuoi includere nella mediana? "
                "Henssge è escluso. Puoi indicare i nomi, scegliere tutti oppure rinunciare."
                if italian else
                "Which of the methods kept should be included in the median? "
                "Henssge is excluded. Name methods, choose all, or skip the median.")
    return question + "\n\n" + "\n".join(f"- **{r.method_name}:** {r.pmi_display}" for r in available)


def _median_reply(median, results, italian):
    by_id = {r.method_id: r for r in results}
    if median.status == "not_calculated":
        return ("Mediana non calcolata. I risultati selezionati da conservare restano disponibili."
                if italian else "Median not calculated. The selected results to keep remain available.")
    names = ", ".join(by_id[m].method_name for m in median.selected_method_ids)
    return ((f"**Mediana PMI:** {median.pmi_display} (hh:mm)\nMetodi: {names}."
             if italian else f"**Median PMI:** {median.pmi_display} (hh:mm)\nMethods: {names}.")
            + ("\nIl time gap è già incluso nei valori; non viene aggiunto di nuovo."
               if italian else "\nThe time gap is already included in the values; it is not added again."))


def handle_median_intent(*, intent, keep_selection, selection, results, session,
                         workflow, apply_selection):
    """Return reply, workflow, median selection, median result, session updates."""
    italian = intent.language == "it"
    if keep_selection.status != "selected":
        return (("Completa prima la selezione dei risultati da conservare." if italian else
                 "First complete the selection of results to keep."), workflow, selection, None, {})
    empty = PMIResultSelection(session_id=selection.session_id,
        source_draft_id=selection.source_draft_id, source_draft_version=selection.source_draft_version)
    available = median_candidates(results, keep_selection)
    if intent.action == "clarify":
        if selection.status == "awaiting_warning_confirmation":
            _, reply, _ = apply_selection(selection, intent, available, purpose="median")
            return reply, workflow, selection, None, {}
        return (("La selezione non è cambiata.\n\n" if italian else
                 "The selection has not changed.\n\n") + median_question(available, italian),
                workflow, selection, None, {})
    if intent.action == "skip_median":
        median = PMIMedianService().calculate(results, PMIMedianSelection(selected_method_ids=[]))
        updates = _median_updates(empty, median, "skipped")
        return _median_reply(median, results, italian), {**workflow, "stage": "ready_to_save"}, empty, median, updates
    if intent.action == "start_median" and not intent.method_ids and not intent.excluded_method_ids:
        return (median_question(available, italian), {**workflow, "stage": "median_selection"}, selection,
                None, {"median_decision": "requested"})
    # Explicitly naming Henssge is rejected; "all" automatically excludes it.
    by_id = {r.method_id: r for r in results}
    if any(by_id.get(m) is not None and by_id[m].method_kind == "henssge" for m in intent.method_ids):
        return (("Henssge non può essere incluso nella mediana. Scegli solo formule biologiche."
                 if italian else "Henssge cannot be included in the median. Choose biological formulas only."),
                {**workflow, "stage": "median_selection"}, selection, None, {})
    if set(intent.method_ids) - {r.method_id for r in available}:
        return (("Per la mediana scegli soltanto i risultati conservati. Per usare altri metodi, "
                 "modifica prima la selezione dei risultati da conservare." if italian else
                 "For the median, choose only results you kept. To use other methods, "
                 "first change the results to keep.") + "\n\n" + median_question(available, italian),
                {**workflow, "stage": "median_selection"}, selection, None, {})
    allowed = {r.method_id for r in available}
    # An exclusion-only median request starts from the kept biological results,
    # not from an empty median selection and never from Henssge.
    if (intent.selection_base == "kept"
            or (selection.status == "empty" and intent.action == "remove")
            or (selection.status == "empty" and intent.excluded_method_ids and not intent.method_ids)
            or (intent.action == "start_median" and intent.excluded_method_ids)):
        excluded = set(intent.excluded_method_ids)
        if intent.action == "remove":
            excluded.update(intent.method_ids)
        intent = intent.model_copy(update={
            "action": "replace", "method_ids": [r.method_id for r in available if r.method_id not in excluded],
            "excluded_method_ids": [],
        })
        if not intent.method_ids:
            intent.action = "clear"
    else:
        intent = intent.model_copy(update={
            "excluded_method_ids": [m for m in intent.excluded_method_ids if m in allowed],
        })
        if intent.action == "start_median":
            intent.action = "replace"
    updated, reply, changed = apply_selection(selection, intent, available, purpose="median")
    if not changed:
        stored = session.get("median_result")
        median = PMIMedianResult.model_validate(stored) if stored else None
        if (median is not None and intent.action in {"show", "other"}
                and (median.status == "calculated" or session.get("median_decision") == "skipped")):
            reply = _median_reply(median, results, italian)
            if intent.action == "other":
                reply += ("\nIl salvataggio definitivo sarà collegato nel prossimo passaggio." if italian
                          else "\nFinal saving will be connected in the next step.")
        elif (updated.status != "awaiting_warning_confirmation"
              and intent.action in {"show", "replace", "add", "remove"} and not intent.method_ids
              and not intent.unresolved_names):
            reply = median_question(available, italian)
        return reply, workflow, updated, median, {}
    median = PMIMedianService().calculate(results, PMIMedianSelection(selected_method_ids=[]))
    if updated.status == "selected":
        try:
            median = PMIMedianService().calculate(results, PMIMedianSelection(
                selected_method_ids=updated.selected_method_ids,
                acknowledged_warning_method_ids=updated.acknowledged_warning_method_ids,
            ))
        except ValueError as exc:
            return (("Mediana non aggiornata: " if italian else "Median not updated: ") + str(exc),
                    workflow, selection, None, {})
        reply = _median_reply(median, results, italian)
    elif updated.status == "empty":
        reply = median_question(available, italian)
    # A changed, incomplete selection invalidates any previously calculated median.
    decision = "calculated" if median.status == "calculated" else "requested"
    updates = _median_updates(updated, median, decision)
    stage = "median_ready" if median.status == "calculated" else "median_selection"
    return reply, {**workflow, "stage": stage}, updated, median, updates


def _median_updates(selection, median, decision):
    return {
        "median_selection": selection.model_dump(),
        "median_decision": decision,
        "median_result": median.model_dump(mode="json", exclude={"pmi_display"}),
        "median_pmi": median.pmi_hours,
        "selected_median_methods": median.selected_method_ids,
        "status": "median_ready" if median.status == "calculated" else "calculated",
    }
