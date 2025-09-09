"""
Response Formatters module - Handles JSON and complex response formatting
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Dict, List, Any, Optional
import json


class ResponseFormatter:
    """Handles formatting of AI responses, especially JSON responses"""
    
    def __init__(self, console: Console):
        self.console = console

    def format_json_response(self, response_content: str, force_json: bool = False):
        """JSON 응답 포맷팅"""
        is_json_response = (force_json or response_content.strip().startswith('```json'))
        
        if not is_json_response:
            return None
            
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
            
            self.console.print(f"[dim white]• 마크다운 감싸짐: {is_markdown_wrapped}[/dim white]")
            self.console.print(f"[dim white]• 정리된 내용 길이: {len(clean_content)}[/dim white]")
            self.console.print(f"[dim white]• 정리된 내용 미리보기: {clean_content[:100]}...[/dim white]")
            
            # JSON 파싱
            json_data = json.loads(clean_content)
            
            # DEBUG: 파싱된 JSON 구조 표시
            self.console.print(f"[dim white]• JSON 파싱 성공, 키들: {list(json_data.keys()) if isinstance(json_data, dict) else 'not dict'}[/dim white]")
            if isinstance(json_data, dict) and json_data.get('analysis_type'):
                self.console.print(f"[dim white]• 분석 타입: {json_data.get('analysis_type')}[/dim white]")
            
            # JSON 데이터를 표 형태로 표시
            return self._format_json_tables(json_data)
            
        except json.JSONDecodeError as e:
            # JSON 파싱 실패시 None 반환 (일반 응답으로 표시)
            self.console.print(f"[dim white]• JSON 파싱 실패: {e}[/dim white]")
            self.console.print(f"[dim white]• 원본 응답을 일반 텍스트로 표시[/dim white]")
            return None

    def _format_json_tables(self, json_data: Dict) -> bool:
        """JSON 데이터를 테이블로 포맷팅"""
        formatted = False
        
        # 입출력 분석인 경우
        if json_data.get('analysis_type') == 'input_output':
            formatted = True
            
            # 입력 파라미터 표
            if json_data.get('inputs'):
                input_table = Table(title="• 입력 파라미터", show_header=True, header_style="bright_white")
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
                self.console.print(input_table)
                self.console.print()
            
            # 출력 값 표
            if json_data.get('outputs'):
                output_table = Table(title="• 출력 값", show_header=True, header_style="bright_white")
                output_table.add_column("출력값명")
                output_table.add_column("타입")
                output_table.add_column("설명")
                
                for out in json_data['outputs']:
                    output_table.add_row(
                        out.get('name', 'N/A'),
                        out.get('type', 'N/A'),
                        out.get('description', 'N/A')
                    )
                self.console.print(output_table)
                self.console.print()
            
            # 요약 표시
            if json_data.get('summary'):
                self.console.print(Panel(json_data['summary'], title="• 분석 요약", border_style="white"))
        
        # 함수 호출관계 분석인 경우
        elif json_data.get('function_calls'):
            formatted = True
            for main_func, call_info in json_data['function_calls'].items():
                if isinstance(call_info, dict) and 'calls' in call_info:
                    # 함수 호출 목록 표
                    call_table = Table(title=f"• {main_func} 함수 호출 관계", show_header=True, header_style="bright_white")
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
                    
                    self.console.print(call_table)
                    self.console.print()
        
        # 기타 JSON 구조인 경우 간단한 키-값 표시
        else:
            # 일반적인 JSON 구조를 표로 표시
            if isinstance(json_data, dict):
                formatted = True
                for key, value in json_data.items():
                    if isinstance(value, (dict, list)):
                        self.console.print(f"[bright_white]• {key}:[/bright_white]")
                        if isinstance(value, list) and len(value) > 0:
                            # 리스트 항목들을 표로 표시
                            if isinstance(value[0], dict):
                                # 딕셔너리 리스트인 경우
                                table = Table(title=f"• {key}", show_header=True, header_style="white")
                                # 첫 번째 항목의 키들을 컬럼으로 사용
                                first_item = value[0]
                                for col_key in first_item.keys():
                                    table.add_column(str(col_key))
                                
                                for item in value:
                                    if isinstance(item, dict):
                                        row_values = [str(item.get(col_key, 'N/A')) for col_key in first_item.keys()]
                                        table.add_row(*row_values)
                                
                                self.console.print(table)
                                self.console.print()
                            else:
                                # 단순 리스트인 경우
                                for item in value:
                                    self.console.print(f"  [white]• {item}[/white]")
                                self.console.print()
                        elif isinstance(value, dict):
                            # 딕셔너리인 경우
                            for sub_key, sub_value in value.items():
                                self.console.print(f"  [white]• {sub_key}:[/white] {sub_value}")
                            self.console.print()
                    else:
                        self.console.print(f"[white]• {key}:[/white] {value}")
                self.console.print()
        
        return formatted

    def create_io_tables(self, io_analysis: Dict) -> List[Table]:
        """Input/Output 분석을 위한 테이블 생성"""
        tables = []
        
        if not io_analysis:
            return tables
            
        # 입력 파라미터 테이블
        inputs = io_analysis.get('inputs', [])
        if inputs:
            input_table = Table(title="• 입력 파라미터", show_header=True, header_style="bright_white")
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
            tables.append(input_table)
        
        # 출력 값 테이블
        outputs = io_analysis.get('outputs', [])
        if outputs:
            output_table = Table(title="• 출력 값", show_header=True, header_style="white")
            output_table.add_column("출력값명")
            output_table.add_column("타입")
            output_table.add_column("설명")
            
            for out in outputs:
                output_table.add_row(
                    out.get('name', 'N/A'),
                    out.get('type', 'N/A'),
                    out.get('description', 'N/A')
                )
            tables.append(output_table)
        
        return tables