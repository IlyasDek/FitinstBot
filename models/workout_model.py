import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

# Загрузка данных
df = pd.read_csv('../utils/combined_dataset.csv')

# Кодирование категориальных признаков
label_encoders = {}
for column in ['Gender', 'Fitness Level', 'Health Restrictions', 'Fitness Goal', 'Body Part', 'Type of Muscle', 'Workout Name', 'Equipment', 'Difficulty Level', 'Exercise Type', 'Health Restrictions (Exercise)', 'Fitness Goal (Exercise)']:
    label_encoders[column] = LabelEncoder()
    df[column] = label_encoders[column].fit_transform(df[column])

# Определение признаков и целевой переменной
X = df.drop(columns=['User ID', 'Workout Name'])  # Признаки
y = df['Workout Name']  # Целевая переменная

# Разделение данных на обучающую и тестовую выборки
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Обучение модели XGBoost
model = xgb.XGBClassifier()
model.fit(X_train, y_train)

# Предсказание на тестовой выборке
y_pred = model.predict(X_test)

# Оценка точности модели
accuracy = accuracy_score(y_test, y_pred)
print(f'Точность: {accuracy:.2f}')
print(classification_report(y_test, y_pred))