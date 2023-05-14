import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pickle

data = pd.read_excel("new_elections_data.xlsx")

# Prepare the features (X) and target (y) for training
X = data.drop(columns=["Percentage"])
y = data["Percentage"]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
model = LinearRegression()
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
print("Mean Squared Error:", mean_squared_error(y_test, y_pred))

# Save the trained model
with open("election_model.pkl", "wb") as f:
    pickle.dump(model, f)
