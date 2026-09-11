import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
from groq import Groq

app = FastAPI()

# This allows your website widget to talk to this backend code safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to your tools using the secret keys from Render Environment Variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

class UserMessage(BaseModel):
    text: str

@app.post("/chat")
async def chat_with_bot(message: UserMessage):
    user_question = message.text

    # 1. Grab all the facts from your Supabase table
    data = supabase.table("knowledge_base").select("*").execute()
    facts = ""
    for row in data.data:
        facts += f"Topic: {row['topic']}. Info: {row['information']}\n"

    # 2. Premium Freelankarx System Prompt
    system_prompt = f"""
    You are the elite AI Sales & Strategy Assistant for Freelankarx, a premium digital studio.
    Your goal is to be professional, confident, and consultative, converting visitors into booked strategy calls.
    
    Rules:
    1. Be concise, incredibly professional, and polite. Emphasize "measurable business outcomes."
    2. Use ONLY this real business information to answer: {facts}
    3. If the user asks about pricing, mention the $1,500 starting point and emphasize that custom quotes follow a discovery call.
    4. ALWAYS end your response with a gentle, persuasive call-to-action to schedule a Strategy Call or connect on WhatsApp if they seem interested.
    5. If you don't know the answer, politely state that a human strategist can provide a custom solution and invite them to book a call.
    """

    # 3. Ask Groq to generate the beautiful response
    completion = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]
    )
    
    bot_response = completion.choices[0].message.content
    return {"response": bot_response}
