import numpy as np

class SignalGenerator:
    def __init__(self, model):
        self.model = model

    def generate_signal(self, features):
        prediction = self.model.predict([features])
        if prediction > 0.6:
            return 'buy'
        elif prediction < 0.4:
            return 'sell'
        else:
            return 'hold'
