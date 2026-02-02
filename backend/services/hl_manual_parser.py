"""
HL-Manual 시트 파싱
주령별 산란율 및 난중 기준 데이터 추출
"""
import pandas as pd
from typing import Dict, Optional


class HLManualParser:
    """HL-Manual 시트에서 주령별 기준 데이터 추출"""

    def __init__(self, excel_path: str):
        """
        Args:
            excel_path: 엑셀 파일 경로
        """
        self.excel_path = excel_path
        self.standards = self._parse_hl_manual()

    def _parse_hl_manual(self) -> Dict[int, Dict]:
        """
        HL-Manual 시트에서 주령별 기준 파싱

        Returns:
            {주령: {최소산란율, 최대산란율, 최소난중, 최대난중}}
        """
        try:
            # HL-Manual 시트 읽기 (헤더 없음)
            df = pd.read_excel(self.excel_path, sheet_name='HL-Manual', header=None)

            # 주령은 0열, 산란율은 7-8열(HD산란율 최소/최대), 난중은 14-15열
            standards = {}

            # 4번째 행부터 데이터 시작 (0-based index = 4)
            for idx in range(4, len(df)):
                row = df.iloc[idx]

                week = row[0]  # 주령
                if pd.isna(week):
                    continue

                week = int(week)

                # HD산란율 (7-8열)
                min_laying_rate = row[7] if not pd.isna(row[7]) else 0
                max_laying_rate = row[8] if not pd.isna(row[8]) else 0

                # HH난중 manual (14열)
                standard_egg_weight = row[14] if not pd.isna(row[14]) else 0

                standards[week] = {
                    'min_laying_rate': float(min_laying_rate),
                    'max_laying_rate': float(max_laying_rate),
                    'standard_egg_weight': float(standard_egg_weight)
                }

            return standards

        except Exception as e:
            print(f"[ERROR] HL-Manual 파싱 실패: {e}")
            return {}

    def get_standard(self, week_age: int) -> Optional[Dict]:
        """
        특정 주령의 기준 데이터 조회

        Args:
            week_age: 주령

        Returns:
            기준 데이터 딕셔너리 또는 None
        """
        return self.standards.get(week_age)

    def check_laying_rate(self, week_age: int, actual_rate: float) -> Optional[str]:
        """
        산란율이 기준 미달인지 확인

        Args:
            week_age: 주령
            actual_rate: 실제 산란율

        Returns:
            경고 메시지 또는 None
        """
        standard = self.get_standard(week_age)
        if not standard:
            return None

        min_rate = standard['min_laying_rate']

        if min_rate > 0 and actual_rate < min_rate:
            return f"산란율 기준 미달: {actual_rate:.1f}% (기준: {min_rate:.1f}% 이상)"

        return None
