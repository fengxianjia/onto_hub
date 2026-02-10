from sqlalchemy.orm import Session
from .database import SessionLocal
from .services.parsing_service import ParsingService
import logging

logger = logging.getLogger(__name__)

def parse_ontology_task(package_id: str, template_id: str, db: Session = None):
    """
    Background task to parse an ontology.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
        
    try:
        service = ParsingService(db)
        service.parse_package(package_id, template_id)
    except Exception as e:
        logger.error(f"Error in parse_ontology_task: {e}")
    finally:
        if should_close:
            db.close()
