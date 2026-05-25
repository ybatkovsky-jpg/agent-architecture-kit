from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Scenario:
    scenario_id: str
    name: str
    request_class: str
    pass_criteria: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReleaseVerdict:
    recommendation: str
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EscalationVerdict:
    allowed: bool
    reason: str


def protected_refresh_allowed(*, protected_passed: bool, sampled_regressions: int, blockers_empty: bool, recommendation: str) -> bool:
    return (
        recommendation == "bootstrap_refresh_baseline"
        and protected_passed
        and sampled_regressions == 0
        and blockers_empty
    )


def release_recommendation(*, continuation_ok: bool, audit_ok: bool, preference_safe: bool, status_reproven: bool) -> ReleaseVerdict:
    reasons: list[str] = []
    if not continuation_ok:
        reasons.append("continuation not yet reliable enough")
    if not audit_ok:
        reasons.append("audit trace not yet reliable enough")
    if not preference_safe:
        reasons.append("preference recall not yet safely closed")
    if not status_reproven:
        reasons.append("status lane not yet strongly reproven")

    if reasons:
        return ReleaseVerdict(recommendation="continue_hardening", reasons=reasons)
    return ReleaseVerdict(recommendation="bounded_release_candidate", reasons=[])


def escalation_allowed(
    *,
    retry_budget_exhausted: bool = False,
    authority_boundary_hit: bool = False,
    information_boundary_hit: bool = False,
    scope_expands_to_different_task: bool = False,
    risk_boundary_crossed: bool = False,
    observation_deadline_reached: bool = False,
    next_strong_move_known: bool = False,
    can_execute_with_current_authority: bool = False,
    same_task_frontier: bool = True,
    would_stop_as_chat_noise: bool = False,
) -> EscalationVerdict:
    real_trigger = any(
        [
            retry_budget_exhausted,
            authority_boundary_hit,
            information_boundary_hit,
            scope_expands_to_different_task,
            risk_boundary_crossed,
            observation_deadline_reached,
        ]
    )

    false_blocker = (
        next_strong_move_known
        and can_execute_with_current_authority
        and same_task_frontier
        and would_stop_as_chat_noise
        and not real_trigger
    )

    if false_blocker:
        return EscalationVerdict(
            allowed=False,
            reason="false_blocker: continue with the next bounded leaf instead of escalating",
        )

    if real_trigger:
        return EscalationVerdict(
            allowed=True,
            reason="real escalation trigger present",
        )

    return EscalationVerdict(
        allowed=False,
        reason="no escalation trigger present",
    )
