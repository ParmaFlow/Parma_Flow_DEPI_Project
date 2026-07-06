# core/llm.py
"""
Thin, production-hardened wrapper around the Groq-hosted, OpenAI-compatible
chat completions API.

This module is the single integration point between every agent (Ops, Risk,
Auditor, Report) and the LLM provider. Per this project's Explainable AI
architecture, the LLM is used ONLY to generate human-readable explanation
text for facts that have already been computed deterministically in Python
-- it never calculates, validates, or decides anything. This module does
not enforce that (agent prompts do); it is responsible only for reliable,
observable, and safe communication with the provider.
"""
import json
import logging
import random
import time
from typing import Any, Dict, Optional

from openai import (
    OpenAI,
    APIError,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class LLMInvocationError(Exception):
    """
    Raised when the underlying LLM provider call fails in a way that
    cannot be recovered from within LLMModel (e.g. retries exhausted,
    a non-retryable provider error, or a structurally empty response).

    This is intentionally a plain Exception subclass rather than one of
    backend.agents.shared.exceptions -- core/ is meant to be a low-level,
    agent-agnostic utility layer with no dependency on the backend.agents
    package. The Orchestrator's existing blanket exception handling around
    each agent's run() call already catches and structures *any* exception
    raised from here, so no other file needs to change for this to work
    correctly within the existing workflow.
    """


class LLMModel:
    """
    Wrapper around the Groq-hosted OpenAI-compatible chat completions API.

    Backward compatibility:
        The public method `get_decision(system_prompt, user_data) -> str`
        keeps its exact original name, signature, and return type (raw
        JSON text) so every existing call site in OpsAgent, RiskAgent,
        AuditorAgent, and ReportAgent continues to work unmodified. All
        new configuration (model, timeout, retries, temperature, etc.) is
        exposed via constructor parameters with defaults that reproduce
        the original hardcoded behavior exactly, so `LLMModel(api_key)`
        continues to work exactly as it did before.

    Thread-safety:
        Instances hold no mutable state beyond immutable configuration
        set once in __init__. The underlying OpenAI SDK client is
        documented as safe for concurrent synchronous use. A single
        instance may therefore safely be reused across concurrent
        workflow runs, as the Orchestrator currently does.
    """

    #: Default model served via Groq's OpenAI-compatible endpoint. Kept
    #: identical to the original hardcoded value to preserve behavior.
    DEFAULT_MODEL = "llama-3.1-8b-instant"

    #: Default base URL for the Groq API. Matches the original hardcoded
    #: value.
    DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"

    #: Network timeout (seconds) for a single request attempt.
    DEFAULT_TIMEOUT_SECONDS = 30.0

    #: Maximum attempts (including the first) before raising
    #: LLMInvocationError for transient failures.
    DEFAULT_MAX_RETRIES = 3

    #: Base delay (seconds) for exponential backoff between retries.
    DEFAULT_RETRY_BASE_DELAY = 0.5

    #: Low, near-deterministic temperature so explanation text stays
    #: consistent for the same inputs.
    DEFAULT_TEMPERATURE = 0.2

    #: Hard ceiling on generated tokens, bounding latency and cost.
    DEFAULT_MAX_TOKENS = 800

    #: Provider errors considered transient and safe to retry.
    _RETRYABLE_EXCEPTIONS = (
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
        InternalServerError,
    )

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_base_delay: float = DEFAULT_RETRY_BASE_DELAY,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        """
        Construct the LLM client wrapper.

        Inputs:
            api_key: Groq API key. Must be a non-empty string; validated
                eagerly so misconfiguration fails at construction time
                rather than deep inside a workflow run.
            model: model identifier used for every call.
            base_url: API base URL.
            timeout_seconds: per-request network timeout.
            max_retries: maximum attempts (including the first) for
                transient failures before raising LLMInvocationError.
            retry_base_delay: base delay for exponential backoff between
                retries (actual delay includes random jitter).
            temperature: sampling temperature forwarded to every request.
            max_tokens: maximum tokens to generate per request.
        Outputs:
            None.
        Raises:
            ValueError: if api_key is missing/empty/non-string, or
                max_retries is less than 1.
        """
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError(
                "LLMModel requires a non-empty string api_key. "
                "Received an empty or invalid value."
            )
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1.")

        self._model = model
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout_seconds,
        )

    def get_decision(self, system_prompt: str, user_data: Dict[str, Any]) -> str:
        """
        Request an LLM-generated explanation for the given pre-computed
        facts.

        Despite the name (kept for backward compatibility with every
        existing agent call site), this method does not ask the LLM to
        make a business decision -- callers are expected to supply a
        prompt instructing the model to only explain facts that have
        already been computed deterministically, per this project's
        Explainable AI architecture.

        Inputs:
            system_prompt: the agent-specific system prompt instructing
                the LLM on its role and required output schema.
            user_data: a JSON-serializable dict of pre-computed facts for
                the LLM to explain.
        Outputs:
            str: the raw JSON text returned by the model. Callers remain
                responsible for json.loads-ing and validating this
                themselves, exactly as before.
        Raises:
            LLMInvocationError: if the request fails after exhausting
                retries, fails with a non-retryable provider error, or
                the provider returns a structurally empty response.
        """
        user_payload = self._serialize_user_data(user_data)
        return self._invoke_with_retries(system_prompt, user_payload)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _serialize_user_data(self, user_data: Dict[str, Any]) -> str:
        """
        Serialize the user data dict into valid JSON text for the prompt.

        Inputs:
            user_data: dict of pre-computed facts.
        Outputs:
            str: JSON-encoded representation. Non-JSON-native values are
                coerced to strings via default=str rather than raising.
        Raises:
            LLMInvocationError: if serialization fails outright (e.g. a
                circular reference).
        """
        try:
            return json.dumps(user_data, default=str)
        except (TypeError, ValueError) as exc:
            logger.error("Failed to serialize LLM input payload: %s", exc)
            raise LLMInvocationError(
                "Could not serialize input data for the LLM request."
            ) from exc

    def _invoke_with_retries(self, system_prompt: str, user_payload: str) -> str:
        """
        Call the chat completion endpoint, retrying transient failures
        with exponential backoff and jitter.

        Inputs:
            system_prompt: system role content.
            user_payload: JSON-encoded user role content.
        Outputs:
            str: sanitized message content from the first choice.
        Raises:
            LLMInvocationError: on non-retryable failure, or once retries
                are exhausted.
        """
        last_exception: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 1):
            start_time = time.monotonic()
            try:
                response = self.client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_payload},
                    ],
                    response_format={"type": "json_object"},
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                )
                elapsed = time.monotonic() - start_time
                logger.info(
                    "LLM call succeeded on attempt %d/%d (model=%s, %.3fs).",
                    attempt,
                    self._max_retries,
                    self._model,
                    elapsed,
                )
                return self._extract_content(response)

            except self._RETRYABLE_EXCEPTIONS as exc:
                last_exception = exc
                elapsed = time.monotonic() - start_time
                logger.warning(
                    "LLM call attempt %d/%d failed with retryable error "
                    "(%s) after %.3fs.",
                    attempt,
                    self._max_retries,
                    type(exc).__name__,
                    elapsed,
                )
                if attempt < self._max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                break

            except APIError as exc:
                # Non-retryable provider error (auth failure, bad request,
                # permission denied, etc). Fail fast instead of retrying
                # a request that will never succeed.
                logger.error(
                    "LLM call failed with non-retryable provider error: %s",
                    type(exc).__name__,
                )
                raise LLMInvocationError(
                    f"LLM provider rejected the request "
                    f"({type(exc).__name__}). See logs for details."
                ) from exc

        logger.error(
            "LLM call failed after %d attempts. Last error: %s",
            self._max_retries,
            type(last_exception).__name__ if last_exception else "unknown",
        )
        raise LLMInvocationError(
            f"LLM call failed after {self._max_retries} attempts due to "
            f"repeated transient errors."
        ) from last_exception

    def _sleep_before_retry(self, attempt: int) -> None:
        """
        Sleep for an exponential-backoff duration with jitter before the
        next retry attempt.

        Inputs:
            attempt: the attempt number that just failed (1-indexed).
        Outputs:
            None.
        """
        delay = self._retry_base_delay * (2 ** (attempt - 1))
        jitter = random.uniform(0, self._retry_base_delay)
        time.sleep(delay + jitter)

    def _extract_content(self, response: Any) -> str:
        """
        Defensively extract and sanitize the message content from a chat
        completion response.

        Inputs:
            response: the object returned by
                client.chat.completions.create().
        Outputs:
            str: the first choice's message content, with any stray
                markdown code fences stripped.
        Raises:
            LLMInvocationError: if the response has no choices, or the
                first choice's content is missing/empty.
        """
        choices = getattr(response, "choices", None)
        if not choices:
            raise LLMInvocationError(
                "LLM response contained no choices; nothing to explain."
            )

        content = choices[0].message.content
        if not content or not content.strip():
            raise LLMInvocationError("LLM response content was empty.")

        return self._strip_markdown_fences(content.strip())

    def _strip_markdown_fences(self, text: str) -> str:
        """
        Remove ```json / ``` markdown code fences that some models
        occasionally wrap JSON output in, even when
        response_format={"type": "json_object"} is requested.

        Inputs:
            text: raw, whitespace-trimmed model output.
        Outputs:
            str: text with a single leading/trailing fence removed, if
                present; otherwise the input unchanged.
        """
        if not text.startswith("```"):
            return text

        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()