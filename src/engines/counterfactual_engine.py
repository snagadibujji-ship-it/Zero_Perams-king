"""Counterfactual Engine — fork timelines at decision points.

For every significant decision in a record, generate:
1. What actually happened (factual)
2. What almost happened (near-miss alternative)
3. What would have happened if a different choice was made (counterfactual)

This trains AI on: planning, consequence prediction, strategy evaluation.
"""
import random
from typing import Dict, List, Tuple


# World-specific counterfactual templates
# Each template contains:
#   decision_point, factual_outcome, counterfactual_outcome,
#   near_miss, probability, consequence_magnitude, lesson

HEALTHCARE_TEMPLATES = [
    {
        "decision_point": "Prescribed Drug A for bacterial infection",
        "factual_outcome": "Patient received Drug A, recovered in 5 days with mild GI side effects",
        "counterfactual_outcome": "If Drug B chosen: 60% chance faster recovery (3 days), 15% chance adverse reaction requiring ICU",
        "near_miss": "Drug C (similar name on formulary) was almost prescribed — would have caused acute renal failure",
        "probability": 0.60,
        "consequence_magnitude": 7,
        "lesson": "Name-alike drugs require verification; faster recovery potential must be weighed against catastrophic tail risk"
    },
    {
        "decision_point": "Ordered CT scan before surgery",
        "factual_outcome": "CT revealed unsuspected aortic aneurysm, surgery approach modified, patient survived",
        "counterfactual_outcome": "If proceeded without CT: 40% chance intraoperative rupture, likely fatal hemorrhage",
        "near_miss": "Radiology was at capacity — scan nearly deferred to post-op",
        "probability": 0.40,
        "consequence_magnitude": 10,
        "lesson": "Pre-operative imaging catches silent killers; capacity constraints should not override clinical judgment"
    },
    {
        "decision_point": "Chose conservative management over immediate surgery",
        "factual_outcome": "Patient monitored for 48hrs, condition stabilized, discharged day 5",
        "counterfactual_outcome": "If immediate surgery: faster resolution but 8% complication rate, 2% mortality for this demographic",
        "near_miss": "Patient deteriorated at hour 36 — surgical team was being assembled when vitals improved",
        "probability": 0.08,
        "consequence_magnitude": 6,
        "lesson": "Conservative management trades speed for safety but requires vigilant monitoring and rapid escalation plans"
    },
    {
        "decision_point": "Administered tPA for suspected stroke within 3-hour window",
        "factual_outcome": "Thrombolysis successful, patient regained speech and motor function within 2 hours",
        "counterfactual_outcome": "If waited for MRI confirmation: would have exceeded treatment window, permanent left-side paralysis",
        "near_miss": "Lab results were delayed 20 minutes — nearly missed the 3-hour window entirely",
        "probability": 0.85,
        "consequence_magnitude": 9,
        "lesson": "Time-critical interventions require acting on clinical suspicion; perfection of diagnosis can be enemy of treatment"
    },
    {
        "decision_point": "Escalated sepsis protocol at early warning signs",
        "factual_outcome": "Broad-spectrum antibiotics started within 1 hour, patient stabilized, ICU stay 3 days",
        "counterfactual_outcome": "If waited for culture results (12hrs): 30% chance progression to septic shock, 15% mortality",
        "near_miss": "Nurse almost attributed fever to post-surgical inflammation — sepsis screening caught it",
        "probability": 0.30,
        "consequence_magnitude": 9,
        "lesson": "Early aggressive treatment of sepsis saves lives; waiting for perfect information costs lives in time-critical scenarios"
    },
    {
        "decision_point": "Transferred patient to tertiary center for specialist care",
        "factual_outcome": "Specialist performed rare procedure, full recovery in 2 weeks",
        "counterfactual_outcome": "If treated locally: general surgeon would have attempted procedure, 35% chance of incomplete repair requiring revision",
        "near_miss": "Transfer helicopter was grounded by weather — road ambulance dispatched with 40-min delay",
        "probability": 0.35,
        "consequence_magnitude": 6,
        "lesson": "Knowing your limits and referring appropriately produces better outcomes than attempting unfamiliar procedures"
    },
    {
        "decision_point": "Chose regional anesthesia over general for elderly patient",
        "factual_outcome": "Procedure completed under spinal block, patient alert post-op, discharged day 2",
        "counterfactual_outcome": "If general anesthesia: 20% chance post-operative delirium, average 5-day stay, increased fall risk",
        "near_miss": "Spinal placement failed on first attempt — anesthesiologist nearly converted to general",
        "probability": 0.20,
        "consequence_magnitude": 5,
        "lesson": "Regional anesthesia in elderly reduces cognitive complications; persistence with technique pays dividends"
    },
    {
        "decision_point": "Initiated palliative care discussion with terminal patient",
        "factual_outcome": "Patient chose comfort care, spent final 3 weeks at home with family, died peacefully",
        "counterfactual_outcome": "If continued aggressive treatment: average 4 additional weeks survival but in ICU, intubated, family unable to visit",
        "near_miss": "Oncologist almost recommended another chemo cycle before palliative referral was raised",
        "probability": 0.70,
        "consequence_magnitude": 8,
        "lesson": "Quality of remaining life often matters more than quantity; early palliative discussions enable patient autonomy"
    },
    {
        "decision_point": "Discharged patient with telemonitoring instead of extended stay",
        "factual_outcome": "Remote monitoring caught arrhythmia on day 3, patient readmitted for pacemaker, recovered fully",
        "counterfactual_outcome": "If kept inpatient: arrhythmia caught sooner but $15K additional cost, hospital-acquired infection risk 5%",
        "near_miss": "Patient almost declined telemonitoring device — would have had undetected arrhythmia at home",
        "probability": 0.05,
        "consequence_magnitude": 7,
        "lesson": "Technology-enabled early discharge balances cost and safety but requires patient engagement and reliable monitoring"
    },
    {
        "decision_point": "Ordered genetic testing before starting chemotherapy regimen",
        "factual_outcome": "Testing revealed DPYD deficiency, dose reduced 50%, patient tolerated treatment without toxicity",
        "counterfactual_outcome": "If standard dose given without testing: 25% chance severe fluoropyrimidine toxicity, potentially fatal mucositis",
        "near_miss": "Lab was backlogged — oncologist nearly started treatment pending results",
        "probability": 0.25,
        "consequence_magnitude": 9,
        "lesson": "Pharmacogenomic testing prevents predictable adverse reactions; treatment urgency rarely justifies skipping safety checks"
    },
]

FINANCE_TEMPLATES = [
    {
        "decision_point": "Held position through volatility spike",
        "factual_outcome": "Trader held position through 3-day volatility, endured -8% drawdown then gained 12% net",
        "counterfactual_outcome": "If stop-loss at -5% triggered: would have avoided the -8% drawdown BUT missed the 12% recovery, net -5%",
        "near_miss": "Fat finger check caught order 10x intended size — would have caused $4M unintended exposure",
        "probability": 0.55,
        "consequence_magnitude": 6,
        "lesson": "Conviction through volatility requires sizing discipline; stop-losses protect capital but can lock in losses during whipsaws"
    },
    {
        "decision_point": "Executed large block trade via dark pool",
        "factual_outcome": "5M shares filled at VWAP with 2bps slippage, no market impact detected",
        "counterfactual_outcome": "If executed on lit exchange: estimated 15bps market impact, $750K additional cost, front-running risk",
        "near_miss": "Dark pool match nearly failed — order was 30 seconds from routing to lit market",
        "probability": 0.70,
        "consequence_magnitude": 5,
        "lesson": "Venue selection for large orders significantly impacts execution quality; dark pools reduce information leakage"
    },
    {
        "decision_point": "Reduced portfolio leverage from 3x to 1.5x ahead of earnings season",
        "factual_outcome": "Earnings miss caused 6% sector drop; reduced leverage limited loss to 9% vs potential 18%",
        "counterfactual_outcome": "If maintained 3x leverage: 18% drawdown would have triggered margin call, forced liquidation at worst prices",
        "near_miss": "Risk committee nearly approved maintaining leverage — one dissenting vote changed the outcome",
        "probability": 0.40,
        "consequence_magnitude": 8,
        "lesson": "Leverage amplifies both gains and losses; reducing ahead of uncertainty events preserves optionality"
    },
    {
        "decision_point": "Hedged currency exposure on international acquisition",
        "factual_outcome": "6-month FX forward locked in rate, acquisition completed at budgeted cost",
        "counterfactual_outcome": "If unhedged: currency moved 8% adverse, would have added $12M to deal cost, possibly killed the deal",
        "near_miss": "Treasury team almost chose 3-month tenor — deal delayed beyond that window",
        "probability": 0.45,
        "consequence_magnitude": 7,
        "lesson": "Hedging converts uncertainty to known cost; tenor selection must account for realistic timeline slippage"
    },
    {
        "decision_point": "Rejected algorithmic trading signal as anomalous",
        "factual_outcome": "Signal was indeed a data feed error; manual override prevented $2M erroneous trade",
        "counterfactual_outcome": "If signal followed blindly: would have bought illiquid instrument at 15% premium, locked in immediate loss",
        "near_miss": "Auto-execution was 200ms from triggering before human override engaged",
        "probability": 0.85,
        "consequence_magnitude": 7,
        "lesson": "Human oversight of algorithmic systems catches data quality issues; speed must be balanced with sanity checks"
    },
    {
        "decision_point": "Allocated to emerging market bonds despite political risk",
        "factual_outcome": "12% yield captured over 18 months, no default event, portfolio outperformed benchmark by 200bps",
        "counterfactual_outcome": "If avoided EM allocation: missed 200bps outperformance, but also avoided the 3-week period of -15% mark-to-market during political crisis",
        "near_miss": "Sovereign credit downgrade rumor nearly triggered early exit at -8% — would have crystallized loss",
        "probability": 0.30,
        "consequence_magnitude": 5,
        "lesson": "Risk premiums compensate for real risks; the ability to hold through volatility IS the edge, but requires position sizing for survivability"
    },
    {
        "decision_point": "Implemented collar strategy on concentrated stock position",
        "factual_outcome": "Stock rose 20% — gains capped at 12% by call strike, but downside protected below -5%",
        "counterfactual_outcome": "If no collar: would have captured full 20% upside, but was exposed to potential -40% downside in sector rotation",
        "near_miss": "Client almost rejected collar cost — sector peer dropped 35% two months later",
        "probability": 0.25,
        "consequence_magnitude": 8,
        "lesson": "Protection has a cost; concentrated positions justify paying insurance premium even when it caps upside"
    },
    {
        "decision_point": "Delayed IPO by 3 months due to market conditions",
        "factual_outcome": "Launched into improved sentiment, priced at top of range, raised $500M at 25x revenue",
        "counterfactual_outcome": "If launched on original date: market was -12% that week from rate shock, likely priced at bottom of range or pulled entirely",
        "near_miss": "Board pressure nearly forced original timeline — CEO's insistence on delay proved correct",
        "probability": 0.65,
        "consequence_magnitude": 8,
        "lesson": "Market timing for capital events matters enormously; the cost of delay is usually less than the cost of poor execution"
    },
    {
        "decision_point": "Closed short position at small loss rather than holding",
        "factual_outcome": "Covered short at 3% loss; stock subsequently rose another 40% over next quarter",
        "counterfactual_outcome": "If held short: would have faced 40% loss on position, possible margin call, $6M additional loss",
        "near_miss": "Short squeeze began the day after covering — borrow cost had already risen 5x",
        "probability": 0.70,
        "consequence_magnitude": 8,
        "lesson": "Small losses are preferable to catastrophic ones; short positions have unlimited loss potential and require strict discipline"
    },
    {
        "decision_point": "Diversified counterparty risk across 5 prime brokers",
        "factual_outcome": "When PB-3 had operational issues, positions seamlessly continued via other four brokers",
        "counterfactual_outcome": "If single prime broker: would have been locked out of trading for 3 days during their outage, missed critical rebalancing window",
        "near_miss": "Concentration limit with PB-3 was nearly breached — would have required emergency margin posting",
        "probability": 0.20,
        "consequence_magnitude": 7,
        "lesson": "Operational diversification is as important as portfolio diversification; single points of failure create systemic risk"
    },
]

