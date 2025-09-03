"""
MCP Tool Manager for Swing CLI
MCP 도구 실행 및 결과 처리를 담당
"""

import json
import re
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .client import MCPClient


class MCPToolManager:
    """MCP 도구 관리자"""
    
    def __init__(self, mcp_client: MCPClient, console: Optional[Console] = None):
        self.client = mcp_client
        self.console = console or Console()
    
    def execute_tool_calls(self, response_content: str, original_question: str = "") -> Dict[str, Any]:
        """LLM 응답에서 도구 호출을 추출하고 실행"""
        tool_calls = self._extract_tool_calls(response_content)
        if not tool_calls:
            return {"has_tool_calls": False}
        
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get('tool_name')
            arguments = tool_call.get('arguments', {})
            
            # 도구 실행 중 애니메이션 표시 (기존 스타일)
            display_name = self._get_display_name(tool_name)
            
            with self.console.status(f"[bold green] MCP 도구 '{display_name}' 실행 중...", spinner="dots"):
                result = self.client.call_tool(tool_name, arguments)
            
            results.append(result)
        
        # MCP 도구 결과를 LLM에게 보내서 자연스러운 답변으로 변환
        natural_response = self._convert_to_natural_response(results, original_question)
        
        return {
            "has_tool_calls": True,
            "results": results,
            "natural_response": natural_response
        }
    
    def _convert_to_natural_response(self, results: List[Dict[str, Any]], original_question: str) -> str:
        """MCP 도구 실행 결과를 LLM에게 보내서 자연스러운 문장으로 변환"""
        try:
            # 결과 요약 생성
            results_summary = ""
            for result in results:
                tool_name = result.get('tool_name', 'Unknown')
                if result.get('success'):
                    tool_result = result.get('result', {})
                    results_summary += f"도구 {tool_name} 실행 결과: {str(tool_result)[:500]}\n"
                else:
                    error_msg = result.get('error', '알 수 없는 오류')
                    results_summary += f"도구 {tool_name} 실행 실패: {error_msg}\n"
            
            # LLM에게 자연스러운 응답 요청
            from llm.service import LLMService
            llm_service = LLMService()
            
            messages = [
                {
                    "role": "system",
                    "content": "당신은 도구 실행 결과를 사용자에게 친근하고 자연스럽게 전달하는 AI입니다. 도구 실행 결과를 바탕으로 사용자 질문에 대한 답변을 만들어주세요."
                },
                {
                    "role": "user", 
                    "content": f"사용자 질문: {original_question}\n\n도구 실행 결과:\n{results_summary}\n\n위 결과를 바탕으로 사용자에게 자연스럽고 친근한 답변을 만들어주세요."
                }
            ]
            
            llm_response = llm_service.chat_completion(messages)
            
            if llm_response and "choices" in llm_response:
                return llm_response["choices"][0]["message"]["content"]
            else:
                return "죄송합니다. 결과를 처리하는 중 오류가 발생했습니다."
                
        except Exception as e:
            print(f"[dim]DEBUG: 자연스러운 응답 생성 실패: {e}[/dim]")
            return "요청하신 작업을 수행했습니다만, 결과를 정리하는 중 오류가 발생했습니다."
    
    def _get_display_name(self, tool_name: str) -> str:
        """도구명을 사용자 친화적으로 변환"""
        if 'assign.lookup' in tool_name or 'assign_lookup' in tool_name:
            return "담당자 조회"
        elif 'email.compose' in tool_name or 'email_compose' in tool_name:
            return "이메일 초안 생성"
        elif 'email.send' in tool_name or 'email_send' in tool_name:
            return "이메일 발송"
        else:
            return tool_name
    
    def _extract_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """응답에서 도구 호출 정보 추출"""
        tool_calls = []
        
        # JSON 코드 블록 찾기
        json_blocks = re.findall(r'```json\s*(.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
        
        for block in json_blocks:
            try:
                data = json.loads(block)
                if isinstance(data, dict) and 'tool_calls' in data:
                    tool_calls.extend(data['tool_calls'])
            except json.JSONDecodeError:
                continue
        
        # 직접 JSON 형태 찾기
        if not tool_calls:
            try:
                # 전체 응답이 JSON인지 확인
                data = json.loads(content.strip())
                if isinstance(data, dict) and 'tool_calls' in data:
                    tool_calls.extend(data['tool_calls'])
            except json.JSONDecodeError:
                pass
        
        return tool_calls
    
    def _format_results(self, results: List[Dict[str, Any]]) -> List[Any]:
        """도구 실행 결과를 UI 컴포넌트로 포맷팅"""
        formatted = []
        
        for result in results:
            tool_name = result.get('tool_name', 'Unknown')
            
            if result.get('success'):
                # 성공한 경우
                tool_result = result.get('result', {})
                formatted.append(self._format_tool_result(tool_name, tool_result))
            else:
                # 실패한 경우
                error_msg = result.get('error', '알 수 없는 오류')
                formatted.append(Panel(
                    f"• {error_msg}",
                    title=f"• {tool_name} 실행 실패",
                    border_style="red"
                ))
        
        return formatted
    
    def _format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> Any:
        """도구별 결과 포맷팅"""
        
        if 'assign.lookup' in tool_name:
            return self._format_assign_lookup_result(result)
        elif 'email.compose' in tool_name:
            return self._format_email_compose_result(result)
        elif 'email.send' in tool_name:
            return self._format_email_send_result(result)
        else:
            # 기본 포맷팅
            return Panel(
                str(result),
                title=f"• {tool_name} 실행 결과",
                border_style="green"
            )
    
    def _format_assign_lookup_result(self, result: Dict[str, Any]) -> Table:
        """담당자 조회 결과 포맷팅"""
        table = Table(title="• 담당자 조회 결과", show_header=True, header_style="bold blue")
        table.add_column("구분")
        table.add_column("이름")
        table.add_column("부서")
        table.add_column("연락처")
        
        # 결과 구조에 따라 조정 필요
        if isinstance(result, list):
            for person in result:
                table.add_row(
                    person.get('type', 'N/A'),
                    person.get('name', 'N/A'),
                    person.get('department', 'N/A'),
                    person.get('contact', 'N/A')
                )
        elif isinstance(result, dict):
            # 단일 결과인 경우
            table.add_row(
                result.get('type', 'N/A'),
                result.get('name', 'N/A'),
                result.get('department', 'N/A'),
                result.get('contact', 'N/A')
            )
        
        return table
    
    def _format_email_compose_result(self, result: Dict[str, Any]) -> Panel:
        """이메일 초안 생성 결과 포맷팅"""
        content = ""
        
        if 'subject' in result:
            content += f"**제목:** {result['subject']}\n\n"
        
        if 'preview_text' in result:
            content += f"**미리보기:**\n{result['preview_text']}\n\n"
        
        if 'draft_id' in result:
            content += f"**초안 ID:** {result['draft_id']}\n"
            content += "'/mcp email.send {draft_id}' 명령으로 발송할 수 있습니다."
        
        return Panel(
            content.strip(),
            title="• 이메일 초안 생성 완료",
            border_style="blue"
        )
    
    def _format_email_send_result(self, result: Dict[str, Any]) -> Panel:
        """이메일 발송 결과 포맷팅"""
        content = ""
        
        if result.get('sent', False):
            content = f"• 이메일이 성공적으로 발송되었습니다.\n"
        else:
            content = f"• 이메일 발송이 시뮬레이트되었습니다.\n"
        
        if 'message_id' in result:
            content += f"메시지 ID: {result['message_id']}"
        
        return Panel(
            content.strip(),
            title="• 이메일 발송 결과",
            border_style="green"
        )
    
    def show_available_tools(self):
        """사용 가능한 도구 목록 표시"""
        tools = self.client.list_tools()
        
        if not tools:
            self.console.print("• 사용 가능한 MCP 도구가 없습니다.")
            return
        
        table = Table(title="• 사용 가능한 MCP 도구들", show_header=True, header_style="bold green")
        table.add_column("도구명", width=30)
        table.add_column("설명", width=50)
        table.add_column("엔드포인트")
        
        for tool in tools:
            table.add_row(
                tool.name,
                tool.description[:47] + "..." if len(tool.description) > 50 else tool.description,
                tool.endpoint
            )
        
        self.console.print(table)
    
    def show_tool_help(self, tool_name: str):
        """특정 도구의 도움말 표시"""
        tool = self.client.get_tool(tool_name)
        if not tool:
            self.console.print(f"• 도구를 찾을 수 없습니다: {tool_name}")
            return
        
        description = self.client.get_tool_description(tool_name)
        self.console.print(Panel(
            description,
            title=f"• {tool_name} 도움말",
            border_style="cyan"
        ))