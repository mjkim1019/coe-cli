#!/usr/bin/env python3
"""
Swing CLI의 독립 실행 명령어들을 제공합니다.
Usage: python coe.py [command] [options]
"""

import sys
import os
import click
from typing import Dict, List

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from actions.file_manager import FileManager
from llm.service import LLMService
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.columns import Columns
from rich.markdown import Markdown


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
            self.console.print("[bold blue]🧠 LLM을 통한 심화 분석을 수행하고 있습니다...[/bold blue]")
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
        
        self.console.print(f"[dim]DEBUG: _perform_llm_analysis 시작, 파일 수: {len(files_data)}[/dim]")
        
        for file_path, file_info in files_data.items():
            try:
                self.console.print(f"[dim]DEBUG: 파일 처리 시작: {file_path}[/dim]")
                
                # 파일 내용 가져오기
                content = self.file_manager.files.get(file_path, "")
                self.console.print(f"[dim]DEBUG: 파일 내용 길이: {len(content)}[/dim]")
                
                if not content:
                    self.console.print(f"[dim]DEBUG: 파일 내용이 비어있어 건너뜀: {file_path}[/dim]")
                    continue
                
                # LLM 분석 프롬프트 구성
                analysis_prompt = self._build_analysis_prompt(file_path, file_info, content)
                self.console.print(f"[dim]DEBUG: 프롬프트 길이: {len(analysis_prompt)}[/dim]")
                
                # LLM 호출
                messages = [
                    {"role": "system", "content": "You are a code analysis expert. Analyze the given file and provide structured insights."},
                    {"role": "user", "content": analysis_prompt}
                ]
                
                self.console.print(f"[dim]DEBUG: LLM 호출 시작[/dim]")
                response = self.llm_service.chat_completion(messages)
                
                if response and "choices" in response:
                    llm_content = response["choices"][0]["message"]["content"]
                    self.console.print(f"[dim]DEBUG: LLM 응답 길이: {len(llm_content)}[/dim]")
                    self.console.print(f"[dim]DEBUG: LLM 응답 미리보기: {llm_content[:200]}...[/dim]")
                    
                    parsed_result = self._parse_llm_response(llm_content)
                    self.console.print(f"[dim]DEBUG: 파싱 결과 키들: {list(parsed_result.keys()) if isinstance(parsed_result, dict) else 'not dict'}[/dim]")
                    
                    llm_results[file_path] = parsed_result
                else:
                    self.console.print(f"[dim]DEBUG: LLM 응답이 비어있음 또는 형식 오류[/dim]")
                
            except Exception as e:
                self.console.print(f"[red]LLM 분석 실패 ({file_path}): {e}[/red]")
                import traceback
                self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
                continue
        
        self.console.print(f"[dim]DEBUG: _perform_llm_analysis 완료, 결과 수: {len(llm_results)}[/dim]")
        return llm_results

    def _build_analysis_prompt(self, file_path: str, file_info: Dict, content: str) -> str:
        """LLM 분석을 위한 프롬프트 구성"""
        file_type = file_info.get('file_type', 'unknown')
        basic_analysis = file_info.get('basic_analysis', {})
        
        prompt = f"""파일 분석 요청:

파일 경로: {file_path}
파일 타입: {file_type}

기본 분석 결과:
{str(basic_analysis)}

파일 내용:
```
{content[:3000]}{'...' if len(content) > 3000 else ''}
```

다음 항목들을 JSON 형태로 정확히 분석해주세요:

1. purpose: 파일의 주요 목적과 역할 (한국어로 상세히)
2. key_functions: 주요 함수들과 그 역할 리스트
3. input_output_analysis: {{
   "inputs": [
     {{
       "name": "파라미터명",
       "type": "데이터타입", 
       "nullable": true/false,
       "description": "파라미터 설명"
     }}
   ],
   "outputs": [
     {{
       "name": "리턴값명",
       "type": "데이터타입",
       "nullable": true/false, 
       "description": "리턴값 설명"
     }}
   ]
}}
4. dependencies: 의존성 분석 (imports, includes 등)
5. complexity_score: 복잡도 점수 (1-10)
6. maintainability: 유지보수성 평가 (한국어)
7. suggestions: 개선 제안사항 (한국어)
8. call_patterns: 호출 관계 패턴

**중요**: 
- input_output_analysis에서 nullable 정보를 반드시 포함하세요
- C 함수의 포인터 파라미터는 nullable: true로 설정
- SQL의 바인드 변수는 nullable 여부를 명시하세요
- 모든 입출력 값에 대해 nullable 정보를 빠짐없이 제공하세요

JSON 형태로만 응답하고, 다른 텍스트는 포함하지 마세요."""
        
        return prompt

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
            'complexity_overview': {},
            'common_patterns': []
        }
        
        # 파일 타입별 통계
        for file_path, file_info in files_data.items():
            file_type = file_info.get('file_type', 'unknown')
            if file_type not in summary['file_types']:
                summary['file_types'][file_type] = 0
            summary['file_types'][file_type] += 1
        
        # 복잡도 분석
        complexities = []
        for file_path, file_info in files_data.items():
            llm_analysis = file_info.get('llm_analysis', {})
            if llm_analysis and 'complexity_score' in llm_analysis:
                complexities.append(llm_analysis['complexity_score'])
        
        if complexities:
            summary['complexity_overview'] = {
                'average': sum(complexities) / len(complexities),
                'max': max(complexities),
                'min': min(complexities)
            }
        
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
        
        complexity = summary.get('complexity_overview', {})
        if complexity:
            summary_text += f"\n복잡도 분석:\n"
            summary_text += f"  • 평균: {complexity.get('average', 0):.1f}/10\n"
            summary_text += f"  • 최고: {complexity.get('max', 0)}/10\n"
            summary_text += f"  • 최저: {complexity.get('min', 0)}/10\n"
        
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
                
                if 'complexity_score' in llm_analysis:
                    content += f"**복잡도**: {llm_analysis['complexity_score']}/10\n\n"
                
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
                
                # Input/Output 분석 추가
                if 'input_output_analysis' in llm_analysis:
                    io_analysis = llm_analysis['input_output_analysis']
                    if io_analysis:
                        content += "**📥 입력 파라미터**:\n"
                        inputs = io_analysis.get('inputs', [])
                        if inputs:
                            for inp in inputs:
                                nullable_text = " (nullable)" if inp.get('nullable', False) else " (non-null)"
                                content += f"  • {inp.get('name', 'N/A')} ({inp.get('type', 'N/A')}){nullable_text}: {inp.get('description', 'N/A')}\n"
                        else:
                            content += "  • 없음\n"
                        
                        content += "\n**📤 출력 값**:\n"
                        outputs = io_analysis.get('outputs', [])
                        if outputs:
                            for out in outputs:
                                nullable_text = " (nullable)" if out.get('nullable', False) else " (non-null)"
                                content += f"  • {out.get('name', 'N/A')} ({out.get('type', 'N/A')}){nullable_text}: {out.get('description', 'N/A')}\n"
                        else:
                            content += "  • 없음\n"
                        content += "\n"
                
                if 'maintainability' in llm_analysis and llm_analysis['maintainability']:
                    content += f"**유지보수성**: {llm_analysis['maintainability']}\n\n"
                
                if 'suggestions' in llm_analysis and llm_analysis['suggestions']:
                    content += f"**개선사항**: {llm_analysis['suggestions']}\n\n"
                
                panel = Panel(
                    Markdown(content.strip()),
                    title=f"📄 {filename}",
                    border_style="green"
                )
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
        
        tree = Tree("호출 관계")
        for file_path, patterns in call_graph.items():
            filename = os.path.basename(file_path)
            if patterns:
                file_node = tree.add(f"📄 {filename}")
                if isinstance(patterns, list):
                    for pattern in patterns:
                        file_node.add(f"→ {pattern}")
                elif isinstance(patterns, str):
                    file_node.add(f"→ {patterns}")
        
        self.console.print(tree)


