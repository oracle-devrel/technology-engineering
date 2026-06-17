from sklearn.metrics import confusion_matrix
def get_confusion_matrix(model,X_test,y_test):
    y_test_pred = model.predict(X_test)
    cm_test = confusion_matrix(y_test, y_test_pred)
    cm_test_pct = cm_test / cm_test.sum(axis=1, keepdims=True) * 100
    return cm_test_pct