"""
认证路由
"""

from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import (
    LoginRequest,
    Token,
    UserResponse,
    UserCreate,
    PasswordChangeRequest,
    UserAdminUpdate,
    MessageResponse,
)
from ...utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_current_admin_user,
)
from ..config import settings

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Token, summary="用户登录")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码
    """
    # 查找用户
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户已被禁用"
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息"""
    return current_user


@router.post("/register", response_model=UserResponse, summary="注册新用户")
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """
    注册新用户（仅管理员可用）

    - **username**: 用户名（3-50字符）
    - **email**: 邮箱（可选）
    - **password**: 密码（至少6字符）
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被使用"
            )

    # 创建新用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_admin=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/users", response_model=List[UserResponse], summary="获取用户列表")
async def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """获取所有用户（仅管理员）"""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.put("/users/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """管理员更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if user_data.email is not None:
        user.email = user_data.email
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.is_admin is not None:
        if user.id == current_admin.id and not user_data.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能取消自己的管理员权限",
            )
        user.is_admin = user_data.is_admin

    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password", response_model=MessageResponse, summary="修改密码")
async def change_password(
    body: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前用户修改自己的密码"""
    if not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误"
        )

    current_user.hashed_password = get_password_hash(body.new_password)
    db.commit()
    return MessageResponse(message="密码修改成功")
