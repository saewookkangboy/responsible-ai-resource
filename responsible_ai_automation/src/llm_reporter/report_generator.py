"""
LLM 기반 자동 리포트 생성기

비기술자도 이해할 수 있는 자연어 기반 AI 윤리 리포트를 생성합니다.
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AudienceType(Enum):
    """리포트 대상 청중 유형"""
    EXECUTIVE = "executive"      # 경영진
    TECHNICAL = "technical"      # 기술팀
    REGULATORY = "regulatory"    # 규제기관
    PUBLIC = "public"            # 일반 공개


class Language(Enum):
    """지원 언어"""
    KOREAN = "ko"
    ENGLISH = "en"
    JAPANESE = "ja"
    CHINESE = "zh"


@dataclass
class ReportConfig:
    """리포트 생성 설정"""
    audience: AudienceType = AudienceType.EXECUTIVE
    language: Language = Language.KOREAN
    include_visualizations: bool = True
    include_recommendations: bool = True
    detail_level: Literal["summary", "standard", "detailed"] = "standard"
    max_length: Optional[int] = None


@dataclass
class GeneratedReport:
    """생성된 리포트"""
    title: str
    summary: str
    sections: List[Dict[str, Any]]
    recommendations: List[str]
    visualizations: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """마크다운 형식으로 변환"""
        md = f"# {self.title}\n\n"
        md += f"## 요약\n{self.summary}\n\n"
        
        for section in self.sections:
            md += f"## {section.get('title', 'Section')}\n"
            md += f"{section.get('content', '')}\n\n"
        
        if self.recommendations:
            md += "## 권고사항\n"
            for i, rec in enumerate(self.recommendations, 1):
                md += f"{i}. {rec}\n"
        
        return md
    
    def to_html(self) -> str:
        """HTML 형식으로 변환"""
        # TODO: HTML 템플릿 적용
        return f"<html><body>{self.to_markdown()}</body></html>"
    
    def to_pdf(self, output_path: str) -> str:
        """PDF 형식으로 저장"""
        # TODO: PDF 생성 로직
        raise NotImplementedError("PDF 생성은 아직 구현되지 않았습니다.")


class LLMProvider(ABC):
    """LLM 프로바이더 추상 클래스"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """텍스트 생성"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API 프로바이더"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.model = model
        self._api_key = api_key
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                import os
                api_key = self._api_key or os.getenv("OPENAI_API_KEY")
                self._client = OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("openai 패키지가 필요합니다: pip install openai")
        return self._client
    
    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content


class GeminiProvider(LLMProvider):
    """Google Gemini API 프로바이더"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        self.model = model
        self._api_key = api_key
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                import google.generativeai as genai
                import os
                api_key = self._api_key or os.getenv("GEMINI_API_KEY")
                genai.configure(api_key=api_key)
                self._client = genai.GenerativeModel(self.model)
            except ImportError:
                raise ImportError("google-generativeai 패키지가 필요합니다: pip install google-generativeai")
        return self._client
    
    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.generate_content(prompt, **kwargs)
        return response.text


class LLMReportGenerator:
    """
    LLM을 활용한 자동 설명 리포트 생성기
    
    비기술자도 이해할 수 있는 자연어 기반 AI 윤리 리포트를 생성합니다.
    
    Attributes:
        provider: LLM 프로바이더 (OpenAI, Gemini 등)
        config: 리포트 생성 설정
    
    Example:
        >>> generator = LLMReportGenerator(model="gpt-4o-mini")
        >>> report = generator.generate_report(
        ...     evaluation_results=results,
        ...     audience="executive",
        ...     language="ko"
        ... )
        >>> print(report.to_markdown())
    """
    
    # 청중별 프롬프트 템플릿
    AUDIENCE_PROMPTS = {
        AudienceType.EXECUTIVE: """
당신은 AI 윤리 전문가입니다. 다음 AI 모델 평가 결과를 경영진이 이해할 수 있도록 
비즈니스 관점에서 요약해주세요. 기술적인 용어는 피하고, 비즈니스 영향과 리스크에 초점을 맞춰주세요.

핵심 포인트:
- 비즈니스 리스크 요약
- 규제 준수 상태
- 권장 조치 사항
- ROI 관점의 개선 우선순위
""",
        AudienceType.TECHNICAL: """
