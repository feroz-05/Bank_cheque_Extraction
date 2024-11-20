import base64
import os
import json
from datetime import datetime
import fitz  # PyMuPDF
import pandas as pd
import streamlit as st
from dbconnection import insert_cheque_details as insert_cheque_detials, fetch_cheque_details as fetch_cheque_detials, get_db_connection
from gemini import Model
import matplotlib.pyplot as plt
import numpy as np

# Inject custom CSS
def set_background(image_file):
    with open(image_file, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Call the function with your image file
set_background("bankbg.JPG")

st.markdown("""
    <style>
        .css-ffhzg2 { background-color: #000; color: #fff; }
        .stButton>button { background-color: #e60000; color: white; border-radius: 8px; padding: 12px 24px; font-size: 16px; font-weight: bold; border: none; cursor: pointer; }
        .stButton>button:hover { background-color: #b30000; }
        .stTextInput>div>input, .stSelectbox>div>div>input, .stTextArea>div>textarea { background-color: #333; color: white; border-radius: 5px; border: 2px solid #e60000; padding: 10px; }
        .stSidebar, .stSidebar .sidebar-content { background-color: #1a1a1a; color: white; }
        h1, h2, h3 { color: #fd0e0e; }
        a { color: #e60000; text-decoration: underline; }
        .stCheckbox>label, .stRadio>label { color: white; }
        .stMarkdown { margin-left:20px color: #fff; }
        .stVerticalBlock{
            background: rgba(124, 155, 223, 0.3); /* Semi-transparent background */
            backdrop-filter: blur(10px); /* Blur effect */
            border-radius: 10px;
            width:800px;
            padding:20px 50px;
    </style>
""", unsafe_allow_html=True)

# Constants
TEMP_IMAGE_DIR = "temp_images"
LOGIN_EMAIL, LOGIN_PASSWORD = "feroz@gmail.com", "feroz"

# Ensure temporary directory exists
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

# Helper Functions
def save_uploaded_file(uploaded_file):
    """Save uploaded file to a temporary directory."""
    file_path = os.path.join(TEMP_IMAGE_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path

def clear_temp_files():
    """Clear all files in the temporary directory."""
    for file in os.listdir(TEMP_IMAGE_DIR):
        os.remove(os.path.join(TEMP_IMAGE_DIR, file))

def convert_pdf_to_images(pdf_path):
    """Convert PDF to images and return their paths."""
    pdf_document = fitz.open(pdf_path)
    image_paths = [os.path.join(TEMP_IMAGE_DIR, f"Cheque_{i+1}.jpg") for i in range(len(pdf_document))]
    for page, image_path in zip(pdf_document, image_paths):
        page.get_pixmap().save(image_path)
    pdf_document.close()
    return image_paths

def preprocess_cheque_detials(details):
    """Preprocess extracted cheque details."""
    date_str = details.get("cheque_date", "")
    formatted_date = None
    if date_str:
        try:
            formatted_date = datetime.strptime(date_str, "%d%m%Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return {
        "payee_name": details.get("payee_name", None),
        "cheque_no": details.get("cheque_number", None),
        "amount": float(details.get("amount", 0)) if details.get("amount") else None,
        "bank_account_no": details.get("bank_account_number", None),
        "bank_name": details.get("bank_name", None),
        "ifsc_code": details.get("ifsc_code", None),
        "cheque_date": formatted_date,
    }

def get_column_names():
    """Retrieve column names dynamically from the database."""
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM cheque_detials LIMIT 0")
        return [desc[0] for desc in cursor.description]

def clean_amount(amount):
    """Clean and convert amount strings."""
    if isinstance(amount, str):
        amount = amount.strip().replace(",", "").replace("/-", "")
        try:
            return float(amount)
        except ValueError:
            return None
    return amount

# Plot Functions
def plot_pie_chart(amounts, labels):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(amounts, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3(np.linspace(0, 1, len(amounts))), wedgeprops={'edgecolor': 'black'})
    ax.axis('equal')
    ax.set_title("Top 5 Bank Names by Cheque Amount", fontsize=14)
    return fig

def plot_bar_chart(amounts, labels):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(labels, amounts, color=plt.cm.Blues(np.linspace(0.3, 0.7, len(amounts))), edgecolor='black')
    ax.set_xlabel('Payee Names')
    ax.set_ylabel('Amount')
    ax.set_title('Top 5 Highest Cheque Amounts by Payee Name')
    ax.tick_params(axis='x', rotation=45)
    return fig

# Pages
def home_page():
    st.title("Bank Cheque Extration")
    st.subheader("What we offer!!")
    st.write("""
    1. Upload Bank Cheque pdf's from anywhere and anytime.
    2. we provide you High Accuracy OCR model for extraction of Cheque data.
    3. Download your Cheque data in CSV file.
    4. Visualize your Cheque data in Bar Chart and Pie Chart.
""")
    st.subheader("Project Overview")
    st.write("""
        **Project Tasks:**  
        1. Read and parse PDFs.  
        2. Convert pages to images.  
        3. Extract cheque details using OCR.  
        4. Store details in PostgreSQL.  
        5. Visualize and export analytics.
    """)

def upload_page():
    st.title("Upload Cheque PDFs or Images")
    uploaded_file = st.file_uploader("Upload a PDF or image file", type=["pdf", "jpg", "jpeg", "png"])
    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file)
        if uploaded_file.type == "application/pdf":
            image_paths = convert_pdf_to_images(file_path)
            for image_path in image_paths:
                st.image(image_path, caption="Extracted Image", use_column_width=True)
                try:
                    details = json.loads(Model(image_path))
                    print(details)
                    insert_cheque_detials(preprocess_cheque_detials(details))
                    st.success("Cheque details saved to the database.")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            try:
                details = json.loads(Model(image_path))
                print(details)
                insert_cheque_detials(preprocess_cheque_detials(details))
                st.success("Cheque details saved to the database.")
            except Exception as e:
                st.error(f"Error: {e}")
        clear_temp_files()

def analytics_page():
    st.title("Analytics Dashboard")
    rows = fetch_cheque_detials()
    if rows:
        columns = get_column_names()  # Ensure dynamic column retrieval works correctly
        df = pd.DataFrame(rows, columns=columns)
                # Sorting functionality: Ascending / Descending
        sort_by = st.selectbox("Sort by", ["Amount", "Payee Name", "Bank Name"])
        sort_order = st.radio("Sort order", ("Ascending", "Descending"))

        if sort_by == "Amount":
            df_sorted = df.sort_values(by="amount", ascending=(sort_order == "Ascending"))
        elif sort_by == "Payee Name":
            df_sorted = df.sort_values(by="payee_name", ascending=(sort_order == "Ascending"))
        elif sort_by == "Bank Name":
            df_sorted = df.sort_values(by="bank_name", ascending=(sort_order == "Ascending"))
        
        st.subheader(f"Sorted Data: {sort_by} ({sort_order})")
        st.dataframe(df_sorted)

        if "amount" in df.columns:
            df["amount"] = df["amount"].apply(clean_amount)  # Clean and convert 'amount' to numeric
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
            df.dropna(subset=["amount"], inplace=True)

            # Top 5 banks by total amount
            top_5_banks = df.groupby("bank_name")["amount"].sum().nlargest(5)

            # Visualizations
            bar_chart = plot_bar_chart(top_5_banks.values, top_5_banks.index)
            pie_chart = plot_pie_chart(top_5_banks.values, top_5_banks.index)
            st.pyplot(bar_chart)
            st.pyplot(pie_chart)
    else:
        st.error("No cheque details found in the database.")


# Sidebar Navigation
PAGES = {"Home": home_page, "Upload": upload_page, "Analytics": analytics_page}
st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Go to", list(PAGES.keys()))
PAGES[selected_page]()
