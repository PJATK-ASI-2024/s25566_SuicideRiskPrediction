import pandas as pd
from sklearn.model_selection import train_test_split

file_path = 'final_depression_dataset_1.csv'
data = pd.read_csv(file_path)

# sprawdzam ile jest brakow
missing_values = data.isnull().sum()

# definicja co usuwamy (gdy kolumna ma >50% brakow)
threshold = 0.5 * len(data)
columns_to_drop = missing_values[missing_values > threshold].index.tolist()

# usuniecie kolumn z duza iloscia brakow
data_cleaned = data.drop(columns=columns_to_drop)

# uzupelnianie brakow medianą
numerical_columns = data_cleaned.select_dtypes(include=['float64', 'int64']).columns
data_cleaned[numerical_columns] = data_cleaned[numerical_columns].fillna(data_cleaned[numerical_columns].median())

# kodowanie kolumn
categorical_columns = data_cleaned.select_dtypes(include=['object']).columns
data_encoded = pd.get_dummies(data_cleaned, columns=categorical_columns, drop_first=True)

# podział na dane treningowe i testowe 70/30
train_data, test_data = train_test_split(data_encoded, test_size=0.3, random_state=42)


print("Training Data - First Few Rows:")
print(train_data.head())

print("\nTraining Data - Information:")
print(train_data.info())

print("\nTest Data - First Few Rows:")
print(test_data.head())

print("\nTest Data - Information:")
print(test_data.info())

