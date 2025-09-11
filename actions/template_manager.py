"""
템플릿 파일 생성 관리 모듈 (핵심 기능만)
"""
import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table


class TemplateManager:
    """템플릿 기반 파일 생성 관리자"""
    
    def __init__(self, templates_dir: str = "templates", llm_service=None):
        self.templates_dir = templates_dir
        self.console = Console()
        self.llm_service = llm_service
        self._ensure_templates_dir()
    
    def _ensure_templates_dir(self):
        """템플릿 디렉토리가 없으면 생성"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
    
    def list_templates(self) -> List[Dict[str, str]]:
        """사용 가능한 템플릿 목록 반환"""
        templates = []
        if not os.path.exists(self.templates_dir):
            return templates
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.c') or filename.endswith('.py') or filename.endswith('.java') or filename.endswith('.xml') or filename.endswith('.sql'):
                template_path = os.path.join(self.templates_dir, filename)
                
                # 템플릿 설명 추출 (첫 번째 주석에서)
                description = self._extract_template_description(template_path)
                
                templates.append({
                    'name': filename,
                    'path': template_path,
                    'description': description,
                    'type': self._get_template_type(filename)
                })
        
        return templates
    
    def _extract_template_description(self, template_path: str) -> str:
        """템플릿 파일에서 설명 추출"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # 처음 500자만 읽어서 설명 찾기
                
                # C 파일의 경우 SERVICE 설명 추출
                if template_path.endswith('.c'):
                    match = re.search(r'\* 2\. SERVICE 설명\s*:\s*([^\n\*]+)', content)
                    if match:
                        return match.group(1).strip()
                
                # 다른 파일 형식의 경우 첫 번째 주석 라인 추출
                lines = content.split('\n')
                for line in lines[:10]:  # 처음 10줄에서 찾기
                    line = line.strip()
                    if line.startswith('//') or line.startswith('#'):
                        return line[2:].strip()
                    elif '/*' in line and '*/' in line:
                        return line.split('/*')[1].split('*/')[0].strip()
                
                return "템플릿 설명 없음"
        except Exception:
            return "설명을 읽을 수 없음"
    
    def _get_template_type(self, filename: str) -> str:
        """파일 확장자로 템플릿 타입 결정"""
        ext = filename.split('.')[-1].lower()
        type_mapping = {
            'c': 'C Program',
            'py': 'Python Script',
            'java': 'Java Class',
            'xml': 'XML Configuration',
            'sql': 'SQL Script'
        }
        return type_mapping.get(ext, 'Unknown')
    
    def create_from_template(self, template_name_or_number: str, service_id: str, filename: str, 
                           author: str = "user", description: str = "") -> bool:
        """템플릿으로부터 새 파일 생성 (핵심 기능)"""
        template_info = self.get_template_info(template_name_or_number)
        if not template_info:
            return False
        
        try:
            # 템플릿 파일 읽기
            with open(template_info['path'], 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # LLM 기반 스마트 생성
            if self.llm_service:
                self.console.print(f"[dim]🤖 LLM으로 적절한 변수명 생성 중...[/dim]")
                smart_names = self._generate_smart_names_with_llm(service_id, description, template_content)
                
                if smart_names:
                    self.console.print(f"[dim]✅ 함수명: {smart_names.get('function_name', 'N/A')}[/dim]")
                    self.console.print(f"[dim]✅ 테이블명: {smart_names.get('dbio_table', 'N/A')}[/dim]")
                    new_content = self._apply_smart_names(template_content, service_id, smart_names, author)
                else:
                    new_content = self._basic_replace(template_content, service_id, author, description)
            else:
                new_content = self._basic_replace(template_content, service_id, author, description)
            
            # SWING_AUTO_FILES에 파일 생성
            return self._save_to_auto_files(filename, new_content)
            
        except Exception as e:
            self.console.print(f"[red]파일 생성 오류: {e}[/red]")
            return False
    
    def _save_to_auto_files(self, filename: str, content: str) -> bool:
        """SWING_AUTO_FILES 디렉토리에 파일 저장"""
        auto_files_dir = "SWING_AUTO_FILES"
        if not os.path.exists(auto_files_dir):
            os.makedirs(auto_files_dir)
            self.console.print(f"[dim]📁 자동 생성 파일 디렉토리 생성: {auto_files_dir}[/dim]")
        
        output_path = os.path.join(auto_files_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    def _basic_replace(self, content: str, service_id: str, author: str, description: str) -> str:
        """기본 템플릿 변수 치환"""
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        
        replacements = [
            ('EDUSS0100101T01', service_id.upper()),
            ('eduss0100101t01', service_id.lower()),
            ('orddd194880', author),
            ('2025/09/03 21:21:15', now),
            ('입력 - 단일 레코드 ,출력 - 복수 레코드 , 유형 - Fetch template', description or '서비스 설명'),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        return content
    
    def _generate_smart_names_with_llm(self, service_id: str, description: str, template_content: str) -> Dict:
        """LLM으로 스마트 변수명 생성"""
        if not self.llm_service:
            return None
        
        template_sample = template_content[:1500] + "..." if len(template_content) > 1500 else template_content
        
        prompt = f"""
템플릿 구조를 분석하여 서비스에 맞는 변수명을 생성해주세요.

**템플릿:**
```c
{template_sample}
```

**서비스 정보:**
- ID: {service_id}
- 설명: {description}

**출력 (JSON):**
{{
    "function_name": "c300_get_svc_info",
    "struct_name": "{service_id.lower()}_ctx_s", 
    "dbio_table": "zord_svc_info",
    "detailed_description": "고객 정보 조회 서비스"
}}
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_service.chat_completion(messages, force_json=True)
            
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'\s*```', '', content)
                return json.loads(content)
                
        except Exception as e:
            self.console.print(f"[dim]LLM 생성 실패: {e}[/dim]")
            
        return None
    
    def _apply_smart_names(self, content: str, service_id: str, smart_names: Dict, author: str) -> str:
        """LLM 생성 결과를 템플릿에 적용"""
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        service_id_upper = service_id.upper()
        service_id_lower = service_id.lower()
        
        replacements = [
            ('EDUSS0100101T01', service_id_upper),
            ('eduss0100101t01', service_id_lower),
            ('orddd194880', author),
            ('2025/09/03 21:21:15', now),
            ('입력 - 단일 레코드 ,출력 - 복수 레코드 , 유형 - Fetch template', 
             smart_names.get('detailed_description', '서비스 설명')),
            (f'{service_id_lower}_ctx', smart_names.get('struct_name', f'{service_id_lower}_ctx')),
            ('ztpm_dept_f0001', smart_names.get('dbio_table', 'ztpm_dept_f0001')),
            ('ZTPM_DEPT_F0001', smart_names.get('dbio_table', 'ztpm_dept_f0001').upper()),
        ]
        
        # 함수명 처리
        if smart_names.get('function_name'):
            function_base = smart_names['function_name']
            replacements.extend([
                (f'c100_{service_id_lower}_fetch', f'c100_{function_base}_fetch'),
                (f'C100_{service_id_upper}_FETCH', f'C100_{function_base.upper()}_FETCH'),
            ])
        
        for old, new in replacements:
            content = content.replace(old, new)
        return content
    
    def get_template_info(self, template_name_or_number: str) -> Optional[Dict]:
        """특정 템플릿 정보 반환 (템플릿명 또는 번호로)"""
        templates = self.list_templates()
        
        # 숫자인 경우 인덱스로 찾기
        if template_name_or_number.isdigit():
            template_number = int(template_name_or_number)
            if 1 <= template_number <= len(templates):
                return templates[template_number - 1]
            return None
        
        # 템플릿명으로 찾기
        for template in templates:
            if template['name'] == template_name_or_number:
                return template
        return None
    
    def display_templates_table(self) -> Table:
        """템플릿 목록을 Rich 테이블로 표시"""
        table = Table(title="📄 사용 가능한 템플릿 목록")
        table.add_column("No.", style="bold green", width=4)
        table.add_column("템플릿명", style="cyan", no_wrap=True)
        table.add_column("타입", style="magenta")
        table.add_column("설명", style="white")
        
        templates = self.list_templates()
        
        if not templates:
            table.add_row("-", "템플릿 없음", "-", "templates/ 디렉토리에 템플릿을 추가하세요")
        else:
            for idx, template in enumerate(templates, 1):
                table.add_row(
                    str(idx),
                    template['name'],
                    template['type'],
                    template['description'][:50] + ('...' if len(template['description']) > 50 else '')
                )
        
        return table