import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

df = pd.read_csv("data/bcn_flight_dataset_preprocessed.csv")

df = df.drop(columns =["error"])
df = df.dropna()
df["route_weekday"] = df["origin"] + "_" + df["weekday"]


X = df[["origin",
        "airline",
        "weekday",
        "route_weekday",
        "duration(min)",
        "dep_minutes"]]

y = df["price"]

categorical_cols = ["origin", "airline", "weekday", "route_weekday"]
numeric_cols = ["duration(min)", "dep_minutes"]

categorical_transformer = OneHotEncoder(sparse_output=False)
preprocessor = ColumnTransformer(transformers=[("cat", categorical_transformer, categorical_cols),
                                               ("num", "passthrough", numeric_cols)])

model = XGBRegressor(n_estimators = 300,
                     learning_rate = 0.05,
                     max_depth =6,
                     subsample = 0.8,
                     colsample_bytree = 0.8,
                     random_state = 42) 
steps = [("preprocess", preprocessor), ("model", model)]
pipe = Pipeline(steps)

pipe.fit(X,y)

df["pred_price"] = pipe.predict(X)
baseline = df[["origin",
               "airline",
               "weekday",
               "duration(min)",
               "dep_minutes",
               "route_weekday",
               "pred_price"]]

baseline.to_csv("data/baseline_prices.csv", index = False)