CODING_TEMPLATES = [
    {
        "decision_point": "Deployed hotfix Friday 5pm to resolve production incident",
        "factual_outcome": "Team deployed hotfix Friday 5pm, resolved incident, no weekend pages",
        "counterfactual_outcome": "If waited until Monday: 48 more hours of degraded service, ~$200K revenue impact, but lower risk of introducing new bugs",
        "near_miss": "Rollback was 30 seconds from executing when fix was confirmed — rollback would have caused 2hr data resync",
        "probability": 0.75,
        "consequence_magnitude": 6,
        "lesson": "Friday deploys carry weekend risk but active incidents have ongoing cost; decision depends on fix confidence and rollback safety"
    },
    {
        "decision_point": "Chose microservices over monolith for new platform",
        "factual_outcome": "Microservices deployed, team scaled to 8 squads independently, 4-month delivery",
        "counterfactual_outcome": "If monolith chosen: 2-month faster initial delivery, but coupling would have slowed team scaling, 12-month refactor needed later",
        "near_miss": "Architect nearly chose monolith-first approach — team growth plan was not yet confirmed when decision was made",
        "probability": 0.60,
        "consequence_magnitude": 7,
        "lesson": "Architecture choices are bets on organizational trajectory; premature microservices adds complexity, but monolith-to-micro migration is expensive"
    },
    {
        "decision_point": "Reverted merge commit instead of forward-fixing broken build",
        "factual_outcome": "Reverted within 5 minutes, main branch green, developer re-submitted fixed PR next day",
        "counterfactual_outcome": "If attempted forward-fix: estimated 2-4 hours of broken main, blocking 12 developers, cascading merge conflicts",
        "near_miss": "CI pipeline was 10 seconds from auto-deploying broken code to staging before revert landed",
        "probability": 0.80,
        "consequence_magnitude": 5,
        "lesson": "Revert-first culture unblocks teams fast; ego cost of revert is far less than productivity cost of broken main"
    },
    {
        "decision_point": "Added database index before feature launch",
        "factual_outcome": "Index reduced p99 query time from 2.3s to 45ms, launch handled 10x expected traffic",
        "counterfactual_outcome": "If launched without index: database CPU at 95% within 1 hour, cascading timeouts, full outage requiring emergency maintenance window",
        "near_miss": "Load test was almost skipped due to timeline pressure — it revealed the missing index",
        "probability": 0.90,
        "consequence_magnitude": 8,
        "lesson": "Performance testing before launch catches issues that are catastrophic under load but invisible in dev; the cost of a load test is trivial vs outage cost"
    },
    {
        "decision_point": "Implemented feature flag for gradual rollout",
        "factual_outcome": "Rolled to 5% of users, caught memory leak at low blast radius, fixed before wider release",
        "counterfactual_outcome": "If full rollout: memory leak would have degraded all users within 6 hours, requiring emergency rollback and hotfix",
        "near_miss": "Product manager pushed for 100% rollout to hit quarterly target — eng lead insisted on gradual",
        "probability": 0.15,
        "consequence_magnitude": 7,
        "lesson": "Gradual rollouts are insurance against unknown-unknowns; the delay cost is minimal compared to blast radius of full failures"
    },
    {
        "decision_point": "Migrated database with dual-write strategy",
        "factual_outcome": "Dual-write ran for 2 weeks, caught 3 data inconsistencies, cutover was seamless",
        "counterfactual_outcome": "If big-bang migration: those 3 inconsistencies would have caused silent data corruption for ~500 users, discovered weeks later",
        "near_miss": "Dual-write nearly abandoned on day 3 due to added latency — optimization fixed it on day 4",
        "probability": 0.30,
        "consequence_magnitude": 9,
        "lesson": "Dual-write migrations are slower but reveal edge cases that big-bang misses; data integrity is worth the operational overhead"
    },
    {
        "decision_point": "Chose to write integration tests over more unit tests",
        "factual_outcome": "Integration tests caught API contract break between services before production, prevented outage",
        "counterfactual_outcome": "If only unit tests: contract break would have passed all tests, failed in production with cryptic errors affecting 30% of requests",
        "near_miss": "Integration test suite nearly removed from CI pipeline due to flakiness — stabilization effort saved it",
        "probability": 0.40,
        "consequence_magnitude": 6,
        "lesson": "Integration tests catch category of bugs unit tests cannot; flaky tests need fixing, not removal"
    },
    {
        "decision_point": "Refactored authentication module before adding new auth provider",
        "factual_outcome": "Refactored auth abstraction layer, new provider integrated in 3 days cleanly",
        "counterfactual_outcome": "If bolted on without refactoring: new provider would work but auth module becomes unmaintainable, next provider takes 3 weeks with high bug risk",
        "near_miss": "Sprint pressure almost forced direct integration — tech debt review flagged the module as critical risk",
        "probability": 0.65,
        "consequence_magnitude": 5,
        "lesson": "Strategic refactoring before new features reduces long-term velocity cost; the best time to pay tech debt is before it compounds"
    },
    {
        "decision_point": "Set up automated dependency updates with security scanning",
        "factual_outcome": "Automated PR caught critical CVE in transitive dependency 4 hours after disclosure, patched same day",
        "counterfactual_outcome": "If manual dependency management: CVE likely unnoticed for 2-3 weeks, during which time exploit actively used in the wild",
        "near_miss": "Auto-update was almost disabled after a breaking change incident — policy was refined instead of removed",
        "probability": 0.25,
        "consequence_magnitude": 9,
        "lesson": "Automated dependency management catches security issues at machine speed; policy refinement beats disabling safety systems"
    },
    {
        "decision_point": "Invested sprint in observability before scaling event",
        "factual_outcome": "Distributed tracing identified bottleneck in 8 minutes during peak, hot-fixed with zero downtime",
        "counterfactual_outcome": "If no observability investment: same bottleneck would have taken 4+ hours to diagnose via log grep, causing extended degradation",
        "near_miss": "Observability sprint was nearly deprioritized for a feature — CTO overruled based on previous incident",
        "probability": 0.70,
        "consequence_magnitude": 7,
        "lesson": "Observability is a force multiplier for incident response; you cannot fix what you cannot see, and MTTR determines customer impact"
    },
]

ENERGY_TEMPLATES = [
    {
        "decision_point": "Grid operator shed 500MW load to prevent cascade failure",
        "factual_outcome": "Controlled load shed affected 200K customers for 45 minutes, grid stabilized, no equipment damage",
        "counterfactual_outcome": "If no load shed: cascade would have blacked out 3 more substations, 2M customers without power for 8-12 hours",
        "near_miss": "Automatic protection relay was 200ms from tripping the interconnector — would have islanded the entire region",
        "probability": 0.75,
        "consequence_magnitude": 9,
        "lesson": "Controlled sacrifice of part prevents catastrophic loss of whole; operators must act decisively with incomplete information"
    },
    {
        "decision_point": "Delayed turbine restart pending vibration analysis",
        "factual_outcome": "Analysis revealed bearing degradation, replaced during planned outage, no forced outage",
        "counterfactual_outcome": "If restarted immediately: 40% chance bearing failure within 72hrs, 6-month repair, $8M replacement cost",
        "near_miss": "Dispatch pressure nearly overrode maintenance hold — spot prices were $200/MWh during delay",
        "probability": 0.40,
        "consequence_magnitude": 8,
        "lesson": "Short-term revenue opportunity must be weighed against catastrophic equipment loss; bearing failures cascade to rotors"
    },
    {
        "decision_point": "Curtailed wind farm output due to grid congestion forecast",
        "factual_outcome": "Curtailed 200MW for 4 hours, lost $160K revenue, grid remained stable",
        "counterfactual_outcome": "If full output maintained: transmission line thermal limit exceeded, automatic trip, 30-minute blackout for downstream loads",
        "near_miss": "Forecast error nearly under-predicted congestion — real-time monitoring caught actual flow 95% of thermal limit",
        "probability": 0.60,
        "consequence_magnitude": 7,
        "lesson": "Proactive curtailment prevents reactive protection trips; forecast uncertainty requires conservative margins"
    },
    {
        "decision_point": "Invested in battery storage instead of peaking gas plant",
        "factual_outcome": "Battery responded in 50ms to frequency event, faster than gas plant could have started, grid frequency restored",
        "counterfactual_outcome": "If gas peaker chosen: 10-minute start time would have allowed frequency to drop below threshold, triggering automatic load shed",
        "near_miss": "Battery was at 12% SOC when event occurred — if 5 minutes later, insufficient energy for response",
        "probability": 0.35,
        "consequence_magnitude": 7,
        "lesson": "Response speed matters as much as capacity for grid stability; batteries excel at fast-response but energy-limited applications"
    },
    {
        "decision_point": "Switched to backup fuel supply during pipeline disruption",
        "factual_outcome": "Dual-fuel capability activated, plant continued operating on oil for 3 days until gas restored",
        "counterfactual_outcome": "If no dual-fuel capability: forced shutdown of 800MW plant, regional capacity shortfall, rolling blackouts",
        "near_miss": "Fuel oil tank level was at minimum — 6 more hours of delay would have forced shutdown anyway",
        "probability": 0.20,
        "consequence_magnitude": 9,
        "lesson": "Fuel diversity provides resilience against supply disruptions; backup systems only work if maintained and supplied"
    },
    {
        "decision_point": "Performed live-line maintenance instead of scheduled outage",
        "factual_outcome": "Transmission line repaired while energized, no customer impact, completed in 4 hours",
        "counterfactual_outcome": "If scheduled outage: 50K customers without power for 6 hours, $2M economic impact, industrial processes disrupted",
        "near_miss": "Weather window nearly closed — wind speed rose to safety limit during final hour of work",
        "probability": 0.05,
        "consequence_magnitude": 6,
        "lesson": "Live-line work eliminates customer impact but requires strict safety protocols; weather windows create hard constraints"
    },
    {
        "decision_point": "Preemptively isolated microgrid ahead of storm",
        "factual_outcome": "Microgrid operated independently for 18 hours during storm, critical facilities maintained power",
        "counterfactual_outcome": "If stayed connected: main grid fault would have propagated into microgrid, hospital and water treatment lost power",
        "near_miss": "Islanding controller had a firmware bug — manual override engaged with 15 minutes to spare before storm hit",
        "probability": 0.70,
        "consequence_magnitude": 9,
        "lesson": "Proactive islanding protects critical loads; automated systems need regular testing and manual override capability"
    },
    {
        "decision_point": "Upgraded transformer based on dissolved gas analysis",
        "factual_outcome": "Replaced transformer during planned outage, inspection confirmed insulation degradation at 80% failure threshold",
        "counterfactual_outcome": "If deferred replacement: 50% chance of explosive failure within 6 months, fire risk, $20M damage, 3-week outage",
        "near_miss": "Budget approval was denied twice before DGA trend convinced management — failure was months away",
        "probability": 0.50,
        "consequence_magnitude": 10,
        "lesson": "Predictive maintenance analytics justify replacement investment; catastrophic transformer failures are among the most expensive grid events"
    },
    {
        "decision_point": "Reduced nuclear plant output for grid frequency support",
        "factual_outcome": "Plant reduced to 80% power, provided 200MW of downward frequency response, grid balanced",
        "counterfactual_outcome": "If refused to reduce: excess generation would have driven frequency above limits, triggering widespread renewable curtailment",
        "near_miss": "Reactor control rod insertion rate was near technical minimum — 5% more reduction request would have required full shutdown",
        "probability": 0.30,
        "consequence_magnitude": 6,
        "lesson": "Baseload flexibility has limits but provides critical grid services; understanding plant operating envelope prevents forced shutdowns"
    },
    {
        "decision_point": "Deferred solar farm commissioning for grid reinforcement",
        "factual_outcome": "3-month delay allowed transformer upgrade, solar farm connected at full capacity with stable voltage",
        "counterfactual_outcome": "If connected without reinforcement: voltage rise would have triggered inverter trips daily, only 60% output achievable, revenue 40% below plan",
        "near_miss": "Developer pressure nearly forced energization — connection agreement clause saved the situation",
        "probability": 0.80,
        "consequence_magnitude": 5,
        "lesson": "Grid connection readiness determines actual vs nameplate capacity; premature connection creates persistent operational issues"
    },
]

