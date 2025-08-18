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

    def build(self, user_input: str, file_context: dict, history: list = None, file_manager=None):
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
                
                # C 파일인 경우 구조 정보 추가
                if file_path.endswith('.c') and file_manager:
                    c_info = file_manager.get_c_file_context(file_path)
                    if c_info:
                        structure_info = self._build_c_structure_info(c_info)
                        file_str += f"\n\n{structure_info}"
                
                messages.append({"role": "system", "content": file_str})

        # 3. Add existing history
        messages.extend(history)

        # 4. Add the final user request
        messages.append({"role": "user", "content": user_input})
        
        # 5. Add the system reminder at the end
        if self.prompts.system_reminder:
            messages.append({"role": "system", "content": self.prompts.system_reminder})

        return messages

    def _build_c_structure_info(self, c_info):
        """C 파일 구조 정보를 프롬프트용 문자열로 변환"""
        structure_text = "### C 파일 표준 함수 구조 정보:\n"
        
        found_functions = c_info.get('found_functions', {})
        standard_functions = c_info.get('standard_functions', {})
        
        if found_functions:
            structure_text += "**발견된 표준 함수들:**\n"
            for func_name, func_info in found_functions.items():
                structure_text += f"- `{func_name}` (라인 {func_info['line_number']}): {func_info['description']}\n"
        
        structure_text += "\n**표준 함수 구조 설명:**\n"
        for func_name, description in standard_functions.items():
            status = "✓ 발견됨" if func_name in found_functions else "✗ 미발견"
            structure_text += f"- `{func_name}`: {description} ({status})\n"
        
        return structure_text
