import random

class ModelState:
    def __init__(self):
        self.current_pipe = None
        self.current_model_name = None

    def formatPrediction(self, predictions):
        # Ensure predictions are sorted in descending order of score
        sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)

        # Adjust probabilities
        adjusted_predictions = self.adjust_probabilities(sorted_predictions)

        # Select the top 3 predictions
        top_predictions = adjusted_predictions[:3]

        # Format the top predictions
        formatted_predictions = [{"label": pred["label"], "probability": pred["probability"]} for pred in top_predictions]

        return formatted_predictions

    def adjust_probabilities(self, predictions):
        """
        Adjusts probabilities so that the highest probability remains as it is,
        and the rest are randomly scaled between 0.30 and 0.50.
        """
        # Ensure predictions are sorted in descending order of score
        sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)

        # Keep the first probability as it is
        top_probability = sorted_predictions[0]['score']

        # Create adjusted predictions list with top probability unchanged
        adjusted_predictions = [{"label": sorted_predictions[0]["label"], "probability": top_probability}]

        # Set the probabilities for the second and third predictions randomly within the range [0.30, 0.50]
        for pred in sorted_predictions[1:3]:  # Only adjust the next two predictions
            adjusted_probability = random.uniform(0.30, 0.60)
            adjusted_predictions.append({"label": pred["label"], "probability": adjusted_probability})

        # Add remaining predictions with probabilities unchanged if any are left
        for pred in sorted_predictions[3:]:
            adjusted_predictions.append({"label": pred["label"], "probability": pred["score"]})

        return adjusted_predictions

model_state = ModelState()

def get_model_state():
    return model_state