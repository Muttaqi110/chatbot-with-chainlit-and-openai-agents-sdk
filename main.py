import os
from dotenv import load_dotenv,find_dotenv
from typing import cast
import chainlit as cl
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled
from openai.types.responses import ResponseTextDeltaEvent

load_dotenv(find_dotenv())
set_tracing_disabled(disabled=True)
gemini_api_key = os.getenv("GEMINI_API_KEY")

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client)
agent: Agent = Agent(name="Assistant", instructions="You are a helpful assistant", model=model)


@cl.on_chat_start
async def start():
    cl.user_session.set("history", [])


@cl.on_message
async def main(message: cl.Message):
    temp = cl.Message(content="")
    temp.send()

    history = cl.user_session.get("history")
    history.append({"role": "user", "content": message.content})
    
    result = Runner.run_streamed(starting_agent=agent, input=history)
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data,ResponseTextDeltaEvent ):
            token = event.data.delta
            await temp.stream_token(token)

    history.append({"role": "assistant", "content": result.final_output})
    cl.user_session.set("history", history)
    # msg = result.final_output
    # await cl.Message(content=msg).send()