"""
준수 분석기

현재 관행과 규제 요구사항 간의 갭을 분석합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import date
import logging

from .database import Regulation, Requirement, RequirementType

logger = logging.getLogger(__name__)


class GapSeverity(Enum):
    """갭 심각도"""
    CRITICAL = "critical"    # 즉시 조치 필요
    HIGH = "high"            # 우선 조치
    MEDIUM = "medium"        # 계획적 조치
    LOW = "low"              # 개선 권장


@dataclass
class ComplianceGap:
    """준수 갭"""
    requirement_id: str
    requirement_name: str
    regulation_name: str
    severity: GapSeverity
    current_status: str
    expected_status: str
    gap_description: str
    remediation_actions: List[str]
    estimated_effort: str  # 예상 소요 시간/자원
    deadline: Optional[date] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "requirement_name": self.requirement_name,
            "regulation_name": self.regulation_name,
            "severity": self.severity.value,
            "current_status": self.current_status,
            "expected_status": self.expected_status,
            "gap_description": self.gap_description,
            "remediation_actions": self.remediation_actions,
            "estimated_effort": self.estimated_effort,
            "deadline": self.deadline.isoformat() if self.deadline else None
        }


@dataclass
class GapAnalysis:
    """갭 분석 결과"""
    analysis_date: date
    regulations_analyzed: List[str]
    total_requirements: int
    compliant_count: int
    non_compliant_count: int
    gaps: List[ComplianceGap]
    overall_compliance_score: float  # 0-100
    priority_actions: List[str]
    
    @property
    def compliance_percentage(self) -> float:
        if self.total_requirements == 0:
            return 100.0
        return (self.compliant_count / self.total_requirements) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "regulations_analyzed": self.regulations_analyzed,
            "total_requirements": self.total_requirements,
            "compliant_count": self.compliant_count,
            "non_compliant_count": self.non_compliant_count,
            "overall_compliance_score": self.overall_compliance_score,
            "compliance_percentage": self.compliance_percentage,
            "gaps": [g.to_dict() for g in self.gaps],
            "priority_actions": self.priority_actions
        }
    
    def to_markdown(self) -> str:
        """마크다운 리포트 생성"""
        md = f"""# 규제 준수 갭 분석 리포트

**분석일**: {self.analysis_date}  
**분석 규제**: {', '.join(self.regulations_analyzed)}

## 요약

| 항목 | 값 |
|------|-----|
| 총 요구사항 | {self.total_requirements} |
| 준수 | {self.compliant_count} |
| 미준수 | {self.non_compliant_count} |
| 준수율 | {self.compliance_percentage:.1f}% |
| 전체 점수 | {self.overall_compliance_score:.1f}/100 |

## 우선 조치 사항

"""
        for i, action in enumerate(self.priority_actions, 1):
            md += f"{i}. {action}\n"
        
        md += "\n## 상세 갭 분석\n\n"
        
        # 심각도별 그룹화
        by_severity = {}
        for gap in self.gaps:
            sev = gap.severity.value
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(gap)
        
        for severity in ["critical", "high", "medium", "low"]:
            if severity in by_severity:
                md += f"### {severity.upper()} 수준 갭\n\n"
                for gap in by_severity[severity]:
                    md += f"""#### {gap.requirement_name}

- **규제**: {gap.regulation_name}
- **현재 상태**: {gap.current_status}
- **기대 상태**: {gap.expected_status}
- **설명**: {gap.gap_description}
- **예상 소요**: {gap.estimated_effort}

