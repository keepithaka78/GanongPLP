"""
자동 업데이트 스케줄러
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from services.file_watcher import FileWatcher
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UpdateScheduler:
    def __init__(self, file_watcher: FileWatcher):
        """
        스케줄러 초기화

        Args:
            file_watcher: FileWatcher 인스턴스
        """
        self.file_watcher = file_watcher
        self.scheduler = BackgroundScheduler()
        self.last_update = None
        self.update_history = []

    def scheduled_update(self):
        """스케줄된 업데이트 실행"""
        try:
            logger.info(f"[스케줄러] 자동 업데이트 시작: {datetime.now().isoformat()}")

            # 변경된 파일만 업데이트
            result = self.file_watcher.reload_changed_files()

            # 업데이트 이력 저장
            self.last_update = datetime.now()
            self.update_history.append({
                "timestamp": self.last_update.isoformat(),
                "status": result["status"],
                "updated_files": result.get("updated_files", []),
                "errors": result.get("errors", [])
            })

            # 이력은 최근 30개만 유지
            if len(self.update_history) > 30:
                self.update_history = self.update_history[-30:]

            logger.info(f"[스케줄러] 업데이트 완료: {result['message']}")

            return result

        except Exception as e:
            logger.error(f"[스케줄러] 업데이트 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def start(self, hour: int = 2, minute: int = 0):
        """
        스케줄러 시작

        Args:
            hour: 실행 시간 (0-23), 기본값 2시
            minute: 실행 분 (0-59), 기본값 0분
        """
        try:
            # 매일 지정된 시간에 실행
            self.scheduler.add_job(
                self.scheduled_update,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_update',
                name='일일 데이터 자동 업데이트',
                replace_existing=True
            )

            self.scheduler.start()
            logger.info(f"[스케줄러] 시작됨 - 매일 {hour:02d}:{minute:02d}에 자동 업데이트")

        except Exception as e:
            logger.error(f"[스케줄러] 시작 실패: {str(e)}")

    def stop(self):
        """스케줄러 중지"""
        try:
            self.scheduler.shutdown()
            logger.info("[스케줄러] 중지됨")
        except Exception as e:
            logger.error(f"[스케줄러] 중지 실패: {str(e)}")

    def get_status(self):
        """
        스케줄러 상태 조회

        Returns:
            스케줄러 상태 정보
        """
        jobs = self.scheduler.get_jobs()

        return {
            "is_running": self.scheduler.running,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "next_run": jobs[0].next_run_time.isoformat() if jobs else None,
            "recent_history": self.update_history[-5:] if self.update_history else []
        }

    def trigger_now(self):
        """즉시 업데이트 실행 (테스트용)"""
        logger.info("[스케줄러] 수동 트리거 실행")
        return self.scheduled_update()
