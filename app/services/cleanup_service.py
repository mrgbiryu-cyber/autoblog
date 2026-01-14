import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.sql_models import Post
from app.core.database import SessionLocal

LOGGER = logging.getLogger("cleanup_service")

def cleanup_old_posts():
    """
    7일이 지난 포스트와 관련 이미지 파일을 삭제합니다.
    """
    db = SessionLocal()
    try:
        seven_days_ago = datetime.now() - timedelta(days=7)
        old_posts = db.query(Post).filter(Post.created_at < seven_days_ago).all()
        
        count = 0
        for post in old_posts:
            # 이미지 파일 삭제
            if post.image_paths:
                for path in post.image_paths:
                    if path.startswith("/generated_images/"):
                        filename = path.replace("/generated_images/", "")
                        file_path = Path("static/generated_images") / filename
                        try:
                            if file_path.exists():
                                os.remove(file_path)
                                LOGGER.info(f"Deleted old image: {file_path}")
                        except Exception as e:
                            LOGGER.error(f"Failed to delete image {file_path}: {e}")
            
            # DB 레코드 삭제
            db.delete(post)
            count += 1
            
        db.commit()
        if count > 0:
            LOGGER.info(f"Cleaned up {count} old posts and their images.")
    except Exception as e:
        LOGGER.error(f"Cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()

