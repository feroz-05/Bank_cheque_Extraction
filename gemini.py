import google.generativeai as genai
from dotenv import load_dotenv
import os
from PIL import Image

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("API key is missing. Please set the GEMINI_API_KEY in the .env file.")

def Model(image):
    genai.configure(api_key=api_key)

    # Choose a Gemini model.
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")

    prompt = """ You are given a scanned cheque, you need to give me the contents of the cheque in the JSON format like below. Strictly follow JSON format given below and dont add any metadata in the response:
    ample_output_json = {
                        "payee_name": "Deeepak Choudary",
                        "cheque_date" "05042019",
                        "bank_account_number": "35583310826",
                        "bank_name": "State Bank of India",
                        "cheque_number": "2500229009",
                        "amount": "5225000",
                        "ifsc_code": "SBIN0007556"
                    }"""
    openedImage = Image.open(image)
    response = model.generate_content([prompt,  openedImage])
    print(response.text)
    return response.text.replace("\n","").replace("```json", "").replace("```", "")
