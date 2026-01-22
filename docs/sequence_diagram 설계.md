## 설계
1. /add와 /ask의 역할이 명확히 분리
   - Add = 컨텍스트 준비 (LLM 호출X, 파일 원문 + 기본구조 분석)
   - Ask = 조건부 분석 + LLM 질의
2. PromptBuilder를 중심으로 한 프롬프트 조립 아키텍처
3. LLM 호출은: Ask 모드에서만, PromptBuilder.build() 이후 단 한 번
4. 기본 분석과 심화 분석을 분리
   - 비용 최적화
   - 응답 성능 개선

## Add 모드 diagram 
``` 
@startuml
title SwingMate CLI - Add Mode Sequence Diagram

actor User
participant "SwingMate CLI" as CLI
participant "FileManager" as FM
participant "CoeAnalyzer\n(SWMate)" as CA

== Add Mode ==

User -> CLI: /add <file>
CLI -> FM: add(file_path)

FM -> FM: Read file content
FM -> FM: Store content in files[]

FM -> CA: Basic structure analysis\n(use_llm = false)
CA --> FM: File structure summary

FM --> CLI: File added\n(context + basic analysis cached)
CLI --> User: Add completed

@enduml

```

Add Mode는 LLM 호출 이전 단계에서 필요한 컨텍스트를 준비하는 역할을 수행합니다.
사용자가 /add <file> 명령을 입력하면, CLI는 FileManager를 통해 파일을 읽고 내부 컨텍스트로 저장한다.

이 과정에서 FileManager는 단순히 **파일 원문**을 보관하는 데 그치지 않고,
파일 확장자(C, SQL, XML 등)에 따라 CoeAnalyzer를 이용한 **기본 구조 분석**을 수행합니다.
이 분석은 LLM을 사용하지 않는 **경량 분석**으로, 이후 Ask 모드에서 빠르고 정확한 응답을 제공하기 위한 **사전 준비 단계**입니다.


## Ask 모드 diagram 
```
@startuml
title SwingMate CLI - Ask Mode Sequence Diagram

actor User
participant "SwingMate CLI" as CLI
participant "PromptBuilder\n(ContextManager)" as PB
participant "FileManager" as FM
participant "CoeAnalyzer\n(SWMate)" as CA
participant "LLM Backend\n(LLM + Tool/RAG)" as LLM

== Ask Mode ==

User -> CLI: /ask <question>
CLI -> PB: build(user_input)

note right of PB
Stateful prompt builder
with analysis cache
end note

PB -> PB: Load AskPrompts.main_system\n(Korean reply, JSON policy, role)

PB -> FM: Get stored file contents

PB -> CA: Generate basic structure analysis\n(use_llm = false)
CA --> PB: Basic analysis text

PB -> PB: Append file contents\n+ basic analysis as system messages

alt Question contains analysis keywords
    PB -> PB: Check analysis cache
    alt Cache miss
        PB -> CA: Deep structure analysis\n(use_llm = true)
        CA --> PB: SWMate analysis result
        PB -> PB: Cache analysis result
    end
    PB -> PB: Append \"File Structure Analysis\"\n(system message)
end

PB -> PB: Append chat history
PB -> PB: Append user question

PB --> CLI: Final messages[]

CLI -> LLM: chat_completion(messages)\n(model: gpt-4o-mini,\njson response if needed)

LLM --> CLI: LLM response
CLI --> User: Render result\n(Rich table / text)

@enduml

```

Ask 모드는 PromptBuilder(ContextManager)를 중심으로 프롬프트를 조립한 뒤 LLM 백엔드에 질의하는 단계입니다.

사용자가 /ask <question>을 입력하면 CLI는 PromptBuilder의 build() 메서드를 호출합니다.
PromptBuilder는 단순한 프롬프트 생성기가 아니라, **상태를 유지하는 캐시형 컨텍스트 관리자**로 동작합니다.


### PromptBuilder의 최종 messages 배열 구성
1. System Prompt 로딩
   - 본 정책 프롬프트(코드 분석 전문가 역할, 한국어 응답, JSON 응답 강제 규칙 등)를 로드합니다.
2. 파일 컨텍스트 및 기본 구조 분석 추가
   - FileManager에 저장된 파일 원문을 system 메시지로 추가합니다.
   - CoeAnalyzer를 사용해 기본 구조 분석 처리한 내용 또한 system 메세지로 추가합니다.
3. 조건부 심화 분석 처리
   - 사용자 질문에 “분석” 키워드가 포함된 경우에만, CoeAnalyzer를 통해 LLM 기반 심화 분석(use_llm=true) 을 수행합니다.
   - 이 결과는 캐시되며, 동일한 분석 요청에 대해 중복 호출을 방지한다.
4. 대화 히스토리 및 사용자 입력 추가
   - 기존 대화 히스토리와 현재 사용자 질문을 마지막에 추가하여 메시지를 완성합니다.
