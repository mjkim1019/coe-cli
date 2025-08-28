"""XML 파일 전용 LLM 분석 프롬프트"""

def get_xml_file_analysis_prompt(file_path: str, file_info: dict, content: str) -> str:
    """XML 파일 분석을 위한 특화 프롬프트"""
    file_type = file_info.get('file_type', 'xml_file')
    basic_analysis = file_info.get('basic_analysis', {})
    
    prompt = f"""XML UI 파일 분석 요청:

파일 경로: {file_path}
파일 타입: {file_type}

기본 분석 결과:
{str(basic_analysis)}

파일 내용:
```
{content[:4000]}{'...' if len(content) > 4000 else ''}
```

**XML 파일 전용 분석**: 다음 항목들을 JSON 형태로 정확히 분석해주세요:

1. purpose: UI 화면의 주요 목적과 역할 (한국어로 상세히)
   - **분석 방법 (우선순위 순서)**:
     a) 먼저 XML 파일 상단의 주석에서 화면 설명을 찾아 사용
     b) 기본 분석 결과의 정보 적극 활용: Form ID, Datasets, UI Components, Functions
     c) JavaScript 함수들과 TrxCode 패턴 분석
     d) UI 컴포넌트의 ID와 이름 패턴에서 업무 도메인 추론
   - **출력 형식**: "[FormID] [구체적인 업무 설명]. 입력데이터는 [입력 컴포넌트와 데이터]를 포함하고, 결과는 [출력/처리 방식]을 제공하는 화면."
   - **예시**: "ZORDSS0340082 서비스 가입 관리 화면. 입력데이터는 고객정보와 서비스 조건을 포함하고, 결과는 가입/정지 처리 상태와 이력을 제공하는 화면."

2. form_info: {{
   "form_id": "폼 ID (FormID)",
   "screen_name": "화면명",
   "description": "화면 설명"
}}

3. trxcode_analysis: {{
   "trx_codes": [
     {{
       "code": "TrxCode 값",
       "function_name": "호출하는 함수명 (scwin.xxx)",
       "purpose": "거래 목적 (조회/등록/수정/삭제 등)",
       "trigger": "호출 시점 (버튼 클릭, 폼 로드 등)",
       "description": "거래 설명"
     }}
   ],
   "main_trx_code": "메인 거래 코드",
   "business_logic": "TrxCode 기반 비즈니스 로직 흐름"
}}

4. ui_components: {{
   "grids": ["그리드 컴포넌트들"],
   "inputs": ["입력 필드들"], 
   "buttons": ["버튼들"],
   "datasets": ["데이터셋들"],
   "other_components": ["기타 UI 컴포넌트들"]
}}

5. data_flow: {{
   "input_fields": [
     {{
       "name": "필드명",
       "type": "데이터타입",
       "required": true/false,
       "description": "필드 설명"
     }}
   ],
   "output_fields": [
     {{
       "name": "필드명", 
       "type": "데이터타입",
       "description": "필드 설명"
     }}
   ]
}}

6. javascript_functions: [
   {{
     "name": "함수명",
     "purpose": "함수 목적",
     "description": "함수 설명"
   }}
]


**XML 파일 분석 중점사항**:
- **기본 분석 결과 활용 필수**: Form ID, Datasets, UI Components, Functions 정보를 반드시 purpose 도출에 활용
- **구체적 업무 도메인 파악**: 단순한 "화면" 대신 실제 업무 기능 (가입, 조회, 관리 등) 명시  
- **TrxCode 패턴**: scwin.xxx 함수에서 TrxCode 사용 패턴과 비즈니스 목적 분석
- **데이터 흐름**: UI 컴포넌트 → 입력 데이터 → TrxCode 호출 → 출력 결과의 전체 흐름
- **컴포넌트 연결**: 입력 필드, 버튼, 그리드, 데이터셋 간의 상호작용 관계
- **업무 컨텍스트**: 파일명, FormID, 컴포넌트 ID에서 업무 도메인 추론하여 구체적 목적 도출

JSON 형태로만 응답하고, 다른 텍스트는 포함하지 마세요."""
    
    return prompt