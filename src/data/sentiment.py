from transformers import pipeline

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = pipeline("sentiment-analysis")

    def analyze(self, text):
        result = self.analyzer(text)
        return result[0]['label'], result[0]['score']
