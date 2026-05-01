import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from category_encoders import TargetEncoder


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create a few simple Titanic features for demo purposes."""
    data = df.copy()

    if {"sibsp", "parch"}.issubset(data.columns):
        data["family_size"] = data["sibsp"].fillna(0) + data["parch"].fillna(0) + 1
        data["is_alone"] = (data["family_size"] == 1).astype(int)

    for col in ["age", "fare", "embarked"]:
        if col in data.columns:
            data[f"{col}_missing"] = data[col].isna().astype(int)

    return data


def split_column_types(
    X: pd.DataFrame,
    low_cardinality_threshold: int = 10,
):
    """Split columns to numeric / low-card categorical / high-card categorical."""
    numeric_cols = X.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()

    low_card = [c for c in categorical_cols if X[c].nunique(dropna=True) <= low_cardinality_threshold]
    high_card = [c for c in categorical_cols if c not in low_card]

    return numeric_cols, low_card, high_card


def build_preprocessor(numeric_cols, low_card_cols, high_card_cols):
    """Build ColumnTransformer with OneHot + TargetEncoder + numeric passthrough."""
    return ColumnTransformer(
        transformers=[
            ("onehot", OneHotEncoder(handle_unknown="ignore"), low_card_cols),
            ("target", TargetEncoder(handle_unknown="value", handle_missing="value"), high_card_cols),
            ("num", "passthrough", numeric_cols),
        ],
        remainder="drop",
    )