@click.group()
def cli():
    """Swing CLI 도구 - 코드 분석 및 관리"""
    pass


@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--no-llm', is_flag=True, help='LLM 분석 없이 기본 분석만 수행')
@click.option('--output', '-o', help='분석 결과를 파일로 저장')
def analyze(files, no_llm, output):
    """파일들의 코드 구조를 분석합니다.
    
    Usage:
        coe analyze file1.c file2.sql
        coe analyze src/ --no-llm
        coe analyze *.c -o analysis_result.json
    """
    if not files:
        console = Console()
        console.print("[red]분석할 파일을 지정해주세요.[/red]")
        console.print("사용법: coe analyze <file1> <file2> ...")
        return
    
    analyzer = CoeAnalyzer()
    
    # 파일 또는 디렉토리 처리
    file_list = []
    for file_path in files:
        if os.path.isdir(file_path):
            # 디렉토리인 경우 하위 파일들 수집
            for root, dirs, filenames in os.walk(file_path):
                for filename in filenames:
                    if filename.endswith(('.c', '.h', '.sql', '.xml', '.py')):
                        file_list.append(os.path.join(root, filename))
        else:
            file_list.append(file_path)
    
    # 분석 수행
    use_llm = not no_llm
    results = analyzer.analyze_files(file_list, use_llm=use_llm)
    
    # 결과 표시
    analyzer.display_analysis_results(results)
    
    # 파일로 저장 (선택사항)
    if output:
        import json
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        analyzer.console.print(f"\n[green]분석 결과가 {output}에 저장되었습니다.[/green]")


@cli.command()
def version():
    """버전 정보를 표시합니다."""
    console = Console()
    console.print("[bold green]Swing CLI v0.2.0[/bold green]")
    console.print("🌀 코드 구조 분석 및 대화형 CLI 도구")


if __name__ == '__main__':
    cli()