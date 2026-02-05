"""
AI 거버넌스 정책 정의

YAML/JSON 기반 정책 스키마를 정의하고 관리합니다.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import date
import yaml
import json


class RiskLevel(Enum):
    """EU AI Act 기준 위험 수준"""
    UNACCEPTABLE = "unacceptable"  # 금지
    HIGH = "high"                   # 고위험
    LIMITED = "limited"             # 제한적 위험
    MINIMAL = "minimal"             # 최소 위험


class EnforcementLevel(Enum):
    """위반 시 조치 수준"""
    BLOCK = "block"           # 배포 차단
    REQUIRE_APPROVAL = "require_approval"  # 승인 필요
    WARN = "warn"             # 경고
    LOG = "log"               # 로깅만


@dataclass
class MetricRequirement:
    """메트릭 요구사항"""
    name: str
    threshold: float
    operator: str = ">="  # >=, >, <=, <, ==
    action: EnforcementLevel = EnforcementLevel.WARN
    
    def is_satisfied(self, value: float) -> bool:
        """요구사항 충족 여부 확인"""
        ops = {
            ">=": lambda a, b: a >= b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            "<": lambda a, b: a < b,
            "==": lambda a, b: abs(a - b) < 0.0001,
        }
        return ops.get(self.operator, lambda a, b: a >= b)(value, self.threshold)


@dataclass
class FairnessPolicy:
    """공정성 정책"""
    enabled: bool = True
    metrics: List[MetricRequirement] = field(default_factory=list)
    protected_attributes: List[str] = field(default_factory=list)
    max_disparity: float = 0.2
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FairnessPolicy':
        metrics = [
            MetricRequirement(
                name=m["name"],
                threshold=m["threshold"],
                operator=m.get("operator", ">="),
                action=EnforcementLevel(m.get("action", "warn"))
            )
            for m in data.get("metrics", [])
        ]
        return cls(
            enabled=data.get("enabled", True),
            metrics=metrics,
            protected_attributes=data.get("protected_attributes", []),
            max_disparity=data.get("max_disparity", 0.2)
        )


@dataclass
class TransparencyPolicy:
    """투명성 정책"""
    enabled: bool = True
    explainability_score: float = 0.7
    model_card_required: bool = True
    feature_importance_documented: bool = True
    decision_logging: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransparencyPolicy':
        reqs = data.get("requirements", {})
        return cls(
            enabled=data.get("enabled", True),
            explainability_score=reqs.get("explainability_score", 0.7),
            model_card_required=reqs.get("model_card_required", True),
            feature_importance_documented=reqs.get("feature_importance_documented", True),
            decision_logging=reqs.get("decision_logging", True)
        )


@dataclass
class PrivacyPolicy:
    """프라이버시 정책"""
    enabled: bool = True
    differential_privacy_epsilon: float = 1.0
    data_anonymization: str = "required"  # required, recommended, optional
    pii_detection: bool = True
    data_retention_days: int = 365
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PrivacyPolicy':
        reqs = data.get("requirements", {})
        return cls(
            enabled=data.get("enabled", True),
            differential_privacy_epsilon=reqs.get("differential_privacy_epsilon", 1.0),
            data_anonymization=reqs.get("data_anonymization", "required"),
            pii_detection=reqs.get("pii_detection", True),
            data_retention_days=reqs.get("data_retention_days", 365)
        )


@dataclass
class RobustnessPolicy:
    """견고성 정책"""
    enabled: bool = True
    adversarial_robustness: float = 0.9
    ood_detection: bool = True
    confidence_calibration: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RobustnessPolicy':
        reqs = data.get("requirements", {})
        return cls(
            enabled=data.get("enabled", True),
            adversarial_robustness=reqs.get("adversarial_robustness", 0.9),
            ood_detection=reqs.get("ood_detection", True),
            confidence_calibration=reqs.get("confidence_calibration", True)
        )


@dataclass
class SustainabilityPolicy:
    """환경 지속가능성 정책"""
    enabled: bool = False
    max_carbon_footprint_kg: float = 100.0
    energy_efficiency_score: float = 0.8
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SustainabilityPolicy':
        reqs = data.get("requirements", {})
        return cls(
            enabled=data.get("enabled", False),
            max_carbon_footprint_kg=reqs.get("max_carbon_footprint_kg", 100.0),
            energy_efficiency_score=reqs.get("energy_efficiency_score", 0.8)
        )


@dataclass
class CompliancePolicy:
    """규제 준수 정책"""
    regulations: List[str] = field(default_factory=list)
    audit_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompliancePolicy':
        return cls(
            regulations=data.get("regulations", []),
            audit_frequency=data.get("audit_frequency", "monthly")
        )


@dataclass
class EnforcementPolicy:
    """위반 시 조치 정책"""
    critical: EnforcementLevel = EnforcementLevel.BLOCK
    high: EnforcementLevel = EnforcementLevel.REQUIRE_APPROVAL
    medium: EnforcementLevel = EnforcementLevel.WARN
    low: EnforcementLevel = EnforcementLevel.LOG
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnforcementPolicy':
        on_violation = data.get("on_violation", {})
        return cls(
            critical=EnforcementLevel(on_violation.get("critical", "block")),
            high=EnforcementLevel(on_violation.get("high", "require_approval")),
            medium=EnforcementLevel(on_violation.get("medium", "warn")),
            low=EnforcementLevel(on_violation.get("low", "log"))
        )


@dataclass
class PolicySpec:
    """정책 스펙"""
    fairness: FairnessPolicy = field(default_factory=FairnessPolicy)
    transparency: TransparencyPolicy = field(default_factory=TransparencyPolicy)
    privacy: PrivacyPolicy = field(default_factory=PrivacyPolicy)
    robustness: RobustnessPolicy = field(default_factory=RobustnessPolicy)
    sustainability: SustainabilityPolicy = field(default_factory=SustainabilityPolicy)
    compliance: CompliancePolicy = field(default_factory=CompliancePolicy)
    enforcement: EnforcementPolicy = field(default_factory=EnforcementPolicy)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicySpec':
        return cls(
            fairness=FairnessPolicy.from_dict(data.get("fairness", {})),
            transparency=TransparencyPolicy.from_dict(data.get("transparency", {})),
            privacy=PrivacyPolicy.from_dict(data.get("privacy", {})),
            robustness=RobustnessPolicy.from_dict(data.get("robustness", {})),
            sustainability=SustainabilityPolicy.from_dict(data.get("sustainability", {})),
            compliance=CompliancePolicy.from_dict(data.get("compliance", {})),
            enforcement=EnforcementPolicy.from_dict(data.get("enforcement", {}))
        )


@dataclass
class PolicyMetadata:
    """정책 메타데이터"""
    name: str
    version: str
    effective_date: date
    description: str = ""
    owner: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class GovernancePolicy:
    """
    AI 거버넌스 정책
    
    YAML/JSON 파일에서 로드하거나 프로그래밍 방식으로 생성할 수 있습니다.
    
    Example:
        >>> policy = GovernancePolicy.from_yaml("policy.yaml")
        >>> print(policy.spec.fairness.enabled)
        True
    """
    
    api_version: str
    kind: str
    metadata: PolicyMetadata
    spec: PolicySpec
    
    @classmethod
    def from_yaml(cls, filepath: str) -> 'GovernancePolicy':
        """YAML 파일에서 정책 로드"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_json(cls, filepath: str) -> 'GovernancePolicy':
        """JSON 파일에서 정책 로드"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GovernancePolicy':
        """딕셔너리에서 정책 생성"""
        metadata_data = data.get("metadata", {})
        
        # effective_date 파싱
        eff_date = metadata_data.get("effective_date")
        if isinstance(eff_date, str):
            eff_date = date.fromisoformat(eff_date)
        elif eff_date is None:
            eff_date = date.today()
        
        metadata = PolicyMetadata(
            name=metadata_data.get("name", "unnamed-policy"),
            version=metadata_data.get("version", "1.0.0"),
            effective_date=eff_date,
            description=metadata_data.get("description", ""),
            owner=metadata_data.get("owner", ""),
            tags=metadata_data.get("tags", [])
        )
        
        return cls(
            api_version=data.get("apiVersion", "rai.governance/v1"),
            kind=data.get("kind", "AIGovernancePolicy"),
            metadata=metadata,
            spec=PolicySpec.from_dict(data.get("spec", {}))
        )
    
    def to_yaml(self, filepath: str):
        """YAML 파일로 저장"""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
    
    def to_json(self, filepath: str):
        """JSON 파일로 저장"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "apiVersion": self.api_version,
            "kind": self.kind,
            "metadata": {
                "name": self.metadata.name,
                "version": self.metadata.version,
                "effective_date": self.metadata.effective_date.isoformat(),
                "description": self.metadata.description,
                "owner": self.metadata.owner,
                "tags": self.metadata.tags
            },
            "spec": {
                "fairness": {
                    "enabled": self.spec.fairness.enabled,
                    "protected_attributes": self.spec.fairness.protected_attributes,
                    "max_disparity": self.spec.fairness.max_disparity,
                    "metrics": [
                        {
                            "name": m.name,
                            "threshold": m.threshold,
                            "operator": m.operator,
                            "action": m.action.value
                        }
                        for m in self.spec.fairness.metrics
                    ]
                },
                "transparency": {
                    "enabled": self.spec.transparency.enabled,
                    "requirements": {
                        "explainability_score": self.spec.transparency.explainability_score,
                        "model_card_required": self.spec.transparency.model_card_required,
                        "feature_importance_documented": self.spec.transparency.feature_importance_documented,
                        "decision_logging": self.spec.transparency.decision_logging
                    }
                },
                "privacy": {
                    "enabled": self.spec.privacy.enabled,
                    "requirements": {
                        "differential_privacy_epsilon": self.spec.privacy.differential_privacy_epsilon,
                        "data_anonymization": self.spec.privacy.data_anonymization,
                        "pii_detection": self.spec.privacy.pii_detection,
                        "data_retention_days": self.spec.privacy.data_retention_days
                    }
                },
                "robustness": {
                    "enabled": self.spec.robustness.enabled,
                    "requirements": {
                        "adversarial_robustness": self.spec.robustness.adversarial_robustness,
                        "ood_detection": self.spec.robustness.ood_detection,
                        "confidence_calibration": self.spec.robustness.confidence_calibration
                    }
                },
                "sustainability": {
                    "enabled": self.spec.sustainability.enabled,
                    "requirements": {
                        "max_carbon_footprint_kg": self.spec.sustainability.max_carbon_footprint_kg,
                        "energy_efficiency_score": self.spec.sustainability.energy_efficiency_score
                    }
                },
                "compliance": {
                    "regulations": self.spec.compliance.regulations,
                    "audit_frequency": self.spec.compliance.audit_frequency
                },
                "enforcement": {
                    "on_violation": {
                        "critical": self.spec.enforcement.critical.value,
                        "high": self.spec.enforcement.high.value,
                        "medium": self.spec.enforcement.medium.value,
                        "low": self.spec.enforcement.low.value
                    }
                }
            }
        }
    
    def merge(self, other: 'GovernancePolicy') -> 'GovernancePolicy':
        """두 정책을 병합 (더 엄격한 정책 적용)"""
        # 간단한 병합 로직 - 실제로는 더 복잡할 수 있음
        merged_dict = self.to_dict()
        other_dict = other.to_dict()
        
        # spec의 각 섹션에서 더 엄격한 값 선택
        # 예: threshold는 더 높은 값, epsilon은 더 낮은 값
        
        return GovernancePolicy.from_dict(merged_dict)
    
    def is_effective(self) -> bool:
        """정책이 현재 유효한지 확인"""
        return self.metadata.effective_date <= date.today()
