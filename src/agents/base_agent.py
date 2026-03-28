"""Base agent with LiteLLM-powered agentic tool-call loop."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentBrief:
    """Output of a single agent's analysis run."""

    agent_name: str
    ticker: str
    content: str  # Markdown-formatted analysis
    structured_data: dict = field(default_factory=dict)
    tool_calls_made: list[str] = field(default_factory=list)
    tokens_used: int = 0
    error: str | None = None


class BaseAgent(ABC):
    """Abstract LiteLLM agent with an agentic tool-call execution loop.

    Subclasses must define:
      name          — display name shown in the dashboard
      system_prompt — the agent's persona and task description
      tool_schemas  — list of litellm-format tool definitions
      _dispatch_tool(name, args) -> dict  — sync or async tool handler
    """

    name: str = "BaseAgent"
    system_prompt: str = ""
    tool_schemas: list[dict] = []

    def __init__(self):
        from src.config import settings

        self._model = settings.agent_model
        self._timeout = settings.agent_timeout_seconds
        self._max_retries = settings.agent_max_retries

    async def run(self, context: dict) -> AgentBrief:
        """Execute the full agentic loop and return a brief.

        Args:
            context: dict with at minimum ``ticker`` key; may include prior
                     agent briefs for downstream agents.
        """
        import litellm

        ticker = context.get("ticker", "UNKNOWN").upper()
        messages = self._build_messages(context)
        tool_calls_made: list[str] = []
        total_tokens = 0
        last_error: str | None = None

        for attempt in range(self._max_retries + 1):
            try:
                # Agentic loop — keep calling until the model stops requesting tools
                loop_messages = list(messages)
                for _ in range(10):  # safety cap on tool-call rounds
                    kwargs: dict[str, Any] = {
                        "model": self._model,
                        "messages": loop_messages,
                        "timeout": self._timeout,
                    }
                    if self.tool_schemas:
                        kwargs["tools"] = self.tool_schemas
                        kwargs["tool_choice"] = "auto"

                    response = await asyncio.wait_for(
                        litellm.acompletion(**kwargs),
                        timeout=self._timeout + 5,
                    )

                    usage = getattr(response, "usage", None)
                    if usage:
                        total_tokens += getattr(usage, "total_tokens", 0) or 0

                    msg = response.choices[0].message
                    tool_calls = getattr(msg, "tool_calls", None)

                    if not tool_calls:
                        # Final text response — we're done
                        content = msg.content or ""
                        return AgentBrief(
                            agent_name=self.name,
                            ticker=ticker,
                            content=content,
                            structured_data=self._parse_structured(content),
                            tool_calls_made=tool_calls_made,
                            tokens_used=total_tokens,
                        )

                    # Execute tool calls and feed results back
                    loop_messages.append(
                        {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments,
                                    },
                                }
                                for tc in tool_calls
                            ],
                        }
                    )

                    for tc in tool_calls:
                        tool_calls_made.append(tc.function.name)
                        try:
                            args = json.loads(tc.function.arguments)
                        except json.JSONDecodeError:
                            args = {}
                        result = await self._dispatch_tool(tc.function.name, args)
                        loop_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": json.dumps(result),
                            }
                        )

                # Exceeded tool-call rounds
                return AgentBrief(
                    agent_name=self.name,
                    ticker=ticker,
                    content="Analysis incomplete — exceeded tool call limit.",
                    tool_calls_made=tool_calls_made,
                    tokens_used=total_tokens,
                    error="tool_call_limit_exceeded",
                )

            except asyncio.TimeoutError:
                last_error = "timeout"
                logger.warning(f"{self.name} timed out (attempt {attempt + 1})")
                if attempt < self._max_retries:
                    await asyncio.sleep(1)
            except Exception as exc:
                last_error = str(exc)
                logger.warning(f"{self.name} error (attempt {attempt + 1}): {exc}")
                if attempt < self._max_retries:
                    await asyncio.sleep(1)

        return AgentBrief(
            agent_name=self.name,
            ticker=ticker,
            content=f"Analysis failed after {self._max_retries + 1} attempts.",
            tool_calls_made=tool_calls_made,
            tokens_used=total_tokens,
            error=last_error,
        )

    def _build_messages(self, context: dict) -> list[dict]:
        """Build the initial messages list from context."""
        user_msg = self._build_user_message(context)
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_msg},
        ]

    @abstractmethod
    def _build_user_message(self, context: dict) -> str:
        """Construct the user-turn prompt from context."""
        ...

    async def _dispatch_tool(self, tool_name: str, args: dict) -> dict:
        """Route tool calls to the right implementation. Override in subclasses."""
        return {"error": f"Tool not implemented: {tool_name}"}

    def _parse_structured(self, content: str) -> dict:
        """Try to extract key-value pairs from the agent's markdown output."""
        result = {}
        for line in content.splitlines():
            for key in ("SIGNAL", "DECISION", "CONFIDENCE", "RISK RATING", "VERDICT", "SENTIMENT"):
                if line.upper().startswith(key + ":"):
                    value = line.split(":", 1)[1].strip()
                    result[key.lower().replace(" ", "_")] = value
        return result
