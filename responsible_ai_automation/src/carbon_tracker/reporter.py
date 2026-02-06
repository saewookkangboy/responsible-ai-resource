"""
ESG 리포트 생성기

AI 시스템의 환경 영향을 ESG 리포트 형식으로 생성합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, date
import json


@dataclass
class CarbonReport:
    """탄소 배출 리포트"""
    report_id: str
    period_start: date
    period_end: date
    total_energy_kwh: float
    total_emissions_kg_co2: float
    emissions_by_activity: Dict[str, float]
    emissions_by_region: Dict[str, float]
    reduction_recommendations: List[str]
    year_over_year_change: Optional[float] = None
    target_emissions: Optional[float] = None
    
    @property
    def on_track(self) -> bool:
        """목표 달성 여부"""
        if self.target_emissions:
            return self.total_emissions_kg_co2 <= self.target_emissions
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat()
            },
            "total_energy_kwh": self.total_energy_kwh,
            "total_emissions_kg_co2": self.total_emissions_kg_co2,
            "emissions_by_activity": self.emissions_by_activity,
            "emissions_by_region": self.emissions_by_region,
            "reduction_recommendations": self.reduction_recommendations,
            "year_over_year_change": self.year_over_year_change,
            "target_emissions": self.target_emissions,
            "on_track": self.on_track
        }


class ESGReporter:
    """
    ESG 리포트 생성기
    
    AI 시스템의 환경 영향을 다양한 형식의 리포트로 생성합니다.
    """
    
    def __init__(self, company_name: str = ""):
        self.company_name = company_name
        self._historical_data: List[CarbonReport] = []
    
    def generate_report(
        self,
        tracker_summary: Dict[str, Any],
        period_start: date,
        period_end: date,
        target_emissions: Optional[float] = None
    ) -> CarbonReport:
        """
        탄소 배출 리포트 생성
        
        Args:
            tracker_summary: CarbonFootprintTracker.get_summary() 결과
            period_start: 기간 시작일
            period_end: 기간 종료일
            target_emissions: 목표 배출량 (kg CO2)
        
        Returns:
            CarbonReport 객체
        """
        import uuid
        
        report = CarbonReport(
            report_id=str(uuid.uuid4())[:8],
            period_start=period_start,
            period_end=period_end,
            total_energy_kwh=tracker_summary.get("total_energy_kwh", 0),
            total_emissions_kg_co2=tracker_summary.get("total_emissions_kg_co2", 0),
            emissions_by_activity={"ai_operations": tracker_summary.get("total_emissions_kg_co2", 0)},
            emissions_by_region={tracker_summary.get("region", "unknown"): tracker_summary.get("total_emissions_kg_co2", 0)},
            reduction_recommendations=self._generate_recommendations(tracker_summary),
            target_emissions=target_emissions
        )
        
        # YoY 변화 계산
        if self._historical_data:
            prev_report = self._historical_data[-1]
            if prev_report.total_emissions_kg_co2 > 0:
                report.year_over_year_change = (
                    (report.total_emissions_kg_co2 - prev_report.total_emissions_kg_co2)
                    / prev_report.total_emissions_kg_co2
                ) * 100
        
        self._historical_data.append(report)
        return report
    
    def _generate_recommendations(
        self,
        summary: Dict[str, Any]
    ) -> List[str]:
        """최적화 권고사항 생성"""
        recommendations = []
        
        carbon_intensity = summary.get("carbon_intensity", 0.5)
        
        if carbon_intensity > 0.4:
            recommendations.append(
                "저탄소 지역(예: europe-north1, us-west1)으로 워크로드 마이그레이션 권장"
            )
        
        recommendations.extend([
            "Mixed Precision Training 적용으로 에너지 소비 30-50% 절감 가능",
            "모델 양자화(INT8)를 통한 추론 효율성 개선",
            "배치 처리로 개별 추론 대비 효율성 향상",
            "재생에너지 100% 데이터센터 선택 검토"
        ])
        
        return recommendations
    
    def to_markdown(self, report: CarbonReport) -> str:
        """마크다운 형식 리포트"""
        status = "✅ 목표 달성" if report.on_track else "⚠️ 목표 초과"
        
        md = f"""# AI 탄소 배출 리포트

**기업**: {self.company_name}  
**기간**: {report.period_start} ~ {report.period_end}  
**리포트 ID**: {report.report_id}

---

## 요약

