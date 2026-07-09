"""Reasoning Chains — What makes AI bypass GPT-5/Opus level.
Multi-turn reasoning, self-correction, expert vs novice contrast, uncertainty.
"""
import random
from typing import Dict, List

# Multi-step reasoning chains (5-10 connected thoughts)
REASONING_CHAINS = {
    "debugging": [
        {"steps": [
            {"thought": "Users reporting 500 errors. Let me check error rate in Grafana.", "action": "check_monitoring", "confidence": 0.3},
            {"thought": "Error rate spiked at 14:32. Correlates with deploy. Checking what changed.", "action": "check_deploy_log", "confidence": 0.5},
            {"thought": "New code added N+1 query in user listing endpoint. But why only 500 errors?", "action": "check_db_connections", "confidence": 0.6},
            {"thought": "Connection pool at 50/50. N+1 query creating 100 connections per request. Pool exhausted.", "action": "identify_root_cause", "confidence": 0.9},
            {"thought": "Fix: add eager loading. Temporary: increase pool to 200. Permanent: fix query.", "action": "implement_fix", "confidence": 0.95},
            {"thought": "Deployed fix. Error rate back to 0%. Monitoring for 30 min.", "action": "verify_fix", "confidence": 0.98},
        ], "domain": "coding"},
        {"steps": [
            {"thought": "Build failing on CI. Error: 'Cannot find module ./config'. Works locally though.", "action": "read_error", "confidence": 0.2},
            {"thought": "File exists locally... wait. Is it a case sensitivity issue? Mac is case-insensitive, Linux CI is case-sensitive.", "action": "hypothesis", "confidence": 0.6},
            {"thought": "Yes! File is 'Config.ts' but import says './config'. Mac doesn't care, Linux does.", "action": "confirm_hypothesis", "confidence": 0.95},
            {"thought": "Renaming file to match import exactly. Also adding lint rule to catch this in future.", "action": "fix_and_prevent", "confidence": 0.99},
        ], "domain": "coding"},
        {"steps": [
            {"thought": "Memory usage growing 100MB/hour. Not an immediate crisis but will OOM in ~8 hours.", "action": "observe_pattern", "confidence": 0.3},
            {"thought": "Heap dump shows growing array in CacheManager. Objects never evicted.", "action": "profile_heap", "confidence": 0.6},
            {"thought": "TTL check: cache.set(key, value, ttl=0). Zero TTL means infinite! Should be 3600.", "action": "find_bug", "confidence": 0.9},
            {"thought": "Config had TTL in milliseconds but code expects seconds. 3600ms = 3.6s not 1 hour.", "action": "root_cause", "confidence": 0.95},
            {"thought": "Fixed unit mismatch. Added unit suffix to config key: cache_ttl_seconds. Clear naming prevents this.", "action": "fix_and_prevent", "confidence": 0.99},
        ], "domain": "coding"},
        {"steps": [
            {"thought": "API latency p99 went from 200ms to 2.3s after Thursday's deploy. What changed?", "action": "correlate_with_deploy", "confidence": 0.4},
            {"thought": "Thursday's PR added user preferences fetch on every request. But it's cached...", "action": "read_code", "confidence": 0.5},
            {"thought": "Cache key includes user-agent string. Every browser version = different key = cache miss.", "action": "identify_issue", "confidence": 0.85},
            {"thought": "Remove user-agent from cache key. Hit rate went from 2% to 94%. Latency back to 180ms.", "action": "fix", "confidence": 0.98},
        ], "domain": "coding"},
        {"steps": [
            {"thought": "Tests pass locally, fail in CI. Race condition? Let me run 100x locally.", "action": "reproduce", "confidence": 0.2},
            {"thought": "Failed on run 47. The async handler fires before DB seed completes.", "action": "narrow_down", "confidence": 0.7},
            {"thought": "Test needs await on setup. Setup was sync but handler is async. Timing luck locally.", "action": "root_cause", "confidence": 0.9},
            {"thought": "Added await. Also added a test helper that ensures setup complete before any test runs.", "action": "fix_systemic", "confidence": 0.99},
        ], "domain": "coding"},
    ],
    "trading_decision": [
        {"steps": [
            {"thought": "BTC at $67k. RSI overbought at 78. But trend is strong. Should I short or wait?", "action": "analyze_indicators", "confidence": 0.3},
            {"thought": "Checking funding rate: +0.03%. Longs paying shorts. Market overleveraged long.", "action": "check_funding", "confidence": 0.5},
            {"thought": "On-chain: exchange inflows increasing. Whales moving to exchanges to sell.", "action": "check_onchain", "confidence": 0.7},
            {"thought": "Multiple signals aligning bearish. But I've been wrong before at this level. Half size.", "action": "express_uncertainty", "confidence": 0.6},
            {"thought": "Opening short with 2% of portfolio. Stop at $69k. Target $62k. R:R is 2.5:1", "action": "execute_trade", "confidence": 0.7},
            {"thought": "Price dropped to $65k. Taking 50% off. Moving stop to entry. Free trade now.", "action": "manage_position", "confidence": 0.85},
        ], "domain": "finance"},
        {"steps": [
            {"thought": "NIFTY fell 3% today. My portfolio is down ₹2L. Should I panic sell?", "action": "assess_emotion", "confidence": 0.3},
            {"thought": "Checking: is my thesis still valid? Company fundamentals unchanged. Revenue growing 25% YoY.", "action": "validate_thesis", "confidence": 0.6},
            {"thought": "This is market-wide sell-off, not stock-specific. FII selling due to US rate concerns.", "action": "identify_cause", "confidence": 0.7},
            {"thought": "Historical: markets recovered from similar FII-driven selloffs in 2-4 weeks. Adding small position.", "action": "historical_context", "confidence": 0.75},
            {"thought": "Bought 20% more at these levels. If wrong, max loss is defined. If right, great avg price.", "action": "act_with_conviction", "confidence": 0.8},
        ], "domain": "finance"},
    ],
    "incident_response": [
        {"steps": [
            {"thought": "Payment service returning 503. First: is it one instance or all?", "action": "scope_impact", "confidence": 0.2},
            {"thought": "All 8 pods affected. Not a single instance issue. Something systemic.", "action": "narrow_scope", "confidence": 0.4},
            {"thought": "Checking dependencies. Database responds. Redis responds. External payment gateway... timeout!", "action": "trace_dependency", "confidence": 0.7},
            {"thought": "Gateway is down. Their status page says 'investigating'. We need a fallback.", "action": "identify_external_cause", "confidence": 0.9},
            {"thought": "Enabling fallback payment processor. Routing new transactions to backup. Existing in queue will retry.", "action": "mitigate", "confidence": 0.9},
            {"thought": "Backup processor live. Error rate dropping. 95% of payments processing again.", "action": "verify_mitigation", "confidence": 0.95},
            {"thought": "Postmortem: we need automatic failover, not manual. Adding circuit breaker to backlog.", "action": "learn_and_improve", "confidence": 0.99},
        ], "domain": "coding"},
        {"steps": [
            {"thought": "Login page returning blank white screen. No errors in console. What changed?", "action": "observe", "confidence": 0.1},
            {"thought": "Last deploy was 2 hours ago. But the issue started 10 min ago. Not deploy-related?", "action": "eliminate_hypothesis", "confidence": 0.3},
            {"thought": "Checking CDN. Assets returning 403. SSL cert expired on CDN edge! Auto-renewal failed.", "action": "find_cause", "confidence": 0.85},
            {"thought": "Manual cert renewal triggered. Propagating to edge nodes. ETA 5 min.", "action": "fix", "confidence": 0.9},
            {"thought": "Site back. Action item: cert auto-renewal monitoring with 14-day advance alert.", "action": "prevent_recurrence", "confidence": 0.99},
        ], "domain": "coding"},
    ],
    "architecture_decision": [
        {"steps": [
            {"thought": "We need real-time notifications. Options: polling, SSE, WebSockets, push notifications.", "action": "enumerate_options", "confidence": 0.3},
            {"thought": "Polling: simple but wasteful. SSE: one-way server→client. WebSocket: bidirectional. Push: mobile only.", "action": "evaluate_tradeoffs", "confidence": 0.5},
            {"thought": "Our use case: server sends updates, client rarely sends back. SSE fits perfectly. Simpler than WS.", "action": "match_to_requirements", "confidence": 0.7},
            {"thought": "SSE reconnects automatically, works through proxies, no special protocol. WebSocket is overkill here.", "action": "decide", "confidence": 0.85},
            {"thought": "Implementing SSE with EventSource. Fallback to polling for IE/old browsers. Redis pub/sub for scaling.", "action": "plan_implementation", "confidence": 0.9},
        ], "domain": "coding"},
    ],
    "security_investigation": [
        {"steps": [
            {"thought": "Alert: 500 failed login attempts on admin account in 10 minutes. Brute force attack.", "action": "detect", "confidence": 0.8},
            {"thought": "Source IPs: distributed across 50 countries. Botnet, not single attacker.", "action": "identify_pattern", "confidence": 0.85},
            {"thought": "Account not compromised (strong password + MFA). But we should block the IPs and add rate limit.", "action": "assess_impact", "confidence": 0.9},
            {"thought": "Implemented: rate limit 5 attempts/min per IP. Added CAPTCHA after 3 fails. Blocked /24 subnets.", "action": "mitigate", "confidence": 0.95},
            {"thought": "Long term: move to passwordless auth. FIDO2/WebAuthn eliminates brute force entirely.", "action": "strategic_improvement", "confidence": 0.99},
        ], "domain": "coding"},
    ],
    "performance_optimization": [
        {"steps": [
            {"thought": "Dashboard page takes 8 seconds to load. Users complaining. Where's the bottleneck?", "action": "identify_problem", "confidence": 0.2},
            {"thought": "Network tab: 3 API calls, each taking 2.5s. Waterfall, not parallel. That's 7.5s right there.", "action": "measure", "confidence": 0.6},
            {"thought": "These 3 calls are independent! Can run in parallel with Promise.all. Should drop to 2.5s total.", "action": "hypothesis", "confidence": 0.8},
            {"thought": "Implemented parallel fetch. Page now loads in 2.8s. But can we do better?", "action": "first_improvement", "confidence": 0.85},
            {"thought": "Adding cache headers. Second visit loads in 400ms. Good enough. Ship it.", "action": "optimize_further", "confidence": 0.95},
        ], "domain": "coding"},
    ],
}

