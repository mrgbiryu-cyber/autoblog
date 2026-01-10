import os
import json
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai

# .env 로드
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class WriterAgent:
    def __init__(self):
        self.model = None
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # 형님, 아까 성능 좋았던 2.5-flash로 통일합니다!
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                print(f"❌ WriterAgent Config Error: {e}")
        else:
            print("⚠️ GEMINI_API_KEY missing.")

    async def write_content(self, topic_data: Dict[str, Any], persona: str) -> Dict[str, Any]:
        """
        주제(Topic)와 페르소나를 받아 실제 블로그 포스팅 콘텐츠를 생성합니다.
        """
        if not self.model:
            return {"error": "Model not loaded"}

        topic = topic_data.get("topic", "")
        keywords = topic_data.get("keywords", [])
        
        print(f"✍️ Writing content for: {topic}...")

        # 1. 콘텐츠 작성 프롬프트
        prompt = f"""
        Act as a professional blog writer.
        
        [Author Persona]
        {persona}
        
        [Topic Info]
        - Title: {topic}
        - Keywords: {', '.join(keywords)}
        - Goal: Write a high-quality blog post optimized for SEO.
        
        [Requirements]
        1. **Title:** Create a catchy, click-worthy title (different from the topic).
        2. **Structure:** Introduction -> Body (H2, H3) -> Conclusion.
        3. **Format:** Use Markdown. Use bullet points for readability.
        4. **Image Prompts:** Provide 6 detailed prompts for generating images (DALL-E 3 style) relevant to the content sections.
        
        Output ONLY a JSON object with this format (no markdown code blocks):
        {{
            "final_title": "Your Catchy Title Here",
            "content": "Full markdown content here...",
            "image_prompts": [
                "Detailed prompt for intro image...",
                "Detailed prompt for section 1...",
                "Detailed prompt for section 2...",
                "Detailed prompt for section 3...",
                "Detailed prompt for conclusion...",
                "Detailed prompt for thumbnail..."
            ]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_text)
            
            print("✅ Content generation complete.")
            return result

        except Exception as e:
            print(f"❌ Error writing content: {e}")
            return {
                "final_title": topic,
                "content": "Error generating content. Please try again.",
                "image_prompts": []
            }

    async def rewrite(self, original_draft: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        [NEW] SEO 분석가의 피드백을 반영하여 원고를 수정합니다.
        """
        print(f"♻️ Rewriting content based on feedback: {feedback[:50]}...")
        
        prompt = f"""
        Act as a professional editor.
        
        [Original Draft]
        Title: {original_draft.get('final_title')}
        Content: {original_draft.get('content')}
        
        [Critical Feedback from SEO Analyst]
        "{feedback}"
        
        [Task]
        Rewrite the content to address the feedback strictly. 
        Maintain the original persona but fix the issues (e.g., insert missing keywords, adjust tone).
        
        Output ONLY JSON:
        {{
            "final_title": "Revised Title",
            "content": "Revised Markdown Content...",
            "image_prompts": ["Keep original or update if needed..."]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_text)
        except Exception as e:
            print(f"❌ Error rewriting content: {e}")
            return original_draft

# 테스트 코드
if __name__ == "__main__":
    # Agent 1에서 나온 결과라고 가정하고 테스트
    test_topic_data = {
        "topic": "The Future of Generative AI OS",
        "keywords": ["GenAI", "Gemini", "H100"]
    }
    test_persona = "친절하고 전문적인 IT 리뷰어. 복잡한 기술을 쉽게 설명함."
    
    agent = WriterAgent()
    result = asyncio.run(agent.write_content(test_topic_data, test_persona))
    
    print("\n[Result Preview]")
    print(f"Title: {result.get('final_title')}")
    print(f"Image Prompts: {len(result.get('image_prompts', []))} generated")
    print("Content Length:", len(result.get('content', '')))