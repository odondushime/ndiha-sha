from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np

class FraudDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)  # Initialize model
        self.is_trained = False  # Track if model is trained

    def prepare_data(self, transactions):
        # Convert transactions to features for AI model
        features = []
        for t in transactions:
            features.append([
                t.amount,  # Transaction amount
                (t.timestamp - pd.Timestamp("2025-01-01")).total_seconds(),  # Time since reference
                hash(t.recipient_id) % 1000  # Simple user ID feature
            ])
        return np.array(features)

    def train(self, transactions):
        # Train the model on transaction data
        if transactions:
            data = self.prepare_data(transactions)
            self.model.fit(data)
            self.is_trained = True

    def predict(self, transaction):
        # Predict if a transaction is fraudulent
        if not self.is_trained:
            return False  # Default to safe if not trained
        data = self.prepare_data([transaction])
        prediction = self.model.predict(data)
        return prediction[0] == -1  # -1 indicates anomaly (fraud)