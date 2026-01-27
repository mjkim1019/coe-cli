
"""
UI 컴포넌트 모듈 - Gemini CLI에서 영감을 받은 재사용 가능한 UI 요소들
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.columns import Columns
from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from rich.syntax import Syntax
from typing import List, Dict, Optional, Tuple, Any
import time
import os
from datetime import datetime

class MiderUIComponents:
    def __init__(self, console: Console):
        self.console = console

    def welcome_banner(self, task: str):
        """환영 배너 표시"""
        # 심플하고 임팩트 있는 제목 (더 작게)
        title_text = Text()
        title_text.append("\n")
        title_text.append("█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█\n", style="bold bright_blue")
        title_text.append("█                            █\n", style="bold bright_blue")
        title_text.append("█     🚀  SWING CLI  🤖     █\n", style="bold bright_cyan")
        title_text.append("█                            █\n", style="bold bright_blue") 
        title_text.append("█  AI Development Assistant  █\n", style="bold bright_magenta")
        title_text.append("█                            █\n", style="bold bright_blue")
        title_text.append("█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█\n", style="bold bright_blue")
        title_text.append("\n")
        
        # 메인 배너 패널 (테두리 없이)
        main_panel = Align.center(title_text)
        
        # 화면 지우고 애니메이션 효과
        self.console.clear()
        
        # 점진적으로 배너 표시
        self.console.print()
        with self.console.status("[bold bright_cyan]🚀 Loading Mider...", spinner="aesthetic"):
            time.sleep(1)
        
        self.console.print(main_panel)
        
        # 짧은 지연 후 상태 패널 표시
        time.sleep(0.5)
        
        # 상태 정보 패널
        status_info = f"""
[bold green]🎯 현재 모드:[/bold green] [bold yellow]{task.upper()}[/bold yellow]
[bold cyan]💡 빠른 시작:[/bold cyan] [bold yellow]/help[/bold yellow] 명령어로 모든 기능 확인  
[bold magenta]🔥 특별 기능:[/bold magenta] C파일과 SQL파일 자동 구조 분석
[bold blue]📁 지원 파일:[/bold blue] C, SQL, Python 등 다양한 파일 형식
        """
        
        status_panel = Panel(
            status_info,
            style="green",
            title="[bold]📊 상태 정보 및 빠른 가이드[/bold]",
            title_align="left",
            border_style="green",
            padding=(0, 1)
        )
        
        self.console.print(status_panel)
        
        # 환영 메시지
        welcome_msg = Panel(
            Align.center("✨ [bold bright_magenta]개발 업무를 도와드릴 준비가 완료되었습니다![/bold bright_magenta] ✨"),
            style="bright_magenta",
            padding=(0, 1),
            border_style="bright_magenta"
        )
        
        self.console.print(welcome_msg)
        self.console.print()

    def help_panel(self):
        """도움말 패널"""
        help_text = """
[bold cyan]📋 사용 가능한 명령어:[/bold cyan]

[yellow]/add[/yellow] <file1|dir1> <file2|dir2> ... - 파일 또는 디렉토리를 재귀적으로 세션에 추가
[yellow]/files[/yellow] - 현재 추가된 파일 목록을 테이블로 보기
[yellow]/tree[/yellow] - 추가된 파일을 트리 구조로 보기
[yellow]/analyze[/yellow] <directory> - 디렉토리 구조 분석 및 프로젝트 인사이트 제공
[yellow]/info[/yellow] <file> - 이미 추가된 파일의 상세 분석 정보 다시 보기
[yellow]/clear[/yellow] - 대화 기록 초기화

[bold cyan]🤖 작업 모드:[/bold cyan]
[yellow]/ask[/yellow] - 질문/분석 모드 (코드 설명, 버그 분석 등)
[yellow]/edit[/yellow] - 수정/구현 모드 (실제 파일 변경, 코드 생성)
[yellow]/edit[/yellow] <전략> - 특정 전략으로 edit 모드 (예: /edit udiff, /edit block)

