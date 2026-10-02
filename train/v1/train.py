import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

FILE_NAME = "data.csv"

df = pd.read_csv(FILE_NAME)
X = df[['title', 'exclamation_count', 'uppercase_ratio']]
y = df['label']

preprocessor = ColumnTransformer(
    transformers=[('tfidf', TfidfVectorizer(max_features=1000), 'title')],
    remainder='passthrough'
)

pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('train', LogisticRegression(max_iter=1000, class_weight='balanced'))
        ])

pipeline.fit(X, y)
joblib.dump(pipeline, "model_v1.joblib")
