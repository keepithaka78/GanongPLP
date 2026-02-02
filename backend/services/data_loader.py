"""
엑셀 데이터를 데이터베이스로 로드하는 로직
"""

import os
import sys
from datetime import datetime
from typing import List, Dict

# 부모 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, init_db
from models import FileMetadata, LayerDaily, PulletDaily
from services.excel_parser import ExcelParser
import pandas as pd


class DataLoader:
    """데이터 로더 클래스"""

    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal()

    def load_file(self, file_path: str) -> bool:
        """
        단일 파일 로드

        Args:
            file_path: 엑셀 파일 경로

        Returns:
            성공 여부
        """
        try:
            print(f"\n[INFO] 파일 로드 시작: {os.path.basename(file_path)}")

            # 파서로 데이터 읽기
            parser = ExcelParser(file_path)
            data = parser.parse_all()

            # 파일 메타데이터 저장
            file_meta = self._save_file_metadata(data['metadata'])

            # Layer-Daily 데이터 저장
            if not data['layer_daily'].empty:
                self._save_layer_daily(file_meta.id, data['layer_daily'])

            # Pullet-Daily 데이터 저장
            if not data['pullet_daily'].empty:
                self._save_pullet_daily(file_meta.id, data['pullet_daily'])

            self.db.commit()
            print(f"[OK] 파일 로드 완료: {os.path.basename(file_path)}")
            return True

        except Exception as e:
            print(f"[ERROR] 파일 로드 실패: {e}")
            self.db.rollback()
            return False

    def _save_file_metadata(self, metadata: Dict) -> FileMetadata:
        """파일 메타데이터 저장"""
        # 기존 파일 확인
        existing = self.db.query(FileMetadata).filter_by(
            filename=metadata['filename']
        ).first()

        if existing:
            # 업데이트
            existing.pullet_house = metadata['pullet_house']
            existing.pullet_batch = metadata['pullet_batch']
            existing.layer_house = metadata['layer_house']
            existing.layer_batch = metadata['layer_batch']
            existing.file_path = metadata['file_path']
            existing.last_modified = datetime.now()
            print(f"  - 파일 메타데이터 업데이트: {metadata['filename']}")
            return existing
        else:
            # 새로 생성
            file_meta = FileMetadata(**metadata)
            self.db.add(file_meta)
            self.db.flush()  # ID 생성
            print(f"  - 파일 메타데이터 생성: {metadata['filename']}")
            return file_meta

    def _save_layer_daily(self, file_id: int, df: pd.DataFrame):
        """Layer-Daily 데이터 저장"""
        # 기존 데이터 삭제 (전체 교체 방식)
        self.db.query(LayerDaily).filter_by(file_id=file_id).delete()

        # 컬럼 매핑 (엑셀 컬럼명 -> DB 컬럼명)
        column_mapping = {
            'Unnamed: 1': 'week_age',
            'Unnamed: 2': 'record_date',
            'Unnamed: 3': 'age_day',
            '현재수수': 'current_count',
            '폐사': 'mortality_count',
            '도태': 'culling_count',
            '폐사율': 'mortality_rate',
            'HH산란율': 'laying_rate',
            '파란율': 'broken_egg_rate',
            '일일공급량(kg)': 'feed_intake',
            '왕란': 'egg_production',  # 왕란 컬럼을 egg_production으로 매핑
        }

        # 왕란 데이터가 있는 행만 필터링
        if '왕란' in df.columns:
            df = df[df['왕란'].notna()]

        records = []
        for _, row in df.iterrows():
            record_data = {'file_id': file_id}

            for excel_col, db_col in column_mapping.items():
                if excel_col in df.columns:
                    value = row[excel_col]
                    # NaN 처리
                    if pd.isna(value):
                        value = None
                    # 날짜 처리
                    elif db_col == 'record_date' and isinstance(value, datetime):
                        value = value.date()
                    record_data[db_col] = value

            records.append(LayerDaily(**record_data))

        self.db.bulk_save_objects(records)
        print(f"  - Layer-Daily 데이터 저장: {len(records)}행")

    def _save_pullet_daily(self, file_id: int, df: pd.DataFrame):
        """Pullet-Daily 데이터 저장"""
        # 기존 데이터 삭제
        self.db.query(PulletDaily).filter_by(file_id=file_id).delete()

        column_mapping = {
            '일령': 'age_day',
            '날짜': 'record_date',
            '현재수수': 'current_count',
            '폐사': 'mortality_count',
            '도태': 'culling_count',
            '폐사율': 'mortality_rate',
        }

        records = []
        for _, row in df.iterrows():
            record_data = {'file_id': file_id}

            for excel_col, db_col in column_mapping.items():
                if excel_col in df.columns:
                    value = row[excel_col]
                    if pd.isna(value):
                        value = None
                    elif db_col == 'record_date' and isinstance(value, datetime):
                        value = value.date()
                    record_data[db_col] = value

            records.append(PulletDaily(**record_data))

        self.db.bulk_save_objects(records)
        print(f"  - Pullet-Daily 데이터 저장: {len(records)}행")

    def load_all_files(self, folder_path: str) -> Dict[str, int]:
        """
        폴더 내 모든 엑셀 파일 로드

        Args:
            folder_path: 엑셀 파일들이 있는 폴더 경로

        Returns:
            결과 통계
        """
        import glob

        pattern = os.path.join(folder_path, "*.xlsm")
        files = glob.glob(pattern)

        print(f"\n{'='*60}")
        print(f"전체 파일 로드 시작")
        print(f"폴더: {folder_path}")
        print(f"파일 수: {len(files)}")
        print(f"{'='*60}")

        success_count = 0
        fail_count = 0

        for file_path in files:
            if self.load_file(file_path):
                success_count += 1
            else:
                fail_count += 1

        print(f"\n{'='*60}")
        print(f"전체 로드 완료")
        print(f"  성공: {success_count}")
        print(f"  실패: {fail_count}")
        print(f"{'='*60}\n")

        return {
            'success': success_count,
            'fail': fail_count,
            'total': len(files)
        }

    def close(self):
        """세션 종료"""
        self.db.close()


def main():
    """메인 함수 - 전체 파일 로드"""
    # 데이터베이스 초기화
    init_db()

    # 모델 테이블 생성
    from models import create_tables
    create_tables()

    # 데이터 로더 생성
    loader = DataLoader()

    # 전체 파일 로드
    folder_path = r"C:\Users\yimmj\OneDrive\Desktop\산란기록부 Renewal\PLP가농바이오\현재 계군"
    result = loader.load_all_files(folder_path)

    # 통계 확인
    db = SessionLocal()
    file_count = db.query(FileMetadata).count()
    layer_count = db.query(LayerDaily).count()
    pullet_count = db.query(PulletDaily).count()

    print(f"\n[INFO] 데이터베이스 통계:")
    print(f"  - 파일 수: {file_count}")
    print(f"  - Layer-Daily 레코드: {layer_count}")
    print(f"  - Pullet-Daily 레코드: {pullet_count}")

    db.close()
    loader.close()


if __name__ == "__main__":
    main()
