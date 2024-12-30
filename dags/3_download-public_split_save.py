from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
import requests
import logging
import os

from sklearn.model_selection import train_test_split

# Ścieżka do pliku JSON z danymi uwierzytelniającymi dla Google API
SERVICE_ACCOUNT_FILE = 'airflow-442316-8c5dfa0cf9c0.json'
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Link do pliku CSV z Kaggle
DATA_URL = "https://www.kaggleusercontent.com/datasets/sumansharmadataworld/depression-surveydataset-for-analysis/final_depression_dataset_1.csv"
PROCESSED_DATA_PATH = '/opt/airflow/processed_data/'

def download_data(**kwargs):
    try:
        response = requests.get(DATA_URL)
        response.raise_for_status()

        os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)
        file_path = os.path.join(PROCESSED_DATA_PATH, 'downloaded_data.csv')

        with open(file_path, 'wb') as file:
            file.write(response.content)

        logging.info("Data downloaded successfully from Kaggle.")
        kwargs['ti'].xcom_push(key='file_path', value=file_path)

    except Exception as e:
        logging.error(f"Error downloading data: {e}")
        raise

def split_data(**kwargs):
    file_path = kwargs['ti'].xcom_pull(key='file_path')
    data = pd.read_csv(file_path)

    # Podział na zbiór modelowy (70%) i douczeniowy (30%)
    train, test = train_test_split(data, test_size=0.3, random_state=42)

    train_file = os.path.join(PROCESSED_DATA_PATH, 'train_data.csv')
    test_file = os.path.join(PROCESSED_DATA_PATH, 'test_data.csv')

    train.to_csv(train_file, index=False)
    test.to_csv(test_file, index=False)

    kwargs['ti'].xcom_push(key='train_file', value=train_file)
    kwargs['ti'].xcom_push(key='test_file', value=test_file)

    logging.info("Data split into train and test sets successfully.")

def upload_to_google_sheets(**kwargs):
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    train_file = kwargs['ti'].xcom_pull(key='train_file')
    test_file = kwargs['ti'].xcom_pull(key='test_file')

    train_data = pd.read_csv(train_file)
    test_data = pd.read_csv(test_file)

    try:
        spreadsheet = client.open("Airflow")
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create("Airflow")

    # Zapis zbioru modelowego
    try:
        train_sheet = spreadsheet.worksheet("Zbiór modelowy")
    except gspread.WorksheetNotFound:
        train_sheet = spreadsheet.add_worksheet(title="Zbiór modelowy", rows=str(len(train_data) + 1),
                                                cols=str(train_data.shape[1]))
    train_sheet.clear()
    train_sheet.update([train_data.columns.values.tolist()] + train_data.values.tolist())

    # Zapis zbioru douczeniowego
    try:
        test_sheet = spreadsheet.worksheet("Zbiór douczeniowy")
    except gspread.WorksheetNotFound:
        test_sheet = spreadsheet.add_worksheet(title="Zbiór douczeniowy", rows=str(len(test_data) + 1),
                                               cols=str(test_data.shape[1]))
    test_sheet.clear()
    test_sheet.update([test_data.columns.values.tolist()] + test_data.values.tolist())

    logging.info("Data uploaded to Google Sheets successfully.")

# Definicja DAG
with DAG(
        dag_id='3_download_public_split_save',
        default_args={
            'owner': 'airflow',
            'depends_on_past': False,
            'email_on_failure': False,
            'retries': 1,
            'retry_delay': timedelta(minutes=5),
        },
        description='DAG do pobrania danych, podziału i zapisu do Google Sheets',
        schedule_interval=None,
        start_date=datetime(2023, 12, 1),
        catchup=False,
) as dag:

    download_task = PythonOperator(
        task_id='download_data',
        python_callable=download_data,
        provide_context=True,
    )

    split_task = PythonOperator(
        task_id='split_data',
        python_callable=split_data,
        provide_context=True,
    )

    upload_task = PythonOperator(
        task_id='upload_to_google_sheets',
        python_callable=upload_to_google_sheets,
        provide_context=True,
    )

    download_task >> split_task >> upload_task