CONSTRUCTION_TEMPLATES = [
    {
        "decision_point": "Delayed concrete pour due to rain forecast",
        "factual_outcome": "Pour delayed 2 days, executed in dry conditions, surface finish met specification",
        "counterfactual_outcome": "If poured anyway: 30% chance rain ruins surface, $50K rework, 2-week delay, potential structural concerns",
        "near_miss": "Forecast changed to clear 4 hours before pour window — crew was already demobilized",
        "probability": 0.30,
        "consequence_magnitude": 6,
        "lesson": "Weather-dependent operations require conservative scheduling; rework cost far exceeds delay cost"
    },
    {
        "decision_point": "Ordered additional soil testing before foundation work",
        "factual_outcome": "Testing revealed clay lens at 8m depth, foundation design modified, building settled uniformly",
        "counterfactual_outcome": "If proceeded with original design: differential settlement of 40mm over 5 years, cracking, $2M remediation",
        "near_miss": "Project manager nearly signed off on original geotechnical report — junior engineer flagged inconsistency in bore logs",
        "probability": 0.45,
        "consequence_magnitude": 8,
        "lesson": "Subsurface conditions are the highest-uncertainty element in construction; additional investigation is cheap insurance against foundation failures"
    },
    {
        "decision_point": "Installed temporary works for crane lift in high wind zone",
        "factual_outcome": "Wind bracing held during unexpected 60km/h gust, crane completed lift safely next day",
        "counterfactual_outcome": "If temporary works skipped: crane would have been stood down for 3 days, $45K idle cost, but no safety risk",
        "near_miss": "Gust exceeded temporary works design capacity by 10% — held due to conservative material factors",
        "probability": 0.15,
        "consequence_magnitude": 9,
        "lesson": "Temporary works seem expensive until they prevent catastrophe; design margins exist for exactly these moments"
    },
    {
        "decision_point": "Chose prefabrication over in-situ construction for bathroom pods",
        "factual_outcome": "120 bathroom pods installed in 6 weeks vs estimated 16 weeks in-situ, project ahead of schedule",
        "counterfactual_outcome": "If in-situ: sequential trade access creates 10 weeks of float erosion, 3 trades clashing, quality defects from rushed finishing",
        "near_miss": "Prefab factory had logistics issue — 20 pods arrived 1 week late, nearly causing critical path delay",
        "probability": 0.70,
        "consequence_magnitude": 5,
        "lesson": "Off-site manufacturing reduces site variability but creates supply chain dependency; logistics planning is critical for prefab strategies"
    },
    {
        "decision_point": "Stopped excavation when unexpected utilities found",
        "factual_outcome": "Work stopped 4 hours for emergency utility survey, unmarked gas line identified and protected",
        "counterfactual_outcome": "If continued excavating: gas line strike probable within next 2m of dig, evacuation required, potential explosion",
        "near_miss": "Excavator bucket was 300mm from the gas line when operator noticed discolored soil",
        "probability": 0.80,
        "consequence_magnitude": 10,
        "lesson": "Unknown utilities are the most dangerous construction hazard; always stop and verify when unexpected conditions arise"
    },
    {
        "decision_point": "Accelerated schedule with overtime to meet contractual milestone",
        "factual_outcome": "Milestone met, $500K liquidated damages avoided, workers rotated to prevent fatigue",
        "counterfactual_outcome": "If maintained normal pace: milestone missed by 8 days, $500K penalty, client relationship damaged",
        "near_miss": "Two workers reported fatigue incidents during acceleration — near-miss triggered safety stand-down that almost caused the very delay it was preventing",
        "probability": 0.60,
        "consequence_magnitude": 6,
        "lesson": "Schedule acceleration has diminishing returns and safety costs; fatigue management is critical during overtime periods"
    },
    {
        "decision_point": "Rejected delivered concrete batch based on slump test",
        "factual_outcome": "Batch returned to plant, compliant batch delivered 3 hours later, structural integrity maintained",
        "counterfactual_outcome": "If accepted non-compliant batch: 20% chance of insufficient strength at 28 days, coring and possible demolition of element",
        "near_miss": "Supervisor initially waved batch through — QA inspector arrived and caught slump at 180mm vs 120mm specified",
        "probability": 0.20,
        "consequence_magnitude": 8,
        "lesson": "Quality control at point of placement prevents structural defects; the cost of rejection is hours, the cost of failure is months"
    },
    {
        "decision_point": "Hired specialist subcontractor for complex facade system",
        "factual_outcome": "Specialist completed facade in 12 weeks to spec, zero defects at practical completion",
        "counterfactual_outcome": "If general trade attempted: likely 8-week delay, 15% rework rate, warranty disputes, water ingress within 2 years",
        "near_miss": "Specialist subcontractor nearly went into administration mid-project — backup contractor identified but would have caused 4-week delay",
        "probability": 0.15,
        "consequence_magnitude": 7,
        "lesson": "Specialist work requires specialist contractors; apparent savings from generalists often become expensive defects"
    },
    {
        "decision_point": "Implemented BIM clash detection before MEP installation",
        "factual_outcome": "47 clashes resolved digitally, MEP installation proceeded without field rework",
        "counterfactual_outcome": "If no clash detection: average of 3 field clashes per floor, $8K rework each, 47 clashes = $376K additional cost and 6-week delay",
        "near_miss": "BIM model was nearly outdated — structural revision hadn't been incorporated, would have introduced 12 false negatives",
        "probability": 0.85,
        "consequence_magnitude": 6,
        "lesson": "Digital coordination eliminates physical rework; BIM models must be current or they provide false confidence"
    },
    {
        "decision_point": "Dewatered excavation before commencing piling",
        "factual_outcome": "Water table lowered 3m, piles installed in dry conditions, design bearing capacity achieved",
        "counterfactual_outcome": "If piled in wet conditions: pile integrity compromised by water infiltration, 30% chance of necking defects, integrity testing and replacement",
        "near_miss": "Dewatering pump failed overnight — water rose 1.5m before backup pump activated, 2 hours from flooding pile bores",
        "probability": 0.30,
        "consequence_magnitude": 8,
        "lesson": "Groundwater management is foundational to foundation work; redundant dewatering systems prevent costly pile defects"
    },
]

DEFENSE_TEMPLATES = [
    {
        "decision_point": "Commander held fire on unidentified vehicle approaching checkpoint",
        "factual_outcome": "Vehicle identified as civilian family, passed through checkpoint safely, zero casualties",
        "counterfactual_outcome": "If engaged: civilian casualties including children, international incident, unit investigated, mission compromised",
        "near_miss": "Gunner had target acquired and was awaiting final clearance — PID confirmed civilian 3 seconds before engagement threshold",
        "probability": 0.85,
        "consequence_magnitude": 10,
        "lesson": "Positive identification before engagement prevents irreversible civilian harm; seconds of patience prevent years of consequence"
    },
    {
        "decision_point": "Diverted patrol route based on SIGINT indicator",
        "factual_outcome": "Patrol avoided ambush site, IED found on original route 2 hours later by EOD",
        "counterfactual_outcome": "If followed original route: IED positioned at channeling point, estimated 2-4 casualties, vehicle destroyed",
        "near_miss": "SIGINT was initially assessed as low-confidence — analyst upgraded assessment 20 minutes before patrol departure",
        "probability": 0.70,
        "consequence_magnitude": 10,
        "lesson": "Intelligence-driven route changes save lives; even low-confidence indicators warrant risk mitigation when cost of being wrong is catastrophic"
    },
    {
        "decision_point": "Delayed air strike pending civilian structure clearance",
        "factual_outcome": "24-hour delay allowed civilians to evacuate, strike executed on confirmed empty structure, target eliminated",
        "counterfactual_outcome": "If struck immediately: 8-12 civilian casualties, propaganda victory for adversary, coalition support eroded",
        "near_miss": "Target nearly relocated during delay — ISR maintained track with 10-minute gap in coverage",
        "probability": 0.30,
        "consequence_magnitude": 9,
        "lesson": "Tactical patience preserves strategic advantage; civilian casualties create more enemies than any single strike eliminates"
    },
    {
        "decision_point": "Deployed electronic countermeasures during convoy movement",
        "factual_outcome": "ECM jammed radio-controlled IED trigger, device failed to detonate, convoy passed safely",
        "counterfactual_outcome": "If ECM not deployed: IED would have detonated under third vehicle, estimated 3 KIA, mission-critical equipment destroyed",
        "near_miss": "ECM system had intermittent fault — technician fixed it 30 minutes before convoy departure",
        "probability": 0.60,
        "consequence_magnitude": 10,
        "lesson": "Electronic protection requires 100% availability on every movement; equipment readiness is a life-or-death maintenance priority"
    },
    {
        "decision_point": "Requested artillery support instead of direct assault on fortified position",
        "factual_outcome": "Precision artillery neutralized position, assault force advanced without contact, zero friendly casualties",
        "counterfactual_outcome": "If direct assault: estimated 30% casualty rate in breach, 4-6 WIA, position may still not be cleared",
        "near_miss": "Artillery was initially unavailable due to competing priority — freed up with 15 minutes of fire mission window remaining",
        "probability": 0.30,
        "consequence_magnitude": 9,
        "lesson": "Combined arms reduces friendly casualties; infantry assault on prepared positions without supporting fires is a last resort"
    },
    {
        "decision_point": "Aborted helicopter insertion due to unexpected ground fire",
        "factual_outcome": "Mission aborted, re-planned with suppression package, executed 6 hours later without incident",
        "counterfactual_outcome": "If continued insertion: aircraft vulnerable during flare/landing, 25% chance of shootdown, 20+ personnel at risk",
        "near_miss": "Pilot was 500m from landing zone when tracers appeared — 8 seconds from committed approach",
        "probability": 0.25,
        "consequence_magnitude": 10,
        "lesson": "Aborting and re-planning is always preferable to flying into a prepared ambush; surprise lost means plan must change"
    },
    {
        "decision_point": "Established observation post rather than immediate raid",
        "factual_outcome": "48-hour surveillance revealed full network structure, subsequent raid captured 12 targets vs expected 3",
        "counterfactual_outcome": "If immediate raid: would have captured 2-3 low-level operators, network leadership alerted and scattered",
        "near_miss": "OP was nearly compromised by civilian shepherd — counter-surveillance plan preserved the position",
        "probability": 0.80,
        "consequence_magnitude": 7,
        "lesson": "Patience in intelligence gathering multiplies operational effectiveness; rushing to action captures bodies, patience captures networks"
    },
    {
        "decision_point": "Withdrew from forward position before predicted mortar attack",
        "factual_outcome": "Position vacated 20 minutes before 12-round mortar barrage impacted the area, zero casualties",
        "counterfactual_outcome": "If maintained position: barrage would have struck occupied fighting positions, estimated 3-5 casualties",
        "near_miss": "Withdrawal order was nearly delayed by ongoing resupply — last vehicle departed 4 minutes before first impact",
        "probability": 0.75,
        "consequence_magnitude": 9,
        "lesson": "Predictable positions invite indirect fire; pattern disruption and timely displacement preserve combat power"
    },
    {
        "decision_point": "Chose negotiation over kinetic response to hostage situation",
        "factual_outcome": "12-hour negotiation resulted in hostage release, all 4 hostages unharmed, captor surrendered",
        "counterfactual_outcome": "If immediate assault: 70% chance of success but 30% chance of hostage casualties during breach",
        "near_miss": "Captor deadline passed twice — negotiator maintained rapport through 2 crisis points where assault was moments from launch",
        "probability": 0.30,
        "consequence_magnitude": 10,
        "lesson": "Negotiation preserves all lives when time permits; kinetic options should be ready but employed as last resort"
    },
    {
        "decision_point": "Implemented cyber deception to protect command network",
        "factual_outcome": "Adversary penetrated honeypot network, revealed TTPs and targeting priorities, real network untouched",
        "counterfactual_outcome": "If no deception: adversary would have accessed operational plans, compromised upcoming operation, lives at risk",
        "near_miss": "Deception network nearly mapped to real assets by configuration error — red team caught it during exercise",
        "probability": 0.40,
        "consequence_magnitude": 9,
        "lesson": "Cyber deception provides intelligence while protecting real systems; the cost of deception infrastructure is trivial vs compromise of operations"
    },
]

