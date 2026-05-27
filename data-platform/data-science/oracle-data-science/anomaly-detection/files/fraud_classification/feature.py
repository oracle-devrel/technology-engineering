import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def feature_engineering(df):

    df = df.copy()

    df['dob'] = pd.to_datetime(df['dob'])
    df['trans_date_trans_time'] = pd.to_datetime(df['trans_date_trans_time'])

    df['age'] = (df['trans_date_trans_time'] - df['dob']) / pd.Timedelta(days=365.2425)

    df['hour'] = df['trans_date_trans_time'].dt.hour

    df['geo_dist'] = np.sqrt(
        (df['lat'] - df['merch_lat'])**2 +
        (df['long'] - df['merch_long'])**2
    )

    return df


def fit_iso_forest(X_train):

    numeric_cols = X_train.select_dtypes(include=["int64","float64"]).columns

    iso = IsolationForest(
        n_estimators=100,
        contamination=0.01,
        random_state=42
    )

    iso.fit(X_train[numeric_cols])

    return iso, numeric_cols


def add_iso_score(df, iso, numeric_cols):

    df = df.copy()

    df['iso_score'] = iso.decision_function(df[numeric_cols])

    return df