# Self-correction examples (AI learns to say "I was wrong")
SELF_CORRECTIONS = [
    {"initial_thought": "This looks like a memory leak. Going to add garbage collection.",
     "correction": "Wait — actually the memory is growing because we're caching without TTL. Not a leak, it's unbounded cache. Adding TTL instead of forcing GC.",
     "lesson": "Don't jump to conclusions. Check if growth is intentional (cache) vs unintentional (leak)."},
    {"initial_thought": "The test is flaky. Let me add a retry.",
     "correction": "No — retrying hides the real bug. The test is revealing a race condition. I need to fix the race, not suppress the symptom.",
     "lesson": "Flaky tests are usually telling you something real. Fix the cause, not the symptom."},
    {"initial_thought": "Performance is slow because the algorithm is O(n²). Need to optimize.",
     "correction": "Profiled it. The O(n²) part takes 2ms. The actual bottleneck is a network call taking 800ms. Optimizing the wrong thing.",
     "lesson": "Always profile before optimizing. The intuitive bottleneck is often not the real one."},
    {"initial_thought": "BTC is dumping, I should sell to avoid more losses.",
     "correction": "This is panic talking. My thesis hasn't changed. The fundamentals are the same. This is just noise. Holding.",
     "lesson": "Distinguish between signal and noise. Don't let short-term price action override long-term thesis."},
    {"initial_thought": "The customer is wrong about this bug report.",
     "correction": "I tested their exact steps and reproduced it. They were right. My local env had different config. Customer is always worth investigating.",
     "lesson": "Don't dismiss user reports based on assumptions. Always reproduce in their exact environment."},
]