TRANSPORT_TEMPLATES = [
    {
        "decision_point": "Rerouted fleet around predicted congestion zone",
        "factual_outcome": "Fleet took 12% longer route but arrived on-time; congestion zone had 90-minute delays",
        "counterfactual_outcome": "If direct route taken: 90-minute delay per vehicle, 23 late deliveries, $18K penalty clauses triggered",
        "near_miss": "GPS routing system briefly recommended direct route — dispatcher overrode based on traffic camera feeds",
        "probability": 0.80,
        "consequence_magnitude": 5,
        "lesson": "Proactive rerouting based on predictive data prevents cascading delays; human oversight of routing algorithms adds value in edge cases"
    },
    {
        "decision_point": "Grounded aircraft for unscheduled maintenance check",
        "factual_outcome": "Hydraulic leak found and repaired, aircraft returned to service in 8 hours, passengers rebooked",
        "counterfactual_outcome": "If dispatched: hydraulic failure in flight, emergency landing at divert airport, 180 passengers stranded 2 days",
        "near_miss": "Captain's walk-around almost missed the fluid weep — caught in specific lighting angle",
        "probability": 0.35,
        "consequence_magnitude": 9,
        "lesson": "Unscheduled maintenance decisions prioritize safety over schedule; the cost of grounding is always less than the cost of in-flight failure"
    },
    {
        "decision_point": "Reduced vessel speed to avoid collision with fishing fleet",
        "factual_outcome": "Container ship slowed to 8 knots through fishing area, arrived 4 hours late, no incidents",
        "counterfactual_outcome": "If maintained 20 knots: 15% chance of collision with fishing vessel, potential loss of life, $50M liability, port detention",
        "near_miss": "AIS showed clear path but radar detected 3 non-transmitting wooden vessels in the lane",
        "probability": 0.15,
        "consequence_magnitude": 10,
        "lesson": "Maritime speed reduction in congested waters prevents irreversible harm; schedule pressure never justifies collision risk"
    },
    {
        "decision_point": "Implemented dynamic pricing during peak demand period",
        "factual_outcome": "Surge pricing spread demand over 45-minute window, all passengers served, average wait 12 minutes",
        "counterfactual_outcome": "If flat pricing: demand spike would have exhausted all available vehicles, 35% of passengers waiting 40+ minutes, negative reviews surge",
        "near_miss": "Pricing algorithm nearly over-corrected — 4.5x surge was capped at 2.8x by newly-implemented ceiling",
        "probability": 0.65,
        "consequence_magnitude": 4,
        "lesson": "Dynamic pricing balances supply and demand but requires caps to prevent exploitation; transparency in pricing builds trust"
    },
    {
        "decision_point": "Cancelled train service due to infrastructure damage report",
        "factual_outcome": "Service cancelled for 6 hours, bridge inspection found cracked bearing, repaired before structural failure",
        "counterfactual_outcome": "If continued service: bridge bearing failure under load would have caused derailment, potential fatalities",
        "near_miss": "Report was initially classified as low-priority — duty manager escalated based on bridge age",
        "probability": 0.20,
        "consequence_magnitude": 10,
        "lesson": "Infrastructure reports deserve investigation regardless of initial priority; the consequence of bridge failure is catastrophic and irreversible"
    },
    {
        "decision_point": "Switched to manual traffic signal control during system outage",
        "factual_outcome": "Traffic officers managed 12 intersections for 3 hours, throughput at 70% of normal, no accidents",
        "counterfactual_outcome": "If signals left in flash mode: estimated 5-8 accidents at major intersections, 2-hour gridlock, emergency vehicle access blocked",
        "near_miss": "Only 8 officers available for 12 intersections — 4 junctions ran on timers that nearly desynchronized",
        "probability": 0.45,
        "consequence_magnitude": 7,
        "lesson": "Manual fallback for automated systems requires trained personnel and pre-planned deployment; graceful degradation beats complete failure"
    },
    {
        "decision_point": "Diverted long-haul truck driver to rest stop after hours-of-service alert",
        "factual_outcome": "Driver rested 10 hours, completed delivery next morning safely, 8-hour delay to customer",
        "counterfactual_outcome": "If driver continued: fatigue-related accident probability rises to 8% per hour beyond limit, potential multi-vehicle incident on highway",
        "near_miss": "ELD system was showing incorrect hours due to timezone glitch — dispatcher manually verified actual driving time",
        "probability": 0.08,
        "consequence_magnitude": 10,
        "lesson": "Hours-of-service regulations exist because fatigue is invisible to the fatigued; delivery deadlines never justify exhausted drivers"
    },
    {
        "decision_point": "Invested in predictive maintenance for rail rolling stock",
        "factual_outcome": "Wheel bearing replacement triggered by vibration trend, completed during scheduled maintenance window",
        "counterfactual_outcome": "If run-to-failure: bearing seizure at speed, potential derailment or at minimum emergency stop stranding 500 passengers",
        "near_miss": "Sensor data was intermittent for 2 weeks — maintenance team extrapolated trend from partial data correctly",
        "probability": 0.25,
        "consequence_magnitude": 9,
        "lesson": "Predictive maintenance transforms catastrophic failures into planned work items; sensor reliability is critical to the strategy"
    },
    {
        "decision_point": "Closed airport runway for FOD inspection after bird strike report",
        "factual_outcome": "Runway closed 25 minutes, 6 flights held, inspection found bird remains and cleared debris",
        "counterfactual_outcome": "If runway kept open: next departing aircraft could have ingested FOD, engine damage, possible rejected takeoff at high speed",
        "near_miss": "Aircraft on final approach was 2 minutes from landing when closure was enacted — executed go-around safely",
        "probability": 0.10,
        "consequence_magnitude": 9,
        "lesson": "FOD on runways is a known engine killer; short closures prevent expensive engine replacements and potential accidents"
    },
    {
        "decision_point": "Implemented geofencing for autonomous vehicle test zone",
        "factual_outcome": "AV hit edge of geofence during sensor confusion, safely halted rather than entering pedestrian zone",
        "counterfactual_outcome": "If no geofence: vehicle would have entered pedestrian-heavy market area during sensor degradation, potential pedestrian collision",
        "near_miss": "Geofence boundary was set 50m too narrow in original design — expanded after simulation showed stopping distance requirement",
        "probability": 0.05,
        "consequence_magnitude": 10,
        "lesson": "Hard safety boundaries for autonomous systems catch software failures; defense-in-depth means not trusting any single system for safety"
    },
]

EDUCATION_TEMPLATES = [
    {
        "decision_point": "Switched from lecture-based to project-based learning mid-semester",
        "factual_outcome": "Student engagement rose 40%, final project quality exceeded expectations, 85% completion rate",
        "counterfactual_outcome": "If continued lectures: engagement would have dropped further, estimated 60% completion, 30% D/F grades",
        "near_miss": "Department head nearly vetoed the change citing curriculum standards — pilot exemption granted with 1 vote margin",
        "probability": 0.60,
        "consequence_magnitude": 5,
        "lesson": "Pedagogical agility responds to student needs; rigid adherence to failing methods guarantees poor outcomes"
    },
    {
        "decision_point": "Implemented early intervention for at-risk student identified by analytics",
        "factual_outcome": "Tutoring and mentorship started week 3, student improved from failing to B grade, graduated on time",
        "counterfactual_outcome": "If no intervention: 70% probability of course failure, delayed graduation by 1 semester, $15K additional cost to student",
        "near_miss": "Student almost fell below the analytics threshold — one missed assignment triggered the alert",
        "probability": 0.70,
        "consequence_magnitude": 6,
        "lesson": "Early detection enables early intervention; waiting for students to self-identify struggles misses those who don't ask for help"
    },
    {
        "decision_point": "Adopted open educational resources instead of traditional textbooks",
        "factual_outcome": "Students saved $850 per course average, access from day 1, no piracy issues, same learning outcomes",
        "counterfactual_outcome": "If traditional textbooks: 25% of students delay purchase, fall behind in weeks 1-3, lower performance in first assessment",
        "near_miss": "OER materials had licensing issue discovered 1 week before semester — resolved with author directly",
        "probability": 0.25,
        "consequence_magnitude": 4,
        "lesson": "Cost barriers to learning materials disproportionately affect disadvantaged students; OER removes artificial obstacles to access"
    },
    {
        "decision_point": "Restructured assessment to continuous portfolio instead of final exam",
        "factual_outcome": "Students demonstrated deeper learning, anxiety reduced, grade distribution improved, academic integrity violations dropped 80%",
        "counterfactual_outcome": "If final exam only: surface-level memorization rewarded, 40% of students cram-and-forget, cheating attempts increase",
        "near_miss": "University assessment policy nearly mandated minimum 40% final exam weight — policy revision passed same semester",
        "probability": 0.40,
        "consequence_magnitude": 5,
        "lesson": "Assessment design drives learning behavior; continuous assessment encourages sustained engagement over strategic cramming"
    },
    {
        "decision_point": "Provided accessibility accommodations proactively rather than on request",
        "factual_outcome": "Universal design benefited all students, 3 undisclosed disabilities supported without stigma, satisfaction scores up 20%",
        "counterfactual_outcome": "If accommodation-on-request only: students with undisclosed disabilities struggle silently, 15% higher attrition in affected group",
        "near_miss": "Budget for universal design was nearly cut — retention data from previous cohort justified the investment",
        "probability": 0.15,
        "consequence_magnitude": 6,
        "lesson": "Proactive accessibility helps everyone and removes barriers for those who won't self-advocate; universal design is more efficient than individual accommodations"
    },
    {
        "decision_point": "Introduced peer code review as 30% of software engineering grade",
        "factual_outcome": "Students developed professional review skills, code quality improved 50%, industry feedback on graduates was excellent",
        "counterfactual_outcome": "If individual-only assessment: students never practice collaboration, first job review experience is overwhelming, quality remains inconsistent",
        "near_miss": "Two students had interpersonal conflict during reviews — nearly escalated to formal complaint before mediation resolved it",
        "probability": 0.50,
        "consequence_magnitude": 4,
        "lesson": "Professional skills require practice in safe environments; peer assessment builds capabilities that individual work cannot develop"
    },
    {
        "decision_point": "Cancelled class and provided async materials during campus emergency",
        "factual_outcome": "Students completed async module safely from home, no learning time lost, wellbeing prioritized",
        "counterfactual_outcome": "If held class anyway: 50% attendance from worried students, poor engagement, potential safety risk for commuters",
        "near_miss": "Emergency alert system delayed by 20 minutes — some students were already commuting when cancellation sent",
        "probability": 0.50,
        "consequence_magnitude": 7,
        "lesson": "Student safety always supersedes curriculum delivery; async fallbacks should be prepared for disruption scenarios"
    },
    {
        "decision_point": "Partnered with industry for capstone project sponsorship",
        "factual_outcome": "Students worked on real problems, 4 of 20 received job offers from sponsors, portfolio quality dramatically higher",
        "counterfactual_outcome": "If academic-only capstone: lower motivation, synthetic problems, weaker portfolios, no direct employment pipeline",
        "near_miss": "Industry partner nearly pulled out due to IP concerns — MOU negotiation saved the partnership 2 weeks before start",
        "probability": 0.60,
        "consequence_magnitude": 5,
        "lesson": "Industry partnerships create authentic learning and employment pathways; IP and scope agreements must be established early"
    },
    {
        "decision_point": "Implemented mastery-based progression instead of time-based semester",
        "factual_outcome": "Fast learners completed 30% ahead of schedule, struggling students got additional time, pass rate improved from 72% to 91%",
        "counterfactual_outcome": "If time-based only: fast students bored and disengaged, slow students failed without reaching mastery, bimodal grade distribution",
        "near_miss": "Registrar system couldn't handle variable completion dates — manual workaround needed for first cohort",
        "probability": 0.72,
        "consequence_magnitude": 6,
        "lesson": "Learning speed varies; flexible progression accommodates human variability while maintaining standards"
    },
    {
        "decision_point": "Trained faculty in trauma-informed teaching practices",
        "factual_outcome": "Disclosure-related crises handled appropriately, 2 students connected to counseling, retention improved in at-risk group",
        "counterfactual_outcome": "If no training: faculty inadvertently retraumatize through triggering content without warning, student disengages or drops out",
        "near_miss": "One faculty member's assignment prompt nearly required trauma disclosure — caught and redesigned during training workshop",
        "probability": 0.20,
        "consequence_magnitude": 7,
        "lesson": "Educators encounter student trauma regardless of subject; training prevents inadvertent harm and enables appropriate support"
    },
]

