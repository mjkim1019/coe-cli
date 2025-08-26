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
   - **우선 순위**: XML 파일 상단의 주석에서 화면 설명을 찾아 그대로 사용
   - 주석이 없으면 FormID나 화면 구성요소를 기반으로 목적 추론

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

7. complexity_score: 복잡도 점수 (1-10)
8. maintainability: 유지보수성 평가 (한국어)  
9. suggestions: XML UI 개선 제안사항 (한국어)

**XML 파일 분석 중점사항**:
- TrxCode를 포함하는 함수들을 중점적으로 분석
- scwin.xxx 형태의 JavaScript 함수에서 TrxCode 사용 패턴 파악
- 각 TrxCode의 비즈니스 목적과 데이터 흐름 분석
- UI 컴포넌트와 데이터셋 간의 연결 관계 파악
- 사용자 입력 필드와 출력 결과 필드의 매핑 관계 분석
- XML에서는 nullable 개념보다는 required/optional 필드로 구분

JSON 형태로만 응답하고, 다른 텍스트는 포함하지 마세요."""
    
    return prompt