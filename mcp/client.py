"""
HTTP-based MCP Client for Swing CLI
CoE 전용 MCP 서버와 통신하는 클라이언트
"""

import requests
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class MCPTool:
    """MCP 도구 정보"""
    name: str
    endpoint: str
    method: str
    description: str
    schema: Dict[str, Any]


class MCPClient:
    """HTTP 기반 MCP 클라이언트"""
    
    def __init__(self, base_url: str = "http://greatcoe.cafe24.com:9000"):
        self.base_url = base_url.rstrip('/')
        self.tools: Dict[str, MCPTool] = {}
        self._load_tools()
    
    def _load_tools(self):
        """OpenAPI 스펙에서 사용 가능한 도구들을 로드"""
        try:
            response = requests.get(f"{self.base_url}/openapi.json")
            response.raise_for_status()
            spec = response.json()
            
            # OpenAPI paths에서 도구들 추출
            for path, methods in spec.get('paths', {}).items():
                for method, details in methods.items():
                    if method.lower() == 'post':  # 현재 모든 도구가 POST
                        tool_name = details.get('operationId', path.replace('/', '.').strip('.'))
                        description = details.get('description', details.get('summary', ''))
                        
                        # 요청 스키마 추출
                        schema = {}
                        request_body = details.get('requestBody', {})
                        if request_body:
                            content = request_body.get('content', {})
                            json_content = content.get('application/json', {})
                            schema = json_content.get('schema', {})
                        
                        self.tools[tool_name] = MCPTool(
                            name=tool_name,
                            endpoint=path,
                            method=method.upper(),
                            description=description,
                            schema=schema
                        )
                        
        except Exception as e:
            print(f"MCP 도구 로딩 실패: {e}")
    
    def list_tools(self) -> List[MCPTool]:
        """사용 가능한 도구 목록 반환"""
        return list(self.tools.values())
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """특정 도구 정보 반환"""
        return self.tools.get(tool_name)
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 도구 호출"""
        from rich.console import Console
        console = Console()
        
        tool = self.tools.get(tool_name)
        if not tool:
            console.print(f"[dim]DEBUG: 도구를 찾을 수 없습니다: {tool_name}[/dim]")
            return {"error": f"도구를 찾을 수 없습니다: {tool_name}"}
        
        try:
            url = f"{self.base_url}{tool.endpoint}"
            headers = {"Content-Type": "application/json"}
            
            console.print(f"[dim]DEBUG: MCP API 호출 시작[/dim]")
            console.print(f"[dim]DEBUG: URL: {url}[/dim]")
            console.print(f"[dim]DEBUG: 도구명: {tool_name}[/dim]")
            console.print(f"[dim]DEBUG: 요청 데이터: {arguments}[/dim]")
            
            response = requests.post(url, headers=headers, json=arguments)
            console.print(f"[dim]DEBUG: HTTP 응답 코드: {response.status_code}[/dim]")
            console.print(f"[dim]DEBUG: HTTP 응답 내용: {response.text[:200]}...[/dim]")
            
            response.raise_for_status()
            
            result_data = response.json()
            console.print(f"[dim]DEBUG: MCP API 호출 성공![/dim]")
            
            return {
                "success": True,
                "result": result_data,
                "tool_name": tool_name
            }
            
        except requests.RequestException as e:
            console.print(f"[dim]DEBUG: MCP API 호출 실패: {e}[/dim]")
            return {
                "success": False,
                "error": f"도구 호출 실패: {e}",
                "tool_name": tool_name
            }
    
    def get_tool_description(self, tool_name: str) -> str:
        """도구 설명을 LLM이 이해할 수 있는 형태로 반환"""
        tool = self.tools.get(tool_name)
        if not tool:
            return ""
        
        schema_props = tool.schema.get('properties', {})
        params = []
        for param_name, param_info in schema_props.items():
            param_type = param_info.get('type', 'string')
            param_desc = param_info.get('description', '')
            default_val = param_info.get('default', '')
            
            param_str = f"- {param_name} ({param_type})"
            if param_desc:
                param_str += f": {param_desc}"
            if default_val:
                param_str += f" [기본값: {default_val}]"
            params.append(param_str)
        
        params_str = "\n".join(params) if params else "파라미터 없음"
        
        return f"""
## {tool.name}
{tool.description}

**파라미터:**
{params_str}

**사용 예시:**
{tool.name}(query="검색어", program_id="프로그램ID")
"""
    
    def format_tools_for_llm(self) -> str:
        """모든 도구 정보를 LLM 프롬프트에 포함할 형태로 포맷팅"""
        if not self.tools:
            return "사용 가능한 MCP 도구가 없습니다."
        
        tool_descriptions = []
        for tool_name, tool in self.tools.items():
            tool_descriptions.append(self.get_tool_description(tool_name))
        
        return f"""
# 사용 가능한 MCP 도구들

다음 도구들을 활용하여 사용자 요청을 처리할 수 있습니다:

{"".join(tool_descriptions)}

도구를 사용할 때는 다음 형식으로 호출해주세요:
```json
{{
  "tool_calls": [
    {{
      "tool_name": "도구명",
      "arguments": {{
        "param1": "값1",
        "param2": "값2"
      }}
    }}
  ]
}}
```
"""