ECOMMERCE_TEMPLATES = [
    {
        "decision_point": "Launched flash sale with rate limiting to prevent bot purchases",
        "factual_outcome": "Sale ran smoothly, 95% of inventory went to real customers, completion in 4 hours",
        "counterfactual_outcome": "If no rate limiting: bots would have purchased 70% of inventory in 30 seconds, resold at 3x markup, customer fury, brand damage",
        "near_miss": "Bot network found bypass via API endpoint — WAF rule caught it 2 minutes after sale started",
        "probability": 0.70,
        "consequence_magnitude": 6,
        "lesson": "Fairness controls in high-demand events protect brand reputation; bots exploit any unprotected endpoint"
    },
    {
        "decision_point": "A/B tested new checkout flow before full rollout",
        "factual_outcome": "Test revealed 12% cart abandonment increase in variant B, reverted to original, saved $2M annual revenue",
        "counterfactual_outcome": "If rolled out without testing: 12% cart abandonment increase for all users, $2M revenue loss before detection",
        "near_miss": "Test was almost declared inconclusive at day 3 — statistician insisted on running to significance at day 7",
        "probability": 0.85,
        "consequence_magnitude": 7,
        "lesson": "A/B testing prevents costly mistakes; statistical rigor prevents premature decisions in either direction"
    },
    {
        "decision_point": "Implemented inventory buffer for viral product prediction",
        "factual_outcome": "Product went viral on social media, 3x normal demand fulfilled from buffer stock, zero stockouts",
        "counterfactual_outcome": "If standard inventory levels: stockout within 2 hours of viral moment, lost $500K in sales, competitor captured demand",
        "near_miss": "Buffer was nearly released to make warehouse space — social team's alert about influencer post saved it",
        "probability": 0.30,
        "consequence_magnitude": 6,
        "lesson": "Demand forecasting must account for viral events; buffer stock for high-potential items is cheap insurance against missed revenue"
    },
    {
        "decision_point": "Blocked suspicious transaction flagged by fraud system",
        "factual_outcome": "Transaction blocked, confirmed fraudulent, customer's stolen card protected, $4,200 fraud prevented",
        "counterfactual_outcome": "If approved: chargeback in 30 days, merchandise lost, $4,200 write-off, fraud rate impacts processor relationship",
        "near_miss": "Fraud score was 0.2 points above threshold — if slightly different model version, would have been approved",
        "probability": 0.90,
        "consequence_magnitude": 5,
        "lesson": "Fraud prevention thresholds trade false positives for loss prevention; calibration requires continuous monitoring of both sides"
    },
    {
        "decision_point": "Offered free shipping threshold instead of flat-rate shipping",
        "factual_outcome": "Average order value increased 23% as customers added items to reach threshold, shipping cost absorbed by margin",
        "counterfactual_outcome": "If flat-rate shipping: no AOV increase, shipping cost directly reduces margin, price-sensitive customers abandon more carts",
        "near_miss": "Threshold was initially set $10 too high — first week showed abandonment spike, reduced threshold saved the strategy",
        "probability": 0.65,
        "consequence_magnitude": 4,
        "lesson": "Free shipping thresholds leverage loss aversion to increase basket size; threshold calibration is critical to avoid backfire"
    },
    {
        "decision_point": "Personalized homepage based on browsing history vs generic bestsellers",
        "factual_outcome": "Click-through rate up 34%, conversion up 18%, customer satisfaction scores improved",
        "counterfactual_outcome": "If generic homepage for all: majority of visitors see irrelevant products, bounce rate 15% higher, revenue per visit lower",
        "near_miss": "Personalization engine served wrong recommendations to 5% of users due to cookie mismatch — caught within 1 hour",
        "probability": 0.75,
        "consequence_magnitude": 4,
        "lesson": "Personalization drives engagement when accurate; incorrect personalization is worse than generic content"
    },
    {
        "decision_point": "Sent cart abandonment email at 2-hour mark instead of 24-hour",
        "factual_outcome": "Recovery rate 15% at 2-hour window vs historical 8% at 24-hour, additional $300K monthly revenue",
        "counterfactual_outcome": "If 24-hour delay: customer has already purchased from competitor or lost purchase intent, recovery rate drops to 8%",
        "near_miss": "Email system had delivery delay that pushed some emails to 4-hour mark — still outperformed 24-hour by 40%",
        "probability": 0.55,
        "consequence_magnitude": 4,
        "lesson": "Timing in recovery communications matters enormously; purchase intent decays rapidly after abandonment"
    },
    {
        "decision_point": "Migrated to headless commerce architecture for mobile experience",
        "factual_outcome": "Mobile conversion rate improved 28%, page load time dropped from 4.2s to 1.1s, mobile revenue share grew from 35% to 52%",
        "counterfactual_outcome": "If stayed on monolithic platform: mobile experience continues degrading, losing 2% conversion per quarter as expectations rise",
        "near_miss": "Migration caused 4-hour checkout outage during cutover — happened at 3am but nearly scheduled for peak hours",
        "probability": 0.80,
        "consequence_magnitude": 6,
        "lesson": "Platform architecture directly impacts user experience metrics; technical debt in commerce platforms costs measurable revenue daily"
    },
    {
        "decision_point": "Implemented dynamic pricing during competitor stockout",
        "factual_outcome": "Raised prices 15% during competitor outage, maintained fair perception, captured $200K incremental margin",
        "counterfactual_outcome": "If raised 40%: short-term margin captured but customers felt exploited, social media backlash, long-term brand damage",
        "near_miss": "Pricing algorithm suggested 45% increase — manual cap prevented reputation damage",
        "probability": 0.40,
        "consequence_magnitude": 6,
        "lesson": "Dynamic pricing must be bounded by fairness perception; short-term extraction destroys long-term customer relationships"
    },
    {
        "decision_point": "Invested in returns experience with prepaid labels and instant refunds",
        "factual_outcome": "Return rate unchanged at 12%, but repeat purchase rate up 25%, lifetime value increased $150 per customer",
        "counterfactual_outcome": "If punitive returns policy: return rate drops to 9% but new customer acquisition drops 20%, negative reviews multiply",
        "near_miss": "CFO nearly cut instant refund program due to cash flow impact — LTV analysis justified the investment",
        "probability": 0.55,
        "consequence_magnitude": 5,
        "lesson": "Frictionless returns build trust that drives repurchase; the cost of easy returns is an investment in customer lifetime value"
    },
]

