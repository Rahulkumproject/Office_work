import csv
from http.client import responses

import google.generativeai as genai
import os
import json
import glob
import docx
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

load_dotenv()

genai.configure(api_key=os.environ["api_key"])

def read_word_file(file_path):
    doc=docx.Document(file_path)
    full_text=[]
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def extract_field_with_ai(document_text):
    model= genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
        Analyze this contract text and extract the following fields in JSON format:
        1. TIN (Tax ID) - If not found, return null.
        2. NPI (National Provider Identifier) - If not found, return null.
        3. CounterParty_Name (The provider or group name).
        4. Contract_Type (Must be either 'Base' or 'Amendment').
        5. Effective_Date (Format YYYY-MM-DD).

        Text:
        {document_text}

        Return ONLY valid JSON. No markdown.
        """
    try:
        response= model.generate_content(prompt)
        clean_json= response.text.replace("'''json","").replace("'''","").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI error: {e}")
        return None
def load_pes_database(csv_file_path):
    valid_npis=[]
    try:
        with open(csv_file_path,"r") as file:
            reader= csv.DictReader(file)
            for row in reader:
                if row["Status"]=="Active":
                    valid_npis.append(row["NPI"])
    except FileNotFoundError:
        print("PES database not found.")
    return valid_npis


folder="Contracts"
docx_files=glob.glob(f"{folder}/*.docx")
pes_db_file= "pes_database.csv"
print("Loading PES database...")
authorized_npis= load_pes_database(pes_db_file)
print(f"Loaded {len(authorized_npis)} active NPIs from PES database.")

print(f"Found {len(docx_files)} contracts in '{folder}'")
all_results=[]
for file_path in docx_files:
    print(f" Processing {file_path}...")
    text=read_word_file(file_path)
    data= extract_field_with_ai(text)
    if data:
        data["Source_File"] = os.path.basename(file_path)
        extracted_npi= data.get("NPI")
        if extracted_npi in authorized_npis:
            data["PES_Active_status"]= True
        else:
            data["PES_Active_status"]= False
        file_name=data["Source_File"]
        if extracted_npi and extracted_npi in file_name:
            data["Metadata_Match"]= "Match"
        else:
            data["Metadata_Match"]= "No Match"
        all_results.append(data)


print("\n batch completed")
print(json.dumps(all_results, indent=4))

print("Generating excel report...")
df=pd.DataFrame(all_results)
desired_columns = [
    "Source_File",
    "PES_Active_status",
    "CounterParty_Name",
    "NPI",
    "TIN",
    "Contract_Type",
    "Effective_Date",
    "Metadata_Match"
]

cols_to_use= [c for c in desired_columns if c in df.columns]
df= df[cols_to_use]
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_file_name= f"Optum_POC_Report_{timestamp}.xlsx"
df.to_excel(report_file_name, index=False)
print(f"Report saved as {report_file_name}")








