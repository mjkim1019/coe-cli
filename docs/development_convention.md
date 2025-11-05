# SwingMate 개발 컨벤션

이 문서는 SwingMate 프로젝트의 원활한 협업을 위한 개발 규칙을 정의합니다.

## 목차
1.  [일반 원칙](#1-일반-원칙)
2.  [Git 브랜치 전략](#2-git-브랜치-전략)
3.  [커밋 메시지 컨벤션](#3-커밋-메시지-컨벤션)
4.  [개발 작업 흐름](#4-개발-작업-흐름)
5.  [Pull Request (PR) 가이드](#5-pull-request-pr-가이드)

---

## 1. 일반 원칙
- 모든 작업은 GitHub Issue를 생성하는 것에서 시작합니다.
- `main` 브랜치에 대한 직접적인 push는 금지되며, 모든 변경은 Pull Request (PR)를 통해서만 반영됩니다.
- 코드, 커밋 메시지, 브랜치명 등은 가급적 영문으로 작성하는 것을 원칙으로 합니다.

---

## 2. Git 브랜치 전략

본 프로젝트는 Git Flow를 기반으로 한 브랜치 전략을 사용합니다.

-   **`main`**: 제품으로 출시될 수 있는 준비가 완료된, 가장 안정적인 브랜치입니다.
-   **`develop`**: 다음 출시 버전을 개발하는 통합 브랜치입니다. 기능 개발이 완료되면 `develop` 브랜치로 병합됩니다.
-   **`feature/{issue-number}-{short-description}`**: 새로운 기능 개발을 위한 브랜치입니다.
    -   `develop` 브랜치에서 생성합니다.
    -   예시: `feature/123-user-authentication`
-   **`fix/{issue-number}-{short-description}`**: 버그 수정을 위한 브랜치입니다.
    -   `develop` 브랜치에서 생성합니다.
    -   예시: `fix/124-login-button-error`
-   **`release/{version}`**: 새로운 버전 출시를 준비하기 위한 브랜치입니다.
    -   `develop` 브랜치에서 생성하며, 버전명(예: `v1.2.0`)을 따릅니다.
    -   이 브랜치에서는 버그 수정, 문서 추가 등 출시에 필요한 최종 작업만 수행합니다.
-   **`hotfix/{issue-number}-{short-description}`**: 출시된 버전에 발생한 긴급한 버그를 수정하기 위한 브랜치입니다.
    -   `main` 브랜치에서 생성합니다.

---

## 3. 커밋 메시지 컨벤션

프로젝트는 [Conventional Commits](https://www.conventionalcommits.org/) 명세를 따릅니다. 이를 통해 커밋 히스토리의 가독성을 높이고, 변경 사항 추적을 용이하게 합니다.

### 구조
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 주요 타입 (Type)
-   **`feat`**: 새로운 기능 추가
-   **`fix`**: 버그 수정
-   **`docs`**: 문서의 추가 또는 수정
-   **`style`**: 코드 스타일에 대한 수정 (포맷팅, 세미콜론 등 기능 변경 없음)
-   **`refactor`**: 코드 리팩토링 (기능 변경 없이 내부 구조 개선)
-   **`test`**: 테스트 코드 추가 또는 수정
-   **`chore`**: 빌드, 패키지 매니저 설정 등 기타 잡다한 작업

### 예시
**Good:**
```
feat(auth): implement user login API
fix(parser): resolve memory leak in XML parser
docs(readme): add project setup guide
```

**Bad:**
```
bug fix
update
코드 수정
```

---

## 4. 개발 작업 흐름

1.  **Issue 생성**: 개발할 기능이나 수정할 버그에 대한 GitHub Issue를 생성합니다. (담당자, 라벨 등을 명시)
2.  **Branch 생성**: 생성된 Issue 페이지에서 `Create a branch` 버튼을 눌러 컨벤션에 맞는 이름의 브랜치를 생성합니다.
3.  **개발 및 커밋**: 로컬 환경에서 기능을 개발하고, 커밋 메시지 컨벤션에 맞게 변경 사항을 커밋합니다.
4.  **Push**: 작업이 완료되면 원격(remote) 브랜치로 push합니다.
    ```bash
    git push origin feature/123-my-feature
    ```
5.  **Pull Request (PR) 생성**: `develop` 브랜치를 대상으로 PR을 생성합니다. (PR 가이드 참고)
6.  **코드 리뷰**: 동료(Reviewer)에게 코드 리뷰를 요청합니다. 리뷰어는 변경 사항을 검토하고 의견을 제시합니다.
7.  **Merge**: 리뷰에서 승인(Approve)을 받고 모든 CI 체크가 통과되면, PR을 `develop` 브랜치에 병합(Squash and Merge)합니다.
8.  **Branch 삭제**: 병합이 완료된 후, 작업 브랜치는 삭제하여 저장소를 깔끔하게 유지합니다.

---

## 5. Pull Request (PR) 가이드

-   **제목**: 커밋 메시지 컨벤션과 유사하게, PR이 어떤 작업을 수행하는지 명확히 나타냅니다. (예: `feat(auth): Implement user login`)
-   **설명 (Description)**:
    -   `Related to: #{issue-number}` 형식으로 관련 이슈를 반드시 링크합니다.
    -   변경 사항에 대한 상세한 설명과 배경을 작성합니다.
    -   어떻게 테스트했는지, 리뷰어가 어떤 부분을 중점적으로 봐야 하는지 가이드를 제공합니다.
-   **리뷰어 지정**: 최소 1명 이상의 동료를 리뷰어로 지정합니다.
-   **단위**: PR은 가능한 작은 단위로, 하나의 특정 목적을 갖도록 작성하는 것을 권장합니다.