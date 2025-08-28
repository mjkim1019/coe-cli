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

1. purpose: 파일의 주요 목적과 역할 (한국어로 매우 상세하게)
   - **분석 방법**: 
     a) 먼저 파일 상단 주석에서 구체적인 업무 설명 찾기
     b) c000_main_proc 함수의 실제 비즈니스 로직 분석
     c) DBIO 호출 패턴을 통한 데이터 처리 방식 파악
     d) 입출력 구조체를 통한 데이터 흐름 분석
   - **출력 형식**: "[서비스명] [업무 요약]. 입력데이터는 [입력 데이터 종류 및 내용]을 포함하고, 결과는 [출력 데이터 종류 및 처리 내용]을 출력하는 로직."
   - **예시**: "ORDSS04S2050T01 주문상품 재고 조회 서비스. 입력데이터는 주문번호와 고객정보를 포함하고, 결과는 해당 주문의 상품별 재고상태와 배송가능 여부를 출력하는 로직."

2. key_functions: 주요 함수들과 그 역할
   - **필수 확인 함수들**: c000_main_proc에서 호출하는 함수들
   - 각 함수의 역할 명시
   - b000_input_validation을 통해 input값의 not null (필수값) 알 수 있음

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
   "main_logic": "c000_main_proc 함수의 핵심 로직을 단계별로 상세 분석",
   "business_flow": "업무 처리 흐름: 1단계-입력검증 → 2단계-데이터조회 → 3단계-비즈니스로직 → 4단계-결과출력",
   "key_processing": "핵심 처리 로직 (반복문, 조건문, 계산 로직 등)",
   "data_transformation": "입력 데이터가 어떻게 변환되어 출력되는지",
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


**C 파일 분석 중점사항**:
- **목적(purpose) 분석**: 단순한 "데이터 처리" 대신 구체적인 업무 도메인과 처리 내용 명시
- **비즈니스 로직**: c000_main_proc 함수 내의 실제 업무 처리 로직을 상세 분석
- **데이터 흐름**: 입력→처리→출력 과정에서 데이터가 어떻게 변환되는지
- **DBIO 패턴**: 어떤 테이블에서 어떤 데이터를 조회하여 무엇을 수행하는지
- **업무 컨텍스트**: 파일명, 함수명, 변수명에서 업무 도메인 추론
- **처리 방식**: 단건 처리, 배치 처리, 실시간 처리 등의 패턴 식별

JSON 형태로만 응답하고, 다른 텍스트는 포함하지 마세요."""
    
    return prompt