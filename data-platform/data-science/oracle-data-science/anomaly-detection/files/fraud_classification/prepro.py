from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from category_encoders import TargetEncoder

def build_preprocessor(numeric_cols, low_card, high_card):

    preprocessor = ColumnTransformer(

        transformers=[

            ("onehot",
             OneHotEncoder(handle_unknown="ignore"),
             low_card),

            ("target",
             TargetEncoder(handle_unknown="value"),
             high_card),

            ("num",
             "passthrough",
             numeric_cols)
        ]
    )

    return preprocessor