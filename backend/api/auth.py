from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from datetime import timedelta
from typing import Optional
from core.database import get_session
from core.security import verify_password, get_password_hash, create_access_token, verify_token
from core.config import settings
from core.audit_logging import get_audit_logger, AuditAction
from core.error_handling import create_secure_http_exception, ErrorCode, raise_security_error
from models.user import User, UserRole
from schemas.auth import Token, TokenData, UserLogin, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    request: Request,
    session: Session = Depends(get_session)
):
    """Login with email and password"""
    
    audit_logger = get_audit_logger()
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Find user by email
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        # Log failed authentication attempt
        audit_logger.log_authentication_failure(
            email=login_data.email,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="Invalid credentials"
        )
        raise create_secure_http_exception(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid credentials provided",
            error_code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            details={"field": "email"}
        )
    
    if not user.is_active:
        # Log failed authentication attempt
        audit_logger.log_authentication_failure(
            email=login_data.email,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="Account inactive"
        )
        raise create_secure_http_exception(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Account is inactive",
            error_code=ErrorCode.AUTH_ACCOUNT_INACTIVE,
            details={"field": "account_status"}
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    # Log successful authentication
    audit_logger.log_authentication_success(
        user_id=user.id,
        user_email=user.email,
        user_role=user.role,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """Refresh access token"""
    
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user data
        statement = select(User).where(User.id == int(user_id))
        user = session.exec(statement).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user_id, "email": payload.get("email"), "role": payload.get("role")},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.post("/logout")
async def logout():
    """Logout (client should discard token)"""
    return {"message": "Successfully logged out"}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """Get current authenticated user"""
    
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        statement = select(User).where(User.id == int(user_id))
        user = session.exec(statement).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