당신은 AI 윤리 전문가입니다. 다음 AI 모델 평가 결과를 기술팀이 활용할 수 있도록 
상세하게 분석해주세요. 기술적인 세부사항과 구체적인 개선 방안을 포함해주세요.

핵심 포인트:
- 각 메트릭의 기술적 분석
- 문제점의 근본 원인
- 구체적인 코드/모델 개선 방안
- 테스트 및 검증 방법
""",
        AudienceType.REGULATORY: """
당신은 AI 윤리 및 규제 전문가입니다. 다음 AI 모델 평가 결과를 규제기관 제출용으로 
작성해주세요. 관련 규제 요구사항과의 매핑 및 준수 상태를 명확히 해주세요.

핵심 포인트:
- EU AI Act 준수 상태
- GDPR 개인정보 보호 상태
- 한국 AI 기본법 관련 사항
- 필요한 개선 조치 및 일정
""",
        AudienceType.PUBLIC: """
당신은 AI 윤리 커뮤니케이션 전문가입니다. 다음 AI 모델 평가 결과를 일반 대중이 
이해할 수 있도록 쉽게 설명해주세요. 전문 용어는 피하고, 일상적인 비유를 사용해주세요.

핵심 포인트:
- AI 시스템이 하는 일
- 공정성과 안전성 상태
- 개인정보 보호 방법
- 사용자가 알아야 할 점
"""
    }
    
    # 언어별 설정
    LANGUAGE_SETTINGS = {
        Language.KOREAN: {
            "title_prefix": "AI 윤리 평가 리포트",
            "summary_title": "요약",
            "recommendations_title": "권고사항",
        },
        Language.ENGLISH: {
            "title_prefix": "AI Ethics Assessment Report",
            "summary_title": "Summary",
            "recommendations_title": "Recommendations",
        },
        Language.JAPANESE: {
            "title_prefix": "AI倫理評価レポート",
            "summary_title": "要約",
            "recommendations_title": "推奨事項",
        },
        Language.CHINESE: {
            "title_prefix": "AI伦理评估报告",
            "summary_title": "摘要",
            "recommendations_title": "建议",
        },
    }
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[ReportConfig] = None
    ):
        """
        리포트 생성기 초기화
        
        Args:
            model: 사용할 LLM 모델명
            provider: LLM 프로바이더 ("openai" 또는 "gemini")
            api_key: API 키 (환경변수 대신 직접 지정)
            config: 리포트 생성 설정
        """
        self.model = model
        self.config = config or ReportConfig()
        
        # 프로바이더 자동 선택
        if provider is None:
            if "gpt" in model.lower() or "openai" in model.lower():
                provider = "openai"
            elif "gemini" in model.lower():
                provider = "gemini"
            else:
                provider = "openai"  # 기본값
        
        # 프로바이더 초기화
        if provider == "openai":
            self._provider = OpenAIProvider(api_key=api_key, model=model)
        elif provider == "gemini":
            self._provider = GeminiProvider(api_key=api_key, model=model)
        else:
            raise ValueError(f"지원하지 않는 프로바이더: {provider}")
        
        logger.info(f"LLMReportGenerator 초기화 완료: model={model}, provider={provider}")
    
    def generate_report(
        self,
        evaluation_results: Dict[str, Any],
        audience: str = "executive",
        language: str = "ko",
        **kwargs
    ) -> GeneratedReport:
        """
        평가 결과를 자연어 리포트로 변환
        
        Args:
            evaluation_results: RAI 평가 결과 딕셔너리
            audience: 대상 청중 (executive/technical/regulatory/public)
            language: 출력 언어 (ko/en/ja/zh)
            **kwargs: 추가 설정
        
        Returns:
            GeneratedReport: 생성된 리포트 객체
        """
        # 청중 및 언어 변환
        audience_type = AudienceType(audience)
        lang = Language(language)
        
        # 프롬프트 구성
        prompt = self._build_prompt(evaluation_results, audience_type, lang)
        
        # LLM 호출
        logger.info(f"리포트 생성 시작: audience={audience}, language={language}")
        response = self._provider.generate(prompt)
        
        # 응답 파싱
        report = self._parse_response(response, audience_type, lang)
        
        # 시각화 추가 (설정에 따라)
        if self.config.include_visualizations:
            report.visualizations = self._generate_visualizations(evaluation_results)
        
        logger.info("리포트 생성 완료")
        return report
    
    def _build_prompt(
        self,
        evaluation_results: Dict[str, Any],
        audience: AudienceType,
        language: Language
    ) -> str:
        """프롬프트 구성"""
        base_prompt = self.AUDIENCE_PROMPTS[audience]
        lang_settings = self.LANGUAGE_SETTINGS[language]
        
        # 언어 지시사항 추가
        if language != Language.ENGLISH:
            lang_instruction = f"\n\n모든 내용은 {language.name}로 작성해주세요."
        else:
            lang_instruction = ""
        
        # 평가 결과 JSON 변환
        results_json = json.dumps(evaluation_results, indent=2, ensure_ascii=False)
        
        prompt = f"""
{base_prompt}
{lang_instruction}

