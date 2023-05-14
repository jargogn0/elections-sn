import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# Load your combined dataset (replace with your actual data file)
data = pd.read_excel('rain_data.xlsx')

# Define input features and target variable
features = ['Rainfall_mm', 'Temperature_C', 'Wind_Speed_kmph', 'Elevation_m', 'Population_Density', 'Flood_History_Count']
target = 'Flood_Status'

# Prepare the dataset
X = data[features]
y = data[target]

# Encode the target variable (Flood_Status) as binary (0: No, 1: Yes)
y = y.map({'No': 0, 'Yes': 1})

# Split the dataset into training, validation, and test sets
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

# Standardize the input features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)
X_test = scaler.transform(X_test)

# Train the model using RandomForestClassifier
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Validate the model
y_val_pred = clf.predict(X_val)
print("Validation set results:")
print(classification_report(y_val, y_val_pred))
print(confusion_matrix(y_val, y_val_pred))

# Test the model
y_test_pred = clf.predict(X_test)
print("Test set results:")
print(classification_report(y_test, y_test_pred))
print(confusion_matrix(y_test, y_test_pred))