# Expert vs Novice contrast (same problem, different skill levels)
EXPERT_VS_NOVICE = [
    {"problem": "API endpoint returning slow responses",
     "novice_approach": "Added sleep(0.1) before the response to 'smooth things out'. Added a loading spinner on frontend. Called it fixed.",
     "expert_approach": "Profiled the endpoint. Found N+1 query. Added eager loading. Response time: 2.3s → 45ms. Added performance regression test.",
     "lesson": "Novice treats symptoms. Expert finds root cause. Novice adds complexity. Expert removes it."},
    {"problem": "Application crashes under load",
     "novice_approach": "Doubled the server size (2x CPU, 2x RAM). Costs went up 100%. Crashes at 2x the previous load.",
     "expert_approach": "Found connection pool exhaustion. Set max connections to match expected concurrency. Added circuit breaker. Added graceful degradation. Handles 10x load on same hardware.",
     "lesson": "Scaling vertically (bigger machines) is the novice move. Scaling horizontally + fixing bottlenecks is expert."},
    {"problem": "Need to add a new feature quickly",
     "novice_approach": "Copied existing similar code, modified it, no tests, pushed directly to main. Works but duplicated 200 lines.",
     "expert_approach": "Extracted shared logic into a reusable function. Added the new feature in 15 lines. Full test coverage. PR with clear description.",
     "lesson": "Speed now vs speed later. Novice is faster today, expert is faster for the next 100 changes."},
]


def generate_reasoning_record(category: str, domain: str, rng: random.Random) -> Dict:
    """Generate a reasoning chain record for training chain-of-thought AI."""
    # Pick relevant reasoning chain
    chains = REASONING_CHAINS.get("debugging" if domain == "coding" else "trading_decision",
                                   REASONING_CHAINS["debugging"])
    chain = rng.choice(chains)

    # Self-correction (20% of events)
    self_correction = None
    if rng.random() < 0.20:
        self_correction = rng.choice(SELF_CORRECTIONS)

    # Expert vs novice (10% of events)
    expert_novice = None
    if rng.random() < 0.10:
        expert_novice = rng.choice(EXPERT_VS_NOVICE)

    return {
        "reasoning_chain": {
            "steps": chain["steps"],
            "total_steps": len(chain["steps"]),
            "final_confidence": chain["steps"][-1]["confidence"],
            "reasoning_type": "deductive",
        },
        "self_correction": self_correction,
        "expert_vs_novice": expert_novice,
        "uncertainty_expressed": any(s["confidence"] < 0.5 for s in chain["steps"]),
        "confidence_calibration": [s["confidence"] for s in chain["steps"]],
    }
