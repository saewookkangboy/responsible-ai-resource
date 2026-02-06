"""
Circuit Breaker 패턴 구현

에이전트의 비정상 동작 시 자동으로 중단시키는 메커니즘을 제공합니다.
"""

from typing import Optional, Callable, Any
from enum import Enum
from datetime import datetime, timedelta
import threading
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit Breaker 상태"""
    CLOSED = "closed"      # 정상 작동
    OPEN = "open"          # 차단됨
    HALF_OPEN = "half_open"  # 테스트 중


class CircuitBreaker:
    """
    Circuit Breaker
    
    연속 실패 시 자동으로 호출을 차단하고,
    일정 시간 후 테스트 호출을 허용합니다.
    
    Example:
        >>> cb = CircuitBreaker(max_failures=3, reset_timeout=60)
        >>> 
        >>> try:
        ...     result = cb.call(risky_function, args)
        ... except CircuitBreakerOpenError:
        ...     print("회로 차단됨")
    """
    
    def __init__(
        self,
        max_failures: int = 5,
        reset_timeout: float = 60.0,
        half_open_max_calls: int = 1
    ):
        """
        Args:
            max_failures: 회로 오픈 전 최대 실패 횟수
            reset_timeout: 회로 리셋까지 대기 시간 (초)
            half_open_max_calls: half-open 상태에서 허용할 테스트 호출 수
        """
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._open_reason = ""
        self._half_open_calls = 0
        
        self._lock = threading.Lock()
        
        # 콜백
        self._on_open: Optional[Callable] = None
        self._on_close: Optional[Callable] = None
        self._on_half_open: Optional[Callable] = None
    
    @property
    def state(self) -> CircuitState:
        """현재 상태"""
        with self._lock:
            self._check_state_transition()
            return self._state
    
    @property
    def is_open(self) -> bool:
        """회로가 열려있는지 (차단 상태)"""
        return self.state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """회로가 닫혀있는지 (정상 상태)"""
        return self.state == CircuitState.CLOSED
    
    @property
    def failure_count(self) -> int:
        """현재 실패 횟수"""
        return self._failure_count
    
    def _check_state_transition(self):
        """상태 전환 확인"""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                if elapsed >= self.reset_timeout:
                    self._transition_to_half_open()
    
    def _transition_to_half_open(self):
        """half-open 상태로 전환"""
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        logger.info("Circuit Breaker: OPEN -> HALF_OPEN")
        
        if self._on_half_open:
            try:
                self._on_half_open()
            except Exception as e:
                logger.error(f"half-open 콜백 오류: {e}")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        함수 호출 (Circuit Breaker 적용)
        
        Args:
            func: 호출할 함수
            *args, **kwargs: 함수 인자
        
        Returns:
            함수 반환값
        
        Raises:
            CircuitBreakerOpenError: 회로가 열려있을 때
        """
        state = self.state
        
        if state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit Breaker 열림: {self._open_reason}"
            )
        
        if state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        "Half-open 상태에서 최대 테스트 호출 초과"
                    )
                self._half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(str(e))
            raise
    
    def record_success(self):
        """성공 기록"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                # half-open에서 성공하면 closed로
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                logger.info("Circuit Breaker: HALF_OPEN -> CLOSED")
                
                if self._on_close:
                    try:
                        self._on_close()
                    except Exception as e:
                        logger.error(f"close 콜백 오류: {e}")
            else:
                self._failure_count = max(0, self._failure_count - 1)
    
    def record_failure(self, reason: str = ""):
        """실패 기록"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                # half-open에서 실패하면 다시 open
                self._state = CircuitState.OPEN
                self._open_reason = reason or "half-open 테스트 실패"
                logger.warning(f"Circuit Breaker: HALF_OPEN -> OPEN ({reason})")
            
            elif self._failure_count >= self.max_failures:
                self._state = CircuitState.OPEN
                self._open_reason = reason or f"연속 {self._failure_count}회 실패"
                logger.warning(f"Circuit Breaker: CLOSED -> OPEN ({self._open_reason})")
                
                if self._on_open:
                    try:
                        self._on_open(self._open_reason)
                    except Exception as e:
                        logger.error(f"open 콜백 오류: {e}")
    
    def force_open(self, reason: str = "수동 오픈"):
        """강제로 회로 열기"""
        with self._lock:
            self._state = CircuitState.OPEN
            self._open_reason = reason
            self._last_failure_time = datetime.now()
            logger.warning(f"Circuit Breaker 강제 오픈: {reason}")
    
    def reset(self):
        """상태 초기화"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._open_reason = ""
            self._half_open_calls = 0
            logger.info("Circuit Breaker 리셋")
    
    def on_open(self, callback: Callable[[str], None]):
        """회로 오픈 시 콜백 등록"""
        self._on_open = callback
    
    def on_close(self, callback: Callable[[], None]):
        """회로 닫힘 시 콜백 등록"""
        self._on_close = callback
    
    def on_half_open(self, callback: Callable[[], None]):
        """half-open 전환 시 콜백 등록"""
        self._on_half_open = callback
    
    def get_status(self) -> dict:
        """현재 상태 정보"""
        return {
            "state": self.state.value,
            "failure_count": self._failure_count,
            "max_failures": self.max_failures,
            "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "open_reason": self._open_reason,
            "reset_timeout": self.reset_timeout
        }


class CircuitBreakerOpenError(Exception):
    """Circuit Breaker가 열려있을 때 발생하는 예외"""
    pass
