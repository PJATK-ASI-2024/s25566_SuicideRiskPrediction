import gspread
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta
import pandas as pd
from google.oauth2.service_account import Credentials
import pickle
from sklearn.metrics import accuracy_score, precision_score, recall_score
import os
import logging

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ścieżka do pliku JSON z danymi uwierzytelniającymi dla Google API
SERVICE_ACCOUNT_FILE = 'airflow-442316-8c5dfa0cf9c0.json'
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
MODEL_FILE_PATH = '/opt/airflow/models/model.pkl'
CRITICAL_ACCURACY_THRESHOLD = 0.80


# Funkcja do ładowania modelu
def load_model():
    if os.path.exists(MODEL_FILE_PATH):
        with open(MODEL_FILE_PATH, 'rb') as f:
            model = pickle.load(f)
        logger.info("Model został poprawnie załadowany.")
        return model
    else:
        raise FileNotFoundError(f'Nie znaleziono pliku modelu w ścieżce: {MODEL_FILE_PATH}')


def fetch_data_from_cloud(**kwargs):
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        spreadsheet = client.open("Airflow")
        sheet = spreadsheet.worksheet("Zbiór modelowy")
        data = pd.DataFrame(sheet.get_all_records())

        # Zapis danych do lokalnego pliku CSV
        file_path = '/opt/airflow/processed_data/cloud_data.csv'
        data.to_csv(file_path, index=False)
        kwargs['ti'].xcom_push(key='file_path', value=file_path)
        logging.info("Data fetched from Google Sheets successfully.")

    except gspread.exceptions.SpreadsheetNotFound:
        logging.error("Spreadsheet not found. Check the name or permissions.")
        raise
    except Exception as e:
        logging.error(f"Error fetching data from Google Sheets: {e}")


# Funkcja do oceny jakości modelu na nowych danych
def evaluate_model(**kwargs):
    try:

        # Ładowanie danych
        file_path = kwargs['ti'].xcom_pull(key='file_path')
        data = pd.read_csv(file_path)

        target_column = 'Have you ever had suicidal thoughts ?_Yes'
        if target_column not in data.columns:
            raise KeyError("Kolumna docelowa nie została znaleziona w danych.")

        X = data.drop(target_column, axis=1)
        y = data[target_column]

        # Ładowanie modelu
        model = load_model()

        # Dopasowanie liczby funkcji do modelu
        if X.shape[1] != model.n_features_in_:
            X = X.iloc[:, :model.n_features_in_]

        # Przewidywanie i ocena
        y_pred = model.predict(X)
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, zero_division=1)
        recall = recall_score(y, y_pred, zero_division=1)

        # Zapis wyników do XCom
        kwargs['ti'].xcom_push(key='model_accuracy', value=accuracy)
        kwargs['ti'].xcom_push(key='model_precision', value=precision)
        kwargs['ti'].xcom_push(key='model_recall', value=recall)
        logger.info(
            f"Model został oceniony z dokładnością: {accuracy:.2f}, precyzją: {precision:.2f}, recall: {recall:.2f}")

        # Sprawdzenie, czy jakość modelu jest poniżej krytycznego progu i zapisanie statusu do XCom
        if accuracy < CRITICAL_ACCURACY_THRESHOLD:
            kwargs['ti'].xcom_push(key='model_status', value='failed')
            logger.warning(
                f"Jakość modelu (accuracy) spadła poniżej progu krytycznego: {accuracy:.2f} < {CRITICAL_ACCURACY_THRESHOLD}")
        else:
            kwargs['ti'].xcom_push(key='model_status', value='passed')
    except FileNotFoundError:
        raise FileNotFoundError(f"Nie znaleziono nowego pliku danych w ścieżce: {file_path}")
    except Exception as e:
        kwargs['ti'].xcom_push(key='model_status', value='failed')
        logging.error(f"Wystąpił błąd podczas oceny: {e}")


