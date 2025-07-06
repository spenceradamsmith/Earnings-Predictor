import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from catboost import CatBoostClassifier, Pool

# Load the dataset and split it into features and target
df = pd.read_csv("training_dataset.csv", parse_dates=['earnings_date'])
X = df.drop(columns=['ticker', 'earnings_date', 'beat'])
y = df['beat']
category_features = ["sector", "quarter", "day_of_week"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size = 0.3,
    random_state = 42
)

class_weights = {0: 3, 1: 1}

# Create CatBoost model with initial parameters
model = CatBoostClassifier(
    iterations = 300,
    learning_rate = 0.1,
    depth = 4,
    l2_leaf_reg = 1,
    eval_metric = "AUC",
    random_seed = 42,
    verbose = 100,
    early_stopping_rounds = 50,
    class_weights = class_weights
)
model.set_params(class_weights={0: 3, 1: 1})

# Create CatBoost Pool objects for training and testing
train_pool = Pool(data = X_train, label = y_train, cat_features = category_features) 
test_pool = Pool(data = X_test,  label = y_test,  cat_features = category_features)
model.fit(train_pool, eval_set = test_pool)

# Save the model after training
model.save_model("catboost_model.cbm")

# Predict on the test set
best_threshold = 0.57
probabilities = model.predict_proba(X_test)[:, 1]
y_pred = (probabilities >= best_threshold).astype(int)

# Evaluate the model using confusion matrix
accuracy = (y_pred == y_test).mean() * 100

print(f"Accuracy: {accuracy:.2f}%")

cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:", cm)

print("Classification Report:", classification_report(y_test, y_pred, digits=3))