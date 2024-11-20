import psycopg2
from psycopg2 import sql
import logging

# Database connection parameters
connection_params = {
    "host": "localhost",       # Database server IP or "localhost" if on the same machine
    "database": "postgres",    # Name of your database
    "user": "postgres",        # Your PostgreSQL username
    "password": "feroz"        # Your PostgreSQL password
}

# Set up logging
logging.basicConfig(level=logging.INFO)

def get_db_connection():
    """
    Establish and return a database connection.
    """
    try:
        connection = psycopg2.connect(**connection_params)
        logging.info("Database connection established successfully.")
        return connection
    except Exception as error:
        logging.error(f"Error connecting to the database: {error}")
        raise

def insert_cheque_details(details):
    """
    Insert cheque details into the 'cheque_detials' table.

    Args:
        details (dict): A dictionary containing cheque details.
    """
    insert_query = """
        INSERT INTO cheque_detials (
            payee_name, cheque_no, amount, bank_account_no, bank_name, ifsc_code, cheque_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    # data = (
    #     details.get("payee_name"),
    #     details.get("cheque_date"),
    #     details.get("cheque_no"),
    #     details.get("bank_account_no"),
    #     details.get("bank_name"),
    #     details.get("amount"),
    #     details.get("ifsc_code")
    # )

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(insert_query, (
                    details["payee_name"],
                    details["cheque_no"],
                    details["amount"],
                    details["bank_account_no"],
                    details["bank_name"],
                    details["ifsc_code"],
                    details["cheque_date"],
                ))
                connection.commit()
                logging.info("Cheque details inserted successfully.")
    except Exception as error:
        logging.error(f"Error inserting cheque details: {error}")
        raise

def fetch_cheque_details():
    """
    Fetch all cheque details from the 'cheque_detials' table.

    Returns:
        list: A list of tuples containing cheque details.
    """
    select_query = "SELECT * FROM cheque_detials"

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(select_query)
                rows = cursor.fetchall()
                logging.info(f"Fetched {len(rows)} cheque details from the database.")
                return rows
    except Exception as error:
        logging.error(f"Error fetching cheque details: {error}")
        return []

def get_column_names():
    """
    Retrieve column names dynamically from the 'cheque_detials' table.

    Returns:
        list: A list of column names from the table.
    """
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM cheque_detials LIMIT 1")
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                if not column_names:
                    logging.warning("No columns found in 'cheque_detials' table.")
                return column_names
    except Exception as error:
        logging.error(f"Error retrieving column names: {error}")
        raise
