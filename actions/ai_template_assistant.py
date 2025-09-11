"""
AI 기반 대화형 템플릿 생성 어시스턴트
"""
import json
import re
from typing import Dict, List, Optional, Tuple
from rich.console import Console


class AITemplateAssistant:
    """AI가 사용자와 대화하며 템플릿 생성을 도와주는 어시스턴트"""
    
    def __init__(self, llm_service, template_manager):
        self.llm_service = llm_service
        self.template_manager = template_manager
        self.console = Console()
    
    def analyze_user_intent(self, user_input: str) -> Dict:
        """사용자 의도를 분석하여 파일 생성 요청인지 판단"""
        if not self.llm_service:
            return {"is_file_creation": False}
        
        prompt = f"""
사용자의 입력을 분석해서 파일 생성 요청인지 판단해주세요.

**사용자 입력:** "{user_input}"

다음 중 어떤 의도인지 분석해주세요:
1. 새로운 파일/서비스를 만들고 싶어함
2. 기존 파일을 수정하고 싶어함  
3. 질문이나 정보 조회
4. 기타

**분석 기준:**
- "생성", "만들어", "새로", "신규", "파일", "서비스" 등의 키워드
- 템플릿 사용 의도
- 구체적인 서비스명이나 기능 언급

**출력 형식 (JSON):**
{{
    "is_file_creation": true/false,
    "confidence": 0.95,
    "detected_keywords": ["생성", "파일"],
    "suggested_service_name": "고객 정보 조회",
    "suggested_filename": "customer_info_inquiry",
    "reasoning": "사용자가 새로운 파일 생성을 요청함"
}}

JSON 형태로만 응답해주세요.
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_service.chat_completion(messages, force_json=True)
            
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'\s*```', '', content)
                
                analysis = json.loads(content)
                return analysis
                
        except Exception as e:
            self.console.print(f"[dim]의도 분석 실패: {e}[/dim]")
            
        return {"is_file_creation": False}
    
    def start_template_conversation(self, user_input: str, analysis: Dict) -> Optional[Dict]:
        """템플릿 사용에 대한 대화 시작"""
        if not self.llm_service:
            return None
        
        # 템플릿 목록 가져오기
        templates = self.template_manager.list_templates()
        template_list = "\n".join([f"{i+1}. {t['name']} - {t['description']}" for i, t in enumerate(templates)])
        
        prompt = f"""
사용자가 파일 생성을 요청했습니다. 템플릿 사용을 제안하고 필요한 정보를 수집해주세요.

**사용자 원본 요청:** "{user_input}"
**분석 결과:** {analysis.get('reasoning', '')}

**사용 가능한 템플릿:**
{template_list}

**대화 목표:**
1. 템플릿 사용을 제안
2. 어떤 템플릿을 사용할지 추천
3. 파일명과 서비스 설명을 요청

**출력 형식 (JSON):**
{{
    "message": "새로운 파일을 생성하시는군요! 템플릿을 사용하시겠습니까? 다음 템플릿들을 사용할 수 있습니다:\\n\\n1. fetch_several_template.c - 조회용 서비스\\n\\n어떤 템플릿을 사용하시겠습니까?",
    "recommended_template": 1,
    "next_action": "wait_template_selection",
    "need_filename": true,
    "need_description": true
}}

자연스럽고 친근한 톤으로 JSON 응답해주세요.
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_service.chat_completion(messages, force_json=True)
            
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'\s*```', '', content)
                
                conversation = json.loads(content)
                return conversation
                
        except Exception as e:
            self.console.print(f"[dim]대화 생성 실패: {e}[/dim]")
            
        return None
    
    def process_template_selection(self, user_input: str, templates: List) -> Optional[Dict]:
        """사용자의 템플릿 선택을 처리"""
        if not self.llm_service:
            return None
        
        template_list = "\n".join([f"{i+1}. {t['name']} - {t['description']}" for i, t in enumerate(templates)])
        
        prompt = f"""
사용자가 템플릿을 선택했습니다. 선택한 템플릿을 파악하고 다음 단계를 안내해주세요.

**사용자 입력:** "{user_input}"
**사용 가능한 템플릿:**
{template_list}

**분석 목표:**
1. 어떤 템플릿을 선택했는지 파악 (번호 또는 이름)
2. 파일명과 서비스 설명이 필요함을 안내
3. 서비스 ID 형식 안내 (예: ORDSS04S1010T01)

**출력 형식 (JSON):**
{{
    "selected_template": 1,
    "template_name": "fetch_several_template.c",
    "message": "좋습니다! fetch_several_template.c 템플릿을 선택하셨네요.\\n\\n이제 다음 정보가 필요합니다:\\n1. 서비스 ID (예: CUST0001001T01)\\n2. 파일명 (예: customer_inquiry)\\n3. 서비스 설명 (예: 고객 정보 조회 서비스)\\n\\n어떤 서비스를 만드시나요?",
    "next_action": "collect_details",
    "success": true
}}

JSON 형태로만 응답해주세요.
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_service.chat_completion(messages, force_json=True)
            
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'\s*```', '', content)
                
                selection = json.loads(content)
                return selection
                
        except Exception as e:
            self.console.print(f"[dim]템플릿 선택 처리 실패: {e}[/dim]")
            
        return None
    
    def extract_service_details(self, user_input: str) -> Optional[Dict]:
        """사용자 입력에서 서비스 상세 정보 추출"""
        if not self.llm_service:
            return None
        
        prompt = f"""
사용자 입력에서 서비스 생성에 필요한 정보를 추출해주세요.

**사용자 입력:** "{user_input}"

**추출할 정보:**
1. 서비스 ID (XXXXX00X0000T00 형식)
2. 서비스 설명 (한국어)
3. 서비스 용도 (조회/등록/수정/삭제 등)

**출력 형식 (JSON):**
{{
    "service_id": "ORDSS04S1010T01",
    "filename": "ordss04s1010t01",
    "description": "고객 정보 조회 서비스",
    "purpose": "조회",
    "has_all_info": true,
    "missing_info": [],
    "message": "정보가 모두 확인되었습니다! 고객 정보 조회 서비스를 생성하겠습니다."
}}

만약 정보가 부족하면 has_all_info: false로 하고 missing_info에 부족한 정보를 나열해주세요.

JSON 형태로만 응답해주세요.
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_service.chat_completion(messages, force_json=True)
            
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'\s*```', '', content)
                
                details = json.loads(content)
                return details
                
        except Exception as e:
            self.console.print(f"[dim]서비스 정보 추출 실패: {e}[/dim]")
            
        return None