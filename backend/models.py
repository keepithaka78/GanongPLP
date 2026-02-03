"""
데이터베이스 모델 정의
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class FileMetadata(Base):
    """엑셀 파일 메타데이터"""
    __tablename__ = "file_metadata"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    pullet_house = Column(String)  # 육성동 (예: "1동")
    pullet_batch = Column(String)  # 육성 차수 (예: "43차")
    layer_house = Column(String)   # 성계동 (예: "6동")
    layer_batch = Column(String)   # 성계 차수 (예: "8차")
    file_path = Column(String)
    last_modified = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    # 관계
    layer_daily_records = relationship("LayerDaily", back_populates="file")
    pullet_daily_records = relationship("PulletDaily", back_populates="file")


class LayerDaily(Base):
    """산란계 일일 데이터"""
    __tablename__ = "layer_daily"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_metadata.id"), index=True)

    # 기본 정보
    week_age = Column(Integer)           # 주령
    record_date = Column(Date, index=True)  # 날짜
    age_day = Column(Integer, index=True)   # 일령

    # 개체 수
    current_count = Column(Integer)      # 현재수수
    mortality_count = Column(Integer)    # 폐사
    culling_count = Column(Integer)      # 도태

    # 비율
    mortality_rate = Column(Float)       # 폐사율
    cumulative_mortality_rate = Column(Float)  # 누적폐사율

    # 산란 관련
    laying_rate = Column(Float)          # 산란율
    egg_production = Column(Integer)     # 산란수 (전체)
    broken_egg_rate = Column(Float)      # 오란율 (파란율)

    # 계란 규격별 개수
    extra_large_eggs = Column(Integer)      # 왕란
    large_eggs = Column(Integer)            # 특란
    medium_large_eggs = Column(Integer)     # 대란
    medium_eggs = Column(Integer)           # 중란
    small_eggs = Column(Integer)            # 소란
    other_eggs = Column(Integer)            # 오파란

    # 사료
    feed_intake = Column(Float)          # 사료섭취량
    cumulative_feed = Column(Float)      # 누적사료
    feed_conversion = Column(Float)      # 사료요구율

    # 체중
    body_weight = Column(Float)          # 체중

    # 수익성
    feed_cost = Column(Float)            # 사료비
    egg_sales = Column(Float)            # 계란판매액

    # 관계
    file = relationship("FileMetadata", back_populates="layer_daily_records")


class PulletDaily(Base):
    """육성계 일일 데이터"""
    __tablename__ = "pullet_daily"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_metadata.id"), index=True)

    # 기본 정보
    week_age = Column(Integer)
    record_date = Column(Date, index=True)
    age_day = Column(Integer, index=True)

    # 개체 수
    current_count = Column(Integer)
    mortality_count = Column(Integer)
    culling_count = Column(Integer)

    # 비율
    mortality_rate = Column(Float)
    cumulative_mortality_rate = Column(Float)

    # 사료
    feed_intake = Column(Float)
    cumulative_feed = Column(Float)

    # 체중
    body_weight = Column(Float)
    uniformity = Column(Float)           # 균일도

    # 관계
    file = relationship("FileMetadata", back_populates="pullet_daily_records")


def create_tables():
    """테이블 생성"""
    from database import engine
    Base.metadata.create_all(bind=engine)
    print("[OK] 테이블 생성 완료")


if __name__ == "__main__":
    create_tables()
