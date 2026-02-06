"""
글로벌 규제 매핑 시스템

AI 시스템에 적용 가능한 규제를 자동으로 식별하고 매핑합니다.
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import date
import logging

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    """EU AI Act 위험 분류"""
    UNACCEPTABLE = "unacceptable"
    HIGH_RISK = "high_risk"
    LIMITED_RISK = "limited_risk"
    MINIMAL_RISK = "minimal_risk"


class AISystemType(Enum):
    """AI 시스템 유형"""
    BIOMETRIC = "biometric"
    CREDIT_SCORING = "credit_scoring"
    RECRUITMENT = "recruitment"
    EDUCATION = "education"
    LAW_ENFORCEMENT = "law_enforcement"
    HEALTHCARE = "healthcare"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    GENERAL_PURPOSE = "general_purpose"
    GENERATIVE = "generative"


@dataclass
class RegulationMapping:
    """규제 매핑 결과"""
    regulation_id: str
    regulation_name: str
    jurisdiction: str
    applicable: bool
    relevance_score: float  # 0-1
    requirements: List[str]
    compliance_actions: List[str]
    deadline: Optional[date] = None
    penalty_info: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "regulation_id": self.regulation_id,
            "regulation_name": self.regulation_name,
            "jurisdiction": self.jurisdiction,
            "applicable": self.applicable,
            "relevance_score": self.relevance_score,
            "requirements": self.requirements,
            "compliance_actions": self.compliance_actions,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "penalty_info": self.penalty_info
        }


class GlobalRegulationMapper:
    """
    글로벌 AI 규제 매핑 시스템
    
    AI 시스템의 특성과 배포 지역에 따라 적용 가능한 규제를 식별합니다.
    
    Example:
        >>> mapper = GlobalRegulationMapper()
        >>> regulations = mapper.identify_applicable_regulations(
        ...     ai_system_type="high_risk",
        ...     deployment_regions=["EU", "KR"],
        ...     industry="finance"
        ... )
    """
    
    # 규제 데이터베이스
    REGULATIONS = {
        "eu_ai_act": {
            "name": "EU AI Act",
            "jurisdiction": "EU",
            "effective_date": date(2026, 8, 2),
            "risk_categories": {
                RiskCategory.UNACCEPTABLE: [
                    AISystemType.BIOMETRIC,  # 실시간 원격 생체인식
                ],
                RiskCategory.HIGH_RISK: [
                    AISystemType.CREDIT_SCORING,
                    AISystemType.RECRUITMENT,
                    AISystemType.EDUCATION,
                    AISystemType.LAW_ENFORCEMENT,
                    AISystemType.HEALTHCARE,
                    AISystemType.CRITICAL_INFRASTRUCTURE,
                ]
            },
            "requirements": {
                "high_risk": [
                    "위험 관리 시스템 구축",
                    "데이터 거버넌스",
                    "기술 문서화",
                    "기록 보관",
                    "투명성 및 정보 제공",
                    "인간 감독",
                    "정확성, 견고성, 사이버보안"
                ],
                "general_purpose": [
                    "모델 카드 작성",
                    "학습 데이터 요약",
                    "저작권 정책 준수"
                ]
            },
            "penalties": "최대 3,500만 유로 또는 전세계 매출의 7%"
        },
        "gdpr": {
            "name": "General Data Protection Regulation",
            "jurisdiction": "EU",
            "effective_date": date(2018, 5, 25),
            "requirements": [
                "자동화된 의사결정에 대한 설명권",
                "프로파일링 관련 정보 제공",
                "데이터 주체의 이의 제기 권리",
                "개인정보 영향평가(DPIA)"
            ],
            "penalties": "최대 2,000만 유로 또는 전세계 매출의 4%"
        },
        "korea_ai_basic_law": {
            "name": "한국 AI 기본법",
            "jurisdiction": "KR",
            "effective_date": date(2026, 1, 22),
            "requirements": [
                "고위험 AI 사전 영향평가",
                "AI 윤리 원칙 준수",
                "투명성 및 설명 가능성",
                "차별 금지",
                "인간 통제권 보장"
            ],
            "penalties": "과태료 및 시정 명령"
        },
        "us_ai_bill_of_rights": {
            "name": "Blueprint for an AI Bill of Rights",
            "jurisdiction": "US",
            "effective_date": date(2022, 10, 4),
            "requirements": [
                "안전하고 효과적인 시스템",
                "알고리즘 차별 보호",
                "데이터 프라이버시",
                "통지 및 설명",
                "인간 대안 및 거부권"
            ],
            "penalties": "자발적 가이드라인 (법적 구속력 없음)"
        },
        "ccpa_cpra": {
            "name": "California Consumer Privacy Act / CPRA",
            "jurisdiction": "US-CA",
            "effective_date": date(2023, 1, 1),
            "requirements": [
                "자동화된 의사결정 기술 옵트아웃",
                "프로파일링 정보 접근권",
                "알고리즘 관련 정보 제공"
            ],
            "penalties": "위반 건당 최대 $7,500"
        },
        "china_ai_regulations": {
            "name": "중국 AI 관련 규정",
            "jurisdiction": "CN",
            "effective_date": date(2023, 8, 15),
            "requirements": [
                "생성형 AI 서비스 등록",
                "콘텐츠 필터링",
                "알고리즘 추천 규제",
                "딥페이크 라벨링"
            ],
            "penalties": "서비스 중단 및 벌금"
        },
        "hipaa": {
            "name": "Health Insurance Portability and Accountability Act",
            "jurisdiction": "US",
            "industries": ["healthcare"],
            "requirements": [
                "PHI 보호",
                "액세스 통제",
                "감사 추적",
                "데이터 암호화"
            ],
            "penalties": "위반 건당 최대 $1.5M"
        }
    }
    
    # 산업별 추가 규제 매핑
    INDUSTRY_REGULATIONS = {
        "finance": ["gdpr", "ccpa_cpra"],
        "healthcare": ["hipaa", "gdpr"],
        "employment": ["gdpr", "korea_ai_basic_law"],
        "education": ["gdpr", "korea_ai_basic_law"],
    }
    
    def __init__(self):
        logger.info("GlobalRegulationMapper 초기화")
    
    def identify_applicable_regulations(
        self,
        ai_system_type: str,
        deployment_regions: List[str],
        industry: Optional[str] = None,
        data_subjects_regions: Optional[List[str]] = None
    ) -> List[RegulationMapping]:
        """
        적용 가능한 규제 식별
        
        Args:
            ai_system_type: AI 시스템 유형 (high_risk, general_purpose 등)
            deployment_regions: 배포 지역 목록 (EU, KR, US 등)
            industry: 산업 분야
            data_subjects_regions: 데이터 주체 거주 지역
        
        Returns:
            적용 가능한 규제 매핑 목록
        """
        applicable_regulations = []
        
        # 지역 정규화
        regions = set(deployment_regions)
        if data_subjects_regions:
            regions.update(data_subjects_regions)
        
        # 각 규제 검토
        for reg_id, reg_data in self.REGULATIONS.items():
            jurisdiction = reg_data["jurisdiction"]
            
            # 지역 적용 여부 확인
            is_applicable = self._check_jurisdiction_match(jurisdiction, regions)
            
            # 산업 적용 여부 확인
            if industry and "industries" in reg_data:
                if industry not in reg_data["industries"]:
                    is_applicable = False
            
            # 적용 가능한 경우 매핑 생성
            if is_applicable:
                requirements = self._get_requirements(reg_data, ai_system_type)
                actions = self._get_compliance_actions(reg_data, ai_system_type)
                
                mapping = RegulationMapping(
                    regulation_id=reg_id,
                    regulation_name=reg_data["name"],
                    jurisdiction=jurisdiction,
                    applicable=True,
                    relevance_score=self._calculate_relevance(reg_data, ai_system_type, industry),
                    requirements=requirements,
                    compliance_actions=actions,
                    deadline=reg_data.get("effective_date"),
                    penalty_info=reg_data.get("penalties", "")
                )
                applicable_regulations.append(mapping)
        
        # 관련도 순으로 정렬
        applicable_regulations.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"적용 가능한 규제 {len(applicable_regulations)}개 식별")
        return applicable_regulations
    
    def _check_jurisdiction_match(
        self,
        regulation_jurisdiction: str,
        target_regions: Set[str]
    ) -> bool:
        """관할권 일치 확인"""
        # 직접 일치
        if regulation_jurisdiction in target_regions:
            return True
        
        # EU 회원국 확인
        eu_members = {"DE", "FR", "IT", "ES", "NL", "BE", "AT", "PL", "SE", "DK", "FI", "IE", "PT", "GR", "CZ"}
        if regulation_jurisdiction == "EU" and target_regions & eu_members:
            return True
        
        # 미국 주 규정
        if regulation_jurisdiction == "US-CA" and ("US" in target_regions or "US-CA" in target_regions):
            return True
        
        return False
    
    def _get_requirements(
        self,
        reg_data: Dict[str, Any],
        ai_system_type: str
    ) -> List[str]:
        """규제 요구사항 추출"""
        if isinstance(reg_data.get("requirements"), dict):
            return reg_data["requirements"].get(ai_system_type, 
                   reg_data["requirements"].get("general_purpose", []))
        return reg_data.get("requirements", [])
    
    def _get_compliance_actions(
        self,
        reg_data: Dict[str, Any],
        ai_system_type: str
    ) -> List[str]:
        """준수 조치 생성"""
        actions = []
        
        requirements = self._get_requirements(reg_data, ai_system_type)
        
        for req in requirements:
            if "문서" in req or "documentation" in req.lower():
                actions.append(f"기술 문서 작성: {req}")
            elif "평가" in req or "assessment" in req.lower():
                actions.append(f"평가 수행: {req}")
            elif "투명성" in req or "transparency" in req.lower():
                actions.append(f"투명성 조치 구현: {req}")
            else:
                actions.append(f"요구사항 준수: {req}")
        
        return actions
    
    def _calculate_relevance(
        self,
        reg_data: Dict[str, Any],
        ai_system_type: str,
        industry: Optional[str]
    ) -> float:
        """관련도 점수 계산"""
        score = 0.5  # 기본 점수
        
        # 고위험 시스템에 대한 EU AI Act
        if "eu_ai_act" in reg_data.get("name", "").lower() and ai_system_type == "high_risk":
            score += 0.3
        
        # 산업별 규제 매칭
        if industry and "industries" in reg_data:
            if industry in reg_data["industries"]:
                score += 0.2
        
        # 발효 여부
        effective_date = reg_data.get("effective_date")
        if effective_date and effective_date <= date.today():
            score += 0.1
        
        return min(score, 1.0)
    
    def get_regulation_summary(self, regulation_id: str) -> Optional[Dict[str, Any]]:
        """규제 요약 정보 조회"""
        return self.REGULATIONS.get(regulation_id)
    
    def compare_jurisdictions(
        self,
        regions: List[str]
    ) -> Dict[str, List[str]]:
        """
        지역별 규제 비교
        
        Args:
            regions: 비교할 지역 목록
        
        Returns:
            지역별 적용 규제 목록
        """
        comparison = {}
        
        for region in regions:
            applicable = []
            for reg_id, reg_data in self.REGULATIONS.items():
                if self._check_jurisdiction_match(reg_data["jurisdiction"], {region}):
                    applicable.append(reg_data["name"])
            comparison[region] = applicable
        
        return comparison
    
    def get_upcoming_deadlines(
        self,
        days_ahead: int = 365
    ) -> List[Dict[str, Any]]:
        """
        다가오는 규제 마감일 조회
        
        Args:
            days_ahead: 조회할 기간 (일)
        
        Returns:
            마감일 목록
        """
        from datetime import timedelta
        
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)
        
        deadlines = []
        for reg_id, reg_data in self.REGULATIONS.items():
            effective_date = reg_data.get("effective_date")
            if effective_date and today <= effective_date <= cutoff:
                deadlines.append({
                    "regulation_id": reg_id,
                    "regulation_name": reg_data["name"],
                    "deadline": effective_date,
                    "days_remaining": (effective_date - today).days
                })
        
        deadlines.sort(key=lambda x: x["deadline"])
        return deadlines
