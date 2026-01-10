from app.agents.base import BaseAgent
from typing import Dict, Any

class WriterAgent(BaseAgent):
    """
    Agent 2: Creative Writer (Content Gen)
    Role: Generates content using Gemini 1.5 Pro.
    """
    
    async def write_content(self, topic: str, persona_prompt: str) -> Dict[str, Any]:
        """
        Logic:
        1. Persona Injection: Prepends user_presets.persona_prompt to system prompt.
        2. Hooking Engine: Generates 5 title variations.
        3. Multi-modal: Generates 6 detailed image prompts.
        """
        print(f"WriterAgent: Writing content on '{topic}' with persona '{persona_prompt}'")
        
        # Placeholder content generation
        draft_content = f"# {topic}\n\nThis is a draft article written by AI..."
        
        return {
            "title": f"Why {topic} Matters",
            "content": draft_content,
            "image_prompts": ["A futuristic robot writing a blog post"]
        }

    async def rewrite(self, draft: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        print(f"WriterAgent: Rewriting content based on feedback: {feedback}")
        draft["content"] += f"\n\n[Revised based on feedback: {feedback}]"
        return draft

    async def execute(self, topic: str, persona_prompt: str) -> Dict[str, Any]:
        return await self.write_content(topic, persona_prompt)
