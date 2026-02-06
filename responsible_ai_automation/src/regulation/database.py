"""
규제 데이터베이스

AI 관련 규제 정보를 구조화하여 관리합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import date
import json


class RequirementType(Enum):
    """요구사항 유형"""
    DOCUMENTATION = "documentation"      # 문서화
    TECHNICAL = "technical"              # 기술적 요구사항
    ORGANIZATIONAL = "organizational"    # 조직적 요구사항
    REPORTING = "reporting"              # 보고 의무
    ASSESSMENT = "assessment"            # 평가/심사
    HUMAN_OVERSIGHT = "human_oversight"  # 인간 감독
    DATA_GOVERNANCE = "data_governance"  # 데이터 거버넌스


class ComplianceLevel(Enum):
    """준수 수준"""
    MANDATORY = "mandatory"      # 필수
    RECOMMENDED = "recommended"  # 권장
    OPTIONAL = "optional"        # 선택


@dataclass
class Requirement:
    """규제 요구사항"""
    id: str
    name: str
    description: str
    requirement_type: RequirementType
    compliance_level: ComplianceLevel
    applicable_to: List[str]  # 적용 대상 AI 시스템 유형
    evidence_needed: List[str]  # 필요한 증빙
    reference: str  # 법조문 참조
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "requirement_type": self.requirement_type.value,
            "compliance_level": self.compliance_level.value,
            "applicable_to": self.applicable_to,
            "evidence_needed": self.evidence_needed,
            "reference": self.reference
        }


@dataclass
class Regulation:
    """규제 정보"""
    id: str
    name: str
    full_name: str
    jurisdiction: str
    effective_date: date
    last_updated: date
    description: str
    requirements: List[Requirement]
    risk_categories: Dict[str, List[str]]
    penalties: str
    enforcement_authority: str
    official_url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name,
            "jurisdiction": self.jurisdiction,
            "effective_date": self.effective_date.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "description": self.description,
            "requirements": [r.to_dict() for r in self.requirements],
            "risk_categories": self.risk_categories,
            "penalties": self.penalties,
            "enforcement_authority": self.enforcement_authority,
            "official_url": self.official_url
        }


class RegulationDatabase:
    """
    규제 데이터베이스
    
    글로벌 AI 규제 정보를 관리합니다.
    """
    
    def __init__(self):
        self._regulations: Dict[str, Regulation] = {}
        self._load_default_regulations()
    
    def _load_default_regulations(self):
        """기본 규제 정보 로드"""
        # EU AI Act
        eu_ai_act_requirements = [
            Requirement(
                id="euai-001",
                name="위험 관리 시스템",
                description="고위험 AI 시스템의 전체 수명주기에 걸친 위험 관리 시스템 구축",
                requirement_type=RequirementType.ORGANIZATIONAL,
                compliance_level=ComplianceLevel.MANDATORY,
                applicable_to=["high_risk"],
                evidence_needed=["위험 관리 계획", "위험 평가 보고서", "완화 조치 문서"],
                reference="Article 9"
            ),
            Requirement(
                id="euai-002",
                name="데이터 및 데이터 거버넌스",
                description="학습, 검증, 테스트 데이터셋에 대한 데이터 거버넌스 및 관리 관행",
                requirement_type=RequirementType.DATA_GOVERNANCE,
                compliance_level=ComplianceLevel.MANDATORY,
                applicable_to=["high_risk"],
                evidence_needed=["데이터 품질 기준", "데이터 거버넌스 정책", "편향 검토 보고서"],
                reference="Article 10"
            ),
            Requirement(
                id="euai-003",
                name="기술 문서화",
                description="시스템 설계, 개발, 테스트에 관한 포괄적인 기술 문서",
                requirement_type=RequirementType.DOCUMENTATION,
                compliance_level=ComplianceLevel.MANDATORY,
                applicable_to=["high_risk"],
                evidence_needed=["기술 문서", "시스템 아키텍처", "알고리즘 설명"],
                reference="Article 11"
            ),
            Requirement(
                id="euai-004",
                name="인간 감독",
                description="AI 시스템의 인간 감독을 가능하게 하는 조치",
                requirement_type=RequirementType.HUMAN_OVERSIGHT,
                compliance_level=ComplianceLevel.MANDATORY,
                applicable_to=["high_risk"],
                evidence_needed=["감독 절차", "개입 메커니즘", "교육 자료"],
                reference="Article 14"
            ),
        ]
        
        self._regulations["eu_ai_act"] = Regulation(
            id="eu_ai_act",
            name="EU AI Act",
            full_name="Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence",
            jurisdiction="EU",
            effective_date=date(2026, 8, 2),
            last_updated=date(2024, 7, 12),
            description="인공지능에 관한 조화로운 규칙을 정하는 EU 규정",
            requirements=eu_ai_act_requirements,
            risk_categories={
                "unacceptable": ["social_scoring", "real_time_biometric"],
                "high_risk": ["credit_scoring", "recruitment", "education", "healthcare", "law_enforcement"],
                "limited_risk": ["chatbots", "emotion_recognition"],
                "minimal_risk": ["spam_filters", "ai_games"]
            },
            penalties="최대 3,500만 유로 또는 전세계 매출의 7%",
            enforcement_authority="EU Member State Authorities",
            official_url="https://eur-lex.europa.eu/eli/reg/2024/1689"
        )
        
        # 한국 AI 기본법
        korea_requirements = [
            Requirement(
                id="krai-001",
                name="고위험 AI 영향평가",
                description="고위험 AI 시스템에 대한 사전 영향평가 수행",
                requirement_type=RequirementType.ASSESSMENT,
                compliance_level=ComplianceLevel.MANDATORY,
                applicable_to=["high_risk"],
                evidence_needed=["영향평가 보고서", "위험 분석"],
                reference="제27조"
            ),
            Requirement(
                id="krai-002",
                name="AI 윤리 기준 준수",
                description="AI 윤리 기준에 따른 개발 및 운영",
                requirement_type=RequirementType.ORGANIZATIONAL,
                compliance_level=ComplianceLevel.MANDATORY,
                applicable_to=["all"],
                evidence_needed=["윤리 정책", "윤리 검토 기록"],
                reference="제22조"
            ),
        ]
        
        self._regulations["korea_ai_basic_law"] = Regulation(
            id="korea_ai_basic_law",
            name="한국 AI 기본법",
            full_name="인공지능 발전과 신뢰 기반 조성 등에 관한 법률",
            jurisdiction="KR",
            effective_date=date(2026, 1, 22),
            last_updated=date(2025, 1, 22),
            description="AI 발전과 신뢰 기반 조성을 위한 기본법",
            requirements=korea_requirements,
            risk_categories={
                "high_risk": ["의료진단", "채용", "교육평가", "금융신용"]
            },
            penalties="과태료 및 시정 명령",
            enforcement_authority="과학기술정보통신부",
            official_url="https://law.go.kr"
        )
    
    def get_regulation(self, regulation_id: str) -> Optional[Regulation]:
        """규제 조회"""
        return self._regulations.get(regulation_id)
    
    def search_regulations(
        self,
        jurisdiction: Optional[str] = None,
        requirement_type: Optional[RequirementType] = None,
        keyword: Optional[str] = None
    ) -> List[Regulation]:
        """규제 검색"""
        results = list(self._regulations.values())
        
        if jurisdiction:
            results = [r for r in results if r.jurisdiction == jurisdiction]
        
        if requirement_type:
            results = [
                r for r in results 
                if any(req.requirement_type == requirement_type for req in r.requirements)
            ]
        
        if keyword:
            keyword_lower = keyword.lower()
            results = [
                r for r in results
                if keyword_lower in r.name.lower() 
                or keyword_lower in r.description.lower()
                or any(keyword_lower in req.name.lower() for req in r.requirements)
            ]
        
        return results
    
    def get_requirements_by_type(
        self,
        requirement_type: RequirementType
    ) -> List[Requirement]:
        """유형별 요구사항 조회"""
        requirements = []
        for reg in self._regulations.values():
            requirements.extend([
                r for r in reg.requirements 
                if r.requirement_type == requirement_type
            ])
        return requirements
    
    def add_regulation(self, regulation: Regulation):
        """규제 추가"""
        self._regulations[regulation.id] = regulation
    
    def export_to_json(self, filepath: str):
        """JSON으로 내보내기"""
        data = {
            reg_id: reg.to_dict() 
            for reg_id, reg in self._regulations.items()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_all_jurisdictions(self) -> List[str]:
        """모든 관할권 목록"""
        return list(set(r.jurisdiction for r in self._regulations.values()))
