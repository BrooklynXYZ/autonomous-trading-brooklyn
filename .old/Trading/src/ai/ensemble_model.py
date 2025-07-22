from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class EnsembleTradingModel:
    def __init__(self):
        self.models = {
            'rf': RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10),
            'gb': GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5),
            'svm': SVC(probability=True, random_state=42, kernel='rbf'),
            'nn': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42, max_iter=500)
        }
        self.weights = {}
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def train(self, X, y):
        """Train ensemble of models"""
        print("Training ensemble models...")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train each model and calculate weights based on cross-validation scores
        for name, model in self.models.items():
            print(f"Training {name}...")
            
            try:
                model.fit(X_scaled, y)
                
                # Calculate weight based on cross-validation performance
                cv_scores = cross_val_score(model, X_scaled, y, cv=3, scoring='accuracy')
                self.weights[name] = cv_scores.mean()
                print(f"{name} CV accuracy: {cv_scores.mean():.4f}")
            except Exception as e:
                print(f"Error training {name}: {e}")
                self.weights[name] = 0.0
        
        # Normalize weights
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {k: v/total_weight for k, v in self.weights.items()}
        else:
            # Equal weights if all models failed
            self.weights = {k: 1.0/len(self.models) for k in self.models.keys()}
        
        self.is_trained = True
        print("Ensemble training complete.")
    
    def predict_proba(self, X):
        """Predict with ensemble voting"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")
        
        X_scaled = self.scaler.transform(X)
        predictions = np.zeros((X_scaled.shape[0], 2))
        
        for name, model in self.models.items():
            try:
                pred = model.predict_proba(X_scaled)
                predictions += pred * self.weights[name]
            except Exception as e:
                print(f"Error predicting with {name}: {e}")
                continue
        
        return predictions
    
    def predict(self, X):
        """Predict class labels"""
        probas = self.predict_proba(X)
        return np.argmax(probas, axis=1)