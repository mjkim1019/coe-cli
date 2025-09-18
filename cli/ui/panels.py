"""
UI Panels module - All panel-related UI logic extracted from main.py
"""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Dict, List, Any, Optional
import os


class UIPanels:
    """Handles various UI panels for different purposes"""
    
    def __init__(self, console: Console):
        self.console = console

    def create_user_question_panel(self, question: str):
        """사용자 질문 패널"""
        return Panel(
            question,
            title="• Your Question",
            title_align="left",
            style="bright_cyan",
            border_style="cyan"
        )

    def create_ai_response_panel(self, response: str):
        """AI 응답 패널"""
        return Panel(
            Markdown(response),
            title="• AI Response",
            title_align="left",
            style="white",
            border_style="green"
        )

    def create_edit_mode_response_panel(self, response: str):
        """Edit 모드 AI 응답 패널 (파일 수정 내용 포함)"""
        return Panel(
            Markdown(response),
            title="• AI가 생성한 코드",
            title_align="left",
            style="bright_white",
            border_style="blue"
        )

    def create_file_added_panel(self, message: str):
        """파일 추가 완료 패널"""
        return Panel(
            f"{message}",
            title="• 파일 추가 완료",
            style="white"
        )

    def create_error_panel(self, error_message: str, title: str = "오류"):
        """에러 패널"""
        return Panel(
            f"[red]• {error_message}[/red]",
            title=f"• {title}",
            style="red"
        )

    def create_success_panel(self, message: str, title: str = "완료"):
        """성공 패널"""
        return Panel(
            f"[green]• {message}[/green]",
            title=f"• {title}",
            style="green"
        )

    def create_info_panel(self, message: str, title: str = "정보"):
        """정보 패널"""
        return Panel(
            f"[blue]• {message}[/blue]",
            title=f"• {title}",
            style="blue"
        )

    def create_warning_panel(self, message: str):
        """경고 패널"""
        return Panel(
            f"[yellow]• {message}[/yellow]",
            title="• 경고",
            style="yellow"
        )

    def create_goodbye_panel(self):
        """종료 메시지"""
        return Panel(
            "[bright_red]• 안녕히 가세요![/bright_red]",
            style="red",
            title="• 종료",
            expand=False
        )

    def create_analysis_summary_panel(self, file_path: str, llm_analysis: Dict[str, Any]):
        """LLM 분석 결과 요약 패널"""
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
        
        llm_content = f"**• 목적**: \n{purpose_formatted.strip()}\n\n"
        
        if 'suggestions' in llm_analysis and llm_analysis['suggestions']:
            llm_content += f"**• 개선사항**: {llm_analysis['suggestions']}\n"
        
        return Panel(
            Markdown(llm_content.strip()),
            title=f"• {filename} LLM 분석",
            border_style="bright_white"
        )

    def create_simple_analysis_panel(self, file_path: str, content: str):
        """간단한 분석 결과 패널"""
        filename = os.path.basename(file_path)
        
        return Panel(
            Markdown(content),
            title=f"• {filename} AI 분석",
            border_style="bright_yellow"
        )

    def create_fallback_analysis_panel(self, file_path: str, purpose_text: str):
        """파싱 실패 시 fallback 분석 패널"""
        import re
        
        filename = os.path.basename(file_path)
        
        # 의미 단위로 줄바꿈 처리
        purpose_formatted = re.sub(r'(\.)', r'\1\n', purpose_text)
        purpose_formatted = re.sub(r'( - )', r'\n\1', purpose_formatted)
        purpose_formatted = re.sub(r'(입니다\. )', r'\1\n', purpose_formatted)
        purpose_formatted = re.sub(r'(습니다\. )', r'\1\n', purpose_formatted)
        
        return Panel(
            Markdown(f"**• 목적**: \n{purpose_formatted.strip()}\n\n*JSON 파싱은 실패했지만 분석 결과를 추출했습니다.*"),
            title=f"• {filename} LLM 분석 (부분)",
            border_style="dim white"
        )

    def create_directory_analysis_panel(self, analysis: Dict):
        """디렉토리 분석 결과를 패널로 표시"""
        if 'error' in analysis:
            return self.create_error_panel(analysis['error'], "디렉토리 분석 오류")
        
        content = []
        
        # 기본 정보
        path = analysis.get('path', 'Unknown')
        total_files = analysis.get('total_files', 0)
        content.append(f"[bright_white]• Path:[/bright_white] {path}")
        content.append(f"[bright_white]• Total Files:[/bright_white] {total_files}")
        
        # 프로젝트 인사이트
        insights = analysis.get('project_insights', {})
        if insights:
            content.append("\n[bright_white]• Project Analysis:[/bright_white]")
            content.append(f"  [white]• Type:[/white] {insights.get('project_type', 'unknown')}")
            content.append(f"  [white]• Complexity:[/white] {insights.get('complexity', 'unknown')}")
            
            characteristics = insights.get('characteristics', [])
            if characteristics:
                content.append(f"  [white]• Characteristics:[/white] {', '.join(characteristics)}")
            
            tech_stack = insights.get('tech_stack', [])
            if tech_stack:
                content.append(f"  [white]• Tech Stack:[/white] {', '.join(tech_stack)}")
        
        # 파일 카테고리별 통계
        file_categories = analysis.get('file_categories', {})
        if file_categories:
            content.append("\n[bright_white]• File Categories:[/bright_white]")
            for category, files in file_categories.items():
                if files:
                    count = len(files)
                    category_display = category.replace('_', ' ').title()
                    content.append(f"  [white]• {category_display}:[/white] {count} files")
                    
                    # 주요 파일들 일부 표시
                    if category in ['c_files', 'header_files', 'sql_files'] and count > 0:
                        sample_files = files[:3]  # 처음 3개만
                        for file_info in sample_files:
                            file_name = os.path.basename(file_info['path'])
                            content.append(f"    [dim white]• {file_name}[/dim white]")
                        if count > 3:
                            content.append(f"    [dim white]• ... and {count - 3} more[/dim white]")
        
        # 추천 파일들
        suggested_files = analysis.get('suggested_files', [])
        if suggested_files:
            content.append("\n[bright_white]• Recommended Context Files:[/bright_white]")
            for suggestion in suggested_files[:5]:  # 상위 5개만
                file_name = os.path.basename(suggestion['file'])
                reason = suggestion.get('reason', '')
                priority = suggestion.get('priority', 'medium')
                
                # 중요도에 따른 색상 조절 (하얀색 계열)
                if priority == 'high':
                    priority_color = "bright_white"
                elif priority == 'medium':
                    priority_color = "white"
                else:  # low
                    priority_color = "dim white"
                    
                content.append(f"  [{priority_color}]• {file_name}[/{priority_color}] - [dim white]{reason}[/dim white]")
        
        return Panel(
            "\n".join(content),
            title="• Directory Analysis",
            title_align="left",
            style="white",
            border_style="cyan"
        )

    def create_llm_result_panel(self, file_path: str, llm_analysis: Dict[str, Any]) -> Optional[Panel]:
        """LLM 분석 결과를 적절한 패널로 변환"""
        filename = os.path.basename(file_path)

        # 표시 조건 및 내용 결정
        should_display = False
        display_content = ""

        if llm_analysis.get('purpose') and llm_analysis.get('purpose') != 'LLM 분석 결과 파싱 실패':
            # JSON 파싱 성공한 경우 - purpose 필드 기반 표시
            purpose_text = llm_analysis.get('purpose', 'N/A')
            # 의미 단위로 줄바꿈 처리 (문장부호와 접속사 기준)
            import re
            purpose_formatted = re.sub(r'(\.)', r'\1\n', purpose_text)  # 문장 끝에서 줄바꿈
            purpose_formatted = re.sub(r'( - )', r'\n\1', purpose_formatted)  # 대시 앞에서 줄바꿈
            purpose_formatted = re.sub(r'(입니다\. )', r'\1\n', purpose_formatted)  # '입니다.' 뒤에 줄바꿈
            purpose_formatted = re.sub(r'(습니다\. )', r'\1\n', purpose_formatted)  # '습니다.' 뒤에 줄바꿈

            display_content = f"**목적**: \n{purpose_formatted.strip()}\n\n"
            should_display = True

        elif llm_analysis.get('raw_response'):
            # JSON 파싱 실패했지만 raw_response가 있는 경우 - raw response 내용을 직접 표시
            raw_response = llm_analysis.get('raw_response', '')
            if len(raw_response.strip()) > 10:  # 의미있는 내용이 있는 경우만
                display_content = f"**AI 분석 결과**: \n{raw_response.strip()}\n\n"
                should_display = True

        elif isinstance(llm_analysis, dict) and len(llm_analysis) > 0:
            # purpose나 raw_response가 없지만 다른 구조화된 데이터가 있는 경우 (예: graph 구조)
            # JSON 전체 내용을 문자열로 변환하여 표시
            import json
            try:
                formatted_json = json.dumps(llm_analysis, ensure_ascii=False, indent=2)
                display_content = f"**AI 분석 결과**: \n```json\n{formatted_json}\n```\n\n"
                should_display = True
            except Exception:
                # JSON 직렬화 실패시 기본 문자열 표시
                display_content = f"**AI 분석 결과**: \n{str(llm_analysis)}\n\n"
                should_display = True

        if not should_display:
            return None

        # Input/Output 분석 결과가 있으면 테이블로 표시 준비
        has_io_analysis = 'input_output_analysis' in llm_analysis and llm_analysis['input_output_analysis']

        if has_io_analysis:
            # suggestions 추가
            if 'suggestions' in llm_analysis and llm_analysis['suggestions']:
                display_content += f"**개선사항**: {llm_analysis['suggestions']}\n"

            # 분석 요약 패널 반환 (IO 테이블은 별도로 처리됨)
            return self.create_analysis_summary_panel(file_path, llm_analysis)
        else:
            # IO 분석이 없는 경우 간단한 패널로 표시
            return self.create_simple_analysis_panel(file_path, display_content)

    def create_repo_map_panel(self, repo_map: str):
        """RepoMap 표시 패널"""
        # 레포맵이 너무 길면 축약
        if len(repo_map) > 2000:
            preview = repo_map[:2000] + "\n\n[... truncated for display ...]"
        else:
            preview = repo_map

        return Panel(
            preview,
            title="•  Repository Structure Map",
            title_align="left",
            border_style="cyan",
            padding=(1, 2)
        )