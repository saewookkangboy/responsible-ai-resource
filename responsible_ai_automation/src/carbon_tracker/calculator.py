"""
탄소 배출량 계산기

정확한 탄소 배출량 계산을 위한 유틸리티입니다.
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class EmissionFactor(Enum):
    """배출 계수 유형"""
    GRID_ELECTRICITY = "grid_electricity"
    RENEWABLE = "renewable"
    NATURAL_GAS = "natural_gas"
    DIESEL = "diesel"


@dataclass
class CarbonEstimate:
    """탄소 배출 추정치"""
    energy_kwh: float
    emissions_kg_co2: float
    emissions_kg_co2e: float  # CO2 equivalent
    region: str
    methodology: str
    confidence: float  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "energy_kwh": self.energy_kwh,
            "emissions_kg_co2": self.emissions_kg_co2,
            "emissions_kg_co2e": self.emissions_kg_co2e,
            "region": self.region,
            "methodology": self.methodology,
            "confidence": self.confidence
        }


class CarbonCalculator:
    """
    탄소 배출량 계산기
    
    다양한 소스와 지역에 대한 정확한 탄소 배출량을 계산합니다.
    """
    
    # 국가별 그리드 탄소 집약도 (kg CO2/kWh) - 2024년 기준
    COUNTRY_INTENSITY = {
        "KR": 0.495,   # 한국
        "US": 0.417,   # 미국
        "CN": 0.581,   # 중국
        "JP": 0.506,   # 일본
        "DE": 0.385,   # 독일
        "FR": 0.056,   # 프랑스 (원자력)
        "UK": 0.233,   # 영국
        "AU": 0.656,   # 호주
        "IN": 0.708,   # 인도
        "BR": 0.074,   # 브라질 (수력)
        "SE": 0.013,   # 스웨덴
        "NO": 0.017,   # 노르웨이
    }
    
    # 클라우드 지역별 탄소 집약도
    CLOUD_REGION_INTENSITY = {
        # GCP
        "us-central1": 0.479,
        "us-east1": 0.425,
        "us-east4": 0.361,
        "us-west1": 0.068,
        "us-west4": 0.213,
        "europe-west1": 0.196,
        "europe-west4": 0.164,
        "europe-north1": 0.024,
        "asia-east1": 0.541,
        "asia-east2": 0.360,
        "asia-northeast1": 0.506,
        "asia-northeast3": 0.495,
        "asia-south1": 0.708,
        # AWS
        "us-east-1": 0.415,
        "us-west-2": 0.349,
        "eu-west-1": 0.296,
        "eu-north-1": 0.008,
        "ap-northeast-1": 0.506,
        "ap-northeast-2": 0.495,
        # Azure
        "eastus": 0.415,
        "westus2": 0.349,
        "northeurope": 0.296,
        "koreacentral": 0.495,
    }
    
    # GPU 전력 소비 데이터 (와트)
    GPU_POWER_CONSUMPTION = {
        "nvidia_a100": {"tdp": 400, "typical": 250},
        "nvidia_h100": {"tdp": 700, "typical": 450},
        "nvidia_v100": {"tdp": 300, "typical": 200},
        "nvidia_t4": {"tdp": 70, "typical": 50},
        "nvidia_rtx_3090": {"tdp": 350, "typical": 280},
        "nvidia_rtx_4090": {"tdp": 450, "typical": 350},
        "amd_mi250": {"tdp": 560, "typical": 400},
        "amd_mi300x": {"tdp": 750, "typical": 550},
    }
    
    def __init__(self):
        pass
    
    def calculate_training_emissions(
        self,
        gpu_hours: float,
        gpu_type: str = "nvidia_a100",
        num_gpus: int = 1,
        region: str = "us-central1",
        pue: float = 1.1  # Power Usage Effectiveness
    ) -> CarbonEstimate:
        """
        모델 학습의 탄소 배출량 계산
        
        Args:
            gpu_hours: 총 GPU 시간
            gpu_type: GPU 유형
            num_gpus: GPU 수
            region: 데이터센터 지역
            pue: 전력 사용 효율성 (1.0 = 완벽)
        
        Returns:
            탄소 배출 추정치
        """
        # GPU 전력 소비
        gpu_power = self.GPU_POWER_CONSUMPTION.get(
            gpu_type, 
            {"typical": 250}
        )["typical"]
        
        # 에너지 계산 (kWh)
        energy_kwh = (gpu_power * num_gpus * gpu_hours / 1000) * pue
        
        # 탄소 집약도
        carbon_intensity = self.CLOUD_REGION_INTENSITY.get(
            region,
            0.475  # 세계 평균
        )
        
        # 배출량 계산
        emissions_kg = energy_kwh * carbon_intensity
        
        return CarbonEstimate(
            energy_kwh=energy_kwh,
            emissions_kg_co2=emissions_kg,
            emissions_kg_co2e=emissions_kg * 1.05,  # 메탄 등 고려
            region=region,
            methodology="GPU-hours based estimation",
            confidence=0.8
        )
    
    def calculate_inference_emissions(
        self,
        num_requests: int,
        avg_latency_ms: float,
        gpu_type: str = "nvidia_t4",
        num_gpus: int = 1,
        region: str = "us-central1"
    ) -> CarbonEstimate:
        """
        추론의 탄소 배출량 계산
        
        Args:
            num_requests: 요청 수
            avg_latency_ms: 평균 지연시간 (밀리초)
            gpu_type: GPU 유형
            num_gpus: GPU 수
            region: 데이터센터 지역
        
        Returns:
            탄소 배출 추정치
        """
        # 총 처리 시간 (시간)
        total_hours = (num_requests * avg_latency_ms) / (1000 * 3600)
        
        return self.calculate_training_emissions(
            gpu_hours=total_hours,
            gpu_type=gpu_type,
            num_gpus=num_gpus,
            region=region,
            pue=1.1
        )
    
    def calculate_llm_inference_emissions(
        self,
        num_tokens: int,
        model_size: str = "7B",
        region: str = "us-central1"
    ) -> CarbonEstimate:
        """
        LLM 추론의 탄소 배출량 계산
        
        Args:
            num_tokens: 생성된 토큰 수
            model_size: 모델 크기 (7B, 13B, 70B 등)
            region: 데이터센터 지역
        
        Returns:
            탄소 배출 추정치
        """
        # 모델 크기별 토큰당 에너지 (Wh)
        energy_per_token = {
            "7B": 0.001,
            "13B": 0.002,
            "70B": 0.01,
            "175B": 0.025,
        }
        
        wh_per_token = energy_per_token.get(model_size, 0.005)
        energy_kwh = (num_tokens * wh_per_token) / 1000
        
        carbon_intensity = self.CLOUD_REGION_INTENSITY.get(region, 0.475)
        emissions_kg = energy_kwh * carbon_intensity
        
        return CarbonEstimate(
            energy_kwh=energy_kwh,
            emissions_kg_co2=emissions_kg,
            emissions_kg_co2e=emissions_kg * 1.05,
            region=region,
            methodology="Token-based LLM estimation",
            confidence=0.6
        )
    
    def compare_regions(
        self,
        energy_kwh: float,
        regions: Optional[list] = None
    ) -> Dict[str, float]:
        """
        여러 지역의 배출량 비교
        
        Args:
            energy_kwh: 에너지 소비량
            regions: 비교할 지역 목록 (없으면 주요 지역 비교)
        
        Returns:
            지역별 배출량
        """
        if regions is None:
            regions = [
                "us-west1", "us-east1", "europe-north1",
                "europe-west1", "asia-northeast1", "asia-northeast3"
            ]
        
        return {
            region: energy_kwh * self.CLOUD_REGION_INTENSITY.get(region, 0.475)
            for region in regions
        }
    
    def get_equivalent_activities(
        self,
        emissions_kg_co2: float
    ) -> Dict[str, float]:
        """
        배출량의 일상 활동 등가치 계산
        
        Args:
            emissions_kg_co2: CO2 배출량 (kg)
        
        Returns:
            등가 활동
        """
        return {
            "car_km": emissions_kg_co2 / 0.21,           # 자동차 운행
            "flights_nyc_sf": emissions_kg_co2 / 900,   # 뉴욕-샌프란시스코 비행
            "smartphone_charges": emissions_kg_co2 / 0.008,  # 스마트폰 충전
            "led_bulb_hours": emissions_kg_co2 / 0.01,  # LED 전구 사용
            "trees_year_offset": emissions_kg_co2 / 21,  # 나무 1년 흡수량
            "beef_kg": emissions_kg_co2 / 27,           # 소고기 생산
        }