| 항목 | 값 |
|------|-----|
| 총 에너지 소비 | {report.total_energy_kwh:.4f} kWh |
| 총 CO2 배출 | {report.total_emissions_kg_co2:.4f} kg |
| 목표 대비 | {status} |
"""
        
        if report.year_over_year_change is not None:
            direction = "증가" if report.year_over_year_change > 0 else "감소"
            md += f"| 전년 대비 | {abs(report.year_over_year_change):.1f}% {direction} |\n"
        
        md += f"""
## 환경 영향 등가치

- 🚗 자동차 주행: {report.total_emissions_kg_co2 / 0.21:.1f} km
- 🌳 나무 연간 흡수량: {report.total_emissions_kg_co2 / 21:.1f} 그루
- 📱 스마트폰 충전: {report.total_emissions_kg_co2 / 0.008:.0f} 회

## 활동별 배출량

"""
        for activity, emission in report.emissions_by_activity.items():
            md += f"- {activity}: {emission:.4f} kg CO2\n"
        
        md += "\n## 권고사항\n\n"
        for i, rec in enumerate(report.reduction_recommendations, 1):
            md += f"{i}. {rec}\n"
        
        return md
    
    def to_html(self, report: CarbonReport) -> str:
        """HTML 형식 리포트"""
        md_content = self.to_markdown(report)
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AI 탄소 배출 리포트</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .recommendation {{ background-color: #f9f9f9; padding: 10px; margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>AI 탄소 배출 리포트</h1>
    <p><strong>기업:</strong> {self.company_name}</p>
    <p><strong>기간:</strong> {report.period_start} ~ {report.period_end}</p>
    
    <h2>요약</h2>
    <table>
        <tr><th>항목</th><th>값</th></tr>
        <tr><td>총 에너지 소비</td><td>{report.total_energy_kwh:.4f} kWh</td></tr>
        <tr><td>총 CO2 배출</td><td>{report.total_emissions_kg_co2:.4f} kg</td></tr>
    </table>
    
    <h2>권고사항</h2>
    {''.join(f'<div class="recommendation">{rec}</div>' for rec in report.reduction_recommendations)}
</body>
</html>
"""
    
    def to_gri_format(self, report: CarbonReport) -> Dict[str, Any]:
        """
        GRI 표준 형식 (Global Reporting Initiative)
        
        GRI 305: Emissions 표준에 따른 데이터
        """
        return {
            "gri_standard": "GRI 305: Emissions 2016",
            "disclosure": {
                "305-1": {
                    "name": "Direct (Scope 1) GHG emissions",
                    "value": 0,  # AI는 보통 직접 배출 없음
                    "unit": "metric tons CO2e"
                },
                "305-2": {
                    "name": "Energy indirect (Scope 2) GHG emissions",
                    "value": report.total_emissions_kg_co2 / 1000,
                    "unit": "metric tons CO2e",
                    "methodology": "Location-based"
                },
                "305-4": {
                    "name": "GHG emissions intensity",
                    "value": report.total_emissions_kg_co2 / max(report.total_energy_kwh, 1),
                    "unit": "kg CO2e per kWh"
                },
                "305-5": {
                    "name": "Reduction of GHG emissions",
                    "value": abs(report.year_over_year_change) if report.year_over_year_change and report.year_over_year_change < 0 else 0,
                    "unit": "percent"
                }
            },
            "reporting_period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat()
            }
        }
    
    def to_tcfd_format(self, report: CarbonReport) -> Dict[str, Any]:
        """
        TCFD 권고안 형식 (Task Force on Climate-related Financial Disclosures)
        """
        return {
            "tcfd_pillar": "Metrics and Targets",
            "metrics": {
                "scope_2_emissions": {
                    "value": report.total_emissions_kg_co2 / 1000,
                    "unit": "metric tons CO2e"
                },
                "energy_consumption": {
                    "value": report.total_energy_kwh,
                    "unit": "kWh"
                },
                "carbon_intensity": {
                    "value": report.total_emissions_kg_co2 / max(report.total_energy_kwh, 1),
                    "unit": "kg CO2e / kWh"
                }
            },
            "targets": {
                "emissions_target": report.target_emissions,
                "on_track": report.on_track,
                "year_over_year_change": report.year_over_year_change
            },
            "risks_and_opportunities": {
                "transition_risks": [
                    "규제 강화로 인한 탄소 가격 상승",
                    "고탄소 지역 데이터센터 사용 제한"
                ],
                "opportunities": [
                    "에너지 효율 개선을 통한 비용 절감",
                    "저탄소 AI 솔루션으로 경쟁력 확보"
                ]
            }
        }
