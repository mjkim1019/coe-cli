"""
Document Generator - AGENTS.md와 같은 프로젝트 문서 파일 생성
"""

import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel


class DocumentGenerator:
    """표준 프로젝트 문서 파일 생성기"""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.templates_dir = Path(__file__).parent.parent / '.mider'

    def generate_agents_md(self, project_name: str = None, project_description: str = None) -> bool:
        """AGENTS.md 파일을 템플릿으로부터 생성"""
        try:
            # 템플릿 읽기
            template_path = self.templates_dir / 'AGENTS.md'
            if not template_path.exists():
                self.console.print(f"[red]❌ 템플릿을 찾을 수 없습니다: {template_path}[/red]")
                return False
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 프로젝트 정보 가져오기
            if project_name is None:
                project_name = Path.cwd().name
            
            if project_description is None:
                project_description = "프로젝트 설명을 입력하세요"
            
            # 변수 치환
            content = template_content.replace('{{ project_name }}', project_name)
            content = content.replace('{{ created_at }}', datetime.now().strftime('%Y-%m-%d'))
            
            # 현재 디렉토리에 AGENTS.md 작성
            output_path = Path.cwd() / 'AGENTS.md'
            
            # 파일이 이미 존재하는지 확인
            if output_path.exists():
                self.console.print(f"[yellow]⚠️  AGENTS.md 파일이 이미 존재합니다: {output_path}[/yellow]")
                response = input("덮어쓰시겠습니까? [y/N]: ").strip().lower()
                if response not in ['y', 'yes']:
                    self.console.print("[dim]취소되었습니다.[/dim]")
                    return False
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.console.print(f"[green]✅ AGENTS.md 파일이 성공적으로 생성되었습니다: {output_path}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ AGENTS.md 생성 중 오류 발생: {e}[/red]")
            return False
    
    def init_project(self) -> bool:
        """표준 문서 파일로 프로젝트 초기화"""
        try:
            # 현재 디렉토리 이름을 프로젝트 이름으로 자동 감지
            project_name = Path.cwd().name
            
            self.console.print()
            self.console.print(Panel(
                "[bold bright_blue]Mider 프로젝트 초기화[/bold bright_blue]\n\n"
                f"프로젝트: [cyan]{project_name}[/cyan]\n"
                "표준 문서 파일을 생성합니다.",
                border_style="bright_blue",
                padding=(1, 2)
            ))
            self.console.print()
            
            self.console.print(f"[dim]프로젝트 문서 생성 중: {project_name}[/dim]")
            self.console.print()
            
            # AGENTS.md 생성
            success = self.generate_agents_md(project_name)
            
            if success:
                self.console.print()
                self.console.print(Panel(
                    "[bold green]✅ 프로젝트 초기화가 완료되었습니다![/bold green]\n\n"
                    "[white]생성된 파일:[/white]\n"
                    "  • AGENTS.md - AI 에이전트 역할 및 협업 규칙\n\n"
                    "[dim]이제 Mider를 사용하여 코드를 분석하고 수정할 수 있습니다.[/dim]",

                    title="성공",
                    border_style="green",
                    padding=(1, 2)
                ))
            
            return success
            
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]초기화가 취소되었습니다.[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ 초기화 중 오류 발생: {e}[/red]")
            return False
