from __future__ import annotations

from dataclasses import dataclass

from app.models.entities import Agent, Task


@dataclass
class RouteDecision:
    tier: str
    adapter_profile: str
    reason: str


class RoutingPolicyService:
    def decide(self, task: Task) -> RouteDecision:
        scope = task.scope or {}
        adapter = scope.get('adapter') if isinstance(scope.get('adapter'), dict) else {}
        explicit_tier = adapter.get('tier') or scope.get('tier')
        explicit_profile = adapter.get('profile') or scope.get('adapter_profile')

        if isinstance(explicit_tier, str) and explicit_tier.strip():
            tier = explicit_tier.strip()
            reason = 'scope override'
        elif task.priority >= 4:
            tier = 'frontier'
            reason = 'priority>=4'
        else:
            tier = 'small'
            reason = 'default'

        if isinstance(explicit_profile, str) and explicit_profile.strip():
            profile = explicit_profile.strip()
        else:
            profile = 'generic-shell'

        return RouteDecision(tier=tier, adapter_profile=profile, reason=reason)

    def supports(self, agent: Agent, decision: RouteDecision) -> bool:
        caps = agent.capabilities or {}
        tiers = caps.get('model_tiers')
        profiles = caps.get('adapter_profiles')

        tier_ok = True
        if isinstance(tiers, list) and tiers:
            tier_ok = decision.tier in tiers

        profile_ok = True
        if isinstance(profiles, list) and profiles:
            profile_ok = decision.adapter_profile in profiles

        return tier_ok and profile_ok
