import os
import json
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai

# .env 로드
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class SEOAgent:
    def __init__(self):
        self.model = None
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # 분석용이라 똑똑하고 빠른 2.5-flash 사용
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                print(f"❌ SEOAgent Config Error: {e}")

    async def analyze(self, draft: Dict[str, Any], topic_data: Dict[str, Any], platform: str = "Naver") -> Dict[str, Any]:
        """
        작성된 초안(Draft)을 SEO 기준과 플랫폼 성향에 맞춰 평가합니다.
        """
        if not self.model:
            return {"score": 0, "pass": False, "feedback": "Model Error"}

        title = draft.get("final_title", "")
        content = draft.get("content", "")
        keywords = topic_data.get("keywords", [])
        
        print(f"🧐 Analyzing SEO for: {title} ({platform} Style)...")

        # 1. 경쟁 문서 시뮬레이션 (나중에 실제 크롤러로 교체할 부분)
        # 지금은 Agent가 '가상의 경쟁자' 정보를 가지고 있다고 가정합니다.
        competitors = [
            f"{keywords[0]} 완벽 정리",
            f"{keywords[0]} 사용법 A to Z",
            f"요즘 뜨는 {keywords[0]} 트렌드 분석"
        ]

        # 2. SEO 검수 프롬프트
        prompt = f"""
        Act as a strict SEO Consultant.
        
        [Target Info]
        - Platform: {platform} (Naver prefers friendly tone, emojis, personal experience. Google prefers structure, data, H-tags.)
        - Target Keywords: {', '.join(keywords)}
        - Competitor Titles: {', '.join(competitors)}
        
        [Draft Content]
        Title: {title}
        Body Length: {len(content)} chars
        Body Preview: {content[:500]}...
        
        [Task]
        Evaluate the draft based on:
        1. **Keyword Density:** Are keywords used naturally?
        2. **Platform Fit:** Does it match the {platform} style?
        3. **Engagement:** Is the title better than competitors?
        
        Output ONLY a JSON object (no markdown):
        {{
            "score": 85,  // 0-100
            "pass": true, // true if score >= 70
            "feedback": "Specific advice on how to improve..."
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_text)
            
            print(f"✅ Analysis Complete. Score: {result.get('score')}/100")
            return result

        except Exception as e:
            print(f"❌ Error analyzing SEO: {e}")
            return {"score": 0, "pass": False, "feedback": "Analysis failed"}

# 테스트 코드
if __name__ == "__main__":
    # Agent 2의 결과물이라고 가정
    test_draft = {
        "final_title": "내 컴퓨터, AI가 숨쉬는 OS로 변모할까?",
        "content": "안녕하세요! 오늘은 제미나이와 H100에 대해 알아볼게요. 정말 신기한 세상입니다..."
    }
    test_topic = {"keywords": ["GenAI", "AI OS"]}
    
    agent = SEOAgent()
    # 네이버 스타일로 검수 요청
    result = asyncio.run(agent.analyze(test_draft, test_topic, platform="Naver"))
    
    print("\n[SEO Report]")
    print(json.dumps(result, indent=2, ensure_ascii=False))