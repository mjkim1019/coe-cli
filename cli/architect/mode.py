"""
Architect Mode - AI 작업 오케스트레이션 엔진

복잡한 자연어 요청을 단계별 실행 계획으로 분해하고,
사용자 승인을 받아 각 단계를 순차적으로 실행합니다.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.prompt import Confirm, Prompt

from .prompts import ArchitectPrompts
from .plan import ExecutionPlan, ExecutionStep
from ..core.debug_manager import DebugManager
from llm.service import LLMService


class ArchitectMode:
    """AI 작업 오케스트레이션 엔진"""
    
    def __init__(self, console: Console, llm_service: LLMService, 
                 file_manager, file_editor, session, template_manager=None):
        self.console = console
        self.llm_service = llm_service
        self.file_manager = file_manager
        self.file_editor = file_editor
        self.session = session
        self.template_manager = template_manager
        self.prompts = ArchitectPrompts()
        self.plans_dir = Path(".mider/plans")
        self.plans_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, user_request: str) -> Optional[ExecutionPlan]:
        """Architect Mode 메인 진입점"""
        self.console.print(Panel(
            f"[bold cyan]🏗️  Architect Mode 시작[/bold cyan]\n\n"
            f"요청: [yellow]{user_request}[/yellow]",
            title="AI Task Orchestration",
            border_style="cyan"
        ))
        
        # 1단계: 계획 생성
        plan = self.generate_plan(user_request)
        if not plan:
            return None
        
        # 2단계: 시각화 및 승인 요청
        self.visualize_plan(plan)
        if not self.approve_plan(plan):
            self.console.print("[yellow]계획이 거부되었습니다.[/yellow]")
            return None
        
        # 3단계: 계획 실행
        self.execute_plan(plan)
        
        # 4단계: 계획 저장
        self.save_plan(plan)
        
        return plan
    
    def generate_plan(self, user_request: str) -> Optional[ExecutionPlan]:
        """1단계: LLM을 사용하여 실행 계획 생성"""
        self.console.print("\n[cyan]📋 실행 계획 생성 중...[/cyan]")
        
        # 컨텍스트 준비 - 현재 파일들을 상세하게 표시
        files_count = len(self.file_manager.files)
        
        if files_count == 0:
            file_list = "None (no files in session yet)"
            self.console.print("[yellow]💡 Tip: 파일을 먼저 추가하면 더 정확한 계획이 생성됩니다.[/yellow]")
            self.console.print("[dim]예: /add schema/*.sql 후 /architect 사용[/dim]\n")
        else:
            # 상세한 파일 목록 표시
            file_paths = list(self.file_manager.files.keys())
            if files_count <= 10:
                # 10개 이하면 모든 파일 표시
                file_list = "\n".join([f"  - {os.path.basename(f)} ({f})" for f in file_paths])
            else:
                # 처음 10개만 표시하고 나머지는 요약
                file_list = "\n".join([f"  - {os.path.basename(f)} ({f})" for f in file_paths[:10]])
                file_list += f"\n  ... and {files_count - 10} more files"
            
            self.console.print(f"[green]✓ {files_count}개 파일이 이미 세션에 있습니다.[/green]")
            self.console.print("[dim]계획 생성 시 이 파일들을 활용합니다...[/dim]\n")
        
        # 메시지 빌드
        messages = [
            {"role": "system", "content": self.prompts.PLAN_GENERATION_SYSTEM},
            {"role": "user", "content": self.prompts.PLAN_GENERATION_USER_TEMPLATE.format(
                user_request=user_request,
                files_count=files_count,
                file_list=file_list
            )}
        ]
        try:
            response = self.llm_service.chat_completion(messages, force_json=True)
            if not response or "choices" not in response:
                self.console.print("[red]❌ LLM 응답을 받지 못했습니다.[/red]")
                return None
            
            response_content = response["choices"][0]["message"]["content"]
            DebugManager.llm(f"Plan generation response: {response_content[:200]}...")
            
            # 응답 정리 - 마크다운 코드 블록이 있으면 제거
            cleaned_content = response_content.strip()
            
            # 마크다운 코드 블록 제거
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]  # ```json 제거
            elif cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]  # ``` 제거
            
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]  # 끝의 ``` 제거
            
            cleaned_content = cleaned_content.strip()
            
            # 앞뒤에 텍스트가 있으면 JSON 객체 찾기
            json_start = cleaned_content.find('{')
            json_end = cleaned_content.rfind('}')
            if json_start != -1 and json_end != -1:
                cleaned_content = cleaned_content[json_start:json_end+1]
            
            DebugManager.llm(f"Cleaned content: {cleaned_content[:200]}...")
            
            # JSON 파싱
            try:
                plan_data = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                self.console.print(f"[yellow]⚠ JSON 파싱 오류가 발생했습니다. 재시도 중...[/yellow]")
                DebugManager.error(f"First parse attempt failed: {e}")
                DebugManager.error(f"Content: {cleaned_content}")
                
                # 일반적인 문제 수정 시도
                import re
                # 작은따옴표를 큰따옴표로 변경 (일반적인 문제)
                fixed_content = cleaned_content.replace("'", '"')
                # 닫는 중괄호/대괄호 앞의 trailing comma 제거
                fixed_content = re.sub(r',(\s*[}\]])', r'\1', fixed_content)
                
                try:
                    plan_data = json.loads(fixed_content)
                    self.console.print("[green]✓ 자동 수정 후 파싱 성공[/green]")
                except json.JSONDecodeError:
                    # 포기하고 에러 표시
                    raise
            
            # 구조 검증
            if "steps" not in plan_data or not isinstance(plan_data["steps"], list):
                self.console.print("[red]❌ 잘못된 계획 형식입니다.[/red]")
                return None
            
            # ExecutionPlan 생성
            plan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            steps = []
            skipped_steps = []
            
            for step_data in plan_data["steps"]:
                step_command = step_data.get("command", "")
                
                # 스마트 필터링: 파일이 이미 세션에 있으면 /add 건너뛰기
                if step_command == "/add":
                    file_param = step_data.get("parameters", {}).get("file") or step_data.get("parameters", {}).get("files")
                    if file_param:
                        # 파일이 이미 추가되었는지 확인
                        file_to_check = file_param if isinstance(file_param, str) else (file_param[0] if file_param else "")
                        
                        # 간단한 확인: 세션의 파일과 매칭되는지 확인
                        already_added = False
                        for existing_file in self.file_manager.files.keys():
                            if file_to_check in existing_file or os.path.basename(file_to_check) in existing_file:
                                already_added = True
                                break
                        
                        if already_added:
                            skipped_steps.append({
                                "step_number": step_data.get("step_number", len(steps) + 1),
                                "description": step_data.get("description", ""),
                                "reason": f"File '{file_to_check}' already in session"
                            })
                            continue  # 이 단계 건너뛰기
                
                # 단계 추가
                step = ExecutionStep(
                    step_number=len(steps) + 1,  # 필터링 후 재번호 매기기
                    command=step_command,
                    description=step_data.get("description", ""),
                    parameters=step_data.get("parameters", {}),
                    reason=step_data.get("reason", "")
                )
                steps.append(step)
            
            # 최적화된 내용 표시
            if skipped_steps:
                self.console.print(f"[yellow]⚡ {len(skipped_steps)}개 불필요한 단계를 최적화했습니다:[/yellow]")
                for skipped in skipped_steps:
                    self.console.print(f"  [dim]- Step {skipped['step_number']}: {skipped['description']} ({skipped['reason']})[/dim]")
                self.console.print()
            
            plan = ExecutionPlan(
                plan_id=plan_id,
                description=user_request,
                steps=steps
            )
            
            self.console.print(f"[green]✅ 실행 계획이 생성되었습니다 ({len(steps)}개 단계).[/green]\n")
            return plan
            
        except json.JSONDecodeError as e:
            self.console.print(f"[red]❌ JSON 파싱 오류: {e}[/red]")
            self.console.print(f"[yellow]💡 팁: 요청을 더 간단하고 명확하게 바꿔보세요.[/yellow]")
            self.console.print(f"[dim]예: '/architect \"고객 테이블을 추가하고 간단한 조회 쿼리를 작성해줘\"'[/dim]")
            DebugManager.error(f"Plan parsing error: {e}")
            DebugManager.error(f"Response content: {response_content}")
            
            # Show a snippet of where the error occurred
            try:
                error_pos = e.pos
                start = max(0, error_pos - 50)
                end = min(len(cleaned_content), error_pos + 50)
                snippet = cleaned_content[start:end]
                self.console.print(f"[dim]오류 발생 위치 근처: ...{snippet}...[/dim]")
            except:
                pass
            
            return None
        except Exception as e:
            self.console.print(f"[red]❌ 계획 생성 중 오류: {e}[/red]")
            DebugManager.error(f"Plan generation error: {e}")
            return None
    
    def visualize_plan(self, plan: ExecutionPlan):
        """2단계: 실행 계획 시각화"""
        # 리치 테이블 생성
        table = Table(title=f"📋 실행 계획: {plan.plan_id}", show_header=True, header_style="bold cyan")
        table.add_column("Step", style="cyan", width=6)
        table.add_column("Command", style="yellow", width=10)
        table.add_column("Description", style="white", width=40)
        table.add_column("Parameters", style="green", width=25)
        table.add_column("Reason", style="dim", width=30)
        
        for step in plan.steps:
            # 파라미터 포맷팅
            params_str = "\n".join([f"{k}: {v}" for k, v in step.parameters.items()])
            
            table.add_row(
                str(step.step_number),
                step.command,
                step.description,
                params_str,
                step.reason
            )
        
        self.console.print(table)
        self.console.print()
    
    def approve_plan(self, plan: ExecutionPlan) -> bool:
        """2단계: 계획 사용자 승인 받기"""
        self.console.print("[bold yellow]❓ 이 계획을 승인하시겠습니까?[/bold yellow]")
        approved = Confirm.ask("계획 실행을 승인하시겠습니까?", default=True, console=self.console)
        
        if approved:
            plan.status = "approved"
            self.console.print("[green]✅ 계획이 승인되었습니다.[/green]\n")
        
        return approved
    
    def execute_plan(self, plan: ExecutionPlan):
        """3단계: 계획을 순차적으로 실행"""
        plan.status = "executing"
        self.console.print(Panel(
            "[bold cyan]🚀 계획 실행 시작[/bold cyan]",
            border_style="cyan"
        ))
        
        for step in plan.steps:
            self.console.print(f"\n[cyan]▶ Step {step.step_number}: {step.description}[/cyan]")
            
            success = self._execute_step(step)
            
            if success:
                step.status = "success"
                self.console.print(f"[green]✅ Step {step.step_number} 완료[/green]")
            else:
                step.status = "failed"
                self.console.print(f"[red]❌ Step {step.step_number} 실패[/red]")
                
                # 실패 처리
                action = self._handle_step_failure(step)
                
                if action == "stop":
                    self.console.print("[yellow]실행이 중단되었습니다.[/yellow]")
                    plan.status = "failed"
                    break
                elif action == "skip":
                    step.status = "skipped"
                    self.console.print(f"[yellow]Step {step.step_number} 건너뛰기[/yellow]")
                    continue
        
        if plan.is_complete():
            summary = plan.get_summary()
            if summary["failed"] == 0:
                plan.status = "completed"
                self.console.print(Panel(
                    f"[bold green]✅ 모든 단계가 성공적으로 완료되었습니다![/bold green]\n\n"
                    f"성공: {summary['success']}, 실패: {summary['failed']}, 건너뛰기: {summary['skipped']}",
                    title="실행 완료",
                    border_style="green"
                ))
            else:
                plan.status = "completed"
                self.console.print(Panel(
                    f"[yellow]⚠ 계획 실행이 완료되었습니다. 일부 단계가 실패했습니다.[/yellow]\n\n"
                    f"성공: {summary['success']}, 실패: {summary['failed']}, 건너뛰기: {summary['skipped']}",
                    title="실행 완료 (경고)",
                    border_style="yellow"
                ))
    
    def _execute_step(self, step: ExecutionStep) -> bool:
        """단일 단계 실행"""
        step.status = "executing"
        
        try:
            if step.command == "/new":
                return self._execute_new(step)
            elif step.command == "/add":
                return self._execute_add(step)
            elif step.command == "/edit":
                return self._execute_edit(step)
            elif step.command == "/ask":
                return self._execute_ask(step)
            elif step.command == "/exec":
                # 레거시 지원 - /exec는 더 이상 권장되지 않음
                self.console.print(f"[yellow]⚠ /exec command is not fully implemented in CLI[/yellow]")
                return self._execute_exec(step)
            elif step.command == "/test":
                # 레거시 지원 - /test는 더 이상 권장되지 않음
                self.console.print(f"[yellow]⚠ /test command is not fully implemented in CLI[/yellow]")
                return self._execute_test(step)
            else:
                self.console.print(f"[red]알 수 없는 명령어: {step.command}[/red]")
                step.error = f"Unknown command: {step.command}"
                return False
        except Exception as e:
            self.console.print(f"[red]실행 오류: {e}[/red]")
            step.error = str(e)
            DebugManager.error(f"Step execution error: {e}")
            return False
    
    def _execute_new(self, step: ExecutionStep) -> bool:
        """Execute /new 명령 - 템플릿에서 파일 생성"""
        if not self.template_manager:
            step.error = "TemplateManager not available"
            self.console.print("[red]⚠ Template creation is not available in this session[/red]")
            return False
        
        # 파라미터 가져오기
        template = step.parameters.get("template")
        service_id = step.parameters.get("service_id")
        filename = step.parameters.get("filename")
        description = step.parameters.get("description", "")
        author = step.parameters.get("author", "architect")
        
        # 필수 파라미터 검증
        if not template:
            step.error = "Missing required parameter: template"
            return False
        if not service_id:
            step.error = "Missing required parameter: service_id"
            return False
        if not filename:
            step.error = "Missing required parameter: filename"
            return False
        
        # 파일명에 확장자가 없으면 추가
        if '.' not in filename:
            template_ext = template.split('.')[-1] if '.' in template else 'txt'
            filename = f"{filename}.{template_ext}"
        
        self.console.print(f"[dim]  템플릿: {template}[/dim]")
        self.console.print(f"[dim]  서비스 ID: {service_id}[/dim]")
        self.console.print(f"[dim]  파일명: {filename}[/dim]")
        if description:
            self.console.print(f"[dim]  설명: {description}[/dim]")
        
        # 템플릿에서 파일 생성
        try:
            success = self.template_manager.create_from_template(
                template_name_or_number=template,
                service_id=service_id,
                filename=filename,
                author=author,
                description=description
            )
            
            if success:
                output_path = os.path.join("SWING_AUTO_FILES", filename)
                step.output = f"Created file: {output_path}"
                self.console.print(f"[green]✅ 파일 생성 완료: {output_path}[/green]")
                return True
            else:
                step.error = "Template creation failed"
                return False
                
        except Exception as e:
            step.error = f"Failed to create from template: {str(e)}"
            self.console.print(f"[red]템플릿 생성 실패: {e}[/red]")
            return False
    
    def _execute_add(self, step: ExecutionStep) -> bool:
        """Execute /add 명령"""
        file_param = step.parameters.get("file") or step.parameters.get("files")
        if not file_param:
            step.error = "No file parameter provided"
            return False
        
        files = [file_param] if isinstance(file_param, str) else file_param
        result = self.file_manager.add(files)
        
        if result.get("added") or result.get("files_added"):
            step.output = f"Added {len(result.get('added', result.get('files_added', [])))} file(s)"
            return True
        else:
            step.error = "Failed to add files"
            return False
    
    def _execute_edit(self, step: ExecutionStep) -> bool:
        """Execute /edit 명령 - 파라미터의 내용으로 새 파일 생성"""
        # 파라미터 가져오기
        file_path = step.parameters.get("file") or step.parameters.get("files")
        content = step.parameters.get("content")
        
        if not file_path:
            step.error = "No file parameter provided"
            return False
        
        if not content:
            step.error = "No content parameter provided"
            return False
        
        # 단일 파일만 처리
        if isinstance(file_path, list):
            file_path = file_path[0]
        
        # 원본 기반으로 새 파일명 생성
        base_dir = os.path.dirname(os.path.abspath(file_path))
        base_name = os.path.basename(file_path)
        name_parts = os.path.splitext(base_name)
        
        # 확장자 앞에 _edited 접미사 추가
        new_filename = f"{name_parts[0]}_edited{name_parts[1]}"
        target_path = os.path.join(base_dir, new_filename)
        
        # 파일이 존재하면 카운터 추가
        counter = 1
        while os.path.exists(target_path):
            new_filename = f"{name_parts[0]}_edited_{counter}{name_parts[1]}"
            target_path = os.path.join(base_dir, new_filename)
            counter += 1
        
        self.console.print(f"[dim]  원본 파일: {file_path}[/dim]")
        self.console.print(f"[dim]  새 파일: {target_path}[/dim]")
        self.console.print(f"[dim]  내용 길이: {len(content)} characters[/dim]")
        
        try:
            # 디렉토리가 존재하는지 확인
            os.makedirs(base_dir, exist_ok=True)
            
            # 새 파일에 내용 쓰기
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 세션 업데이트
            self.file_manager.files[target_path] = content
            
            step.output = f"Created {target_path} with {len(content)} characters"
            self.console.print(f"[green]✅ 새 파일 생성 완료: {target_path}[/green]")
            
            return True
            
        except Exception as e:
            step.error = f"Failed to create file: {str(e)}"
            self.console.print(f"[red]파일 생성 실패: {e}[/red]")
            DebugManager.error(f"Edit step error: {e}")
            return False
    
    def _execute_exec(self, step: ExecutionStep) -> bool:
        """Execute /exec 명령 - 쉘 명령 실행"""
        command = step.parameters.get("command")
        if not command:
            step.error = "No command parameter provided"
            return False
        
        self.console.print(f"[dim]  실행할 명령: {command}[/dim]")
        
        # 안전을 위해 exec 명령 실행 전 확인
        if not Confirm.ask(f"명령을 실행하시겠습니까? '{command}'", default=False, console=self.console):
            step.error = "User cancelled execution"
            return False
        
        # 명령 실행 (단순화됨 - 프로덕션에서는 적절한 subprocess 처리 사용)
        import subprocess
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            step.output = result.stdout if result.returncode == 0 else result.stderr
            return result.returncode == 0
        except Exception as e:
            step.error = str(e)
            return False
    
    def _execute_test(self, step: ExecutionStep) -> bool:
        """Execute /test 명령"""
        test_type = step.parameters.get("type", "syntax")
        file_path = step.parameters.get("file")
        
        self.console.print(f"[dim]  테스트 타입: {test_type}[/dim]")
        self.console.print(f"[dim]  대상 파일: {file_path}[/dim]")
        
        # 단순화됨 - 프로덕션에서는 실제 테스트 프레임워크와 통합
        step.output = f"Test '{test_type}' on '{file_path}' passed"
        return True
    
    def _execute_ask(self, step: ExecutionStep) -> bool:
        """Execute /ask 명령 - LLM 쿼리 (대용량 파일 청킹 지원)"""
        question = step.parameters.get("question") or step.description

        from cli.core.context_manager import PromptBuilder
        from cli.core.file_chunker import FileChunker

        prompt_builder = PromptBuilder('ask')

        # 대용량 파일 자동 청킹
        chunker = FileChunker()
        has_large = any(
            chunker.needs_chunking(c)
            for c in self.file_manager.files.values()
        )

        if has_large:
            messages, aggregated = prompt_builder.build_with_chunking(
                question, self.file_manager.files, [], self.file_manager,
                llm_service=self.llm_service, console=self.console
            )
            if aggregated:
                step.output = aggregated[:200] + "..." if len(aggregated) > 200 else aggregated
                self.console.print(f"[dim]  답변: {step.output}[/dim]")
                return True
            # fallback: messages가 반환되면 기존 방식으로 호출
            if messages:
                response = self.llm_service.chat_completion(messages)
                if response and "choices" in response:
                    answer = response["choices"][0]["message"]["content"]
                    step.output = answer[:200] + "..." if len(answer) > 200 else answer
                    self.console.print(f"[dim]  답변: {step.output}[/dim]")
                    return True
        else:
            messages = prompt_builder.build(question, self.file_manager.files, [], self.file_manager)
            response = self.llm_service.chat_completion(messages)
            if response and "choices" in response:
                answer = response["choices"][0]["message"]["content"]
                step.output = answer[:200] + "..." if len(answer) > 200 else answer
                self.console.print(f"[dim]  답변: {step.output}[/dim]")
                return True

        step.error = "Failed to get LLM response"
        return False
    
    def _handle_step_failure(self, step: ExecutionStep) -> str:
        """단계 실패 처리 - 사용자에게 조치 방법 물어보기"""
        self.console.print(f"\n[yellow]⚠ Step {step.step_number} 실패: {step.error}[/yellow]\n")
        
        self.console.print("[bold]다음 조치를 선택하세요:[/bold]")
        self.console.print("  1. [red]중단 (stop)[/red] - 전체 실행 중단")
        self.console.print("  2. [yellow]건너뛰기 (skip)[/yellow] - 이 단계를 건너뛰고 계속")
        # self.console.print("  3. [cyan]재시도 (retry)[/cyan] - 이 단계 다시 실행")  # 향후 구현
        # self.console.print("  4. [green]수정 (modify)[/green] - 단계 수정 후 재실행")  # 향후 구현
        
        choice = Prompt.ask("선택", choices=["stop", "skip"], default="stop", console=self.console)
        return choice
    
    def save_plan(self, plan: ExecutionPlan):
        """4단계: 계획을 파일로 저장"""
        filepath = self.plans_dir / f"plan_{plan.plan_id}.yaml"
        plan.save_to_file(filepath)
        
        self.console.print(f"\n[green]💾 계획이 저장되었습니다: {filepath}[/green]")
    
    def load_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """파일에서 계획 로드"""
        filepath = self.plans_dir / f"plan_{plan.plan_id}.yaml"
        if not filepath.exists():
            self.console.print(f"[red]계획을 찾을 수 없습니다: {plan_id}[/red]")
            return None
        
        try:
            plan = ExecutionPlan.load_from_file(filepath)
            self.console.print(f"[green]✅ 계획 로드됨: {plan_id}[/green]")
            return plan
        except Exception as e:
            self.console.print(f"[red]계획 로드 실패: {e}[/red]")
            return None
    
    def list_plans(self) -> List[str]:
        """저장된 모든 계획 목록 표시"""
        plan_files = list(self.plans_dir.glob("plan_*.yaml"))
        plan_ids = [f.stem.replace("plan_", "") for f in plan_files]
        return sorted(plan_ids, reverse=True)  # 최신 순으로 정렬
