from app.llm_client import LLMClient

class InsightAgent:
    def __init__(self):
        self.llm = LLMClient()

    def summarize(self, structured_data):
        messages = [
            {
                "role": "system",
                "content": "You are a business intelligence analyst. Results are from the \"sales\" table (columns: id, region, product, revenue, order_date). Explain the results clearly using this terminology."
            },
            {
                "role": "user",
                "content": f"Explain these results: {structured_data}"
            }
        ]

        response = self.llm.chat(messages)
        return response.choices[0].message.content