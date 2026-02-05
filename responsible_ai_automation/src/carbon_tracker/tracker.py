"""
AI 탄소 발자국 추적기

AI 작업의 에너지 소비와 탄소 배출을 실시간으로 추적합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
import logging
import time
import os
import platform

logger = logging.getLogger(__name__)


@dataclass
class EnergyMeasurement:
    """에너지 측정 결과"""
    timestamp: datetime
    duration_seconds: float
    cpu_energy_kwh: float
    gpu_energy_kwh: float
    memory_energy_kwh: float
    total_energy_kwh: float
    power_watts: float


@dataclass
class TrackingSession:
    """추적 세션"""
    id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    measurements: List[EnergyMeasurement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def total_energy_kwh(self) -> float:
        return sum(m.total_energy_kwh for m in self.measurements)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "total_energy_kwh": self.total_energy_kwh,
            "measurement_count": len(self.measurements),
            "metadata": self.metadata
        }


class CarbonFootprintTracker:
    """
    AI 탄소 발자국 추적기
    
    AI 모델 학습 및 추론의 에너지 소비와 탄소 배출을 추적합니다.
    
    Example:
        >>> tracker = CarbonFootprintTracker(region="asia-east2")
        >>> 
        >>> with tracker.track("training"):
        ...     model.train(epochs=10)
        >>> 
        >>> report = tracker.get_report()
        >>> print(f"CO2: {report.total_emissions_kg}kg")
    """
    
    # 지역별 탄소 집약도 (kg CO2/kWh)
    CARBON_INTENSITY = {
        # 한국
        "asia-east2": 0.5,       # 서울
        "korea": 0.5,
        # 미국
        "us-east1": 0.45,
        "us-west1": 0.25,       # 캘리포니아 (재생에너지 높음)
        "us-central1": 0.48,
        # 유럽
        "europe-west1": 0.2,    # 벨기에
        "europe-north1": 0.02,  # 핀란드 (매우 낮음)
        # 아시아
        "asia-northeast1": 0.5,  # 도쿄
        "asia-south1": 0.7,     # 인도
        # 기본값
        "default": 0.475
    }
    
    # 하드웨어별 전력 소비 (와트)
    HARDWARE_POWER = {
        "cpu": {
            "idle": 50,
            "active": 100,
            "max": 150
        },
        "gpu": {
            "idle": 30,
            "active": 250,      # 일반 GPU
            "nvidia_a100": 400,
            "nvidia_v100": 300,
            "nvidia_t4": 70,
            "amd_mi250": 560
        },
        "memory": {
            "per_gb": 0.375     # GB당 와트
        }
    }
    
    def __init__(
        self,
        region: str = "default",
        auto_detect_hardware: bool = True
    ):
        """
        Args:
            region: 데이터센터 지역 (탄소 집약도 계산용)
            auto_detect_hardware: 하드웨어 자동 감지
        """
        self.region = region
        self.carbon_intensity = self.CARBON_INTENSITY.get(
            region, 
            self.CARBON_INTENSITY["default"]
        )
        
        self._sessions: Dict[str, TrackingSession] = {}
        self._active_session: Optional[TrackingSession] = None
        
        # 하드웨어 정보
        self._hardware_info = self._detect_hardware() if auto_detect_hardware else {}
        
        logger.info(
            f"CarbonFootprintTracker 초기화: region={region}, "
            f"carbon_intensity={self.carbon_intensity}kg CO2/kWh"
        )
    
    def _detect_hardware(self) -> Dict[str, Any]:
        """하드웨어 정보 감지"""
        info = {
            "platform": platform.system(),
            "cpu_count": os.cpu_count(),
            "gpu_available": False,
            "gpu_name": None
        }
        
        # GPU 감지 시도
        try:
            import torch
            if torch.cuda.is_available():
                info["gpu_available"] = True
                info["gpu_name"] = torch.cuda.get_device_name(0)
                info["gpu_count"] = torch.cuda.device_count()
        except ImportError:
            pass
        
        return info
    
    @contextmanager
    def track(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        컨텍스트 매니저로 에너지 소비 추적
        
        Args:
            name: 추적 세션 이름
            metadata: 추가 메타데이터
        
        Example:
            >>> with tracker.track("inference"):
            ...     result = model.predict(data)
        """
        session = self.start_session(name, metadata)
        try:
            yield session
        finally:
            self.end_session(session.id)
    
    def start_session(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TrackingSession:
        """추적 세션 시작"""
        import uuid
        
        session_id = str(uuid.uuid4())[:8]
        session = TrackingSession(
            id=session_id,
            name=name,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        self._sessions[session_id] = session
        self._active_session = session
        
        logger.info(f"추적 세션 시작: {name} (id={session_id})")
        return session
    
    def end_session(self, session_id: str) -> TrackingSession:
        """추적 세션 종료"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"세션을 찾을 수 없음: {session_id}")
        
        session.end_time = datetime.now()
        
        # 에너지 측정
        measurement = self._measure_energy(session.duration_seconds)
        session.measurements.append(measurement)
        
        if self._active_session and self._active_session.id == session_id:
            self._active_session = None
        
        logger.info(
            f"추적 세션 종료: {session.name} "
            f"(duration={session.duration_seconds:.1f}s, "
            f"energy={measurement.total_energy_kwh:.6f}kWh)"
        )
        
        return session
    
    def _measure_energy(self, duration_seconds: float) -> EnergyMeasurement:
        """에너지 소비 측정"""
        # CPU 에너지 (간단한 추정)
        cpu_power = self.HARDWARE_POWER["cpu"]["active"]
        cpu_energy_kwh = (cpu_power * duration_seconds) / 3600000
        
        # GPU 에너지
        gpu_power = 0
        if self._hardware_info.get("gpu_available"):
            gpu_name = self._hardware_info.get("gpu_name", "").lower()
            if "a100" in gpu_name:
                gpu_power = self.HARDWARE_POWER["gpu"]["nvidia_a100"]
            elif "v100" in gpu_name:
                gpu_power = self.HARDWARE_POWER["gpu"]["nvidia_v100"]
            elif "t4" in gpu_name:
                gpu_power = self.HARDWARE_POWER["gpu"]["nvidia_t4"]
            else:
                gpu_power = self.HARDWARE_POWER["gpu"]["active"]
        gpu_energy_kwh = (gpu_power * duration_seconds) / 3600000
        
        # 메모리 에너지 (추정)
        memory_gb = 16  # 기본값
        memory_power = memory_gb * self.HARDWARE_POWER["memory"]["per_gb"]
        memory_energy_kwh = (memory_power * duration_seconds) / 3600000
        
        total_energy = cpu_energy_kwh + gpu_energy_kwh + memory_energy_kwh
        total_power = cpu_power + gpu_power + memory_power
        
        return EnergyMeasurement(
            timestamp=datetime.now(),
            duration_seconds=duration_seconds,
            cpu_energy_kwh=cpu_energy_kwh,
            gpu_energy_kwh=gpu_energy_kwh,
            memory_energy_kwh=memory_energy_kwh,
            total_energy_kwh=total_energy,
            power_watts=total_power
        )
    
    def calculate_emissions(
        self,
        energy_kwh: float,
        region: Optional[str] = None
    ) -> float:
        """
        에너지 소비량으로부터 CO2 배출량 계산
        
        Args:
            energy_kwh: 에너지 소비량 (kWh)
            region: 지역 (없으면 기본 지역 사용)
        
        Returns:
            CO2 배출량 (kg)
        """
        intensity = self.CARBON_INTENSITY.get(
            region or self.region,
            self.CARBON_INTENSITY["default"]
        )
        return energy_kwh * intensity
    
    def get_session(self, session_id: str) -> Optional[TrackingSession]:
        """세션 조회"""
        return self._sessions.get(session_id)
    
    def get_all_sessions(self) -> List[TrackingSession]:
        """모든 세션 조회"""
        return list(self._sessions.values())
    
    def get_total_energy(self) -> float:
        """총 에너지 소비량 (kWh)"""
        return sum(s.total_energy_kwh for s in self._sessions.values())
    
    def get_total_emissions(self) -> float:
        """총 CO2 배출량 (kg)"""
        return self.calculate_emissions(self.get_total_energy())
    
    def get_summary(self) -> Dict[str, Any]:
        """추적 요약"""
        total_energy = self.get_total_energy()
        total_emissions = self.get_total_emissions()
        
        return {
            "region": self.region,
            "carbon_intensity": self.carbon_intensity,
            "total_sessions": len(self._sessions),
            "total_energy_kwh": total_energy,
            "total_emissions_kg_co2": total_emissions,
            "equivalent_trees_year": total_emissions / 21,  # 나무 1그루 = 연간 21kg CO2 흡수
            "equivalent_car_km": total_emissions / 0.21,    # 자동차 1km = 0.21kg CO2
            "hardware_info": self._hardware_info
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """최적화 권고사항"""
        recommendations = []
        
        total_energy = self.get_total_energy()
        
        # 지역 기반 권고
        if self.carbon_intensity > 0.4:
            recommendations.append(
                f"현재 지역({self.region})의 탄소 집약도가 높습니다. "
                f"재생에너지 비율이 높은 지역(예: europe-north1)으로 마이그레이션을 고려하세요."
            )
        
        # GPU 사용 기반 권고
        if self._hardware_info.get("gpu_available"):
            recommendations.append(
                "Mixed Precision Training (FP16)을 사용하여 GPU 에너지 소비를 30-50% 절감할 수 있습니다."
            )
        
        # 일반 권고
        recommendations.extend([
            "모델 양자화(Quantization)를 통해 추론 에너지를 최대 4배 절감할 수 있습니다.",
            "Knowledge Distillation으로 더 작은 모델을 학습하여 효율성을 높이세요.",
            "배치 추론을 사용하여 개별 요청 대비 에너지 효율을 개선하세요."
        ])
        
        return recommendations
    
    def clear(self):
        """모든 세션 초기화"""
        self._sessions.clear()
        self._active_session = None
