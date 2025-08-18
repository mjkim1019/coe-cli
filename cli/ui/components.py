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
from typing import List, Dict, Optional
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
[yellow]/ask[/yellow] - 코드에 대해 질문하는 'ask' 모드로 전환
[yellow]/edit[/yellow] - 코드 수정을 요청하는 'edit' 모드로 전환
[yellow]/files[/yellow] - 현재 추가된 파일 목록을 테이블로 보기
[yellow]/tree[/yellow] - 추가된 파일을 트리 구조로 보기
[yellow]/clear[/yellow] - 대화 기록 초기화
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