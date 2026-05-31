import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

df = pd.read_csv("data.csv")

X = df.drop("fitness_score", axis=1)
y = df["fitness_score"]

scaler = StandardScaler()
X = scaler.fit_transform(X)

model = RandomForestRegressor()
model.fit(X, y)

joblib.dump(model, "model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("Model Saved")