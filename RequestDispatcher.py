import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertTokenizer, BertModel
import torch


class RequestDispatcher:
    def __init__(self, agents):
        self.agents = agents
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.model = BertModel.from_pretrained("bert-base-uncased")
        self.agent_vectors = self._create_agent_vectors(agents)

    # def _create_agent_vectors(self, agents):
    #     vectors = {}
    #     for name, agent in agents.items():
    #         representative_text = agent.get_representative_text()  # Assuming each agent has this method
    #         vectors[name] = self._get_vector(representative_text)
    #     return vectors
    #
    # def _get_vector(self, text):
    #     # Tokenize input and convert to tensor
    #     inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    #     with torch.no_grad():
    #         outputs = self.model(**inputs)
    #
    #     # Get the mean of the last layer hidden state (vector representation)
    #     return outputs.last_hidden_state.mean(dim=1).numpy()  # Returns a numpy array
    #
    # def dispatch_request(self, request):
    #     request_vector = self._get_vector(request)
    #     similarities = {name: cosine_similarity(request_vector, vec.reshape(1, -1))[0][0]
    #                     for name, vec in self.agent_vectors.items()}
    #
    #     # Find the agent with the highest similarity
    #     best_agent_name = max(similarities, key=similarities.get)
    #     best_agent = self.agents[best_agent_name]
    #
    #     # Process the request through the best agent
    #     response = best_agent.handle_request(request)
    #     return response