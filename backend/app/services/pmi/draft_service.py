from app.schemas.pmi_case import PMICaseDraft, PMICaseInput
from app.schemas.pmi_draft import (
    PMIDraftConfirmRequest,
    PMIDraftState,
    PMIDraftSummary,
    PMIDraftUpdateRequest,
)


class PMIDraftConflict(ValueError):
    pass


class PMIDraftNotReady(ValueError):
    pass


class PMIDraftService:
    @staticmethod
    def create() -> PMIDraftState:
        return PMIDraftState()

    @staticmethod
    def _check_version(
        draft: PMIDraftState,
        expected_version: int,
    ) -> None:
        if draft.version != expected_version:
            raise PMIDraftConflict(
                "La bozza è cambiata. Ricaricala prima di continuare."
            )

    def update(
        self,
        draft: PMIDraftState,
        request: PMIDraftUpdateRequest,
    ) -> PMIDraftState:
        self._check_version(draft, request.expected_version)

        changes = request.changes.model_dump(exclude_unset=True)

        if not changes:
            return draft.model_copy(deep=True)

        merged_data = draft.data.model_dump()

        for field, value in changes.items():
            if field == "exclusion_criteria":
                merged_data[field] = {
                    **merged_data[field],
                    **value,
                }
            else:
                merged_data[field] = value

        if (
            "correction_factor" in changes
            and "correction_factor_context" not in changes
            and changes["correction_factor"] != draft.data.correction_factor
        ):
            merged_data["correction_factor_context"] = None

        validated_data = PMICaseDraft.model_validate(merged_data)

        if validated_data == draft.data:
            return draft.model_copy(deep=True)

        missing = validated_data.get_missing_fields()

        # Ogni modifica effettiva annulla la conferma precedente.
        return PMIDraftState(
            data=validated_data,
            version=draft.version + 1,
            status="collecting" if missing else "ready",
        )

    @staticmethod
    def summarize(draft: PMIDraftState) -> PMIDraftSummary:
        missing = draft.data.get_missing_fields()

        return PMIDraftSummary(
            data=draft.data.model_copy(deep=True),
            version=draft.version,
            status=draft.status,
            missing_required_fields=missing,
            can_confirm=not missing and draft.status == "ready",
        )

    def confirm(
        self,
        draft: PMIDraftState,
        request: PMIDraftConfirmRequest,
    ) -> PMIDraftState:
        self._check_version(draft, request.expected_version)

        missing = draft.data.get_missing_fields()

        if missing:
            raise PMIDraftNotReady(
                "Mancano i campi obbligatori: " + ", ".join(missing)
            )

        # Verifica anche il contratto completo prima di confermare.
        draft.data.to_complete_input()

        if draft.status == "confirmed":
            return draft.model_copy(deep=True)

        return PMIDraftState(
            data=draft.data.model_copy(deep=True),
            version=draft.version + 1,
            status="confirmed",
        )

    @staticmethod
    def get_calculation_input(draft: PMIDraftState) -> PMICaseInput:
        if draft.status != "confirmed":
            raise PMIDraftNotReady(
                "Conferma il riepilogo prima di procedere con il calcolo."
            )

        return draft.data.to_complete_input()