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
        """RepoMap 관련 디버그 출력 (cyan)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[cyan][RepoMap DEBUG][/cyan] {message}")

    @classmethod
    def file_analysis(cls, message: str):
        """파일 분석 관련 디버그 출력 (yellow)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[yellow][FileAnalysis DEBUG][/yellow] {message}")

    @classmethod
    def context(cls, message: str):
        """컨텍스트 관련 디버그 출력 (blue)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[blue][Context DEBUG][/blue] {message}")

    @classmethod
    def error(cls, message: str):
        """에러 관련 디버그 출력 (red)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[red][Error DEBUG][/red] {message}")

    @classmethod
    def info(cls, message: str):
        """일반 정보 디버그 출력 (기본색)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[INFO DEBUG] {message}")

    @classmethod
    def llm(cls, message: str):
        """LLM 호출 관련 디버그 출력 (magenta)"""
        if cls._debug_enabled:
            console = cls._get_console()
            console.print(f"[magenta][LLM DEBUG][/magenta] {message}")