class ModelRouter:
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def generate(self, context, goal, step):
        prompt = f"""
You are TALOS.

Context:
{context}

Goal:
{goal}

Step:
{step}

Respond clearly and concisely.
"""
        return self.client.generate(self.model, prompt)