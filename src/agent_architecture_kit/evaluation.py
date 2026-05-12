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
