# Przewidywanie skłonności do myśli samobójczych na podstawie czynników demograficznych i zdrowotnych

## Autor: Natalia Borowska s25566

---

### 1. Wprowadzenie

Problemy zdrowia psychicznego, w tym depresja i myśli samobójcze, są globalnym wyzwaniem dotykającym ludzi w każdym wieku i sytuacji życiowej. W kontekście coraz większego nacisku na rozwój zrównoważonych rozwiązań zdrowotnych, sztuczna inteligencja i uczenie maszynowe oferują możliwość wcześniejszego wykrywania czynników ryzyka. Projekt ten ma na celu przewidywanie ryzyka wystąpienia myśli samobójczych na podstawie danych demograficznych i zdrowotnych, co może pomóc w identyfikacji osób potrzebujących wsparcia.

### 2. Opis problemu

Myśli samobójcze są często skutkiem złożonej kombinacji czynników, takich jak presja finansowa, historia zdrowia psychicznego w rodzinie, nawyki związane ze snem oraz zadowolenie z życia zawodowego lub akademickiego. Celem projektu jest stworzenie modelu przewidującego ryzyko myśli samobójczych na podstawie czynników związanych z demografią i stylem życia. Dokładne przewidywanie tego ryzyka może przyczynić się do szybszej interwencji i skierowania osób zagrożonych na odpowiednią ścieżkę wsparcia psychologicznego.

### 3. Cel projektu

Celem projektu jest zbudowanie modelu uczenia maszynowego, który na podstawie zebranych danych potrafi przewidywać skłonność do myśli samobójczych. Model ten będzie analizował kluczowe cechy demograficzne i zdrowotne, takie jak:
- czas snu,
- poziom presji finansowej,
- historia zdrowia psychicznego w rodzinie,
- zadowolenie z pracy lub nauki.

### 4. Zbiór danych

Zbiór danych zawiera 2556 rekordów i 19 kolumn, w tym zarówno dane liczbowe, jak i kategoryczne. Wykorzystane dane demograficzne oraz informacje o stylu życia umożliwiają zbudowanie modelu przewidującego ryzyko myśli samobójczych. Kluczowe kolumny używane w projekcie to:
- **Have you ever had suicidal thoughts?** (zmienna docelowa),
- **Financial Stress**,
- **Sleep Duration**,
- **Family History of Mental Illness**.

### 5. Struktura projektu

Projekt został zorganizowany w następujące kroki:
1. **Eksploracja danych** – analiza eksploracyjna danych (EDA) i zrozumienie zależności między zmiennymi.
2. **Przetwarzanie danych** – usuwanie braków danych, kodowanie zmiennych kategorycznych oraz standaryzacja.
3. **Budowa modelu** – stworzenie i trenowanie modelu na podstawie wybranych cech predykcyjnych.
4. **Walidacja i testowanie** – ocena skuteczności modelu za pomocą danych testowych.
5. **Wdrożenie i prezentacja wyników** – przygotowanie wyników oraz prezentacja końcowa.

### 6. Wyniki i oczekiwane korzyści

Dzięki temu modelowi chcemy dostarczyć wartościowe wnioski na temat kluczowych czynników ryzyka. W przyszłości model taki mógłby być wykorzystany jako narzędzie wspierające pracę psychologów i specjalistów zdrowia psychicznego, pomagając im zidentyfikować osoby, które mogą potrzebować wsparcia.

### 7. Technologia i narzędzia

- **Język programowania**: Python
- **Biblioteki**: Pandas, NumPy, Scikit-Learn, Matplotlib
- **Repozytorium**: GitHub
- **Platforma do dokumentacji i współpracy**: GitHub Project, README.md
