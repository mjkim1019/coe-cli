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
                
                # 상세 구조 분석 정보 추가 (백그라운드에서 CoeAnalyzer 사용)
                detailed_analysis = self._get_detailed_analysis(file_path, content)
                if detailed_analysis:
                    file_str += f"\n\n{detailed_analysis}"
                
                messages.append({"role": "system", "content": file_str})

        # 3. Add existing history
        messages.extend(history)

        # 4. Add the final user request
        messages.append({"role": "user", "content": user_input})
        
        # 5. Add the system reminder at the end
        if self.prompts.system_reminder:
            messages.append({"role": "system", "content": self.prompts.system_reminder})

        return messages

    def _get_detailed_analysis(self, file_path, content):
        """CoeAnalyzer를 사용하여 파일의 상세 분석 정보 생성 (화면 표시 없음)"""
        try:
            from .analyzer import CoeAnalyzer
            import tempfile
            import os
            
            # 임시 파일 생성하여 분석
            with tempfile.NamedTemporaryFile(mode='w', suffix=os.path.splitext(file_path)[1], delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # CoeAnalyzer로 분석 (화면 출력 없이)
                analyzer = CoeAnalyzer()
                # console 출력을 비활성화하기 위해 quiet 모드로 분석
                original_console = analyzer.console
                from rich.console import Console
                from io import StringIO
                
                # 출력을 StringIO로 리다이렉트 (화면에 표시되지 않게)
                quiet_console = Console(file=StringIO(), stderr=False)
                analyzer.console = quiet_console
                
                # 분석 수행
                results = analyzer.analyze_files([tmp_path], use_llm=False)  # LLM 분석은 생략, 기본 분석만
                
                # 원래 console 복원
                analyzer.console = original_console
                
                if results and 'files' in results and tmp_path in results['files']:
                    file_info = results['files'][tmp_path]
                    basic_analysis = file_info.get('basic_analysis', {})
                    
                    # 기본 분석 정보를 문자열로 변환
                    analysis_text = self._format_analysis_info(file_path, basic_analysis)
                    return analysis_text
                    
            finally:
                # 임시 파일 삭제
                os.unlink(tmp_path)
                
        except Exception as e:
            # 분석 실패 시 기존 방식으로 fallback
            return self._get_basic_structure_info(file_path, content)
        
        return None
    
    def _format_analysis_info(self, file_path, basic_analysis):
        """기본 분석 정보를 프롬프트용 문자열로 포맷팅"""
        analysis_text = "### 파일 구조 분석 정보:\n"
        
        file_type = basic_analysis.get('file_type', 'unknown')
        analysis_text += f"**파일 타입**: {file_type}\n\n"
        
        # C 파일인 경우
        if file_path.endswith('.c'):
            includes = basic_analysis.get('includes', {})
            if includes:
                if includes.get('io_formatter'):
                    analysis_text += "**IO Formatter 헤더들**:\n"
                    for include in includes['io_formatter']:
                        analysis_text += f"  • {include}\n"
                
                if includes.get('static_library'):
                    analysis_text += "**Static Library (Business Logic)**:\n"
                    for include in includes['static_library']:
                        analysis_text += f"  • {include}\n"
                
                if includes.get('dbio_library'):
                    analysis_text += "**DBIO Library**:\n"
                    for include in includes['dbio_library']:
                        analysis_text += f"  • {include}\n"
            
            functions = basic_analysis.get('functions', [])
            if functions:
                analysis_text += "**발견된 표준 함수들**:\n"
                for func in functions:
                    analysis_text += f"  • {func.get('name', 'N/A')} (라인 {func.get('line', 'N/A')})\n"
        
        # SQL 파일인 경우  
        elif file_path.endswith('.sql'):
            sql_features = basic_analysis.get('sql_features', {})
            if sql_features:
                if sql_features.get('bind_variables'):
                    analysis_text += "**바인드 변수들**:\n"
                    for var in sql_features['bind_variables']:
                        analysis_text += f"  • :{var}\n"
                
                if sql_features.get('hints'):
                    analysis_text += "**Oracle 힌트들**:\n"
                    for hint in sql_features['hints']:
                        analysis_text += f"  • {hint}\n"
                
                if sql_features.get('oracle_functions'):
                    analysis_text += "**Oracle 함수들**:\n"
                    for func in sql_features['oracle_functions']:
                        analysis_text += f"  • {func}\n"
        
        return analysis_text
    
    def _get_basic_structure_info(self, file_path, content):
        """기존 방식의 기본 구조 정보 (fallback)"""
        if file_path.endswith('.c'):
            return self._build_c_structure_info_simple(content)
        elif file_path.endswith('.sql'):
            return self._build_sql_structure_info_simple(content)
        return None
    
    def _build_c_structure_info_simple(self, content):
        """간단한 C 파일 구조 분석"""
        structure_text = "### C 파일 기본 구조 정보:\n"
        
        # 간단한 함수 찾기
        standard_functions = ['a000_init_proc', 'b000_input_validation', 'c000_main_proc', 'z000_norm_exit_proc', 'z999_err_exit_proc']
        found_functions = []
        
        lines = content.splitlines()
        for i, line in enumerate(lines):
            for func_name in standard_functions:
                if func_name in line and ('(' in line or 'void' in line or 'int' in line):
                    found_functions.append(f"  • {func_name} (라인 {i + 1})")
                    break
        
        if found_functions:
            structure_text += "**발견된 표준 함수들**:\n"
            structure_text += "\n".join(found_functions)
        
        return structure_text
    
    def _build_sql_structure_info_simple(self, content):
        """간단한 SQL 파일 구조 분석"""
        structure_text = "### SQL 파일 기본 구조 정보:\n"
        
        # 바인드 변수 찾기
        import re
        bind_vars = re.findall(r':(\w+)', content)
        if bind_vars:
            structure_text += "**바인드 변수들**:\n"
            for var in set(bind_vars):
                structure_text += f"  • :{var}\n"
        
        return structure_text

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
