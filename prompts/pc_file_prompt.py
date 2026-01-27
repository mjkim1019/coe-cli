"""Pro*C (.pc) 파일 전용 LLM 분석 프롬프트"""

def get_pc_file_analysis_prompt(file_path: str, file_info: dict, content: str) -> str:
    """Pro*C 파일 분석을 위한 특화 프롬프트"""
    file_type = file_info.get('file_type', 'pc_file')
    basic_analysis = file_info.get('basic_analysis', {})

    prompt = f"""Pro*C 파일 분석 요청:

파일 경로: {file_path}
파일 타입: {file_type}

기본 분석 결과:
{str(basic_analysis)}

파일 내용:
```
{content[:4000]}{'...' if len(content) > 4000 else ''}
```

**Pro*C 파일 전용 분석**: 다음 항목들을 JSON 형태로 정확히 분석해주세요:

1. purpose: 파일의 주요 목적과 역할 (한국어로 매우 상세하게)
   - **분석 방법**:
     a) 파일 상단 주석(프로그램 헤더)에서 TABLE CRUD, FILE IN/OUT, 업무 설명 찾기
     b) 메인 함수(rep_pgm_*, main 등)의 비즈니스 로직 분석
     c) EXEC SQL 패턴을 통한 데이터 처리 방식 파악
     d) 파일 I/O 구조체(st_*_file_w_*)를 통한 출력 데이터 흐름 분석
   - **출력 형식**: "[프로그램명] [업무 요약]. 입력데이터는 [입력 데이터 종류]를 포함하고, 결과는 [출력 데이터 종류 및 처리 내용]을 출력하는 배치/리포트 프로그램."

2. key_functions: 주요 함수들과 그 역할
   - **필수 확인 패턴**: rep_pgm_*, rep_make_*, rep_get_*, rep_file_* 함수들
   - 각 함수의 역할과 호출 순서 명시

3. exec_sql_analysis: {{
   "includes": ["EXEC SQL INCLUDE로 포함하는 헤더 파일 목록"],
   "host_variables": {{
     "declare_sections": [
       {{
         "section_description": "DECLARE SECTION 설명",
         "variables": [
           {{
             "name": "변수명",
             "type": "데이터타입",
             "nullable": true/false,
             "description": "변수 용도 설명"
           }}
         ]
       }}
     ]
   }},
   "cursors": [
     {{
       "cursor_name": "커서명",
       "query_type": "SELECT/INSERT/UPDATE/DELETE",
       "target_tables": ["대상 테이블명"],
       "purpose": "커서의 업무 목적",
       "fetch_into": "FETCH 결과가 저장되는 호스트 변수"
     }}
   ],
   "prepared_statements": [
     {{
       "statement_name": "PREPARE 문 이름",
       "sql_type": "동적 SQL 타입",
       "purpose": "목적"
     }}
   ],
   "direct_sql": [
     {{
       "type": "SELECT INTO/INSERT/UPDATE/DELETE",
       "target_table": "대상 테이블",
       "purpose": "직접 실행 SQL 목적"
     }}
   ]
}}

4. file_io_analysis: {{
   "write_structures": [
     {{
       "struct_name": "st_*_file_w_* 구조체명",
       "file_type": "출력 파일 형식 (고정길이/CSV 등)",
       "key_fields": [
         {{
           "name": "필드명",
           "type": "데이터타입",
           "description": "필드 설명"
         }}
       ]
     }}
   ],
   "read_structures": [
     {{
       "struct_name": "입력 파일 구조체명",
       "description": "입력 파일 설명"
     }}
   ],
   "file_operations": "파일 열기/쓰기/닫기 패턴 요약"
}}

5. program_header: {{
   "program_name": "프로그램명",
   "table_crud": "TABLE CRUD 정보 (어떤 테이블에 대해 어떤 작업을 수행하는지)",
   "file_in_out": "FILE IN/OUT 정보 (입출력 파일 정보)",
   "description": "프로그램 설명 (헤더 주석에서 추출)"
}}

6. business_flow: {{
   "main_logic": "메인 처리 흐름을 단계별로 상세 분석",
   "data_transformation": "입력 데이터가 어떻게 변환되어 출력되는지",
   "error_handling": "EXEC SQL 에러 처리 방식 (WHENEVER SQLERROR 등)"
}}

7. dependencies: EXEC SQL INCLUDE 헤더, 외부 라이브러리 등 의존성 분석


**Pro*C 파일 분석 중점사항**:
- **EXEC SQL 패턴**: INCLUDE, DECLARE CURSOR, PREPARE, OPEN, FETCH, CLOSE 등 임베디드 SQL 구문 분석
- **호스트 변수**: EXEC SQL BEGIN/END DECLARE SECTION 내의 C 변수와 SQL 바인딩 관계
- **커서 처리**: 커서 선언, 열기, 페치, 닫기의 전체 흐름과 각 커서의 업무 목적
- **파일 I/O**: st_*_file_w_* 형태의 구조체를 통한 파일 출력 패턴
- **함수 흐름**: rep_pgm_* (메인), rep_make_* (데이터 생성), rep_get_* (데이터 조회), rep_file_* (파일 처리) 패턴
- **프로그램 헤더**: 파일 상단 주석에서 TABLE CRUD, FILE IN/OUT 정보 추출
- **동적 SQL**: EXEC SQL PREPARE를 통한 동적 쿼리 패턴

JSON 형태로만 응답하고, 다른 텍스트는 포함하지 마세요."""

    return prompt
