"""
디버그 출력 전용 매니저 클래스
Rich Console을 사용하여 통일된 색깔과 포맷으로 디버그 메시지를 출력
"""
from rich.console import Console
from typing import Optional

class DebugManager:
    """
    디버그 출력을 관리하는 전용 클래스

    색깔 코드:
    - RepoMap: cyan
    - FileAnalysis: yellow
    - Context: blue
    - Error: red
    """

    _console: Optional[Console] = None
    _debug_enabled: bool = True

    @classmethod
    def _get_console(cls) -> Console:
        """Console 인스턴스를 반환 (싱글톤 패턴)"""
        if cls._console is None:
            cls._console = Console()
        return cls._console

    @classmethod
    def set_debug_enabled(cls, enabled: bool):
        """디버그 출력 ON/OFF 설정"""
        cls._debug_enabled = enabled

    @classmethod
    def is_debug_enabled(cls) -> bool:
        """디버그 출력 상태 확인"""
        return cls._debug_enabled

    @classmethod
    def repo_map(cls, message: str):
        """RepoMap 관련 디버그 출력 (dim cyan)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[cyan dim][RepoMap DEBUG][/cyan dim] [dim]{message}[/dim]")

    @classmethod
    def file_analysis(cls, message: str):
        """파일 분석 관련 디버그 출력 (dim yellow)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[yellow dim][FileAnalysis DEBUG][/yellow dim] [dim]{message}[/dim]")

    @classmethod
    def context(cls, message: str):
        """컨텍스트 관련 디버그 출력 (dim blue)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[blue dim][Context DEBUG][/blue dim] [dim]{message}[/dim]")

    @classmethod
    def error(cls, message: str):
        """에러 관련 디버그 출력 (dim red)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[red dim][Error DEBUG][/red dim] [dim]{message}[/dim]")

    @classmethod
    def info(cls, message: str):
        """일반 정보 디버그 출력 (dim)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[dim][INFO DEBUG] {message}[/dim]")

    @classmethod
    def llm(cls, message: str):
        """LLM 호출 관련 디버그 출력 (dim magenta)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[magenta dim][LLM DEBUG][/magenta dim] [dim]{message}[/dim]")

    @classmethod
    def prompt(cls, message: str):
        """프롬프트 관련 디버그 출력 (dim green)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[green dim][Prompt DEBUG][/green dim] [dim]{message}[/dim]")

    @classmethod
    def prompt_content(cls, title: str, content: str, max_length: int = 500):
        """프롬프트 내용 전체 출력 (긴 내용 지원)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[green dim][Prompt DEBUG][/green dim] [dim]{title}:[/dim]")
            if len(content) > max_length:
                console.print(f"[dim]{content[:max_length]}...[truncated, total: {len(content)} chars][/dim]")
            else:
                console.print(f"[dim]{content}[/dim]")