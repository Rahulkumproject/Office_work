from http.client import responses

import google.generativeai as genai
import json
import docx
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["api_key"])

def read_word_file(file_path):
    doc= docx.Document(file_path)
    full_text=[]
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def extract_field_with_ai(document_text):
    model= genai.GenerativeModel('gemini-2.5-flash')
    prompt=f"""
            Analyze this contract text and extract the following fields in JSON format:
            1. TIN (Tax ID) - If not found, return null.
            2. NPI (National Provider Identifier) - If not found, return null.
            3. CounterParty_Name (The provider or group name).
            4. Contract_Type (Must be either 'Base' or 'Amendment').
            5. Effective_Date (Format YYYY-MM-DD).
            Text:
            {document_text}
            Return only valid JSON. no markdown.
            """
    response= model.generate_content(prompt)
    clean_json= response.text.replace("'''json","").replace("'''","").strip()
    return json.loads(clean_json)

file_name= "Contracts/contract_1.docx"
print("Reading file...")
text_content= read_word_file(file_name)
print("Extracting the data")
extracted_data= extract_field_with_ai(text_content)
print("Extracted Data:")
print(json.dumps(extracted_data, indent=4))


