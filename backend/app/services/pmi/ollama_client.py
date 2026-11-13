from typing import Any

import httpx

from app.configs.config import settings


class OllamaError(RuntimeError):
    pass


class OllamaUnavailable(OllamaError):
    pass


class OllamaResponseError(OllamaError):
    pass


async def chat_with_ollama(
    *,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    response_format: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "keep_alive": "5m",
        "options": {
            "temperature": 0,
            "num_ctx": settings.OLLAMA_CONTEXT_TOKENS,
            "num_predict": settings.OLLAMA_MAX_OUTPUT_TOKENS,
        },
    }

    if tools:
        payload["tools"] = tools
    if response_format is not None:
        payload["format"] = response_format

    timeout = httpx.Timeout(
        settings.OLLAMA_TIMEOUT_SECONDS,
        connect=5.0,
    )

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            trust_env=False,
        ) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat",
                json=payload,
            )

            response.raise_for_status()

    except httpx.TimeoutException:
        raise OllamaUnavailable(
            "Ollama did not respond within the configured timeout."
        ) from None

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise OllamaResponseError(
                "Ollama returned 404. Check the configured model "
                "and whether it has been downloaded."
            ) from None

        raise OllamaResponseError(
            f"Ollama returned HTTP {exc.response.status_code}."
        ) from None

    except httpx.RequestError:
        raise OllamaUnavailable(
            "Cannot reach Ollama. Check that it is running "
            "and reachable from the backend."
        ) from None

    try:
        data = response.json()
    except ValueError:
        raise OllamaResponseError(
            "Ollama returned an invalid JSON response."
        ) from None

    if not isinstance(data, dict):
        raise OllamaResponseError(
            "Ollama returned an unexpected response format."
        )

    if data.get("error"):
        raise OllamaResponseError(
            "Ollama reported a generation error."
        )

    if data.get("done") is not True:
        raise OllamaResponseError(
            "Ollama returned an incomplete response."
        )

    if data.get("done_reason") == "length":
        raise OllamaResponseError(
            "The response reached the output token limit."
        )

    message = data.get("message")

    if not isinstance(message, dict):
        raise OllamaResponseError(
            "Ollama returned no valid assistant message."
        )

    if message.get("role") != "assistant":
        raise OllamaResponseError(
            "Ollama returned an unexpected message role."
        )

    content = message.get("content", "")
    tool_calls = message.get("tool_calls", [])

    if not isinstance(content, str) or not isinstance(tool_calls, list):
        raise OllamaResponseError(
            "Ollama returned invalid message fields."
        )

    if not content.strip() and not tool_calls:
        raise OllamaResponseError(
            "Ollama returned an empty assistant message."
        )

    # Tool calls are only returned here.
    # They must be validated and executed by the backend.
    return message
