"""
멀티모달 AI 공정성 검증 모듈

이미지, 비디오, 오디오 AI 모델의 공정성을 전문적으로 검증합니다.

주요 기능:
- 얼굴 인식 편향 테스트
- 비디오 분석 공정성 검증
- 음성 인식 다양성 테스트
- 교차 모달 편향 분석

사용 예시:
    from src.multimodal import MultimodalFairnessValidator
    
    validator = MultimodalFairnessValidator()
    
    # 얼굴 인식 편향 테스트
    results = validator.test_facial_recognition_bias(
        model=face_model,
        test_dataset=diverse_faces
    )
    
    # 결과 확인
    for demographic, accuracy in results.accuracy_by_group.items():
        print(f"{demographic}: {accuracy:.2%}")
"""

from .validator import MultimodalFairnessValidator, ValidationResult
from .face_bias import FacialRecognitionBiasTester, DemographicGroup
from .audio_bias import AudioBiasTester, AccentType
from .cross_modal import CrossModalAnalyzer

__all__ = [
    "MultimodalFairnessValidator",
    "ValidationResult",
    "FacialRecognitionBiasTester",
    "DemographicGroup",
    "AudioBiasTester",
    "AccentType",
    "CrossModalAnalyzer",
]

__version__ = "0.1.0"
