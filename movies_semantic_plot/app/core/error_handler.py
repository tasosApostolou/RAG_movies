"""
Error Handler Middleware
========================
Centralized error handling for the API.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from openai import APIError, APIConnectionError, APITimeoutError

class ErrorResponse(BaseModel):
    """Standard error response"""
    error_type: str = Field(..., description="Error-type-format error_status_case like REQUEST_LIMIT_429_AI_CALL")

    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(default=None, description="Additional details")

class RateLimitError(Exception):
    def __init__(
        self, 
        message: str, 
        code: int = 429, 
        case: str = "AI_CALL", 
        limit: str = "RATE_LIMIT",
        retry: int = 60
    ):
        self.message = message
        self.code = code
        self.case = case
        self.limit = limit
        self.retry = retry      

        # RATE_LIMIT_429_AI_CALL | REQUEST_LIMIT_429_AI_CALL | TOKEN_LIMIT_429_AI_CALL
        self.error_type = f"{self.limit}_{self.code}_{self.case}"  
        super().__init__(self.message)

class RequestLimitError(RateLimitError):
    def __init__(self, message: str, **kwargs):
        # type_error = REQUEST_LIMIT_429_AI_CALL
        super().__init__(
            message=message, limit="REQUEST_LIMIT", **kwargs)

# class TokenLimitError(RateLimitError):
#     def __init__(self, message: str, **kwargs):
#         super().__init__(message=message, limit="TOKEN_LIMIT", **kwargs)



logger = logging.getLogger(__name__)




def setup_error_handlers(app: FastAPI):
    """Configure error handlers for the FastAPI application"""
    
    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError):
        """Handle OpenAI rate limit errors"""
        logger.warning(f"Rate limit exceeded: {exc}")
        return JSONResponse(
            status_code=exc.code,
            content=ErrorResponse(
                error_type=exc.error_type,
                message=exc.message,
                details={"retry_after": exc.retry}
            ).model_dump()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_request",
                "issues": [
                    {
                        "field": ".".join(map(str, e["loc"][1:])),
                        "msg": e["msg"],
                    }
                    for e in exc.errors()
                ],
            },
        )    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_type="HTTP_ERROR",
                message=exc.detail,
                details=None
            ).model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.exception(f"Unexpected error: {exc}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_type="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred.",
                details=None
            ).model_dump()
        )