GOVERNMENT_TEMPLATES = [
    {
        "decision_point": "Evacuated coastal area 48 hours before hurricane landfall",
        "factual_outcome": "250K residents evacuated safely, hurricane caused property damage but zero fatalities in evacuation zone",
        "counterfactual_outcome": "If waited for upgraded forecast (24hr out): insufficient time for full evacuation, estimated 50-200 fatalities in flood zones",
        "near_miss": "Forecast models disagreed on path — governor ordered evacuation despite one model showing miss",
        "probability": 0.60,
        "consequence_magnitude": 10,
        "lesson": "Early evacuation saves lives even with forecast uncertainty; the cost of unnecessary evacuation is trivial vs preventable deaths"
    },
    {
        "decision_point": "Implemented automated eligibility verification for benefits program",
        "factual_outcome": "Processing time reduced from 45 days to 3 days, error rate dropped 85%, $12M annual admin savings",
        "counterfactual_outcome": "If manual processing continued: 45-day delays cause hardship, errors deny eligible applicants, $12M in unnecessary admin cost annually",
        "near_miss": "Automated system initially denied 8% of eligible applicants due to data matching errors — caught in parallel-run testing phase",
        "probability": 0.85,
        "consequence_magnitude": 6,
        "lesson": "Automation improves speed and accuracy but requires thorough testing with real cases; parallel runs catch errors before they harm citizens"
    },
    {
        "decision_point": "Published open data portal for government spending",
        "factual_outcome": "Journalists identified $3M in duplicate contracts, citizens reported 12 procurement irregularities, trust scores improved",
        "counterfactual_outcome": "If kept spending opaque: duplicate contracts continue, irregularities undetected, public trust continues eroding",
        "near_miss": "Portal nearly launched without PII redaction — security review caught 200 Social Security numbers in contract attachments",
        "probability": 0.70,
        "consequence_magnitude": 5,
        "lesson": "Transparency enables accountability and builds trust; data must be reviewed for privacy before publication"
    },
    {
        "decision_point": "Imposed temporary water use restrictions during drought",
        "factual_outcome": "Consumption dropped 30%, reservoir maintained above critical level, restrictions lifted after 3 months",
        "counterfactual_outcome": "If no restrictions: reservoir would have hit dead pool in 6 weeks, requiring emergency water imports at 10x cost",
        "near_miss": "Agricultural lobby nearly blocked restrictions — compromise exemption for critical crops preserved compliance",
        "probability": 0.75,
        "consequence_magnitude": 8,
        "lesson": "Early mild restrictions prevent later severe rationing; stakeholder compromise enables compliance better than absolute mandates"
    },
    {
        "decision_point": "Funded preventive infrastructure maintenance over new construction",
        "factual_outcome": "Bridge maintenance program extended service life by 25 years, cost $40M vs $200M replacement",
        "counterfactual_outcome": "If deferred maintenance for new projects: bridge deterioration forces emergency closure in 5 years, economic disruption of $500K/day during replacement",
        "near_miss": "Budget allocation was nearly reversed by incoming administration — engineering report on collapse risk preserved funding",
        "probability": 0.50,
        "consequence_magnitude": 8,
        "lesson": "Maintenance is unglamorous but prevents catastrophic failure; new construction ribbon-cutting incentives create maintenance debt"
    },
    {
        "decision_point": "Implemented contact tracing app with privacy-by-design architecture",
        "factual_outcome": "65% adoption rate due to trust, identified 40K exposure events, contributed to 15% reduction in transmission",
        "counterfactual_outcome": "If centralized surveillance approach: 20% adoption due to privacy concerns, effectiveness too low to impact transmission",
        "near_miss": "Initial vendor proposal included location tracking — privacy review forced redesign to Bluetooth-only proximity detection",
        "probability": 0.65,
        "consequence_magnitude": 7,
        "lesson": "Privacy-preserving design enables public trust and adoption; surveillance approaches fail because people opt out"
    },
    {
        "decision_point": "Established multi-agency coordination center before wildfire season",
        "factual_outcome": "First major fire: resources deployed in 2 hours, contained at 500 acres vs typical 2000 acres for similar ignitions",
        "counterfactual_outcome": "If separate agency responses: 6-hour coordination delay, fire grows to 2000+ acres, threatens residential areas",
        "near_miss": "Radio interoperability failed in first real deployment — pre-planned backup communication via satellite phones saved coordination",
        "probability": 0.70,
        "consequence_magnitude": 8,
        "lesson": "Inter-agency coordination must be practiced before emergencies; communication interoperability is the critical enabler"
    },
    {
        "decision_point": "Required environmental impact assessment before industrial zone approval",
        "factual_outcome": "Assessment identified groundwater contamination risk, site design modified with containment systems, approved with conditions",
        "counterfactual_outcome": "If approved without assessment: 30% chance of aquifer contamination within 10 years, $100M remediation, class-action lawsuits",
        "near_miss": "Developer lobbied for expedited approval without full study — council member's motion for full assessment passed by 1 vote",
        "probability": 0.30,
        "consequence_magnitude": 9,
        "lesson": "Environmental review costs are insignificant compared to remediation costs; prevention is orders of magnitude cheaper than cleanup"
    },
    {
        "decision_point": "Deployed social workers alongside police for mental health calls",
        "factual_outcome": "De-escalation success rate 89%, use of force incidents dropped 60%, repeat calls reduced 40%",
        "counterfactual_outcome": "If police-only response: 35% of mental health calls escalate to use of force, subjects traumatized, no underlying issue addressed",
        "near_miss": "Program nearly defunded after 1 incident where social worker was threatened — protocol revision added safety measures",
        "probability": 0.35,
        "consequence_magnitude": 8,
        "lesson": "Specialized response to specialized problems improves outcomes; one adverse event shouldn't eliminate effective programs"
    },
    {
        "decision_point": "Invested in cybersecurity for election infrastructure 18 months before election",
        "factual_outcome": "Detected and blocked 3 intrusion attempts, zero successful breaches, public confidence in results maintained",
        "counterfactual_outcome": "If legacy systems maintained: successful breach probable, even if no data changed, public confidence destroyed, legitimacy questioned",
        "near_miss": "One county system had unpatched vulnerability discovered 2 weeks before election — emergency patch deployed",
        "probability": 0.40,
        "consequence_magnitude": 10,
        "lesson": "Election integrity requires proactive security investment; the cost of perceived compromise exceeds any IT budget"
    },
]

SPACE_TEMPLATES = [
    {
        "decision_point": "Scrubbed launch due to upper-level wind shear data",
        "factual_outcome": "Launch delayed 48 hours, winds confirmed destructive at T+60s altitude, rocket and payload preserved",
        "counterfactual_outcome": "If launched: max-Q aerodynamic loading would have exceeded vehicle limits, potential breakup, $400M payload lost",
        "near_miss": "Wind data arrived 8 minutes before terminal count — launch was in final poll when scrub called",
        "probability": 0.35,
        "consequence_magnitude": 10,
        "lesson": "Natural environment constraints are absolute for launch vehicles; schedule pressure must never override atmospheric safety limits"
    },
    {
        "decision_point": "Performed debris avoidance maneuver on space station",
        "factual_outcome": "Station boosted orbit by 1.2km, debris passed through predicted orbital plane without impact",
        "counterfactual_outcome": "If no maneuver: 1-in-500 chance of catastrophic impact, potential loss of station and crew",
        "near_miss": "Debris tracking data updated 90 minutes before conjunction — barely enough time to compute and execute burn",
        "probability": 0.002,
        "consequence_magnitude": 10,
        "lesson": "Low-probability catastrophic events justify mitigation when stakes are irreversible; orbital debris decisions have zero margin for error"
    },
    {
        "decision_point": "Selected redundant flight computer design over single high-performance unit",
        "factual_outcome": "Primary computer failed during lunar orbit insertion — backup assumed control seamlessly, mission completed",
        "counterfactual_outcome": "If single computer: failure means loss of vehicle control during critical burn, crash into lunar surface, $1.2B mission lost",
        "near_miss": "Backup computer had firmware discrepancy from late change — caught during pre-flight integrated test 3 days before launch",
        "probability": 0.05,
        "consequence_magnitude": 10,
        "lesson": "Redundancy in space systems is not optional; single points of failure create binary mission outcomes"
    },
    {
        "decision_point": "Extended satellite mission beyond design life with reduced operations",
        "factual_outcome": "Satellite operated 3 additional years in degraded mode, returned $200M of additional science data",
        "counterfactual_outcome": "If decommissioned on schedule: $200M of science data never collected, follow-on mission gap of 4 years",
        "near_miss": "Solar array degradation nearly forced shutdown — power management redesign in software extended capability",
        "probability": 0.70,
        "consequence_magnitude": 5,
        "lesson": "Conservative design margins enable mission extension; operational creativity can extract value beyond design life"
    },
    {
        "decision_point": "Chose propulsive landing over parachute recovery for booster",
        "factual_outcome": "Booster landed successfully, refurbished in 30 days, reflown at 60% cost of new vehicle",
        "counterfactual_outcome": "If parachute/ocean recovery: saltwater damage requires 6-month refurbishment, 85% cost of new vehicle, ocean recovery risky",
        "near_miss": "Grid fin actuator stalled during landing burn — redundant hydraulic system took over with 200m altitude remaining",
        "probability": 0.85,
        "consequence_magnitude": 7,
        "lesson": "Reusability architecture choices determine economics; propulsive landing is harder but enables rapid reuse that parachutes cannot"
    },
    {
        "decision_point": "Aborted crewed spacecraft docking due to relative velocity error",
        "factual_outcome": "Docking aborted at 100m range, crew backed away safely, re-attempted next orbit successfully",
        "counterfactual_outcome": "If continued docking: closure rate 3x above limit would have caused hard contact, potential breach of docking port, crew at risk",
        "near_miss": "Navigation system showed nominal — crew commander overrode based on visual assessment of closure rate",
        "probability": 0.40,
        "consequence_magnitude": 10,
        "lesson": "Human judgment complements automated systems in spaceflight; abort decisions protect irreplaceable crew and hardware"
    },
    {
        "decision_point": "Included radiation-hardened electronics despite 3x cost premium",
        "factual_outcome": "Satellite survived 2 major solar particle events that would have fried commercial electronics, 15-year mission achieved",
        "counterfactual_outcome": "If commercial-grade electronics: single solar event would have ended mission in year 3, total loss of $800M investment",
        "near_miss": "Cost review nearly downgraded radiation spec — space weather physicist's presentation on solar cycle timing changed the decision",
        "probability": 0.60,
        "consequence_magnitude": 9,
        "lesson": "Space environment is unforgiving; cost optimization that reduces environmental resilience creates binary failure modes"
    },
    {
        "decision_point": "Routed Mars rover around suspected soft terrain",
        "factual_outcome": "Detour added 3 sols of driving but reached target safely on firm ground",
        "counterfactual_outcome": "If direct route: 40% chance of wheel entrapment in soft regolith, potential permanent immobilization of $2.5B asset",
        "near_miss": "Traverse planner initially classified terrain as firm — orbital imagery reanalysis at higher resolution revealed wind-deposited dust",
        "probability": 0.40,
        "consequence_magnitude": 10,
        "lesson": "Planetary rover operations trade time for certainty; immobilization is irreversible and ends missions permanently"
    },
    {
        "decision_point": "Conducted emergency spacewalk to repair cooling system",
        "factual_outcome": "Crew repaired ammonia leak in 6-hour EVA, station cooling restored, no health impacts",
        "counterfactual_outcome": "If delayed repair: ammonia system pressure would have dropped below operational minimum in 72hrs, station evacuation required",
        "near_miss": "EVA suit had CO2 scrubber anomaly during prep — backup suit used, adding 2-hour delay to already urgent timeline",
        "probability": 0.80,
        "consequence_magnitude": 9,
        "lesson": "Urgent repairs in space require immediate action with backup plans; equipment redundancy enables operations when primary systems fail"
    },
    {
        "decision_point": "Selected polar orbit over equatorial for Earth observation satellite",
        "factual_outcome": "Polar orbit provides full global coverage every 14 days, captures both poles, meets all science objectives",
        "counterfactual_outcome": "If equatorial orbit: miss polar regions entirely, 30% of Earth's surface unobserved, climate models lack critical polar data",
        "near_miss": "Launch vehicle performance margin was tight for polar insertion — 2% fuel margin remaining after orbit achieved",
        "probability": 0.90,
        "consequence_magnitude": 7,
        "lesson": "Orbit selection determines mission value permanently; the physics of orbital mechanics cannot be changed after launch"
    },
]

