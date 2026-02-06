"""
LLM 기반 자동 설명 리포트 생성 모듈

비기술자도 이해할 수 있는 자연어 기반 AI 윤리 리포트를 자동으로 생성합니다.

주요 기능:
- 청중별 맞춤 리포트 (경영진/기술팀/규제기관/일반)
- 다국어 지원 (한국어, 영어, 일본어, 중국어)
- 자연어 기반 메트릭 설명
- 시각화 자동 생성

사용 예시:
    from src.llm_reporter import LLMReportGenerator
    
    generator = LLMReportGenerator(model="gpt-4o-mini")
    report = generator.generate_report(
        evaluation_results=results,
        audience="executive",
        language="ko"
    )
"""

from .report_generator import LLMReportGenerator
from .templates import ReportTemplate, TemplateLibrary
from .visualizer import ReportVisualizer
from .explainer import MetricExplainer

__all__ = [
    "LLMReportGenerator",
    "ReportTemplate",
    "TemplateLibrary",
    "ReportVisualizer",
    "MetricExplainer",
]

__version__ = "0.1.0"
