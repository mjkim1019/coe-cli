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

class SwingUIComponents:
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
        with self.console.status("[bold bright_cyan]🚀 Loading Swing CLI...", spinner="aesthetic"):
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

[yellow]/add[/yellow] <file1> <file2> ... - 파일을 세션에 추가
[yellow]/files[/yellow] - 현재 추가된 파일 목록을 테이블로 보기
[yellow]/tree[/yellow] - 추가된 파일을 트리 구조로 보기
[yellow]/clear[/yellow] - 대화 기록 초기화

[bold cyan]🤖 작업 모드:[/bold cyan]
[yellow]/ask[/yellow] - 질문/분석 모드 (코드 설명, 버그 분석 등)
[yellow]/edit[/yellow] - 수정/구현 모드 (실제 파일 변경, 코드 생성)

[bold cyan]📝 파일 편집 명령어:[/bold cyan]
[yellow]/preview[/yellow] - 마지막 edit 응답의 변경사항 미리보기
[yellow]/apply[/yellow] - 변경사항을 실제 파일에 적용
[yellow]/history[/yellow] - 편집 히스토리 보기
[yellow]/rollback[/yellow] <ID> - 특정 편집 작업 되돌리기
[yellow]/debug[/yellow] - 마지막 edit 응답 디버깅 정보

[yellow]/help[/yellow] - 이 도움말 메시지 표시
[yellow]/exit[/yellow] or [yellow]/quit[/yellow] - CLI 종료

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
            title="🤖 AI Response",
            title_align="left",
            style="bright_green",
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
            f"[green]{message}[/green]",
            title="📁 파일 추가 완료",
            style="bright_green"
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

    def loading_spinner(self, message: str = "AI가 생각중입니다..."):
        """로딩 스피너 컨텍스트 매니저"""
        return self.console.status(f"[bold green]🧠 {message}", spinner="dots")

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
                        if child.label == f"📂 {part}":
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
                from datetime import datetime
                dt = datetime.fromisoformat(op.timestamp)
                formatted_time = dt.strftime("%m/%d %H:%M")
            except:
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