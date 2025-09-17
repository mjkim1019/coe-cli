#!/usr/bin/env python3
"""
코드 분석을 담당하는 CoeAnalyzer 클래스
파일 분석, LLM 기반 심화 분석, 결과 표시 등의 기능을 제공합니다.
"""

import sys
import os
from typing import Dict, List

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from actions.file_manager import FileManager
from llm.service import LLMService
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.markdown import Markdown
from .debug_manager import DebugManager


class CoeAnalyzer:
    def __init__(self):
        self.file_manager = FileManager()
        self.llm_service = LLMService()
        self.console = Console()

    def analyze_files(self, file_paths: List[str], use_llm: bool = True) -> Dict:
        """파일들을 분석하고 결과를 반환"""
        analysis_results = {
            'files': {},
            'summary': {},
            'call_graph': {},
            'file_categories': {}
        }
        
        # 파일들 추가 및 기본 분석
        self.console.print("[bold blue]📁 파일들을 분석하고 있습니다...[/bold blue]")
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                result = self.file_manager.add_single_file(file_path)
                if result['analysis']:
                    analysis_results['files'][file_path] = {
                        'file_type': result['file_type'],
                        'basic_analysis': result['analysis'],
                        'llm_analysis': None
                    }
        
        # LLM 기반 분석
        if use_llm and analysis_results['files']:
            self.console.print("[bold blue] LLM을 통한 심화 분석을 수행하고 있습니다...[/bold blue]")
            llm_analysis = self._perform_llm_analysis(analysis_results['files'])
            
            # LLM 분석 결과를 통합
            for file_path, llm_result in llm_analysis.items():
                if file_path in analysis_results['files']:
                    analysis_results['files'][file_path]['llm_analysis'] = llm_result
            
            # 전체 요약 생성
            analysis_results['summary'] = self._generate_summary(analysis_results['files'])
            analysis_results['call_graph'] = self._extract_call_relationships(analysis_results['files'])
            analysis_results['file_categories'] = self._categorize_files(analysis_results['files'])
        
        return analysis_results

    def _perform_llm_analysis(self, files_data: Dict) -> Dict:
        """LLM을 통한 파일 분석"""
        llm_results = {}
        
        DebugManager.llm(f"_perform_llm_analysis 시작, 파일 수: {len(files_data)}")
        
        for file_path, file_info in files_data.items():
            try:
                DebugManager.llm(f"파일 처리 시작: {file_path}")
                
                # 파일 내용 가져오기
                content = self.file_manager.files.get(file_path, "")
                DebugManager.llm(f"파일 내용 길이: {len(content)}")

                if not content:
                    DebugManager.llm(f"파일 내용이 비어있어 건너뜀: {file_path}")
                    continue

                # LLM 분석 프롬프트 구성
                analysis_prompt = self._build_analysis_prompt(file_path, file_info, content)
                DebugManager.llm(f"프롬프트 길이: {len(analysis_prompt)}")
                
                # LLM 호출
                messages = [
                    {"role": "system", "content": "You are a code analysis expert. Analyze the given file and provide structured insights."},
                    {"role": "user", "content": analysis_prompt}
                ]
                
                DebugManager.llm("LLM 호출 시작")
                response = self.llm_service.chat_completion(messages)
                
                if response and "choices" in response:
                    llm_content = response["choices"][0]["message"]["content"]
                    DebugManager.llm(f"LLM 응답 길이: {len(llm_content)}")
                    DebugManager.llm(f"LLM 응답 미리보기: {llm_content[:200]}...")
                    
                    parsed_result = self._parse_llm_response(llm_content)
                    DebugManager.llm(f"파싱 결과 키들: {list(parsed_result.keys()) if isinstance(parsed_result, dict) else 'not dict'}")
                    
                    llm_results[file_path] = parsed_result
                else:
                    DebugManager.llm("LLM 응답이 비어있음 또는 형식 오류")
                
            except Exception as e:
                self.console.print(f"[red]LLM 분석 실패 ({file_path}): {e}[/red]")
                import traceback
                self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
                continue
        
        DebugManager.llm(f"_perform_llm_analysis 완료, 결과 수: {len(llm_results)}")
        return llm_results

    def _build_analysis_prompt(self, file_path: str, file_info: Dict, content: str) -> str:
        """파일 타입별 특화된 LLM 분석 프롬프트 구성"""
        file_type = file_info.get('file_type', 'unknown')
        
        # 파일 타입별 전용 프롬프트 사용
        try:
            if file_type == 'c_file' or file_path.endswith('.c'):
                from prompts.c_file_prompt import get_c_file_analysis_prompt
                return get_c_file_analysis_prompt(file_path, file_info, content)
            
            elif file_type == 'xml_file' or file_path.lower().endswith('.xml'):
                from prompts.xml_file_prompt import get_xml_file_analysis_prompt
                return get_xml_file_analysis_prompt(file_path, file_info, content)
            
            elif file_type == 'sql_file' or file_path.endswith('.sql'):
                from prompts.sql_file_prompt import get_sql_file_analysis_prompt
                return get_sql_file_analysis_prompt(file_path, file_info, content)
            
            else:
                # 기본 프롬프트 사용
                from prompts.generic_file_prompt import get_generic_file_analysis_prompt
                return get_generic_file_analysis_prompt(file_path, file_info, content)
                
        except ImportError as e:
            self.console.print(f"[red]프롬프트 모듈 로드 실패: {e}[/red]")
            # fallback to basic prompt
            return self._get_fallback_prompt(file_path, file_info, content)
    
    def _get_fallback_prompt(self, file_path: str, file_info: Dict, content: str) -> str:
        """프롬프트 로드 실패 시 fallback 프롬프트"""
        basic_analysis = file_info.get('basic_analysis', {})
        file_type = file_info.get('file_type', 'unknown')
        
        return f"""파일 분석 요청 (Fallback):

파일 경로: {file_path}
파일 타입: {file_type}

기본 분석 결과:
{str(basic_analysis)}

파일 내용:
```
{content[:3000]}{'...' if len(content) > 3000 else ''}
```

다음 항목들을 JSON 형태로 분석해주세요:
1. purpose: 파일의 주요 목적과 역할
2. key_functions: 주요 함수들

JSON 형태로만 응답하세요."""

    def _parse_llm_response(self, llm_content: str) -> Dict:
        """LLM 응답을 파싱하여 구조화된 데이터로 변환"""
        try:
            import json
            # JSON 블록 추출 시도
            if '```json' in llm_content:
                start = llm_content.find('```json') + 7
                end = llm_content.find('```', start)
                json_str = llm_content[start:end].strip()
            elif llm_content.strip().startswith('{'):
                json_str = llm_content.strip()
            else:
                # JSON이 아닌 경우 기본 구조로 변환
                return {
                    'purpose': 'LLM 분석 결과 파싱 실패',
                    'raw_response': llm_content
                }
            
            return json.loads(json_str)
        except Exception as e:
            return {
                'purpose': 'LLM 분석 결과 파싱 실패',
                'error': str(e),
                'raw_response': llm_content
            }

    def _generate_summary(self, files_data: Dict) -> Dict:
        """전체 파일들의 요약 생성"""
        summary = {
            'total_files': len(files_data),
            'file_types': {},
            'common_patterns': []
        }
        
        # 파일 타입별 통계
        for file_path, file_info in files_data.items():
            file_type = file_info.get('file_type', 'unknown')
            if file_type not in summary['file_types']:
                summary['file_types'][file_type] = 0
            summary['file_types'][file_type] += 1
        
        
        return summary

    def _extract_call_relationships(self, files_data: Dict) -> Dict:
        """호출 관계 분석"""
        call_graph = {}
        
        for file_path, file_info in files_data.items():
            llm_analysis = file_info.get('llm_analysis', {})
            if llm_analysis and 'call_patterns' in llm_analysis:
                call_graph[file_path] = llm_analysis['call_patterns']
        
        return call_graph

    def _categorize_files(self, files_data: Dict) -> Dict:
        """파일들을 카테고리별로 분류"""
        categories = {
            'controller': [],
            'utils': [],
            'service': [],
            'sql': [],
            'config': [],
            'ui': [],
            'other': []
        }
        
        for file_path, file_info in files_data.items():
            llm_analysis = file_info.get('llm_analysis', {})
            file_type = file_info.get('file_type', 'unknown')
            
            # 파일명과 내용 기반으로 카테고리 결정
            filename = os.path.basename(file_path).lower()
            
            if file_type == 'sql_file' or filename.endswith('.sql'):
                categories['sql'].append(file_path)
            elif any(keyword in filename for keyword in ['main', 'controller', 'ctrl']):
                categories['controller'].append(file_path)
            elif any(keyword in filename for keyword in ['util', 'helper', 'tool']):
                categories['utils'].append(file_path)
            elif any(keyword in filename for keyword in ['service', 'svc']):
                categories['service'].append(file_path)
            elif any(keyword in filename for keyword in ['config', 'setting']):
                categories['config'].append(file_path)
            elif file_type == 'xml_file' or filename.endswith('.xml'):
                categories['ui'].append(file_path)
            else:
                categories['other'].append(file_path)
        
        return categories

    def display_analysis_results(self, results: Dict):
        """분석 결과를 Rich UI로 표시"""
        self.console.print("\n[bold green]🎯 코드 구조 분석 결과[/bold green]")
        
        # 1. 전체 요약
        self._display_summary(results['summary'])
        
        # 2. 파일 카테고리
        self._display_file_categories(results['file_categories'])
        
        # 3. 파일별 상세 분석
        self._display_detailed_analysis(results['files'])
        
        # 4. 호출 관계 그래프
        if results['call_graph']:
            self._display_call_graph(results['call_graph'])

    def _display_summary(self, summary: Dict):
        """전체 요약 표시"""
        if not summary:
            return
            
        # 요약 패널
        summary_text = f"분석된 파일 수: {summary.get('total_files', 0)}개\n"
        
        file_types = summary.get('file_types', {})
        if file_types:
            summary_text += "\n파일 타입별 분포:\n"
            for file_type, count in file_types.items():
                summary_text += f"  • {file_type}: {count}개\n"
        
        
        panel = Panel(
            summary_text.strip(),
            title="📊 전체 요약",
            border_style="blue"       
        )
        self.console.print(panel)

    def _display_file_categories(self, categories: Dict):
        """파일 카테고리 표시"""
        if not categories:
            return
            
        tree = Tree("📁 파일 카테고리")
        
        for category, files in categories.items():
            if files:
                category_node = tree.add(f"[bold]{category.upper()}[/bold] ({len(files)}개)")
                for file_path in files:
                    filename = os.path.basename(file_path)
                    category_node.add(f"📄 {filename}")
        
        self.console.print(tree)
    
    def _create_file_type_tables(self, llm_analysis: Dict, file_path: str) -> List:
        """파일 타입별 특화 테이블 생성"""
        tables = []
        
        # C 파일 특화 테이블들
        if file_path.endswith('.c'):
            # IO Formatter 분석 테이블
            if 'io_formatter_analysis' in llm_analysis:
                io_formatter = llm_analysis['io_formatter_analysis']
                
                # 통합된 IO Formatter 테이블
                has_input = 'input_structure' in io_formatter and io_formatter['input_structure'].get('key_fields')
                has_output = 'output_structure' in io_formatter and io_formatter['output_structure'].get('key_fields')
                
                if has_input or has_output:
                    formatter_table = Table(title="📋 IO Formatter", show_header=True, header_style="bold blue")
                    formatter_table.add_column("구분")
                    formatter_table.add_column("필드명")
                    formatter_table.add_column("타입")
                    formatter_table.add_column("Nullable")
                    formatter_table.add_column("설명")
                    
                    # 입력 필드들 추가
                    if has_input:
                        for field in io_formatter['input_structure']['key_fields']:
                            nullable_text = "O" if field.get('nullable', False) else "X"
                            formatter_table.add_row(
                                "📥 입력",
                                field.get('name', 'N/A'),
                                field.get('type', 'N/A'),
                                nullable_text,
                                field.get('description', 'N/A')
                            )
                    
                    # 출력 필드들 추가
                    if has_output:
                        for field in io_formatter['output_structure']['key_fields']:
                            formatter_table.add_row(
                                "📤 출력",
                                field.get('name', 'N/A'),
                                field.get('type', 'N/A'),
                                "-",  # 출력은 nullable 표시 안함
                                field.get('description', 'N/A')
                            )
                    
                    tables.append(formatter_table)
            
            # DBIO 호출 분석 테이블
            if 'dbio_analysis' in llm_analysis and llm_analysis['dbio_analysis'].get('dbio_calls'):
                dbio_table = Table(title="🗄️ DBIO 호출 분석", show_header=True, header_style="bold magenta")
                dbio_table.add_column("함수명")
                dbio_table.add_column("목적")
                dbio_table.add_column("입력 데이터")
                dbio_table.add_column("출력 데이터")
                
                for dbio_call in llm_analysis['dbio_analysis']['dbio_calls']:
                    dbio_table.add_row(
                        dbio_call.get('function_name', 'N/A'),
                        dbio_call.get('purpose', 'N/A'),
                        dbio_call.get('input_data', 'N/A'),
                        dbio_call.get('output_data', 'N/A')
                    )
                tables.append(dbio_table)
                
        # XML 파일 특화 테이블들
        elif file_path.lower().endswith('.xml'):
            # TrxCode 분석 테이블
            if 'trxcode_analysis' in llm_analysis and llm_analysis['trxcode_analysis'].get('trx_codes'):
                trx_table = Table(title="🔄 TrxCode 분석", show_header=True, header_style="bold purple")
                trx_table.add_column("TrxCode")
                trx_table.add_column("함수명")
                trx_table.add_column("목적")
                trx_table.add_column("호출 시점")
                trx_table.add_column("설명")
                
                for trx in llm_analysis['trxcode_analysis']['trx_codes']:
                    trx_table.add_row(
                        trx.get('code', 'N/A'),
                        trx.get('function_name', 'N/A'),
                        trx.get('purpose', 'N/A'),
                        trx.get('trigger', 'N/A'),
                        trx.get('description', 'N/A')
                    )
                tables.append(trx_table)
            
            # 데이터 흐름 테이블 (XML은 required/optional로 구분)
            if 'data_flow' in llm_analysis:
                data_flow = llm_analysis['data_flow']
                
                # 입력 필드 테이블
                if data_flow.get('input_fields'):
                    input_table = Table(title="📥 입력 필드", show_header=True, header_style="bold blue")
                    input_table.add_column("필드명")
                    input_table.add_column("타입")
                    input_table.add_column("필수여부")
                    input_table.add_column("설명")
                    
                    for field in data_flow['input_fields']:
                        required_text = "✓" if field.get('required', False) else "✗"
                        input_table.add_row(
                            field.get('name', 'N/A'),
                            field.get('type', 'N/A'),
                            required_text,
                            field.get('description', 'N/A')
                        )
                    tables.append(input_table)
                
                # 출력 필드 테이블
                if data_flow.get('output_fields'):
                    output_table = Table(title="📤 출력 필드", show_header=True, header_style="bold green")
                    output_table.add_column("필드명")
                    output_table.add_column("타입")
                    output_table.add_column("설명")
                    
                    for field in data_flow['output_fields']:
                        output_table.add_row(
                            field.get('name', 'N/A'),
                            field.get('type', 'N/A'),
                            field.get('description', 'N/A')
                        )
                    tables.append(output_table)
                    
        # SQL 파일 특화 테이블들
        elif file_path.endswith('.sql'):
            # 입출력 분석 테이블
            if 'input_output_analysis' in llm_analysis:
                io_analysis = llm_analysis['input_output_analysis']
                
                # 바인드 변수 테이블
                if io_analysis.get('inputs'):
                    input_table = Table(title="📥 바인드 변수", show_header=True, header_style="bold blue")
                    input_table.add_column("변수명")
                    input_table.add_column("타입") 
                    input_table.add_column("Nullable")
                    input_table.add_column("설명")
                    input_table.add_column("예시")
                    
                    for inp in io_analysis['inputs']:
                        nullable_text = "O" if inp.get('nullable', False) else "X"
                        input_table.add_row(
                            inp.get('name', 'N/A'),
                            inp.get('type', 'N/A'),
                            nullable_text,
                            inp.get('description', 'N/A'),
                            inp.get('example', 'N/A')
                        )
                    tables.append(input_table)
                
                # 출력 컬럼 테이블
                if io_analysis.get('outputs'):
                    output_table = Table(title="📤 출력 컬럼", show_header=True, header_style="bold green")
                    output_table.add_column("컬럼명")
                    output_table.add_column("타입")
                    output_table.add_column("설명")
                    output_table.add_column("출처 테이블")
                    
                    for out in io_analysis['outputs']:
                        output_table.add_row(
                            out.get('name', 'N/A'),
                            out.get('type', 'N/A'),
                            out.get('description', 'N/A'),
                            out.get('table_source', 'N/A')
                        )
                    tables.append(output_table)
            
            # 테이블 조인 분석 테이블
            if 'table_analysis' in llm_analysis and llm_analysis['table_analysis'].get('join_analysis'):
                join_table = Table(title="🔗 테이블 조인 분석", show_header=True, header_style="bold cyan")
                join_table.add_column("조인 타입")
                join_table.add_column("테이블들")
                join_table.add_column("조인 조건")
                join_table.add_column("목적")
                
                for join in llm_analysis['table_analysis']['join_analysis']:
                    tables_str = " ↔ ".join(join.get('tables', []))
                    join_table.add_row(
                        join.get('type', 'N/A'),
                        tables_str,
                        join.get('condition', 'N/A'),
                        join.get('purpose', 'N/A')
                    )
                tables.append(join_table)
                
        # 기본 입출력 테이블 (다른 파일 타입들)
        else:
            if 'input_output_analysis' in llm_analysis:
                io_analysis = llm_analysis['input_output_analysis']
                
                # 입력 파라미터 테이블
                if io_analysis.get('inputs'):
                    input_table = Table(title="📥 입력 파라미터", show_header=True, header_style="bold blue")
                    input_table.add_column("파라미터명")
                    input_table.add_column("타입") 
                    input_table.add_column("Nullable")
                    input_table.add_column("설명")
                    
                    for inp in io_analysis['inputs']:
                        nullable_text = "O" if inp.get('nullable', False) else "X"
                        input_table.add_row(
                            inp.get('name', 'N/A'),
                            inp.get('type', 'N/A'),
                            nullable_text,
                            inp.get('description', 'N/A')
                        )
                    tables.append(input_table)
                
                # 출력 값 테이블
                if io_analysis.get('outputs'):
                    output_table = Table(title="📤 출력 값", show_header=True, header_style="bold green")
                    output_table.add_column("출력값명")
                    output_table.add_column("타입")
                    output_table.add_column("설명")
                    
                    for out in io_analysis['outputs']:
                        output_table.add_row(
                            out.get('name', 'N/A'),
                            out.get('type', 'N/A'),
                            out.get('description', 'N/A')
                        )
                    tables.append(output_table)
        
        return tables

    def _display_detailed_analysis(self, files_data: Dict):
        """파일별 상세 분석 표시"""
        if not files_data:
            return
            
        self.console.print("\n[bold blue]📋 파일별 상세 분석[/bold blue]")
        
        for file_path, file_info in files_data.items():
            filename = os.path.basename(file_path)
            llm_analysis = file_info.get('llm_analysis', {})
            
            if llm_analysis and 'purpose' in llm_analysis:
                # LLM 분석 결과가 있는 경우
                content = f"**목적**: {llm_analysis.get('purpose', 'N/A')}\n\n"
                
                
                if 'key_functions' in llm_analysis and llm_analysis['key_functions']:
                    if isinstance(llm_analysis['key_functions'], list):
                        # 리스트의 각 항목이 문자열인지 확인
                        func_strs = []
                        for func in llm_analysis['key_functions']:
                            if isinstance(func, dict):
                                func_strs.append(str(func.get('name', func)))
                            else:
                                func_strs.append(str(func))
                        content += f"**주요 함수**: {', '.join(func_strs)}\n\n"
                    else:
                        content += f"**주요 함수**: {llm_analysis['key_functions']}\n\n"
                
                # 파일 타입별 특화된 테이블 생성
                special_tables = self._create_file_type_tables(llm_analysis, file_path)
                
                
                panel = Panel(
                    Markdown(content.strip()),
                    title=f"📄 {filename}",
                    border_style="green"
                )
                self.console.print(panel)
                
                # 파일 타입별 특화 테이블들을 별도로 표시
                for table in special_tables:
                    self.console.print(table)
                    self.console.print()  # 빈 줄 추가
                    
            else:
                # 기본 분석만 있는 경우
                basic_analysis = file_info.get('basic_analysis', {})
                content = f"파일 타입: {file_info.get('file_type', 'unknown')}\n"
                content += f"기본 분석: {str(basic_analysis)[:200]}..."
                
                panel = Panel(
                    content,
                    title=f"📄 {filename}",
                    border_style="yellow"
                )
                self.console.print(panel)

    def _display_call_graph(self, call_graph: Dict):
        """호출 관계 그래프 표시"""
        if not call_graph:
            return
            
        self.console.print("\n[bold purple]🔗 호출 관계 분석[/bold purple]")
        
        for file_path, calls in call_graph.items():
            filename = os.path.basename(file_path)
            if calls:
                self.console.print(f"📄 {filename}:")
                for call in calls:
                    self.console.print(f"  → {call}")