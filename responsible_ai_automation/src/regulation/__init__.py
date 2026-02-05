"""
글로벌 규제 자동 매핑 모듈

AI 관련 글로벌 규제를 자동으로 매핑하고 준수 상태를 분석합니다.

주요 기능:
- 규제 요구사항 데이터베이스
- AI 시스템-규제 자동 매핑
- 갭 분석 및 준수 점검
- 규제 변경 모니터링

사용 예시:
    from src.regulation import GlobalRegulationMapper
    
    mapper = GlobalRegulationMapper()
    
    # 적용 가능한 규제 식별
    applicable = mapper.identify_applicable_regulations(
        ai_system_type="high_risk",
        deployment_regions=["EU", "KR"],
        industry="finance"
    )
    
    # 갭 분석
    gaps = mapper.analyze_compliance_gaps(current_practices)
"""

from .mapper import GlobalRegulationMapper, RegulationMapping
from .database import RegulationDatabase, Regulation, RequirementType
from .analyzer import ComplianceAnalyzer, GapAnalysis

__all__ = [
    "GlobalRegulationMapper",
    "RegulationMapping",
    "RegulationDatabase",
    "Regulation",
    "RequirementType",
    "ComplianceAnalyzer",
    "GapAnalysis",
]

__version__ = "0.1.0"
