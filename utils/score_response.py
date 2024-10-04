def score_response(self, response, ideal_state_vector, historical_data):
    sentiment_score = self.get_sentiment_score(response)
    relevance_score = self.get_relevance_score(response, historical_data)
    proximity_score = self.calculate_proximity(response, ideal_state_vector)

    total_score = (sentiment_score * self.weight_sentiment +
                   relevance_score * self.weight_relevance +
                   proximity_score * self.weight_proximity)

    return total_score