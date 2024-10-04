import json

import numpy as np
from transformers import BertTokenizer, BertModel
from sklearn.metrics.pairwise import cosine_similarity
class EmotionalStateHandler:
    def __init__(self):
        # Load pre-trained BERT model and tokenizer
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.model = BertModel.from_pretrained("bert-base-uncased")

        # Define emotional phrases
        # Define emotional phrases for 10 additional emotions
        self.emotional_phrases = {
            "happy": "I am so happy!",
            "sad": "This is really sad.",
            "angry": "I am angry.",
            "surprised": "Wow, I didn't see that coming!",
            "fearful": "I'm really scared right now.",
            "disgusted": "That's absolutely disgusting.",
            "confused": "I'm not sure what’s going on.",
            "excited": "I can't wait for this!",
            "bored": "This is really boring.",
            "jealous": "I wish I had that.",
            "guilty": "I feel so guilty about it.",
            "embarrassed": "I can't believe I did that.",
            "proud": "I'm so proud of what I accomplished.",
            "lonely": "I feel so alone right now."
        }

        # Vectorize the emotional phrases using BERT
        self.emotional_vectors = {emotion: self._get_vector(phrase) for emotion, phrase in self.emotional_phrases.items()}

    def get_src(self):
        """Retrieve the chatbot's own source code."""
        try:
            with open(__file__, 'r') as file:
                src_code = file.read()
            return src_code
        except Exception as e:
            return f"An error occurred while fetching source code: {str(e)}"

    def _get_vector(self, phrase):
        """Get the vector representation of a phrase using BERT."""
        inputs = self.tokenizer(phrase, return_tensors="pt")
        outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).detach().numpy()

    def get_emotional_state(self, user_input):
        """Determine the user's emotional state based on their input."""

        inputs = self.tokenizer(json.dumps(list(filter(lambda a: 'request' in a and a['request'], user_input))), return_tensors="pt")
        outputs = self.model(**inputs)
        user_vector = outputs.last_hidden_state.mean(dim=1).detach().numpy()

        # Compare user_vector to emotional_vectors
        similarities = {emotion: cosine_similarity(user_vector, vector.reshape(1, -1)) for emotion, vector in self.emotional_vectors.items()}
        user_emotion = max(similarities, key=lambda x: similarities[x][0][0])  # Get the highest similarity

        return user_emotion