AGRICULTURE_TEMPLATES = [
    {
        "decision_point": "Delayed planting by 2 weeks based on soil temperature data",
        "factual_outcome": "Soil reached optimal 12°C, germination rate 94%, uniform emergence, strong early growth",
        "counterfactual_outcome": "If planted on calendar date: soil at 8°C, germination rate drops to 65%, patchy emergence, 20% yield reduction",
        "near_miss": "Seed supplier deadline nearly forced early planting — negotiated 1-week extension on delivery window",
        "probability": 0.65,
        "consequence_magnitude": 6,
        "lesson": "Data-driven planting decisions outperform calendar-based traditions; soil conditions matter more than dates"
    },
    {
        "decision_point": "Applied targeted fungicide based on disease model prediction",
        "factual_outcome": "Single application at predicted onset prevented epidemic, saved 95% of yield, minimal chemical use",
        "counterfactual_outcome": "If no application: disease would have spread exponentially, 40% yield loss by harvest, $200K revenue impact",
        "near_miss": "Weather window for application was 6 hours — rain arrived same evening that would have washed off treatment",
        "probability": 0.40,
        "consequence_magnitude": 7,
        "lesson": "Predictive disease models enable precise intervention; timing is critical for fungicide efficacy"
    },
    {
        "decision_point": "Invested in drip irrigation over flood irrigation",
        "factual_outcome": "Water use reduced 45%, yield increased 15% from consistent moisture, energy costs halved",
        "counterfactual_outcome": "If flood irrigation continued: water rights would have been curtailed in drought year 3, forced fallowing of 30% of acreage",
        "near_miss": "Drip system clogged from mineral buildup in month 2 — filtration upgrade prevented crop stress during critical growth phase",
        "probability": 0.55,
        "consequence_magnitude": 7,
        "lesson": "Water efficiency investments pay dividends in both normal and drought years; system maintenance is critical for reliability"
    },
    {
        "decision_point": "Diversified crop rotation instead of continuous corn",
        "factual_outcome": "Soybean-corn rotation broke pest cycle, reduced nitrogen input 40%, soil organic matter improved",
        "counterfactual_outcome": "If continuous corn: rootworm resistance develops by year 4, requiring expensive insecticide, yield decline 15% over 5 years",
        "near_miss": "Corn price spike nearly convinced farmer to break rotation — neighbor who did faced rootworm collapse 2 years later",
        "probability": 0.70,
        "consequence_magnitude": 6,
        "lesson": "Short-term commodity prices should not override long-term soil health strategies; rotation benefits compound over time"
    },
    {
        "decision_point": "Harvested grain at 18% moisture for early delivery premium",
        "factual_outcome": "Grain dried to 14% in bin, captured $0.30/bushel premium, drying cost $0.10/bushel, net gain $0.20/bushel",
        "counterfactual_outcome": "If waited for field dry to 14%: lost premium window, rain event 5 days later would have delayed harvest 2 weeks, quality downgrade",
        "near_miss": "Dryer fan motor failed during peak drying — hot grain nearly exceeded safe temperature before repair",
        "probability": 0.50,
        "consequence_magnitude": 5,
        "lesson": "Early harvest with controlled drying captures market premiums and avoids weather risk; dryer reliability is critical infrastructure"
    },
    {
        "decision_point": "Installed variable-rate seeding technology",
        "factual_outcome": "Seed population optimized per soil zone, yield increased 8% overall, seed cost reduced 5% from reduced overplanting",
        "counterfactual_outcome": "If flat-rate seeding: overpopulation in poor zones causes lodging, underpopulation in good zones wastes yield potential",
        "near_miss": "Prescription map had GPS offset error — first pass planted wrong rates before calibration check caught it",
        "probability": 0.75,
        "consequence_magnitude": 4,
        "lesson": "Precision agriculture matches inputs to field variability; calibration and verification prevent technology from causing harm"
    },
    {
        "decision_point": "Culled infected animals early to prevent herd spread",
        "factual_outcome": "3 animals culled, disease contained, remaining 200 head herd tested clean, quarantine lifted in 14 days",
        "counterfactual_outcome": "If delayed culling: disease spreads to 40+ animals within 10 days, full quarantine 90 days, $300K loss, movement restrictions affect neighbors",
        "near_miss": "Vet initially diagnosed as non-reportable condition — second opinion from state vet identified notifiable disease",
        "probability": 0.60,
        "consequence_magnitude": 8,
        "lesson": "Aggressive early disease response in livestock prevents exponential spread; hesitation costs herds"
    },
    {
        "decision_point": "Built grain storage rather than selling at harvest",
        "factual_outcome": "Stored grain, sold 4 months later at 25% price premium during supply tightness",
        "counterfactual_outcome": "If sold at harvest: captured lowest annual price, missed $150K premium opportunity, same input costs",
        "near_miss": "Grain quality started declining at month 3 from insect activity — fumigation at week 10 saved the stored value",
        "probability": 0.60,
        "consequence_magnitude": 5,
        "lesson": "Storage enables marketing flexibility but requires quality management; grain in poor condition loses the premium it was stored to capture"
    },
    {
        "decision_point": "Adopted cover crops despite no immediate yield benefit",
        "factual_outcome": "After 3 years: soil water-holding capacity up 30%, erosion eliminated, input costs down 20%, yield stability improved",
        "counterfactual_outcome": "If bare fallow continued: topsoil loss of 5 tons/acre/year, declining organic matter, increasing fertilizer dependency, vulnerability to drought",
        "near_miss": "Cover crop terminated 1 week late in year 1 — moisture competition nearly reduced main crop yield, teaching proper termination timing",
        "probability": 0.80,
        "consequence_magnitude": 6,
        "lesson": "Soil health investments have 3-5 year payback periods; short-term thinking depletes the resource base that future yields depend on"
    },
    {
        "decision_point": "Purchased crop insurance despite additional cost",
        "factual_outcome": "Hailstorm destroyed 60% of wheat crop, insurance paid $280K, farm remained solvent, replanted next season",
        "counterfactual_outcome": "If uninsured: $280K loss would have forced land sale or bankruptcy, multi-generational farm operation ended",
        "near_miss": "Premium payment was 3 days from deadline when hail forecast prompted purchase decision",
        "probability": 0.15,
        "consequence_magnitude": 10,
        "lesson": "Catastrophic risk requires insurance regardless of probability; the events you insure against are the ones that end operations"
    },
]

ROBOTICS_TEMPLATES = [
    {
        "decision_point": "Halted robotic arm mid-cycle due to vision system anomaly",
        "factual_outcome": "Arm stopped safely, vision recalibrated, cycle resumed with zero defects",
        "counterfactual_outcome": "If continued blind: 30% chance of misplaced weld on fuselage, $150K rework, 2-day line stoppage",
        "near_miss": "Safety PLC was 50ms from triggering emergency stop — software halt executed first, avoiding hard brake damage",
        "probability": 0.30,
        "consequence_magnitude": 7,
        "lesson": "Vision system integrity checks must gate physical actions; autonomous systems need self-doubt capabilities"
    },
    {
        "decision_point": "Deployed collaborative robot without safety cage using force-limiting",
        "factual_outcome": "Cobot operated alongside 12 workers for 6 months, zero contact incidents, productivity up 35%",
        "counterfactual_outcome": "If traditional caged robot: same productivity gain but $200K cage infrastructure, 40% floor space consumed, worker isolation increased",
        "near_miss": "Worker stumbled into cobot workspace — force limiter activated in 8ms, worker felt gentle push, no injury",
        "probability": 0.05,
        "consequence_magnitude": 8,
        "lesson": "Force-limited cobots enable human-robot collaboration safely; the technology must be matched to payload and speed requirements"
    },
    {
        "decision_point": "Rolled back autonomous navigation firmware after edge case failure",
        "factual_outcome": "Previous firmware restored, robot fleet operated at 95% capability while fix developed over 2 weeks",
        "counterfactual_outcome": "If kept new firmware: 1-in-200 chance of navigation failure per robot per day, with 50 robots = 1 incident every 4 days",
        "near_miss": "One robot had already entered the edge case state before rollback — manual intervention caught it mid-path",
        "probability": 0.50,
        "consequence_magnitude": 6,
        "lesson": "Fleet-wide firmware must be validated beyond lab conditions; rollback capability is essential for autonomous systems"
    },
    {
        "decision_point": "Added redundant encoder to critical joint on surgical robot",
        "factual_outcome": "Primary encoder failed during procedure — redundant encoder maintained position accuracy, surgery completed successfully",
        "counterfactual_outcome": "If single encoder: loss of position feedback mid-surgery, emergency manual takeover required, potential patient harm",
        "near_miss": "Redundant encoder disagreement was initially flagged as noise — investigation found primary encoder degrading",
        "probability": 0.03,
        "consequence_magnitude": 10,
        "lesson": "Medical robotics requires redundancy in every safety-critical sensor; single failures must never reach the patient"
    },
    {
        "decision_point": "Implemented geofenced exclusion zones for warehouse AGVs",
        "factual_outcome": "AGV approached pedestrian zone, geofence triggered stop, waited for clearance, no incidents",
        "counterfactual_outcome": "If relying only on LIDAR detection: sensor occlusion in narrow aisle could miss pedestrian, potential collision at 2m/s",
        "near_miss": "Reflective safety vest caused LIDAR ghost detection — geofence prevented AGV from stopping in traffic lane",
        "probability": 0.10,
        "consequence_magnitude": 8,
        "lesson": "Defense-in-depth for mobile robots combines sensing with hard boundaries; no single sensor modality is sufficient for safety"
    },
    {
        "decision_point": "Scheduled predictive maintenance on robot servo motor based on current signature",
        "factual_outcome": "Motor replaced during planned downtime, inspection confirmed bearing wear at 80% of failure threshold",
        "counterfactual_outcome": "If run-to-failure: servo seizes during production, arm crashes into fixture, $50K damage, 3 days repair",
        "near_miss": "Maintenance window was nearly postponed due to production pressure — manager approved based on failure cost analysis",
        "probability": 0.40,
        "consequence_magnitude": 7,
        "lesson": "Current signature analysis detects mechanical degradation before catastrophic failure; production pressure must not override safety data"
    },
    {
        "decision_point": "Chose simulation-validated path over shortest-distance path for pick-and-place",
        "factual_outcome": "Robot executed longer but validated path, maintained cycle time within tolerance, zero singularity events",
        "counterfactual_outcome": "If shortest path: joint 4 passes through singularity region, 15% chance of uncontrolled acceleration, potential fixture collision",
        "near_miss": "Path planner initially output shortest path as default — simulation caught singularity proximity in validation step",
        "probability": 0.15,
        "consequence_magnitude": 8,
        "lesson": "Kinematic simulation must validate all robot paths before execution; geometric shortcuts through singularities create unpredictable motion"
    },
    {
        "decision_point": "Implemented human-in-the-loop confirmation for drone delivery in urban area",
        "factual_outcome": "Operator confirmed clear landing zone, drone delivered package safely to rooftop pad",
        "counterfactual_outcome": "If fully autonomous: 5% chance of landing on occupied area, child on rooftop, or temporary obstruction not in map",
        "near_miss": "Drone detected clear zone but camera feed showed child's toy — operator correctly interpreted near-miss scenario",
        "probability": 0.05,
        "consequence_magnitude": 9,
        "lesson": "Urban autonomous operations require human verification for landing; maps are always stale and environments always changing"
    },
    {
        "decision_point": "Activated emergency stop on assembly line after torque limit exceeded",
        "factual_outcome": "Line stopped in 200ms, investigation found misaligned part, corrected, restarted in 15 minutes",
        "counterfactual_outcome": "If torque limit ignored: cross-threaded fastener would damage $30K component, rework of 50 assemblies downstream",
        "near_miss": "Torque threshold was nearly raised to reduce nuisance stops — this event validated the original conservative setting",
        "probability": 0.60,
        "consequence_magnitude": 6,
        "lesson": "Torque monitoring catches assembly errors at the source; loosening thresholds to reduce stops increases escape rate of defects"
    },
    {
        "decision_point": "Deployed digital twin for robot cell optimization before physical changes",
        "factual_outcome": "Simulation revealed interference between new tool and existing fixture, design modified virtually, zero physical rework",
        "counterfactual_outcome": "If built without simulation: interference discovered during commissioning, $80K fixture redesign, 4-week delay",
        "near_miss": "Digital twin was slightly out-of-date with a recent fixture modification — updated just before simulation run",
        "probability": 0.75,
        "consequence_magnitude": 5,
        "lesson": "Digital twins prevent costly physical rework but must mirror reality precisely; an inaccurate twin provides false confidence"
    },
]

