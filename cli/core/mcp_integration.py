"""
MCP Integration for Swing CLI
기존 LLM 서비스와 MCP를 연동하는 통합 모듈
"""

import json
from typing import Dict, List, Any, Optional
from cli.core.context_manager import PromptBuilder
from mcp.client import MCPClient
from mcp.tools import MCPToolManager
from .debug_manager import DebugManager


class MCPPromptBuilder(PromptBuilder):
    """MCP 도구 정보를 포함한 프롬프트 빌더"""
    
    def __init__(self, task: str, mcp_client: Optional[MCPClient] = None):
        super().__init__(task)
        self.mcp_client = mcp_client
    
    def build(self, user_input: str, file_context: dict, history: list = None, file_manager=None):
        """MCP 도구 정보를 포함한 프롬프트 생성"""
        messages = super().build(user_input, file_context, history, file_manager)
        
        # MCP 도구 정보를 시스템 메시지에 추가
        if self.mcp_client and self._should_include_mcp_tools(user_input):
            from rich.console import Console
            DebugManager.info("MCP 도구 정보를 프롬프트에 추가 중...")
            mcp_tools_info = self.mcp_client.format_tools_for_llm()
            DebugManager.info(f"MCP 도구 정보 길이: {len(mcp_tools_info)} 글자")
            messages.insert(-1, {  # 마지막 사용자 메시지 앞에 삽입
                "role": "system", 
                "content": mcp_tools_info
            })
            DebugManager.info(f"최종 메시지 수: {len(messages)}개")
        
        return messages
    
    def _should_include_mcp_tools(self, user_input: str) -> bool:
        """MCP 도구 포함 여부 결정"""
        # 특정 키워드가 있으면 MCP 도구 포함
        mcp_keywords = [
            '담당자', '매니저', '연락처', '조회', '찾아',  # assign.lookup 관련
            '이메일', '메일', '발송', '초안',              # email 관련
            'mcp', 'tool', '스윙'                        # 직접 도구 요청
        ]
        
        user_input_lower = user_input.lower()
        should_include = any(keyword in user_input_lower for keyword in mcp_keywords)
        
        # 디버그 로그 추가 (기존 스타일에 맞춤)
        from rich.console import Console
        console = Console()
        #console.print(f"[dim]DEBUG: MCP 키워드 검사: '{user_input}' -> {should_include}[/dim]")
        if should_include:
            matched_keywords = [kw for kw in mcp_keywords if kw in user_input_lower]
            #console.print(f"[dim]DEBUG: 매치된 키워드: {matched_keywords}[/dim]")
        
        return should_include


class MCPIntegration:
    """Swing CLI와 MCP의 통합 관리"""
    
    def __init__(self, mcp_base_url: str = "http://greatcoe.cafe24.com:9000"):
        self.mcp_client = MCPClient(mcp_base_url)
        self.tool_manager = None
        self.enabled = True
    
    def initialize(self, console=None):
        """MCP 통합 초기화"""
        try:
            self.tool_manager = MCPToolManager(self.mcp_client, console)
            return True
        except Exception as e:
            print(f"MCP 초기화 실패: {e}")
            self.enabled = False
            return False
    
    def create_prompt_builder(self, task: str) -> PromptBuilder:
        """MCP 통합된 프롬프트 빌더 생성"""
        if self.enabled:
            return MCPPromptBuilder(task, self.mcp_client)
        else:
            return PromptBuilder(task)  # 기본 프롬프트 빌더
    
    def process_llm_response(self, response_content: str, original_question: str = "") -> Dict[str, Any]:
        """LLM 응답에서 MCP 도구 호출 처리"""
        if not self.enabled or not self.tool_manager:
            from rich.console import Console
            DebugManager.info("MCP가 비활성화되어 있거나 tool_manager가 없습니다.")
            return {"has_tool_calls": False}
        
        from rich.console import Console
        DebugManager.info(f"LLM 응답에서 도구 호출 확인 중... (응답 길이: {len(response_content)})")
        result = self.tool_manager.execute_tool_calls(response_content, original_question)
        DebugManager.info(f"도구 호출 결과: {result.get('has_tool_calls', False)}")
        
        return result
    
    def show_mcp_status(self, console):
        """MCP 상태 표시"""
        if not self.enabled:
            console.print("• MCP 연동이 비활성화되어 있습니다.")
            return
        
        tools = self.mcp_client.list_tools()
        #console.print(f"• MCP 서버: {self.mcp_client.base_url}")
        console.print(f"• 사용 가능한 도구 수: {len(tools)}개")
        
        if self.tool_manager:
            self.tool_manager.show_available_tools()
    
    def show_tool_help(self, tool_name: str, console):
        """특정 도구 도움말 표시"""
        if not self.enabled or not self.tool_manager:
            console.print("• MCP가 비활성화되어 있습니다.")
            return
        
        self.tool_manager.show_tool_help(tool_name)