# Mider 사용법 소개서

## 시작하기

1. swing_cli.exe을 SOC 게시판에서 다운받아 특정 위치에 위치시켜주세요. (ex. Users/development)
2. Users/development 폴더 내에 분석하고자 하는 파일들을 복사해 위치시켜주세요.
   즉, swing_cli.exe와 분석하고자하는 파일은 같은 폴더 내에 위치합니다.
3. 이제 swing_cli와 함께 개발/분석할 준비가 완료되었습니다!


## 기본 워크플로우

### 1. **파일 추가하기**
```bash
> /add @file.c
> /add @file.sql
> /add @file.xml
```
- 분석하고 싶은 파일을 컨텍스트에 추가합니다
- 여러 파일을 순차적으로 추가할 수 있습니다
- 빠른 응답을 위해 기본 정보만 수집됩니다
- 한 세션당 5개의 파일로 제한합니다.

### 2. **프로젝트 구조 파악하기**
```bash
> /repo
```
- 프로젝트 전체의 파일 구조 맵을 생성합니다
- 주요 파일들의 관계와 의존성을 한눈에 파악할 수 있습니다

### 3. **코드에 대해 질문하기**
```bash
> /ask
Ask mode> 이 파일의 구조를 분석해줘
Ask mode> DBIO 호출은 어디서 하고 있어?
Ask mode> .xml파일에서 어떤 TP를 호출하고 있는지 알려줘.
```
- `/ask` 명령어로 질문 모드에 진입합니다
- "구조 분석", "분석해줘" 등의 키워드를 사용하면 심층 분석이 자동으로 실행됩니다

### 4. **코드 수정하기**
```bash
> /edit
Edit mode> input_validation 함수에 NULL 체크 추가해줘
Edit mode> /preview              # 변경사항 미리보기
Edit mode> /apply                # 변경사항 적용
```
- `/edit` 명령어로 수정 모드에 진입합니다
- whole/block/udiff 방식을 지원합니다


## 파일 타입별 활용법

### **C 파일 분석 시**
```bash
> /add ORDSS04S2050T01.c
> /ask
Ask mode> 이 파일의 IO Formatter 구조 분석해줘
Ask mode> c000_main_proc에서 어떤 DBIO를 호출하고 있어?
Ask mode> a000_init_proc와 b000_input_validation의 역할은?
```

**자동으로 분석되는 요소:**
- IO Formatter 구조체
- 표준 함수 (a000_init, b000_input_validation, c000_main_proc, z999_err_exit)
- DBIO 호출 패턴
- 함수 간 호출 관계

### **XML 파일 분석 시**
```bash
> /add ZORDSS0340082.XML
> /ask
Ask mode> 이 화면에서 호출하는 TrxCode(TP)는 뭐야?
Ask mode> 그리드 컴포넌트 구조 설명해줘
Ask mode> scwin으로 시작하는 JavaScript 함수들 정리해줘
```

**자동으로 분석되는 요소:**
- TrxCode 호출 패턴
- UI 컴포넌트 (그리드, 입력필드, 버튼, 데이터셋)
- JavaScript 함수 (scwin.xxx)
- 데이터 흐름 및 이벤트 핸들러

### **SQL 파일 분석 시**
```bash
> /add zord_svc_prod_grp_s0001.sql
> /ask
Ask mode> 이 쿼리의 입출력 값과 nullable 정보 알려줘
Ask mode> 어떤 테이블을 조인하고 있고 그 목적은?
Ask mode> Oracle 힌트는 어떤 게 사용되고 있어?
```
- DB schema를 알려줘야 정확도가 올라갑니다.

**자동으로 분석되는 요소:**
- 바인드 변수 (:variable)와 nullable 여부
- SELECT 결과 컬럼과 nullable 정보
- 테이블 조인 관계 및 목적
- Oracle 힌트, (+) 조인, 특수 함수
- 성능 최적화 제안사항

## 💡 효과적인 사용 팁

### **1. 구조 분석이 필요할 때만 요청하기**
```bash
> /add @file.c
> /ask
Ask mode> 구조 분석해줘
```
- @ 를 통해 자동으로 실제 파일 위치를 가져옵니다.

### **2. DBIO 관련 질문**
"dbio"라는 키워드를 사용하면 자동으로 데이터베이스 입출력 컨텍스트로 인식됩니다:
```bash
Ask mode> 이 파일의 dbio 호출 패턴 설명해줘
Ask mode> dbio 함수에서 어떤 SQL을 실행하는지 알려줘
```

