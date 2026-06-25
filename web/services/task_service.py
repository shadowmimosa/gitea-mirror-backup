"""
备份任务服务 - 管理 TaskRun 与 CLI 子进程
"""

import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ..api.config import settings
from ..api.models import Task, TaskRun, User


MANUAL_TASK_NAME = "manual-backup"


class TaskService:
    """备份任务管理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.log_dir = Path(settings.TASK_LOG_DIR)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_or_create_manual_task(self) -> Task:
        task = self.db.query(Task).filter(Task.name == MANUAL_TASK_NAME).first()
        if task:
            return task

        task = Task(
            name=MANUAL_TASK_NAME,
            description="Web 手动触发的备份任务",
            cron_expression="manual",
            is_enabled=True,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_running_task(self) -> Optional[TaskRun]:
        return (
            self.db.query(TaskRun)
            .filter(TaskRun.status == "running")
            .order_by(TaskRun.started_at.desc())
            .first()
        )

    def list_task_runs(self, page: int = 1, page_size: int = 20) -> List[TaskRun]:
        offset = (page - 1) * page_size
        return (
            self.db.query(TaskRun)
            .order_by(TaskRun.started_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

    def count_task_runs(self) -> int:
        return self.db.query(TaskRun).count()

    def get_task_run(self, run_id: int) -> Optional[TaskRun]:
        return self.db.query(TaskRun).filter(TaskRun.id == run_id).first()

    def get_task_log(self, run_id: int, tail_lines: int = 200) -> str:
        run = self.get_task_run(run_id)
        if not run or not run.log_file:
            return ""

        log_path = Path(run.log_file)
        if not log_path.exists():
            return ""

        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            return "\n".join(lines[-tail_lines:])
        except Exception:
            return ""

    def start_backup(
        self, user: User, repository: Optional[str] = None
    ) -> Dict:
        running = self.get_running_task()
        if running:
            return {
                "already_running": True,
                "task_run_id": running.id,
                "status": running.status,
            }

        task = self.get_or_create_manual_task()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file = self.log_dir / f"backup-{timestamp}.log"

        task_run = TaskRun(
            task_id=task.id,
            user_id=user.id,
            status="running",
            log_file=str(log_file),
            repository=repository,
        )
        self.db.add(task_run)
        self.db.commit()
        self.db.refresh(task_run)

        thread = threading.Thread(
            target=self._execute_backup,
            args=(task_run.id, log_file, repository),
            daemon=True,
        )
        thread.start()

        return {
            "already_running": False,
            "task_run_id": task_run.id,
            "status": "running",
            "started_at": task_run.started_at,
            "repository": repository,
        }

    def _execute_backup(
        self, task_run_id: int, log_file: Path, repository: Optional[str]
    ):
        db = self.db
        script_path = Path(settings.BACKUP_SCRIPT_PATH)
        config_path = Path(settings.BACKUP_CONFIG_PATH)

        with open(log_file, "w", encoding="utf-8") as log_fp:
            if repository:
                log_fp.write(f"单仓备份: {repository}\n")

            if not script_path.exists():
                log_fp.write(f"错误: 备份脚本不存在: {script_path}\n")
                self._finish_task_run(task_run_id, "failed", "备份脚本不存在")
                return

            cmd = ["python3", str(script_path), "-c", str(config_path)]
            if repository:
                cmd.extend(["--repo", repository])
            return_code = 1
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=log_fp,
                    stderr=subprocess.STDOUT,
                    cwd=str(script_path.parent),
                )
                return_code = proc.wait()
            except Exception as exc:
                log_fp.write(f"启动备份失败: {exc}\n")
                self._finish_task_run(task_run_id, "failed", str(exc))
                return

        if return_code == 0:
            self._finish_task_run(task_run_id, "success", None)
        else:
            self._finish_task_run(
                task_run_id, "failed", f"备份进程退出码: {return_code}"
            )

    def _finish_task_run(
        self, task_run_id: int, status: str, error_message: Optional[str]
    ):
        from ..api.database import SessionLocal

        session = SessionLocal()
        try:
            run = session.query(TaskRun).filter(TaskRun.id == task_run_id).first()
            if run:
                run.status = status
                run.finished_at = datetime.now()
                run.error_message = error_message
                task = session.query(Task).filter(Task.id == run.task_id).first()
                if task:
                    task.last_run_at = datetime.now()
                session.commit()
        finally:
            session.close()
