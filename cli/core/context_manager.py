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
        # 입출력 관련 질문인지 검사
        io_keywords = ['입출력', 'input', 'output', 'in/out', 'inout', 'in out', 'io', '파라미터', '인자', '리턴값', '출력값', '바인드', 'bind']
        self.is_io_question = any(keyword in user_input.lower() for keyword in io_keywords)
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
                
                # SQL 파일인 경우 구조 정보 추가
                elif file_path.endswith('.sql') and file_manager:
                    sql_info = file_manager.get_sql_file_context(file_path)
                    if sql_info:
                        structure_info = self._build_sql_structure_info(sql_info)
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

    def _build_sql_structure_info(self, sql_info):
        """SQL 파일 구조 정보를 프롬프트용 문자열로 변환"""
        structure_text = "### Oracle SQL 구조 분석 정보:\n"
        
        # 힌트 정보
        if sql_info.get('hints'):
            structure_text += "**오라클 힌트:**\n"
            for hint in sql_info['hints']:
                structure_text += f"- `/*+ {hint} */`\n"
        
        # 바인드 변수
        if sql_info.get('bind_variables'):
            structure_text += "\n**바인드 변수:**\n"
            for bind_var in sql_info['bind_variables']:
                structure_text += f"- `:{bind_var}`\n"
        
        # 오라클 함수
        if sql_info.get('oracle_functions'):
            structure_text += "\n**사용된 오라클 함수:**\n"
            for func in sql_info['oracle_functions']:
                structure_text += f"- `{func}`\n"
        
        # 아우터 조인
        if sql_info.get('outer_joins'):
            structure_text += "\n**아우터 조인:**\n"
            structure_text += "- Oracle 전용 아우터 조인 구문 `(+)` 사용됨\n"
        
        # 테이블 별칭
        if sql_info.get('table_aliases'):
            structure_text += "\n**테이블 별칭:**\n"
            for alias in sql_info['table_aliases'][:5]:  # 최대 5개만 표시
                structure_text += f"- `{alias}`\n"
        
        # 유효성 체크 패턴
        if sql_info.get('validity_patterns'):
            structure_text += "\n**유효성 체크 날짜 패턴:**\n"
            for pattern in sql_info['validity_patterns']:
                structure_text += f"- `{pattern}` - 레코드 유효 종료일 체크\n"
        
        structure_text += "\n**SQL 특징:**\n"
        structure_text += "- Oracle SQL 문법 사용\n"
        structure_text += "- 성능 최적화를 위한 힌트 활용\n"
        structure_text += "- 바인드 변수를 통한 안전한 파라미터 처리\n"
        if sql_info.get('validity_patterns'):
            structure_text += "- 99991231 또는 99991231235959를 사용한 유효성 체크 (무한대 날짜)\n"
        
        return structure_text
