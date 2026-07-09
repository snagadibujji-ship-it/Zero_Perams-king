"""Multi-turn dialogue generator for Hybrid-HybridAI synthetic training data.

Generates deterministic, domain-specific multi-turn conversations for training
language models on industrial operations scenarios. Supports 20+ worlds with
tailored system prompts, scenario templates, and difficulty-controlled turn counts.

Usage:
    import random
    rng = random.Random(42)
    record = generate_multi_turn("healthcare", rng, tick=1, difficulty="hard")
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# World-specific system prompts — professional personas for each domain
# ---------------------------------------------------------------------------

WORLD_SYSTEM_PROMPTS: dict[str, str] = {
    "healthcare": (
        "You are an experienced emergency medicine physician with 15 years of "
        "critical care experience. You provide evidence-based clinical guidance, "
        "interpret diagnostic results, and recommend treatment protocols following "
        "current medical guidelines. You communicate clearly with clinical staff "
        "and prioritize patient safety."
    ),
    "finance": (
        "You are a senior quantitative risk analyst at a global investment bank. "
        "You specialize in portfolio risk assessment, derivatives pricing, regulatory "
        "compliance (Basel III/IV), and market microstructure. You provide precise "
        "numerical analysis and cite relevant financial regulations."
    ),
    "coding": (
        "You are a principal software engineer with expertise in distributed systems, "
        "performance optimization, and production incident response. You write clean, "
        "well-tested code and guide teams through complex debugging scenarios using "
        "systematic root-cause analysis."
    ),
    "industries": (
        "You are a senior industrial process engineer specializing in continuous "
        "improvement, Lean Six Sigma, and plant operations optimization. You analyze "
        "production metrics, identify bottlenecks, and recommend process changes with "
        "quantified ROI projections."
    ),
    "cybersecurity": (
        "You are a senior threat analyst and incident responder with CISSP and OSCP "
        "certifications. You specialize in APT detection, malware analysis, SIEM "
        "correlation, and NIST/MITRE ATT&CK framework application. You guide SOC "
        "teams through active incidents with precision."
    ),
    "manufacturing": (
        "You are a manufacturing systems engineer with expertise in CNC operations, "
        "quality control (SPC/Six Sigma), predictive maintenance, and MES integration. "
        "You diagnose equipment failures, optimize production schedules, and ensure "
        "compliance with ISO 9001/IATF 16949 standards."
    ),
    "supplychain": (
        "You are a supply chain operations director with expertise in demand planning, "
        "logistics optimization, vendor management, and S&OP processes. You use "
        "quantitative methods to optimize inventory levels, reduce lead times, and "
        "mitigate supply disruptions across global networks."
    ),
    "energy": (
        "You are a power systems engineer specializing in grid operations, renewable "
        "integration, load balancing, and NERC compliance. You monitor real-time grid "
        "conditions, manage generation dispatch, and coordinate emergency responses "
        "to maintain system reliability."
    ),
    "defense": (
        "You are a military operations analyst with expertise in C4ISR systems, "
        "threat assessment, mission planning, and logistics coordination. You provide "
        "tactical and strategic recommendations based on intelligence analysis and "
        "operational constraints."
    ),
    "education": (
        "You are an instructional design specialist and educational technology "
        "consultant. You design adaptive learning pathways, analyze student performance "
        "data, implement competency-based assessment frameworks, and optimize LMS "
        "configurations for diverse learner populations."
    ),
    "telecom": (
        "You are a network operations center (NOC) senior engineer specializing in "
        "5G/LTE infrastructure, fiber optic networks, QoS management, and service "
        "assurance. You troubleshoot complex network degradations and coordinate "
        "maintenance windows across multi-vendor environments."
    ),
    "agriculture": (
        "You are a precision agriculture specialist with expertise in crop modeling, "
        "IoT sensor networks, drone-based imaging analysis, and automated irrigation "
        "systems. You optimize yield through data-driven decisions on planting, "
        "fertilization, and pest management."
    ),
    "logistics": (
        "You are a logistics operations manager specializing in fleet management, "
        "route optimization, warehouse automation, and last-mile delivery. You use "
        "real-time telemetry and predictive analytics to maintain SLA compliance "
        "and reduce transportation costs."
    ),
    "aviation": (
        "You are an aviation maintenance and operations specialist with A&P "
        "certification and 20 years of experience. You oversee airworthiness "
        "directives, MEL management, predictive maintenance programs, and AOG "
        "resolution for commercial fleets."
    ),
    "maritime": (
        "You are a port operations and maritime logistics expert specializing in "
        "vessel traffic management, berth scheduling, container terminal optimization, "
        "and IMO regulatory compliance. You coordinate complex multi-modal transfers "
        "and manage disruption recovery."
    ),
    "mining": (
        "You are a mining operations engineer with expertise in extraction planning, "
        "geotechnical monitoring, equipment fleet management, and environmental "
        "compliance. You optimize ore processing, manage blast patterns, and ensure "
        "worker safety in underground and open-pit operations."
    ),
    "pharma": (
        "You are a pharmaceutical manufacturing specialist with expertise in GMP "
        "compliance, batch process validation, CAPA management, and FDA 21 CFR Part 11 "
        "requirements. You oversee production quality, deviation investigations, and "
        "technology transfer protocols."
    ),
    "retail": (
        "You are a retail operations analyst specializing in omnichannel fulfillment, "
        "demand forecasting, markdown optimization, and store operations. You leverage "
        "POS data, foot traffic analytics, and inventory models to maximize revenue "
        "per square foot."
    ),
    "construction": (
        "You are a construction project controls engineer with expertise in CPM "
        "scheduling, earned value management, BIM coordination, and safety compliance. "
        "You manage multi-trade coordination, resolve RFIs, and maintain project "
        "velocity on complex commercial builds."
    ),
    "water": (
        "You are a water utility operations engineer specializing in SCADA-controlled "
        "treatment plants, distribution network management, regulatory compliance "
        "(EPA/SDWA), and demand forecasting. You optimize chemical dosing, manage "
        "pressure zones, and respond to water quality events."
    ),
}


# ---------------------------------------------------------------------------
# Scenario templates — (scenario_type, [user_prompt_templates], [assistant_response_templates])
# Each world has 5+ scenarios. Templates use {placeholders} filled at generation time.
# ---------------------------------------------------------------------------

SCENARIO_TEMPLATES: dict[str, list[tuple[str, list[str], list[str]]]] = {
    "healthcare": [
        (
            "diagnostic_reasoning",
            [
                "Patient presents with {symptom1} and {symptom2}. Vitals: HR {hr}, BP {bp}, SpO2 {spo2}%. History of {history}.",
                "Lab results are back: {lab1} is {lab1_value}, {lab2} is {lab2_value}. {additional_finding}.",
                "What's the most likely diagnosis and what should we order next?",
                "The {imaging} shows {imaging_finding}. Does this change your assessment?",
                "Patient is now {status_change}. How do we adjust the plan?",
            ],
            [
                "Based on the presentation of {symptom1} with {symptom2} and the hemodynamic profile, my differential includes {ddx1}, {ddx2}, and {ddx3}. I'd prioritize {priority_workup}.",
                "The {lab1} elevation to {lab1_value} combined with {lab2} at {lab2_value} narrows our differential significantly. This pattern is consistent with {likely_dx}. I recommend {next_step}.",
                "Given the clinical picture, {likely_dx} is most probable. We should order {order1} and {order2} to confirm and guide management.",
                "The {imaging_finding} on {imaging} is {significance}. This {confirms_or_changes} our working diagnosis. I'd now recommend {revised_plan}.",
                "With the patient now {status_change}, we need to {intervention}. Start {medication} and reassess in {timeframe}.",
            ],
        ),
        (
            "incident_response",
            [
                "Code Blue called in {location}. Patient found {found_state}. ETA of crash cart: {eta}.",
                "First rhythm check shows {rhythm}. {additional_info}.",
                "We've given {intervention1}. Still in {rhythm2}. What's next per ACLS?",
                "ROSC achieved. Patient now {post_rosc_state}. What's the post-arrest protocol?",
                "Family is here asking about prognosis. What do we tell them?",
            ],
            [
                "Initiate BLS immediately — high-quality compressions at 100-120/min, depth 5-6cm. Ensure airway with {airway_device}. Once crash cart arrives, attach defib pads immediately.",
                "For {rhythm}, the protocol is {protocol}. {shock_or_noshock}. Ensure IV/IO access and prepare {first_med} {dose}.",
                "After {intervention1} with persistent {rhythm2}, administer {next_med} {next_dose} IV push. Continue CPR. Consider {reversible_cause} — check for {h_and_t}.",
                "Post-ROSC protocol: target MAP >65, initiate {temperature_mgmt}, obtain 12-lead ECG and serial troponins. Consider {cath_decision} based on ECG findings. Start {drip} for hemodynamic support.",
                "Communicate honestly: the patient had a cardiac arrest and was resuscitated. Prognosis depends on {prognostic_factors}. We'll know more in {prognostic_timeframe}. Offer support services.",
            ],
        ),
        (
            "troubleshooting",
            [
                "Ventilator alarming high pressure on patient in {unit}. Settings: mode {vent_mode}, TV {tv}mL, PEEP {peep}cmH2O, FiO2 {fio2}%.",
                "I've checked the circuit — {circuit_finding}. Patient exam shows {exam_finding}.",
                "Suctioning returned {suction_result}. Pressure still elevated. What else?",
                "CXR shows {cxr_finding}. How do we manage?",
                "After intervention, pressures normalized but SpO2 dropped to {new_spo2}%. Thoughts?",
            ],
            [
                "High pressure alarm with those settings suggests {cause_list}. Systematic approach: first disconnect patient and bag — if bagging is easy, problem is circuit/ETT. If difficult, problem is patient (bronchospasm, pneumothorax, etc.).",
                "Given {circuit_finding} and {exam_finding}, I'm concerned about {primary_concern}. Let's {immediate_action} and get a stat {stat_order}.",
                "With {suction_result} and persistent high pressures, consider {next_differential}. Auscultate for {auscultation_target}. May need {procedure} if confirmed.",
                "The {cxr_finding} requires {management}. {urgency_statement}. Have {equipment} at bedside and notify {team}.",
                "SpO2 drop post-intervention suggests {post_intervention_cause}. Check {check_list}. May need to adjust PEEP to {new_peep} and FiO2 to {new_fio2}%.",
            ],
        ),
        (
            "planning",
            [
                "We need to plan discharge for {patient_type} patient with {conditions}. Current status: {current_status}.",
                "Insurance approved {approved_days} days. Patient needs {need_list}. How do we coordinate?",
                "Home situation: {home_situation}. Is home discharge safe?",
                "What follow-up appointments and monitoring do we need to arrange?",
                "Patient is requesting {patient_request}. How do we handle this?",
            ],
            [
                "For discharge planning of this {patient_type} patient, we need to address: {planning_items}. Let's involve {team_members} and target discharge by {target_day}.",
                "With {approved_days} days, prioritize {priorities}. For {need_list}, contact {resources}. Start the referrals today to avoid delays.",
                "Given {home_situation}, {safety_assessment}. I'd recommend {recommendation} with {support_services} in place before discharge.",
                "Schedule: {followup_schedule}. Monitoring plan: {monitoring_plan}. Ensure patient has {equipment_supplies} and knows {red_flags} to watch for.",
                "Regarding {patient_request}: {clinical_assessment}. We can {accommodation} while ensuring {safety_measure}.",
            ],
        ),
        (
            "decision_making",
            [
                "Ethical consult requested: {ethical_scenario}. Patient is {patient_capacity}.",
                "Family member {family_member} is insisting on {family_demand}. Patient previously expressed {patient_wish}.",
                "The team is split — {team_opinion_a} vs {team_opinion_b}. What framework should we use?",
                "Legal has weighed in: {legal_opinion}. How does this affect our clinical decision?",
                "We need to make a final recommendation. What's your position?",
            ],
            [
                "This involves core bioethical principles: autonomy, beneficence, non-maleficence, and justice. Given {ethical_scenario} with patient {patient_capacity}, the key question is {key_question}.",
                "Patient autonomy takes precedence when capacity is established. The documented wish for {patient_wish} should guide us. We need to {communication_plan} with {family_member}.",
                "I recommend the {framework} framework here. Considering {team_opinion_a} vs {team_opinion_b}, the evidence supports {evidence_position} because {rationale}.",
                "Legal guidance on {legal_opinion} {aligns_or_conflicts} with clinical best practice. We should {action} while documenting {documentation_needs}.",
                "My recommendation: {final_recommendation}. Rationale: {rationale_summary}. Document thoroughly and ensure {follow_through}.",
            ],
        ),
    ],
    "finance": [
        (
            "diagnostic_reasoning",
            [
                "Portfolio VaR breach detected: {portfolio} showing {var_value} against {limit} limit. Sector exposure: {sectors}.",
                "Drill-down shows concentration in {concentrated_asset}. Greeks: delta {delta}, gamma {gamma}, vega {vega}.",
                "Stress test results: {stress_scenario} yields P&L of {pnl}. Is this within risk appetite?",
                "Counterparty {counterparty} just got downgraded to {rating}. Exposure is {exposure_value}.",
                "What hedging strategy do you recommend to bring us back within limits?",
            ],
            [
                "VaR breach of {var_value} against {limit} indicates {breach_severity} risk exceedance. Given sector exposure to {sectors}, this is likely driven by {driver}. Recommend immediate review of {review_items}.",
                "Concentration in {concentrated_asset} with those Greeks suggests {risk_profile}. The gamma of {gamma} means {gamma_implication}. We need to {greek_action}.",
                "Under {stress_scenario}, the {pnl} P&L {within_or_exceeds} risk appetite per {policy}. {recommendation}. Consider {mitigation} if we retain the position.",
                "Downgrade to {rating} triggers {trigger_action} per CSA agreements. CVA adjustment needed: approximately {cva_adjustment}. Recommend {counterparty_action}.",
                "Optimal hedge: {hedge_strategy}. Cost: approximately {hedge_cost} bps. This reduces VaR by {var_reduction}% and brings portfolio within limits. Execute via {execution_venue}.",
            ],
        ),
        (
            "troubleshooting",
            [
                "Trade reconciliation showing {recon_breaks} breaks today vs normal {normal_breaks}. Concentrated in {asset_class} book.",
                "SWIFT messages show {swift_issue}. Custodian confirms {custodian_status}.",
                "Found {root_cause_candidate} in the booking system. {additional_evidence}.",
                "We need to resolve by {deadline} for regulatory reporting. What's the priority order?",
                "How do we prevent this class of break going forward?",
            ],
            [
                "Spike from {normal_breaks} to {recon_breaks} breaks in {asset_class} suggests {likely_cause}. Priority: classify breaks by {classification_method} and focus on {high_priority_type} first.",
                "SWIFT showing {swift_issue} combined with custodian status {custodian_status} points to {diagnosis}. Check {check_items} in the settlement chain.",
                "If {root_cause_candidate} is confirmed, {impact_assessment}. Remediation: {remediation_steps}. Audit trail shows {additional_evidence} which supports this root cause.",
                "For {deadline} compliance: Tier 1 (regulatory impact) — {tier1_actions}. Tier 2 (client-facing) — {tier2_actions}. Tier 3 (internal) — {tier3_actions}.",
                "Prevention: implement {control1} at booking time, add {control2} validation in STP flow, and establish {control3} threshold alerts. Estimated implementation: {timeline}.",
            ],
        ),
        (
            "incident_response",
            [
                "Flash crash detected in {instrument}. Price moved {price_move}% in {timeframe}. Our exposure: {exposure}.",
                "Market maker {mm} has withdrawn quotes. Order book depth now {depth}. Spread at {spread}.",
                "Regulator is on the phone asking about our activity. We executed {volume} in the window.",
                "Position is {position_status}. Mark-to-market loss currently {mtm_loss}.",
                "What's our communication plan for clients and compliance?",
            ],
            [
                "Immediate actions: {immediate_actions}. Halt algorithmic execution on {instrument}. Check circuit breakers at {levels}. Assess whether our flow contributed to the move.",
                "With {mm} out and spread at {spread}, liquidity is critically impaired. Do NOT attempt to unwind at market. Set {limit_orders} to capture reversion. Alert prime broker.",
                "For the regulatory inquiry: {regulatory_response}. Provide {data_items} showing our orders were {order_characterization}. Engage compliance and legal immediately.",
                "With MTM loss at {mtm_loss} and position {position_status}: {risk_action}. P&L reserve of {reserve} recommended. Notify {stakeholders} per escalation matrix.",
                "Client communication: {client_msg}. Compliance filing: {compliance_filing} within {filing_deadline}. Internal post-mortem scheduled for {postmortem_time}.",
            ],
        ),
        (
            "planning",
            [
                "Q{quarter} rebalancing due. AUM {aum}, target allocation: {target_alloc}. Current drift: {drift}.",
                "Transaction cost analysis shows {tca_estimate} for full rebalance. Market conditions: {market_conditions}.",
                "Tax-loss harvesting opportunities identified in {tlh_positions}. Estimated tax benefit: {tax_benefit}.",
                "Client wants to add {new_mandate} mandate. How does this affect the overall plan?",
                "Final trade list review — any concerns before execution?",
            ],
            [
                "Current drift of {drift} exceeds rebalancing threshold. Priority trades: {priority_trades}. Consider {approach} to minimize market impact given AUM of {aum}.",
                "TCA of {tca_estimate} is {tca_assessment}. Recommend {execution_strategy} over {execution_window} to reduce implementation shortfall. Use {algo_choice} for {large_orders}.",
                "Tax-loss harvesting in {tlh_positions} yields {tax_benefit}. Watch wash-sale rules — substitute with {substitutes} maintaining factor exposure. Net benefit after costs: {net_benefit}.",
                "Adding {new_mandate} changes target allocation to {revised_alloc}. Transition cost: {transition_cost}. Recommend phasing over {phase_period} to manage tracking error.",
                "Trade list review: {list_summary}. Concerns: {concerns}. Recommend {final_adjustments} before sending to execution desk at {execution_time}.",
            ],
        ),
        (
            "decision_making",
            [
                "Investment committee reviewing {opportunity}. Expected return: {expected_return}, risk: {risk_metric}.",
                "Due diligence found {dd_finding}. How material is this?",
                "Comparable transactions: {comps}. Our valuation model says {model_value} vs market at {market_value}.",
                "Liquidity profile: {liquidity}. Redemption terms: {redemption_terms}. Does this fit our mandate?",
                "Committee vote needed. What's your recommendation and conviction level?",
            ],
            [
                "Risk-adjusted return of {risk_adj_return} is {attractiveness} relative to our hurdle rate of {hurdle}. Key drivers: {key_drivers}. Main risks: {main_risks}.",
                "Finding of {dd_finding} is {materiality} material. {impact_on_thesis}. Mitigant: {mitigant}. Adjust expected return to {adjusted_return} if unmitigated.",
                "Model value of {model_value} vs market {market_value} implies {discount_premium}. Comps support {comp_conclusion}. Key assumption sensitivity: {sensitivity}.",
                "Liquidity profile of {liquidity} with {redemption_terms} redemptions {fits_or_not} our mandate constraint of {mandate_constraint}. {liquidity_recommendation}.",
                "Recommendation: {recommendation} at {conviction} conviction. Position size: {position_size} of NAV. Stop-loss at {stop_loss}. Review trigger: {review_trigger}.",
            ],
        ),
    ],
    "coding": [
        (
            "troubleshooting",
            [
                "Production alert: {service} returning {error_rate}% 5xx errors. Started {time_ago}. No recent deploys in the last {hours}h.",
                "Logs show: `{log_snippet}`. Correlated with {correlated_metric} spike to {metric_value}.",
                "Traced to {component}. The {resource} is at {utilization}% utilization. Connection pool: {pool_status}.",
                "Applying {mitigation} helped temporarily but errors resumed after {duration}.",
                "Found root cause: {root_cause}. What's the proper fix and how do we prevent regression?",
            ],
            [
                "5xx spike without recent deploys suggests infrastructure or upstream dependency issue. Check: {check_list}. Correlate with {correlation_targets}. Set up {monitoring_action} for real-time triage.",
                "Log pattern `{log_snippet}` with {correlated_metric} spike indicates {diagnosis}. This typically means {explanation}. Immediate mitigation: {mitigation_steps}.",
                "At {utilization}% on {resource} with pool {pool_status}, we're hitting {limit_type} limits. Short-term: {short_term_fix}. The {component} needs {architectural_change}.",
                "{mitigation} providing only temporary relief confirms {confirmation}. The underlying issue is {underlying_issue}. We need to {definitive_action}.",
                "Fix for {root_cause}: {fix_description}. PR should include: {pr_contents}. Regression prevention: add {test_type} test covering {test_scenario}. Update runbook with {runbook_addition}.",
            ],
        ),
        (
            "diagnostic_reasoning",
            [
                "Performance regression detected: {endpoint} P99 latency went from {before}ms to {after}ms after {change_event}.",
                "Profiling shows {hotspot} consuming {cpu_percent}% CPU. Allocation rate: {alloc_rate} MB/s.",
                "Database query plan for the hot path: {query_plan_summary}. Index usage: {index_status}.",
                "Tried {optimization_attempt} but P99 only improved to {partial_improvement}ms.",
                "What's the optimal architecture to sustain {target_latency}ms at {target_rps} RPS?",
            ],
            [
                "P99 jump from {before}ms to {after}ms post {change_event} suggests {hypothesis}. Profile with {profiling_tool} focusing on {focus_area}. Check if {change_event} altered {altered_behavior}.",
                "{hotspot} at {cpu_percent}% with {alloc_rate} MB/s allocation indicates {gc_pressure_or_compute}. Optimize by {optimization_strategy}. Consider {data_structure_change}.",
                "Query plan showing {query_plan_summary} with {index_status} means {plan_assessment}. Recommend {index_action}. Expected improvement: {expected_improvement}.",
                "Partial improvement to {partial_improvement}ms means {partial_diagnosis}. Remaining latency is in {remaining_component}. Need to {next_optimization}.",
                "For {target_latency}ms at {target_rps} RPS: {architecture_recommendation}. Key changes: {key_changes}. Estimated capacity: {capacity_estimate}.",
            ],
        ),
        (
            "planning",
            [
                "Designing new {system_type} service. Requirements: {requirements}. SLA: {sla}.",
                "Expected load: {load_profile}. Data model: {data_model_summary}. Consistency needs: {consistency}.",
                "Team has experience with {tech_stack}. Timeline: {timeline}. Any concerns with {proposed_approach}?",
                "How should we handle {failure_mode}? What's the fallback strategy?",
                "What's the testing and rollout plan for safe deployment?",
            ],
            [
                "For {system_type} with {sla} SLA, recommend {architecture_pattern}. Key components: {components}. This handles {requirements} via {mechanism}.",
                "Given {load_profile} with {consistency} requirements, use {storage_choice} for {storage_reason}. Data model: {data_model_recommendation}. Partition strategy: {partition_strategy}.",
                "With {tech_stack} experience and {timeline} timeline: {feasibility_assessment}. Concern with {proposed_approach}: {concern}. Alternative: {alternative}.",
                "For {failure_mode}: implement {resilience_pattern}. Fallback: {fallback_strategy}. Circuit breaker config: {cb_config}. Recovery: {recovery_mechanism}.",
                "Rollout plan: {rollout_phases}. Testing: {test_strategy}. Feature flags for {flagged_features}. Rollback criteria: {rollback_criteria}. Monitoring: {monitoring_plan}.",
            ],
        ),
        (
            "incident_response",
            [
                "SEV1: {service} is completely down. {users_affected} users affected. Started {start_time}.",
                "Status page shows {dependency_status}. Our healthchecks: {healthcheck_status}.",
                "Attempting rollback to {version}. Deploy pipeline shows {pipeline_status}.",
                "Rollback {rollback_result}. Current impact: {current_impact}. Stakeholders asking for ETA.",
                "Service restored. What's the post-incident process?",
            ],
            [
                "SEV1 declared. Incident commander: establish {ic_actions}. Immediate: {immediate_steps}. Communication: notify {notify_list} with {initial_message}.",
                "Dependency {dependency_status} combined with healthcheck {healthcheck_status} suggests {failure_point}. Try {diagnostic_steps}. Parallel track: {parallel_action}.",
                "Pipeline {pipeline_status}: {pipeline_action}. If rollback blocked, {alternative_recovery}. ETA for rollback completion: {rollback_eta}.",
                "Rollback {rollback_result}: {next_steps}. Communicate to stakeholders: {stakeholder_update}. If partial restoration possible: {partial_options}.",
                "Post-incident: {postmortem_timeline}. Blameless retrospective covering {retro_topics}. Action items: {action_items}. Prevention: {prevention_measures}.",
            ],
        ),
        (
            "decision_making",
            [
                "Tech debt prioritization: {debt_items}. Sprint capacity: {capacity}. Upcoming feature: {feature} depends on {dependency}.",
                "Option A: {option_a}. Option B: {option_b}. Team preference split {split}.",
                "Benchmarks show: Option A — {bench_a}. Option B — {bench_b}. At our scale of {scale}.",
                "Migration cost: {migration_cost}. Risk of staying: {stay_risk}.",
                "What's your recommendation for the technical steering committee?",
            ],
            [
                "Prioritize by {prioritization_framework}: {ranked_items}. Given {feature} dependency on {dependency}, address {critical_debt} first. Allocate {allocation} of sprint to debt.",
                "Comparing: Option A ({option_a}) — pros: {a_pros}, cons: {a_cons}. Option B ({option_b}) — pros: {b_pros}, cons: {b_cons}. Key differentiator: {differentiator}.",
                "At {scale}, benchmarks favor {benchmark_winner} by {margin}. However, consider {considerations}. The performance difference matters {when_matters}.",
                "Migration cost of {migration_cost} amortizes over {amortization_period}. Stay risk of {stay_risk} has probability {probability} of materializing within {risk_timeline}. Expected value: {ev_analysis}.",
                "Recommendation: {recommendation}. Justification: {justification}. Implementation: {implementation_plan}. Revisit criteria: {revisit_criteria}.",
            ],
        ),
    ],
}


SCENARIO_TEMPLATES["industries"] = [
    (
        "troubleshooting",
        [
            "Production line {line_id} throughput dropped {drop_pct}% in the last {timeframe}. OEE now at {oee}%.",
            "Checked {subsystem}: {finding}. Operator reports {operator_obs}.",
            "Vibration analysis on {equipment} shows {vib_pattern}. Temperature: {temp}C above baseline.",
            "Parts from this line failing QC at {reject_rate}% vs normal {normal_rate}%.",
            "What's the repair-vs-replace decision framework here?",
        ],
        [
            "OEE drop to {oee}% indicates losses in {loss_category}. Pareto analysis: check {top_losses}. Start with {first_check} as it accounts for {pct_contribution}% of similar failures.",
            "Finding of {finding} combined with {operator_obs} suggests {root_cause}. Verify with {verification_method}. If confirmed, estimated repair time: {repair_time}.",
            "Vibration pattern {vib_pattern} with {temp}C elevation indicates {bearing_or_alignment} issue. Severity: {severity}. Schedule {maintenance_action} within {urgency_window}.",
            "Reject rate of {reject_rate}% correlates with {correlation}. Implement {containment} immediately. Sort {sort_quantity} units from last {sort_window} hours.",
            "Decision matrix: repair cost {repair_cost} vs replace cost {replace_cost}. MTBF post-repair: {mtbf_repair}. Remaining useful life: {rul}. Recommendation: {decision} based on {rationale}.",
        ],
    ),
    (
        "planning",
        [
            "Annual maintenance shutdown planned for {plant_section}. Window: {window_days} days. Critical path items: {critical_items}.",
            "Contractor availability: {contractor_status}. Parts lead time: {lead_time} weeks for {long_lead_parts}.",
            "Regulatory inspection due within {inspection_window} of restart. Requirements: {reg_requirements}.",
            "How do we compress the schedule if {risk_scenario} occurs?",
            "What's the commissioning and startup sequence?",
        ],
        [
            "Shutdown plan for {plant_section}: {phase_breakdown}. Critical path: {critical_path_duration} days. Float on non-critical: {float_days} days. Pre-shutdown prep: {prep_items}.",
            "For {long_lead_parts} with {lead_time} week lead time: order by {order_deadline}. Contractor {contractor_status} — {contractor_action}. Backup: {contingency}.",
            "Align {reg_requirements} with maintenance scope. Inspection-ready checklist: {checklist_items}. Documentation: {documentation_needs}. Pre-audit {pre_audit_timing}.",
            "Schedule compression options: {compression_options}. Additional cost: {crash_cost}. Risk: {crash_risk}. Minimum feasible window: {min_window} days with {constraints}.",
            "Startup sequence: {startup_steps}. Hold points: {hold_points}. Performance test criteria: {perf_criteria}. Full production ramp: {ramp_timeline}.",
        ],
    ),
    (
        "incident_response",
        [
            "Chemical release alarm triggered in {area}. Sensor reading: {reading} ppm of {chemical}. Wind direction: {wind_dir}.",
            "Evacuation status: {evac_status}. Personnel count: {headcount_status}. Emergency services ETA: {ems_eta}.",
            "{containment_status}. Source identified as {source}. Release rate estimated at {release_rate}.",
            "Regulatory notification deadline: {notification_deadline}. Media inquiries starting.",
            "Release controlled. What's the investigation and remediation plan?",
        ],
        [
            "Activate ERP Level {erp_level}. Immediate actions: {immediate_actions}. Establish exclusion zone of {zone_radius}m downwind. Don {ppe_level} PPE for response team.",
            "Priority: 100% personnel accountability. {headcount_status} — {headcount_action}. Stage at {muster_point}. Brief EMS on {chemical} hazards: {hazard_info}.",
            "Source at {source} with {release_rate}: {isolation_procedure}. Deploy {containment_equipment}. Monitor LEL/oxygen at {monitoring_points}.",
            "Notify {regulatory_bodies} within {notification_deadline}. Statement: {prepared_statement}. Designate {spokesperson} for media. Log all actions in {log_system}.",
            "Investigation: {investigation_method}. Root cause categories to examine: {rca_categories}. Remediation: {remediation_steps}. Timeline to full compliance: {compliance_timeline}.",
        ],
    ),
    (
        "diagnostic_reasoning",
        [
            "Energy consumption on {process} increased {energy_increase}% without corresponding production increase. Utility cost impact: ${cost_impact}/month.",
            "Sub-metering shows {submeter_data}. Process parameters nominal except {anomaly}.",
            "Thermal imaging reveals {thermal_finding}. Insulation inspection: {insulation_status}.",
            "Similar issue occurred {history_timeframe} ago. Resolution was {historical_fix}.",
            "What's the payback period for the recommended fix?",
        ],
        [
            "Energy increase without production gain indicates {efficiency_loss_type}. Check: {check_list}. Benchmark against {benchmark} to quantify loss.",
            "Sub-meter data of {submeter_data} with {anomaly} points to {energy_sink}. This accounts for approximately {pct_explained}% of the excess consumption.",
            "Thermal finding of {thermal_finding} confirms {thermal_diagnosis}. Heat loss rate: approximately {heat_loss_kw} kW. {insulation_status} explains {explanation}.",
            "Historical pattern with {historical_fix} suggests {recurrence_cause}. Permanent fix: {permanent_solution} vs recurring patch. Consider {design_change}.",
            "Capital cost: ${capex}. Annual savings: ${annual_savings}. Simple payback: {payback_months} months. IRR: {irr}%. Recommend {approval_path}.",
        ],
    ),
    (
        "decision_making",
        [
            "Capacity expansion needed: demand forecast shows {demand_gap} unit shortfall by Q{quarter}. Options on table.",
            "Option 1: Add shift ({shift_cost}/yr, {shift_lead} weeks). Option 2: New equipment (${equip_cost}, {equip_lead} weeks). Option 3: Outsource ({outsource_cost}/unit).",
            "Quality risk assessment: {quality_risks}. Customer contractual requirements: {contract_reqs}.",
            "Workforce availability: {workforce_status}. Training time for new operators: {training_weeks} weeks.",
            "Board presentation next week. What's the recommendation with supporting analysis?",
        ],
        [
            "Demand gap of {demand_gap} units requires {capacity_pct}% capacity increase. Timeline constraint eliminates options requiring more than {max_lead} weeks. Evaluate on: cost, quality, speed, flexibility.",
            "NPV comparison: Shift — {shift_npv}. Equipment — {equip_npv}. Outsource — {outsource_npv}. Break-even volume for equipment: {breakeven_vol} units.",
            "Quality risks: {quality_assessment}. {contract_reqs} requires {quality_requirement}. This {eliminates_or_constrains} {affected_option} unless {quality_mitigation}.",
            "Workforce: {workforce_assessment}. {training_weeks} weeks training means earliest full productivity: {productivity_date}. Factor {learning_curve} learning curve into capacity ramp.",
            "Recommendation: {recommendation}. Phase 1: {phase1} (immediate gap coverage). Phase 2: {phase2} (long-term). Present with {financial_metrics} and {risk_matrix}.",
        ],
    ),
]

SCENARIO_TEMPLATES["cybersecurity"] = [
    (
        "incident_response",
        [
            "SIEM alert: {alert_type} from {source_ip} targeting {target}. Severity: {severity}. {ioc_count} IOCs matched.",
            "Threat intel match: {threat_actor} TTP. MITRE ATT&CK: {technique_id} ({technique_name}). Last seen: {last_seen}.",
            "Affected systems: {affected_systems}. Lateral movement indicators: {lateral_indicators}.",
            "Containment options: {containment_options}. Business impact of isolation: {business_impact}.",
            "Eradication complete. What's the recovery and hardening plan?",
        ],
        [
            "Alert triage: {alert_type} from {source_ip} is {classification}. Enrich with {enrichment_sources}. Check {log_sources} for {lookback_period}h lookback. Escalate to {escalation_tier}.",
            "{threat_actor} using {technique_name} ({technique_id}): expected next steps are {kill_chain_next}. Hunt for {hunt_indicators} across {hunt_scope}. Deploy {detection_rule}.",
            "Scope: {affected_systems} confirmed compromised. {lateral_indicators} suggests {lateral_assessment}. Priority: {containment_priority}. Preserve {forensic_evidence} before action.",
            "Recommend {chosen_containment}: {containment_rationale}. Business impact mitigation: {impact_mitigation}. Duration estimate: {containment_duration}. Communicate to {stakeholders}.",
            "Recovery: {recovery_steps}. Hardening: {hardening_measures}. Monitoring: enhanced detection for {monitoring_focus} for {monitoring_duration} days. Lessons learned: {lessons}.",
        ],
    ),
    (
        "diagnostic_reasoning",
        [
            "Unusual authentication pattern detected: {auth_pattern}. Source: {auth_source}. Time: {auth_time} (outside business hours).",
            "User {username} has {access_level} privileges. Last legitimate login: {last_login}. MFA status: {mfa_status}.",
            "Correlated events: {correlated_events}. No password reset ticket in ServiceNow.",
            "EDR shows {edr_finding} on {endpoint}. Memory analysis: {memory_finding}.",
            "Is this a compromised credential, insider threat, or false positive? Confidence level?",
        ],
        [
            "Authentication anomaly: {auth_pattern} from {auth_source} at {auth_time} is {anomaly_score} anomalous. Baseline for this user: {user_baseline}. Check {verification_steps}.",
            "User with {access_level} access and {mfa_status} MFA: {risk_assessment}. Gap since {last_login} is {gap_assessment}. Contact user via {contact_method} for verification.",
            "Correlated events {correlated_events} without password reset ticket {strengthens_or_weakens} compromise hypothesis. Probability: {probability}%. Additional evidence needed: {needed_evidence}.",
            "EDR finding {edr_finding} with memory showing {memory_finding}: this is {edr_assessment}. Indicates {malware_or_tool}. YARA match: {yara_result}.",
            "Assessment: {final_assessment} at {confidence}% confidence. Basis: {evidence_summary}. Immediate action: {immediate_action}. If {alternative_hypothesis}, would expect {expected_evidence}.",
        ],
    ),
    (
        "troubleshooting",
        [
            "Firewall rule change causing {symptom}. Change ticket: {ticket_id}. Implemented {when}.",
            "Before/after diff shows {rule_diff}. Affected traffic: {affected_traffic}.",
            "Application team reports {app_impact}. Business process {process} is {process_status}.",
            "Rollback attempted but {rollback_issue}. Current state: {current_state}.",
            "How do we fix forward without reverting to the insecure previous config?",
        ],
        [
            "Symptom {symptom} correlates with change {ticket_id}. Verify causation: {verification_method}. Check {related_rules} for implicit dependencies.",
            "Rule diff {rule_diff} affecting {affected_traffic}: {impact_analysis}. The change {intended_or_unintended} blocked {blocked_flow}. Original intent was {original_intent}.",
            "{app_impact} on {process} confirms {confirmation}. Workaround: {workaround} while we implement proper fix. SLA impact: {sla_impact}.",
            "Rollback blocked by {rollback_issue}: {explanation}. Alternative: {alternative_approach}. Apply {intermediate_rule} to restore functionality while maintaining {security_posture}.",
            "Fix-forward approach: {fix_forward_plan}. This maintains security intent of {security_goal} while permitting {legitimate_traffic}. Validate with {validation_steps} before closing.",
        ],
    ),
    (
        "planning",
        [
            "Penetration test scheduled for {scope}. Rules of engagement: {roe}. Duration: {duration} days.",
            "Previous findings included {prev_findings}. Remediation status: {remediation_status}.",
            "New attack surface: {new_surface}. Threat model shows {threat_model_findings}.",
            "How should we prioritize testing given limited hours?",
            "What success metrics and reporting format should we use?",
        ],
        [
            "Scope {scope} with {roe}: test plan covers {test_phases}. Team composition: {team_composition}. Communication plan: {comms_plan}. Emergency contacts: {emergency_contacts}.",
            "Re-test {prev_findings} first — {remediation_status} items need validation. Regression coverage: {regression_approach}. Allocate {retest_hours}h for retesting.",
            "New surface {new_surface}: prioritize based on {prioritization_criteria}. Threat model shows {threat_model_findings} — focus {focus_hours}h here. Attack scenarios: {attack_scenarios}.",
            "Priority matrix: {priority_breakdown}. High-value targets: {high_value}. Quick wins: {quick_wins}. Deep-dive: {deep_dive}. Time allocation: {time_allocation}.",
            "Metrics: {metrics}. Report structure: {report_structure}. Findings rated by {rating_system}. Executive summary format: {exec_format}. Remediation timeline: {remediation_timeline}.",
        ],
    ),
    (
        "decision_making",
        [
            "Zero-day advisory: {cve_id} affecting {affected_product}. CVSS: {cvss}. Exploit: {exploit_status}.",
            "Our exposure: {exposure_count} systems, {criticality} criticality. Patch available: {patch_status}.",
            "Compensating controls possible: {compensating_controls}. Downtime for patching: {downtime}.",
            "Risk acceptance request from {business_unit} citing {business_justification}.",
            "What's the CISO recommendation?",
        ],
        [
            "CVE {cve_id} at CVSS {cvss} with {exploit_status} exploit status: risk rating {risk_rating}. Affected: {affected_product} — {exposure_count} systems at {criticality} criticality.",
            "Patch {patch_status}: {patch_action}. If patching not immediate, {interim_measures}. Detection: deploy {detection_signatures} to monitor exploitation attempts.",
            "Compensating controls ({compensating_controls}): {controls_effectiveness}% effective against known exploit paths. Residual risk: {residual_risk}. Acceptable for {acceptable_duration}.",
            "Risk acceptance from {business_unit}: {acceptance_assessment}. {business_justification} {valid_or_insufficient}. Require {acceptance_conditions} if approved. Review in {review_period}.",
            "CISO recommendation: {ciso_recommendation}. Rationale: {rationale}. Timeline: {action_timeline}. Escalation to {escalation_body} if {escalation_trigger}.",
        ],
    ),
]

SCENARIO_TEMPLATES["manufacturing"] = [
    (
        "troubleshooting",
        [
            "CNC machine {machine_id} producing parts out of tolerance. Dimension {dim} reading {actual} vs spec {spec} +/- {tolerance}.",
            "Tool wear monitor shows {wear_pct}% on {tool_type}. Last change: {last_change} cycles ago.",
            "Coolant flow rate dropped to {coolant_flow} L/min. Chip evacuation: {chip_status}.",
            "Tried offset adjustment of {offset}. Next 3 parts measured: {measurements}.",
            "Is this a thermal drift issue or mechanical wear? What confirms it?",
        ],
        [
            "Out-of-tolerance on {dim} by {deviation}: check {check_sequence}. With {wear_pct}% tool wear at {last_change} cycles, tool life may be exceeded. Inspect insert {insert_position}.",
            "At {wear_pct}% wear after {last_change} cycles vs expected life of {expected_life}: {wear_assessment}. Replace {tool_type} and verify with {verification_method}. Update tool life counter.",
            "Coolant at {coolant_flow} L/min is {flow_assessment}. {chip_status} confirms {chip_diagnosis}. Check {coolant_checks}. Thermal stability affected: expect {thermal_impact}.",
            "Offset of {offset} yielding {measurements}: {trend_analysis}. This {confirms_or_denies} progressive drift. {next_action} to isolate thermal vs mechanical.",
            "Confirmation test: {confirmation_method}. If thermal: {thermal_indicators}. If mechanical: {mechanical_indicators}. Based on evidence: {conclusion}. Corrective action: {corrective_action}.",
        ],
    ),
    (
        "diagnostic_reasoning",
        [
            "SPC chart for {characteristic} showing {pattern} pattern. Process capability Cpk dropped from {cpk_before} to {cpk_current}.",
            "Raw material lot changed to {lot_id} from supplier {supplier}. Incoming inspection: {inspection_result}.",
            "Operator {shift} shift reports {operator_report}. Setup sheet reviewed: {setup_status}.",
            "Measurement system analysis: R&R at {rr_pct}%. Is our measurement reliable?",
            "What's the corrective action and how do we update the control plan?",
        ],
        [
            "SPC {pattern} pattern indicates {statistical_cause}. Cpk drop from {cpk_before} to {cpk_current} means {cpk_interpretation}. Investigate {investigation_focus} per control plan reaction.",
            "Lot {lot_id} from {supplier} with {inspection_result}: {material_assessment}. Run {material_test} to compare properties. If confirmed, {material_action}.",
            "{operator_report} on {shift} shift with setup {setup_status}: {human_factor_assessment}. Verify {verification_items}. Consider {training_or_pokayoke}.",
            "R&R at {rr_pct}% is {rr_assessment} (target <10% for critical). {rr_implication}. Before concluding process issue, {measurement_action}. Improve with {gage_improvement}.",
            "Corrective action: {corrective_action}. Control plan updates: add {new_control} at {frequency}. PFMEA update: severity {severity}, occurrence {occurrence}, detection {detection}. New RPN: {rpn}.",
        ],
    ),
    (
        "planning",
        [
            "New product launch: {product}. Production volume: {volume}/month. Required Cpk: {required_cpk}. Timeline: {timeline} weeks to SOP.",
            "Process design: {process_steps} operations. Critical characteristics: {critical_chars}.",
            "Equipment capacity analysis shows {capacity_status}. Tooling lead time: {tooling_lead} weeks.",
            "PPAP submission due {ppap_due}. Customer requires Level {ppap_level}.",
            "What's the launch readiness checklist and risk mitigation?",
        ],
        [
            "Launch timeline of {timeline} weeks for {volume}/month: {feasibility_assessment}. APQP phase gates: {phase_gates}. Critical path: {critical_path_item} at {critical_path_weeks} weeks.",
            "For {critical_chars} at Cpk {required_cpk}: process design must include {process_requirements}. Recommend {process_recommendations}. GR&R study by week {grr_week}.",
            "Capacity {capacity_status}: {capacity_action}. Tooling at {tooling_lead} weeks: order by {order_date}. Backup plan: {backup_plan} if delay occurs.",
            "PPAP Level {ppap_level} by {ppap_due}: deliverables needed: {ppap_deliverables}. Start {start_items} immediately. Run-at-rate: {run_at_rate_plan}.",
            "Launch readiness: {readiness_items}. Risks: {top_risks}. Mitigation: {mitigations}. Go/no-go criteria: {go_nogo}. Safe launch plan: {safe_launch_duration} with {safe_launch_controls}.",
        ],
    ),
    (
        "incident_response",
        [
            "Customer complaint: {complaint_count} field returns for {failure_mode}. Lot: {affected_lot}. Shipped: {shipped_qty} units.",
            "Containment: {contained_qty} units still in pipeline. {in_field_qty} units at customer locations.",
            "8D team assembled. Failure analysis shows {failure_analysis_result}.",
            "Root cause: {root_cause}. Escape point: {escape_point} in the process.",
            "Customer wants corrective action report by {deadline}. What's our response?",
        ],
        [
            "Severity assessment: {failure_mode} is {severity_class}. Immediate containment: sort {shipped_qty} units in pipeline, notify {notify_parties}. Customer communication: {customer_comms}.",
            "Pipeline containment: {contained_qty} units — {containment_method}. For {in_field_qty} in-field units: {field_action}. Tracking: {tracking_method}.",
            "8D D4 (Root Cause): {failure_analysis_result} indicates {cause_category}. Verify with {verification_test}. Contributing factors: {contributing_factors}.",
            "D5/D6: Root cause {root_cause} escaped at {escape_point}. Corrective action: {corrective_action}. Detection improvement: {detection_improvement}. Validation: {validation_plan}.",
            "D7/D8: Report structure: {report_structure}. Prevention: {systemic_prevention}. Lessons learned: {lessons}. Submit by {deadline} with {supporting_docs}.",
        ],
    ),
    (
        "decision_making",
        [
            "Make-vs-buy analysis for {component}. Current internal cost: ${internal_cost}/unit. Quote from {supplier}: ${external_cost}/unit.",
            "Internal capability: {capability_status}. Quality history: {quality_history}.",
            "Volume scenario: {volume_scenarios}. Break-even at {breakeven_vol} units.",
            "Strategic considerations: {strategic_factors}. IP sensitivity: {ip_level}.",
            "What's the recommendation with total cost of ownership?",
        ],
        [
            "Direct cost comparison: internal ${internal_cost} vs external ${external_cost}. Delta: ${delta}/unit. But TCO must include {tco_factors}. Adjusted comparison: {adjusted_comparison}.",
            "Capability {capability_status}: {capability_implication}. Quality {quality_history}: {quality_implication}. Internal investment needed: ${investment} for {capability_gap}.",
            "At {volume_scenarios}: {volume_analysis}. Below {breakeven_vol}: outsource preferred. Above: internal favorable. Forecast confidence: {forecast_confidence}.",
            "Strategic: {strategic_assessment}. IP at {ip_level}: {ip_recommendation}. Core competency alignment: {core_alignment}. Supply chain risk: {supply_risk}.",
            "Recommendation: {recommendation}. TCO over {tco_period} years: internal ${tco_internal} vs external ${tco_external}. Decision: {decision} with {conditions}.",
        ],
    ),
]

SCENARIO_TEMPLATES["supplychain"] = [
    (
        "troubleshooting",
        [
            "Stockout alert: SKU {sku} at DC {dc}. Current inventory: {current_inv} units. Daily demand: {daily_demand}. Replenishment ETA: {eta} days.",
            "Root cause: {stockout_cause}. Supplier {supplier} reports {supplier_status}.",
            "Alternative sources: {alt_sources}. Expedite cost: ${expedite_cost}. Air freight vs ocean: {freight_comparison}.",
            "Customer orders at risk: {orders_at_risk}. Revenue impact: ${revenue_impact}/day.",
            "How do we prevent this class of stockout systematically?",
        ],
        [
            "Critical: {current_inv} units covers {days_coverage} days vs {eta} day ETA. Gap: {gap_days} days. Immediate: {immediate_actions}. Demand shaping: {demand_shaping}.",
            "Cause {stockout_cause} with supplier {supplier_status}: {diagnosis}. This indicates {systemic_issue}. Short-term: {short_term_fix}. Update safety stock calc: {ss_adjustment}.",
            "Alt source analysis: {source_analysis}. Recommend {recommended_source}: {source_rationale}. Total landed cost: ${landed_cost} vs normal ${normal_cost}. Lead time: {alt_lead_time}.",
            "{orders_at_risk} orders representing ${revenue_impact}/day: prioritize by {priority_criteria}. Allocation: {allocation_plan}. Customer communication: {customer_comms}.",
            "Systemic prevention: {prevention_measures}. Monitoring: {kpi_additions}. Policy changes: safety stock = {new_ss_formula}. Supplier diversification: {diversification_plan}.",
        ],
    ),
    (
        "planning",
        [
            "S&OP cycle: {month} demand plan shows {demand_change}% vs prior month. Supply constraint: {constraint}.",
            "Inventory targets: {inv_target} weeks of supply. Current: {current_wos} weeks. Excess in {excess_categories}.",
            "New product introduction {npi_product} launching in {npi_weeks} weeks. Cannibalization estimate: {cannibalization}% of {cannibalized_sku}.",
            "Capacity rough-cut: {capacity_status}. Outsource ceiling: {outsource_capacity}.",
            "What's the consensus plan and what trade-offs do we present to leadership?",
        ],
        [
            "Demand plan {demand_change}% shift: {demand_drivers}. Adjust {supply_response}. Constraint {constraint} limits us to {max_output}. Gap: {gap} units in {gap_period}.",
            "Current {current_wos} vs target {inv_target} weeks: {inv_assessment}. Excess in {excess_categories}: {excess_action}. Working capital impact: ${wc_impact}.",
            "{npi_product} at {npi_weeks} weeks: pipeline build starts {build_start}. Reduce {cannibalized_sku} forecast by {cannibalization}% starting {reduction_start}. Transition plan: {transition}.",
            "Capacity {capacity_status}: {capacity_plan}. Outsource {outsource_capacity} allocated to {outsource_allocation}. Overtime: {overtime_plan}. Hiring: {hiring_plan}.",
            "Consensus plan: {plan_summary}. Trade-offs: {tradeoff_1} vs {tradeoff_2}. Recommendation: {recommendation}. Leadership decision needed on: {decisions_needed}.",
        ],
    ),
    (
        "incident_response",
        [
            "Force majeure: {event} affecting {affected_region}. {supplier_count} suppliers impacted. Estimated disruption: {disruption_weeks} weeks.",
            "Exposed SKUs: {exposed_sku_count}. Revenue at risk: ${revenue_at_risk}M over {risk_period}.",
            "Buffer stock assessment: {buffer_assessment}. Alternative qualification status: {alt_qual_status}.",
            "Customers notified: {notification_status}. Contractual penalties: ${penalty_exposure}.",
            "What's the 30-60-90 day recovery plan?",
        ],
        [
            "Activate supply disruption protocol. Impact: {supplier_count} suppliers, {disruption_weeks} weeks. Crisis team: {crisis_team}. Immediate: {immediate_actions}. Communication: {comms_plan}.",
            "Exposed SKUs: {exposed_sku_count} — categorize by {categorization_method}. Tier 1 (revenue critical): {tier1_action}. Tier 2: {tier2_action}. Tier 3: {tier3_action}.",
            "Buffer covers {buffer_coverage}. Extended runway: {extended_runway} with demand reduction. Alt sources {alt_qual_status}: {qualification_acceleration} to compress timeline.",
            "Customer communication: {customer_strategy}. Penalty mitigation: {penalty_mitigation}. Force majeure clause applicability: {fm_applicability}.",
            "30-day: {thirty_day_plan}. 60-day: {sixty_day_plan}. 90-day: {ninety_day_plan}. KPIs: {recovery_kpis}. Resilience investment: ${resilience_investment} for future mitigation.",
        ],
    ),
    (
        "diagnostic_reasoning",
        [
            "Forecast accuracy degraded: MAPE increased from {mape_before}% to {mape_current}% over {period}. Bias: {bias_direction}.",
            "Top contributors to error: {top_error_skus}. Common attributes: {common_attributes}.",
            "Model inputs checked: {input_status}. External signals: {external_signals}.",
            "Demand sensing data shows {sensing_data}. POS vs warehouse shipments diverging by {divergence}%.",
            "What model adjustments are needed and what's the expected MAPE improvement?",
        ],
        [
            "MAPE degradation from {mape_before}% to {mape_current}% with {bias_direction} bias indicates {bias_cause}. Decompose error: {error_decomposition}. Focus on {focus_area}.",
            "SKUs {top_error_skus} share {common_attributes}: suggests {pattern_cause}. Segment-specific model adjustment: {segment_adjustment}. Impact: {impact_estimate}.",
            "Inputs {input_status}: {input_assessment}. External {external_signals}: {signal_incorporation}. Missing signals: {missing_signals}. Recommendation: {input_recommendation}.",
            "POS-warehouse divergence of {divergence}%: {divergence_cause}. Demand sensing {sensing_data} suggests {true_demand_signal}. Adjust pipeline by {pipeline_adjustment}.",
            "Model adjustments: {adjustments}. Expected MAPE improvement: {expected_mape}% (reduction of {mape_reduction} points). Implementation: {implementation_steps}. Validation: {validation_approach}.",
        ],
    ),
    (
        "decision_making",
        [
            "Distribution network redesign proposed. Current: {current_network}. Proposed: {proposed_network}. Investment: ${investment}M.",
            "Service level impact: {sl_before}% to {sl_after}%. Transit time: {transit_change}.",
            "Operating cost change: ${opex_change}M/year. Lease commitments: {lease_status}.",
            "Risk assessment: {network_risks}. Phasing options: {phasing_options}.",
            "Board needs ROI analysis and go/no-go recommendation.",
        ],
        [
            "Network redesign from {current_network} to {proposed_network}: {strategic_rationale}. Investment ${investment}M justified if {justification_criteria}.",
            "Service level {sl_before}% to {sl_after}%: {sl_assessment}. Customer impact: {customer_impact}. Competitive position: {competitive_assessment}. Transit {transit_change}: {transit_impact}.",
            "Opex savings ${opex_change}M/yr vs capex ${investment}M: payback {payback_years} years. NPV: ${npv}M at {discount_rate}% WACC. Lease {lease_status}: {lease_action}.",
            "Risks: {risk_assessment}. Phasing: recommend {recommended_phasing}. This reduces execution risk by {risk_reduction}. Milestones: {milestones}.",
            "Recommendation: {recommendation}. ROI: {roi}% over {horizon} years. Go criteria: {go_criteria}. No-go triggers: {nogo_triggers}. Board summary: {board_summary}.",
        ],
    ),
]

SCENARIO_TEMPLATES["energy"] = [
    (
        "incident_response",
        [
            "Grid frequency deviation: {freq_value} Hz (nominal 60.00). UFLS stage {ufls_stage} approaching. Generation shortfall: {shortfall_mw} MW.",
            "Tripped unit: {tripped_unit} ({capacity_mw} MW). Cause: {trip_cause}. Reserve margin now: {reserve_pct}%.",
            "Demand response available: {dr_mw} MW in {dr_time} minutes. Interchange capacity: {interchange_mw} MW from {neighbor_ba}.",
            "Frequency stabilized at {stabilized_freq} Hz. Recovery path needed.",
            "Post-event analysis: what failed and what changes are needed?",
        ],
        [
            "Frequency at {freq_value} Hz — {urgency_level} urgency. Deploy {first_response}: spinning reserves, AGC max output. If UFLS stage {ufls_stage} triggers: {ufls_impact}. Notify RC immediately.",
            "Loss of {tripped_unit} ({capacity_mw} MW) from {trip_cause}: {reserve_assessment}. Dispatch {replacement_units}. Ramp rate constraint: {ramp_limit}. Full replacement in {replacement_time} min.",
            "Activate DR: {dr_mw} MW in {dr_time} min covers {coverage_pct}% of shortfall. Request {interchange_mw} MW interchange from {neighbor_ba}. Total recovery: {total_recovery} MW in {total_time} min.",
            "At {stabilized_freq} Hz: {recovery_actions}. Restore reserves within {reserve_restore_time}. Ramp {ramp_sequence}. Cancel UFLS alert when frequency sustained above {safe_freq} Hz for {sustain_time} min.",
            "Failure analysis: {failure_points}. Changes: {required_changes}. NERC reporting: {reporting_requirements}. Reliability improvement: {improvement_plan}.",
        ],
    ),
    (
        "troubleshooting",
        [
            "Solar farm {farm_id} output {actual_pct}% of expected. Irradiance sensor reads {irradiance} W/m2. Weather: {weather}.",
            "Inverter {inverter_id} showing {inverter_alarm}. DC string voltages: {string_voltages}.",
            "Cleaning last performed: {cleaning_date}. Soiling loss estimate: {soiling_pct}%.",
            "Comparison with adjacent farm {adjacent_farm}: producing at {adjacent_pct}% of expected.",
            "Is this degradation, equipment failure, or environmental? What's the financial impact?",
        ],
        [
            "Output at {actual_pct}% of expected with {irradiance} W/m2 irradiance: performance ratio = {pr_value}. Expected PR: {expected_pr}. Deficit explains {deficit_explanation}. Check {check_items}.",
            "Inverter {inverter_id} alarm {inverter_alarm}: {alarm_interpretation}. String voltages {string_voltages}: {voltage_assessment}. {inverter_action}.",
            "Soiling at {soiling_pct}% since {cleaning_date}: {soiling_assessment}. Cost-benefit of cleaning: ${cleaning_cost} vs {generation_recovery} kWh recovery (${revenue_recovery}).",
            "Adjacent farm at {adjacent_pct}%: {comparison_conclusion}. If environmental (shared): {environmental_cause}. If isolated to our farm: {isolated_cause}.",
            "Assessment: {assessment}. Financial impact: ${daily_loss}/day, ${annual_loss}/year. Action plan: {action_plan}. ROI on fix: {fix_roi}. Priority: {priority}.",
        ],
    ),
    (
        "planning",
        [
            "Renewable integration study: adding {new_capacity} MW {generation_type} to {area}. Current penetration: {current_penetration}%.",
            "Interconnection queue position: {queue_position}. Grid studies show {study_results}.",
            "Storage requirements: {storage_need} MWh for {storage_purpose}. Technology options: {storage_options}.",
            "Curtailment risk: {curtailment_estimate}% at full build-out. Mitigation?",
            "What's the optimal phasing and what grid upgrades are prerequisites?",
        ],
        [
            "Adding {new_capacity} MW {generation_type} raises penetration to {new_penetration}%: {integration_assessment}. Key challenges: {challenges}. Required studies: {required_studies}.",
            "Queue position {queue_position}: {timeline_estimate}. Study results showing {study_results}: {study_implications}. Network upgrades identified: {network_upgrades}.",
            "{storage_need} MWh for {storage_purpose}: recommend {recommended_storage}. Comparison: {storage_comparison}. Sizing: {sizing_rationale}. Cost: ${storage_cost}/kWh installed.",
            "Curtailment at {curtailment_estimate}%: revenue impact ${curtailment_cost}M/yr. Mitigation: {curtailment_mitigation}. Residual curtailment after mitigation: {residual_curtailment}%.",
            "Optimal phasing: {phase_plan}. Prerequisites: {prerequisites}. Grid upgrades: {upgrade_details} — cost shared: {cost_sharing}. Timeline: {overall_timeline}.",
        ],
    ),
    (
        "diagnostic_reasoning",
        [
            "Transformer {transformer_id} DGA results: {dga_results}. Previous test ({prev_test_date}): {prev_dga}.",
            "Key gas ratios: {gas_ratios}. Duval triangle indicates: {duval_result}.",
            "Load history: {load_pattern}. Ambient temperature trend: {ambient_trend}.",
            "Age: {transformer_age} years. Last maintenance: {last_maintenance}. Nameplate rating: {rating} MVA.",
            "What's the condition assessment and recommended action timeline?",
        ],
        [
            "DGA showing {dga_results} vs previous {prev_dga}: {trend_assessment}. Rate of change: {rate_of_change}. IEEE C57.104 condition: {ieee_condition}.",
            "Duval triangle result {duval_result}: indicates {fault_type}. Gas ratios {gas_ratios} confirm {confirmation}. Severity: {severity_level}.",
            "Load pattern {load_pattern} with {ambient_trend}: {thermal_assessment}. Hot spot calculation: {hot_spot_temp}C vs limit {limit_temp}C. Loading margin: {margin}%.",
            "At {transformer_age} years with {rating} MVA rating: {age_assessment}. Expected remaining life: {remaining_life} years at current loading. {maintenance_gap_assessment}.",
            "Condition: {overall_condition}. Recommended actions: {actions_timeline}. If deferred: risk is {deferral_risk}. Budget estimate: ${budget}. Replacement planning: {replacement_plan}.",
        ],
    ),
    (
        "decision_making",
        [
            "Peak demand forecast: {peak_forecast} MW for summer {year}. Current capacity: {current_capacity} MW. Planning margin: {planning_margin}%.",
            "Resource options: {resource_options}. Lead times: {lead_times}.",
            "Environmental constraints: {env_constraints}. Community input: {community_input}.",
            "Cost comparison (LCOE): {lcoe_comparison}. Reliability contribution: {reliability_values}.",
            "IRP recommendation needed for commission filing.",
        ],
        [
            "Capacity need: {peak_forecast} MW peak with {planning_margin}% margin requires {required_capacity} MW firm. Gap: {capacity_gap} MW. Need-by date: {need_date}.",
            "Resource evaluation: {resource_evaluation}. Lead time constraint eliminates {eliminated_options}. Viable: {viable_options}. Each scored on: {scoring_criteria}.",
            "Environmental: {env_assessment}. Community {community_input}: {community_impact_on_decision}. Siting constraints: {siting_constraints}. Permitting timeline: {permitting_timeline}.",
            "LCOE: {lcoe_ranking}. Adding reliability value: {reliability_adjusted_ranking}. Portfolio approach: {portfolio_recommendation} captures {portfolio_benefits}.",
            "IRP recommendation: {irp_recommendation}. Portfolio: {portfolio_composition}. Total cost: ${total_cost}B over {planning_horizon} years. Risk-adjusted: {risk_adjusted_cost}. Filing: {filing_details}.",
        ],
    ),
]

SCENARIO_TEMPLATES["defense"] = [
    (
        "planning",
        [
            "Mission planning for {mission_type} in {aor}. Assets available: {assets}. Timeline: H-{h_hour} to execution.",
            "Intelligence update: {intel_update}. Threat assessment: {threat_level}. ROE: {roe}.",
            "Logistics: {logistics_status}. Comms plan: {comms_plan}. Weather window: {weather_window}.",
            "Contingency triggers: {contingency_triggers}. Abort criteria: {abort_criteria}.",
            "Final brief checklist — what are we missing?",
        ],
        [
            "Mission {mission_type} in {aor}: COA development based on {coa_factors}. Timeline analysis: {timeline_analysis}. Asset allocation: {asset_allocation}.",
            "Intel: {intel_assessment}. Threat {threat_level} impacts {threat_impacts}. ROE {roe} constrains {roe_constraints}. Recommend {intel_recommendation}.",
            "Logistics {logistics_status}: {logistics_actions}. Comms: {comms_assessment}. Redundancy: {comms_redundancy}. Weather {weather_window}: {weather_impact}.",
            "Contingencies: {contingency_plans}. Branch plans for {branch_triggers}. Sequel: {sequel_options}. PACE for {pace_element}: {pace_plan}.",
            "Gaps identified: {gaps}. Risk mitigation: {risk_mitigation}. Decision points: {decision_points}. Commander's intent clear on: {intent_elements}.",
        ],
    ),
    (
        "incident_response",
        [
            "SIGINT indicates {threat_indicator} in sector {sector}. Confidence: {confidence_level}. Time-sensitive: {time_constraint}.",
            "Blue force posture: {blue_posture}. Nearest QRF: {qrf_status}. ISR coverage: {isr_status}.",
            "Confirmed: {confirmed_activity}. {civilians_status}. Engagement authority: {engagement_auth}.",
            "Situation developing: {development}. Higher HQ directing: {higher_guidance}.",
            "After-action: outcomes and lessons learned?",
        ],
        [
            "SIGINT {threat_indicator}: {initial_assessment}. At {confidence_level} confidence with {time_constraint}: recommend {immediate_recommendation}. Increase ISR on sector {sector}.",
            "Blue posture {blue_posture}: {posture_adequacy}. QRF {qrf_status}: {qrf_recommendation}. ISR {isr_status}: redirect {isr_redirect} for {isr_purpose}.",
            "Confirmed {confirmed_activity}: engagement decision matrix — {decision_factors}. {civilians_status} requires {civilian_considerations}. Authority: {authority_assessment}.",
            "Development {development}: {adaptation}. Higher guidance {higher_guidance}: {compliance_actions}. Adjust {adjustment_items}. Report {report_requirements}.",
            "Outcomes: {outcomes}. BDA: {bda}. Lessons: {lessons_learned}. Recommendations: {recommendations}. Update TTPs: {ttp_updates}.",
        ],
    ),
    (
        "diagnostic_reasoning",
        [
            "C4ISR system degradation: {system} latency increased {latency_increase}%. Mission impact: {mission_impact}.",
            "Network diagnostics: {network_findings}. SATCOM link: {satcom_status}. Terrestrial backup: {terrestrial_status}.",
            "Cybersecurity scan: {cyber_findings}. Last patch: {patch_status}. Classification: {classification_level}.",
            "Similar degradation observed at {other_location}. Coincidence or coordinated?",
            "Recommendation for maintaining C4ISR continuity?",
        ],
        [
            "System {system} degradation at {latency_increase}%: {impact_classification}. Immediate: switch to {backup_mode}. Diagnose: {diagnostic_sequence}.",
            "Network {network_findings}: {network_assessment}. SATCOM {satcom_status}: {satcom_action}. Terrestrial {terrestrial_status}: {terrestrial_viability}.",
            "Cyber {cyber_findings} at {classification_level}: {cyber_assessment}. Patch status {patch_status}: {patch_concern}. Conduct {cyber_investigation}.",
            "Correlation with {other_location}: {correlation_assessment}. If coordinated: {coordinated_response}. If coincidental: {coincidental_explanation}. Determine via {determination_method}.",
            "Continuity plan: {continuity_measures}. Degraded mode operations: {degraded_ops}. Restoration priority: {restoration_priority}. Report to {report_chain}.",
        ],
    ),
    (
        "decision_making",
        [
            "Force protection level change consideration. Current: {current_fpcon}. Indicators: {threat_indicators}.",
            "Impact of raising to {proposed_fpcon}: {operational_impact}. Duration estimate: {duration}.",
            "Intelligence gaps: {intel_gaps}. Verification timeline: {verification_timeline}.",
            "Commander's priorities: {commander_priorities}. Upcoming operations: {upcoming_ops}.",
            "Recommendation with risk assessment?",
        ],
        [
            "Indicators {threat_indicators} against criteria for {proposed_fpcon}: {criteria_assessment}. Current {current_fpcon} is {adequacy_assessment}.",
            "Raising to {proposed_fpcon}: {impact_analysis}. Operational tempo reduced by {tempo_reduction}%. Mitigation: {impact_mitigation}.",
            "Intel gaps {intel_gaps}: fill via {collection_plan}. Timeline {verification_timeline}: {interim_recommendation}. Decision point: {decision_point}.",
            "Balancing {commander_priorities} with threat: {balance_assessment}. {upcoming_ops} can proceed under {proposed_fpcon} with {modifications}.",
            "Recommendation: {fpcon_recommendation}. Risk: {risk_level} ({risk_rationale}). Selective measures: {selective_measures}. Review: {review_schedule}.",
        ],
    ),
    (
        "troubleshooting",
        [
            "UAV {uav_id} lost link at {lost_link_time}. Last position: {last_position}. Mission: {mission_status}.",
            "Link diagnostics: {link_diagnostics}. Weather at relay: {relay_weather}. Terrain masking: {terrain_assessment}.",
            "Autonomous mode: {autonomous_status}. Fuel state: {fuel_state}. Preprogrammed actions: {preprogrammed}.",
            "Recovery options: {recovery_options}. Airspace deconfliction: {airspace_status}.",
            "Decision: wait for link restoration or execute recovery?",
        ],
        [
            "Lost link on {uav_id}: execute lost-link checklist. {autonomous_status} means {autonomous_assessment}. Expected behavior: {expected_behavior}. Time to critical fuel: {time_to_bingo}.",
            "Link loss from {link_diagnostics}: {diagnosis}. Relay weather {relay_weather}: {weather_factor}. Terrain {terrain_assessment}: {terrain_action}.",
            "Fuel {fuel_state} with {preprogrammed} programmed: {fuel_assessment}. Window for recovery: {recovery_window}. If no link by {link_deadline}: {automatic_action}.",
            "Recovery: {recovery_plan}. Airspace {airspace_status}: {deconfliction_actions}. Coordinate with {coordinate_with}. Recovery site: {recovery_site}.",
            "Decision: {recommendation}. Rationale: {rationale}. If wait: timeline {wait_timeline}. If recover now: {recovery_procedure}. Risk: {decision_risk}.",
        ],
    ),
]

SCENARIO_TEMPLATES["education"] = [
    (
        "diagnostic_reasoning",
        [
            "Student performance data: cohort {cohort_id} showing {performance_pattern}. Avg score dropped from {score_before} to {score_after} on {assessment_type}.",
            "Disaggregated data: {subgroup_data}. Attendance: {attendance_pattern}. Engagement metrics: {engagement_data}.",
            "Curriculum pacing: {pacing_status}. Prerequisite mastery: {prereq_status}.",
            "Teacher survey: {teacher_feedback}. Student survey: {student_feedback}.",
            "What interventions do we implement and how do we measure effectiveness?",
        ],
        [
            "Score decline from {score_before} to {score_after}: {decline_magnitude} effect size. Pattern {performance_pattern} suggests {pattern_interpretation}. Investigate: {investigation_items}.",
            "Subgroup analysis: {subgroup_analysis}. Attendance {attendance_pattern}: {attendance_impact}. Engagement {engagement_data}: {engagement_interpretation}.",
            "Pacing {pacing_status}: {pacing_recommendation}. Prerequisite mastery {prereq_status}: {prereq_action}. Scaffold: {scaffolding_plan}.",
            "Teacher reporting {teacher_feedback}: {teacher_interpretation}. Students reporting {student_feedback}: {student_interpretation}. Alignment: {alignment_assessment}.",
            "Interventions: {intervention_plan}. Tier {tier_level} supports for {targeted_students}. Measurement: {measurement_plan}. Timeline: {timeline}. Success criteria: {success_criteria}.",
        ],
    ),
    (
        "planning",
        [
            "New program design: {program_type} for {target_population}. Learning objectives: {objectives}. Modality: {modality}.",
            "Baseline assessment data: {baseline_data}. Learner personas: {personas}.",
            "Technology infrastructure: {tech_status}. Budget: ${budget}. Timeline: {timeline} for pilot.",
            "Accreditation requirements: {accreditation_reqs}. Assessment framework needed.",
            "What's the curriculum architecture and assessment blueprint?",
        ],
        [
            "Program design for {target_population}: backward design from {objectives}. Framework: {design_framework}. Modality {modality}: {modality_rationale}.",
            "Baseline {baseline_data}: {baseline_implications}. Personas {personas}: differentiation via {differentiation_strategy}. Entry requirements: {entry_requirements}.",
            "Tech {tech_status}: {tech_plan}. Budget ${budget}: allocation — {budget_allocation}. Pilot {timeline}: {pilot_plan}.",
            "Accreditation {accreditation_reqs}: {alignment_plan}. Assessment types: {assessment_types}. Evidence: {evidence_requirements}. Portfolio: {portfolio_requirements}.",
            "Architecture: {curriculum_architecture}. Modules: {module_structure}. Assessment blueprint: {assessment_blueprint}. Progression: {progression_model}. QA: {qa_process}.",
        ],
    ),
    (
        "troubleshooting",
        [
            "LMS {lms_name} showing {lms_issue} since {issue_start}. Affected users: {affected_count}. Support tickets: {ticket_count}.",
            "Error logs: {error_pattern}. Last system update: {last_update}. Integration status: {integration_status}.",
            "Workaround attempted: {workaround}. Result: {workaround_result}.",
            "Upcoming deadline: {deadline_event} in {days_until} days. {students_affected} students impacted.",
            "Resolution plan with rollback option?",
        ],
        [
            "LMS {lms_issue} affecting {affected_count} users: severity {severity}. Immediate: {immediate_action}. Communication: {user_communication}.",
            "Error {error_pattern} post {last_update}: {diagnosis}. Integration {integration_status}: {integration_assessment}. Root cause: {root_cause}.",
            "Workaround {workaround} yielding {workaround_result}: {workaround_assessment}. Alternative: {alternative_workaround}. Instructor guidance: {instructor_guidance}.",
            "Deadline {deadline_event} in {days_until} days: {deadline_plan}. Extension policy: {extension_policy}. {students_affected} students: {student_accommodation}.",
            "Resolution: {resolution_steps}. ETA: {resolution_eta}. Rollback: {rollback_plan}. Testing: {test_plan}. Post-resolution: {post_resolution_verification}.",
        ],
    ),
    (
        "incident_response",
        [
            "Academic integrity violation detected: {violation_type} involving {student_count} students in {course}. Evidence: {evidence}.",
            "Investigation reveals {investigation_finding}. {tool_or_method} used. Scope possibly wider: {scope_indicators}.",
            "Policy states: {policy_relevant_sections}. Precedent: {precedent_cases}.",
            "Students claiming: {student_defense}. Faculty recommendation: {faculty_recommendation}.",
            "What's the fair resolution balancing accountability and educational mission?",
        ],
        [
            "Violation {violation_type}: gather {evidence_needed}. Preserve: {preservation_steps}. Due process: notify students per {notification_policy}. Timeline: {process_timeline}.",
            "Finding {investigation_finding}: {finding_assessment}. Scope indicators {scope_indicators}: {scope_action}. Recommend {additional_investigation}.",
            "Policy application: {policy_interpretation}. Precedent {precedent_cases}: {precedent_guidance}. Proportionality: {proportionality_assessment}.",
            "Student defense {student_defense}: {defense_assessment}. Faculty {faculty_recommendation}: {faculty_assessment}. Mitigating factors: {mitigating_factors}.",
            "Resolution: {resolution}. Sanctions: {sanctions}. Educational component: {educational_requirement}. Prevention: {prevention_measures}. Appeal rights: {appeal_process}.",
        ],
    ),
    (
        "decision_making",
        [
            "Program review: {program_name} enrollment {enrollment_trend} over {period}. Graduation rate: {grad_rate}%. Employment rate: {employment_rate}%.",
            "Market analysis: {market_data}. Competitor programs: {competitor_landscape}.",
            "Faculty capacity: {faculty_status}. Facility needs: {facility_needs}.",
            "Student feedback: {student_satisfaction}. Alumni survey: {alumni_data}.",
            "Continue, restructure, or sunset? Recommendation needed for academic council.",
        ],
        [
            "Program health: enrollment {enrollment_trend}, graduation {grad_rate}%, employment {employment_rate}%. Viability index: {viability_score}. Benchmark: {benchmark_comparison}.",
            "Market {market_data}: {market_assessment}. Demand trajectory: {demand_trajectory}. Competitors: {competitive_position}. Differentiation opportunity: {differentiation}.",
            "Resources: faculty {faculty_status} — {faculty_sustainability}. Facilities {facility_needs}: {facility_investment}. Cross-subsidization: {cross_subsidy_status}.",
            "Satisfaction {student_satisfaction}: {satisfaction_interpretation}. Alumni {alumni_data}: {alumni_insights}. Net promoter: {nps}.",
            "Recommendation: {recommendation}. Rationale: {rationale}. If restructure: {restructure_plan}. If sunset: {sunset_plan}. Timeline: {decision_timeline}. Impact: {stakeholder_impact}.",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def generate_multi_turn(world: str, rng: Any, tick: int, difficulty: str = "medium") -> dict:
    """Generate a multi-turn conversation for the given world.

    Args:
        world: Domain name (healthcare, finance, coding, etc.)
        rng: random.Random instance for deterministic generation
        tick: Sequence number for record ID generation
        difficulty: 'easy' (3-4 turns), 'medium' (5-6 turns), 'hard' (7-10 turns)

    Returns:
        Dict with format, record_id, metadata, system_prompt, conversation
    """
    # Determine turn count based on difficulty
    if difficulty == "easy":
        num_turns = rng.randint(3, 4)
    elif difficulty == "hard":
        num_turns = rng.randint(7, 10)
    else:
        num_turns = rng.randint(5, 6)

    # Get system prompt (fallback to industries if world not found)
    system_prompt = WORLD_SYSTEM_PROMPTS.get(world, WORLD_SYSTEM_PROMPTS.get("industries", "You are a helpful domain expert."))

    # Get scenario templates for this world
    scenarios = SCENARIO_TEMPLATES.get(world, SCENARIO_TEMPLATES.get("industries", []))
    if not scenarios:
        scenarios = SCENARIO_TEMPLATES.get("healthcare", [])

    # Pick a random scenario
    scenario = rng.choice(scenarios)
    scenario_type = scenario[0]
    user_templates = scenario[1]
    assistant_templates = scenario[2]

    # Build conversation
    conversation = []
    max_pairs = min(len(user_templates), len(assistant_templates))
    turns_to_generate = min(num_turns, max_pairs * 2)

    for i in range(min(max_pairs, (turns_to_generate + 1) // 2)):
        # User turn
        user_msg = user_templates[i] if i < len(user_templates) else f"Please continue with the analysis for {world}."
        conversation.append({"role": "user", "content": user_msg})

        # Assistant turn
        if i < len(assistant_templates):
            assistant_msg = assistant_templates[i]
            # Add thinking block for hard difficulty
            if difficulty == "hard" and i > 0:
                think_content = f"Let me analyze this step carefully considering the {world} context and prior information provided."
                assistant_msg = f"<think>{think_content}</think>\n{assistant_msg}"
            conversation.append({"role": "assistant", "content": assistant_msg})

    # Ensure we have at least the requested turns
    actual_turns = len(conversation)

    return {
        "format": "multi_turn",
        "record_id": f"mt_{tick:06d}_{world}_{rng.randint(0, 99999):05d}",
        "metadata": {
            "world": world,
            "turns": actual_turns,
            "difficulty": difficulty,
            "scenario_type": scenario_type,
        },
        "system_prompt": system_prompt,
        "conversation": conversation,
    }
