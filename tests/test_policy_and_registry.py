from bear.domain.enums import PermissionLevel
from bear.policy.permissions import PermissionPolicy
from bear.tools.registry import build_default_registry


def test_permission_policy_prefers_context_override() -> None:
    policy = PermissionPolicy(
        defaults={'edit': PermissionLevel.REQUEST},
        context_overrides={'safe': {'edit': PermissionLevel.ALLOW}},
    )

    decision = policy.resolve('edit', context='safe')

    assert decision.level == PermissionLevel.ALLOW


def test_default_registry_contains_expected_tools() -> None:
    registry = build_default_registry()

    names = {tool.name for tool in registry.list()}

    assert {'read', 'edit', 'run_experiment', 'submit_slurm_job', 'notify_human'}.issubset(names)
