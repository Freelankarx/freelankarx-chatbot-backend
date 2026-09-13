import os
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
from groq import Groq

# Initialize FastAPI app
app = FastAPI()

# Allow your Vercel frontend to talk to this Render backend safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Environment Variables from Render
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Debug prints to verify keys are loading in Render logs
print(f"DEBUG: SUPABASE_URL loaded: {bool(SUPABASE_URL)}")
print(f"DEBUG: SUPABASE_KEY loaded: {bool(SUPABASE_KEY)}")
print(f"DEBUG: GROQ_API_KEY loaded: {bool(GROQ_API_KEY)}")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("DEBUG: Successfully initialized Supabase and Groq clients.")
except Exception as e:
    print(f"DEBUG: Initialization error: {e}")

# Define the expected format of the incoming message
class UserMessage(BaseModel):
    text: str

@app.post("/chat")
async def chat_with_bot(message: UserMessage):
    try:
        user_question = message.text

        # 1. Grab all the facts from your Supabase table
        data = supabase.table("knowledge_base").select("*").execute()
        facts = ""
        if data.data:
            for row in data.data:
                facts += f"Topic: {row['topic']}. Info: {row['information']}\n"
        else:
            facts = "No facts found in database. Please check Supabase table name and RLS policies."

        # 2. Premium Freelankarx System Prompt
        system_prompt = f"""
        You are the Senior Sales Strategist & Director of Growth at Freelankarx, a premium digital studio.
        
        Your primary mission is to provide expert consultative guidance, uncover visitor business challenges, demonstrate immediate authority, and smoothly convert qualified leads into booked strategy calls or WhatsApp conversations
        CORE CONVERSION & PSYCHOLOGY RULES:
        1. POSITION AS THE GUIDE: Always position the prospect as the Hero pursuing business growth, and Freelankarx as their expert Guide. Speak directly to their growth objectives, lead conversion gaps, and market positioning.
        2. DIAGNOSE BEFORE PITCHING: Never jump straight into pitching features. Ask 1 calibrated open-ended question starting with "What" or "How" (e.g., "What is the main bottleneck in your current lead conversion process?") to get the prospect invested in the conversation.
        3. VALUE-FIRST PRICING FRAME: If asked about pricing, lead with value and outcome first before stating figures. State: "Custom growth systems and website builds start at $1,500, designed specifically to yield measurable ROI. Because every project is tailored to your business model, exact scope and execution strategy are finalized during a discovery call."
        4. LOW-FRICTION CALL TO ACTION: End every interaction with a single, clear, low-pressure invitation to take the next step. Invite them to schedule a 15-minute Strategy Call or connect directly on WhatsApp at 09068526805.
        5. FALLBACK & OFF-RAMP: If a query cannot be answered using the provided knowledge or requires custom scoping, state politely that a human growth strategist will craft a custom roadmap for them, and invite them to reach out via WhatsApp or email at info@freelankarx.com / freelankarx@gmail.com.
        
        STRICT TONE & FORMATTING RULES:
        - TONE: Warm, confident, consultative, and human. ABSOLUTELY NEVER use robotic AI phrases ("As an AI", "I am a chatbot", "Here is the information").
        - PARAGRAPHS: Keep responses short and mobile-optimized (maximum 2–3 sentences per paragraph).
        - ELEGANT FORMATTING: Do NOT use excessive bullet points, messy markdown, or long walls of text. Keep copy clean and effortless to skim.
        - STRICT GROUNDING: Restrict all business factual claims exclusively to this provided information: {facts}"""

        # 3. Ask Groq to generate the beautiful response
        # UPDATED: Using openai/gpt-oss-120b, the current standard, highly-capable model available on Groq
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",  
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ]
        )
        
        bot_response = completion.choices[0].message.content
        return {"response": bot_response}
    
    except Exception as e:
        # Fallback error handler to prevent silent 500 crashes
        error_details = traceback.format_exc()
        print(f"ERROR in /chat endpoint: {error_details}")
        return {"response": f"🚨 DEBUG ERROR: {str(e)}\n\nPlease check Render logs for details."}
