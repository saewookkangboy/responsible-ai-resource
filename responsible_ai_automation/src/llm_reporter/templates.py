"""
리포트 템플릿 관리

다양한 청중과 목적에 맞는 리포트 템플릿을 제공합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class TemplateCategory(Enum):
    """템플릿 카테고리"""
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    REGULATORY = "regulatory"
    PUBLIC = "public"
    CUSTOM = "custom"


@dataclass
class ReportSection:
    """리포트 섹션 정의"""
    id: str
    title: str
    description: str
    required: bool = True
    order: int = 0
    subsections: List['ReportSection'] = field(default_factory=list)


@dataclass
class ReportTemplate:
    """
    리포트 템플릿
    
    Attributes:
        name: 템플릿 이름
        category: 템플릿 카테고리
        description: 템플릿 설명
        sections: 섹션 목록
        styles: 스타일 설정
    """
    name: str
    category: TemplateCategory
    description: str
    sections: List[ReportSection]
    styles: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "sections": [
                {
                    "id": s.id,
                    "title": s.title,
                    "description": s.description,
                    "required": s.required,
                    "order": s.order
                }
                for s in self.sections
            ],
            "styles": self.styles,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportTemplate':
        """딕셔너리에서 생성"""
        sections = [
            ReportSection(
                id=s["id"],
                title=s["title"],
                description=s["description"],
                required=s.get("required", True),
                order=s.get("order", 0)
            )
            for s in data.get("sections", [])
        ]
        
        return cls(
            name=data["name"],
            category=TemplateCategory(data.get("category", "custom")),
            description=data.get("description", ""),
            sections=sections,
            styles=data.get("styles", {}),
            metadata=data.get("metadata", {})
        )


class TemplateLibrary:
    """
    템플릿 라이브러리
    
    다양한 목적에 맞는 사전 정의된 템플릿을 제공합니다.
    """
    
    def __init__(self):
        self._templates: Dict[str, ReportTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """기본 템플릿 로드"""
        # 경영진용 템플릿
        self._templates["executive_summary"] = ReportTemplate(
            name="경영진 요약 리포트",
            category=TemplateCategory.EXECUTIVE,
            description="경영진을 위한 핵심 요약 리포트",
            sections=[
                ReportSection(
                    id="executive_summary",
                    title="경영진 요약",
                    description="핵심 발견사항과 비즈니스 영향 요약",
                    order=1
                ),
                ReportSection(
                    id="risk_assessment",
                    title="리스크 평가",
                    description="주요 리스크와 비즈니스 영향",
                    order=2
                ),
                ReportSection(
                    id="compliance_status",
                    title="규제 준수 현황",
                    description="주요 규제 준수 상태 요약",
                    order=3
                ),
                ReportSection(
                    id="recommendations",
                    title="권장 조치",
                    description="우선순위별 권장 조치 사항",
                    order=4
                ),
                ReportSection(
                    id="next_steps",
                    title="향후 계획",
                    description="단기/중기 조치 계획",
                    order=5
                )
            ],
            styles={
                "theme": "professional",
                "charts": ["gauge", "summary_table"],
                "max_pages": 5
            }
        )
        
        # 기술팀용 템플릿
        self._templates["technical_detailed"] = ReportTemplate(
            name="기술 상세 리포트",
            category=TemplateCategory.TECHNICAL,
            description="기술팀을 위한 상세 분석 리포트",
            sections=[
                ReportSection(
                    id="overview",
                    title="개요",
                    description="평가 개요 및 방법론",
                    order=1
                ),
                ReportSection(
                    id="fairness_analysis",
                    title="공정성 분석",
                    description="공정성 메트릭 상세 분석",
                    order=2
                ),
                ReportSection(
                    id="transparency_analysis",
                    title="투명성 분석",
                    description="모델 설명 가능성 분석",
                    order=3
                ),
                ReportSection(
                    id="robustness_analysis",
                    title="견고성 분석",
                    description="적대적 공격 저항성 분석",
                    order=4
                ),
                ReportSection(
                    id="privacy_analysis",
                    title="프라이버시 분석",
                    description="프라이버시 보호 수준 분석",
                    order=5
                ),
                ReportSection(
                    id="technical_recommendations",
                    title="기술적 개선 권고",
                    description="구체적인 코드/모델 개선 방안",
                    order=6
                ),
                ReportSection(
                    id="appendix",
                    title="부록",
                    description="상세 데이터 및 메트릭",
                    required=False,
                    order=7
                )
            ],
            styles={
                "theme": "technical",
                "charts": ["radar", "heatmap", "distribution"],
                "include_code_snippets": True
            }
        )
        
        # 규제기관 제출용 템플릿
        self._templates["regulatory_compliance"] = ReportTemplate(
            name="규제 준수 리포트",
            category=TemplateCategory.REGULATORY,
            description="규제기관 제출용 컴플라이언스 리포트",
            sections=[
                ReportSection(
                    id="system_overview",
                    title="AI 시스템 개요",
                    description="시스템 목적, 범위, 위험 등급",
                    order=1
                ),
                ReportSection(
                    id="eu_ai_act_compliance",
                    title="EU AI Act 준수",
                    description="EU AI Act 요구사항 준수 상태",
                    order=2
                ),
                ReportSection(
                    id="gdpr_compliance",
                    title="GDPR 준수",
                    description="개인정보 보호 준수 상태",
                    order=3
                ),
                ReportSection(
                    id="korea_ai_law",
                    title="한국 AI 기본법",
                    description="한국 AI 기본법 관련 준수 상태",
                    order=4
                ),
                ReportSection(
                    id="risk_management",
                    title="위험 관리",
                    description="위험 식별 및 완화 조치",
                    order=5
                ),
                ReportSection(
                    id="documentation",
                    title="문서화",
                    description="기술 문서 및 감사 추적",
                    order=6
                ),
                ReportSection(
                    id="action_plan",
                    title="조치 계획",
                    description="미준수 사항 개선 계획",
                    order=7
                )
            ],
            styles={
                "theme": "formal",
                "include_checklist": True,
                "include_evidence": True
            }
        )
        
        # 일반 공개용 템플릿
        self._templates["public_transparency"] = ReportTemplate(
            name="투명성 공개 리포트",
            category=TemplateCategory.PUBLIC,
            description="일반 대중을 위한 투명성 리포트",
            sections=[
                ReportSection(
                    id="what_we_do",
                    title="AI 시스템 소개",
                    description="AI 시스템이 하는 일",
                    order=1
                ),
                ReportSection(
                    id="fairness_commitment",
                    title="공정성 노력",
                    description="공정한 AI를 위한 노력",
                    order=2
                ),
                ReportSection(
                    id="privacy_protection",
                    title="개인정보 보호",
                    description="개인정보 보호 방법",
                    order=3
                ),
                ReportSection(
                    id="safety_measures",
                    title="안전 조치",
                    description="AI 안전을 위한 조치",
                    order=4
                ),
                ReportSection(
                    id="user_rights",
                    title="사용자 권리",
                    description="사용자가 알아야 할 권리",
                    order=5
                ),
                ReportSection(
                    id="contact",
                    title="문의",
                    description="추가 정보 및 문의처",
                    order=6
                )
            ],
            styles={
                "theme": "friendly",
                "use_icons": True,
                "reading_level": "general"
            }
        )
    
    def get_template(self, name: str) -> Optional[ReportTemplate]:
        """템플릿 조회"""
        return self._templates.get(name)
    
    def list_templates(
        self,
        category: Optional[TemplateCategory] = None
    ) -> List[ReportTemplate]:
        """템플릿 목록 조회"""
        if category is None:
            return list(self._templates.values())
        return [t for t in self._templates.values() if t.category == category]
    
    def add_template(self, template: ReportTemplate):
        """커스텀 템플릿 추가"""
        self._templates[template.name] = template
    
    def remove_template(self, name: str) -> bool:
        """템플릿 제거"""
        if name in self._templates:
            del self._templates[name]
            return True
        return False
    
    def export_template(self, name: str) -> Optional[str]:
        """템플릿을 JSON으로 내보내기"""
        template = self._templates.get(name)
        if template:
            return json.dumps(template.to_dict(), indent=2, ensure_ascii=False)
        return None
    
    def import_template(self, json_str: str) -> ReportTemplate:
        """JSON에서 템플릿 가져오기"""
        data = json.loads(json_str)
        template = ReportTemplate.from_dict(data)
        self._templates[template.name] = template
        return template
