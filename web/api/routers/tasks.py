"""
任务监控路由
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import TaskRunListResponse, TaskRunResponse, BackupTriggerResponse
from ...utils.auth import get_current_user, get_current_admin_user
from ...services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["任务监控"])


@router.get("", response_model=TaskRunListResponse, summary="获取任务执行记录")
async def list_task_runs(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    items = service.list_task_runs(page=page, page_size=page_size)
    total = service.count_task_runs()
    return TaskRunListResponse(items=items, total=total)


@router.get("/running", response_model=Optional[TaskRunResponse], summary="获取运行中任务")
async def get_running_task(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    run = service.get_running_task()
    return run


@router.get("/{run_id}", response_model=TaskRunResponse, summary="获取任务详情")
async def get_task_run(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    run = service.get_task_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return run


@router.get("/{run_id}/logs", summary="获取任务日志")
async def get_task_logs(
    run_id: int,
    tail: int = 200,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    run = service.get_task_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return {"content": service.get_task_log(run_id, tail_lines=tail)}


@router.post("/backup", response_model=BackupTriggerResponse, summary="触发全量备份")
async def trigger_full_backup(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    result = service.start_backup(user=current_admin)
    if result.get("already_running"):
        return BackupTriggerResponse(
            task_run_id=result["task_run_id"],
            status=result["status"],
            already_running=True,
            message="已有备份任务正在运行",
        )
    return BackupTriggerResponse(
        task_run_id=result["task_run_id"],
        status=result["status"],
        already_running=False,
        message="备份任务已启动",
    )
