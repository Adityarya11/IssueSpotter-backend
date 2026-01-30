from typing import Dict

class AIClassifier:

    @staticmethod
    def classify(title: str, description: str, images: list) -> Dict:
        """
        PlaceHolder for future AI integr.
        Returning dummy scores fot now.
        """

        return {
            "stage": "AI_CLASSIFIER",
            "toxicity": 0.1,
            "misinformation": 0.05,
            "civic_relevance": 0.85,
            "image_match_score": 0.9 if images else 0.0,
            "confidence": 0.6,
            "decision": "APPROVE"
        }