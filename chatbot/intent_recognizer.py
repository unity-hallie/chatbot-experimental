import numpy as np
from transformers import BertTokenizer, BertModel
import torch


class IntentRecognizer:
    def __init__(self):
        # Load pre-trained model and tokenizer
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.model = BertModel.from_pretrained("bert-base-uncased")

        # Define user intents and associated reference phrases
        self.INTENT_MAP = {
            "seeking_information": "I need information about...",
            "requesting_help": "Can you help me with...",
            "expressing_discontent": "I'm unhappy about...",
            "requesting_clarity": "Can you clarify...",
            "general_query": "Tell me about...",
        }

        # Precompute the intent vectors
        self.intent_vectors = self._vectorize_intents()

    def _vectorize_intents(self):
        """
        Generate vector representations for each intent based on reference phrases.
        """
        intent_vectors = {}
        for intent, phrase in self.INTENT_MAP.items():
            inputs = self.tokenizer(phrase, return_tensors="pt")
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use the mean of the last hidden state as the vector representation
                vector = outputs.last_hidden_state.mean(dim=1).numpy()
                intent_vectors[intent] = vector

        return intent_vectors

    def recognize_intent(self, user_input):
        """
        Analyze the user input, convert it to a vector, and determine the probable intent.
        """
        # Convert user input to vector
        user_vector = self._vectorize_input(user_input)

        # Calculate similarities with intent vectors
        similarities = {
            intent: self.cosine_similarity(user_vector, vector)
            for intent, vector in self.intent_vectors.items()
        }

        # Identify the intent with the highest similarity score
        max_intent = max(similarities, key=similarities.get)
        return max_intent

    def _vectorize_input(self, user_input):
        """
        Convert user input to a vector representation.
        """
        inputs = self.tokenizer(user_input, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
            vector = outputs.last_hidden_state.mean(dim=1).numpy()
        return vector

    def cosine_similarity(self, vec_a, vec_b):
        """
        Calculate cosine similarity between two vectors.
        """
        return np.dot(vec_a, vec_b.T) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))