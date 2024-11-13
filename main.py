import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from tpot import TPOTClassifier
from ydata_profiling import ProfileReport
from sklearn.ensemble import ExtraTreesClassifier
import numpy as np

# Wczytanie danych
file_path = 'final_depression_dataset_1.csv'
data = pd.read_csv(file_path)


# Podstawowa analiza danych (EDA)
print("Podstawowe informacje o danych:")
print(data.info())
print("\nOpis statystyczny danych:")
print(data.describe())

# Sprawdzenie brakujących wartości
missing_values = data.isnull().sum()
print("\nBrakujące wartości w każdej kolumnie:\n", missing_values)

# Zamiana wartości tekstowych w kolumnach numerycznych na NaN
for col in data.select_dtypes(include=['float64', 'int64']).columns:
    data[col] = pd.to_numeric(data[col], errors='coerce')

# Wizualizacja rozkładów zmiennych numerycznych
print("\nTworzenie histogramów dla kolumn numerycznych...")
data.hist(bins=15, figsize=(15, 10))
plt.suptitle("Histogram dla kolumn numerycznych")
plt.show()

# Wykresy pudełkowe dla zmiennych numerycznych
print("\nTworzenie wykresów pudełkowych dla kolumn numerycznych...")
for col in data.select_dtypes(include=['float64', 'int64']).columns:
    plt.figure()
    sns.boxplot(data[col])
    plt.title(f"Wykres pudełkowy dla {col}")
    plt.show()

# Macierz korelacji (tylko kolumny numeryczne)
print("\nTworzenie macierzy korelacji...")
numerical_data = data.select_dtypes(include=['float64', 'int64'])
plt.figure(figsize=(10, 8))
sns.heatmap(numerical_data.corr(), annot=True, cmap='coolwarm')
plt.title("Macierz korelacji")
plt.show()

# Generowanie raportu
print("\nGenerowanie raportu Pandas Profiling...")
profile = ProfileReport(data)
profile.to_file("automated_eda_report.html")

# Usunięcie kolumn z dużą ilością brakujących danych (ponad 50%)
threshold = 0.5 * len(data)
columns_to_drop = missing_values[missing_values > threshold].index.tolist()
columns_to_drop.append('Name')  # Usunięcie kolumny 'Name'
data_cleaned = data.drop(columns=columns_to_drop)

# Uzupełnianie brakujących wartości - medianą
numerical_columns = data_cleaned.select_dtypes(include=['float64', 'int64']).columns
data_cleaned[numerical_columns] = data_cleaned[numerical_columns].fillna(data_cleaned[numerical_columns].median())

# Usunięcie kolumn z imionami
name_columns = [col for col in data_cleaned.columns if 'Name_' in col]
data_cleaned = data_cleaned.drop(columns=name_columns)

# Kodowanie kolumn
categorical_columns = data_cleaned.select_dtypes(include=['object']).columns
data_encoded = pd.get_dummies(data_cleaned, columns=categorical_columns, drop_first=True)

# Podział na dane treningowe i testowe 70/30
print("Dostępne kolumny po kodowaniu:")
print(data_encoded.columns.tolist())

# Znalezienie poprawnej nazwy kolumny docelowej
target_column = 'Have you ever had suicidal thoughts ?_Yes'

X = data_encoded.drop(target_column, axis=1)  # Zastąp 'Have you ever had suicidal thoughts ?' nazwą zmiennej docelowej
y = data_encoded[target_column]
y = data_encoded[target_column]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

# Analiza AutoML z TPOT
print("\nRozpoczęcie analizy TPOT...")
tpot = TPOTClassifier(generations=20, population_size=150, verbosity=3, random_state=42, crossover_rate=0.1, mutation_rate=0.9, n_jobs=-1)
tpot.fit(X_train, y_train)
print("Zalecana struktura pipeline przez TPOT: ", tpot.fitted_pipeline_)
tpot.export("tpot_best_pipeline.py")

# Wybór modelu
from sklearn.ensemble import ExtraTreesClassifier

print("Trenowanie modelu ExtraTreesClassifier zgodnie z zaleceniem TPOT...")
model = ExtraTreesClassifier(
    criterion='gini',
    max_features=0.5,
    min_samples_leaf=5,
    min_samples_split=5,
    n_estimators=200,
    random_state=42
)
model.fit(X_train, y_train)

# Ocena modelu
print("\nOcena modelu...")
y_pred = model.predict(X_test)

# Zamiana wartości logicznych na liczby całkowite
if y_test.dtype == 'bool':
    y_test = y_test.astype(int)
if y_pred.dtype == 'bool':
    y_pred = y_pred.astype(int)
accuracy = accuracy_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print(f"Dokładność: {accuracy}")
print(f"Średni Błąd Bezwzględny: {mae}")

# Zapisanie wyników do dokumentacji
with open("model_evaluation.txt", "w") as f:
    f.write(f"Dokładność: {accuracy}\n")
    f.write(f"Średni Błąd Bezwzględny: {mae}\n")