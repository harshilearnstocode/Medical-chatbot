from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import logging
from dotenv import load_dotenv
from typing import TypedDict, List, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatState(TypedDict):
    messages: List[Dict[str, Any]]

def gpt4o_medical_advice(state: ChatState) -> ChatState:
    messages = state["messages"]
    user_input = messages[-1]["content"]

    system_prompt = (
        "You are a compassionate medical assistant chatbot. "
        "You analyze symptoms described by the user, ask clarifying questions if needed, "
        "and recommend the most appropriate medical department or action. "
        "You do NOT provide a diagnosis or prescription. Always be clear, concise, and empathetic."
    )

    chat_history = [
        SystemMessage(content=system_prompt)
    ]

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            chat_history.append(HumanMessage(content=content))
        elif role == "assistant":
            chat_history.append(AIMessage(content=content))

    try:
        role_map = {
            "human": "user",
            "ai": "assistant",
            "system": "system"
        }

        openai_chat_messages = [
            {"role": role_map.get(m.type, "user"), "content": m.content} for m in chat_history
        ]

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=openai_chat_messages,
            max_tokens=300,
            temperature=0.7,
        )


        reply = response.choices[0].message.content.strip()

        return {
            "messages": messages + [{"role": "assistant", "content": reply}]
        }
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return {
            "messages": messages + [{"role": "assistant", "content": "⚠️ I'm having trouble processing your request."}]
        }

graph = StateGraph(ChatState)
graph.add_node("GPT-4o", gpt4o_medical_advice)
graph.set_entry_point("GPT-4o")
graph.set_finish_point("GPT-4o")
lang_graph = graph.compile()

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    messages = data.get("messages", [])

    if not messages or not any(m.get("sender") == "user" and m.get("text") for m in messages):
        return {"response": "⚠️ Please provide a medical symptom or question.", "suggestions": []}

    formatted_messages = []
    for msg in messages:
        if "text" in msg:
            role = "user" if msg["sender"] == "user" else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg["text"]
            })

    final_state = lang_graph.invoke({"messages": formatted_messages})

    assistant_replies = [m for m in final_state["messages"] if m["role"] == "assistant"]
    answer = assistant_replies[-1]["content"] if assistant_replies else "⚠️ No response generated."

    return {"response": answer, "suggestions": []}
