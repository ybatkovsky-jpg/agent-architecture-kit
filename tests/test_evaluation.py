from agent_architecture_kit.evaluation import escalation_allowed, protected_refresh_allowed, release_recommendation


def test_protected_refresh_allowed_only_when_all_conditions_hold() -> None:
    assert protected_refresh_allowed(
        protected_passed=True,
        sampled_regressions=0,
        blockers_empty=True,
        recommendation="bootstrap_refresh_baseline",
    )
    assert not protected_refresh_allowed(
        protected_passed=True,
        sampled_regressions=1,
        blockers_empty=True,
        recommendation="bootstrap_refresh_baseline",
    )


def test_release_recommendation_blocks_when_high_risk_lanes_are_not_closed() -> None:
    verdict = release_recommendation(
        continuation_ok=True,
        audit_ok=True,
        preference_safe=False,
        status_reproven=False,
    )
    assert verdict.recommendation == "continue_hardening"
    assert len(verdict.reasons) == 2


def test_release_recommendation_allows_bounded_candidate_when_all_core_lanes_are_clean() -> None:
    verdict = release_recommendation(
        continuation_ok=True,
        audit_ok=True,
        preference_safe=True,
        status_reproven=True,
    )
    assert verdict.recommendation == "bounded_release_candidate"


def test_escalation_allowed_blocks_false_blocker_when_next_move_is_actionable() -> None:
    verdict = escalation_allowed(
        next_strong_move_known=True,
        can_execute_with_current_authority=True,
        same_task_frontier=True,
        would_stop_as_chat_noise=True,
    )
    assert not verdict.allowed
    assert verdict.reason.startswith("false_blocker")


def test_escalation_allowed_permits_real_authority_boundary() -> None:
    verdict = escalation_allowed(
        authority_boundary_hit=True,
        next_strong_move_known=True,
        can_execute_with_current_authority=False,
        same_task_frontier=True,
        would_stop_as_chat_noise=False,
    )
    assert verdict.allowed
    assert verdict.reason == "real escalation trigger present"


def test_escalation_allowed_rejects_empty_escalation_without_real_trigger() -> None:
    verdict = escalation_allowed()
    assert not verdict.allowed
    assert verdict.reason == "no escalation trigger present"
