from typing import Any

from pydantic import ValidationError
from redis.exceptions import RedisError

from app.schemas.pmi_chat_tools import ReadDraftArguments
from app.schemas.pmi_draft import (
    PMIDraftResponse,
    PMIDraftState,
    PMIDraftUpdateRequest,
)
from app.services.pmi.draft_service import (
    PMIDraftConflict,
    PMIDraftService,
)
from app.services.pmi.draft_store import PMIDraftStore
from app.services.pmi.session_store import (
    PMISessionConflict,
    PMISessionNotFound,
)


# Contratti interni, indipendenti dal provider LLM.
# Li adatteremo al formato richiesto dal provider quando lo collegheremo.
TOOL_DEFINITIONS = [
    {
        "name": "read_pmi_draft",
        "description": (
            "Read the current draft data, version, status, "
            "and missing required fields."
        ),
        "parameters": ReadDraftArguments.model_json_schema(),
    },
    {
        "name": "update_pmi_draft",
        "description": (
            "Update one or more fields explicitly provided by the user. "
            "Omitted fields remain unchanged. An explicit null value "
            "clears the field. Biochemical measurements must be supplied "
            "as complete objects, including the technique when required. "
            "Use the latest draft version."
        ),
        "parameters": PMIDraftUpdateRequest.model_json_schema(),
    },
]


class PMIChatTools:
    def __init__(self, store: PMIDraftStore) -> None:
        self.store = store
        self.service = PMIDraftService()

    @staticmethod
    def _error(code: str, message: str, **details: Any) -> dict:
        return {
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                **details,
            },
        }

    def _response(self, record: dict) -> dict:
        state = PMIDraftState.model_validate(record["input_data"])
        summary = self.service.summarize(state)

        response = PMIDraftResponse(
            **summary.model_dump(),
            draft_id=record["session_id"],
            expires_at=record["expires_at"],
        )

        return {
            "ok": True,
            "draft": response.model_dump(mode="json"),
        }

    def execute(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        user_id: int,
        draft_id: str,
    ) -> dict:
    
        argument_models = {
            "read_pmi_draft": ReadDraftArguments,
            "update_pmi_draft": PMIDraftUpdateRequest,
        }

        argument_model = argument_models.get(tool_name)

        if argument_model is None:
            return self._error(
                "unknown_tool",
                "Strumento non disponibile.",
            )

        try:
            parsed_arguments = argument_model.model_validate(arguments)
        except ValidationError as exc:
            return self._error(
                "invalid_arguments",
                "I parametri proposti non rispettano il contratto.",
                issues=[
                    {
                        "field": ".".join(str(part) for part in error["loc"]),
                        "message": error["msg"],
                    }
                    for error in exc.errors(
                        include_url=False,
                        include_context=False,
                        include_input=False,
                    )
                ],
            )

        try:
            record = self.store.get_session(
                user_id=user_id,
                session_id=draft_id,
            )

            if isinstance(parsed_arguments, ReadDraftArguments):
                return self._response(record)

            state = PMIDraftState.model_validate(record["input_data"])

            updated_state = self.service.update(
                state,
                parsed_arguments,
            )

    
            updated_state = updated_state.model_copy(
                update={
                    "version": parsed_arguments.expected_version + 1,
                },
                deep=True,
            )

            updated_record = self.store.update_session(
                user_id=user_id,
                session={
                    **record,
                    "input_data": updated_state.model_dump(mode="json"),
                },
                expected_version=parsed_arguments.expected_version,
            )

            return self._response(updated_record)

        except PMISessionNotFound:
            return self._error(
                "draft_not_found",
                "Bozza non trovata o scaduta.",
            )

        except (PMIDraftConflict, PMISessionConflict):
            return self._error(
                "version_conflict",
                
            )

        except RedisError:
            return self._error(
                "storage_unavailable",
            )