import ads
from ads.common.auth import default_signer
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import ConfusionMatrixDisplay,confusion_matrix
from xgboost import XGBClassifier
from datetime import datetime
import io
import matplotlib.pyplot as plt
import oci
import os
import utils
from ads import set_auth

set_auth("resource_principal")

n_trees = int(os.getenv('TREES')) # reading the customized evn_var
max_depth = int(os.getenv('DEPTH'))
learning_rate = float(os.getenv('LRATE'))
print(n_trees,max_depth,learning_rate)


ads.set_auth(auth='resource_principal')
bucket_name = '<bucket_name>'
file_name_import = 'adult_income'
namespace = '<name_space>'
df = pd.read_csv(f"oci://{bucket_name}@{namespace}/{file_name_import}", storage_options=default_signer())


X = df.drop('class', axis=1)
X=pd.get_dummies(X)
y = df['class']
X_train, X_test, y_train, y_test = train_test_split(X, y,test_size=0.3)


model = XGBClassifier(max_depth=max_depth, n_estimators=n_trees, learning_rate=learning_rate,eval_metric='logloss')
model.fit(X_train, y_train)


cm_test_pct=utils.get_confusion_matrix(model,X_test,y_test)
cm_test_pct


disp = ConfusionMatrixDisplay(cm_test_pct, display_labels=['<=50K', '>50K'])
disp.plot(cmap='Blues', values_format=".1f")
file_path="output/confusion_matrix_xgboost_custom_vars.png" #files will be deleted during job deprovisioning
disp.figure_.savefig(file_path, bbox_inches="tight")