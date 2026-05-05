from celery import Celery
import joblib
import os
import pandas as pd

celery_app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

MODEL_PATH = "/code/brain/model.pkl"

@celery_app.task
def run_prediction_task(data):
    if not os.path.exists(MODEL_PATH):
        return "Model file not found"
        
    model = joblib.load(MODEL_PATH)
    
    mapping = {
        "fixed_acidity": "fixed acidity", "volatile_acidity": "volatile acidity",
        "citric_acid": "citric acid", "residual_sugar": "residual sugar",
        "chlorides": "chlorides", "free_sulfur_dioxide": "free sulfur dioxide",
        "total_sulfur_dioxide": "total sulfur dioxide", "density": "density",
        "ph": "pH", "sulphates": "sulphates", "alcohol": "alcohol"
    }
    final_features = {mapping[k]: [v] for k, v in data.items() if k in mapping}
    df = pd.DataFrame(final_features)
    
    prediction = model.predict(df)
    return int(prediction[0])