[bold cyan]🏗️  AI 태스크 오케스트레이션:[/bold cyan]
[yellow]/architect[/yellow] "자연어 요청" - AI가 자동으로 계획 생성 및 실행
    예: /architect "유선 회선 기준 유무선 결합 가입년수 조회 쿼리 개발해줘"
    지원: 파일 생성(/new), 파일 추가(/add), 편집(/edit), 실행(/exec), 테스트(/test), 질문(/ask)

[bold cyan]📝 파일 편집 명령어:[/bold cyan]
[yellow]/preview[/yellow] - 마지막 edit 응답의 변경사항 미리보기
[yellow]/apply[/yellow] - 변경사항을 실제 파일에 적용
[yellow]/history[/yellow] - 편집 히스토리 보기
[yellow]/rollback[/yellow] <ID> - 특정 편집 작업 되돌리기
[yellow]/debug[/yellow] - 마지막 edit 응답 디버깅 정보

[bold cyan]🌐 세션 관리:[/bold cyan]
[yellow]/session[/yellow] - 현재 세션 ID 확인
[yellow]/session-reset[/yellow] - 세션 초기화

[yellow]/tutorial[/yellow] - 대화형 튜토리얼 시작
[yellow]/help[/yellow] - 이 도움말 메시지 표시
[yellow]/exit[/yellow] or [yellow]/quit[/yellow] - CLI 종료

[bold cyan]🛠️ 편집 전략 예시:[/bold cyan]
[yellow]/edit udiff[/yellow] - "print 오타 수정해줘" (정밀 수정)
[yellow]/edit block[/yellow] - "login 함수 수정해줘" (블록 교체)  
[yellow]/edit whole[/yellow] - "User 클래스 추가해줘" (대규모 변경)

[dim]💡 팁: .c 파일과 .sql 파일은 자동으로 구조를 분석합니다![/dim]

