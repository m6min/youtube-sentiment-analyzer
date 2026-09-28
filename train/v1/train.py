import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

FILE_NAME = "data.csv"

df = pd.read_csv(FILE_NAME)
X = df[['title', 'exclamation_count', 'uppercase_ratio']]
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=21)

transformer = TfidfVectorizer(max_features=1000)
preprocessor = ColumnTransformer(transformers=[
    ('tfidf', transformer, 'title')
        ],
        remainder='passthrough')

pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('train', LogisticRegression(max_iter=1000, class_weight='balanced'))
        ])

pipeline.fit(X_train, y_train)
y_predicted = pipeline.predict(X_test)
print(f"{len(X_train)+len(X_test)}")
print("\n--- Stats ---")
print(f"Accuracy: % {accuracy_score(y_test, y_predicted) * 100:.2f}")
print("\nGeneral:\n", classification_report(y_test, y_predicted))

joblib.dump(pipeline, "model_v1.joblib")
