import anthropic


class ClaudeClient:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def complete(self, system: str, user: str) -> str:
        response = self.client.messages.create(
            system=system,
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text
