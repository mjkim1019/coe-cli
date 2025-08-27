"""C 파일 전용 LLM 분석 프롬프트"""

def get_c_file_analysis_prompt(file_path: str, file_info: dict, content: str) -> str:
    """C 파일 분석을 위한 특화 프롬프트"""
    file_type = file_info.get('file_type', 'c_file')
    basic_analysis = file_info.get('basic_analysis', {})
    
    prompt = f"""C 파일 분석 요청:

파일 경로: {file_path}
파일 타입: {file_type}

기본 분석 결과:
{str(basic_analysis)}

파일 내용:
```
{content[:4000]}{'...' if len(content) > 4000 else ''}
```

**C 파일 전용 분석**: 다음 항목들을 JSON 형태로 정확히 분석해주세요:

1. purpose: 파일의 주요 목적과 역할 (한국어로 상세히)
   - **우선 순위**: 파일 상단의 주석(/* ... */ 또는 //)에서 설명을 찾아 그대로 사용
   - 주석이 없으면 c000_main_proc 함수의 로직을 기반으로 목적 추론

2. key_functions: 주요 함수들과 그 역할
   - **필수 확인 함수들**: a000_init_proc, c000_main_proc, z000_norm_exit_proc, z999_err_exit_proc
   - 각 함수의 역할과 중요도 명시

3. io_formatter_analysis: {{
   "io_includes": ["pio_xxx_in.h", "pio_xxx_out.h 등 IO 관련 헤더들"],
   "input_structure": {{
     "structure_name": "입력 구조체명",
     "key_fields": [
       {{
         "name": "필드명",
         "type": "데이터타입",
         "nullable": true/false,
         "description": "필드 설명"
       }}
     ]
   }},
   "output_structure": {{
     "structure_name": "출력 구조체명", 
     "key_fields": [
       {{
         "name": "필드명",
         "type": "데이터타입",
         "nullable": true/false,
         "description": "필드 설명"
       }}
     ]
   }}
}}

4. c000_main_proc_analysis: {{
   "main_logic": "c000_main_proc 함수의 핵심 로직 설명",
   "business_flow": "비즈니스 처리 흐름",
   "error_handling": "에러 처리 방식"
}}

5. dbio_analysis: {{
   "dbio_calls": [
     {{
       "function_name": "호출하는 DBIO 함수명",
       "purpose": "조회/수정/삭제 목적",
       "input_data": "입력 데이터 설명",
       "output_data": "출력 데이터 설명"
     }}
   ],
   "database_operations": "수행하는 데이터베이스 작업 요약"
}}

6. dependencies: Static Library, DBIO Library 등 의존성 분석
7. complexity_score: 복잡도 점수 (1-10)
8. maintainability: 유지보수성 평가 (한국어)
9. suggestions: C 코드 개선 제안사항 (한국어)

**C 파일 분석 중점사항**:
- IO Formatter 섹션의 헤더 파일들과 구조체 정의를 중점 분석
- c000_main_proc 함수의 비즈니스 로직을 상세히 분석
- DBIO Library 호출 부분을 찾아 어떤 데이터를 조회/수정하는지 파악
- 표준 함수 구조(a000, b000, c000, z000, z999)의 역할 분석
- 입출력 구조체의 필드별 nullable 정보 정확히 분석

JSON 형태로만 응답하고, 다른 텍스트는 포함하지 마세요."""
    
    return prompt