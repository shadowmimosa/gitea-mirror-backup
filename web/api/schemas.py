"""
Pydantic 模式定义
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ============ 用户相关 ============


class UserBase(BaseModel):
    """用户基础模式"""

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """创建用户"""

    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """更新用户"""

    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应"""

    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 认证相关 ============


class Token(BaseModel):
    """令牌响应"""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据"""

    username: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""

    username: str
    password: str


# ============ 任务相关 ============


class TaskBase(BaseModel):
    """任务基础模式"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    cron_expression: str
    is_enabled: bool = True


class TaskCreate(TaskBase):
    """创建任务"""

    pass


class TaskUpdate(BaseModel):
    """更新任务"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    is_enabled: Optional[bool] = None


class TaskResponse(TaskBase):
    """任务响应"""

    id: int
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 任务执行记录相关 ============


class TaskRunResponse(BaseModel):
    """任务执行记录响应"""

    id: int
    task_id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    log_file: Optional[str] = None
    error_message: Optional[str] = None
    repository: Optional[str] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class TaskRunListResponse(BaseModel):
    """任务列表响应"""

    items: list[TaskRunResponse]
    total: int


class BackupTriggerResponse(BaseModel):
    """备份触发响应"""

    task_run_id: int
    status: str
    already_running: bool = False
    repository: Optional[str] = None
    message: str


class PasswordChangeRequest(BaseModel):
    """修改密码请求"""

    password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class UserAdminUpdate(BaseModel):
    """管理员更新用户"""

    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class ConfigContentResponse(BaseModel):
    """配置内容响应"""

    content: str
    path: str


class ConfigValidateResponse(BaseModel):
    """配置校验响应"""

    valid: bool
    errors: list[str] = []


class BackupScopeResponse(BaseModel):
    """备份范围配置"""

    organizations: list[str] = []
    check_mirror_only: bool = False
    available_organizations: list[str] = []
    effective_organizations: list[str] = []
    effective_check_mirror_only: bool = False
    warnings: list[str] = []
    config_path: str


class BackupScopeUpdateRequest(BaseModel):
    """更新备份范围"""

    organizations: list[str] = []
    check_mirror_only: bool = False


class NotificationTestRequest(BaseModel):
    """通知测试请求"""

    channel: str = Field(..., description="email, webhook, wechat, dingtalk")


class NotificationTestResponse(BaseModel):
    """通知测试响应"""

    success: bool
    message: str


# ============ 配置相关 ============


class SettingBase(BaseModel):
    """配置基础模式"""

    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class SettingCreate(SettingBase):
    """创建配置"""

    pass


class SettingUpdate(BaseModel):
    """更新配置"""

    value: Optional[str] = None
    description: Optional[str] = None


class SettingResponse(SettingBase):
    """配置响应"""

    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 仪表板相关 ============


class DashboardStats(BaseModel):
    """仪表板统计数据"""

    total_repositories: int
    total_snapshots: int
    protected_snapshots: int = 0
    total_disk_usage: int  # 字节
    last_backup_time: Optional[datetime] = None
    success_rate: float  # 0-100
    failed_backups: int


class DashboardTrend(BaseModel):
    """趋势数据"""

    date: str
    success_count: int
    failed_count: int
    disk_usage: int


# ============ 仓库相关 ============


class RepositoryInfo(BaseModel):
    """仓库信息"""

    name: str
    full_name: str
    owner: str
    description: Optional[str] = None
    last_backup_time: Optional[datetime] = None
    snapshot_count: int
    protected_snapshots: int = 0
    commit_count: int = 0
    disk_usage: int  # 字节
    status: str  # success, warning


class RepositoryDetail(RepositoryInfo):
    """仓库详情"""

    snapshots: list[dict]
    recent_logs: list[str]


# ============ 快照相关 ============


class SnapshotInfo(BaseModel):
    """快照信息"""

    id: str
    repository: str
    created_at: datetime
    size: int  # 字节
    is_protected: bool = False
    status: str


# ============ 报告相关 ============


class ReportInfo(BaseModel):
    """报告信息"""

    filename: str
    created_at: datetime
    size: int
    is_protected: bool = False
    has_alerts: bool = False
    status: str  # normal, alert


class ReportDetail(ReportInfo):
    """报告详情"""

    content: str  # Markdown 内容


# ============ 恢复相关 ============


class RestorePreviewRequest(BaseModel):
    """恢复命令预览请求"""

    repository: str
    snapshot_id: str
    mode: str = "interactive"  # interactive, inplace, export_new, bundle
    new_repo_name: Optional[str] = None
    bundle_path: Optional[str] = None


class RestorePreviewResponse(BaseModel):
    """恢复命令预览响应"""

    repository: str
    snapshot_id: str
    mode: str
    snapshot_path: str
    restore_script_path: str
    host_repo_path: str
    container_repo_path: str
    is_docker: bool
    commands: list[str]
    warnings: list[str]
    notes: list[str]
    archives: list[str] = []


# ============ 通用响应 ============


class MessageResponse(BaseModel):
    """消息响应"""

    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""

    error: str
    detail: Optional[str] = None
