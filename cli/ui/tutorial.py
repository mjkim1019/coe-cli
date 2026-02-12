"""
Mider 튜토리얼 모드
새 사용자를 위한 단계별 대화형 튜토리얼 제공
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from itertools import chain
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from prompt_toolkit import PromptSession


class TutorialMode:
    """Mider 대화형 튜토리얼 모드"""
    
    def __init__(self, console: Console, file_manager, file_editor, llm_service, ui_components, panels, interactive_ui, session: PromptSession):
        self.console = console
        self.file_manager = file_manager
        self.file_editor = file_editor
        self.llm_service = llm_service
        self.ui = ui_components
        self.panels = panels
        self.interactive_ui = interactive_ui
        self.session = session
        self.tutorial_dir = None
        self.current_step = 0
        self.total_steps = 8
        
        # 튜토리얼 단계 설정
        self.steps = [
            {
                'title': '환영합니다!',
                'description': 'Mider 튜토리얼에 오신 것을 환영합니다.\n\n이 튜토리얼은 실제 파일을 사용하여 Mider의 주요 기능을 단계별로 안내합니다.\n\n언제든지 "exit" 또는 "restart"를 입력하여 튜토리얼을 종료하거나 재시작할 수 있습니다.',
                'action': None
            },
            {
                'title': '1단계: 파일 추가하기',
                'description': '먼저 작업할 파일을 추가하는 방법을 배워봅시다.\n\n/add 명령어를 사용하면 분석하고 편집할 파일을 추가할 수 있습니다.\n\n실습용 C, XML, SQL 파일을 추가해보겠습니다.',
                'action': 'add_files',
                'command': '/add',
                'files': ['tests/fixtures/ORDSS04S2050T01.c', 'tests/fixtures/ZORDSS04S2050.XML', 'tests/fixtures/zord_svc_prod_grp_s0001.sql']
            },
            {
                'title': '2단계: 파일 목록 확인하기',
                'description': '추가된 파일들을 확인하는 방법을 배워봅시다.\n\n/files 명령어로 현재 추가된 파일 목록을 볼 수 있습니다.\n/tree 명령어로 파일의 트리 구조를 볼 수 있습니다.',
                'action': 'list_files',
                'command': '/files'
            },
            {
                'title': '3단계: C 파일 분석하기',
                'description': '파일에 대한 상세 분석 정보를 확인하는 방법을 배워봅시다.\n\n/info 명령어를 사용하면 파일의 구조와 내용을 자동으로 분석한 결과를 볼 수 있습니다.\n\nC 파일의 경우 함수, 구조체, 변수 등을 자동으로 분석합니다.',
                'action': 'analyze_file',
                'command': '/info',
                'file': 'ORDSS04S2050T01.c',
                'file_type': 'C'
            },
            {
                'title': '4단계: XML 파일 분석하기',
                'description': 'XML 파일 분석 기능을 배워봅시다.\n\n/info 명령어는 XML 파일의 구조도 자동으로 분석합니다.\n\nXML 스키마, 엘리먼트, 속성 등을 파악할 수 있습니다.',
                'action': 'analyze_file',
                'command': '/info',
                'file': 'ZORDSS04S2050.XML',
                'file_type': 'XML'
            },
            {
                'title': '5단계: SQL 파일 분석하기',
                'description': 'SQL 파일 분석 기능을 배워봅시다.\n\n/info 명령어는 SQL 파일도 분석하여 쿼리 구조를 파악합니다.\n\n테이블, 컬럼, 조인 관계 등을 자동으로 추출합니다.',
                'action': 'analyze_file',
                'command': '/info',
                'file': 'zord_svc_prod_grp_s0001.sql',
                'file_type': 'SQL'
            },
            {
                'title': '6단계: AI에게 질문하기',
                'description': 'AI에게 코드에 대한 질문을 하는 방법을 배워봅시다.\n\n/ask 모드(기본 모드)에서는 추가된 파일에 대해 질문할 수 있습니다.\n\n예: "이 파일의 주요 기능은 무엇인가요?"\n     "어떤 함수들이 있나요?"',
                'action': 'ask_question',
                'command': '/ask',
                'question': '이 C 파일의 주요 기능과 함수들을 설명해주세요.'
            },
            {
                'title': '7단계: 코드 수정하기',
                'description': 'AI를 통해 코드를 수정하는 방법을 배워봅시다.\n\n/edit 모드에서는 파일에 대한 수정 요청을 할 수 있습니다.\n수정 사항은 /preview로 미리 확인하고 /apply로 적용할 수 있습니다.\n\n간단한 주석을 추가해보겠습니다.',
                'action': 'edit_code',
                'command': '/edit',
                'edit_request': 'a000_init_proc 함수 위에 "초기화 함수입니다" 라는 주석을 추가해주세요.'
            },
            {
                'title': '튜토리얼 완료!',
                'description': '축하합니다! Mider의 기본 기능을 모두 배우셨습니다.\n\n학습한 내용:\n• /add - 파일 추가\n• /files, /tree - 파일 목록 확인\n• /info - 파일 분석 (C, XML, SQL)\n• /ask - AI에게 질문\n• /edit - 코드 수정\n\n더 많은 명령어는 /help를 입력하여 확인하세요.\n\n이제 실제 프로젝트에서 Mider를 활용해보세요!',
                'action': 'complete'
            }
        ]
    
    def start(self) -> bool:
        """튜토리얼 모드 시작"""
        try:
            # 튜토리얼 환경 설정
            if not self._setup_tutorial_env():
                return False
            
            self.current_step = 0
            
            # 환영 메시지 표시
            self._display_step()
            
            # 단계 진행
            while self.current_step < self.total_steps:
                response = self._wait_for_user()
                
                if response == 'exit':
                    self.console.print("[yellow]튜토리얼을 종료합니다...[/yellow]")
                    self._cleanup()
                    return False
                elif response == 'restart':
                    self.console.print("[cyan]튜토리얼을 처음부터 다시 시작합니다...[/cyan]")
                    self._cleanup()
                    return self.start()
                
                # 단계 액션 실행
                step_result = self._execute_step()
                
                if not step_result:
                    # 단계 실패 - 사용자에게 다음 행동 요청
                    self.console.print()
                    self.console.print("[yellow]⚠️  이 단계에서 오류가 발생했습니다.[/yellow]")
                    retry_response = self.session.prompt("다시 시도하시겠습니까? [Y/N]: ").strip().lower()
                    
                    if retry_response in ['y', 'yes']:
                        self.console.print("[cyan]🔄 단계를 다시 시도합니다...[/cyan]")
                        continue  # 동일한 단계 재시도
                    else:
                        self.console.print("[yellow]튜토리얼을 종료합니다.[/yellow]")
                        self._cleanup()
                        return False
                
                # 단계 성공 - 다음 단계로 이동할지 확인
                self.console.print()
                self.console.print("[bold green]✅ 단계 완료![/bold green]")
                
                # 마지막 단계가 아니면 다음 단계로 이동 여부 확인
                if self.current_step < self.total_steps:
                    # 유효한 입력을 받을 때까지 반복
                    while True:
                        next_step_response = self.session.prompt("다음 단계로 이동하시겠습니까? [Y/n]: ").strip().lower()
                        
                        # 유효한 입력 체크 (입력은 이미 소문자로 변환됨)
                        valid_yes = ['y', 'yes', '예', '네', '']  # 빈 문자열 = Enter 키
                        valid_no = ['n', 'no', '아니오', '아니요']
                        
                        if next_step_response in valid_yes:
                            # Yes 선택 - 다음 단계로 진행
                            break
                        elif next_step_response in valid_no:
                            # No 선택 - 옵션 메뉴 표시
                            action = self._handle_step_pause()
                            
                            if action == 'retry':
                                # 현재 단계 재실행
                                self.console.print("[cyan]🔄 이 단계를 다시 실행합니다...[/cyan]")
                                continue  # 동일한 단계 재시도
                            elif action == 'continue':
                                # 다음 단계로 진행
                                self.console.print("[green]▶ 다음 단계로 이동합니다.[/green]")
                                # 아래에서 자동으로 다음 단계로 이동
                                break
                            elif action == 'exit':
                                # 튜토리얼 종료
                                self.console.print("[yellow]튜토리얼을 종료합니다.[/yellow]")
                                self._cleanup()
                                return False
                        else:
                            # 잘못된 입력
                            self.console.print(f"[yellow]⚠️  잘못된 입력: '{next_step_response}'[/yellow]")
                            self.console.print("[dim]'Y' (예/Yes) 또는 'n' (아니오/No)만 입력 가능합니다.[/dim]")
                            continue  # 다시 입력 받기
                
                # 다음 단계로 이동
                self.current_step += 1
                if self.current_step <= self.total_steps:  # <= 로 변경하여 완료 단계도 표시
                    self._display_step()
            
            # 정리
            self._cleanup()
            
            self.console.print()
            self.console.print(Panel(
                "[bold green]튜토리얼을 완료했습니다! 이제 Mider를 자유롭게 사용하실 수 있습니다.[/bold green]",
                title="✅ 완료",
                border_style="green"
            ))
            
            return True
            
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]튜토리얼이 중단되었습니다.[/yellow]")
            self._cleanup()
            return False
        except Exception as e:
            self.console.print(f"[red]튜토리얼 중 오류 발생: {e}[/red]")
            self._cleanup()
            return False
    
    def _setup_tutorial_env(self) -> bool:
        """픽스처 파일로 튜토리얼 환경 설정"""
        try:
            # 임시 튜토리얼 디렉토리 생성
            self.tutorial_dir = Path.cwd() / '.tutorial_workspace'
            
            # 존재하면 삭제
            if self.tutorial_dir.exists():
                shutil.rmtree(self.tutorial_dir)
            
            self.tutorial_dir.mkdir(parents=True, exist_ok=True)
            
            # 픽스처 파일을 튜토리얼 디렉토리로 복사
            fixtures_dir = Path(__file__).parent.parent.parent / 'tests' / 'fixtures'
            
            if not fixtures_dir.exists():
                self.console.print(f"[red]❌ 테스트 픽스처 디렉터리를 찾을 수 없습니다: {fixtures_dir}[/red]")
                self.console.print("[yellow]튜토리얼을 실행하려면 tests/fixtures/ 디렉터리가 필요합니다.[/yellow]")
                return False
            
            # 필수 픽스처 파일 확인
            required_files = ['ORDSS04S2050T01.c', 'ZORDSS04S2050.XML', 'zord_svc_prod_grp_s0001.sql']
            missing_files = []
            
            for required in required_files:
                if not (fixtures_dir / required).exists():
                    missing_files.append(required)
            
            if missing_files:
                self.console.print(f"[red]❌ 필수 픽스처 파일이 없습니다:[/red]")
                for missing in missing_files:
                    self.console.print(f"   • {missing}")
                self.console.print()
                
                response = self.session.prompt("계속 진행하시겠습니까? (일부 단계를 건너뛸 수 있습니다) [y/N]: ").strip().lower()
                if response not in ['y', 'yes']:
                    self.console.print("[yellow]튜토리얼이 취소되었습니다.[/yellow]")
                    return False
                self.console.print("[yellow]⚠️  일부 단계가 제대로 작동하지 않을 수 있습니다.[/yellow]")
            
            # C 파일 복사
            copied_count = 0
            for fixture_file in fixtures_dir.glob('*.c'):
                dest = self.tutorial_dir / fixture_file.name
                shutil.copy2(fixture_file, dest)
                copied_count += 1
            
            # 헤더 파일 복사
            for fixture_file in fixtures_dir.glob('*.h'):
                dest = self.tutorial_dir / fixture_file.name
                shutil.copy2(fixture_file, dest)
                copied_count += 1
            
            # SQL 파일 복사
            for fixture_file in fixtures_dir.glob('*.sql'):
                dest = self.tutorial_dir / fixture_file.name
                shutil.copy2(fixture_file, dest)
                copied_count += 1
            
            # XML 파일 복사 (.xml 및 .XML 확장자 모두)
            for fixture_file in chain(fixtures_dir.glob('*.xml'), fixtures_dir.glob('*.XML')):
                dest = self.tutorial_dir / fixture_file.name
                shutil.copy2(fixture_file, dest)
                copied_count += 1
            
            self.console.print(f"[dim]✓ 튜토리얼 환경 준비 완료: {self.tutorial_dir} ({copied_count}개 파일)[/dim]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ 튜토리얼 환경 설정 실패: {e}[/red]")
            import traceback
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return False
    
    def _cleanup(self):
        """튜토리얼 환경 정리"""
        try:
            # 파일 매니저 초기화
            self.file_manager.files.clear()
            
            # 튜토리얼 디렉토리 삭제
            if self.tutorial_dir and self.tutorial_dir.exists():
                shutil.rmtree(self.tutorial_dir)
                self.console.print(f"[dim]튜토리얼 환경 정리 완료[/dim]")
        except Exception as e:
            self.console.print(f"[yellow]정리 중 오류: {e}[/yellow]")
    
    def _display_step(self):
        """현재 단계 정보 표시"""
        step = self.steps[self.current_step]
        
        # 진행률 표시 (환영 단계를 위해 total_steps + 1)
        progress = f"단계 {self.current_step + 1}/{self.total_steps + 1}"
        
        # Create panel
        panel_content = Text()
        panel_content.append(f"\n{step['description']}\n\n", style="white")
        
        if step.get('command'):
            panel_content.append(f"다음 명령어를 실행합니다: ", style="dim")
            panel_content.append(f"{step['command']}", style="bold cyan")
            
            if step.get('files'):
                panel_content.append(f"\n대상 파일: ", style="dim")
                panel_content.append(f"{', '.join(step['files'])}", style="yellow")
            
            if step.get('file'):
                panel_content.append(f"\n대상 파일: ", style="dim")
                panel_content.append(f"{step['file']}", style="yellow")
        
        panel_content.append("\n\n계속하려면 Enter를 누르세요...", style="bold bright_cyan")
        panel_content.append("\n(종료: exit, 재시작: restart)", style="dim")
        
        panel = Panel(
            panel_content,
            title=f"[bold bright_blue]{step['title']}[/bold bright_blue] [{progress}]",
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
    
    def _wait_for_user(self) -> str:
        """사용자가 Enter를 누르거나 명령어를 입력할 때까지 대기"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = self.session.prompt("").strip().lower()
                
                # 입력 검증
                if response and response not in ['', 'exit', 'restart']:
                    self.console.print(f"[yellow]⚠️  알 수 없는 명령어: '{response}'[/yellow]")
                    self.console.print("[dim]사용 가능한 명령어: Enter (계속), 'exit' (종료), 'restart' (재시작)[/dim]")
                    retry_count += 1
                    if retry_count >= max_retries:
                        self.console.print("[yellow]⚠️  잘못된 입력이 반복되어 자동으로 계속 진행합니다.[/yellow]")
                        return 'continue'
                    continue  # 다시 시도
                
                return response if response else 'continue'
            except (KeyboardInterrupt, EOFError):
                return 'exit'
        
        return 'continue'  # 폴백
    
    def _handle_step_pause(self) -> str:
        """사용자가 다음 단계로 이동하지 않기로 선택했을 때 옵션 메뉴 표시"""
        self.console.print()
        self.console.print("[bold cyan]어떻게 하시겠습니까?[/bold cyan]")
        self.console.print("  [yellow]1.[/yellow] 이 단계 다시 실행 (retry)")
        self.console.print("  [green]2.[/green] 다음 단계로 이동 (continue)")
        self.console.print("  [red]3.[/red] 튜토리얼 종료 (exit)")
        self.console.print()
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                choice = self.session.prompt("선택 [1-3]: ").strip().lower()
                
                # 숫자 또는 텍스트 입력 처리
                if choice in ['1', 'retry', 'r']:
                    return 'retry'
                elif choice in ['2', 'continue', 'c', 'next', '']:
                    return 'continue'
                elif choice in ['3', 'exit', 'e', 'quit', 'q']:
                    return 'exit'
                else:
                    self.console.print(f"[yellow]⚠️  잘못된 선택: '{choice}'[/yellow]")
                    self.console.print("[dim]1, 2, 3 중 하나를 선택하거나 retry/continue/exit를 입력하세요.[/dim]")
                    retry_count += 1
                    
                    if retry_count >= max_retries:
                        self.console.print("[yellow]⚠️  잘못된 입력이 반복되어 자동으로 다음 단계로 이동합니다.[/yellow]")
                        return 'continue'
                    continue
                    
            except (KeyboardInterrupt, EOFError):
                self.console.print()
                return 'exit'
        
        return 'continue'  # 폴백

    
    def _execute_step(self) -> bool:
        """현재 단계의 액션 실행"""
        step = self.steps[self.current_step]
        action = step.get('action')
        
        if action is None:
            return True
        
        try:
            self.console.print()
            
            if action == 'add_files':
                return self._step_add_files(step)
            elif action == 'list_files':
                return self._step_list_files(step)
            elif action == 'analyze_file':
                return self._step_analyze_file(step)
            elif action == 'ask_question':
                return self._step_ask_question(step)
            elif action == 'edit_code':
                return self._step_edit_code(step)
            elif action == 'complete':
                return True
            
            return True
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]단계가 중단되었습니다.[/yellow]")
            raise  # 메인 핸들러로 전파
        except Exception as e:
            self.console.print(f"[red]❌ 단계 실행 중 오류 발생:[/red]")
            self.console.print(f"[red]   {type(e).__name__}: {e}[/red]")
            
            # 디버그 모드에서 상세한 오류 표시
            import traceback
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
            
            return False  # 단계 실패 신호
    
    def _step_add_files(self, step: Dict) -> bool:
        """파일 추가 단계 실행"""
        files = step.get('files', [])
        
        # Convert to absolute paths in tutorial directory
        abs_files = [str(self.tutorial_dir / Path(f).name) for f in files]
        
        # Check if files exist
        missing_files = [f for f in abs_files if not Path(f).exists()]
        if missing_files:
            self.console.print(f"[red]❌ 필요한 파일을 찾을 수 없습니다:[/red]")
            for missing in missing_files:
                self.console.print(f"   • {Path(missing).name}")
            self.console.print()
            return False
        
        self.console.print(f"[cyan]► {step['command']} 명령 실행 중...[/cyan]")
        
        try:
            result = self.file_manager.add(abs_files)
            
            # 결과 표시
            self.interactive_ui.display_file_add_results(result, self.file_manager, self.ui, self.console)
            
            self.console.print("[green]✓ 파일 추가 완료![/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]❌ 파일 추가 중 오류: {e}[/red]")
            return False
    
    def _step_list_files(self, step: Dict) -> bool:
        """파일 목록 표시 단계 실행"""
        try:
            self.console.print(f"[cyan]► {step['command']} 명령 실행 중...[/cyan]")
            self.console.print()
            
            if not self.file_manager.files:
                self.console.print("[yellow]⚠️  파일 관리자에 파일이 없습니다.[/yellow]")
                self.console.print("[dim]이전 단계에서 파일 추가가 실패했을 수 있습니다.[/dim]")
                return False
            
            self.console.print(self.ui.file_list_table(self.file_manager.files))
            
            self.console.print()
            self.console.print("[green]✓ 파일 목록 확인 완료![/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]❌ 파일 목록 표시 중 오류: {e}[/red]")
            return False
    
    def _step_analyze_file(self, step: Dict) -> bool:
        """파일 분석 단계 실행"""
        file_name = step.get('file')
        file_type = step.get('file_type', 'Unknown')
        
        try:
            # 파일 매니저에서 파일 찾기
            found_file = None
            for file_path in self.file_manager.files.keys():
                if Path(file_path).name == file_name:
                    found_file = file_path
                    break
            
            if not found_file:
                self.console.print(f"[red]❌ 파일을 찾을 수 없습니다: {file_name}[/red]")
                self.console.print("[dim]파일 관리자에 이 파일이 추가되어 있지 않습니다.[/dim]")
                return False
            
            self.console.print(f"[cyan]► {step['command']} 명령 실행 중... ({file_type} 파일)[/cyan]")
            
            # 파일 재분석
            result = self.file_manager.add_single_file(found_file)
            
            if result.get('analysis'):
                analysis_result = self.ui.file_analysis_panel([
                    {
                        'file_path': found_file,
                        'file_type': result['file_type'],
                        'analysis': result['analysis']
                    }
                ])
                
                if isinstance(analysis_result, list):
                    for panel in analysis_result:
                        self.console.print(panel)
                        self.console.print()
                else:
                    self.console.print(analysis_result)
            
            self.console.print(f"[green]✓ {file_type} 파일 분석 완료![/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]❌ 파일 분석 중 오류: {e}[/red]")
            return False
    
    def _step_ask_question(self, step: Dict) -> bool:
        """질문하기 단계 실행"""
        question = step.get('question')
        
        try:
            self.console.print(f"[cyan]► AI에게 질문 중...[/cyan]")
            self.console.print(f"[dim]질문: {question}[/dim]")
            self.console.print()
            
            # 프롬프트 생성
            from cli.core.context_manager import PromptBuilder
            prompt_builder = PromptBuilder('ask')
            messages = prompt_builder.build(question, self.file_manager.files, [], self.file_manager)
            
            # AI 응답 받기
            with self.interactive_ui.display_loading_message():
                llm_response = self.llm_service.chat_completion(messages)
            
            if llm_response and "choices" in llm_response:
                response_content = llm_response["choices"][0]["message"]["content"]
                self.console.print(self.panels.create_ai_response_panel(response_content))
                self.console.print()
                self.console.print("[green]✓ AI 응답 완료![/green]")
                return True
            else:
                self.console.print("[red]❌ AI 응답을 받지 못했습니다.[/red]")
                self.console.print("[dim]LLM 서비스에 문제가 있을 수 있습니다.[/dim]")
                return False
        except Exception as e:
            self.console.print(f"[red]❌ AI 질문 중 오류: {e}[/red]")
            return False
    
    def _step_edit_code(self, step: Dict) -> bool:
        """코드 수정 단계 실행"""
        edit_request = step.get('edit_request')
        
        try:
            self.console.print(f"[cyan]► 코드 수정 요청 중...[/cyan]")
            self.console.print(f"[dim]요청: {edit_request}[/dim]")
            self.console.print()
            
            # 수정용 프롬프트 생성
            from cli.core.context_manager import PromptBuilder
            prompt_builder = PromptBuilder('edit')
            messages = prompt_builder.build(edit_request, self.file_manager.files, [], self.file_manager)
            
            # AI 응답 받기
            with self.interactive_ui.display_loading_message("AI가 코드를 수정하고 있습니다..."):
                llm_response = self.llm_service.chat_completion(messages)
            
            if llm_response and "choices" in llm_response:
                response_content = llm_response["choices"][0]["message"]["content"]
                
                # 변경사항 미리보기 (적용하지 않음)
                from cli.coders.base_coder import registry
                coder = registry.get_coder('whole', self.file_editor)
                
                try:
                    preview = coder.preview_changes(response_content, self.file_manager.files)
                    
                    if preview and 'error' not in preview:
                        self.console.print()
                        panels = self.ui.file_changes_preview(preview)
                        for panel in panels:
                            self.console.print(panel)
                        
                        self.console.print()
                        self.console.print("[green]✓ 코드 수정 미리보기 완료![/green]")
                        self.console.print("[dim]💡 실제 프로젝트에서는 /apply 명령으로 변경사항을 적용할 수 있습니다.[/dim]")
                        return True
                    else:
                        self.console.print("[yellow]⚠️  수정 사항을 미리볼 수 없습니다.[/yellow]")
                        self.console.print("[dim]AI가 예상과 다른 형식으로 응답했을 수 있습니다.[/dim]")
                        return True  # 단계를 실패시키지 않고 경고만 표시
                except Exception as e:
                    self.console.print(f"[yellow]⚠️  미리보기 생성 실패: {e}[/yellow]")
                    return True  # 단계를 실패시키지 않음
            else:
                self.console.print("[red]❌ AI 응답을 받지 못했습니다.[/red]")
                self.console.print("[dim]LLM 서비스에 문제가 있을 수 있습니다.[/dim]")
                return False
        except Exception as e:
            self.console.print(f"[red]❌ 코드 수정 중 오류: {e}[/red]")
            return False
