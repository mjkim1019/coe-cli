import importlib

class PromptBuilder:
    def __init__(self, task: str):
        self.task = task
        self.prompts = self._load_prompt_class()

    def _load_prompt_class(self):
        try:
            module_name = f"cli.core.{self.task}_prompts"
            module = importlib.import_module(module_name)
            class_name = f"{self.task.capitalize()}Prompts"
            prompt_class = getattr(module, class_name)
            return prompt_class()
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Invalid task name '{self.task}'. Could not load prompts.") from e

    def build(self, user_input: str, file_context: dict, history: list = None):
        if history is None:
            history = []

        messages = []

        # 1. Add the main system prompt
        messages.append({"role": "system", "content": self.prompts.main_system})

        # 2. Add the file context
        if file_context:
            messages.append({"role": "system", "content": self.prompts.files_content_prefix})
            messages.append({"role": "assistant", "content": self.prompts.files_content_assistant_reply})

            for file_path, content in file_context.items():
                file_str = f"File: {file_path}\n```\n{content}\n```"
                messages.append({"role": "system", "content": file_str})

        # 3. Add existing history
        messages.extend(history)

        # 4. Add the final user request
        messages.append({"role": "user", "content": user_input})
        
        # 5. Add the system reminder at the end
        if self.prompts.system_reminder:
            messages.append({"role": "system", "content": self.prompts.system_reminder})

        return messages