**개선 조치**:
"""
                    for action in gap.remediation_actions:
                        md += f"- {action}\n"
                    md += "\n"
        
        return md


class ComplianceAnalyzer:
    """
    준수 분석기
    
    현재 AI 시스템의 관행과 규제 요구사항 간의 갭을 분석합니다.
    
    Example:
        >>> analyzer = ComplianceAnalyzer()
        >>> analysis = analyzer.analyze(
        ...     current_practices=my_practices,
        ...     regulations=[eu_ai_act, korea_law]
        ... )
        >>> print(analysis.to_markdown())
    """
    
    def __init__(self):
        pass
    
    def analyze(
        self,
        current_practices: Dict[str, Any],
        regulations: List[Regulation]
    ) -> GapAnalysis:
        """
        갭 분석 수행
        
        Args:
            current_practices: 현재 관행 (체크리스트 형태)
            regulations: 분석 대상 규제 목록
        
        Returns:
            GapAnalysis 객체
        """
        gaps = []
        total_requirements = 0
        compliant_count = 0
        
        for regulation in regulations:
            for requirement in regulation.requirements:
                total_requirements += 1
                
                # 준수 여부 확인
                practice_key = self._get_practice_key(requirement)
                current_status = current_practices.get(practice_key, {})
                
                is_compliant = self._check_compliance(requirement, current_status)
                
                if is_compliant:
                    compliant_count += 1
                else:
                    # 갭 생성
                    gap = self._create_gap(
                        requirement,
                        regulation.name,
                        current_status,
                        regulation.effective_date
                    )
                    gaps.append(gap)
        
        # 전체 점수 계산
        score = (compliant_count / total_requirements * 100) if total_requirements > 0 else 100
        
        # 우선 조치 생성
        priority_actions = self._generate_priority_actions(gaps)
        
        return GapAnalysis(
            analysis_date=date.today(),
            regulations_analyzed=[r.name for r in regulations],
            total_requirements=total_requirements,
            compliant_count=compliant_count,
            non_compliant_count=len(gaps),
            gaps=gaps,
            overall_compliance_score=score,
            priority_actions=priority_actions
        )
    
    def _get_practice_key(self, requirement: Requirement) -> str:
        """요구사항에 해당하는 관행 키 생성"""
        return requirement.requirement_type.value
    
    def _check_compliance(
        self,
        requirement: Requirement,
        current_status: Dict[str, Any]
    ) -> bool:
        """준수 여부 확인"""
        if not current_status:
            return False
        
        # 구현됨 플래그 확인
        if not current_status.get("implemented", False):
            return False
        
        # 증빙 확인
        evidence = current_status.get("evidence", [])
        required_evidence = requirement.evidence_needed
        
        # 최소 50%의 증빙 필요
        if len(required_evidence) > 0:
            coverage = len([e for e in required_evidence if e in evidence]) / len(required_evidence)
            if coverage < 0.5:
                return False
        
        return True
    
    def _create_gap(
        self,
        requirement: Requirement,
        regulation_name: str,
        current_status: Dict[str, Any],
        deadline: Optional[date]
    ) -> ComplianceGap:
        """갭 객체 생성"""
        # 심각도 결정
        severity = self._determine_severity(requirement, deadline)
        
        # 현재 상태 설명
        if not current_status:
            current = "미구현"
        elif not current_status.get("implemented"):
            current = "부분 구현"
        else:
            current = "불완전 구현"
        
        # 개선 조치 생성
        actions = self._generate_remediation_actions(requirement)
        
        # 예상 소요 시간
        effort = self._estimate_effort(requirement)
        
        return ComplianceGap(
            requirement_id=requirement.id,
            requirement_name=requirement.name,
            regulation_name=regulation_name,
            severity=severity,
            current_status=current,
            expected_status=f"완전 구현 (증빙: {', '.join(requirement.evidence_needed[:2])}...)",
            gap_description=requirement.description,
            remediation_actions=actions,
            estimated_effort=effort,
            deadline=deadline
        )
    
    def _determine_severity(
        self,
        requirement: Requirement,
        deadline: Optional[date]
    ) -> GapSeverity:
        """갭 심각도 결정"""
        # 필수 요구사항 + 임박한 마감
        if requirement.compliance_level.value == "mandatory":
            if deadline and (deadline - date.today()).days < 180:
                return GapSeverity.CRITICAL
            return GapSeverity.HIGH
        
        # 권장 사항
        if requirement.compliance_level.value == "recommended":
            return GapSeverity.MEDIUM
        
        return GapSeverity.LOW
    
    def _generate_remediation_actions(
        self,
        requirement: Requirement
    ) -> List[str]:
        """개선 조치 생성"""
        actions = []
        
        # 요구사항 유형별 기본 조치
        type_actions = {
            RequirementType.DOCUMENTATION: [
                "기술 문서 작성 또는 업데이트",
                "모델 카드 생성",
                "변경 이력 문서화"
            ],
            RequirementType.TECHNICAL: [
                "기술적 구현 검토",
                "테스트 수행 및 검증",
                "성능 메트릭 측정"
            ],
            RequirementType.ORGANIZATIONAL: [
                "담당 조직/인력 지정",
                "프로세스 수립",
                "정책 문서 작성"
            ],
            RequirementType.ASSESSMENT: [
                "영향 평가 수행",
                "위험 분석 실시",
                "평가 보고서 작성"
            ],
            RequirementType.HUMAN_OVERSIGHT: [
                "인간 감독 절차 수립",
                "개입 메커니즘 구현",
                "담당자 교육"
            ],
            RequirementType.DATA_GOVERNANCE: [
                "데이터 품질 기준 정의",
                "데이터 거버넌스 정책 수립",
                "데이터 모니터링 체계 구축"
            ]
        }
        
        actions.extend(type_actions.get(requirement.requirement_type, []))
        
        # 증빙 관련 조치
        for evidence in requirement.evidence_needed[:3]:
            actions.append(f"증빙 자료 준비: {evidence}")
        
        return actions
    
    def _estimate_effort(self, requirement: Requirement) -> str:
        """소요 시간 추정"""
        effort_map = {
            RequirementType.DOCUMENTATION: "2-4 주",
            RequirementType.TECHNICAL: "4-8 주",
            RequirementType.ORGANIZATIONAL: "4-6 주",
            RequirementType.ASSESSMENT: "2-4 주",
            RequirementType.HUMAN_OVERSIGHT: "4-8 주",
            RequirementType.DATA_GOVERNANCE: "6-12 주"
        }
        
        return effort_map.get(requirement.requirement_type, "4-8 주")
    
    def _generate_priority_actions(
        self,
        gaps: List[ComplianceGap]
    ) -> List[str]:
        """우선 조치 생성"""
        # Critical 및 High 갭 먼저
        critical_gaps = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        high_gaps = [g for g in gaps if g.severity == GapSeverity.HIGH]
        
        actions = []
        
        if critical_gaps:
            actions.append(f"긴급: {len(critical_gaps)}개 Critical 갭에 대한 즉시 조치 필요")
            for gap in critical_gaps[:3]:
                actions.append(f"  - {gap.requirement_name} ({gap.regulation_name})")
        
        if high_gaps:
            actions.append(f"우선: {len(high_gaps)}개 High 갭에 대한 계획 수립 필요")
        
        # 규제별 요약
        regulations = set(g.regulation_name for g in gaps)
        for reg in regulations:
            reg_gaps = [g for g in gaps if g.regulation_name == reg]
            actions.append(f"{reg} 관련 {len(reg_gaps)}개 항목 개선 필요")
        
        return actions
