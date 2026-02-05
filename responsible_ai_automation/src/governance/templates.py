"""
정책 템플릿 라이브러리

다양한 산업 및 규제에 맞는 사전 정의된 정책 템플릿을 제공합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .policy import (
    GovernancePolicy,
    PolicyMetadata,
    PolicySpec,
    FairnessPolicy,
    TransparencyPolicy,
    PrivacyPolicy,
    RobustnessPolicy,
    SustainabilityPolicy,
    CompliancePolicy,
    EnforcementPolicy,
    MetricRequirement,
    EnforcementLevel
)
from datetime import date


class IndustryType(Enum):
    """산업 유형"""
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    GOVERNMENT = "government"
    RETAIL = "retail"
    GENERAL = "general"


class RegulationType(Enum):
    """규제 유형"""
    EU_AI_ACT = "eu_ai_act"
    GDPR = "gdpr"
    KOREA_AI_LAW = "korea_ai_law"
    US_AI_BILL_OF_RIGHTS = "us_ai_bill_of_rights"
    HIPAA = "hipaa"
    GENERAL = "general"


@dataclass
class PolicyTemplate:
    """정책 템플릿"""
    name: str
    description: str
    industry: IndustryType
    regulation: RegulationType
    risk_level: str  # high, medium, low
    policy: GovernancePolicy
    tags: List[str] = field(default_factory=list)
    
    def create_policy(
        self,
        name: str,
        owner: str = "",
        effective_date: Optional[date] = None
    ) -> GovernancePolicy:
        """템플릿에서 새 정책 생성"""
        policy_dict = self.policy.to_dict()
        policy_dict["metadata"]["name"] = name
        policy_dict["metadata"]["owner"] = owner
        policy_dict["metadata"]["effective_date"] = (effective_date or date.today()).isoformat()
        
        return GovernancePolicy.from_dict(policy_dict)


class TemplateLibrary:
    """
    정책 템플릿 라이브러리
    
    산업별, 규제별 사전 정의된 정책 템플릿을 제공합니다.
    
    Example:
        >>> library = TemplateLibrary()
        >>> template = library.get_template("healthcare_hipaa")
        >>> policy = template.create_policy("my-healthcare-ai", owner="AI Team")
    """
    
    def __init__(self):
        self._templates: Dict[str, PolicyTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """기본 템플릿 로드"""
        # 금융 산업 - 고위험
        self._templates["finance_high_risk"] = self._create_finance_template()
        
        # 헬스케어 - HIPAA
        self._templates["healthcare_hipaa"] = self._create_healthcare_template()
        
        # 채용/고용
        self._templates["employment_fair"] = self._create_employment_template()
        
        # EU AI Act 고위험
        self._templates["eu_ai_act_high"] = self._create_eu_ai_act_template()
        
        # 한국 AI 기본법
        self._templates["korea_ai_law"] = self._create_korea_ai_law_template()
        
        # 범용 (표준)
        self._templates["general_standard"] = self._create_general_template()
    
    def _create_finance_template(self) -> PolicyTemplate:
        """금융 산업 템플릿"""
        policy = GovernancePolicy(
            api_version="rai.governance/v1",
            kind="AIGovernancePolicy",
            metadata=PolicyMetadata(
                name="finance-ai-policy-template",
                version="1.0.0",
                effective_date=date.today(),
                description="금융 서비스 AI 시스템을 위한 고위험 정책 템플릿",
                tags=["finance", "high-risk", "regulated"]
            ),
            spec=PolicySpec(
                fairness=FairnessPolicy(
                    enabled=True,
                    metrics=[
                        MetricRequirement("demographic_parity", 0.9, ">=", EnforcementLevel.BLOCK),
                        MetricRequirement("equalized_odds", 0.9, ">=", EnforcementLevel.BLOCK),
                    ],
                    protected_attributes=["gender", "age", "race", "income_level"],
                    max_disparity=0.1
                ),
                transparency=TransparencyPolicy(
                    enabled=True,
                    explainability_score=0.8,
                    model_card_required=True,
                    decision_logging=True
                ),
                privacy=PrivacyPolicy(
                    enabled=True,
                    differential_privacy_epsilon=0.5,
                    data_anonymization="required",
                    pii_detection=True
                ),
                robustness=RobustnessPolicy(
                    enabled=True,
                    adversarial_robustness=0.95,
                    ood_detection=True
                ),
                compliance=CompliancePolicy(
                    regulations=["gdpr", "basel_iii", "korea_financial_ai"],
                    audit_frequency="weekly"
                ),
                enforcement=EnforcementPolicy(
                    critical=EnforcementLevel.BLOCK,
                    high=EnforcementLevel.BLOCK,
                    medium=EnforcementLevel.REQUIRE_APPROVAL,
                    low=EnforcementLevel.WARN
                )
            )
        )
        
        return PolicyTemplate(
            name="금융 서비스 고위험 정책",
            description="신용평가, 대출, 보험 등 금융 AI 시스템을 위한 엄격한 정책",
            industry=IndustryType.FINANCE,
            regulation=RegulationType.GDPR,
            risk_level="high",
            policy=policy,
            tags=["finance", "credit", "loan", "insurance"]
        )
    
    def _create_healthcare_template(self) -> PolicyTemplate:
        """헬스케어 템플릿"""
        policy = GovernancePolicy(
            api_version="rai.governance/v1",
            kind="AIGovernancePolicy",
            metadata=PolicyMetadata(
                name="healthcare-ai-policy-template",
                version="1.0.0",
                effective_date=date.today(),
                description="의료 AI 시스템을 위한 HIPAA 준수 정책 템플릿"
            ),
            spec=PolicySpec(
                fairness=FairnessPolicy(
                    enabled=True,
                    metrics=[
                        MetricRequirement("demographic_parity", 0.85, ">=", EnforcementLevel.REQUIRE_APPROVAL),
                        MetricRequirement("equal_opportunity", 0.9, ">=", EnforcementLevel.BLOCK),
                    ],
                    protected_attributes=["gender", "age", "race", "disability"]
                ),
                transparency=TransparencyPolicy(
                    enabled=True,
                    explainability_score=0.85,
                    model_card_required=True,
                    decision_logging=True
                ),
                privacy=PrivacyPolicy(
                    enabled=True,
                    differential_privacy_epsilon=0.3,
                    data_anonymization="required",
                    pii_detection=True,
                    data_retention_days=2555  # 7년
                ),
                compliance=CompliancePolicy(
                    regulations=["hipaa", "gdpr", "eu_mdr"],
                    audit_frequency="weekly"
                )
            )
        )
        
        return PolicyTemplate(
            name="헬스케어 HIPAA 준수 정책",
            description="의료 진단, 치료 추천 등 의료 AI를 위한 정책",
            industry=IndustryType.HEALTHCARE,
            regulation=RegulationType.HIPAA,
            risk_level="high",
            policy=policy,
            tags=["healthcare", "hipaa", "medical", "diagnosis"]
        )
    
    def _create_employment_template(self) -> PolicyTemplate:
        """채용/고용 템플릿"""
        policy = GovernancePolicy(
            api_version="rai.governance/v1",
            kind="AIGovernancePolicy",
            metadata=PolicyMetadata(
                name="employment-ai-policy-template",
                version="1.0.0",
                effective_date=date.today(),
                description="채용 및 인사 AI 시스템을 위한 공정성 중심 정책"
            ),
            spec=PolicySpec(
                fairness=FairnessPolicy(
                    enabled=True,
                    metrics=[
                        MetricRequirement("demographic_parity", 0.8, ">=", EnforcementLevel.BLOCK),
                        MetricRequirement("equalized_odds", 0.85, ">=", EnforcementLevel.BLOCK),
                        MetricRequirement("disparate_impact", 0.8, ">=", EnforcementLevel.BLOCK),
                    ],
                    protected_attributes=["gender", "age", "race", "disability", "veteran_status"],
                    max_disparity=0.2
                ),
                transparency=TransparencyPolicy(
                    enabled=True,
                    explainability_score=0.75,
                    model_card_required=True
                ),
                privacy=PrivacyPolicy(
                    enabled=True,
                    pii_detection=True
                ),
                compliance=CompliancePolicy(
                    regulations=["eeoc_guidelines", "korea_employment_law"],
                    audit_frequency="monthly"
                )
            )
        )
        
        return PolicyTemplate(
            name="채용/고용 공정성 정책",
            description="이력서 스크리닝, 면접 평가 등 채용 AI를 위한 정책",
            industry=IndustryType.EMPLOYMENT,
            regulation=RegulationType.GENERAL,
            risk_level="high",
            policy=policy,
            tags=["employment", "hiring", "hr", "recruitment"]
        )
    
    def _create_eu_ai_act_template(self) -> PolicyTemplate:
        """EU AI Act 고위험 템플릿"""
        policy = GovernancePolicy(
            api_version="rai.governance/v1",
            kind="AIGovernancePolicy",
            metadata=PolicyMetadata(
                name="eu-ai-act-high-risk-template",
                version="1.0.0",
                effective_date=date.today(),
                description="EU AI Act 고위험 AI 시스템 요구사항 준수 정책"
            ),
            spec=PolicySpec(
                fairness=FairnessPolicy(
                    enabled=True,
                    metrics=[
                        MetricRequirement("demographic_parity", 0.85, ">=", EnforcementLevel.BLOCK),
                    ],
                    protected_attributes=["gender", "age", "race", "religion", "disability"]
                ),
                transparency=TransparencyPolicy(
                    enabled=True,
                    explainability_score=0.8,
                    model_card_required=True,
                    decision_logging=True
                ),
                privacy=PrivacyPolicy(
                    enabled=True,
                    data_anonymization="required",
                    pii_detection=True
                ),
                robustness=RobustnessPolicy(
                    enabled=True,
                    adversarial_robustness=0.9
                ),
                compliance=CompliancePolicy(
                    regulations=["eu_ai_act", "gdpr"],
                    audit_frequency="monthly"
                ),
                enforcement=EnforcementPolicy(
                    critical=EnforcementLevel.BLOCK,
                    high=EnforcementLevel.BLOCK,
                    medium=EnforcementLevel.REQUIRE_APPROVAL,
                    low=EnforcementLevel.WARN
                )
            )
        )
        
        return PolicyTemplate(
            name="EU AI Act 고위험 정책",
            description="EU AI Act Article 6 고위험 AI 시스템 요구사항",
            industry=IndustryType.GENERAL,
            regulation=RegulationType.EU_AI_ACT,
            risk_level="high",
            policy=policy,
            tags=["eu", "ai_act", "high_risk", "compliance"]
        )
    
    def _create_korea_ai_law_template(self) -> PolicyTemplate:
        """한국 AI 기본법 템플릿"""
        policy = GovernancePolicy(
            api_version="rai.governance/v1",
            kind="AIGovernancePolicy",
            metadata=PolicyMetadata(
                name="korea-ai-law-template",
                version="1.0.0",
                effective_date=date.today(),
                description="한국 AI 기본법 준수 정책 템플릿"
            ),
            spec=PolicySpec(
                fairness=FairnessPolicy(
                    enabled=True,
                    metrics=[
                        MetricRequirement("demographic_parity", 0.8, ">=", EnforcementLevel.REQUIRE_APPROVAL),
                    ],
                    protected_attributes=["gender", "age", "disability", "region"]
                ),
                transparency=TransparencyPolicy(
                    enabled=True,
                    explainability_score=0.7,
                    model_card_required=True
                ),
                privacy=PrivacyPolicy(
                    enabled=True,
                    pii_detection=True,
                    data_retention_days=365
                ),
                compliance=CompliancePolicy(
                    regulations=["korea_ai_basic_law", "pipa"],
                    audit_frequency="monthly"
                )
            )
        )
        
        return PolicyTemplate(
            name="한국 AI 기본법 준수 정책",
            description="한국 AI 기본법 및 개인정보보호법 준수 정책",
            industry=IndustryType.GENERAL,
            regulation=RegulationType.KOREA_AI_LAW,
            risk_level="medium",
            policy=policy,
            tags=["korea", "ai_law", "pipa", "compliance"]
        )
    
    def _create_general_template(self) -> PolicyTemplate:
        """범용 표준 템플릿"""
        policy = GovernancePolicy(
            api_version="rai.governance/v1",
            kind="AIGovernancePolicy",
            metadata=PolicyMetadata(
                name="general-standard-template",
                version="1.0.0",
                effective_date=date.today(),
                description="범용 AI 시스템을 위한 표준 정책 템플릿"
            ),
            spec=PolicySpec(
                fairness=FairnessPolicy(
                    enabled=True,
                    metrics=[
                        MetricRequirement("demographic_parity", 0.7, ">=", EnforcementLevel.WARN),
                    ]
                ),
                transparency=TransparencyPolicy(
                    enabled=True,
                    explainability_score=0.6
                ),
                privacy=PrivacyPolicy(
                    enabled=True,
                    pii_detection=True
                ),
                robustness=RobustnessPolicy(
                    enabled=True,
                    adversarial_robustness=0.8
                )
            )
        )
        
        return PolicyTemplate(
            name="범용 표준 정책",
            description="일반적인 AI 시스템을 위한 기본 정책",
            industry=IndustryType.GENERAL,
            regulation=RegulationType.GENERAL,
            risk_level="low",
            policy=policy,
            tags=["general", "standard", "baseline"]
        )
    
    def get_template(self, name: str) -> Optional[PolicyTemplate]:
        """템플릿 조회"""
        return self._templates.get(name)
    
    def list_templates(
        self,
        industry: Optional[IndustryType] = None,
        regulation: Optional[RegulationType] = None,
        risk_level: Optional[str] = None
    ) -> List[PolicyTemplate]:
        """
        템플릿 목록 조회
        
        Args:
            industry: 산업 필터
            regulation: 규제 필터
            risk_level: 위험 수준 필터
        """
        templates = list(self._templates.values())
        
        if industry:
            templates = [t for t in templates if t.industry == industry]
        if regulation:
            templates = [t for t in templates if t.regulation == regulation]
        if risk_level:
            templates = [t for t in templates if t.risk_level == risk_level]
        
        return templates
    
    def add_template(self, key: str, template: PolicyTemplate):
        """커스텀 템플릿 추가"""
        self._templates[key] = template
    
    def get_template_names(self) -> List[str]:
        """템플릿 이름 목록"""
        return list(self._templates.keys())
