#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from llm.service import LLMService
from cli.core.architect_prompts import ArchitectPrompts

llm = LLMService()
prompts = ArchitectPrompts()

user_request = "고객 정보를 분석해서 월별 구독 통계 리포트 만들어줘"

messages = [
    {"role": "system", "content": prompts.PLAN_GENERATION_SYSTEM},
    {"role": "user", "content": prompts.PLAN_GENERATION_USER_TEMPLATE.format(
        user_request=user_request,
        files_count=0,
        file_list="None"
    )}
]

print("Calling LLM...")
response = llm.chat_completion(messages, force_json=True)

if response and "choices" in response:
    content = response["choices"][0]["message"]["content"]
    print("\n=== RAW RESPONSE ===")
    print(content)
    print("\n=== END RESPONSE ===")
    
    # Try to parse
    import json
    try:
        data = json.loads(content)
        print("\n✅ JSON is valid!")
        print(f"Steps: {len(data.get('steps', []))}")
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Error: {e}")
        print(f"Position: {e.pos}")
        print(f"Line: {e.lineno}, Column: {e.colno}")
        
        # Show context around error
        lines = content.split('\n')
        if e.lineno <= len(lines):
            print(f"\nError on line {e.lineno}:")
            print(f"  {lines[e.lineno - 1]}")
            print(f"  {' ' * (e.colno - 1)}^")
else:
    print("No response from LLM")
