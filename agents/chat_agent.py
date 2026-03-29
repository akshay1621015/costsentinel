import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def chat_with_data(question, context):
    prompt = f"""You are an expert construction cost analyst AI.
You have access to real project data. Answer questions specifically using the data.

PROJECT DATA:
{context}

QUESTION: {question}

Rules:
- Be specific, cite actual numbers from the data
- Keep answer under 4 sentences
- If you don't know, say so clearly
- Always mention the most critical finding first"""

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return resp.choices[0].message.content.strip()