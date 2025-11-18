import asyncio
import json
import os
import random
import types
from collections.abc import Awaitable, Callable
from typing import Any

from strands import Agent, tool
from strands.models.gemini import GeminiModel

from strands_agents_bugs.env import load_env


if not load_env():
    raise OSError("Failed to load environment variables")

model: GeminiModel = GeminiModel(
    client_args={"api_key": os.getenv("GOOGLE_AI_API_KEY")},
    model_id="gemini-2.5-flash",
)


@tool
async def call_api() -> str:
    """Call API asynchronously."""

    await asyncio.sleep(3)  # simulated api call
    return f"API result: {random.randint(1, 1000)}"


def make_tool(
    tool_name: str,
) -> Callable[[str | None, int | None], Awaitable[dict[str, Any]]]:
    """Create an async tool function for a specific source."""

    async def tool_impl() -> dict[str, Any]:
        """Call API asynchronously."""

        await asyncio.sleep(3)  # simulated api call
        return f"API result: {random.randint(1, 1000)}"

    # Create a new function with the correct name before applying the decorator
    tool_func = types.FunctionType(
        tool_impl.__code__,
        tool_impl.__globals__,
        name=tool_name,
        argdefs=tool_impl.__defaults__,
        closure=tool_impl.__closure__,
    )
    # Copy other function attributes
    tool_func.__doc__ = tool_impl.__doc__
    tool_func.__annotations__ = tool_impl.__annotations__
    tool_func.__kwdefaults__ = tool_impl.__kwdefaults__

    # Now apply the decorator to the properly named function
    return tool(tool_func)


agent_1 = Agent(tools=[call_api], model=model, callback_handler=None, name="normal_agent")
tool_2 = make_tool("call_api")
agent_2 = Agent(tools=[tool_2], model=model, callback_handler=None, name="duplicate_agent")


def _json_default(obj: object) -> object:
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode(errors="replace")
    return str(obj)


def _write_events_to_file(agent_name: str, events: list[dict]) -> None:
    with open(f"agent_stream_events_{agent_name}.jsonl", "w") as f:
        for event in events:
            f.write(json.dumps(event, default=_json_default))
            f.write("\n")


# Async function that iterators over streamed agent events
async def process_streaming_response(agent: Agent) -> None:
    agent_stream = agent.stream_async("Can you call my API twice?")
    events: list[dict] = []
    print(f"Starting to stream events for {agent.name}")
    async for event in agent_stream:
        events.append(event)
    print(f"Finished streaming events for {agent.name}")
    await asyncio.to_thread(_write_events_to_file, agent.name, events)


def main() -> None:
    asyncio.run(process_streaming_response(agent_1))
    asyncio.run(process_streaming_response(agent_2))
