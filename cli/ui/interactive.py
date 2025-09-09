"""
Interactive UI module - Handles user interactions and mode switching
"""

from rich.console import Console
from typing import Dict, List, Any


class InteractiveUI:
    """Handles interactive UI elements and mode switching"""
    
    def __init__(self, console: Console):
        self.console = console

    def display_mode_switch_message(self, mode: str):
        """모드 전환 메시지"""
        description = "코드에 대해 질문할 수 있습니다" if mode == "ask" else "코드 수정을 요청할 수 있습니다"
        
        self.console.print(f"[bright_green]• '{mode}' 모드로 전환되었습니다.[/bright_green]")
        self.console.print(f"[dim white]• 이제 {description}.[/dim white]\n")

    def display_loading_message(self, message: str = "AI가 생각중입니다..."):
        """로딩 메시지 표시"""
        return self.console.status(f"[white]• {message}[/white]", spinner="dots")

    def display_separator(self):
        """구분선 표시"""
        from rich.rule import Rule
        self.console.print(Rule(style="dim white"))

    def display_welcome_banner(self, task: str):
        """환영 배너 표시 - 아이콘 없이 dots 사용"""
        import time
        from rich.text import Text
        from rich.align import Align
        
        # 심플하고 임팩트 있는 제목 (더 작게)
        title_text = Text()
        title_text.append("\n")
        title_text.append("█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█\n", style="bold bright_blue")
        title_text.append("█                            █\n", style="bold bright_blue")
        title_text.append("█         SWING CLI          █\n", style="bold bright_cyan")
        title_text.append("█                            █\n", style="bold bright_blue") 
        title_text.append("█     AI Coding Assistant    █\n", style="bold bright_magenta")
        title_text.append("█                            █\n", style="bold bright_blue")
        title_text.append("█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█\n", style="bold bright_blue")
        title_text.append("\n")
        
        # 메인 배너 패널 (테두리 없이)
        main_panel = Align.center(title_text)
        
        # 화면 지우고 애니메이션 효과
        self.console.clear()
        
        # 점진적으로 배너 표시
        self.console.print()
        with self.console.status("[bright_white]• Loading Swing CLI...", spinner="dots"):
            time.sleep(1)
        
        self.console.print(main_panel)
        
        # 짧은 지연 후 상태 패널 표시
        time.sleep(0.5)
        
        # 상태 정보 패널
        from rich.panel import Panel
        status_info = f"""
[bright_white]• 현재 모드:[/bright_white] [white]{task.upper()}[/white]
[bright_white]• 빠른 시작:[/bright_white] [white] [yellow]/help[/yellow] 명령어로 모든 기능 확인 [/white]
[bright_white]• 특별 기능:[/bright_white] [white]C파일과 SQL파일 자동 구조 분석[/white]
[bright_white]• 지원 파일:[/bright_white] [white]C, SQL, Python 등 다양한 파일 형식[/white]
        """
        
        status_panel = Panel(
            status_info,
            style="green",
            title="[bold] 상태 정보 및 빠른 가이드[/bold]",
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

    def display_help_panel(self):
        """도움말 패널 - 아이콘 없이 dots 사용"""
        from rich.panel import Panel
        
        help_text = """
[bold cyan]•  사용 가능한 명령어:[/bold cyan]

[yellow]/add[/yellow] <file1|dir1> <file2|dir2> ... - 파일 또는 디렉토리를 재귀적으로 세션에 추가
[yellow]/files[/yellow] - 현재 추가된 파일 목록을 테이블로 보기
[yellow]/tree[/yellow] - 추가된 파일을 트리 구조로 보기
[yellow]/analyze[/yellow] <directory> - 디렉토리 구조 분석 및 프로젝트 인사이트 제공
[yellow]/info[/yellow] <file> - 이미 추가된 파일의 상세 분석 정보 다시 보기
[yellow]/clear[/yellow] - 대화 기록 초기화


[bold cyan]•  작업 모드:[/bold cyan]

[yellow]/ask[/yellow] - 질문/분석 모드 (코드 설명, 버그 분석 등)
[yellow]/edit[/yellow] - 수정/구현 모드 (실제 파일 변경, 코드 생성)
[yellow]/edit[/yellow] <전략> - 특정 전략으로 edit 모드 (예: /edit udiff, /edit block)


[bold cyan]•  파일 편집 명령어:[/bold cyan]

[yellow]/preview[/yellow] - 마지막 edit 응답의 변경사항 미리보기
[yellow]/apply[/yellow] - 변경사항을 실제 파일에 적용
[yellow]/history[/yellow] - 편집 히스토리 보기
[yellow]/rollback[/yellow] <ID> - 특정 편집 작업 되돌리기
[yellow]/debug[/yellow] - 마지막 edit 응답 디버깅 정보


[bold cyan]•  세션 관리:[/bold cyan]

[yellow]/session[/yellow] - 현재 세션 ID 확인
[yellow]/session-reset[/yellow] - 세션 초기화

[yellow]/help[/yellow] - 이 도움말 메시지 표시
[yellow]/exit[/yellow] or [yellow]/quit[/yellow] - CLI 종료


[bold cyan]•  편집 전략 예시:[/bold cyan]

[yellow]/edit udiff[/yellow] - "print 오타 수정해줘" (정밀 수정)
[yellow]/edit block[/yellow] - "login 함수 수정해줘" (블록 교체)  
[yellow]/edit whole[/yellow] - "User 클래스 추가해줘" (대규모 변경)


[dim]💡 팁: .c 파일과 .sql 파일은 자동으로 구조를 분석합니다![/dim]

[bold cyan]•  키보드 단축키:[/bold cyan]
[dim]Ctrl+C[/dim] - 현재 작업 중단
[dim]Ctrl+D[/dim] - 프로그램 종료
[dim]↑/↓[/dim] - 명령어 히스토리 탐색
                """ 
        return Panel(help_text, title="📖 도움말", style="bright_blue")

    def detect_edit_keywords(self, user_input: str) -> bool:
        """사용자 입력에서 edit 요청 키워드 감지"""
        edit_keywords = ["수정해줘", "수정해 줘", "바꿔줘", "바꿔 줘", "고쳐줘", "고쳐 줘", "편집해줘", "편집해 줘"]
        return any(keyword in user_input for keyword in edit_keywords)

    def auto_switch_to_edit_mode(self):
        """edit 모드로 자동 전환 메시지"""
        self.console.print(f"[bright_green]• '수정해줘' 요청으로 edit 모드로 자동 전환되었습니다.[/bright_green]")
        self.console.print(f"[dim white]• 이제 파일 수정을 요청할 수 있습니다.[/dim white]\n")

    def display_unknown_command_error(self, command_part: str):
        """알려진 명령어가 아닌 경우 에러 메시지"""
        from rich.panel import Panel
        
        known_commands = ['/add', '/files', '/tree', '/analyze', '/info', '/clear', '/preview', '/apply', 
                        '/history', '/debug', '/rollback', '/ask', '/edit', '/session', '/session-reset', '/mcp', '/help', '/exit', '/quit']
        
        if command_part not in [cmd.lower() for cmd in known_commands]:
            error_panel = Panel(
                f"[red]• 알 수 없는 명령어: '{command_part}'[/red]\n\n"
                f"[white]• 사용 가능한 명령어:[/white]\n"
                f"[dim white]• 파일 관리: /add, /files, /tree, /analyze, /info, /clear[/dim white]\n"
                f"[dim white]• 모드 전환: /ask, /edit[/dim white]\n"
                f"[dim white]• 편집 기능: /preview, /apply, /history, /rollback, /debug[/dim white]\n"
                f"[dim white]• 세션 관리: /session, /session-reset[/dim white]\n"
                f"[dim white]• MCP 도구: /mcp, /mcp help <도구명>[/dim white]\n"
                f"[dim white]• 기타: /help, /exit[/dim white]\n\n"
                f"[dim white]'/help' 명령어로 자세한 도움말을 확인하세요.[/dim white]",
                title="• 명령어 오류",
                style="red"
            )
            self.console.print(error_panel)
            return True
        return False

    def display_edit_next_steps(self):
        """Edit 후 다음 단계 안내"""
        from rich.columns import Columns
        from rich.panel import Panel
        
        info_dict = {
            "다음 단계": "'/apply' - 변경사항 적용\n'/ask' - 질문 모드로 전환"
        }
        
        panels = []
        for key, value in info_dict.items():
            panel = Panel(
                value,
                title=f"• {key}",
                style="white",
                expand=True
            )
            panels.append(panel)
        
        self.console.print(Columns(panels, equal=True, expand=True))