INSURANCE_TEMPLATES = [
    {
        "decision_point": "Declined to underwrite coastal property based on updated flood model",
        "factual_outcome": "Policy declined, property flooded 8 months later, would have been $2.3M claim",
        "counterfactual_outcome": "If underwritten at standard rate: $2.3M claim against $12K premium, 190:1 loss ratio on that policy",
        "near_miss": "Previous flood model showed acceptable risk — new model incorporating sea level data changed assessment by 1 day before binding",
        "probability": 0.35,
        "consequence_magnitude": 8,
        "lesson": "Model updates that incorporate climate data prevent catastrophic underpricing; legacy models understate emerging risks"
    },
    {
        "decision_point": "Investigated suspicious claim pattern before paying",
        "factual_outcome": "Investigation revealed organized fraud ring, 12 related claims totaling $4.2M denied, ring prosecuted",
        "counterfactual_outcome": "If auto-paid per normal process: $4.2M paid to fraudsters, pattern never detected, ring continues targeting carrier",
        "near_miss": "Claims were individually below investigation threshold — analyst noticed pattern only because of shared repair shop",
        "probability": 0.80,
        "consequence_magnitude": 8,
        "lesson": "Pattern detection across claims catches fraud invisible at individual claim level; threshold-only systems miss coordinated schemes"
    },
    {
        "decision_point": "Purchased reinsurance treaty despite high premium year",
        "factual_outcome": "Hurricane season produced $500M in claims, reinsurance covered $380M, carrier remained solvent",
        "counterfactual_outcome": "If skipped reinsurance to save premium: $500M gross loss would have exceeded surplus, regulatory action, potential insolvency",
        "near_miss": "CFO argued against renewal citing 5 quiet years — CRO insisted based on accumulated exposure growth",
        "probability": 0.15,
        "consequence_magnitude": 10,
        "lesson": "Reinsurance is capital protection against tail events; quiet years increase complacency but don't reduce exposure"
    },
    {
        "decision_point": "Offered telematics-based discount for safe driving behavior",
        "factual_outcome": "Telematics cohort had 28% fewer claims, program profitable, attracted low-risk drivers from competitors",
        "counterfactual_outcome": "If standard rating only: best drivers subsidize worst, adverse selection as good risks leave for telematics competitors",
        "near_miss": "Privacy backlash nearly killed the program — opt-in design with clear data limits preserved adoption",
        "probability": 0.70,
        "consequence_magnitude": 5,
        "lesson": "Behavior-based pricing aligns incentives and attracts good risks; privacy-respecting design enables adoption"
    },
    {
        "decision_point": "Reserved additional IBNR for long-tail liability claims",
        "factual_outcome": "Claims emerged 3 years later at 40% above initial estimate, additional reserves covered the development",
        "counterfactual_outcome": "If reserved at initial estimate: reserve deficiency triggers surplus strain, regulatory scrutiny, rating downgrade",
        "near_miss": "Actuarial committee was split — conservative estimate adopted by 1 vote margin over optimistic projection",
        "probability": 0.55,
        "consequence_magnitude": 7,
        "lesson": "Long-tail liabilities consistently develop adversely; conservative reserving protects solvency better than optimistic projections"
    },
    {
        "decision_point": "Excluded cyber coverage from standard commercial policy",
        "factual_outcome": "Insured suffered ransomware attack, $800K loss not covered, purchased standalone cyber policy afterward",
        "counterfactual_outcome": "If silent cyber exposure remained: $800K claim paid from property policy never priced for cyber risk, portfolio-wide exposure of $200M unquantified",
        "near_miss": "Three other policyholders had similar attacks same quarter — portfolio would have faced $3M+ in silent cyber claims",
        "probability": 0.25,
        "consequence_magnitude": 8,
        "lesson": "Silent cyber exposure in traditional policies creates unpriced catastrophe risk; explicit exclusion forces proper pricing through standalone products"
    },
    {
        "decision_point": "Implemented parametric trigger for crop insurance payout",
        "factual_outcome": "Drought index triggered automatic payment within 5 days of threshold breach, farmer maintained cash flow for next planting",
        "counterfactual_outcome": "If traditional loss adjustment: 60-day assessment process, farmer misses planting window, second-season loss compounds first",
        "near_miss": "Weather station had calibration drift — secondary station data confirmed trigger was legitimate",
        "probability": 0.80,
        "consequence_magnitude": 6,
        "lesson": "Parametric insurance eliminates adjustment delays but requires robust trigger data; speed of payment prevents cascading losses"
    },
    {
        "decision_point": "Mandated IoT water leak sensors for commercial property coverage",
        "factual_outcome": "Sensor detected slow leak in server room, $500 repair vs estimated $2M water damage to IT infrastructure",
        "counterfactual_outcome": "If no sensor requirement: water damage discovered after weekend, servers destroyed, business interruption claim of $5M+",
        "near_miss": "Sensor battery was at 5% — maintenance alert triggered replacement 1 week before the leak event",
        "probability": 0.20,
        "consequence_magnitude": 9,
        "lesson": "Loss prevention technology reduces claim frequency and severity; mandating sensors aligns insurer and insured interests"
    },
    {
        "decision_point": "Repriced workers compensation portfolio after claims trend analysis",
        "factual_outcome": "15% rate increase applied to high-risk segments, loss ratio improved from 85% to 68% within 2 years",
        "counterfactual_outcome": "If maintained pricing: loss ratio would have hit 95%+, combined ratio unprofitable, forced exit from line of business",
        "near_miss": "Sales team lobbied against increase citing competitive pressure — actuarial analysis showing trajectory toward insolvency prevailed",
        "probability": 0.65,
        "consequence_magnitude": 7,
        "lesson": "Pricing discipline preserves long-term market participation; underpricing for market share leads to forced withdrawal"
    },
    {
        "decision_point": "Denied business interruption claim based on virus exclusion clause",
        "factual_outcome": "Claim denied per policy terms, insured litigated unsuccessfully, exclusion upheld by court",
        "counterfactual_outcome": "If no exclusion existed: pandemic-related BI claims would have totaled $40B industry-wide, multiple carrier insolvencies",
        "near_miss": "Exclusion language was nearly removed in 2018 policy simplification project — underwriting review preserved it",
        "probability": 0.90,
        "consequence_magnitude": 10,
        "lesson": "Exclusions for systemic uninsurable risks protect carrier solvency and policyholder security; clarity in policy language prevents ambiguity litigation"
    },
]

# Map world names to their counterfactual templates
WORLD_TEMPLATES: Dict[str, List[Dict]] = {
    "healthcare": HEALTHCARE_TEMPLATES,
    "finance": FINANCE_TEMPLATES,
    "coding": CODING_TEMPLATES,
    "energy": ENERGY_TEMPLATES,
    "construction": CONSTRUCTION_TEMPLATES,
    "defense": DEFENSE_TEMPLATES,
    "transport": TRANSPORT_TEMPLATES,
    "education": EDUCATION_TEMPLATES,
    "ecommerce": ECOMMERCE_TEMPLATES,
    "government": GOVERNMENT_TEMPLATES,
    "space": SPACE_TEMPLATES,
    "agriculture": AGRICULTURE_TEMPLATES,
    "robotics": ROBOTICS_TEMPLATES,
    "insurance": INSURANCE_TEMPLATES,
}

# Alias for spec compatibility
WORLD_COUNTERFACTUALS = WORLD_TEMPLATES


class CounterfactualEngine:
    """Generate counterfactual reasoning layers for training records.

    For every significant decision in a record, generates:
    1. What actually happened (factual)
    2. What almost happened (near-miss alternative)
    3. What would have happened if a different choice was made (counterfactual)

    This trains AI on: planning, consequence prediction, strategy evaluation.
    """

    # Probability of injecting counterfactual into any given record
    INJECTION_RATE = 0.20

    def __init__(self, rng: random.Random):
        self.rng = rng

    def _select_template(self, world: str) -> Dict:
        """Select a random counterfactual template for the given world."""
        templates = WORLD_TEMPLATES.get(world, [])
        if not templates:
            # Fallback: pick from a random available world
            available_worlds = list(WORLD_TEMPLATES.keys())
            fallback_world = self.rng.choice(available_worlds)
            templates = WORLD_TEMPLATES[fallback_world]
        return self.rng.choice(templates)

    def _contextualize_template(self, template: Dict, record: Dict) -> Dict:
        """Add record-specific context to the selected template."""
        # Build the counterfactual structure
        counterfactual = {
            "decision_point": template["decision_point"],
            "factual_outcome": template["factual_outcome"],
            "counterfactual_outcome": template["counterfactual_outcome"],
            "near_miss": template.get("near_miss", ""),
            "probability": template["probability"],
            "consequence_magnitude": template["consequence_magnitude"],
            "lesson": template["lesson"],
        }

        # Add record context to anchor the counterfactual
        if "decision" in record:
            counterfactual["record_decision"] = record["decision"]
        if "event_type" in record:
            counterfactual["record_event_type"] = record["event_type"]
        if "outcome" in record:
            counterfactual["record_outcome"] = record["outcome"]

        # Add reasoning metadata
        counterfactual["reasoning_type"] = self.rng.choice([
            "consequential_thinking",
            "risk_assessment",
            "opportunity_cost_analysis",
            "near_miss_learning",
            "decision_tree_evaluation",
        ])

        # Add temporal framing
        counterfactual["temporal_framing"] = self.rng.choice([
            "what_if_earlier",
            "what_if_later",
            "what_if_different_choice",
            "what_if_no_action",
            "what_if_opposite_action",
        ])

        return counterfactual

    def generate_counterfactuals(self, record: Dict, world: str) -> Dict:
        """Given a record with a decision/event, generate alternative timelines.

        Returns a dictionary containing:
        - counterfactual: the primary alternative timeline
        - alternatives: list of 1-2 additional brief alternatives
        - meta: reasoning metadata about the counterfactual generation
        """
        template = self._select_template(world)
        primary = self._contextualize_template(template, record)

        # Generate 1-2 additional brief alternatives
        num_alternatives = self.rng.randint(1, 2)
        alternatives = []
        for _ in range(num_alternatives):
            alt_template = self._select_template(world)
            # Avoid exact duplicates
            if alt_template["decision_point"] != template["decision_point"]:
                alternatives.append({
                    "decision_point": alt_template["decision_point"],
                    "counterfactual_outcome": alt_template["counterfactual_outcome"],
                    "probability": alt_template["probability"],
                    "consequence_magnitude": alt_template["consequence_magnitude"],
                })

        result = {
            "counterfactual": primary,
            "alternatives": alternatives,
            "meta": {
                "world": world,
                "generation_method": "template_based",
                "template_pool_size": len(WORLD_TEMPLATES.get(world, [])),
                "purpose": "Train AI on consequence prediction, planning, and strategic evaluation",
            },
        }

        return result

    def inject(self, record: Dict, world: str) -> Dict:
        """Add counterfactual layer to record (20% of records).

        Args:
            record: The original record dictionary
            world: The world/domain identifier

        Returns:
            The record with an optional _ai_training.counterfactual layer added
        """
        # Always inject if called directly with a matching record,
        # but use probability gate for general pipeline use
        should_inject = self.rng.random() < self.INJECTION_RATE

        # If the record has explicit decision indicators, boost injection rate
        has_decision_signal = any(
            key in record for key in [
                "decision", "choice", "action", "intervention",
                "event_type", "incident", "resolution",
            ]
        )
        if has_decision_signal:
            should_inject = self.rng.random() < (self.INJECTION_RATE * 3)  # 60% for decision-rich records

        if not should_inject:
            return record

        # Generate counterfactual data
        cf_data = self.generate_counterfactuals(record, world)

        # Add to record under _ai_training namespace
        result = dict(record)
        if "_ai_training" not in result:
            result["_ai_training"] = {}

        result["_ai_training"]["counterfactual"] = cf_data["counterfactual"]
        result["_ai_training"]["counterfactual_alternatives"] = cf_data["alternatives"]
        result["_ai_training"]["counterfactual_meta"] = cf_data["meta"]

        return result
