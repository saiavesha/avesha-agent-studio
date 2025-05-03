# agents/evaluator.py
from nltk.translate.bleu_score import sentence_bleu

class EvaluatorAgent:
    def __init__(self, threshold=0.7):
        self.threshold = threshold

    def score(self, generated: str, reference: str) -> bool:
        score = sentence_bleu([reference.split()], generated.split())
        return score >= self.threshold
