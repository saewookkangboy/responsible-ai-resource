"""
AI 탄소 발자국 추적 모듈

AI 모델 학습 및 추론의 환경 영향을 측정하고 최적화합니다.

주요 기능:
- 실시간 에너지 소비 모니터링
- CO2 배출량 계산
- 효율성 최적화 권고
- ESG 리포트 생성

사용 예시:
    from src.carbon_tracker import CarbonFootprintTracker
    
    tracker = CarbonFootprintTracker()
    
    with tracker.track("model_training"):
        model.train()
    
    report = tracker.get_report()
    print(f"CO2 배출량: {report.total_emissions_kg}kg")
"""

from .tracker import CarbonFootprintTracker, TrackingSession
from .calculator import CarbonCalculator, EmissionFactor
from .reporter import ESGReporter, CarbonReport

__all__ = [
    "CarbonFootprintTracker",
    "TrackingSession",
    "CarbonCalculator",
    "EmissionFactor",
    "ESGReporter",
    "CarbonReport",
]

__version__ = "0.1.0"
