import os
import json
import asyncio
import random
from typing import Dict, Any
from datetime import datetime

# 이미지 처리 및 마크다운 변환 라이브러리
try:
    from PIL import Image
    import markdown
except ImportError:
    print("⚠️ Pillow or markdown not installed. Run: pip install Pillow markdown")

class PublisherAgent:
    def __init__(self):
        pass

    async def execute(self, draft: Dict[str, Any], blog_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        최종 원고를 받아 포맷을 변환하고, 이미지를 세탁한 뒤 배포(를 가장한 처리)를 수행합니다.
        """
        print(f"🚀 Publisher Agent Started for: {draft.get('final_title')}")

        # 1. 포맷 변환 (Markdown -> HTML body)
        body_html = self._convert_to_html(draft.get('content', ''))

        # 1.5 메타 태그 + 본문만 포함하는 HTML 문서 생성
        title = draft.get("final_title") or "Untitled"
        meta_description = draft.get("meta_description") or ""
        meta_keywords = draft.get("meta_keywords") or []
        if not isinstance(meta_keywords, list):
            meta_keywords = [str(meta_keywords)]
        kw = ", ".join([str(k).strip() for k in meta_keywords if str(k).strip()])
        html_content = (
            "<!doctype html>\n"
            "<html lang=\"ko\">\n"
            "<head>\n"
            "  <meta charset=\"utf-8\" />\n"
            f"  <title>{title}</title>\n"
            f"  <meta name=\"description\" content=\"{meta_description}\" />\n"
            f"  <meta name=\"keywords\" content=\"{kw}\" />\n"
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
            "</head>\n"
            "<body>\n"
            f"{body_html}\n"
            "</body>\n"
            "</html>"
        )
        
        # 2. 이미지 세탁 (Exif 제거 시뮬레이션)
        # 실제로는 생성된 이미지 경로를 받아 처리하지만, 여기선 더미 경로로 테스트
        dummy_images = ["image_01.jpg", "image_02.png"] 
        processed_images = self._process_images(dummy_images)

        # NOTE: Reviewer 요구사항에 따라 최종 HTML은 메타+본문만 포함해야 하므로
        # 광고 삽입은 기본적으로 비활성화합니다.

        # 4. 배포 시뮬레이션
        platform = blog_config.get("platform_type", "Naver")
        post_url = f"https://blog.naver.com/{blog_config.get('user_id')}/12345"
        
        print(f"📡 Uploading to {platform}...")
        await asyncio.sleep(1) # 네트워크 딜레이 시뮬레이션

        # 5. 애드온: 색인 자동화 요청
        indexing_result = self._request_indexing(post_url)

        return {
            "status": "published",
            "url": post_url,
            "published_at": datetime.now().isoformat(),
            "html": html_content,
            "addons": {
                "image_processed_count": len(processed_images),
                "ad_injected": False,
                "indexing_status": indexing_result
            }
        }

    def _convert_to_html(self, markdown_text: str) -> str:
        """마크다운을 HTML로 변환"""
        try:
            html = markdown.markdown(markdown_text)
            print("✅ Format Converted: Markdown -> HTML")
            return html
        except Exception:
            return markdown_text

    def _process_images(self, image_paths: list) -> list:
        """
        [핵심] 이미지의 Exif 메타데이터를 제거하여 '유사 이미지' 판독을 회피합니다.
        """
        cleaned_images = []
        print("🧼 Cleaning Image Metadata (Exif)...")
        
        for img_path in image_paths:
            # 실제 파일이 없으므로 로직만 구현 (파일이 있다고 가정)
            try:
                # img = Image.open(img_path)
                # data = list(img.getdata())
                # image_without_exif = Image.new(img.mode, img.size)
                # image_without_exif.putdata(data)
                # image_without_exif.save(f"clean_{img_path}")
                cleaned_images.append(f"clean_{img_path}")
            except Exception:
                pass
        
        print(f"✅ {len(image_paths)} Images sanitized.")
        return cleaned_images

    def _inject_ads(self, content: str, ad_id: str) -> str:
        """본문 중간에 광고 코드를 삽입"""
        ad_code = f'<div class="adsense" data-ad-client="{ad_id}"></div>'
        # 문단이 끝나는 지점(<p> 태그 닫힘)에 랜덤하게 삽입
        if "</p>" in content:
            parts = content.split("</p>")
            # 중간 지점에 광고 삽입
            mid_index = len(parts) // 2
            parts.insert(mid_index, f"</p>{ad_code}")
            print("💰 AdSense Code Injected in the middle of content.")
            return "".join(parts)
        return content

    def _request_indexing(self, url: str) -> str:
        """네이버/구글 색인 API 호출 시뮬레이션"""
        print(f"🔍 Requesting Indexing for: {url}")
        # 실제론 requests.post() 로 Google Indexing API 호출
        return "Submitted to Google & Naver Search Advisor"

# 테스트 코드
if __name__ == "__main__":
    test_draft = {
        "final_title": "내 컴퓨터, AI가 숨쉬는 OS로 변모할까?",
        "content": "# 안녕하세요\n\n이것은 **테스트 본문**입니다.\n\nGenAI는 혁신적입니다."
    }
    test_config = {
        "platform_type": "Naver",
        "user_id": "rich_brother",
        "ad_client_id": "ca-pub-123456789"
    }

    agent = PublisherAgent()
    result = asyncio.run(agent.execute(test_draft, test_config))

    print("\n[Publish Result]")
    print(json.dumps(result, indent=2, ensure_ascii=False))