"""
FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import get_db, init_db
from models import FileMetadata, LayerDaily, PulletDaily
from services.file_watcher import FileWatcher
from services.scheduler import UpdateScheduler
from typing import List, Dict
from datetime import datetime
import os
import glob
import shutil
from pathlib import Path

# FastAPI 앱 생성
app = FastAPI(
    title="가농바이오 양계 대시보드 API",
    description="PLP Report 데이터 분석 및 시각화 API",
    version="1.0.0"
)

# 정적 파일 경로
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# 엑셀 파일 경로 (환경 변수 또는 기본값 사용)
EXCEL_DIR = os.environ.get("EXCEL_DIR", r"C:\Users\yimmj\OneDrive\Desktop\산란기록부 Renewal\PLP가농바이오\현재 계군")

# 클라우드 환경 감지 (엑셀 파일이 없으면 클라우드로 판단)
IS_CLOUD = not os.path.exists(EXCEL_DIR)

# 파일 감시자 및 스케줄러 초기화 (로컬 환경에서만)
if not IS_CLOUD:
    file_watcher = FileWatcher(EXCEL_DIR)
    scheduler = UpdateScheduler(file_watcher)
else:
    file_watcher = None
    scheduler = None
    print("[INFO] 클라우드 환경 감지 - 파일 감시 및 스케줄러 비활성화")

# CORS 설정 (프론트엔드 연결 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """서버 시작 시 데이터베이스 초기화"""
    init_db()

    # 로컬 환경에서만 스케줄러 시작
    if scheduler:
        scheduler.start(hour=2, minute=0)
        print("[OK] 스케줄러 시작 (로컬 환경)")

    print("[OK] FastAPI 서버 시작")


@app.on_event("shutdown")
def shutdown_event():
    """서버 종료 시 스케줄러 정리"""
    if scheduler:
        scheduler.stop()
    print("[OK] FastAPI 서버 종료")


@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """헬스 체크"""
    file_count = db.query(FileMetadata).count()
    layer_count = db.query(LayerDaily).count()
    pullet_count = db.query(PulletDaily).count()

    return {
        "status": "healthy",
        "database": "connected",
        "statistics": {
            "files": file_count,
            "layer_records": layer_count,
            "pullet_records": pullet_count
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/files")
def get_files(db: Session = Depends(get_db)):
    """파일 목록 조회"""
    files = db.query(FileMetadata).all()

    return {
        "total": len(files),
        "files": [
            {
                "id": f.id,
                "filename": f.filename,
                "pullet_house": f.pullet_house,
                "pullet_batch": f.pullet_batch,
                "layer_house": f.layer_house,
                "layer_batch": f.layer_batch,
                "last_modified": f.last_modified.isoformat() if f.last_modified else None
            }
            for f in files
        ]
    }


@app.get("/api/layer/summary")
def get_layer_summary(
    house: str = None,
    batch: str = None,
    db: Session = Depends(get_db)
):
    """
    산란계 전체 요약 통계

    Args:
        house: 필터링할 동 (예: "1동", "6동")
        batch: 필터링할 차수 (예: "8차", "9차")
    """
    # 파일별 최신 데이터 가져오기 (산란율이 있는 데이터만)
    from sqlalchemy import func, and_

    # 각 파일의 최신 레코드 조회 (산란율이 null이 아닌 것 중)
    subquery = db.query(
        LayerDaily.file_id,
        func.max(LayerDaily.age_day).label('max_age')
    ).filter(LayerDaily.laying_rate.isnot(None)).group_by(LayerDaily.file_id).subquery()

    latest_records = db.query(LayerDaily).join(
        subquery,
        and_(
            LayerDaily.file_id == subquery.c.file_id,
            LayerDaily.age_day == subquery.c.max_age
        )
    ).all()

    # 파일 정보 조인 및 필터링
    result = []
    for record in latest_records:
        file_info = db.query(FileMetadata).filter_by(id=record.file_id).first()
        if file_info:
            # 동/차수 필터링
            if house and file_info.layer_house != house:
                continue
            if batch and file_info.layer_batch != batch:
                continue
            # 데이터베이스에 이미 퍼센트로 저장되어 있으므로 그대로 사용
            laying_rate = record.laying_rate if record.laying_rate else 0
            mortality_rate = record.mortality_rate if record.mortality_rate else 0
            broken_egg_rate = record.broken_egg_rate if record.broken_egg_rate else 0

            # 수당 사료섭취량 계산 (g 단위)
            feed_per_bird = 0
            if record.feed_intake and record.current_count and record.current_count > 0:
                feed_per_bird = (record.feed_intake * 1000) / record.current_count

            result.append({
                "house": file_info.layer_house,
                "batch": file_info.layer_batch,
                "age_day": record.age_day,
                "laying_rate": laying_rate,
                "mortality_rate": mortality_rate,
                "broken_egg_rate": broken_egg_rate,
                "current_count": record.current_count,
                "feed_per_bird": feed_per_bird,
                "record_date": record.record_date.isoformat() if record.record_date else None
            })

    return {
        "total_houses": len(result),
        "data": result
    }


@app.get("/api/layer/compare")
def compare_layer_by_age(age_day: int, db: Session = Depends(get_db)):
    """
    특정 일령의 동별 산란계 성적 비교

    Args:
        age_day: 일령 (예: 120)
    """
    records = db.query(LayerDaily, FileMetadata).join(
        FileMetadata, LayerDaily.file_id == FileMetadata.id
    ).filter(LayerDaily.age_day == age_day).all()

    result = []
    for record, file_meta in records:
        # 데이터베이스에 이미 퍼센트로 저장되어 있으므로 그대로 사용
        laying_rate = record.laying_rate if record.laying_rate else 0
        mortality_rate = record.mortality_rate if record.mortality_rate else 0
        broken_egg_rate = record.broken_egg_rate if record.broken_egg_rate else 0

        # 수당 사료섭취량 계산 (g 단위)
        feed_per_bird = 0
        if record.feed_intake and record.current_count and record.current_count > 0:
            feed_per_bird = (record.feed_intake * 1000) / record.current_count  # kg를 g으로 변환 후 나누기

        result.append({
            "house": file_meta.layer_house,
            "batch": file_meta.layer_batch,
            "age_day": record.age_day,
            "laying_rate": laying_rate,
            "mortality_rate": mortality_rate,
            "broken_egg_rate": broken_egg_rate,
            "current_count": record.current_count,
            "feed_intake": record.feed_intake,
            "feed_per_bird": feed_per_bird
        })

    return {
        "age_day": age_day,
        "total_houses": len(result),
        "data": result
    }


@app.get("/api/layer/age-range")
def get_age_range(db: Session = Depends(get_db)):
    """
    전체 데이터의 일령 범위 조회 (비교 차트용)
    """
    from sqlalchemy import func

    result = db.query(
        func.min(LayerDaily.age_day).label('min_age'),
        func.max(LayerDaily.age_day).label('max_age')
    ).filter(LayerDaily.laying_rate.isnot(None)).first()

    return {
        "min_age": result.min_age if result else 0,
        "max_age": result.max_age if result else 0
    }


@app.get("/api/layer/filter-options")
def get_filter_options(db: Session = Depends(get_db)):
    """
    필터링 옵션 조회 (동, 차수 목록)
    """
    files = db.query(FileMetadata).all()

    houses = sorted(list(set(f.layer_house for f in files if f.layer_house)))
    batches = sorted(list(set(f.layer_batch for f in files if f.layer_batch)))

    return {
        "houses": houses,
        "batches": batches
    }


@app.get("/api/layer/search")
def search_layer_data(
    house: str = None,
    batch: str = None,
    start_date: str = None,
    end_date: str = None,
    min_age: int = None,
    max_age: int = None,
    db: Session = Depends(get_db)
):
    """
    산란계 데이터 검색

    Args:
        house: 동 필터 (예: "1동")
        batch: 차수 필터 (예: "8차")
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        min_age: 최소 일령
        max_age: 최대 일령
    """
    from sqlalchemy import and_
    from datetime import datetime as dt

    # 파일 필터링
    file_query = db.query(FileMetadata)
    if house:
        file_query = file_query.filter(FileMetadata.layer_house == house)
    if batch:
        file_query = file_query.filter(FileMetadata.layer_batch == batch)

    files = file_query.all()
    file_ids = [f.id for f in files]

    if not file_ids:
        return {
            "total": 0,
            "data": []
        }

    # 데이터 필터링
    data_query = db.query(LayerDaily).filter(LayerDaily.file_id.in_(file_ids))

    if start_date:
        data_query = data_query.filter(LayerDaily.record_date >= dt.fromisoformat(start_date))
    if end_date:
        data_query = data_query.filter(LayerDaily.record_date <= dt.fromisoformat(end_date))
    if min_age:
        data_query = data_query.filter(LayerDaily.age_day >= min_age)
    if max_age:
        data_query = data_query.filter(LayerDaily.age_day <= max_age)

    records = data_query.order_by(LayerDaily.record_date.desc()).limit(100).all()

    # 결과 조합
    result = []
    for record in records:
        file_info = db.query(FileMetadata).filter_by(id=record.file_id).first()
        if file_info:
            laying_rate = record.laying_rate if record.laying_rate else 0
            mortality_rate = record.mortality_rate if record.mortality_rate else 0
            broken_egg_rate = record.broken_egg_rate if record.broken_egg_rate else 0

            feed_per_bird = 0
            if record.feed_intake and record.current_count and record.current_count > 0:
                feed_per_bird = (record.feed_intake * 1000) / record.current_count

            result.append({
                "house": file_info.layer_house,
                "batch": file_info.layer_batch,
                "age_day": record.age_day,
                "record_date": record.record_date.isoformat() if record.record_date else None,
                "laying_rate": laying_rate,
                "mortality_rate": mortality_rate,
                "broken_egg_rate": broken_egg_rate,
                "current_count": record.current_count,
                "feed_per_bird": feed_per_bird,
                "egg_production": record.egg_production
            })

    return {
        "total": len(result),
        "filters": {
            "house": house,
            "batch": batch,
            "start_date": start_date,
            "end_date": end_date,
            "min_age": min_age,
            "max_age": max_age
        },
        "data": result
    }


@app.get("/api/layer/trends")
def get_layer_trends(file_id: int, db: Session = Depends(get_db)):
    """
    특정 파일의 일령별 추이 데이터

    Args:
        file_id: 파일 ID
    """
    from sqlalchemy import and_

    # 파일 정보 조회
    file_info = db.query(FileMetadata).filter_by(id=file_id).first()
    if not file_info:
        return {"error": "File not found"}

    # 일령별 데이터 조회 (산란율이 있는 데이터만)
    records = db.query(LayerDaily).filter(
        and_(
            LayerDaily.file_id == file_id,
            LayerDaily.laying_rate.isnot(None)
        )
    ).order_by(LayerDaily.age_day).all()

    # 데이터 변환
    result = []
    for record in records:
        # 데이터베이스에 이미 퍼센트로 저장되어 있으므로 그대로 사용
        laying_rate = record.laying_rate if record.laying_rate else 0
        mortality_rate = record.mortality_rate if record.mortality_rate else 0
        broken_egg_rate = record.broken_egg_rate if record.broken_egg_rate else 0

        # 수당 사료섭취량 계산 (g 단위)
        feed_per_bird = 0
        if record.feed_intake and record.current_count and record.current_count > 0:
            feed_per_bird = (record.feed_intake * 1000) / record.current_count

        result.append({
            "age_day": record.age_day,
            "record_date": record.record_date.isoformat() if record.record_date else None,
            "laying_rate": laying_rate,
            "mortality_rate": mortality_rate,
            "broken_egg_rate": broken_egg_rate,
            "current_count": record.current_count,
            "feed_intake": record.feed_intake,
            "feed_per_bird": feed_per_bird,
            "egg_production": record.egg_production
        })

    return {
        "file_info": {
            "id": file_info.id,
            "house": file_info.layer_house,
            "batch": file_info.layer_batch,
            "filename": file_info.filename
        },
        "total_records": len(result),
        "data": result
    }


@app.post("/api/admin/reload-data")
def reload_data(force: bool = False):
    """
    데이터 새로고침

    Args:
        force: True일 경우 모든 파일 강제 재로드, False일 경우 변경된 파일만 로드
    """
    if IS_CLOUD:
        return {
            "status": "unavailable",
            "message": "클라우드 환경에서는 데이터 새로고침을 사용할 수 없습니다",
            "timestamp": datetime.now().isoformat()
        }

    try:
        if force:
            result = file_watcher.reload_all_files()
        else:
            result = file_watcher.reload_changed_files()

        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"데이터 새로고침 실패: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/admin/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    """
    엑셀 파일 업로드 및 데이터베이스 갱신

    Args:
        file: 업로드할 엑셀 파일
    """
    try:
        # 파일 확장자 확인
        if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
            return {
                "status": "error",
                "message": "엑셀 파일만 업로드 가능합니다 (.xlsx, .xls, .xlsm)",
                "timestamp": datetime.now().isoformat()
            }

        # 업로드 디렉토리 생성
        upload_dir = Path(EXCEL_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 파일 저장
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 파일 파싱 및 DB 업데이트
        from services.excel_parser import ExcelParser
        parser = ExcelParser()

        # DB 세션 생성
        db = next(get_db())

        try:
            # 파일 파싱
            result = parser.parse_file(str(file_path))

            if result["status"] == "success":
                # 파일 메타데이터 저장
                file_info = result["file_info"]

                # 기존 동일 파일 데이터 삭제 (동/차수 기준)
                db.query(FileMetadata).filter(
                    FileMetadata.layer_house == file_info.layer_house,
                    FileMetadata.layer_batch == file_info.layer_batch
                ).delete()

                db.query(LayerDaily).filter(
                    LayerDaily.file_id == None  # 임시로 None 체크
                ).delete()

                # 새 데이터 저장
                db.add(file_info)
                db.flush()

                # 산란계 데이터 저장
                for record in result["layer_records"]:
                    record.file_id = file_info.id
                    db.add(record)

                # 육성계 데이터 저장
                for record in result["pullet_records"]:
                    record.file_id = file_info.id
                    db.add(record)

                db.commit()

                return {
                    "status": "success",
                    "message": f"파일 업로드 및 데이터 갱신 완료: {file.filename}",
                    "file_info": {
                        "filename": file.filename,
                        "house": file_info.layer_house,
                        "batch": file_info.layer_batch,
                        "layer_records": len(result["layer_records"]),
                        "pullet_records": len(result["pullet_records"])
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"파일 파싱 실패: {result.get('message', '알 수 없는 오류')}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    except Exception as e:
        return {
            "status": "error",
            "message": f"파일 업로드 실패: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@app.get("/api/admin/check-updates")
def check_updates():
    """
    파일 변경 확인 (실제 업데이트 없이 확인만)
    """
    try:
        changed_files = file_watcher.check_for_changes()

        return {
            "status": "success",
            "has_changes": len(changed_files) > 0,
            "changed_files": [f.name for f in changed_files],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"변경 확인 실패: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@app.get("/api/admin/scheduler-status")
def get_scheduler_status():
    """
    스케줄러 상태 조회
    """
    if IS_CLOUD:
        return {
            "status": "success",
            "scheduler": {
                "is_running": False,
                "next_run": None,
                "last_update": None,
                "message": "클라우드 환경 - 스케줄러 비활성화"
            },
            "timestamp": datetime.now().isoformat()
        }

    try:
        status = scheduler.get_status()
        return {
            "status": "success",
            "scheduler": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"스케줄러 상태 조회 실패: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/admin/trigger-update")
def trigger_update():
    """
    스케줄러 수동 트리거 (테스트용)
    """
    if IS_CLOUD:
        return {
            "status": "unavailable",
            "message": "클라우드 환경에서는 수동 업데이트를 사용할 수 없습니다",
            "timestamp": datetime.now().isoformat()
        }

    try:
        result = scheduler.trigger_now()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"수동 트리거 실패: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@app.get("/api/alerts")
def get_alerts(db: Session = Depends(get_db)):
    """
    알림 및 경고 조회

    HL-Manual 시트의 주령별 기준에 따라 산란율 체크
    - 산란율이 HL-Manual 기준 미달 시 경고
    - 폐사율 > 0.1%: 경고
    - 파란율 > 2%: 경고
    """
    from sqlalchemy import func, and_
    from services.hl_manual_parser import HLManualParser
    import glob

    # 각 파일의 최신 레코드 조회
    subquery = db.query(
        LayerDaily.file_id,
        func.max(LayerDaily.age_day).label('max_age')
    ).filter(LayerDaily.laying_rate.isnot(None)).group_by(LayerDaily.file_id).subquery()

    latest_records = db.query(LayerDaily).join(
        subquery,
        and_(
            LayerDaily.file_id == subquery.c.file_id,
            LayerDaily.age_day == subquery.c.max_age
        )
    ).all()

    alerts = []

    for record in latest_records:
        file_info = db.query(FileMetadata).filter_by(id=record.file_id).first()
        if not file_info:
            continue

        house_label = f"{file_info.layer_house} {file_info.layer_batch}"

        # HL-Manual 파서 초기화 (해당 파일의 엑셀 찾기)
        hl_parser = None
        if not IS_CLOUD and os.path.exists(EXCEL_DIR):
            excel_files = glob.glob(os.path.join(EXCEL_DIR, "*.xlsm"))
            for excel_file in excel_files:
                if file_info.layer_house in excel_file and file_info.layer_batch in excel_file:
                    try:
                        hl_parser = HLManualParser(excel_file)
                        break
                    except:
                        pass

        # 산란율 체크 (HL-Manual 기준 사용)
        if record.laying_rate and record.week_age:
            threshold = 70  # 기본 임계값
            warning_message = None

            if hl_parser:
                standard = hl_parser.get_standard(record.week_age)
                if standard and standard['min_laying_rate'] > 0:
                    threshold = standard['min_laying_rate']
                    if record.laying_rate < threshold:
                        warning_message = hl_parser.check_laying_rate(record.week_age, record.laying_rate)

            # HL-Manual 기준이 없으면 기본 70% 기준 사용
            if not warning_message and record.laying_rate < 70:
                warning_message = f"산란율 낮음: {record.laying_rate:.1f}%"

            if warning_message:
                # 기준 대비 차이 계산
                diff_percent = abs(record.laying_rate - threshold)
                severity = "critical" if diff_percent > 10 else "warning"

                alerts.append({
                    "type": "laying_rate",
                    "severity": severity,
                    "house": house_label,
                    "message": warning_message,
                    "value": record.laying_rate,
                    "threshold": threshold,
                    "age_day": record.age_day,
                    "week_age": record.week_age,
                    "date": record.record_date.isoformat() if record.record_date else None
                })

        # 폐사율 체크 (0.1% 초과 경고)
        if record.mortality_rate and record.mortality_rate > 0.1:
            alerts.append({
                "type": "mortality_rate",
                "severity": "warning" if record.mortality_rate <= 0.2 else "critical",
                "house": house_label,
                "message": f"폐사율 높음: {record.mortality_rate:.2f}%",
                "value": record.mortality_rate,
                "threshold": 0.1,
                "age_day": record.age_day,
                "date": record.record_date.isoformat() if record.record_date else None
            })

        # 파란율 체크 (오파란율 = 파란+오란 합산)
        # ~5%: 정상 (알림 없음)
        # 5~10%: 주의 (warning)
        # 10%~: 심각 (critical)
        if record.broken_egg_rate and record.broken_egg_rate > 5:
            if record.broken_egg_rate >= 10:
                severity = "critical"
                message = f"오파란율 심각: {record.broken_egg_rate:.2f}%"
                threshold = 10
            else:  # 5~10%
                severity = "warning"
                message = f"오파란율 주의: {record.broken_egg_rate:.2f}%"
                threshold = 5

            alerts.append({
                "type": "broken_egg_rate",
                "severity": severity,
                "house": house_label,
                "message": message,
                "value": record.broken_egg_rate,
                "threshold": threshold,
                "age_day": record.age_day,
                "date": record.record_date.isoformat() if record.record_date else None
            })

    return {
        "total": len(alerts),
        "critical_count": sum(1 for a in alerts if a["severity"] == "critical"),
        "warning_count": sum(1 for a in alerts if a["severity"] == "warning"),
        "alerts": sorted(alerts, key=lambda x: (0 if x["severity"] == "critical" else 1, x["house"])),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/predictions/{file_id}")
def get_predictions(file_id: int, days_ahead: int = 7, db: Session = Depends(get_db)):
    """
    예측 분석 - 향후 성적 예측

    간단한 선형 회귀를 사용하여 향후 성적 예측
    - 최근 30일 데이터를 기반으로 추세 분석
    - days_ahead: 예측할 미래 일수 (기본값: 7일)
    """
    from sqlalchemy import desc
    import numpy as np

    # 최근 30일 데이터 조회
    recent_data = db.query(LayerDaily).filter(
        LayerDaily.file_id == file_id,
        LayerDaily.laying_rate.isnot(None)
    ).order_by(desc(LayerDaily.age_day)).limit(30).all()

    if len(recent_data) < 5:
        return {
            "status": "error",
            "message": "예측에 필요한 충분한 데이터가 없습니다 (최소 5일 필요)"
        }

    # 데이터를 일령 순으로 정렬
    recent_data = sorted(recent_data, key=lambda x: x.age_day)

    # 현재 데이터
    ages = np.array([r.age_day for r in recent_data])
    laying_rates = np.array([r.laying_rate for r in recent_data if r.laying_rate])
    mortality_rates = np.array([r.mortality_rate for r in recent_data if r.mortality_rate])
    broken_egg_rates = np.array([r.broken_egg_rate for r in recent_data if r.broken_egg_rate])

    def simple_linear_regression(x, y):
        """간단한 선형 회귀"""
        n = len(x)
        if n == 0:
            return 0, y[-1] if len(y) > 0 else 0

        x_mean = np.mean(x)
        y_mean = np.mean(y)

        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)

        if denominator == 0:
            return 0, y_mean

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        return slope, intercept

    # 예측
    current_age = ages[-1]
    future_ages = [current_age + i for i in range(1, days_ahead + 1)]

    predictions = {
        "current_age": int(current_age),
        "prediction_days": days_ahead,
        "predictions": []
    }

    # 산란율 예측
    if len(laying_rates) >= 5:
        slope, intercept = simple_linear_regression(
            ages[-len(laying_rates):], laying_rates
        )
        laying_rate_predictions = [
            max(0, min(100, slope * age + intercept)) for age in future_ages
        ]
    else:
        laying_rate_predictions = [laying_rates[-1] if len(laying_rates) > 0 else 0] * days_ahead

    # 폐사율 예측
    if len(mortality_rates) >= 5:
        slope, intercept = simple_linear_regression(
            ages[-len(mortality_rates):], mortality_rates
        )
        mortality_rate_predictions = [
            max(0, slope * age + intercept) for age in future_ages
        ]
    else:
        mortality_rate_predictions = [mortality_rates[-1] if len(mortality_rates) > 0 else 0] * days_ahead

    # 파란율 예측
    if len(broken_egg_rates) >= 5:
        slope, intercept = simple_linear_regression(
            ages[-len(broken_egg_rates):], broken_egg_rates
        )
        broken_egg_rate_predictions = [
            max(0, slope * age + intercept) for age in future_ages
        ]
    else:
        broken_egg_rate_predictions = [broken_egg_rates[-1] if len(broken_egg_rates) > 0 else 0] * days_ahead

    # 예측 결과 구성
    for i, age in enumerate(future_ages):
        predictions["predictions"].append({
            "age_day": int(age),
            "predicted_laying_rate": float(round(laying_rate_predictions[i], 2)),
            "predicted_mortality_rate": float(round(mortality_rate_predictions[i], 3)),
            "predicted_broken_egg_rate": float(round(broken_egg_rate_predictions[i], 3))
        })

    # 추세 분석
    laying_trend = "상승" if len(laying_rates) >= 2 and float(laying_rates[-1]) > float(laying_rates[0]) else \
                   "하락" if len(laying_rates) >= 2 and float(laying_rates[-1]) < float(laying_rates[0]) else "안정"

    predictions["trend_analysis"] = {
        "laying_rate_trend": laying_trend,
        "current_laying_rate": float(round(laying_rates[-1], 2)) if len(laying_rates) > 0 else 0.0,
        "predicted_change": float(round(laying_rate_predictions[-1] - laying_rates[-1], 2)) if len(laying_rates) > 0 else 0.0
    }

    return predictions


# 정적 파일 서빙 (마지막에 추가 - 다른 라우트가 우선)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    # 포트는 환경 변수에서 가져오거나 기본값 8000 사용 (Render 지원)
    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=not IS_CLOUD  # 클라우드에서는 reload 비활성화
    )
