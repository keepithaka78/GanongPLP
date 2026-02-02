"""
파일 변경 감지 및 자동 업데이트 서비스
"""

import os
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from services.data_loader import DataLoader


class FileWatcher:
    def __init__(self, watch_directory: str):
        """
        파일 감시 초기화

        Args:
            watch_directory: 감시할 디렉토리 경로
        """
        self.watch_directory = Path(watch_directory)
        self.file_timestamps: Dict[str, float] = {}
        self.last_check = datetime.now()

    def get_excel_files(self) -> List[Path]:
        """엑셀 파일 목록 가져오기"""
        return list(self.watch_directory.glob("*.xlsm"))

    def get_file_timestamp(self, file_path: Path) -> float:
        """파일 수정 시간 가져오기"""
        return os.path.getmtime(str(file_path))

    def check_for_changes(self) -> List[Path]:
        """
        파일 변경 감지

        Returns:
            변경된 파일 경로 리스트
        """
        changed_files = []
        current_files = self.get_excel_files()

        for file_path in current_files:
            current_timestamp = self.get_file_timestamp(file_path)
            file_name = file_path.name

            # 새 파일이거나 수정된 파일 감지
            if file_name not in self.file_timestamps:
                self.file_timestamps[file_name] = current_timestamp
                changed_files.append(file_path)
            elif self.file_timestamps[file_name] < current_timestamp:
                self.file_timestamps[file_name] = current_timestamp
                changed_files.append(file_path)

        return changed_files

    def reload_changed_files(self) -> Dict[str, any]:
        """
        변경된 파일 재로드

        Returns:
            업데이트 결과 딕셔너리
        """
        changed_files = self.check_for_changes()

        if not changed_files:
            return {
                "status": "no_changes",
                "message": "변경된 파일이 없습니다.",
                "updated_files": [],
                "timestamp": datetime.now().isoformat()
            }

        # 데이터베이스 세션 생성
        db = SessionLocal()

        try:
            updated_files = []
            errors = []

            for file_path in changed_files:
                try:
                    loader = DataLoader(db)
                    loader.load_file(str(file_path))
                    updated_files.append(file_path.name)
                except Exception as e:
                    errors.append({
                        "file": file_path.name,
                        "error": str(e)
                    })

            db.commit()

            return {
                "status": "success" if not errors else "partial_success",
                "message": f"{len(updated_files)}개 파일 업데이트 완료",
                "updated_files": updated_files,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            db.rollback()
            return {
                "status": "error",
                "message": f"업데이트 실패: {str(e)}",
                "updated_files": [],
                "timestamp": datetime.now().isoformat()
            }
        finally:
            db.close()

    def reload_all_files(self) -> Dict[str, any]:
        """
        모든 파일 강제 재로드

        Returns:
            업데이트 결과 딕셔너리
        """
        all_files = self.get_excel_files()

        if not all_files:
            return {
                "status": "error",
                "message": "엑셀 파일을 찾을 수 없습니다.",
                "updated_files": [],
                "timestamp": datetime.now().isoformat()
            }

        # 데이터베이스 세션 생성
        db = SessionLocal()

        try:
            updated_files = []
            errors = []

            for file_path in all_files:
                try:
                    loader = DataLoader(db)
                    loader.load_file(str(file_path))
                    updated_files.append(file_path.name)

                    # 타임스탬프 업데이트
                    self.file_timestamps[file_path.name] = self.get_file_timestamp(file_path)
                except Exception as e:
                    errors.append({
                        "file": file_path.name,
                        "error": str(e)
                    })

            db.commit()

            return {
                "status": "success" if not errors else "partial_success",
                "message": f"{len(updated_files)}개 파일 재로드 완료",
                "updated_files": updated_files,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            db.rollback()
            return {
                "status": "error",
                "message": f"재로드 실패: {str(e)}",
                "updated_files": [],
                "timestamp": datetime.now().isoformat()
            }
        finally:
            db.close()
