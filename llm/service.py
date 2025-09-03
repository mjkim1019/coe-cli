import requests
import os

class LLMService:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv("COE_BACKEND_URL", "http://greatcoe.cafe24.com:8000")
        self.chat_completions_url = f"{self.base_url}/v1/chat/completions"
        self.current_session_id = None

    def chat_completion(self, messages, model="gpt-4o-mini", context="aider", session_id=None, force_json=False):
        headers = {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {os.getenv("OPENAI_API_KEY")}" # CoE-Backend handles its own auth
        }
        payload = {
            "model": model,
            "messages": messages,
        }
        
        # JSON 응답 강제 시 response_format 추가
        if force_json:
            payload["response_format"] = {"type": "json_object"}
        
        # CoE Backend API 사용가이드에 따른 context와 session_id 추가
        if context:
            payload["context"] = context
            
        if session_id:
            payload["session_id"] = session_id
        elif self.current_session_id:
            payload["session_id"] = self.current_session_id
            
        try:
            response = requests.post(self.chat_completions_url, headers=headers, json=payload)
            response.raise_for_status() # Raise an exception for HTTP errors

            result = response.json()
            
            # 응답에서 session_id 추출하여 저장
            if "session_id" in result:
                self.current_session_id = result["session_id"]
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with LLM backend: {e}")
            return None
    
    def set_context(self, context):
        """현재 컨텍스트 설정"""
        self.context = context
    
    def get_session_id(self):
        """현재 세션 ID 반환"""
        return self.current_session_id
    
    def reset_session(self):
        """세션 초기화"""
        self.current_session_id = None
