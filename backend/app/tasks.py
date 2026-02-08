from .database import SessionLocal
from .services.parsing_service import ParsingService
import logging

logger = logging.getLogger(__name__)

def parse_ontology_task(package_id: str, template_id: str):
    """
    Background task to parse an ontology.
    Creates a new DB session for the task.
    """
    db = SessionLocal()
    try:
        service = ParsingService(db)
        service.parse_package(package_id, template_id)
    except Exception as e:
        logger.error(f"Error in parse_ontology_task: {e}")
    finally:
        db.close()