def run_tests(**kwargs):
    failed_tests = []

    # Wczytanie modelu
    model = load_model()

    # Test: Czy model ładuje dane i przewiduje wyniki
    try:
        test_data = pd.read_csv('/opt/airflow/processed_data/cloud_data.csv').drop(
            columns=['Name', 'City', 'Have you ever had suicidal thoughts ?_Yes'], errors='ignore')
        model.predict(test_data.iloc[:, :model.n_features_in_])
        logging.info("Model poprawnie przewiduje wyniki na danych testowych.")
    except Exception as e:
        failed_tests.append(f"Model nie powiódł się podczas predykcji: {e}")

    # Test: Czy pipeline walidacji obsługuje przypadki braku danych
    try:
        empty_data = pd.DataFrame()
        model.predict(empty_data)
    except ValueError:
        # Oczekiwane zachowanie: model powinien rzucić ValueError
        logging.info("Model poprawnie obsługuje przypadek braku danych.")
    except Exception as e:
        failed_tests.append(f"Nieoczekiwany błąd podczas testowania obsługi pustych danych: {e}")

    # Zapisanie informacji o nieudanych testach do XCom
    if failed_tests:
        kwargs['ti'].xcom_push(key='failed_tests', value=failed_tests)
        kwargs['ti'].xcom_push(key='test_status', value='failed')
        logging.error("Niektóre testy nie przeszły pomyślnie.")
    else:
        kwargs['ti'].xcom_push(key='test_status', value='passed')


def send_alert_email(**kwargs):
    model_status = kwargs['ti'].xcom_pull(key='model_status')
    if model_status == 'failed':
        logging.info("Sending failure alert email...")


# Definicja DAG
with DAG(
        dag_id='5_monitoring',
        default_args={
            'owner': 'airflow',
            'depends_on_past': False,
            'email_on_failure': False,
            'retries': 1,
            'retry_delay': timedelta(minutes=5),
        },
        description='DAG do walidacji i monitorowania modelu ML z powiadomieniem mailowym',
        schedule_interval=None,
        start_date=datetime(2023, 11, 28),
        catchup=False,
) as dag:

    fetch_data_task = PythonOperator(
        task_id='fetch_data_from_cloud',
        python_callable=fetch_data_from_cloud,
        provide_context=True,
    )

    evaluate_model_task = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_model,
        provide_context=True,
    )

    run_tests_task = PythonOperator(
        task_id='run_model_tests',
        python_callable=run_tests,
        provide_context=True,
    )

    # Task 3: Wysłanie powiadomienia mailowego, jeśli jakość modelu spadnie poniżej progu lub testy nie przejdą
    send_email_task = EmailOperator(
        task_id='send_email_notification',
        to='n.borowska@huma.waw.pl',
        subject='[Alert] Spadek jakości modelu ML poniżej krytycznego progu',
        html_content="""
        <h3>Uwaga!</h3>
        <p>Model ML nie spełnia kryterium jakości lub testy modelu zakończyły się niepowodzeniem.</p>
        <ul>
            <li>Nazwa modelu: model.pkl</li>
            <li>Aktualna jakość (Accuracy): {{ task_instance.xcom_pull(task_ids='evaluate_model', key='model_accuracy') }}</li>
            <li>Aktualna precyzja (Precision): {{ task_instance.xcom_pull(task_ids='evaluate_model', key='model_precision') }}</li>
            <li>Aktualny recall: {{ task_instance.xcom_pull(task_ids='evaluate_model', key='model_recall') }}</li>
            <li>Krytyczny próg: 80%</li>
            <li>Nieudane testy: {{ task_instance.xcom_pull(task_ids='run_model_tests', key='failed_tests') }}</li>
        </ul>
        <p>Sprawdź szczegóły i podejmij odpowiednie działania.</p>
        """,
        trigger_rule='one_failed',  # Wysyłanie emaila, jeśli poprzedni task zakończył się błędem
    )

    fetch_data_task >> evaluate_model_task >> run_tests_task >> send_email_task
