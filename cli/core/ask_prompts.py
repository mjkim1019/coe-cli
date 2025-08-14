from .base_prompts import BasePrompts

class AskPrompts(BasePrompts):
    main_system = """
Act as an expert code analyst. Answer questions about the supplied code.
Do not suggest code changes.
If you need to show code, display it in a markdown code block.
Always reply to the user in Korean.
""".strip()

    # We can add specific examples for 'ask' tasks here later
    example_messages = []
