"""
정책 시행 모듈

정책 위반 시 자동 조치를 수행합니다.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

from .policy import EnforcementLevel
from .validator import ValidationResult, PolicyViolation

logger = logging.getLogger(__name__)


class EnforcementAction(Enum):
    """시행 조치"""
    BLOCKED = "blocked"
    PENDING_APPROVAL = "pending_approval"
    WARNED = "warned"
    LOGGED = "logged"
    PASSED = "passed"


@dataclass
class EnforcementRecord:
    """시행 기록"""
    timestamp: datetime
    validation_result: ValidationResult
    action_taken: EnforcementAction
    approver: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "policy_name": self.validation_result.policy_name,
            "action_taken": self.action_taken.value,
            "violation_count": self.validation_result.violation_count,
            "approver": self.approver,
            "approval_timestamp": self.approval_timestamp.isoformat() if self.approval_timestamp else None,
            "notes": self.notes
        }


class PolicyEnforcer:
    """
    정책 시행자
    
    검증 결과에 따라 자동으로 조치를 수행합니다.
    
    Example:
        >>> enforcer = PolicyEnforcer()
        >>> enforcer.on_block(lambda r: notify_team(r))
        >>> enforcer.on_require_approval(lambda r: create_approval_ticket(r))
        >>> 
        >>> action = enforcer.enforce(validation_result)
        >>> if action == EnforcementAction.BLOCKED:
        ...     print("배포가 차단되었습니다.")
    """
    
    def __init__(self):
        self._handlers: Dict[EnforcementLevel, List[Callable]] = {
            level: [] for level in EnforcementLevel
        }
        self._history: List[EnforcementRecord] = []
        self._pending_approvals: Dict[str, EnforcementRecord] = {}
    
    def on_block(self, handler: Callable[[ValidationResult], None]):
        """차단 시 핸들러 등록"""
        self._handlers[EnforcementLevel.BLOCK].append(handler)
    
    def on_require_approval(self, handler: Callable[[ValidationResult], None]):
        """승인 필요 시 핸들러 등록"""
        self._handlers[EnforcementLevel.REQUIRE_APPROVAL].append(handler)
    
    def on_warn(self, handler: Callable[[ValidationResult], None]):
        """경고 시 핸들러 등록"""
        self._handlers[EnforcementLevel.WARN].append(handler)
    
    def on_log(self, handler: Callable[[ValidationResult], None]):
        """로깅 시 핸들러 등록"""
        self._handlers[EnforcementLevel.LOG].append(handler)
    
    def enforce(self, result: ValidationResult) -> EnforcementAction:
        """
        정책 시행
        
        Args:
            result: 검증 결과
        
        Returns:
            수행된 조치
        """
        if result.passed:
            action = EnforcementAction.PASSED
            logger.info("정책 검증 통과 - 추가 조치 없음")
        else:
            enforcement_level = result.enforcement_action or EnforcementLevel.WARN
            action = self._execute_enforcement(enforcement_level, result)
        
        # 기록 저장
        record = EnforcementRecord(
            timestamp=datetime.now(),
            validation_result=result,
            action_taken=action
        )
        self._history.append(record)
        
        if action == EnforcementAction.PENDING_APPROVAL:
            self._pending_approvals[result.policy_name] = record
        
        return action
    
    def _execute_enforcement(
        self,
        level: EnforcementLevel,
        result: ValidationResult
    ) -> EnforcementAction:
        """조치 실행"""
        # 핸들러 호출
        for handler in self._handlers.get(level, []):
            try:
                handler(result)
            except Exception as e:
                logger.error(f"핸들러 실행 실패: {e}")
        
        # 조치 매핑
        action_map = {
            EnforcementLevel.BLOCK: EnforcementAction.BLOCKED,
            EnforcementLevel.REQUIRE_APPROVAL: EnforcementAction.PENDING_APPROVAL,
            EnforcementLevel.WARN: EnforcementAction.WARNED,
            EnforcementLevel.LOG: EnforcementAction.LOGGED,
        }
        
        action = action_map.get(level, EnforcementAction.LOGGED)
        logger.info(f"정책 시행: {action.value}")
        
        return action
    
    def approve(
        self,
        policy_name: str,
        approver: str,
        notes: str = ""
    ) -> bool:
        """
        승인 대기 중인 항목 승인
        
        Args:
            policy_name: 정책 이름
            approver: 승인자
            notes: 승인 메모
        
        Returns:
            승인 성공 여부
        """
        if policy_name not in self._pending_approvals:
            logger.warning(f"승인 대기 중인 항목 없음: {policy_name}")
            return False
        
        record = self._pending_approvals[policy_name]
        record.approver = approver
        record.approval_timestamp = datetime.now()
        record.notes = notes
        record.action_taken = EnforcementAction.PASSED
        
        del self._pending_approvals[policy_name]
        logger.info(f"승인 완료: {policy_name} by {approver}")
        
        return True
    
    def reject(
        self,
        policy_name: str,
        rejector: str,
        reason: str = ""
    ) -> bool:
        """
        승인 대기 중인 항목 거부
        
        Args:
            policy_name: 정책 이름
            rejector: 거부자
            reason: 거부 사유
        
        Returns:
            거부 성공 여부
        """
        if policy_name not in self._pending_approvals:
            logger.warning(f"승인 대기 중인 항목 없음: {policy_name}")
            return False
        
        record = self._pending_approvals[policy_name]
        record.approver = rejector
        record.approval_timestamp = datetime.now()
        record.notes = f"거부 사유: {reason}"
        record.action_taken = EnforcementAction.BLOCKED
        
        del self._pending_approvals[policy_name]
        logger.info(f"거부됨: {policy_name} by {rejector}")
        
        return True
    
    def get_pending_approvals(self) -> List[EnforcementRecord]:
        """승인 대기 목록 조회"""
        return list(self._pending_approvals.values())
    
    def get_history(
        self,
        policy_name: Optional[str] = None,
        action: Optional[EnforcementAction] = None,
        limit: int = 100
    ) -> List[EnforcementRecord]:
        """
        시행 이력 조회
        
        Args:
            policy_name: 필터링할 정책 이름
            action: 필터링할 조치 유형
            limit: 최대 결과 수
        
        Returns:
            시행 기록 목록
        """
        filtered = self._history
        
        if policy_name:
            filtered = [r for r in filtered if r.validation_result.policy_name == policy_name]
        
        if action:
            filtered = [r for r in filtered if r.action_taken == action]
        
        return filtered[-limit:]
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """감사 리포트 생성"""
        total = len(self._history)
        by_action = {}
        
        for record in self._history:
            action = record.action_taken.value
            by_action[action] = by_action.get(action, 0) + 1
        
        return {
            "total_enforcements": total,
            "by_action": by_action,
            "pending_approvals": len(self._pending_approvals),
            "recent_blocks": [
                r.to_dict() for r in self._history[-10:]
                if r.action_taken == EnforcementAction.BLOCKED
            ]
        }


class CICDIntegration:
    """
    CI/CD 파이프라인 통합
    
    GitHub Actions, GitLab CI 등과의 통합을 지원합니다.
    """
    
    @staticmethod
    def github_actions_check(result: ValidationResult) -> Dict[str, Any]:
        """
        GitHub Actions Check 결과 생성
        
        Returns:
            GitHub Checks API 형식의 결과
        """
        conclusion = "success" if result.passed else "failure"
        
        annotations = []
        for v in result.violations:
            annotations.append({
                "path": ".",
                "start_line": 1,
                "end_line": 1,
                "annotation_level": "failure" if v.severity.value in ["critical", "high"] else "warning",
                "message": f"[{v.policy_area}] {v.message}",
                "title": v.requirement
            })
        
        return {
            "name": "AI Governance Policy Check",
            "status": "completed",
            "conclusion": conclusion,
            "output": {
                "title": f"Policy: {result.policy_name}",
                "summary": f"Violations: {result.violation_count}, Critical: {result.critical_count}",
                "annotations": annotations
            }
        }
    
    @staticmethod
    def gitlab_ci_job(result: ValidationResult) -> int:
        """
        GitLab CI Job 종료 코드 반환
        
        Returns:
            0 (성공) 또는 1 (실패)
        """
        return 0 if result.passed else 1
    
    @staticmethod
    def generate_badge(result: ValidationResult) -> str:
        """
        README 배지 생성
        
        Returns:
            Shields.io 배지 URL
        """
        if result.passed:
            color = "brightgreen"
            status = "passing"
        elif result.critical_count > 0:
            color = "red"
            status = "failing"
        else:
            color = "yellow"
            status = "warning"
        
        return f"![AI Governance](https://img.shields.io/badge/AI_Governance-{status}-{color})"
