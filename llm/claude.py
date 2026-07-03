import anthropic


class ClaudeClient:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def complete(self, system: str, user: str, web_search: bool = False) -> str:
        kwargs = {}
        if web_search:
            kwargs["tools"] = [
                {"type": "web_search_20260209", "name": "web_search", "max_uses": 5}
            ]
        response = self.client.messages.create(
            system=system,
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": user}],
            **kwargs,
        )
        # With web search enabled the response interleaves tool-result blocks
        # with text blocks, so concatenate every text block.
        return "".join(getattr(block, "text", "") for block in response.content)
