"""일반 파일 전용 LLM 분석 프롬프트"""

def get_generic_file_analysis_prompt(file_path: str, file_info: dict, content: str) -> str:
    """일반 파일 분석을 위한 기본 프롬프트"""
    file_type = file_info.get('file_type', 'generic_file')
    basic_analysis = file_info.get('basic_analysis', {})
    
    prompt = f"""파일 분석 요청:

파일 경로: {file_path}
파일 타입: {file_type}

기본 분석 결과:
{str(basic_analysis)}

파일 내용:
```
{content[:3000]}{'...' if len(content) > 3000 else ''}
```

다음 항목들을 JSON 형태로 정확히 분석해주세요:

1. purpose: 파일의 주요 목적과 역할 (한국어로 상세히)
   **우선 순위**: 
   - 파일 상단의 주석에서 파일 설명을 찾아 그대로 사용
   - 주석이 없으면 코드 분석을 통해 목적 추론

2. key_functions: 주요 함수들과 그 역할 리스트

3. input_output_analysis: {{
   "inputs": [
     {{
       "name": "파라미터명",
       "type": "데이터타입", 
       "nullable": true/false,
       "description": "파라미터 설명"
     }}
   ],
   "outputs": [
     {{
       "name": "리턴값명",
       "type": "데이터타입",
       "nullable": true/false, 
       "description": "리턴값 설명"
     }}
   ]
}}

4. dependencies: 의존성 분석 (imports, includes 등)
5. call_patterns: 호출 관계 패턴

**중요**: 
- purpose는 파일 최상단의 주석(/* ... */ 또는 // ...)에서 파일 설명을 먼저 찾아보세요
- input_output_analysis에서 nullable 정보를 반드시 포함하세요
- 모든 입출력 값에 대해 nullable 정보를 빠짐없이 제공하세요

JSON 형태로만 응답하고, 다른 텍스트는 포함하지 마세요."""
    
    return prompt