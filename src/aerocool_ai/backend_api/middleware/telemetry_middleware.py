"""FastAPI Asynchronous Telemetry & Performance Middleware."""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from aerocool_ai.backend_api.auth import decode_access_token
from aerocool_ai.database.connection import get_session_factory
from aerocool_ai.database.repositories.telemetry_repository import TelemetryRepository

logger = logging.getLogger(__name__)


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Middleware capturing request execution latency, status codes, and user context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        user_id = None
        user_role = "anonymous"

        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = decode_access_token(token)
                user_id = payload.get("sub")
                user_role = payload.get("role", "customer")
            except Exception:
                pass

        error_message = None
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            error_message = str(exc)
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Exclude asset static files to avoid cluttering telemetry logs
            path = request.url.path
            if not path.startswith(("/assets", "/docs", "/redoc", "/openapi.json")) and not path.endswith((".js", ".css", ".ico", ".png", ".jpg")):
                client_ip = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")

                try:
                    session_factory = get_session_factory()
                    async with session_factory() as session:
                        async with session.begin():
                            telemetry_repo = TelemetryRepository(session)
                            await telemetry_repo.log_event(
                                endpoint=path,
                                method=request.method,
                                status_code=status_code,
                                duration_ms=duration_ms,
                                user_id=user_id,
                                user_role=user_role,
                                ip_address=client_ip,
                                user_agent=user_agent,
                                error_message=error_message,
                            )
                except Exception as log_err:
                    logger.debug(f"Telemetry log failed: {log_err}")

        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response
