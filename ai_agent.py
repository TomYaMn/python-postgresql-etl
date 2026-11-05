import json
import PyPDF2
from google import genai
from google.genai import types
from config import API_KEY
from prompts import AI_SYSTEM_PROMPT
#from openai import OpenAI

## openAI
# ai_client = OpenAI(api_key=API_KEY)

# Initialize Gemini
ai_client = genai.Client(api_key=API_KEY)

def extract_text_from_file(uploaded_file):
    text_content = ""
    if uploaded_file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            text_content += page.extract_text() + "\n"
    else:
        text_content = uploaded_file.read().decode("utf-8")
    return text_content

def process_bank_statement(text_content):
    response = ai_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"Extract these transactions:\n\n{text_content}",
        config=types.GenerateContentConfig(
            system_instruction=AI_SYSTEM_PROMPT,
            temperature=0.0,
            response_mime_type="application/json"
        )
    )
    
    raw_json = response.text.strip()
    
    # Fallback cleanup
    if raw_json.startswith("```json"):
        raw_json = raw_json[7:-3]
    elif raw_json.startswith("```"):
        raw_json = raw_json[3:-3]
        
    return json.loads(raw_json)


def process_bank_statement_openai(text_content):
    response = ai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract these transactions:\n\n{text_content}"}
        ],
        temperature=0.0
    )

    raw_json = response.choices[0].message.content.strip()
    if raw_json.startswith("```json"):
        raw_json = raw_json[7:-3]
        
    return json.loads(raw_json)