[bold cyan]⌨️  키보드 단축키:[/bold cyan]
[dim]Ctrl+C[/dim] - 현재 작업 중단
[dim]Ctrl+D[/dim] - 프로그램 종료
[dim]↑/↓[/dim] - 명령어 히스토리 탐색
        """
        return Panel(help_text, title="📖 도움말", style="bright_blue")

    def user_question_panel(self, question: str):
        """사용자 질문 패널"""
        return Panel(
            question,
            title="🤔 Your Question",
            title_align="left",
            style="bright_cyan",
            border_style="cyan"
        )

    def ai_response_panel(self, response: str):
        """AI 응답 패널"""
        return Panel(
            Markdown(response),
            title="AI Response",
            title_align="left",
            style="white",
            border_style="green"
        )

    def file_list_table(self, files: Dict[str, str]):
        """파일 목록을 테이블로 표시"""
        if not files:
            return Panel(
                "[yellow]📁 추가된 파일이 없습니다.[/yellow]\n[dim]'/add <파일경로>' 명령으로 파일을 추가하세요.[/dim]",
                title="📂 File List",
                style="yellow"
            )

        table = Table(title="📂 Added Files", show_header=True, header_style="bold magenta")
        table.add_column("File Path", style="cyan", no_wrap=False)
        table.add_column("Size", justify="right", style="green")
        table.add_column("Type", justify="center", style="yellow")
        
        for file_path, content in files.items():
            file_size = f"{len(content)} chars"
            file_type = "📄 Text"
            if file_path.endswith('.c'):
                file_type = "🔧 C"
            elif file_path.endswith('.sql'):
                file_type = "🗃️ SQL"
            elif file_path.endswith('.py'):
                file_type = "🐍 Python"
            
            table.add_row(file_path, file_size, file_type)
        
        return table

    def file_added_panel(self, message: str):
        """파일 추가 완료 패널"""
        return Panel(
            f"{message}",
            title="파일 추가 완료",
            style="white"
        )

    def mode_switch_message(self, mode: str):
        """모드 전환 메시지"""
        icon = "💬" if mode == "ask" else "✏️"
        description = "코드에 대해 질문할 수 있습니다" if mode == "ask" else "코드 수정을 요청할 수 있습니다"
        
        self.console.print(f"[bold green]✅ '{mode}' 모드로 전환되었습니다.[/bold green]")
        self.console.print(f"[dim]{icon} 이제 {description}.[/dim]\n")

    def error_panel(self, error_message: str, title: str = "오류"):
        """에러 패널"""
        return Panel(
            f"[red]❌ {error_message}[/red]",
            title=title,
            style="red"
        )

    def success_panel(self, message: str, title: str = "완료"):
        """성공 패널"""
        return Panel(
            f"[green]✅ {message}[/green]",
            title=title,
            style="green"
        )

    def info_panel(self, message: str, title: str = "정보"):
        """정보 패널"""
        return Panel(
            f"[blue]ℹ️  {message}[/blue]",
            title=title,
            style="blue"
        )

    def loading_spinner(self, message: str = "AI가 생각중입니다..."):
        """로딩 스피너 컨텍스트 매니저"""
        return self.console.status(f"[bold green] {message}", spinner="dots")

    def separator(self):
        """구분선"""
        self.console.print(Rule(style="dim"))

    def goodbye_panel(self):
        """종료 메시지"""
        return Panel(
            "[bold red]👋 안녕히 가세요![/bold red]",
            style="red",
            title="종료",
            expand=False
        )

    def info_columns(self, info_dict: Dict[str, str]):
        """정보를 컬럼으로 표시"""
        panels = []
        for key, value in info_dict.items():
            panel = Panel(
                value,
                title=key,
                style="blue",
                expand=True
            )
            panels.append(panel)
        
        return Columns(panels, equal=True, expand=True)

    def file_tree(self, files: Dict[str, str]):
        """파일 트리 구조로 표시"""
        tree = Tree("📁 Project Files")
        
        # 파일들을 경로별로 그룹화
        for file_path in files.keys():
            parts = file_path.split('/')
            current = tree
            
            # 경로의 각 부분을 트리에 추가
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # 마지막 부분 (파일명)
                    if file_path.endswith('.c'):
                        current.add(f"🔧 {part}")
                    elif file_path.endswith('.sql'):
                        current.add(f"🗃️ {part}")
                    elif file_path.endswith('.py'):
                        current.add(f"🐍 {part}")
                    else:
                        current.add(f"📄 {part}")
                else:  # 디렉토리
                    # 기존 노드가 있는지 확인
                    found = False
                    for child in current.children:
                        if str(child.label) == f"📂 {part}":
                            current = child
                            found = True
                            break
                    
                    if not found:
                        current = current.add(f"📂 {part}")
        
        return tree

    def warning_panel(self, message: str):
        """경고 패널"""
        return Panel(
            f"[yellow]⚠️ {message}[/yellow]",
            title="경고",
            style="yellow"
        )

    def diff_panel(self, diff_content: str, file_path: str):
        """diff 내용을 표시하는 패널"""
        return Panel(
            diff_content,
            title=f"📝 변경사항 - {file_path}",
            style="cyan",
            border_style="cyan"
        )

    def render_visual_diff(self, visual_diff: List[Tuple[str, str]]) -> Text:
        """시각적 diff를 Rich Text 객체로 렌더링"""
        result = Text()
        
        for diff_type, line in visual_diff:
            if diff_type == 'header':
                # 파일 헤더 (파란색)
                result.append(line + '\n', style="bold blue")
            elif diff_type == 'hunk':
                # 라인 번호 정보 (마젠타)
                result.append(line + '\n', style="bold magenta")
            elif diff_type == 'removed':
                # 삭제된 라인 (빨간 배경)
                result.append(line + '\n', style="white on red")
            elif diff_type == 'added':
                # 추가된 라인 (초록 배경)
                result.append(line + '\n', style="white on green")
            elif diff_type == 'context':
                # 컨텍스트 라인 (회색)
                result.append(line + '\n', style="dim white")
            else:
                # 기타
                result.append(line + '\n', style="white")
        
        return result

    def file_changes_preview(self, preview_data: Dict[str, Dict[str, Any]]):
        """파일 변경사항 미리보기"""
        if not preview_data:
            return [self.warning_panel("변경할 파일이 없습니다.")]
        
        panels = []
        
        for file_path, data in preview_data.items():
            # 파일 상태 표시
            status = "🆕 새 파일" if not data['exists'] else "✏️ 수정"
            
            # 시각적 diff 렌더링
            if 'visual_diff' in data and data['visual_diff']:
                diff_content = self.render_visual_diff(data['visual_diff'])
            else:
                # fallback to regular diff
                diff_content = data.get('diff', "[dim]차이점 없음[/dim]")
            
            # diff가 비어있거나 헤더만 있는 경우
            if not data.get('visual_diff') or len(data['visual_diff']) <= 2:
                if data['exists']:
                    diff_content = Text("[dim]파일 내용이 동일합니다[/dim]")
                else:
                    # 새 파일의 경우 전체 내용 표시
                    new_lines = data['new'].splitlines()
                    diff_content = Text()
                    diff_content.append(f"새 파일 생성 ({len(new_lines)}줄)\n", style="bold green")
                    for i, line in enumerate(new_lines[:10]):  # 처음 10줄만 표시
                        diff_content.append(f"+ {line}\n", style="white on green")
                    if len(new_lines) > 10:
                        diff_content.append(f"... ({len(new_lines) - 10}줄 더)\n", style="dim")
            
            panel = Panel(
                diff_content,
                title=f"{status} {file_path}",
                style="cyan",
                border_style="cyan",
                expand=False
            )
            panels.append(panel)
        
        # 메인 컨테이너
        header = Panel(
            f"[bold cyan]📋 총 {len(preview_data)}개 파일이 변경됩니다[/bold cyan]",
            style="bright_cyan",
            title="변경사항 미리보기"
        )
        
        result_panels = [header] + panels
        return result_panels

    def edit_history_table(self, operations: List):
        """편집 히스토리를 테이블로 표시"""
        if not operations:
            return Panel(
                "[yellow]📋 편집 히스토리가 없습니다.[/yellow]",
                title="📜 Edit History",
                style="yellow"
            )

        table = Table(title="📜 편집 히스토리", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=8)
        table.add_column("시간", style="green", width=16)
        table.add_column("설명", style="white")
        table.add_column("파일 수", justify="center", style="yellow", width=8)
        
        for op in operations:
            # 시간 포맷팅
            try:
                dt = datetime.fromisoformat(op.timestamp)
                formatted_time = dt.strftime("%m/%d %H:%M")
            except ValueError:
                formatted_time = op.timestamp[:16]
            
            table.add_row(
                op.operation_id,
                formatted_time,
                op.description,
                str(len(op.changes))
            )
        
        return table

    def rollback_confirmation(self, operation_id: str, description: str):
        """롤백 확인 메시지"""
        return Panel(
            f"[yellow]⚠️ 다음 작업을 되돌리시겠습니까?[/yellow]\n\n" 
            f"[bold]작업 ID:[/bold] {operation_id}\n"
            f"[bold]설명:[/bold] {description}\n\n"
            f"[dim]'/rollback {operation_id} confirm' 명령으로 확인하거나[/dim]\n"
            f"[dim]'/rollback cancel'로 취소하세요.[/dim]",
            title="🔄 롤백 확인",
            style="yellow"
        )

    def apply_confirmation(self, file_count: int):
        """변경사항 적용 확인 메시지"""
        return Panel(
            f"[green]✅ 총 {file_count}개 파일에 변경사항이 적용되었습니다![/green]\n\n"
            f"[dim]'/history' 명령으로 편집 히스토리를 확인하거나[/dim]\n"
            f"[dim]문제가 있다면 '/rollback <ID>'로 되돌릴 수 있습니다.[/dim]",
            title="🎉 적용 완료",
            style="green"
        )

    def edit_summary_panel(self, summary: Dict[str, Any]):
        """편집 작업 요약 패널"""
        content = []
        
        # 전체 요약
        total = summary['total_files']
        new = summary['new_files'] 
        modified = summary['modified_files']
        
        content.append(f"[bold green]📊 편집 완료 요약[/bold green]\n")
        content.append(f"[cyan]총 파일:[/cyan] {total}개")
        if new > 0:
            content.append(f"[green]새 파일:[/green] {new}개")
        if modified > 0:
            content.append(f"[yellow]수정:[/yellow] {modified}개")
        
        content.append("")
        
        # 파일별 상세
        for detail in summary['files_details']:
            path = detail['file_path']
            filename = os.path.basename(path)
            description = detail['change_description']
            
            if detail['is_new']:
                content.append(f"[green]🆕 {filename}[/green]")
                content.append(f"   [dim]{description}[/dim]")
            else:
                content.append(f"[yellow]✏️ {filename}[/yellow]")
                content.append(f"   [dim]{description}[/dim]")
        
        return Panel(
            "\n".join(content),
            title="📈 편집 요약",
            style="bright_blue",
            border_style="blue"
        )

    def rollback_success(self, operation_id: str):
        """롤백 성공 메시지"""
        return Panel(
            f"[green]✅ 작업 '{operation_id}'이 성공적으로 되돌려졌습니다![/green]",
            title="🔄 롤백 완료",
            style="green"
        )

    def edit_mode_response_panel(self, response: str):
        """Edit 모드 AI 응답 패널 (파일 수정 내용 포함)"""
        return Panel(
            Markdown(response),
            title="🤖 AI가 생성한 코드",
            title_align="left",
            style="bright_blue",
            border_style="blue"
        )

    def strategies_table(self, strategies: Dict[str, Any], current_strategy: str):
        """편집 전략 목록을 테이블로 표시"""
        table = Table(title="🛠️ 편집 전략 목록", show_header=True, header_style="bold magenta")
        table.add_column("전략", style="cyan", width=12)
        table.add_column("현재", justify="center", style="green", width=6)
        table.add_column("설명", style="white")
        table.add_column("최적 용도", style="yellow")
        
        for strategy_name, coder_class in strategies.items():
            # 현재 전략인지 체크
            is_current = "✅" if strategy_name == current_strategy else ""
            
            # 코더 인스턴스 생성해서 정보 얻기
            try:
                temp_coder = coder_class(None)  # FileEditor는 임시로 None
                description = ""
                use_cases = ""
                
                # 전략별 설명 매핑
                if strategy_name == "whole":
                    description = "전체 파일 교체"
                    use_cases = "새 파일, 대규모 변경"
                elif strategy_name == "block":
                    description = "코드 블록 교체"
                    use_cases = "부분 수정, 함수 변경"
                elif strategy_name == "udiff":
                    description = "Unix diff 형식"
                    use_cases = "정밀 수정, Git 연동"
                else:
                    description = "사용자 정의 전략"
                    use_cases = "특수 목적"
                    
            except Exception:
                description = "편집 전략"
                use_cases = "일반 목적"
            
            table.add_row(strategy_name, is_current, description, use_cases)
        
        return table

    def directory_analysis_panel(self, analysis: Dict):
        """디렉토리 분석 결과를 패널로 표시"""
        if 'error' in analysis:
            return self.error_panel(analysis['error'], "디렉토리 분석 오류")
        
        content = []
        
        # 기본 정보
        path = analysis.get('path', 'Unknown')
        total_files = analysis.get('total_files', 0)
        content.append(f"📁 Path: {path}")
        content.append(f"📊 Total Files: {total_files}")
        
        # 프로젝트 인사이트
        insights = analysis.get('project_insights', {})
        if insights:
            content.append("\n🔍 Project Analysis:")
            content.append(f"  • Type: {insights.get('project_type', 'unknown')}")
            content.append(f"  • Complexity: {insights.get('complexity', 'unknown')}")
            
            characteristics = insights.get('characteristics', [])
            if characteristics:
                content.append(f"  • Characteristics: {', '.join(characteristics)}")
            
            tech_stack = insights.get('tech_stack', [])
            if tech_stack:
                content.append(f"  • Tech Stack: {', '.join(tech_stack)}")
        
        # 파일 카테고리별 통계
        file_categories = analysis.get('file_categories', {})
        if file_categories:
            content.append("\n📋 File Categories:")
            for category, files in file_categories.items():
                if files:
                    count = len(files)
                    category_display = category.replace('_', ' ').title()
                    content.append(f"  • {category_display}: {count} files")
                    
                    # 주요 파일들 일부 표시
                    if category in ['c_files', 'header_files', 'sql_files'] and count > 0:
                        sample_files = files[:3]  # 처음 3개만
                        for file_info in sample_files:
                            file_name = os.path.basename(file_info['path'])
                            content.append(f"    - {file_name}")
                        if count > 3:
                            content.append(f"    ... and {count - 3} more")
        
        # 추천 파일들
        suggested_files = analysis.get('suggested_files', [])
        if suggested_files:
            content.append("\n💡 Recommended Context Files:")
            for suggestion in suggested_files[:5]:  # 상위 5개만
                file_name = os.path.basename(suggestion['file'])
                reason = suggestion.get('reason', '')
                priority = suggestion.get('priority', 'medium')
                priority_emoji = "🔥" if priority == 'high' else "📄"
                content.append(f"  {priority_emoji} {file_name} - {reason}")
        
        return Panel(
            "\n".join(content),
            title="Directory Analysis",
            title_align="left",
            style="cyan",
            border_style="cyan"
        )

    def file_analysis_panel(self, file_analyses: List[Dict]) -> Optional[Panel]:
        """파일 분석 결과를 패널로 표시"""
        if not file_analyses:
            return None
        
        content = []
        
        for analysis_data in file_analyses:
            file_path = analysis_data['file_path']
            file_type = analysis_data['file_type']
            analysis = analysis_data['analysis']
            
            file_name = os.path.basename(file_path)
            content.append(f"[bold white]• {file_name}[/bold white] [dim]({file_type})[/dim]")
            
            if file_type == 'c_file':
                # C 파일 분석 결과
                found_functions = analysis.get('found_functions', {})
                if found_functions:
                    content.append("  [bold]Standard Functions:[/bold]")
                    for func_name, func_info in found_functions.items():
                        line_num = func_info.get('line_number', 'unknown')
                        content.append(f"    • [white]{func_name}[/white] [dim](line {line_num})[/dim]")
                
                includes = analysis.get('includes', {})
                if includes:
                    # IO Formatter 헤더들
                    io_formatter = includes.get('io_formatter', [])
                    if io_formatter:
                        content.append("  [bold]I/O Formatter:[/bold]")
                        for include in io_formatter:
                            content.append(f"    • [white]{include}[/white]")
                    
                    # Static Library 헤더들 (중요!)
                    static_lib = includes.get('static_library', [])
                    if static_lib:
                        content.append("  [bold]Static Library (Business Logic):[/bold]")
                        for include in static_lib:
                            content.append(f"    • [white]{include}[/white]")
                    
                    # DBIO Library 헤더들
                    dbio_lib = includes.get('dbio_library', [])
                    if dbio_lib:
                        content.append("  [bold]DBIO Library:[/bold]")
                        for include in dbio_lib:
                            content.append(f"    • [white]{include}[/white]")
                
            
            elif file_type == 'header_file':
                # 헤더 파일 분석 결과
                header_type = analysis.get('type', 'unknown')
                content.append(f"  [bold]Type:[/bold] [white]{header_type}[/white]")
                
                structures = analysis.get('structures', [])
                struct_details = analysis.get('struct_details', {})
                if structures:
                    content.append("  [bold]Structures:[/bold]")
                    for struct in structures:
                        content.append(f"    • [white]{struct}[/white]")
                        # I/O 구조체인 경우 별도 테이블로 표시됨
                        if header_type == 'io_structure' and struct in struct_details:
                            fields = struct_details[struct]
                            if fields:
                                content.append(f"      [cyan]{len(fields)}[/cyan] [dim]fields (detailed table below)[/dim]")
                        # 일반 구조체인 경우 중요 필드만 표시
                        elif struct in struct_details:
                            fields = struct_details[struct]
                            if fields:
                                important_fields = [f for f in fields if f['comment']][:3]  # 코멘트 있는 중요 필드 3개
                                for field in important_fields:
                                    field_desc = f"[yellow]{field['type']}[/yellow] [white]{field['name']}[/white]"
                                    if field['size']:
                                        field_desc += f"[blue][{field['size']}][/blue]"
                                    if field['comment']:
                                        field_desc += f" [dim]// {field['comment']}[/dim]"
                                    content.append(f"      - {field_desc}")
                                if len(fields) > len(important_fields):
                                    content.append(f"      [dim]... and {len(fields) - len(important_fields)} more fields[/dim]")
                
                defines = analysis.get('defines', [])
                if defines:
                    content.append(f"  [bold]Defines:[/bold] [white]{len(defines)}[/white] [dim]macros[/dim]")
                    # 길이 정의들 표시 (LEN_으로 시작하는 것들)
                    len_defines = [d for d in defines if isinstance(d, dict) and d['name'].startswith('LEN_')][:3]
                    for define in len_defines:
                        content.append(f"    • [cyan]{define['name']}[/cyan] = [white]{define['value']}[/white]")
            
            elif file_type == 'sql_file':
                # SQL 파일 분석 결과
                oracle_features = analysis.get('oracle_features', [])
                if oracle_features:
                    content.append(f"  [bold]Oracle Features:[/bold] [bright_white]{', '.join(oracle_features)}[/bright_white]")
                
                bind_variables = analysis.get('bind_variables', [])
                if bind_variables:
                    content.append(f"  [bold]Bind Variables:[/bold] [bright_white]{', '.join(bind_variables[:5])}[/bright_white]")
                    if len(bind_variables) > 5:
                        content.append(f"    [dim]... and {len(bind_variables) - 5} more[/dim]")
            
            elif file_type == 'xml_file':
                # XML 파일 분석 결과
                form_id = analysis.get('form_id', '')
                if form_id:
                    content.append(f"  [bold]Form ID:[/bold] [white]{form_id}[/white]")
                
                form_description = analysis.get('form_description', '')
                if form_description:
                    content.append(f"  [bold]Form 설명:[/bold] [white]{form_description}[/white]")
                
                datalist_ids = analysis.get('datalist_ids', [])
                if datalist_ids:
                    content.append(f"  [bold]DataList IDs:[/bold] [white]{', '.join(datalist_ids[:3])}[/white]")
                    if len(datalist_ids) > 3:
                        content.append(f"    [dim]... and {len(datalist_ids) - 3} more[/dim]")
                
                trx_codes = analysis.get('trx_codes', [])
                if trx_codes:
                    content.append(f"  [bold]TrxCodes:[/bold] [white]{len(trx_codes)}개[/white] [dim]({', '.join(trx_codes[:2])}{'...' if len(trx_codes) > 2 else ''})[/dim]")
                
                svc_combo_count = analysis.get('svc_combo_count', 0)
                if svc_combo_count > 0:
                    content.append(f"  [bold]svcCombo:[/bold] [white]{svc_combo_count}개[/white]")
                
                functions = analysis.get('functions', [])
                if functions:
                    content.append(f"  [bold]Functions:[/bold] [white]{len(functions)}[/white] [dim]JavaScript functions[/dim]")
        
        # I/O 구조체 테이블 생성
        struct_tables = []
        for analysis_data in file_analyses:
            file_type = analysis_data['file_type']
            analysis = analysis_data['analysis']
            
            # I/O 구조체인 경우 테이블 생성
            if file_type == 'header_file' and analysis.get('type') == 'io_structure':
                struct_details = analysis.get('struct_details', {})
                for struct_name, fields in struct_details.items():
                    if fields:  # 필드가 있는 경우에만
                        table = self._create_struct_table(struct_name, fields)
                        struct_tables.append(table)
        
        # 메인 분석 패널
        main_panel = Panel(
            "\n".join(content),
            title=None,
            title_align="left",
            style="white",
            border_style="green"
        )
        
        # 구조체 테이블이 있으면 함께 반환
        if struct_tables:
            return [main_panel] + struct_tables
        else:
            return main_panel
    
    def _create_struct_table(self, struct_name: str, fields: List[Dict]) -> Table:
        """구조체 필드를 테이블로 생성"""
        table = Table(title=f"📋 {struct_name} Structure", show_header=True, header_style="bold cyan")
        table.add_column("Type", style="yellow", width=12)
        table.add_column("Field Name", style="green", width=20)
        table.add_column("Size", style="blue", width=15)
        table.add_column("Comment", style="white")
        
        for field in fields:
            field_type = field.get('type', '')
            field_name = field.get('name', '')
            field_size = field.get('size', '') or '-'
            field_comment = field.get('comment', '') or '-'
            
            table.add_row(field_type, field_name, field_size, field_comment)
        
        return table
