import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from actions.file_manager import FileManager
from actions.file_editor import FileEditor
from cli.completer import PathCompleter
from llm.service import LLMService
from cli.core.context_manager import PromptBuilder
from cli.core.mcp_integration import MCPIntegration
from rich.console import Console
from rich.panel import Panel
from cli.ui.components import SwingUIComponents

# 편집 전략 import
from cli.coders.base_coder import registry
from cli.coders import wholefile_coder, editblock_coder, udiff_coder

@click.command()
def main():
    """An interactive REPL for the Swing LLM assistant."""
    console = Console()
    ui = SwingUIComponents(console)
    history = FileHistory('.swing-cli-history')
    session = PromptSession(history=history, completer=PathCompleter())
    file_manager = FileManager()
    file_editor = FileEditor()
    llm_service = LLMService()
    chat_history = []
    
    # MCP 통합 초기화
    mcp_integration = MCPIntegration()
    mcp_integration.initialize(console)
    task = 'ask'  # Default task
    edit_strategy = 'whole'  # 기본 편집 전략
    last_edit_response = None  # 마지막 edit 응답 저장
    last_user_request = None  # 마지막 사용자 요청 저장
    current_coder = registry.get_coder(edit_strategy, file_editor)  # 현재 코더

    # 웰컴 메시지
    ui.welcome_banner(task)

    while True:
        try:
            user_input = session.prompt("> ")

            if user_input.strip().lower() in ('/exit', '/quit'):
                console.print(ui.goodbye_panel())
                break

            elif user_input.strip().lower() == '/help':
                console.print(ui.help_panel())
                continue

            elif user_input.strip().lower().startswith('/add '):
                parts = user_input.strip().split()
                if len(parts) > 1:
                    files_to_add = [p.replace('@', '') for p in parts[1:]]
                    result = file_manager.add(files_to_add)
                    
                    # 기본 추가 메시지 표시
                    if isinstance(result, dict) and 'messages' in result:
                        console.print(ui.file_added_panel("\n".join(result['messages'])))
                        
                        # 파일 분석 결과가 있으면 추가로 표시
                        if result.get('analyses'):
                            analysis_result = ui.file_analysis_panel(result['analyses'])
                            if analysis_result:
                                console.print()
                                # 결과가 리스트인 경우 (테이블 포함)
                                if isinstance(analysis_result, list):
                                    for panel in analysis_result:
                                        console.print(panel)
                                        console.print()
                                else:
                                    console.print(analysis_result)
                        
                        # 자동으로 LLM 기반 분석 수행 (모든 파일에 대해)
                        if True:  # result.get('analyses') 조건 제거하여 모든 파일 분석
                            console.print("\n[bold blue] LLM 기반 심화 분석을 수행합니다...[/bold blue]")
                            try:
                                from cli.core.analyzer import CoeAnalyzer
                                analyzer = CoeAnalyzer()
                                
                                # 추가된 파일들 경로 수집
                                added_files = []
                                if result.get('analyses'):
                                    # 기존 방식 (analyses가 있는 경우)
                                    for analysis in result['analyses']:
                                        added_files.append(analysis['file_path'])
                                else:
                                    # analyses가 없는 경우, 방금 add 명령으로 추가한 파일들 
                                    # parts[1:]에서 파일 경로들을 가져옴
                                    for file_path in files_to_add:
                                        if os.path.exists(file_path):
                                            added_files.append(file_path)
                                
                                console.print(f"[dim]DEBUG: 분석할 파일 수: {len(added_files)}[/dim]")
                                
                                if added_files:
                                    files_data = {}
                                    for f in added_files:
                                        if result.get('analyses'):
                                            # 기존 분석이 있는 경우
                                            files_data[f] = {
                                                'file_type': next((a['file_type'] for a in result['analyses'] if a['file_path'] == f), 'unknown'),
                                                'basic_analysis': next((a['analysis'] for a in result['analyses'] if a['file_path'] == f), {})
                                            }
                                        else:
                                            # 기본 분석이 없는 경우
                                            files_data[f] = {
                                                'file_type': 'unknown',
                                                'basic_analysis': {}
                                            }
                                    
                                    console.print(f"[dim]DEBUG: files_data 구성 완료: {list(files_data.keys())}[/dim]")
                                    console.print(f"[dim]DEBUG: file_manager.files 키들: {list(file_manager.files.keys())}[/dim]")
                                    
                                    # analyzer의 file_manager를 현재 file_manager로 업데이트
                                    analyzer.file_manager = file_manager
                                    
                                    llm_results = analyzer._perform_llm_analysis(files_data)
                                    
                                    console.print(f"[dim]DEBUG: LLM 결과 수: {len(llm_results) if llm_results else 0}[/dim]")
                                    if llm_results:
                                        console.print(f"[dim]DEBUG: LLM 결과 키들: {list(llm_results.keys())}[/dim]")
                                        for key, value in llm_results.items():
                                            console.print(f"[dim]DEBUG: {key} -> {type(value)} with keys: {list(value.keys()) if isinstance(value, dict) else 'not dict'}[/dim]")
                                    
                                    # LLM 분석 결과 표시
                                    if llm_results:
                                        console.print()
                                        results_displayed = 0
                                        for file_path, llm_analysis in llm_results.items():
                                            console.print(f"[dim]DEBUG: 파일 {file_path} 분석 중... purpose: {llm_analysis.get('purpose', 'None')}[/dim]")
                                            if llm_analysis.get('purpose') and llm_analysis.get('purpose') != 'LLM 분석 결과 파싱 실패':
                                                filename = os.path.basename(file_path)
                                                # purpose 텍스트를 의미 단위로 줄바꿈
                                                purpose_text = llm_analysis.get('purpose', 'N/A')
                                                # 의미 단위로 줄바꿈 처리 (문장부호와 접속사 기준)
                                                import re
                                                # 문장을 의미 단위로 분리
                                                purpose_formatted = re.sub(r'(\.)', r'\1\n', purpose_text)  # 문장 끝에서 줄바꿈
                                                purpose_formatted = re.sub(r'( - )', r'\n\1', purpose_formatted)  # 대시 앞에서 줄바꿈
                                                purpose_formatted = re.sub(r'(입니다\. )', r'\1\n', purpose_formatted)  # '입니다.' 뒤에 줄바꿈
                                                purpose_formatted = re.sub(r'(습니다\. )', r'\1\n', purpose_formatted)  # '습니다.' 뒤에 줄바꿈
                                                
                                                llm_content = f"**목적**: \n{purpose_formatted.strip()}\n\n"
                                                
                                                
                                                # Input/Output 분석을 위한 테이블 준비
                                                io_tables = []
                                                if 'input_output_analysis' in llm_analysis:
                                                    io_analysis = llm_analysis['input_output_analysis']
                                                    if io_analysis:
                                                        from rich.table import Table
                                                        
                                                        # 입력 파라미터 테이블
                                                        inputs = io_analysis.get('inputs', [])
                                                        if inputs:
                                                            input_table = Table(title="📥 입력 파라미터", show_header=True, header_style="bold blue")
                                                            input_table.add_column("파라미터명")
                                                            input_table.add_column("타입") 
                                                            input_table.add_column("Nullable")
                                                            input_table.add_column("설명")
                                                            
                                                            for inp in inputs:
                                                                nullable_text = "O" if inp.get('nullable', False) else "X"
                                                                input_table.add_row(
                                                                    inp.get('name', 'N/A'),
                                                                    inp.get('type', 'N/A'),
                                                                    nullable_text,
                                                                    inp.get('description', 'N/A')
                                                                )
                                                            io_tables.append(input_table)
                                                        
                                                        # 출력 값 테이블
                                                        outputs = io_analysis.get('outputs', [])
                                                        if outputs:
                                                            output_table = Table(title="📤 출력 값", show_header=True, header_style="bold green")
                                                            output_table.add_column("출력값명")
                                                            output_table.add_column("타입")
                                                            output_table.add_column("설명")
                                                            
                                                            for out in outputs:
                                                                output_table.add_row(
                                                                    out.get('name', 'N/A'),
                                                                    out.get('type', 'N/A'),
                                                                    out.get('description', 'N/A')
                                                                )
                                                            io_tables.append(output_table)
                                                
                                                if 'suggestions' in llm_analysis and llm_analysis['suggestions']:
                                                    llm_content += f"**개선사항**: {llm_analysis['suggestions']}\n"
                                                
                                                from rich.markdown import Markdown
                                                llm_panel = Panel(
                                                    Markdown(llm_content.strip()),
                                                    title=f" {filename} LLM 분석",
                                                    border_style="magenta"
                                                )
                                                console.print(llm_panel)
                                                
                                                # Input/Output 테이블들을 별도로 표시
                                                for table in io_tables:
                                                    console.print(table)
                                                    console.print()  # 빈 줄 추가
                                                results_displayed += 1
                                            elif llm_analysis.get('purpose') == 'LLM 분석 결과 파싱 실패':
                                                # 파싱 실패 시에도 raw_response에서 purpose 추출 시도
                                                raw_response = llm_analysis.get('raw_response', '')
                                                if 'purpose' in raw_response:
                                                    import re
                                                    # raw_response에서 purpose 값 추출
                                                    match = re.search(r'"purpose":\s*"([^"]+)"', raw_response)
                                                    if match:
                                                        purpose_text = match.group(1)
                                                        # 의미 단위로 줄바꿈 처리
                                                        purpose_formatted = re.sub(r'(\.)', r'\1\n', purpose_text)
                                                        purpose_formatted = re.sub(r'( - )', r'\n\1', purpose_formatted)
                                                        purpose_formatted = re.sub(r'(입니다\. )', r'\1\n', purpose_formatted)
                                                        purpose_formatted = re.sub(r'(습니다\. )', r'\1\n', purpose_formatted)
                                                        
                                                        filename = os.path.basename(file_path)
                                                        console.print()
                                                        from rich.markdown import Markdown
                                                        fallback_panel = Panel(
                                                            Markdown(f"**목적**: \n{purpose_formatted.strip()}\n\n*JSON 파싱은 실패했지만 분석 결과를 추출했습니다.*"),
                                                            title=f" {filename} LLM 분석 (부분)",
                                                            border_style="yellow"
                                                        )
                                                        console.print(fallback_panel)
                                                        results_displayed += 1
                                                    else:
                                                        console.print(f"[dim]DEBUG: raw_response에서도 purpose 추출 실패[/dim]")
                                                else:
                                                    console.print(f"[dim]DEBUG: {file_path} - 파싱 실패, raw_response: {raw_response[:200]}...[/dim]")
                                            else:
                                                console.print(f"[dim]DEBUG: {file_path} - purpose가 없음 (전체 결과: {llm_analysis})[/dim]")
                                        
                                        if results_displayed == 0:
                                            console.print("[yellow]LLM 분석은 완료되었으나 표시할 결과가 없습니다.[/yellow]")
                                    else:
                                        console.print("[yellow]LLM 분석 결과를 받지 못했습니다.[/yellow]")
                            except Exception as e:
                                console.print(f"[red]LLM 분석 중 오류 발생: {e}[/red]")
                                import traceback
                                console.print(f"[dim]{traceback.format_exc()}[/dim]")
                    else:
                        # 이전 버전 호환성
                        console.print(ui.file_added_panel(str(result)))
                else:
                    console.print(ui.error_panel("사용법: /add <file1|dir1> <file2|dir2> ...", "입력 오류"))
                continue

            elif user_input.strip().lower() == '/files':
                console.print(ui.file_list_table(file_manager.files))
                continue

            elif user_input.strip().lower() == '/tree':
                if file_manager.files:
                    console.print(ui.file_tree(file_manager.files))
                else:
                    console.print(ui.warning_panel("추가된 파일이 없습니다. '/add <파일경로>' 명령으로 파일을 추가하세요."))
                continue

            elif user_input.strip().lower().startswith('/analyze '):
                parts = user_input.strip().split()
                if len(parts) > 1:
                    directory_path = parts[1].replace('@', '')  # @ 제거
                    # 상대 경로를 절대 경로로 변환
                    if not os.path.isabs(directory_path):
                        directory_path = os.path.abspath(directory_path)
                    
                    if os.path.isdir(directory_path):
                        analysis = file_manager.analyze_directory_structure(directory_path)
                        console.print(ui.directory_analysis_panel(analysis))
                    else:
                        console.print(ui.error_panel(f"디렉토리를 찾을 수 없습니다: {directory_path}", "분석 오류"))
                else:
                    console.print(ui.error_panel("사용법: /analyze @<directory_path> 또는 /analyze <directory_path>", "입력 오류"))
                continue

            elif user_input.strip().lower().startswith('/info '):
                parts = user_input.strip().split()
                if len(parts) > 1:
                    user_file_path = parts[1].replace('@', '')  # @ 제거
                    
                    # 여러 방식으로 파일 찾기 시도
                    found_file_path = None
                    
                    # 1. 입력 경로 그대로
                    if user_file_path in file_manager.files:
                        found_file_path = user_file_path
                    # 2. 절대 경로로 변환
                    elif not os.path.isabs(user_file_path):
                        abs_path = os.path.abspath(user_file_path)
                        if abs_path in file_manager.files:
                            found_file_path = abs_path
                    # 3. 파일명만으로 검색 (basename)
                    if not found_file_path:
                        input_basename = os.path.basename(user_file_path)
                        for file_path in file_manager.files.keys():
                            if os.path.basename(file_path) == input_basename:
                                found_file_path = file_path
                                break
                    # 4. 부분 경로 매칭
                    if not found_file_path:
                        for file_path in file_manager.files.keys():
                            if user_file_path in file_path or file_path.endswith(user_file_path):
                                found_file_path = file_path
                                break
                    
                    if found_file_path:
                        # 파일 분석 다시 수행
                        result = file_manager.add_single_file(found_file_path)
                        if result.get('analysis'):
                            analysis_result = ui.file_analysis_panel([
                                {
                                    'file_path': found_file_path,
                                    'file_type': result['file_type'],
                                    'analysis': result['analysis']
                                }
                            ])
                            if isinstance(analysis_result, list):
                                for panel in analysis_result:
                                    console.print(panel)
                                    console.print()
                            else:
                                console.print(analysis_result)
                        else:
                            console.print(ui.warning_panel(f"파일 분석 정보가 없습니다: {os.path.basename(found_file_path)}"))
                    else:
                        # 사용 가능한 파일들 표시
                        available_files = [os.path.basename(f) for f in file_manager.files.keys()]
                        console.print(ui.error_panel(
                            f"파일을 찾을 수 없습니다: {user_file_path}\n\n"
                            f"사용 가능한 파일들:\n" +
                            "\n".join(f"• {f}" for f in available_files[:10]), 
                            "파일 오류"
                        ))
                else:
                    console.print(ui.error_panel("사용법: /info @<file_path>", "입력 오류"))
                continue

            elif user_input.strip().lower() == '/session':
                session_id = llm_service.get_session_id()
                if session_id:
                    console.print(ui.info_panel(f"현재 세션 ID: {session_id}", "세션 정보"))
                else:
                    console.print(ui.info_panel("활성 세션이 없습니다.", "세션 정보"))
                continue

            elif user_input.strip().lower() == '/session-reset':
                llm_service.reset_session()
                console.print(ui.success_panel("세션이 초기화되었습니다.", "세션 리셋"))
                continue

            elif user_input.strip().lower() == '/mcp':
                mcp_integration.show_mcp_status(console)
                continue

            elif user_input.strip().lower().startswith('/mcp help '):
                parts = user_input.strip().split()
                if len(parts) >= 3:
                    tool_name = ' '.join(parts[2:])
                    mcp_integration.show_tool_help(tool_name, console)
                else:
                    console.print(ui.error_panel("사용법: /mcp help <도구명>", "명령어 오류"))
                continue

            elif user_input.strip().lower() == '/clear':
                chat_history.clear()
                console.print(ui.success_panel("대화 기록이 초기화되었습니다.", "초기화 완료"))
                continue

            elif user_input.strip().lower() == '/preview':
                if not last_edit_response:
                    console.print(ui.warning_panel("미리볼 edit 응답이 없습니다. edit 모드에서 먼저 요청하세요."))
                else:
                    preview = current_coder.preview_changes(last_edit_response, file_manager.files)
                    if 'error' in preview:
                        console.print(ui.error_panel(preview['error']['message'], f"미리보기 오류 ({preview['error']['strategy']})"))
                    else:
                        panels = ui.file_changes_preview(preview)
                        for panel in panels:
                            console.print(panel)
                continue

            elif user_input.strip().lower() == '/apply':
                if not last_edit_response:
                    console.print(ui.warning_panel("적용할 edit 응답이 없습니다. edit 모드에서 먼저 요청하세요."))
                else:
                    try:
                        # 더 구체적인 설명 생성
                        summary = current_coder.preview_changes(last_edit_response, file_manager.files)
                        if summary and 'error' not in summary:
                            file_names = list(summary.keys())
                            if len(file_names) == 1:
                                file_desc = f"{file_names[0]} 수정"
                            else:
                                file_desc = f"{len(file_names)}개 파일 수정"
                        else:
                            file_desc = "파일 수정"
                        
                        # 사용자 요청 내용 포함
                        if last_user_request and len(last_user_request) < 50:
                            description = f"{file_desc}: {last_user_request} ({edit_strategy})"
                        else:
                            description = f"{file_desc} ({edit_strategy} 전략)"
                        
                        operation = current_coder.apply_changes(last_edit_response, file_manager.files, description)
                        console.print(ui.apply_confirmation(len(operation.changes)))
                        
                        # 편집 요약 표시
                        summary = operation.get_summary()
                        console.print(ui.edit_summary_panel(summary))
                        
                        last_edit_response = None  # 적용 후 초기화
                    except Exception as e:
                        console.print(ui.error_panel(f"파일 적용 중 오류 발생: {e}", "적용 실패"))
                continue

            elif user_input.strip().lower() == '/history':
                operations = file_editor.get_history(10)
                console.print(ui.edit_history_table(operations))
                continue

            elif user_input.strip().lower() == '/debug':
                if last_edit_response:
                    console.print(Panel(
                        f"[bold]현재 전략:[/bold] {edit_strategy}\n"
                        f"[bold]마지막 Edit 응답 원문:[/bold]\n\n{last_edit_response[:1000]}{'...' if len(last_edit_response) > 1000 else ''}",
                        title="🐛 디버그 정보",
                        style="yellow"
                    ))
                    
                    # 코더별 파싱 테스트
                    parsed = current_coder.parse_response(last_edit_response, file_manager.files)
                    console.print(Panel(
                        f"[bold]파싱 결과 ({edit_strategy}):[/bold]\n" +
                        (f"파일 {len(parsed)}개 감지: {list(parsed.keys())}" if parsed else "파싱된 파일 없음"),
                        title="📝 파싱 결과",
                        style="cyan"
                    ))
                else:
                    console.print(ui.warning_panel("디버그할 edit 응답이 없습니다."))
                continue


            elif user_input.strip().lower().startswith('/rollback '):
                parts = user_input.strip().split()
                if len(parts) == 2:
                    operation_id = parts[1]
                    # 해당 작업 찾기
                    operations = file_editor.get_history()
                    target_op = None
                    for op in operations:
                        if op.operation_id == operation_id:
                            target_op = op
                            break
                    
                    if target_op:
                        console.print(ui.rollback_confirmation(operation_id, target_op.description))
                    else:
                        console.print(ui.error_panel(f"작업 ID '{operation_id}'를 찾을 수 없습니다.", "롤백 실패"))
                
                elif len(parts) == 3 and parts[1] != 'cancel':
                    operation_id, action = parts[1], parts[2]
                    if action == 'confirm':
                        try:
                            success = file_editor.rollback_operation(operation_id)
                            if success:
                                console.print(ui.rollback_success(operation_id))
                            else:
                                console.print(ui.error_panel(f"작업 '{operation_id}' 롤백에 실패했습니다.", "롤백 실패"))
                        except Exception as e:
                            console.print(ui.error_panel(f"롤백 중 오류 발생: {e}", "롤백 실패"))
                    else:
                        console.print(ui.error_panel("'/rollback <ID> confirm' 형식으로 입력하세요.", "명령어 오류"))
                
                elif len(parts) == 2 and parts[1] == 'cancel':
                    console.print(ui.success_panel("롤백이 취소되었습니다.", "취소됨"))
                
                else:
                    console.print(ui.error_panel("사용법: /rollback <ID> 또는 /rollback <ID> confirm", "명령어 오류"))
                continue

            elif user_input.strip().lower() == '/ask':
                task = 'ask'
                ui.mode_switch_message(task)
                continue

            elif user_input.strip().lower().startswith('/edit'):
                parts = user_input.strip().split()
                if len(parts) == 1:
                    # 기본 edit 모드
                    task = 'edit'
                    ui.mode_switch_message(task)
                elif len(parts) == 2:
                    # 전략과 함께 edit 모드
                    strategy_name = parts[1].lower()
                    if strategy_name in registry._coders:
                        edit_strategy = strategy_name
                        current_coder = registry.get_coder(edit_strategy, file_editor)
                        task = 'edit'
                        console.print(f"[bold green]✅ '{strategy_name}' 전략으로 edit 모드가 설정되었습니다.[/bold green]")
                        console.print(f"[dim]✏️ 이제 {strategy_name} 방식으로 코드 수정을 요청할 수 있습니다.[/dim]\n")
                    else:
                        available = list(registry._coders.keys())
                        console.print(ui.error_panel(f"알 수 없는 전략: {strategy_name}\n사용 가능: {', '.join(available)}", "전략 오류"))
                else:
                    console.print(ui.error_panel("사용법: /edit 또는 /edit <전략명> (예: /edit udiff)", "명령어 오류"))
                continue

            elif user_input.strip() == "":
                continue

            # "수정해줘" 등 edit 요청 키워드 감지 시 edit 모드로 자동 전환
            elif any(keyword in user_input for keyword in ["수정해줘", "수정해 줘", "바꿔줘", "바꿔 줘", "고쳐줘", "고쳐 줘", "편집해줘", "편집해 줘"]):
                if task != 'edit':
                    task = 'edit'
                    console.print(f"[bold green]✅ '수정해줘' 요청으로 edit 모드로 자동 전환되었습니다.[/bold green]")
                    console.print(f"[dim]✏️ 이제 파일 수정을 요청할 수 있습니다.[/dim]\n")
                
                # edit 모드에서 처리하도록 계속 진행
                ui.separator()
                console.print(ui.user_question_panel(user_input))

            # 잘못된 명령어 처리 (/ 로 시작하지만 알려진 명령어가 아닌 경우)
            elif user_input.startswith('/'):
                known_commands = ['/add', '/files', '/tree', '/analyze', '/info', '/clear', '/preview', '/apply', 
                                '/history', '/debug', '/rollback', '/ask', '/edit', '/session', '/session-reset', '/mcp', '/help', '/exit', '/quit']
                
                # 명령어 부분만 추출 (공백 전까지)
                command_part = user_input.split()[0].lower()
                
                if command_part not in known_commands:
                    console.print(ui.error_panel(
                        f"알 수 없는 명령어: '{command_part}'\n\n"
                        f"사용 가능한 명령어:\n"
                        f"• 파일 관리: /add, /files, /tree, /analyze, /info, /clear\n"
                        f"• 모드 전환: /ask, /edit\n"
                        f"• 편집 기능: /preview, /apply, /history, /rollback, /debug\n"
                        f"• 세션 관리: /session, /session-reset\n"
                        f"• MCP 도구: /mcp, /mcp help <도구명>\n"
                        f"• 기타: /help, /exit\n\n"
                        f"'/help' 명령어로 자세한 도움말을 확인하세요.",
                        "명령어 오류"
                    ))
                    continue

            else:
                # 일반 사용자 입력 - AI에게 전달
                ui.separator()
                console.print(ui.user_question_panel(user_input))

            # Build the prompt using MCP-integrated PromptBuilder
            prompt_builder = mcp_integration.create_prompt_builder(task)
            messages = prompt_builder.build(user_input, file_manager.files, chat_history, file_manager)

            # 입출력 관련 질문인지 확인하고 JSON 강제 모드 사용
            force_json = hasattr(prompt_builder, 'is_io_question') and prompt_builder.is_io_question
            
            # 로딩 메시지
            with ui.loading_spinner():
                llm_response = llm_service.chat_completion(messages, force_json=force_json)

            if llm_response and "choices" in llm_response:
                llm_message = llm_response["choices"][0]["message"]
                response_content = llm_message['content']
                
                # DEBUG: LLM 응답 정보 표시
                console.print(f"[dim]DEBUG: LLM 응답 길이: {len(response_content)}[/dim]")
                console.print(f"[dim]DEBUG: LLM 응답 미리보기: {response_content[:200]}...[/dim]")
                #console.print(f"[dim]DEBUG: JSON 강제 모드: {force_json}[/dim]")
                
                # MCP 도구 호출 처리
                mcp_result = mcp_integration.process_llm_response(response_content, user_input)
                if mcp_result.get('has_tool_calls'):
                    # MCP 도구 호출 시 LLM 응답은 디버그로만 표시
                    console.print(f"[dim]DEBUG: LLM 원본 응답: {response_content[:100]}...[/dim]")
                    
                    # LLM이 자연스럽게 변환한 답변을 AI Response로 표시
                    natural_response = mcp_result.get('natural_response', '응답을 생성할 수 없습니다.')
                    console.print(ui.ai_response_panel(natural_response))
                # MCP 도구 호출이 없는 경우 - 원래 응답 처리 로직 실행
                elif task == 'edit':
                    # Edit 모드: 코드 생성 응답 표시
                    # console.print(ui.edit_mode_response_panel(response_content))
                    
                    # 마지막 edit 응답과 사용자 요청 저장
                    last_edit_response = response_content
                    last_user_request = user_input
                    
                    # 자동으로 미리보기 표시
                    try:
                        preview = current_coder.preview_changes(response_content, file_manager.files)
                        if preview and 'error' not in preview:
                            console.print()
                            panels = ui.file_changes_preview(preview)
                            for panel in panels:
                                console.print(panel)
                            
                            console.print()
                            console.print(ui.info_columns({
                                "다음 단계": "'/apply' - 변경사항 적용\n'/ask' - 질문 모드로 전환"
                            }))
                        elif preview and 'error' in preview:
                            console.print(ui.error_panel(preview['error']['message'], f"미리보기 오류 ({preview['error']['strategy']})"))
                    except Exception as e:
                        console.print(ui.warning_panel(f"미리보기 생성 중 오류: {e}"))
                    
                    # Edit 후 자동으로 파일 분석 수행
                    if preview and 'error' not in preview and preview:
                        console.print("\n[bold blue]🔍 수정된 파일에 대한 자동 분석을 수행합니다...[/bold blue]")
                        try:
                            from cli.core.analyzer import CoeAnalyzer
                            analyzer = CoeAnalyzer()
                            
                            # 수정될 파일들 추출
                            modified_files = list(preview.keys())
                            
                            if modified_files:
                                llm_results = analyzer._perform_llm_analysis(
                                    {f: {'file_type': 'unknown', 'basic_analysis': {}}}
                                     for f in modified_files if f in file_manager.files
                                )
                                
                                # 분석 결과 요약 표시
                                if llm_results:
                                    console.print()
                                    for file_path, llm_analysis in llm_results.items():
                                        if llm_analysis.get('purpose'):
                                            filename = os.path.basename(file_path)
                                            summary_text = f"수정 후 예상 결과: {llm_analysis.get('purpose', 'N/A')}"
                                            
                                            console.print(f"[dim]📊 {filename}: {summary_text}[/dim]")
                        except Exception as e:
                            pass  # 자동 분석 실패는 조용히 넘어감
                else:
                    # Ask 모드: 입출력 분석 결과인지 확인
                    # JSON 응답인지 확인 (force_json이거나 ```json으로 시작)
                    is_json_response = (force_json or 
                                      response_content.strip().startswith('```json'))
                    
                    if is_json_response:
                        # JSON 응답 파싱 및 표시
                        try:
                            import json
                            
                            # 마크다운 코드 블록이 있는지 확인
                            is_markdown_wrapped = response_content.strip().startswith('```')
                            
                            # 마크다운 코드 블록 제거하여 JSON 파싱용 내용 준비
                            clean_content = response_content.strip()
                            if clean_content.startswith('```json'):
                                clean_content = clean_content[7:]  # ```json 제거
                            elif clean_content.startswith('```'):
                                clean_content = clean_content[3:]  # ``` 제거
                            if clean_content.endswith('```'):
                                clean_content = clean_content[:-3]  # 끝의 ``` 제거
                            clean_content = clean_content.strip()
                            
                            console.print(f"[dim]DEBUG: 마크다운 감싸짐: {is_markdown_wrapped}[/dim]")
                            console.print(f"[dim]DEBUG: 정리된 내용 길이: {len(clean_content)}[/dim]")
                            console.print(f"[dim]DEBUG: 정리된 내용 미리보기: {clean_content[:100]}...[/dim]")
                            
                            # JSON 파싱
                            json_data = json.loads(clean_content)
                            
                            
                            # DEBUG: 파싱된 JSON 구조 표시
                            console.print(f"[dim]DEBUG: JSON 파싱 성공, 키들: {list(json_data.keys()) if isinstance(json_data, dict) else 'not dict'}[/dim]")
                            if isinstance(json_data, dict) and json_data.get('analysis_type'):
                                console.print(f"[dim]DEBUG: 분석 타입: {json_data.get('analysis_type')}[/dim]")
                            
                            # JSON 데이터를 표 형태로 표시
                            from rich.table import Table
                            
                            # 입출력 분석인 경우
                            if json_data.get('analysis_type') == 'input_output':
                                
                                # 입력 파라미터 표
                                if json_data.get('inputs'):
                                    input_table = Table(title="📥 입력 파라미터", show_header=True, header_style="bold blue")
                                    input_table.add_column("파라미터명")
                                    input_table.add_column("타입")
                                    input_table.add_column("Nullable")
                                    input_table.add_column("설명")
                                    
                                    for inp in json_data['inputs']:
                                        nullable_text = "O" if inp.get('nullable', False) else "X"
                                        input_table.add_row(
                                            inp.get('name', 'N/A'),
                                            inp.get('type', 'N/A'),
                                            nullable_text,
                                            inp.get('description', 'N/A')
                                        )
                                    console.print(input_table)
                                    console.print()
                                
                                # 출력 값 표
                                if json_data.get('outputs'):
                                    output_table = Table(title="📤 출력 값", show_header=True, header_style="bold green")
                                    output_table.add_column("출력값명")
                                    output_table.add_column("타입")
                                    output_table.add_column("설명")
                                    
                                    for out in json_data['outputs']:
                                        output_table.add_row(
                                            out.get('name', 'N/A'),
                                            out.get('type', 'N/A'),
                                            out.get('description', 'N/A')
                                        )
                                    console.print(output_table)
                                    console.print()
                                
                                # 요약 표시
                                if json_data.get('summary'):
                                    console.print(Panel(json_data['summary'], title="📊 분석 요약", border_style="green"))
                            
                            # 함수 호출관계 분석인 경우
                            elif json_data.get('function_calls'):
                                for main_func, call_info in json_data['function_calls'].items():
                                    if isinstance(call_info, dict) and 'calls' in call_info:
                                        # 함수 호출 목록 표
                                        call_table = Table(title=f"🔗 {main_func} 함수 호출 관계", show_header=True, header_style="bold blue")
                                        call_table.add_column("순서")
                                        call_table.add_column("호출 함수명")
                                        call_table.add_column("설명")
                                        
                                        for i, func_call in enumerate(call_info['calls'], 1):
                                            if isinstance(func_call, dict):
                                                call_table.add_row(
                                                    str(i),
                                                    func_call.get('name', 'N/A'),
                                                    func_call.get('description', 'N/A')
                                                )
                                            else:
                                                # 문자열인 경우
                                                call_table.add_row(str(i), str(func_call), "")
                                        
                                        console.print(call_table)
                                        console.print()
                            
                            # 기타 JSON 구조인 경우 간단한 키-값 표시
                            else:
                                # 일반적인 JSON 구조를 표로 표시
                                if isinstance(json_data, dict):
                                    for key, value in json_data.items():
                                        if isinstance(value, (dict, list)):
                                            console.print(f"[bold]{key}:[/bold]")
                                            if isinstance(value, list) and len(value) > 0:
                                                # 리스트 항목들을 표로 표시
                                                if isinstance(value[0], dict):
                                                    # 딕셔너리 리스트인 경우
                                                    table = Table(title=f"📋 {key}", show_header=True, header_style="bold green")
                                                    # 첫 번째 항목의 키들을 컬럼으로 사용
                                                    first_item = value[0]
                                                    for col_key in first_item.keys():
                                                        table.add_column(str(col_key))
                                                    
                                                    for item in value:
                                                        if isinstance(item, dict):
                                                            row_values = [str(item.get(col_key, 'N/A')) for col_key in first_item.keys()]
                                                            table.add_row(*row_values)
                                                    
                                                    console.print(table)
                                                    console.print()
                                                else:
                                                    # 단순 리스트인 경우
                                                    for item in value:
                                                        console.print(f"  • {item}")
                                                    console.print()
                                            elif isinstance(value, dict):
                                                # 딕셔너리인 경우
                                                for sub_key, sub_value in value.items():
                                                    console.print(f"  [cyan]{sub_key}:[/cyan] {sub_value}")
                                                console.print()
                                        else:
                                            console.print(f"[cyan]{key}:[/cyan] {value}")
                                    console.print()
                            
                        except json.JSONDecodeError as e:
                            # JSON 파싱 실패시 일반 응답으로 표시
                            console.print(f"[dim]DEBUG: JSON 파싱 실패: {e}[/dim]")
                            console.print(f"[dim]DEBUG: 원본 응답을 일반 텍스트로 표시[/dim]")
                            console.print(ui.ai_response_panel(response_content))
                    else:
                        # 일반 응답 표시
                        console.print(ui.ai_response_panel(response_content))


                # Add user input and LLM response to history
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": response_content})
            else:
                console.print(ui.err/or_panel("AI가 응답을 생성하지 못했습니다."))
            
            console.print()  # 빈 줄 추가

        except KeyboardInterrupt:
            console.print(ui.warning_panel("작업이 중단되었습니다."))
            continue
        except EOFError:
            console.print(ui.goodbye_panel())
            break
        except ValueError as e:
            console.print(ui.error_panel(str(e), "입력 오류"))
            continue


if __name__ == '__main__':
    main()
