from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from tortoise.exceptions import (
    IntegrityError,
    DoesNotExist,
    ValidationError,
    OperationalError,
)

if TYPE_CHECKING:
    from nexios import NexiosApp
    from nexios.http import Request, Response

logger = logging.getLogger("nexios.tortoise.exceptions")


def handle_tortoise_exceptions(app: "NexiosApp") -> None:

    @app.add_exception_handler(IntegrityError)
    async def handle_integrity(request: Request, response: Response, exc: IntegrityError):
        logger.warning(f"Tortoise IntegrityError: {exc}")
        return response.status(400).json({
            "error": "Integrity constraint violation",
            "detail": str(exc),
            "type": "integrity_error"
        })

    @app.add_exception_handler(DoesNotExist)
    async def handle_not_found(request: Request, response: Response, exc: DoesNotExist):
        logger.info(f"Tortoise DoesNotExist: {exc}")
        return response.status(404).json({
            "error": "Record not found",
            "detail": str(exc),
            "type": "not_found_error"
        })

    @app.add_exception_handler(ValidationError)
    async def handle_validation(request: Request, response: Response, exc: ValidationError):
        logger.warning(f"Tortoise ValidationError: {exc}")
        return response.status(422).json({
            "error": "Validation failed",
            "detail": str(exc),
            "type": "validation_error"
        })

    @app.add_exception_handler(OperationalError)
    async def handle_operational(request: Request, response: Response, exc: OperationalError):
        logger.error(f"Tortoise OperationalError: {exc}")
        return response.status(503).json({
            "error": "Database operational error",
            "detail": "Service temporarily unavailable",
            "type": "operational_error"
        })

    logger.info("Tortoise exception handlers (4 types) registered.")
