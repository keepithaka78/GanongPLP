# 유지보수 가이드

## 일상적인 유지보수

### 데이터 확인
- 대시보드에서 최근 업데이트 시간 확인
- 각 계군의 데이터가 최신인지 확인
- 알림/경고 확인

### 주간 점검
- [ ] 스케줄러 상태 확인 (매주 월요일)
- [ ] 데이터베이스 백업 (매주 금요일)
- [ ] 서버 로그 확인

---

## 데이터베이스 관리

### 백업 생성
```bash
# 수동 백업
cd poultry-dashboard/data
copy poultry.db poultry.db.backup_2026-02-02

# 또는 날짜 자동 포함
copy poultry.db poultry.db.backup_%date:~0,4%%date:~5,2%%date:~8,2%
```

### 백업 복원
```bash
cd poultry-dashboard/data
copy poultry.db.backup_2026-02-02 poultry.db
```

### 데이터베이스 최적화
```bash
# Python으로 데이터베이스 vacuum 실행
cd backend
python -c "import sqlite3; conn = sqlite3.connect('../data/poultry.db'); conn.execute('VACUUM'); conn.close()"
```

---

## 새로운 엑셀 파일 추가

### 자동 감지 (권장)
1. 엑셀 파일을 `현재 계군` 폴더에 추가
2. 다음날 새벽 2시 자동 로드
3. 또는 대시보드에서 "데이터 새로고침" 클릭

### 파일명 형식
```
가농바이오_육성X동Y차_성계Z동W차_PLP Report v.2.2.6.xlsm
```

예시:
- `가농바이오_육성1동43차_성계6동8차_PLP Report v.2.2.6.xlsm`

---

## 알림 임계값 수정

`backend/main.py`의 `/api/alerts` 엔드포인트에서 수정:

```python
# 현재 설정
산란율 < 70%: 경고
폐사율 > 0.1%: 경고
파란율 > 2%: 경고

# 수정 예시
if record.laying_rate and record.laying_rate < 75:  # 75%로 변경
    alerts.append({
        "type": "laying_rate",
        "severity": "warning" if record.laying_rate >= 65 else "critical",
        ...
    })
```

수정 후 서버 재시작 필요

---

## 새로운 지표 추가

### 1. 데이터베이스 모델 수정

`backend/models.py`의 `LayerDaily` 클래스에 컬럼 추가:

```python
class LayerDaily(Base):
    # 기존 컬럼...
    new_metric = Column(Float)  # 새 지표
```

### 2. 엑셀 파서 수정

`backend/services/data_loader.py`의 컬럼 매핑에 추가:

```python
record = LayerDaily(
    # 기존 필드...
    new_metric=row.get('새지표컬럼명'),
)
```

### 3. API 엔드포인트 수정

`backend/main.py`에서 응답에 새 지표 포함:

```python
return {
    "house": file_info.layer_house,
    # 기존 필드...
    "new_metric": record.new_metric,
}
```

### 4. 프론트엔드 표시

`frontend/index.html`에 새 지표 카드 추가:

```html
<div class="col-md-2">
    <div class="stat-label">새 지표</div>
    <div class="h4 mb-0">${house.new_metric}</div>
</div>
```

---

## 성능 최적화

### 데이터베이스 인덱스 추가

자주 검색하는 필드에 인덱스 추가:

```python
# backend/models.py
class LayerDaily(Base):
    # ...
    __table_args__ = (
        Index('idx_age_day', 'age_day'),
        Index('idx_record_date', 'record_date'),
    )
```

### 캐싱 추가

자주 조회되는 데이터를 메모리에 캐싱:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_summary_cached(house=None, batch=None):
    # 캐시된 요약 데이터 반환
    pass
```

---

## 보안 강화

### 인증 추가 (선택사항)

FastAPI의 OAuth2 또는 Basic Auth 사용:

```python
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@app.get("/api/layer/summary")
def get_summary(credentials: HTTPBasicCredentials = Depends(security)):
    # 인증 확인
    if credentials.username != "admin" or credentials.password != "password":
        raise HTTPException(status_code=401)
    # ...
```

### HTTPS 강제 (프로덕션)

Render/클라우드는 자동으로 HTTPS 제공.

로컬에서는 Nginx 또는 Caddy 사용.

---

## 로그 관리

### 로그 파일 저장

`backend/main.py`에 로깅 설정 추가:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### 로그 파일 정리

오래된 로그 파일 삭제:

```bash
# 30일 이상된 로그 삭제
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 문제 해결

### 서버가 시작되지 않음

1. **포트 충돌 확인**
   ```bash
   # Windows
   netstat -ano | findstr :8000

   # 프로세스 종료
   taskkill /PID {프로세스ID} /F
   ```

2. **Python 버전 확인**
   ```bash
   python --version
   # 3.11 이상이어야 함
   ```

3. **패키지 재설치**
   ```bash
   cd backend
   pip install -r requirements.txt --force-reinstall
   ```

### 데이터가 업데이트되지 않음

1. **스케줄러 상태 확인**
   - 대시보드의 "자동 업데이트 스케줄러" 카드 확인

2. **파일 경로 확인**
   ```python
   # backend/main.py
   EXCEL_DIR = r"C:\Users\...\현재 계군"
   # 경로가 올바른지 확인
   ```

3. **수동 업데이트**
   - "데이터 새로고침" 버튼 클릭
   - 에러 메시지 확인

### 성능 저하

1. **데이터베이스 크기 확인**
   ```bash
   # Windows
   dir data\poultry.db
   ```

2. **불필요한 데이터 정리**
   ```sql
   -- SQLite로 오래된 데이터 삭제
   DELETE FROM layer_daily WHERE record_date < '2024-01-01';
   VACUUM;
   ```

3. **인덱스 재구축**
   ```sql
   REINDEX;
   ```

---

## 업그레이드 가이드

### 시스템 패키지 업데이트

```bash
cd backend
pip list --outdated
pip install --upgrade fastapi uvicorn pandas
```

### Python 버전 업그레이드

1. 새 Python 버전 설치
2. 새 가상환경 생성
3. 패키지 재설치
4. 테스트 후 기존 환경 교체

---

## 정기 점검 체크리스트

### 매일
- [ ] 대시보드 접속 확인
- [ ] 최근 데이터 확인

### 매주
- [ ] 스케줄러 로그 확인
- [ ] 데이터베이스 백업
- [ ] 알림/경고 검토

### 매월
- [ ] 데이터베이스 최적화 (VACUUM)
- [ ] 오래된 로그 파일 정리
- [ ] 패키지 업데이트 확인
- [ ] 백업 파일 정리

### 분기별
- [ ] 시스템 성능 검토
- [ ] 새로운 기능 검토
- [ ] 사용자 피드백 반영

---

## 연락처

기술 지원이 필요한 경우:
- GitHub Issues
- 이메일: [지원 이메일]
- 전화: [지원 전화번호]
