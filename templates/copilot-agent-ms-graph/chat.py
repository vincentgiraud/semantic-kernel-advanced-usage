import os
import requests
from dotenv import load_dotenv
load_dotenv()

import chainlit as cl
from chainlit import run_sync
from chainlit import make_async

import sys
sys.path.append("./")
sys.path.append("./src")

from sk_orchestrator import *
o = Orchestrator()


@cl.on_chat_start
async def start():
    pass

@cl.on_message
async def main(message: cl.Message):
    message_content = message.content.strip().lower()
    elements = []

    # Uncomment below line to run the code using chainlit run chat.py
    answer = await o.chat(message_content)
    
    await cl.Message(content=answer, elements = elements).send()