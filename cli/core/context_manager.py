import importlib
import datetime
import tempfile
import os
import json
from io import StringIO
from rich.console import Console

from .analyzer import MiderAnalyzer
from ..ui.interactive import analysis_keywords
from .debug_manager import DebugManager

class PromptBuilder:
    def __init__(self, task: str):
        self.task = task
        self.prompts = self._load_prompt_class()
        # RepoMap 캐싱용 저장소
        self._repo_map_cache = {}
        self._cache_key = None
        # MiderAnalyzer 캐싱용 저장소
        self._mider_analysis_cache = {}

    def _load_prompt_class(self):
        try:
            module_name = f"cli.core.{self.task}_prompts"
            module = importlib.import_module(module_name)
            class_name = f"{self.task.capitalize()}Prompts"
            prompt_class = getattr(module, class_name)
            return prompt_class()
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Invalid task name '{self.task}'. Could not load prompts.") from e

    def set_task(self, task: str):
        """캐시를 유지하면서 task 모드 변경"""
        if self.task != task:
            self.task = task
            self.prompts = self._load_prompt_class()
            DebugManager.info(f"PromptBuilder task 변경됨: {task}")

    def build(self, user_input: str, file_context: dict, history: list = None, file_manager=None):
        # 입출력 관련 질문인지 검사
        io_keywords = ['입출력', 'input', 'output', 'in/out', 'inout', 'in out', 'io', '파라미터', '인자', '리턴값', '출력값', '바인드', 'bind']
        self.is_io_question = any(keyword in user_input.lower() for keyword in io_keywords)
        if history is None:
            history = []

        messages = []

        # 1. Add the main system prompt
        messages.append({"role": "system", "content": self.prompts.main_system})

        # 2. Add repository map (if manually generated)
        repo_map = self._get_cached_repo_map()
        if repo_map:
            repo_prompt_content = f"Repository Structure Overview:\n```\n{repo_map}\n```\n\nUse this overview to better understand the codebase structure when answering questions."
            messages.append({
                "role": "system",
                "content": repo_prompt_content
            })
            # RepoMap 프롬프트 내용 전체 출력
            DebugManager.prompt_content("RepoMap이 프롬프트에 포함된 내용", repo_prompt_content)

        # 3. Add the file context
        if file_context:
            messages.append({"role": "system", "content": self.prompts.files_content_prefix})
            messages.append({"role": "assistant", "content": self.prompts.files_content_assistant_reply})

            for file_path, content in file_context.items():
                file_str = f"File: {file_path}\n```\n{content}\n```"

                # 상세 구조 분석 정보 추가 (백그라운드에서 MiderAnalyzer 사용)
                detailed_analysis = self._get_detailed_analysis(file_path, content)
                if detailed_analysis:
                    file_str += f"\n\n{detailed_analysis}"

                messages.append({"role": "system", "content": file_str})

        # 4. Add MiderAnalyzer results if available (for structure analysis requests)
        mider_analysis = self._get_relevant_mider_analysis(user_input, file_context)
        if mider_analysis:
            for file_path, analysis in mider_analysis.items():
                analysis_str = f"File Structure Analysis for {file_path}:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}"
                messages.append({"role": "system", "content": analysis_str})
                DebugManager.mider_analyzer(f"MiderAnalyzer 결과를 프롬프트에 포함: {file_path}")

        # 4. Add existing history
        messages.extend(history)

        # 5. Add the final user request
        messages.append({"role": "user", "content": user_input})

        # 5. Add the system reminder at the end
        if self.prompts.system_reminder:
            messages.append({"role": "system", "content": self.prompts.system_reminder})

        # 전체 프롬프트 구성 디버그 출력
        DebugManager.prompt(f"전체 프롬프트 메시지 수: {len(messages)}")
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            DebugManager.prompt(f"Message {i+1} [{role}]: {len(content)} chars")
            if i < 5:  # 처음 5개 메시지만 내용도 출력
                DebugManager.prompt_content(f"Message {i+1} [{role}] 내용", content, max_length=200)

        return messages

    def _get_detailed_analysis(self, file_path, content):
        """MiderAnalyzer를 사용하여 파일의 상세 분석 정보 생성 (화면 표시 없음)"""
        try:
            from .analyzer import MiderAnalyzer
            import tempfile
            import os
            
            # 임시 파일 생성하여 분석
            with tempfile.NamedTemporaryFile(mode='w', suffix=os.path.splitext(file_path)[1], delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # MiderAnalyzer로 분석 (화면 출력 없이)
                analyzer = MiderAnalyzer()
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

    def _get_cached_repo_map(self):
        """캐시된 레포맵 조회 (자동 생성 없음)"""
        if self._repo_map_cache:
            # 가장 최근 캐시된 레포맵 반환
            latest_key = list(self._repo_map_cache.keys())[-1]
            cached_repo_map = self._repo_map_cache[latest_key]
            DebugManager.repo_map(f"✅ 캐시된 레포맵 사용 ({len(cached_repo_map)} chars)")
            return cached_repo_map

        DebugManager.repo_map("캐시된 레포맵 없음 - /repo 명령으로 생성 필요")
        return None

    def generate_repo_map_manually(self, target_files: list, file_manager=None):
        """수동으로 레포맵 생성 (/repo 명령어용)"""
        DebugManager.repo_map("수동 레포맵 생성 시작")
        DebugManager.repo_map(f"- 대상 파일들: {target_files}")

        try:
            from cli.coders.repo_mapper import RepoMapper

            # 파일 정보 수집
            chat_files = target_files if target_files else None
            other_files = []

            # file_manager에서 추가 파일 정보 가져오기
            if file_manager and hasattr(file_manager, 'files'):
                other_files = list(file_manager.files.keys())

            # RepoMapper로 맵 생성
            repo_mapper = RepoMapper()
            repo_map = repo_mapper.generate_map(
                chat_files=chat_files,
                other_files=other_files,
                mentioned_fnames=target_files,
                mentioned_idents=[]
            )

            if repo_map and len(repo_map.strip()) > 50:
                # 캐시에 저장 (새로운 키로)
                cache_key = self._generate_manual_cache_key(target_files)
                self._repo_map_cache[cache_key] = repo_map
                DebugManager.repo_map("✅ 수동 레포맵 생성 성공하여 캐시에 저장")
                return repo_map
            else:
                DebugManager.repo_map(f"❌ 레포맵이 너무 짧음 ({len(repo_map) if repo_map else 0} chars)")
                return None

        except Exception as e:
            DebugManager.error(f"수동 레포맵 생성 실패: {e}")
            return None

    def _generate_cache_key(self, file_context: dict, file_manager=None):
        """캐시 키 생성 (파일들의 조합으로)"""
        key_parts = []

        # file_context의 파일들
        if file_context:
            sorted_files = sorted(file_context.keys())
            key_parts.extend(sorted_files)

        # file_manager의 파일들
        if file_manager and hasattr(file_manager, 'files'):
            fm_files = sorted(file_manager.files.keys())
            key_parts.extend(fm_files)

        # 중복 제거하고 정렬
        unique_files = sorted(set(key_parts))
        cache_key = "|".join(unique_files)

        # 너무 긴 키는 해시로 축약
        if len(cache_key) > 200:
            import hashlib
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()

        return cache_key

    def _generate_manual_cache_key(self, target_files: list):
        """수동 생성용 캐시 키 생성"""
        sorted_files = sorted(target_files) if target_files else []
        cache_key = "MANUAL:" + "|".join(sorted_files)

        # 너무 긴 키는 해시로 축약
        if len(cache_key) > 200:
            import hashlib
            cache_key = "MANUAL:" + hashlib.md5(cache_key.encode()).hexdigest()

        return cache_key

    def clear_repo_map_cache(self):
        """레포맵 캐시 클리어"""
        self._repo_map_cache.clear()
        DebugManager.repo_map("레포맵 캐시 클리어됨")

    def get_repo_map_status(self):
        """레포맵 상태 확인"""
        if not self._repo_map_cache:
            return "❌ 생성된 레포맵 없음"

        cache_count = len(self._repo_map_cache)
        latest_key = list(self._repo_map_cache.keys())[-1]
        latest_size = len(self._repo_map_cache[latest_key])

        return f"✅ 캐시된 레포맵: {cache_count}개, 최신 크기: {latest_size} chars"

    def get_cached_mider_analysis(self, file_path: str):
        """캐싱된 MiderAnalyzer 분석 결과 반환"""
        if file_path in self._mider_analysis_cache:
            cached_data = self._mider_analysis_cache[file_path]
            DebugManager.mider_analyzer(f"✅ 캐시된 MiderAnalyzer 결과 사용: {file_path}")
            return cached_data.get('analysis')
        return None

    def perform_mider_analysis_on_demand(self, file_path: str, file_content: str, file_manager=None):
        """요청 시에만 MiderAnalyzer 실행하고 캐싱"""
        try:
            DebugManager.mider_analyzer(f"MiderAnalyzer 실행 시작: {file_path}")
            # MiderAnalyzer 인스턴스 생성
            analyzer = MiderAnalyzer()
            # 임시 파일 생성하여 분석 (기존 _get_detailed_analysis 로직 참고)
            with tempfile.NamedTemporaryFile(mode='w', suffix=os.path.splitext(file_path)[1], delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name

            try:
                # 화면 출력 없이 분석 수행
                original_console = analyzer.console


                # 출력을 StringIO로 리다이렉트
                quiet_console = Console(file=StringIO(), stderr=False)
                analyzer.console = quiet_console

                # LLM 분석 수행 (기본 분석 + LLM 심화 분석)
                results = analyzer.analyze_files([tmp_path], use_llm=True)

                # 원래 console 복원
                analyzer.console = original_console

                if results and 'files' in results and tmp_path in results['files']:
                    file_info = results['files'][tmp_path]

                    # 캐시에 저장
                    cache_data = {
                        'timestamp': datetime.datetime.now().isoformat(),
                        'analysis': {
                            'basic_analysis': file_info.get('basic_analysis', {}),
                            'llm_analysis': file_info.get('llm_analysis', {}),
                            'file_type': file_info.get('file_type', 'unknown')
                        }
                    }

                    self._mider_analysis_cache[file_path] = cache_data

                    DebugManager.mider_analyzer(f"✅ MiderAnalyzer 분석 완료 및 캐시 저장: {file_path}")
                    return cache_data['analysis']
                else:
                    DebugManager.mider_analyzer(f"❌ MiderAnalyzer 분석 결과 없음: {file_path}")
                    return None

            finally:
                # 임시 파일 삭제
                os.unlink(tmp_path)

        except Exception as e:
            DebugManager.error(f"MiderAnalyzer 분석 실패 ({file_path}): {e}")
            return None

    def get_mider_cache_status(self):
        """MiderAnalyzer 캐시 상태 확인"""
        if not self._mider_analysis_cache:
            return "❌ 캐시된 MiderAnalyzer 분석 결과 없음"

        cache_count = len(self._mider_analysis_cache)
        cached_files = list(self._mider_analysis_cache.keys())

        status = f"✅ 캐시된 MiderAnalyzer 분석: {cache_count}개 파일\n"
        for file_path in cached_files:
            filename = os.path.basename(file_path)
            timestamp = self._mider_analysis_cache[file_path].get('timestamp', 'unknown')
            status += f"  • {filename} ({timestamp})\n"

        return status.strip()

    def _get_relevant_mider_analysis(self, user_input: str, file_context: dict):
        """사용자 입력과 파일 컨텍스트를 기반으로 관련된 MiderAnalyzer 분석 결과 반환"""
        # 구조 분석 키워드 감지
   
        has_analysis_request = any(keyword in user_input.lower() for keyword in analysis_keywords)

        if not has_analysis_request:
            return {}

        DebugManager.mider_analyzer(f"구조 분석 키워드 감지됨: {user_input[:50]}...")

        # 분석 요청이 감지된 경우, 컨텍스트의 모든 파일에 대해 MiderAnalyzer 결과 확인
        relevant_analysis = {}

        if file_context:
            for file_path, content in file_context.items():
                # 캐시된 결과 확인
                cached_analysis = self.get_cached_mider_analysis(file_path)

                if cached_analysis:
                    relevant_analysis[file_path] = cached_analysis
                else:
                    # 캐시에 없으면 새로 분석 수행
                    DebugManager.mider_analyzer(f"MiderAnalyzer 새 분석 수행: {file_path}")
                    new_analysis = self.perform_mider_analysis_on_demand(file_path, content, None)
                    if new_analysis:
                        relevant_analysis[file_path] = new_analysis

        if relevant_analysis:
            DebugManager.mider_analyzer(f"MiderAnalyzer 분석 결과 {len(relevant_analysis)}개 파일에 대해 프롬프트에 포함")

        return relevant_analysis

    def _extract_mentioned_files(self, text: str):
        """텍스트에서 언급된 파일명 추출"""
        import re
        # 파일 패턴 (확장자가 있는 것들)
        file_pattern = r'\b[\w/.-]+\.[a-zA-Z]{1,4}\b'
        files = re.findall(file_pattern, text)
        return [f for f in files if len(f) > 3 and '.' in f]

    def _extract_mentioned_identifiers(self, text: str):
        """텍스트에서 언급된 식별자 추출"""
        import re
        # 함수명이나 변수명 패턴 (언더스코어 포함)
        ident_pattern = r'\b[a-zA-Z_]\w{2,}\b'
        identifiers = re.findall(ident_pattern, text)
        # 일반적인 단어 제외
        excluded = {'파일', '함수', '변수', '코드', '프로그램', '시스템', '데이터', 'file', 'function', 'code', 'data'}
        return [ident for ident in identifiers if ident.lower() not in excluded]
