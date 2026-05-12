from agent_architecture_kit.evaluation import protected_refresh_allowed, release_recommendation


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
