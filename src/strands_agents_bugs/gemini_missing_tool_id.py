import asyncio
import json
import os
import random

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


agent = Agent(tools=[call_api], model=model, callback_handler=None, name="gemini_agent")


def _json_default(obj: object) -> object:
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode(errors="replace")
    return str(obj)


# Async function that iterators over streamed agent events
async def process_streaming_response(agent: Agent) -> None:
    agent_stream = agent.stream_async("Can you call my API twice?")
    events: list[dict] = []
    print(f"Starting to stream events for {agent.name}")
    with open(f"agent_stream_events_{agent.name}.jsonl", "w") as f:  # noqa
        async for event in agent_stream:
            events.append(event)
            f.write(json.dumps(event, default=_json_default))
            f.write("\n")
    print(f"Finished streaming events for {agent.name}")


def main() -> None:
    asyncio.run(process_streaming_response(agent))
