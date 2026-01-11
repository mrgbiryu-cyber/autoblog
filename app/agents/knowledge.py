from neo4j import GraphDatabase
import datetime


class KnowledgeAgent:
    def __init__(self, db=None):
        self.uri = "bolt://localhost:7687"
        self.user = "neo4j"
        self.password = "password1234"
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    async def update_ontology(self, keyword: str, data: dict):
        print(f"     [Knowledge Graph] Saving nodes into Neo4j for '{keyword}'...")
        query = """
        MERGE (k:Keyword {name: $keyword})
        CREATE (f:Fact {content: $content, source: $source, date: datetime()})
        CREATE (k)-[:HAS_UPDATE]->(f)
        RETURN f
        """
        with self.driver.session() as session:
            session.run(query, keyword=keyword, content=data["content"], source=data["source"])
        return data["content"]

    async def search_ontology(self, query: str) -> str:
        cypher_query = """
        MATCH (k:Keyword)-[:HAS_UPDATE]->(f:Fact)
        WHERE k.name CONTAINS $search_term
        RETURN f.content AS content, f.source AS source
        ORDER BY f.date DESC
        LIMIT 3
        """
        with self.driver.session() as session:
            result = session.run(cypher_query, search_term=query)
            records = [record for record in result]
        if not records:
            return "No specific knowledge found in Graph DB."
        context_text = "\n".join(
            [f"- {r['content']} (Source: {r['source']})" for r in records]
        )
        return context_text
import os
import random
import json
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv  # [수정1] 이거 필수입니다!
from urllib.parse import urlparse

# [수정2] .env 파일 강제 로드
load_dotenv()

import google.generativeai as genai
from neo4j import GraphDatabase

# 환경 변수 로드
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def _normalize_neo4j_uri(uri: str) -> str:
    """
    docker 환경에서 bolt://neo4j:7687 로 설정될 수 있는데,
    단독 실행(또는 GCP) 환경에서는 'neo4j' 호스트가 resolve되지 않아 ServiceUnavailable이 발생합니다.
    """
    try:
        parsed = urlparse(uri)
        if parsed.hostname == "neo4j":
            return f"{parsed.scheme}://localhost:{parsed.port or 7687}"
    except Exception:
        return uri
    return uri


NEO4J_URI = _normalize_neo4j_uri(NEO4J_URI)

class KnowledgeAgent:
    def __init__(self):
        self.model = None  # 초기화
        
        # Gemini 설정
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                print("✅ Gemini API Connected Successfully.")
            except Exception as e:
                print(f"❌ Gemini Configuration Error: {e}")
        else:
            print("⚠️ Warning: GEMINI_API_KEY not found in .env file.")
        
        # Neo4j 드라이버 설정
        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except Exception as e:
            # 로컬 개발 시 Neo4j가 꺼져있어도 죽지 않게 처리
            print(f"⚠️ Neo4j connection warning (Running in standalone mode): {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    async def get_optimized_topic(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        사용자의 페르소나와 현재 트렌드를 분석하여 최적의 글감을 선정합니다.
        """
        category = user_profile.get("category_keywords", ["IT", "Tech"])[0]
        persona = user_profile.get("persona_prompt", "Expert Blogger")
        
        # 모델이 로드되지 않았으면 바로 기본값 반환 (에러 방지)
        if not self.model:
            print("🚫 Gemini Model is not active. Returning fallback topic.")
            return self._get_fallback_topic(category)

        # 1. 트렌드 스캐닝 (Mock)
        raw_trends = self._fetch_realtime_trends(category)
        
        # 2. 탐험 vs 활용 결정
        exploration_rate = 0.1 
        is_exploration = random.random() < exploration_rate
        strategy = "NEW_DISCOVERY" if is_exploration else "DEEP_DIVE"
        print(f"[{category}] Strategy Selected: {strategy}")

        # 3. Gemini 프롬프트
        prompt = f"""
        당신은 전문 콘텐츠 기획자입니다.
        [사용자 프로필] 분야: {category}, 페르소나: {persona}
        [트렌드] {raw_trends}
        [전략] {strategy} ({'새로운 주제 탐험' if is_exploration else '전문성 강화'})
        
        다음 JSON 형식으로 1개의 주제만 출력해줘 (마크다운 없이 순수 JSON만):
        {{
            "topic": "주제 제목",
            "reason": "선정 이유",
            "keywords": ["키워드1", "키워드2"],
            "difficulty": "Tier 1"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            topic_data = json.loads(cleaned_text)
            
            if self.driver:
                self._update_ontology(topic_data['topic'], topic_data['keywords'])
                
            return topic_data

        except Exception as e:
            print(f"❌ Error in generating topic: {e}")
            return self._get_fallback_topic(category)

    def _get_fallback_topic(self, category):
        return {
            "topic": f"{category} 관련 기초 가이드",
            "reason": "시스템 연결 확인 필요 (Fallback)",
            "keywords": [category, "기본", "정보"],
            "difficulty": "Tier 1"
        }

    def _fetch_realtime_trends(self, category: str) -> List[str]:
        mock_db = {
            "AI": ["Gemini 1.5 Pro Launch", "Sora AI Video", "Nvidia H100"],
            "Stock": ["Bitcoin ETF", "Interest Rate Cut", "Tesla Stock"],
        }
        return mock_db.get(category, [f"{category} Latest Trends"])

    def _update_ontology(self, topic: str, keywords: List[str]):
        # Neo4j 로직 (연결 안되면 패스)
        pass

if __name__ == "__main__":
    # 테스트 실행
    test_profile = {"category_keywords": ["AI"], "persona_prompt": "Tech Expert"}
    agent = KnowledgeAgent()
    print("\nFetching Topic...")
    result = asyncio.run(agent.get_optimized_topic(test_profile))
    print(json.dumps(result, indent=2, ensure_ascii=False))