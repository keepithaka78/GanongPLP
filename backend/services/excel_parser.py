"""
엑셀 파일 파싱 핵심 로직
가농바이오 PLP Report v.2.2.6 파일 구조에 특화된 파서
"""

import os
import re
from typing import Dict, Optional, List
from datetime import datetime
import pandas as pd
from openpyxl import load_workbook


class ExcelParser:
    """PLP Report 엑셀 파일 파서"""

    def __init__(self, file_path: str):
        """
        Args:
            file_path: 엑셀 파일 경로
        """
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.metadata = self.parse_filename()
        self.workbook = None

    def parse_filename(self) -> Dict[str, str]:
        """
        파일명에서 메타데이터 추출

        예시: 가농바이오_육성1동43차_성계6동8차_PLP Report v.2.2.6.xlsm
        → {'pullet_house': '1동', 'pullet_batch': '43차',
           'layer_house': '6동', 'layer_batch': '8차'}

        Returns:
            메타데이터 딕셔너리
        """
        pattern = r'육성(\d+)동(\d+)차_성계(\d+)동(\d+)차'
        match = re.search(pattern, self.filename)

        if not match:
            raise ValueError(f"파일명 형식이 올바르지 않습니다: {self.filename}")

        return {
            'pullet_house': f"{match.group(1)}동",
            'pullet_batch': f"{match.group(2)}차",
            'layer_house': f"{match.group(3)}동",
            'layer_batch': f"{match.group(4)}차",
            'filename': self.filename,
            'file_path': self.file_path
        }

    def _load_workbook(self):
        """워크북 로드 (VBA 매크로 무시)"""
        if self.workbook is None:
            self.workbook = load_workbook(
                self.file_path,
                read_only=True,
                keep_vba=False,
                data_only=True  # 수식 대신 값만 읽기
            )

    def read_info_sheet(self) -> Dict:
        """
        Info 시트 읽기

        Returns:
            입추일, 품종, 초기 수수 등의 정보
        """
        self._load_workbook()

        try:
            # pandas로 읽기 시도
            df = pd.read_excel(
                self.file_path,
                sheet_name='Info',
                header=None
            )

            # Info 시트는 키-값 쌍으로 구성되어 있을 것으로 예상
            info_data = {}

            # 기본 정보 추출 (실제 구조에 맞게 조정 필요)
            # 예시: B4에 입추일, B5에 품종 등이 있다고 가정

            return {
                'parsed': True,
                'raw_data': df.head(20).to_dict(),  # 처음 20행만 저장
                'metadata': self.metadata
            }

        except Exception as e:
            print(f"Info 시트 읽기 오류: {e}")
            return {
                'parsed': False,
                'error': str(e),
                'metadata': self.metadata
            }

    def read_layer_daily(self) -> pd.DataFrame:
        """
        Layer-Daily 시트 읽기

        행 구조:
        - 행 0-5: 제목 및 농장 정보
        - 행 6: 컬럼 헤더
        - 행 7~: 실제 데이터

        Returns:
            산란계 일일 데이터 DataFrame
        """
        try:
            # 행 6을 헤더로 사용
            df = pd.read_excel(
                self.file_path,
                sheet_name='Layer-Daily',
                header=6  # 7번째 행(인덱스 6)이 헤더
            )

            # NaN 컬럼명 제거 (병합된 셀 때문에 생김)
            df = df.loc[:, ~df.columns.isna()]

            # 컬럼명 정리
            df.columns = [str(col).strip() if col else f"col_{i}" for i, col in enumerate(df.columns)]

            # 완전히 빈 행 제거
            df = df.dropna(how='all')

            # 일령 컬럼이 없는 행 제거 (데이터가 아닌 행)
            if '일령' in df.columns:
                df = df[df['일령'].notna()]

            print(f"[OK] Layer-Daily 시트 읽기 성공: {len(df)}행, {len(df.columns)}컬럼")
            print(f"  주요 컬럼: {list(df.columns[:10])}")

            return df

        except Exception as e:
            print(f"[ERROR] Layer-Daily 시트 읽기 오류: {e}")
            return pd.DataFrame()

    def read_pullet_daily(self) -> pd.DataFrame:
        """
        Pullet-Daily 시트 읽기 (Layer-Daily와 동일한 구조)

        Returns:
            육성계 일일 데이터 DataFrame
        """
        try:
            df = pd.read_excel(
                self.file_path,
                sheet_name='Pullet-Daily',
                header=6
            )

            # NaN 컬럼명 제거
            df = df.loc[:, ~df.columns.isna()]
            df.columns = [str(col).strip() if col else f"col_{i}" for i, col in enumerate(df.columns)]
            df = df.dropna(how='all')

            if '일령' in df.columns:
                df = df[df['일령'].notna()]

            print(f"[OK] Pullet-Daily 시트 읽기 성공: {len(df)}행, {len(df.columns)}컬럼")

            return df

        except Exception as e:
            print(f"[ERROR] Pullet-Daily 시트 읽기 오류: {e}")
            return pd.DataFrame()

    def get_sheet_names(self) -> List[str]:
        """사용 가능한 시트 이름 목록 반환"""
        self._load_workbook()
        return self.workbook.sheetnames

    def parse_all(self) -> Dict:
        """
        모든 시트 파싱

        Returns:
            전체 데이터 딕셔너리
        """
        print(f"\n{'='*60}")
        print(f"파일 파싱 시작: {self.filename}")
        print(f"{'='*60}")

        result = {
            'metadata': self.metadata,
            'info': self.read_info_sheet(),
            'layer_daily': self.read_layer_daily(),
            'pullet_daily': self.read_pullet_daily(),
            'sheet_names': self.get_sheet_names()
        }

        print(f"\n{'='*60}")
        print(f"파싱 완료!")
        print(f"  - 메타데이터: {self.metadata}")
        print(f"  - 시트 수: {len(result['sheet_names'])}")
        print(f"  - Layer-Daily 행수: {len(result['layer_daily'])}")
        print(f"  - Pullet-Daily 행수: {len(result['pullet_daily'])}")
        print(f"{'='*60}\n")

        return result


def test_parser():
    """파서 테스트 함수"""
    # 테스트 파일 경로
    base_path = r"C:\Users\yimmj\OneDrive\Desktop\산란기록부 Renewal\PLP가농바이오\현재 계군"
    test_file = "가농바이오_육성2동44차_성계4동8차_PLP Report v.2.2.6.xlsm"
    file_path = os.path.join(base_path, test_file)

    if not os.path.exists(file_path):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {file_path}")
        return

    # 파서 생성 및 테스트
    parser = ExcelParser(file_path)

    # 파일명 파싱 테스트
    print("1. 파일명 파싱 테스트")
    print(f"   메타데이터: {parser.metadata}")

    # 시트 목록 확인
    print("\n2. 시트 목록")
    sheet_names = parser.get_sheet_names()
    for i, name in enumerate(sheet_names, 1):
        print(f"   {i}. {name}")

    # 전체 파싱
    print("\n3. 전체 데이터 파싱")
    data = parser.parse_all()

    # Layer-Daily 데이터 샘플
    if not data['layer_daily'].empty:
        print("\n4. Layer-Daily 데이터 샘플 (처음 5행)")
        print(data['layer_daily'].head())

    return data


if __name__ == "__main__":
    test_parser()
