from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np
from datetime import timedelta, datetime

class FraudDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.is_trained = False
        self.user_transaction_counts = {}
        self.last_training_time = None
        self.prediction_cache = {}
        self.min_transactions_for_training = 100
        self.training_interval = timedelta(hours=24)

    def prepare_data(self, transactions, user_id=None):
        # Convert transactions to features
        features = []
        # Calculate user-specific metrics
        if user_id:
            user_transactions = [t for t in transactions if t.wallet.user_id == user_id]
            amounts = [t.amount for t in user_transactions]
            avg_amount = np.mean(amounts) if amounts else 0.0
            std_amount = np.std(amounts) if amounts else 0.0
            recent_transactions = len([
                t for t in user_transactions
                if t.timestamp >= pd.Timestamp.now() - timedelta(hours=24)
            ])
        else:
            avg_amount = std_amount = recent_transactions = 0.0

        for t in transactions:
            time_diff = (pd.Timestamp.now() - t.timestamp).total_seconds() / 3600
            amount_deviation = (t.amount - avg_amount) / (std_amount + 1e-6) if user_id else 0.0
            features.append([
                t.amount,
                time_diff,
                recent_transactions,
                amount_deviation,
                hash(t.recipient_id) % 1000
            ])
        return np.array(features)

    def should_train(self, transactions):
        if not self.is_trained:
            return True
        if not self.last_training_time:
            return True
        if datetime.now() - self.last_training_time > self.training_interval:
            return True
        if len(transactions) >= self.min_transactions_for_training:
            return True
        return False

    def train(self, transactions):
        if not self.should_train(transactions):
            return

        if transactions:
            data = self.prepare_data(transactions)
            self.model.fit(data)
            self.is_trained = True
            self.last_training_time = datetime.now()
            self.prediction_cache.clear()  # Clear cache after training
            
            # Update transaction counts
            for t in transactions:
                user_id = t.wallet.user_id
                self.user_transaction_counts[user_id] = self.user_transaction_counts.get(user_id, 0) + 1

    def predict(self, transaction):
        if not self.is_trained:
            return False

        # Generate cache key
        cache_key = f"{transaction.wallet.user_id}_{transaction.amount}_{transaction.recipient_id}"
        
        # Check cache first
        if cache_key in self.prediction_cache:
            return self.prediction_cache[cache_key]

        # Make prediction
        user_id = transaction.wallet.user_id
        data = self.prepare_data([transaction], user_id=user_id)
        prediction = self.model.predict(data)
        is_fraud = prediction[0] == -1

        # Cache the result
        self.prediction_cache[cache_key] = is_fraud
        return is_fraud