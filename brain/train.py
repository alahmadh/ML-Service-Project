import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

url = "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv"
data = pd.read_csv(url, sep=';')

X = data.drop('quality', axis=1) 
y = data['quality']              

model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, 'model.pkl')
joblib.dump(model, model_path)

print(f"✅ The model has been successfully trained and saved at: {model_path}")