### **3. 디버그 정보 활용**
화면에 표시되는 색깔별 디버그 정보:
- **Cyan (청록색)**: RepoMap 관련 정보
- **Yellow (노란색)**: 파일 분석 관련 정보
- **Red (빨간색)**: 에러 메시지

### **4. JSON 응답 자동 변환**
LLM이 JSON 형태로 답변하면 자동으로 보기 좋은 표 형식으로 변환됩니다.

## 🎓 실전 시나리오 예시

### **시나리오 1: 레거시 C 프로그램 분석**
```bash
> /add @ORDSS04S2050T01.c
> /ask
Ask mode> 이 파일의 전체 구조 분석해줘
Ask mode> IO Formatter에는 어떤 필드들이 있어?
Ask mode> c000_main_proc의 주요 로직 설명해줘
```

### **시나리오 2: XML 화면 개발 이해**
```bash
> /add screen.xml
> /ask
Ask mode> 이 화면의 TrxCode 호출 패턴 분석해줘
Ask mode> 사용자가 버튼 클릭하면 어떤 일이 일어나?
Ask mode> 데이터셋과 그리드의 바인딩 관계는?
```

### **시나리오 3: SQL 쿼리 최적화**
```bash
> /add query.sql
> /ask
Ask mode> 이 쿼리의 조인 관계와 목적 설명해줘
Ask mode> explain이 아래와 같은데, 성능 개선할 수 있는 부분 있어?
Ask mode> 바인드 변수 중 nullable인 것들 알려줘
```

## 📋 주요 명령어 요약

| 명령어 | 설명 |
|--------|------|
| `/add <파일>` | 파일을 컨텍스트에 추가 |
| `/ask` | 질문 모드 진입 |
| `/edit` | 수정 모드 진입 |
| `/test` | 테스트 실행 |
| `/preview` | 변경사항 미리보기 |
| `/apply` | 변경사항 적용 |
| `/repo` | 리포지토리 맵 생성 |
| `/help` | 도움말 표시 |
| `/exit` | CLI 종료 |

## 언제 Mider를 사용하면 좋을까?

**이럴 때 사용하세요:**
- 스윙 코드의 구조를 빠르게 파악하고 싶을 때
- C/SQL/XML 파일의 특정 패턴을 분석하고 싶을 때
- DBIO 호출 관계나 TrxCode 패턴을 추적하고 싶을 때
- 입출력 파라미터의 nullable 정보를 확인하고 싶을 때
- AI의 도움을 받아 코드를 수정하고 싶을 때

## 주요 기능

### **LLM 기반 코드 구조 분석**
- 계층 구조, 호출 관계, 파일 카테고리화
- 자연어로 된 코드 요약 제공
- MiderAnalyzer 엔진을 통한 심층 분석

### **대화형 REPL 인터페이스**
- prompt_toolkit 기반의 명령어 인터페이스
- 자동완성 기능 지원
- 직관적인 명령어 체계

### **파일 타입별 특화 분석**
- **C 파일 (.c)**: IO Formatter, DBIO 호출 패턴, 표준 함수 구조 분석
- **XML 파일 (.xml)**: TrxCode 패턴, UI 컴포넌트, JavaScript 함수 분석
- **SQL 파일 (.sql)**: 바인드 변수, 테이블 조인, Oracle 힌트 분석

### **온디맨드 분석 시스템**
- `/add` 시 기본 분석만 수행하여 빠른 파일 추가
- 사용자가 "구조 분석" 요청 시에만 MiderAnalyzer 실행
- 성능 최적화를 위한 캐싱 시스템

### **스마트 JSON 응답 처리**
- LLM의 ```json 형태 응답을 자동으로 테이블로 변환
- Rich 라이브러리 기반의 보기 좋은 표 형식 출력

### **디버그 정보 시스템**
- LLM 호출 과정의 투명성 제공
- 색상별로 구분된 상세 디버그 출력

### **리포지토리 맵 생성**
- `/repo` 명령어로 프로젝트 전체 구조 맵 생성
- 우선순위 파일 자동 수집 및 분석

## 특별한 기능

- **DBIO 특수 용어 인식**: "dbio" 질문 시 데이터베이스 입출력 컨텍스트로 자동 인식
- **Nullable 정보 분석**: 모든 입출력 파라미터의 nullable 여부 자동 분석
- **Oracle SQL 특화**: 오라클 힌트, 바인드 변수, (+) 조인, 특수 날짜(99991231235959) 패턴 인식
