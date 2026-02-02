# 가농바이오 양계 대시보드

PLP Report 엑셀 파일 데이터를 통합 분석하는 웹 대시보드입니다.

## 주요 기능

### 1. 실시간 대시보드
- 현재 사육중인 계군 현황 모니터링
- 산란율, 폐사율, 파란율, 수당 사료섭취량 등 주요 지표 표시
- 동/차수별 필터링 기능
- 자동 업데이트 기능 (하루 1회)

### 2. 동별 비교
- 특정 일령 기준으로 여러 계군 성적 비교
- 산란율, 폐사율, 파란율, 수당 사료섭취량 막대 그래프
- 일령 슬라이더로 동적 비교

### 3. 추이 그래프
- 시간에 따른 성적 변화 추이
- 다중 계군 선택 및 비교
- 산란율, 폐사율 등 라인 차트

### 4. 데이터 검색
- 고급 검색 필터 (동, 차수, 날짜, 일령 범위)
- 검색 결과 요약 통계
- 상세 데이터 테이블

### 5. 알림 및 경고
- 성적 임계값 모니터링
  - 산란율 < 70%: 경고
  - 폐사율 > 0.1%: 경고
  - 파란율 > 2%: 경고
- 경고/심각 수준별 알림 표시

### 6. 예측 분석
- 향후 7~90일 성적 예측
- 선형 회귀 기반 추세 분석
- 산란율, 폐사율, 파란율 예측 그래프

## 기술 스택

### 백엔드
- **Python 3.11.9**
- **FastAPI**: REST API 프레임워크
- **SQLAlchemy**: ORM
- **SQLite**: 데이터베이스
- **Pandas + openpyxl**: 엑셀 파일 처리
- **APScheduler**: 자동 업데이트 스케줄링

### 프론트엔드
- **HTML + Vanilla JavaScript**
- **Bootstrap 5**: UI 프레임워크
- **Chart.js**: 데이터 시각화

## 설치 방법

### 1. 필수 요구사항
- Python 3.11 이상
- pip (Python 패키지 관리자)

### 2. 저장소 클론
```bash
git clone https://github.com/your-username/poultry-dashboard.git
cd poultry-dashboard
```

### 3. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 4. 패키지 설치
```bash
cd backend
pip install -r requirements.txt
```

### 5. 환경 변수 설정
`.env` 파일을 생성하고 엑셀 파일 경로를 설정:
```
EXCEL_DIR=C:\Users\your-path\엑셀파일폴더
```

### 6. 서버 실행
```bash
cd backend
python main.py
```

서버가 `http://localhost:8000`에서 실행됩니다.

### 7. 브라우저에서 접속
```
http://localhost:8000
```

## 프로젝트 구조

```
poultry-dashboard/
├── backend/
│   ├── main.py                 # FastAPI 메인 애플리케이션
│   ├── database.py             # 데이터베이스 설정
│   ├── models.py               # SQLAlchemy 모델
│   ├── services/
│   │   ├── excel_parser.py     # 엑셀 파일 파싱
│   │   ├── data_loader.py      # 데이터 로딩
│   │   ├── file_watcher.py     # 파일 변경 감시
│   │   └── scheduler.py        # 자동 업데이트 스케줄러
│   └── requirements.txt        # Python 패키지 목록
│
├── frontend/
│   ├── index.html              # 메인 대시보드
│   ├── compare.html            # 동별 비교
│   ├── trends.html             # 추이 그래프
│   ├── search.html             # 데이터 검색
│   └── predictions.html        # 예측 분석
│
├── data/
│   └── poultry.db              # SQLite 데이터베이스
│
└── README.md
```

## API 문서

서버 실행 후 `http://localhost:8000/docs`에서 Swagger UI를 통해 API 문서를 확인할 수 있습니다.

### 주요 엔드포인트

- `GET /api/health` - 서버 상태 확인
- `GET /api/files` - 파일 목록 조회
- `GET /api/layer/summary` - 계군 요약 정보
- `GET /api/layer/compare?age_day={일령}` - 동별 비교 데이터
- `GET /api/layer/trends/{file_id}` - 추이 데이터
- `GET /api/layer/search` - 데이터 검색
- `GET /api/alerts` - 알림 및 경고
- `GET /api/predictions/{file_id}?days_ahead={일수}` - 예측 분석
- `POST /api/admin/reload-data` - 데이터 수동 새로고침
- `GET /api/admin/scheduler-status` - 스케줄러 상태 확인

## 자동 업데이트

시스템은 매일 새벽 2시에 자동으로 엑셀 파일 변경을 감지하고 데이터를 업데이트합니다.

수동으로 업데이트하려면:
1. 대시보드 우측 하단의 "데이터 새로고침" 버튼 클릭
2. 또는 스케줄러 카드의 "즉시 실행 (테스트)" 버튼 클릭

## 유지보수

### 데이터베이스 백업
```bash
cp data/poultry.db data/poultry.db.backup
```

### 로그 확인
서버는 콘솔에 실시간 로그를 출력합니다. 주요 이벤트:
- 파일 변경 감지
- 데이터 업데이트
- 스케줄러 실행
- API 요청

### 문제 해결

**문제: 서버가 시작되지 않음**
- Python 버전 확인: `python --version` (3.11 이상 필요)
- 패키지 재설치: `pip install -r requirements.txt`

**문제: 데이터가 표시되지 않음**
- 엑셀 파일 경로 확인
- 데이터베이스 파일 존재 확인: `data/poultry.db`
- API 상태 확인: `http://localhost:8000/api/health`

**문제: 자동 업데이트가 작동하지 않음**
- 스케줄러 상태 확인: 대시보드의 "자동 업데이트 스케줄러" 카드
- 엑셀 파일이 실제로 수정되었는지 확인

## 배포

### Render.com 배포 (권장)
1. GitHub에 코드 푸시
2. Render.com 계정 생성 및 로그인
3. "New +" → "Web Service" 선택
4. GitHub 리포지토리 연결
5. 설정:
   - Environment: Python 3
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && python main.py`
6. 환경 변수 추가: `EXCEL_DIR`

### 로컬 네트워크 배포
```bash
# backend/main.py에서 host 설정 확인
uvicorn.run("main:app", host="0.0.0.0", port=8000)
```

같은 네트워크의 다른 기기에서 `http://{서버IP}:8000`으로 접속 가능

## 라이선스

MIT License

## 지원

문의사항이나 버그 리포트는 이슈 트래커를 이용해주세요.
