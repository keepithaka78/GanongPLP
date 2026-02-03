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
            {주령: {산란율min/max, 폐사율min/max, 사료섭취min/max, 난중}}
        """
        try:
            # HL-Manual 시트 읽기 (헤더 없음)
            df = pd.read_excel(self.excel_path, sheet_name='HL-Manual', header=None)

            # 컬럼 매핑 (0-based indexing)
            # A(0): 주령
            # H(7)-I(8): HD산란율 최소/최대
            # R(17)-S(18): 폐사율 최소/최대
            # T(19)-U(20): 사료섭취 ml 최소/최대 (ml/day)
            # N(13): HH난중 기준값
            standards = {}

            # 4번째 행부터 데이터 시작 (0-based index = 4)
            for idx in range(4, len(df)):
                row = df.iloc[idx]

                week = row[0]  # 주령
                if pd.isna(week):
                    continue

                try:
                    week = int(week)
                except:
                    continue

                # HD산란율 (열 7-8)
                min_laying_rate = row[7] if len(row) > 7 and not pd.isna(row[7]) else None
                max_laying_rate = row[8] if len(row) > 8 and not pd.isna(row[8]) else None

                # 폐사율 (열 17-18)
                min_mortality_rate = row[17] if len(row) > 17 and not pd.isna(row[17]) else None
                max_mortality_rate = row[18] if len(row) > 18 and not pd.isna(row[18]) else None

                # 사료섭취 ml (열 19-20)
                min_feed_intake = row[19] if len(row) > 19 and not pd.isna(row[19]) else None
                max_feed_intake = row[20] if len(row) > 20 and not pd.isna(row[20]) else None

                # HH난중 기준 (열 13)
                standard_egg_weight = row[13] if len(row) > 13 and not pd.isna(row[13]) else None

                standards[week] = {
                    'min_laying_rate': float(min_laying_rate) if min_laying_rate is not None else None,
                    'max_laying_rate': float(max_laying_rate) if max_laying_rate is not None else None,
                    'min_mortality_rate': float(min_mortality_rate) if min_mortality_rate is not None else None,
                    'max_mortality_rate': float(max_mortality_rate) if max_mortality_rate is not None else None,
                    'min_feed_intake': float(min_feed_intake) if min_feed_intake is not None else None,  # ml/day
                    'max_feed_intake': float(max_feed_intake) if max_feed_intake is not None else None,  # ml/day
                    'standard_egg_weight': float(standard_egg_weight) if standard_egg_weight is not None else None
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
