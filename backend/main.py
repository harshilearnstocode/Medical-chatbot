from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your React app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    messages = data.get("messages", [])

    if not messages or not any(m.get("sender") == "user" and m.get("text") for m in messages):
        return {"response": "⚠️ Please provide a medical symptom or question.", "suggestions": []}

    # Get last user message text
    last_user_msg = [m["text"] for m in messages if m["sender"] == "user"][-1]

    system_prompt = (
        "You are a compassionate medical assistant chatbot. "
        "You analyze symptoms described by the user, ask clarifying questions if needed, "
        "and recommend the most appropriate medical department or action. "
        "You do NOT provide a diagnosis or prescription. Always be clear, concise, and empathetic."
    )

    openai_messages = [
        {"role": "system", "content": system_prompt},
    ]

    for msg in messages:
        if "text" in msg:
            role = "user" if msg["sender"] == "user" else "assistant"
            openai_messages.append({"role": role, "content": msg["text"]})

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=openai_messages,
            max_tokens=300,
            temperature=0.7,
        )
        answer = response.choices[0].message.content.strip()
        return {"response": answer, "suggestions": []}
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return {"response": "⚠️ Sorry, I am having trouble processing your request right now.", "suggestions": []}
