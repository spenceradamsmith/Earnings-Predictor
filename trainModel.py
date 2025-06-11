import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.utils.class_weight import compute_class_weight
from catboost import CatBoostClassifier, Pool

# Load the dataset and split it into features and target
df = pd.read_csv("training_dataset.csv", parse_dates=['earnings_date'])
X = df.drop(columns=['ticker', 'earnings_date', 'beat'])
y = df['beat']
category_features = ["quarter", "day_of_week"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size = 0.3,
    random_state = 42
)

# Compute class weights to handle class imbalance
classes = np.array([0, 1])
weights = compute_class_weight(
    class_weight = 'balanced',
    classes = classes,
    y = y_train
)
class_weights = {0: weights[0], 1: weights[1]}

# Create the CatBoost model with initial parameters
model = CatBoostClassifier(
    iterations = 1000,
    learning_rate = 0.05,
    depth = 6,
    eval_metric = "AUC",
    random_seed = 42,
    verbose = 100,
    early_stopping_rounds = 50,
    class_weights = class_weights
)

# Create CatBoost Pool objects for training and testing
train_pool = Pool(data = X_train, label = y_train, cat_features = category_features) 
test_pool  = Pool(data = X_test,  label = y_test,  cat_features = category_features)
model.fit(train_pool, eval_set = test_pool)

# Predict on the test set
y_pred = model.predict(test_pool)

# Evaluate the model using confusion matrix
total = y_test.shape[0]
correct = (y_pred == y_test).sum()
accuracy = (correct / total) * 100

print(f"Accuracy: {accuracy:.2f}%")

cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:", cm)

print("Classification Report:", classification_report(y_test, y_pred, digits=3))