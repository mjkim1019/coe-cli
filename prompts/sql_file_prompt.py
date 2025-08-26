"""SQL 파일 전용 LLM 분석 프롬프트"""

def get_sql_file_analysis_prompt(file_path: str, file_info: dict, content: str) -> str:
    """SQL 파일 분석을 위한 특화 프롬프트"""
    file_type = file_info.get('file_type', 'sql_file')
    basic_analysis = file_info.get('basic_analysis', {})
    
    prompt = f"""Oracle SQL 파일 분석 요청:

파일 경로: {file_path}
파일 타입: {file_type}

기본 분석 결과:
{str(basic_analysis)}

파일 내용:
```
{content[:4000]}{'...' if len(content) > 4000 else ''}
```

**SQL 파일 전용 분석**: 다음 항목들을 JSON 형태로 정확히 분석해주세요:

1. purpose: SQL 파일의 주요 목적과 역할 (한국어로 상세히)
   - **우선 순위**: SQL 파일 상단의 주석에서 쿼리 설명을 찾아 그대로 사용
   - 주석이 없으면 쿼리 분석을 통해 목적 추론

2. query_type: "SELECT" | "INSERT" | "UPDATE" | "DELETE" | "MERGE" | "MIXED"

3. input_output_analysis: {{
   "inputs": [
     {{
       "name": "바인드 변수명 (:variable_name)",
       "type": "추정 데이터타입",
       "nullable": true/false,
       "description": "바인드 변수 용도 설명",
       "example": "예시 값"
     }}
   ],
   "outputs": [
     {{
       "name": "컬럼명",
       "type": "데이터타입",
       "nullable": true/false,
       "description": "컬럼 설명",
       "table_source": "출처 테이블명"
     }}
   ]
}}

4. table_analysis: {{
   "main_tables": [
     {{
       "name": "테이블명",
       "alias": "별칭",
       "role": "MAIN | LOOKUP | REFERENCE",
       "description": "테이블 역할 설명"
     }}
   ],
   "join_analysis": [
     {{
       "type": "INNER JOIN | LEFT JOIN | RIGHT JOIN | FULL OUTER JOIN | ORACLE OUTER JOIN (+)",
       "tables": ["테이블1", "테이블2"],
       "condition": "조인 조건",
       "purpose": "조인 목적"
     }}
   ]
}}

5. oracle_features: {{
   "hints": [
     {{
       "hint": "힌트명 /*+ ... */",
       "purpose": "힌트 목적",
       "performance_impact": "성능 영향"
     }}
   ],
   "oracle_functions": [
     {{
       "function": "함수명 (NVL, TO_CHAR, DECODE 등)",
       "usage": "사용 목적",
       "context": "사용 컨텍스트"
     }}
   ],
   "date_patterns": [
     {{
       "pattern": "날짜 패턴 (99991231 등)",
       "meaning": "의미 (유효종료일 등)",
       "usage": "사용 목적"
     }}
   ]
}}

6. business_logic: {{
   "data_purpose": "조회/처리하는 데이터의 비즈니스 목적",
   "conditions": "주요 조건절 분석",
   "calculations": "계산 로직이 있다면 설명"
}}

7. performance_analysis: {{
   "estimated_complexity": "LOW | MEDIUM | HIGH",
   "potential_bottlenecks": ["성능 이슈 가능성이 있는 부분들"],
   "optimization_hints": ["최적화 제안사항들"]
}}

8. complexity_score: 복잡도 점수 (1-10)
9. maintainability: 유지보수성 평가 (한국어)
10. suggestions: SQL 쿼리 개선 제안사항 (한국어)

**SQL 파일 분석 중점사항**:
- 모든 바인드 변수(:variable)의 용도와 nullable 여부를 정확히 분석
- SELECT 결과 컬럼들의 출처 테이블과 nullable 여부를 명확히 파악
- 테이블 간 조인 관계와 조인 목적을 상세히 분석
- Oracle 특화 기능(힌트, 함수, (+) 조인 등) 사용 패턴 분석
- 99991231, 99991231235959 같은 특수 날짜 패턴의 의미 파악
- 성능 최적화 관점에서 쿼리 복잡도 평가
- 비즈니스 로직 관점에서 데이터 조회/처리 목적 파악

JSON 형태로만 응답하고, 다른 텍스트는 포함하지 마세요."""
    
    return prompt