## 평가 결과 데이터:
```json
{results_json}
```

## 출력 형식:
다음 JSON 형식으로 응답해주세요:
{{
    "title": "리포트 제목",
    "summary": "전체 요약 (2-3 문단)",
    "sections": [
        {{"title": "섹션 제목", "content": "섹션 내용"}},
        ...
    ],
    "recommendations": ["권고사항 1", "권고사항 2", ...],
    "risk_level": "low/medium/high/critical"
}}
"""
        return prompt
    
    def _parse_response(
        self,
        response: str,
        audience: AudienceType,
        language: Language
    ) -> GeneratedReport:
        """LLM 응답 파싱"""
        try:
            # JSON 추출 시도
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # JSON이 없으면 텍스트로 처리
                data = {
                    "title": self.LANGUAGE_SETTINGS[language]["title_prefix"],
                    "summary": response,
                    "sections": [],
                    "recommendations": []
                }
        except json.JSONDecodeError:
            data = {
                "title": self.LANGUAGE_SETTINGS[language]["title_prefix"],
                "summary": response,
                "sections": [],
                "recommendations": []
            }
        
        return GeneratedReport(
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            sections=data.get("sections", []),
            recommendations=data.get("recommendations", []),
            visualizations=[],
            metadata={
                "audience": audience.value,
                "language": language.value,
                "risk_level": data.get("risk_level", "unknown")
            }
        )
    
    def _generate_visualizations(
        self,
        evaluation_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """시각화 데이터 생성"""
        visualizations = []
        
        # 공정성 메트릭 차트
        if "fairness" in evaluation_results:
            visualizations.append({
                "type": "radar",
                "title": "공정성 메트릭",
                "data": evaluation_results["fairness"]
            })
        
        # 전체 점수 게이지
        if "overall_score" in evaluation_results:
            visualizations.append({
                "type": "gauge",
                "title": "전체 RAI 점수",
                "value": evaluation_results["overall_score"]
            })
        
        return visualizations
    
    def explain_metric(
        self,
        metric_name: str,
        metric_value: float,
        threshold: float,
        language: str = "ko"
    ) -> str:
        """
        특정 메트릭을 비전문가도 이해할 수 있도록 설명
        
        Args:
            metric_name: 메트릭 이름
            metric_value: 메트릭 값
            threshold: 임계값
            language: 출력 언어
        
        Returns:
            자연어 설명
        """
        prompt = f"""
다음 AI 평가 메트릭을 비전문가도 이해할 수 있도록 설명해주세요.

메트릭: {metric_name}
측정값: {metric_value}
기준값: {threshold}

설명은 {language}로 작성하고, 다음을 포함해주세요:
1. 이 메트릭이 무엇을 의미하는지
2. 현재 값이 좋은지 나쁜지
3. 일상생활 비유로 설명
"""
        return self._provider.generate(prompt)
    
    def generate_recommendations(
        self,
        issues: List[Dict[str, Any]],
        context: Dict[str, Any],
        language: str = "ko"
    ) -> List[str]:
        """
        발견된 문제에 대한 맞춤형 개선 권고안 생성
        
        Args:
            issues: 발견된 문제 목록
            context: 추가 컨텍스트 (산업, 규제 등)
            language: 출력 언어
        
        Returns:
            권고안 목록
        """
        prompt = f"""
다음 AI 시스템 문제점에 대한 구체적인 개선 권고안을 생성해주세요.

문제점:
{json.dumps(issues, indent=2, ensure_ascii=False)}

컨텍스트:
{json.dumps(context, indent=2, ensure_ascii=False)}

각 권고안은 다음을 포함해야 합니다:
- 구체적인 조치 사항
- 예상 효과
- 구현 난이도

{language}로 작성해주세요. JSON 배열 형식으로 응답해주세요.
"""
        response = self._provider.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        return [response]
