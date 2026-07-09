"""
Chain-of-thought reasoning trace generator for Hybrid-HybridAI.

Generates structured chain-of-thought (CoT) reasoning records across 10+ worlds
(domains). Each record includes a problem statement, step-by-step reasoning with
monotonically increasing confidence scores, a final answer, and verifiable
ground-truth metadata.

Usage:
    import random
    rng = random.Random(42)
    record = generate_cot(world='finance', rng=rng, tick=1, difficulty='hard')

The generator is fully deterministic: given the same RNG state, it produces
identical output. Pure Python with no external dependencies.
"""

from typing import Any, Callable, Dict, List, Tuple


# Type alias for problem generator functions
# Each takes (rng, difficulty) and returns (problem_text, reasoning_steps, answer, ground_truth)
ProblemGenerator = Callable[[Any, str], Tuple[str, List[str], str, Dict[str, Any]]]

# Difficulty -> number of reasoning steps range
DIFFICULTY_STEPS = {
    "easy": (2, 3),
    "medium": (4, 5),
    "hard": (6, 8),
}


def _generate_confidence_scores(rng: Any, num_steps: int) -> List[float]:
    """
    Generate monotonically increasing confidence scores for reasoning steps.

    Args:
        rng: Random number generator instance.
        num_steps: Number of reasoning steps.

    Returns:
        List of floats in [0.2, 0.95], monotonically non-decreasing.
    """
    start = rng.uniform(0.2, 0.4)
    end = rng.uniform(0.85, 0.95)
    if num_steps == 1:
        return [round(end, 2)]
    # Generate sorted intermediate values
    raw = sorted([rng.uniform(start, end) for _ in range(num_steps)])
    # Ensure strict monotonic increase by nudging
    for i in range(1, len(raw)):
        if raw[i] <= raw[i - 1]:
            raw[i] = raw[i - 1] + 0.01
    # Clamp and round
    result = [round(min(max(v, 0.1), 0.99), 2) for v in raw]
    # Final enforcement of monotonicity after rounding
    for i in range(1, len(result)):
        if result[i] <= result[i - 1]:
            result[i] = round(result[i - 1] + 0.01, 2)
    return result


def _pick_num_steps(rng: Any, difficulty: str) -> int:
    """Pick the number of reasoning steps based on difficulty."""
    lo, hi = DIFFICULTY_STEPS.get(difficulty, (4, 5))
    return rng.randint(lo, hi)



# =============================================================================
# HEALTHCARE WORLD TEMPLATES
# =============================================================================

def _healthcare_dosage_calc(rng, difficulty):
    """Drug dosage calculation based on patient weight and renal function."""
    weight = rng.randint(45, 120)
    gfr = rng.randint(15, 120)
    base_dose_per_kg = rng.choice([5, 10, 15, 20])
    drug = rng.choice(["vancomycin", "gentamicin", "amikacin", "tobramycin", "ciprofloxacin"])
    full_dose = weight * base_dose_per_kg
    if gfr < 30:
        adjusted = round(full_dose * 0.5)
        adjustment = "50% reduction"
    elif gfr < 60:
        adjusted = round(full_dose * 0.75)
        adjustment = "25% reduction"
    else:
        adjusted = full_dose
        adjustment = "no adjustment"

    problem = (f"A {weight}kg patient with GFR {gfr} mL/min requires {drug}. "
               f"Standard dosing is {base_dose_per_kg}mg/kg. Calculate the appropriate dose.")

    steps = [
        f"Calculate base dose: {weight}kg x {base_dose_per_kg}mg/kg = {full_dose}mg",
        f"Assess renal function: GFR {gfr} mL/min indicates {'impaired' if gfr < 60 else 'normal'} clearance",
        f"Apply renal adjustment: {adjustment} needed for GFR {gfr}",
        f"Verify against therapeutic range for {drug}",
        f"Final adjusted dose: {adjusted}mg",
        f"Consider monitoring trough levels given renal status",
        f"Confirm no contraindications at this dose level",
        f"Recommend dosing interval adjustment if GFR < 30",
    ]
    answer = f"Administer {adjusted}mg of {drug} ({adjustment} due to GFR {gfr})."
    ground_truth = {"correct": True, "key_insight": "renal_dose_adjustment",
                    "computed_dose": adjusted, "adjustment_factor": adjustment}
    return problem, steps, answer, ground_truth


def _healthcare_triage(rng, difficulty):
    """Emergency triage priority assessment."""
    hr = rng.randint(40, 180)
    bp_sys = rng.randint(70, 200)
    spo2 = rng.randint(80, 100)
    temp = round(rng.uniform(35.0, 41.0), 1)
    gcs = rng.randint(3, 15)
    age = rng.randint(18, 90)

    critical = (hr > 150 or hr < 50 or bp_sys < 90 or spo2 < 90 or gcs < 9 or temp > 40.0)
    urgent = (hr > 120 or bp_sys < 100 or spo2 < 94 or gcs < 13 or temp > 39.0)
    priority = "immediate" if critical else ("urgent" if urgent else "delayed")

    problem = (f"Patient age {age}: HR {hr}bpm, BP {bp_sys}/?, SpO2 {spo2}%, "
               f"Temp {temp}°C, GCS {gcs}. Determine triage priority.")
    steps = [
        f"Assess airway/breathing: SpO2 {spo2}% {'critically low' if spo2 < 90 else 'acceptable' if spo2 >= 94 else 'concerning'}",
        f"Evaluate circulation: HR {hr}, systolic BP {bp_sys}mmHg",
        f"Neurological status: GCS {gcs}/15 {'severe impairment' if gcs < 9 else 'mild deficit' if gcs < 13 else 'intact'}",
        f"Temperature assessment: {temp}°C {'hyperpyrexia' if temp > 40 else 'febrile' if temp > 38.5 else 'normal range'}",
        f"Apply triage algorithm: {'meets critical criteria' if critical else 'meets urgent criteria' if urgent else 'stable vitals'}",
        f"Consider age {age} as compounding factor",
        f"Final triage classification: {priority}",
        f"Reassess in {'5 min' if priority == 'immediate' else '15 min' if priority == 'urgent' else '60 min'}",
    ]
    answer = f"Triage priority: {priority}. Key drivers: {'SpO2/GCS critical' if critical else 'elevated HR/temp' if urgent else 'vitals within acceptable range'}."
    ground_truth = {"correct": True, "key_insight": f"triage_{priority}", "priority": priority}
    return problem, steps, answer, ground_truth


def _healthcare_lab_interpretation(rng, difficulty):
    """Interpret a panel of lab results for differential diagnosis."""
    wbc = round(rng.uniform(2.0, 25.0), 1)
    hgb = round(rng.uniform(6.0, 18.0), 1)
    plt = rng.randint(50, 500)
    crp = round(rng.uniform(0.1, 200.0), 1)
    lactate = round(rng.uniform(0.5, 8.0), 1)

    sepsis = (wbc > 12 or wbc < 4) and crp > 50 and lactate > 2.0
    anemia = hgb < 10
    diagnosis = "sepsis" if sepsis else ("anemia_workup" if anemia else "monitor")

    problem = (f"Lab panel: WBC {wbc}x10^9/L, Hgb {hgb}g/dL, Plt {plt}x10^9/L, "
               f"CRP {crp}mg/L, Lactate {lactate}mmol/L. Interpret findings.")
    steps = [
        f"WBC {wbc}: {'leukocytosis' if wbc > 12 else 'leukopenia' if wbc < 4 else 'normal'}",
        f"Hemoglobin {hgb}: {'anemia' if hgb < 10 else 'normal'}",
        f"CRP {crp}: {'markedly elevated suggesting systemic inflammation' if crp > 50 else 'mildly elevated' if crp > 10 else 'normal'}",
        f"Lactate {lactate}: {'elevated indicating tissue hypoperfusion' if lactate > 2 else 'normal'}",
        f"Pattern recognition: {'meets SIRS + organ dysfunction criteria' if sepsis else 'isolated finding'}",
        f"Differential includes: {'sepsis/severe infection' if sepsis else 'iron deficiency vs chronic disease' if anemia else 'non-specific'}",
        f"Recommended action: {'blood cultures + empiric antibiotics' if sepsis else 'iron studies' if anemia else 'repeat in 24h'}",
        f"Platelet count {plt} {'thrombocytopenia' if plt < 100 else 'normal'} as secondary finding",
    ]
    answer = f"Primary assessment: {diagnosis}. {'Initiate sepsis bundle immediately.' if sepsis else 'Further workup indicated.' if anemia else 'Continue monitoring.'}"
    ground_truth = {"correct": True, "key_insight": diagnosis, "sepsis_criteria_met": sepsis}
    return problem, steps, answer, ground_truth


def _healthcare_drug_interaction(rng, difficulty):
    """Assess drug-drug interaction severity."""
    pairs = [
        ("warfarin", "aspirin", "bleeding_risk", "major"),
        ("metformin", "contrast_dye", "lactic_acidosis", "major"),
        ("ssri", "tramadol", "serotonin_syndrome", "major"),
        ("ace_inhibitor", "potassium_supplement", "hyperkalemia", "moderate"),
        ("statin", "grapefruit", "myopathy", "moderate"),
        ("methotrexate", "nsaid", "nephrotoxicity", "major"),
        ("lithium", "thiazide", "lithium_toxicity", "major"),
        ("digoxin", "amiodarone", "digoxin_toxicity", "major"),
    ]
    drug_a, drug_b, risk, severity = rng.choice(pairs)
    patient_age = rng.randint(30, 85)
    renal_impaired = rng.choice([True, False])

    problem = (f"Patient age {patient_age}{' with renal impairment' if renal_impaired else ''} "
               f"is prescribed {drug_a} and {drug_b}. Assess interaction risk.")
    steps = [
        f"Identify interaction: {drug_a} + {drug_b} = risk of {risk}",
        f"Severity classification: {severity}",
        f"Patient factors: age {patient_age}, {'impaired renal clearance amplifies risk' if renal_impaired else 'normal clearance'}",
        f"Mechanism: altered {'metabolism' if severity == 'moderate' else 'pharmacodynamics'}",
        f"Clinical significance: {'contraindicated combination' if severity == 'major' and renal_impaired else 'use with monitoring'}",
        f"Alternative options available: consider therapeutic substitution",
        f"Monitoring plan: {'weekly labs' if severity == 'major' else 'routine monitoring'}",
        f"Risk-benefit assessment for this patient profile",
    ]
    contraindicated = severity == "major" and renal_impaired
    answer = (f"{'Contraindicated' if contraindicated else 'Use with caution'}: "
              f"{drug_a} + {drug_b} poses {risk} risk ({severity} severity).")
    ground_truth = {"correct": True, "key_insight": risk, "severity": severity,
                    "contraindicated": contraindicated}
    return problem, steps, answer, ground_truth


def _healthcare_ventilator(rng, difficulty):
    """Ventilator setting optimization for ARDS patient."""
    pao2 = rng.randint(50, 120)
    fio2 = rng.choice([0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    peep = rng.randint(5, 20)
    plateau = rng.randint(20, 40)
    tidal_vol = rng.randint(300, 600)
    weight_ibw = rng.randint(50, 80)
    vt_per_kg = round(tidal_vol / weight_ibw, 1)

    pf_ratio = round(pao2 / fio2)
    ards_severity = "severe" if pf_ratio < 100 else ("moderate" if pf_ratio < 200 else "mild" if pf_ratio < 300 else "none")
    lung_protective = vt_per_kg <= 6.0 and plateau <= 30

    problem = (f"ARDS patient: PaO2 {pao2}mmHg, FiO2 {fio2}, PEEP {peep}cmH2O, "
               f"Plateau {plateau}cmH2O, TV {tidal_vol}mL (IBW {weight_ibw}kg). "
               f"Optimize ventilator settings.")
    steps = [
        f"Calculate P/F ratio: {pao2}/{fio2} = {pf_ratio} → {ards_severity} ARDS",
        f"Assess tidal volume: {tidal_vol}mL / {weight_ibw}kg = {vt_per_kg} mL/kg IBW",
        f"Lung-protective threshold: Vt ≤ 6mL/kg IBW → {'met' if vt_per_kg <= 6 else f'exceeded, reduce to {weight_ibw * 6}mL'}",
        f"Plateau pressure {plateau}cmH2O {'exceeds' if plateau > 30 else 'within'} safe limit of 30",
        f"PEEP optimization: current {peep}, {'adequate' if pf_ratio > 150 else 'consider increasing'}",
        f"Prone positioning {'indicated' if pf_ratio < 150 else 'not yet indicated'} at P/F {pf_ratio}",
        f"Overall lung-protective ventilation: {'achieved' if lung_protective else 'requires adjustment'}",
        f"Consider neuromuscular blockade if P/F < 150 with high driving pressure",
    ]
    target_vt = min(tidal_vol, weight_ibw * 6)
    answer = (f"{'Settings acceptable' if lung_protective else 'Adjust settings'}: "
              f"Target Vt {target_vt}mL ({round(target_vt/weight_ibw, 1)} mL/kg), "
              f"{'increase PEEP' if pf_ratio < 150 else 'maintain PEEP'}, "
              f"{'prone positioning indicated' if pf_ratio < 150 else 'continue supine'}.")
    ground_truth = {"correct": True, "key_insight": "lung_protective_ventilation",
                    "pf_ratio": pf_ratio, "ards_severity": ards_severity,
                    "lung_protective": lung_protective}
    return problem, steps, answer, ground_truth


def _healthcare_ecg_interpretation(rng, difficulty):
    """ECG rhythm interpretation and clinical decision."""
    rhythms = [
        ("sinus_tachycardia", 110, True, "regular", "evaluate_cause"),
        ("atrial_fibrillation", 130, False, "irregularly_irregular", "rate_control"),
        ("ventricular_tachycardia", 180, True, "regular_wide_qrs", "immediate_cardioversion"),
        ("third_degree_block", 35, False, "dissociated", "pacing"),
        ("svt", 160, True, "regular_narrow", "vagal_then_adenosine"),
    ]
    rhythm_name, base_rate, p_waves, pattern, action = rng.choice(rhythms)
    rate = base_rate + rng.randint(-10, 10)
    bp = rng.randint(70, 140)
    symptomatic = bp < 90 or rate > 150

    problem = (f"ECG shows: rate {rate}bpm, {pattern} rhythm, "
               f"{'visible' if p_waves else 'absent'} P-waves. BP {bp}mmHg. "
               f"Patient {'symptomatic' if symptomatic else 'stable'}. Interpret and manage.")
    steps = [
        f"Rate assessment: {rate}bpm ({'tachy' if rate > 100 else 'brady' if rate < 60 else 'normal'}cardiac)",
        f"Rhythm regularity: {pattern}",
        f"P-wave morphology: {'present and uniform' if p_waves else 'absent/chaotic'}",
        f"QRS width assessment for differentiation",
        f"Pattern recognition: consistent with {rhythm_name.replace('_', ' ')}",
        f"Hemodynamic status: BP {bp} → {'unstable' if symptomatic else 'stable'}",
        f"Management algorithm: {action.replace('_', ' ')}",
        f"{'Immediate intervention required' if symptomatic else 'Pharmacologic approach appropriate'}",
    ]
    answer = (f"Diagnosis: {rhythm_name.replace('_', ' ')}. "
              f"Management: {action.replace('_', ' ')}. "
              f"{'URGENT - hemodynamically unstable.' if symptomatic else 'Patient stable, proceed with standard protocol.'}")
    ground_truth = {"correct": True, "key_insight": rhythm_name,
                    "action": action, "hemodynamic_stability": not symptomatic}
    return problem, steps, answer, ground_truth



# =============================================================================
# FINANCE WORLD TEMPLATES
# =============================================================================

def _finance_portfolio_risk(rng, difficulty):
    """Portfolio risk assessment with Sharpe ratio and drawdown analysis."""
    annual_return = round(rng.uniform(4.0, 25.0), 1)
    sharpe = round(rng.uniform(0.3, 2.5), 2)
    max_drawdown = round(rng.uniform(5.0, 35.0), 1)
    risk_mandate = rng.choice([15, 20, 25])
    concentration = round(rng.uniform(10, 60), 1)

    exceeds_mandate = max_drawdown > risk_mandate
    problem = (f"A portfolio shows {annual_return}% annual return with Sharpe ratio {sharpe}. "
               f"Maximum drawdown is {max_drawdown}%, concentration in top-5 holdings is {concentration}%. "
               f"Fund risk mandate limits drawdown to {risk_mandate}%.")
    steps = [
        f"Assess risk-adjusted return: Sharpe {sharpe} {'excellent' if sharpe > 1.5 else 'acceptable' if sharpe > 0.8 else 'subpar'}",
        f"Compare drawdown {max_drawdown}% against mandate {risk_mandate}%",
        f"Concentration risk: {concentration}% in top-5 {'excessive' if concentration > 40 else 'acceptable'}",
        f"{'Drawdown exceeds mandate by {:.1f}%'.format(max_drawdown - risk_mandate) if exceeds_mandate else 'Drawdown within mandate'}",
        f"Risk-return tradeoff: {annual_return}% return {'does not justify' if exceeds_mandate else 'justifies'} the risk exposure",
        f"Recommend {'rebalancing' if exceeds_mandate or concentration > 40 else 'maintaining'} current allocation",
        f"Tail risk assessment: VaR implications of {max_drawdown}% historical drawdown",
        f"Factor exposure analysis for concentration risk mitigation",
    ]
    rebalance = exceeds_mandate or concentration > 40
    answer = (f"{'Rebalance to reduce risk' if rebalance else 'Maintain current allocation'}. "
              f"{'Drawdown exceeds mandate.' if exceeds_mandate else ''} "
              f"{'Concentration risk elevated.' if concentration > 40 else ''}")
    ground_truth = {"correct": True, "key_insight": "drawdown_exceeds_mandate" if exceeds_mandate else "within_mandate",
                    "rebalance_needed": rebalance}
    return problem, steps, answer, ground_truth


def _finance_loan_default(rng, difficulty):
    """Loan default probability assessment."""
    dti = round(rng.uniform(15, 65), 1)
    credit_score = rng.randint(300, 850)
    employment_years = rng.randint(0, 30)
    loan_amount = rng.randint(5000, 500000)
    collateral_ratio = round(rng.uniform(0.5, 2.0), 2)

    high_risk = dti > 43 or credit_score < 580
    medium_risk = dti > 36 or credit_score < 670
    risk_level = "high" if high_risk else ("medium" if medium_risk else "low")

    problem = (f"Loan application: DTI {dti}%, credit score {credit_score}, "
               f"employment {employment_years} years, amount ${loan_amount:,}, "
               f"collateral ratio {collateral_ratio}x.")
    steps = [
        f"DTI ratio {dti}%: {'exceeds 43% threshold' if dti > 43 else 'within guidelines'}",
        f"Credit score {credit_score}: {'subprime' if credit_score < 580 else 'near-prime' if credit_score < 670 else 'prime'}",
        f"Employment stability: {employment_years} years {'strong' if employment_years > 5 else 'limited'} history",
        f"Loan-to-collateral: {collateral_ratio}x {'under-collateralized' if collateral_ratio < 1.0 else 'adequately secured'}",
        f"Combined risk assessment: {risk_level} probability of default",
        f"Expected loss calculation given collateral coverage",
        f"Decision: {'deny' if high_risk and collateral_ratio < 1.0 else 'approve with conditions' if medium_risk else 'approve'}",
        f"Pricing adjustment: +{max(0, int((750 - credit_score) * 0.01 * 100))}bps risk premium",
    ]
    approve = not (high_risk and collateral_ratio < 1.0)
    answer = (f"{'Approve' if approve else 'Deny'} loan. Risk level: {risk_level}. "
              f"{'Require additional collateral.' if collateral_ratio < 1.0 and approve else ''}")
    ground_truth = {"correct": True, "key_insight": f"risk_{risk_level}",
                    "approve": approve, "risk_level": risk_level}
    return problem, steps, answer, ground_truth


def _finance_valuation_dcf(rng, difficulty):
    """Discounted cash flow valuation."""
    fcf = rng.randint(10, 500)  # millions
    growth_rate = round(rng.uniform(2.0, 15.0), 1)
    wacc = round(rng.uniform(6.0, 14.0), 1)
    terminal_growth = round(rng.uniform(1.5, 3.5), 1)
    shares_outstanding = rng.randint(50, 2000)  # millions
    current_price = rng.randint(10, 500)

    if wacc <= terminal_growth:
        wacc = terminal_growth + 2.0
    terminal_value = round(fcf * (1 + growth_rate / 100) ** 5 * (1 + terminal_growth / 100) / (wacc / 100 - terminal_growth / 100))
    pv_factor = sum([(1 / (1 + wacc / 100) ** i) for i in range(1, 6)])
    enterprise_value = round(fcf * pv_factor + terminal_value / (1 + wacc / 100) ** 5)
    fair_value_per_share = round(enterprise_value / shares_outstanding, 2)
    upside = round((fair_value_per_share - current_price) / current_price * 100, 1)

    problem = (f"Company with FCF ${fcf}M, growing at {growth_rate}%, WACC {wacc}%, "
               f"terminal growth {terminal_growth}%. {shares_outstanding}M shares at ${current_price}. Value the equity.")
    steps = [
        f"Project FCF for 5 years at {growth_rate}% growth",
        f"Calculate terminal value using Gordon Growth: TV = FCF_5 * (1+g) / (WACC-g)",
        f"Discount rate (WACC): {wacc}%, terminal growth: {terminal_growth}%",
        f"Enterprise value estimate: ~${enterprise_value}M",
        f"Per-share fair value: ${enterprise_value}M / {shares_outstanding}M = ${fair_value_per_share}",
        f"Current price ${current_price} vs fair value ${fair_value_per_share}: {upside}% {'upside' if upside > 0 else 'downside'}",
        f"Sensitivity: +1% WACC would reduce value by ~15%",
        f"Recommendation: {'buy' if upside > 15 else 'hold' if upside > -10 else 'sell'}",
    ]
    recommendation = "buy" if upside > 15 else ("hold" if upside > -10 else "sell")
    answer = f"Fair value: ${fair_value_per_share}/share ({upside}% vs current). Recommendation: {recommendation}."
    ground_truth = {"correct": True, "key_insight": "dcf_valuation",
                    "fair_value": fair_value_per_share, "recommendation": recommendation}
    return problem, steps, answer, ground_truth


def _finance_fraud_detection(rng, difficulty):
    """Transaction fraud detection analysis."""
    amount = rng.randint(100, 50000)
    avg_transaction = rng.randint(50, 5000)
    velocity = rng.randint(1, 20)  # transactions in last hour
    geo_distance = rng.randint(0, 5000)  # km from usual location
    device_known = rng.choice([True, False])
    time_unusual = rng.choice([True, False])

    amount_anomaly = amount > avg_transaction * 5
    velocity_anomaly = velocity > 5
    geo_anomaly = geo_distance > 500
    fraud_score = sum([amount_anomaly, velocity_anomaly, geo_anomaly, not device_known, time_unusual])
    is_fraud = fraud_score >= 3

    problem = (f"Transaction: ${amount:,} (avg ${avg_transaction:,}), {velocity} txns/hr, "
               f"{geo_distance}km from usual location, {'known' if device_known else 'unknown'} device, "
               f"{'unusual' if time_unusual else 'normal'} time. Assess fraud risk.")
    steps = [
        f"Amount anomaly: ${amount:,} is {amount/avg_transaction:.1f}x average {'→ FLAG' if amount_anomaly else '→ normal'}",
        f"Velocity: {velocity} txns/hr {'→ FLAG' if velocity_anomaly else '→ normal'}",
        f"Geolocation: {geo_distance}km deviation {'→ FLAG impossible travel' if geo_anomaly else '→ normal'}",
        f"Device fingerprint: {'known' if device_known else 'unknown → FLAG'}",
        f"Temporal pattern: {'unusual hours → FLAG' if time_unusual else 'normal hours'}",
        f"Composite fraud score: {fraud_score}/5 indicators triggered",
        f"Decision threshold: ≥3 flags → block. Score: {fraud_score} → {'BLOCK' if is_fraud else 'ALLOW'}",
        f"Recommend {'manual review' if fraud_score == 2 else 'auto-' + ('block' if is_fraud else 'approve')}",
    ]
    answer = (f"{'BLOCK transaction' if is_fraud else 'ALLOW transaction'}. "
              f"Fraud score: {fraud_score}/5. "
              f"Key signals: {', '.join(filter(None, ['amount' if amount_anomaly else '', 'velocity' if velocity_anomaly else '', 'geo' if geo_anomaly else '']))}.")
    ground_truth = {"correct": True, "key_insight": "fraud_score_threshold",
                    "is_fraud": is_fraud, "fraud_score": fraud_score}
    return problem, steps, answer, ground_truth


def _finance_options_pricing(rng, difficulty):
    """Options pricing and Greeks analysis."""
    spot = rng.randint(50, 500)
    strike = spot + rng.randint(-30, 30)
    days_to_expiry = rng.randint(7, 180)
    iv = round(rng.uniform(15, 80), 1)
    risk_free = round(rng.uniform(1.0, 6.0), 2)

    moneyness = "ITM" if spot > strike else ("ATM" if spot == strike else "OTM")
    time_value_high = days_to_expiry > 60
    intrinsic = max(0, spot - strike)
    # Simplified BS approximation
    approx_premium = intrinsic + round(spot * (iv / 100) * (days_to_expiry / 365) ** 0.5 * 0.4, 2)

    problem = (f"Call option: Spot ${spot}, Strike ${strike}, {days_to_expiry} DTE, "
               f"IV {iv}%, risk-free {risk_free}%. Analyze pricing.")
    steps = [
        f"Moneyness: {moneyness} (spot ${spot} vs strike ${strike})",
        f"Intrinsic value: max(0, {spot}-{strike}) = ${intrinsic}",
        f"Time value component: {days_to_expiry} DTE with IV {iv}%",
        f"Implied volatility {iv}% {'elevated' if iv > 40 else 'moderate' if iv > 25 else 'low'} - affects premium significantly",
        f"Approximate premium: ${approx_premium:.2f}",
        f"Delta estimate: ~{min(0.95, max(0.05, 0.5 + (spot-strike)/(spot*iv/100*0.1))):.2f}",
        f"Theta decay: {'accelerating' if days_to_expiry < 30 else 'moderate'} time decay",
        f"Strategy assessment: {'sell premium' if iv > 50 else 'buy for directional exposure'}",
    ]
    strategy = "sell premium (IV elevated)" if iv > 50 else "buy for directional bet"
    answer = (f"Option analysis: {moneyness}, premium ~${approx_premium:.2f}. "
              f"Strategy: {strategy}. "
              f"{'Theta decay concern' if days_to_expiry < 30 else 'Adequate time value'}.")
    ground_truth = {"correct": True, "key_insight": "options_pricing_analysis",
                    "moneyness": moneyness, "approx_premium": approx_premium}
    return problem, steps, answer, ground_truth



# =============================================================================
# CODING WORLD TEMPLATES
# =============================================================================

def _coding_complexity(rng, difficulty):
    """Algorithm time complexity analysis."""
    algorithms = [
        ("nested loop over n items with inner binary search", "O(n log n)", "linearithmic"),
        ("triple nested loop", "O(n^3)", "cubic"),
        ("recursive fibonacci without memoization", "O(2^n)", "exponential"),
        ("hash table lookup in a loop of n", "O(n)", "linear"),
        ("sorting then binary search", "O(n log n)", "linearithmic"),
        ("BFS on adjacency list graph", "O(V+E)", "linear_graph"),
        ("matrix multiplication naive", "O(n^3)", "cubic"),
        ("merge sort", "O(n log n)", "linearithmic"),
    ]
    algo_desc, complexity, category = rng.choice(algorithms)
    n = rng.choice([1000, 10000, 100000, 1000000])

    problem = (f"Analyze the time complexity of: {algo_desc}. "
               f"Input size n={n:,}. Determine Big-O and feasibility.")
    steps = [
        f"Identify the dominant operation pattern: {algo_desc}",
        f"Count nested iteration levels and recursive branching",
        f"Determine complexity class: {complexity}",
        f"Calculate approximate operations for n={n:,}",
        f"Feasibility: {'feasible' if category in ('linear', 'linearithmic', 'linear_graph') or n < 10000 else 'may be slow' if n < 100000 else 'infeasible for large n'}",
        f"Compare against typical 10^8 operations/second threshold",
        f"Suggest optimization: {'memoization' if 'recursive' in algo_desc else 'better algorithm' if category == 'cubic' else 'already optimal'}",
        f"Space complexity consideration for this approach",
    ]
    feasible = category in ("linear", "linearithmic", "linear_graph") or n <= 10000
    answer = (f"Complexity: {complexity} ({category}). "
              f"{'Feasible' if feasible else 'Infeasible'} for n={n:,}. "
              f"{'No optimization needed.' if feasible else 'Requires algorithmic improvement.'}")
    ground_truth = {"correct": True, "key_insight": "complexity_" + category,
                    "complexity": complexity, "feasible": feasible}
    return problem, steps, answer, ground_truth


def _coding_bug_diagnosis(rng, difficulty):
    """Diagnose a code bug from symptoms."""
    bugs = [
        ("off-by-one in loop bound", "ArrayIndexOutOfBounds at last iteration",
         "Change < to <= or adjust array size", "boundary_error"),
        ("null pointer dereference", "NullPointerException on method call",
         "Add null check before access", "null_safety"),
        ("race condition in shared counter", "Intermittent incorrect count under load",
         "Use atomic operations or mutex", "concurrency"),
        ("memory leak in event listener", "Gradual memory growth over hours",
         "Remove listener on component unmount", "resource_leak"),
        ("SQL injection via string concat", "Unexpected query results with special chars",
         "Use parameterized queries", "security"),
        ("integer overflow in accumulator", "Negative values after large sums",
         "Use long/BigInteger type", "overflow"),
    ]
    bug_type, symptom, fix, category = rng.choice(bugs)
    language = rng.choice(["Java", "Python", "C++", "JavaScript", "Go", "Rust"])
    frequency = rng.choice(["always", "intermittent", "under high load", "after long runtime"])

    problem = (f"{language} application exhibits: '{symptom}'. "
               f"Occurs {frequency}. Diagnose the root cause.")
    steps = [
        f"Symptom analysis: '{symptom}' occurring {frequency}",
        f"Pattern matching: {frequency} frequency suggests {'deterministic bug' if frequency == 'always' else 'timing/state dependent issue'}",
        f"Common causes for this symptom in {language}: {bug_type}",
        f"Root cause identified: {bug_type}",
        f"Verification approach: {'unit test with boundary input' if category == 'boundary_error' else 'load test' if category == 'concurrency' else 'code review'}",
        f"Fix: {fix}",
        f"Prevention: {'static analysis' if category in ('null_safety', 'overflow') else 'code review + testing'}",
        f"Regression test to prevent recurrence",
    ]
    answer = (f"Root cause: {bug_type}. Fix: {fix}. "
              f"The {frequency} occurrence pattern is characteristic of {category} bugs in {language}.")
    ground_truth = {"correct": True, "key_insight": category,
                    "bug_type": bug_type, "fix": fix}
    return problem, steps, answer, ground_truth


def _coding_system_design(rng, difficulty):
    """System design decision analysis."""
    scenarios = [
        ("10M users, read-heavy", "caching_layer", "Add Redis cache, read replicas"),
        ("real-time messaging, 1M concurrent", "websocket_scaling", "WebSocket with pub/sub, horizontal scaling"),
        ("large file uploads, 5GB max", "chunked_upload", "Multipart upload to object storage with resumability"),
        ("global low-latency API", "cdn_edge", "CDN + edge computing, regional replicas"),
        ("event-driven microservices", "message_queue", "Message broker with exactly-once semantics"),
        ("full-text search over 100M docs", "search_engine", "Elasticsearch cluster with sharding"),
    ]
    scenario, pattern, solution = rng.choice(scenarios)
    qps = rng.choice([1000, 10000, 100000, 1000000])
    latency_req = rng.choice([10, 50, 100, 500])  # ms

    problem = (f"Design system for: {scenario}. Requirements: {qps:,} QPS, "
               f"p99 latency < {latency_req}ms. Select architecture.")
    steps = [
        f"Requirement analysis: {qps:,} QPS with {latency_req}ms latency target",
        f"Identify bottleneck pattern: {scenario}",
        f"Architecture pattern: {pattern.replace('_', ' ')}",
        f"Component selection: {solution}",
        f"Capacity estimate: {qps:,} QPS → {'single node sufficient' if qps < 5000 else f'{qps // 5000 + 1} nodes minimum'}",
        f"Latency budget: {latency_req}ms allows {'in-memory only' if latency_req < 20 else 'cached DB reads' if latency_req < 100 else 'standard DB access'}",
        f"Fault tolerance: {'active-active' if qps > 50000 else 'active-passive'} replication",
        f"Monitoring: p99 alerting at {int(latency_req * 0.8)}ms threshold",
    ]
    answer = (f"Architecture: {pattern.replace('_', ' ')}. Implementation: {solution}. "
              f"Scale to {qps:,} QPS with {'distributed' if qps > 10000 else 'single-region'} deployment.")
    ground_truth = {"correct": True, "key_insight": pattern,
                    "solution": solution, "distributed": qps > 10000}
    return problem, steps, answer, ground_truth


def _coding_refactoring(rng, difficulty):
    """Code smell identification and refactoring recommendation."""
    smells = [
        ("god_class", 2500, 45, "Extract classes by responsibility", "single_responsibility"),
        ("feature_envy", 800, 12, "Move method to the class it uses most", "encapsulation"),
        ("long_method", 200, 8, "Extract method for each logical block", "readability"),
        ("primitive_obsession", 600, 20, "Introduce value objects", "type_safety"),
        ("shotgun_surgery", 400, 30, "Consolidate into single module", "cohesion"),
    ]
    smell, lines, methods, fix, principle = rng.choice(smells)
    coupling = round(rng.uniform(0.1, 0.9), 2)
    test_coverage = rng.randint(0, 95)

    problem = (f"Class with {lines} lines, {methods} methods, coupling factor {coupling}. "
               f"Test coverage: {test_coverage}%. Identify code smell and refactoring.")
    steps = [
        f"Size metrics: {lines} lines, {methods} methods → {'excessive' if lines > 500 else 'acceptable'}",
        f"Coupling analysis: {coupling} {'high coupling' if coupling > 0.5 else 'acceptable coupling'}",
        f"Code smell identified: {smell.replace('_', ' ')}",
        f"Risk assessment: test coverage {test_coverage}% {'safe to refactor' if test_coverage > 70 else 'add tests first'}",
        f"Refactoring strategy: {fix}",
        f"Principle violated: {principle.replace('_', ' ')}",
        f"Estimated effort: {'high' if lines > 1000 else 'medium' if lines > 500 else 'low'}",
        f"{'Write characterization tests first' if test_coverage < 50 else 'Proceed with refactoring'}",
    ]
    safe = test_coverage > 70
    answer = (f"Code smell: {smell.replace('_', ' ')}. Refactoring: {fix}. "
              f"{'Safe to proceed.' if safe else 'Add tests before refactoring (coverage too low).'}")
    ground_truth = {"correct": True, "key_insight": smell,
                    "principle": principle, "safe_to_refactor": safe}
    return problem, steps, answer, ground_truth


def _coding_database_query(rng, difficulty):
    """Database query optimization analysis."""
    table_size = rng.choice([100000, 1000000, 10000000, 100000000])
    current_time = round(rng.uniform(0.5, 30.0), 1)  # seconds
    has_index = rng.choice([True, False])
    join_count = rng.randint(0, 5)
    uses_subquery = rng.choice([True, False])

    needs_index = not has_index and table_size > 1000000
    needs_rewrite = uses_subquery and join_count > 2
    optimal_time = round(current_time * (0.1 if needs_index else 0.5 if needs_rewrite else 0.8), 2)

    problem = (f"Query on {table_size:,} row table takes {current_time}s. "
               f"{'No index' if not has_index else 'Has index'} on filter column. "
               f"{join_count} JOINs, {'uses' if uses_subquery else 'no'} subqueries. Optimize.")
    steps = [
        f"Table scan analysis: {table_size:,} rows {'full scan without index' if not has_index else 'index seek available'}",
        f"Current execution time {current_time}s is {'unacceptable' if current_time > 5 else 'slow' if current_time > 1 else 'acceptable'}",
        f"Index recommendation: {'CREATE INDEX on filter column' if needs_index else 'existing index adequate'}",
        f"Join optimization: {join_count} joins {'consider denormalization' if join_count > 3 else 'acceptable'}",
        f"Subquery analysis: {'rewrite as JOIN for better optimizer hints' if uses_subquery else 'no subqueries to optimize'}",
        f"Estimated optimized time: ~{optimal_time}s",
        f"Additional: {'partition table' if table_size > 10000000 else 'no partitioning needed'}",
        f"Consider query caching for repeated execution patterns",
    ]
    answer = (f"Optimize: {'Add index (primary improvement)' if needs_index else 'Rewrite subqueries as JOINs' if needs_rewrite else 'Minor tuning only'}. "
              f"Expected improvement: {current_time}s → ~{optimal_time}s.")
    ground_truth = {"correct": True, "key_insight": "index_needed" if needs_index else "query_rewrite" if needs_rewrite else "minor_tuning",
                    "needs_index": needs_index, "expected_time": optimal_time}
    return problem, steps, answer, ground_truth



# =============================================================================
# CYBERSECURITY WORLD TEMPLATES
# =============================================================================

def _cyber_incident_response(rng, difficulty):
    """Incident response triage and classification."""
    indicators = rng.randint(2, 8)
    source_ips = rng.randint(1, 50)
    data_exfil_mb = rng.randint(0, 5000)
    lateral_movement = rng.choice([True, False])
    privilege_escalation = rng.choice([True, False])
    persistence = rng.choice([True, False])

    severity = "critical" if (data_exfil_mb > 1000 or (lateral_movement and privilege_escalation)) else (
        "high" if (lateral_movement or privilege_escalation or data_exfil_mb > 100) else "medium")

    problem = (f"SIEM alerts: {indicators} IOCs, {source_ips} source IPs, "
               f"{data_exfil_mb}MB potential exfiltration. "
               f"Lateral movement: {'detected' if lateral_movement else 'none'}. "
               f"Privilege escalation: {'detected' if privilege_escalation else 'none'}. Classify and respond.")
    steps = [
        f"IOC count: {indicators} indicators across {source_ips} sources",
        f"Data exfiltration: {data_exfil_mb}MB {'CRITICAL - major data loss' if data_exfil_mb > 1000 else 'concerning' if data_exfil_mb > 100 else 'minimal'}",
        f"Kill chain analysis: lateral movement {'confirmed' if lateral_movement else 'not observed'}",
        f"Privilege escalation: {'detected - attacker has elevated access' if privilege_escalation else 'no evidence'}",
        f"Persistence mechanisms: {'installed' if persistence else 'not yet established'}",
        f"MITRE ATT&CK mapping: {'TA0010 Exfiltration' if data_exfil_mb > 0 else 'TA0001 Initial Access'}",
        f"Severity classification: {severity}",
        f"Response: {'isolate affected systems immediately' if severity == 'critical' else 'investigate and contain'}",
    ]
    answer = (f"Severity: {severity}. "
              f"{'IMMEDIATE isolation required - active data exfiltration.' if severity == 'critical' else 'Contain and investigate.'} "
              f"{'Persistence detected - full reimaging needed.' if persistence else ''}")
    ground_truth = {"correct": True, "key_insight": f"severity_{severity}",
                    "severity": severity, "immediate_action": severity == "critical"}
    return problem, steps, answer, ground_truth


def _cyber_vuln_assessment(rng, difficulty):
    """Vulnerability prioritization using CVSS-like scoring."""
    cvss_base = round(rng.uniform(3.0, 10.0), 1)
    exploitable = rng.choice([True, False])
    public_exploit = rng.choice([True, False])
    internet_facing = rng.choice([True, False])
    affected_systems = rng.randint(1, 500)
    data_sensitivity = rng.choice(["public", "internal", "confidential", "restricted"])

    risk_score = cvss_base * (1.5 if exploitable else 1.0) * (1.3 if internet_facing else 1.0)
    risk_score = min(10.0, round(risk_score, 1))
    priority = "P1" if risk_score > 8.5 else ("P2" if risk_score > 6.0 else "P3")

    problem = (f"Vulnerability: CVSS {cvss_base}, {'exploitable' if exploitable else 'theoretical'}, "
               f"{'public exploit available' if public_exploit else 'no public exploit'}, "
               f"{'internet-facing' if internet_facing else 'internal'}, {affected_systems} systems, "
               f"{data_sensitivity} data. Prioritize remediation.")
    steps = [
        f"Base CVSS score: {cvss_base}/10",
        f"Exploitability: {'actively exploitable with public PoC' if public_exploit else 'theoretical' if not exploitable else 'exploitable but no public PoC'}",
        f"Attack surface: {'internet-facing increases exposure' if internet_facing else 'internal only reduces risk'}",
        f"Blast radius: {affected_systems} systems with {data_sensitivity} data",
        f"Adjusted risk score: {risk_score}/10",
        f"Priority assignment: {priority} (SLA: {'24h' if priority == 'P1' else '7d' if priority == 'P2' else '30d'})",
        f"Compensating controls: {'WAF rule possible' if internet_facing else 'network segmentation'}",
        f"Remediation: patch or {'virtual patch immediately' if priority == 'P1' else 'schedule maintenance window'}",
    ]
    schedule = "7d" if priority == "P2" else "30d"
    action_msg = "Patch within 24h - critical exposure." if priority == "P1" else f"Schedule within {schedule}."
    answer = f"Priority: {priority} (risk score {risk_score}/10). {action_msg}"
    ground_truth = {"correct": True, "key_insight": f"priority_{priority}",
                    "risk_score": risk_score, "priority": priority}
    return problem, steps, answer, ground_truth


def _cyber_network_forensics(rng, difficulty):
    """Network traffic anomaly forensic analysis."""
    bytes_out = rng.randint(1000, 10000000)
    normal_bytes = rng.randint(1000, 100000)
    dst_port = rng.choice([443, 8080, 4444, 53, 22, 3389, 1337])
    protocol = rng.choice(["TCP", "UDP", "DNS", "HTTPS"])
    beacon_interval = rng.choice([0, 30, 60, 300, 3600])  # 0 = no beaconing
    unusual_port = dst_port in (4444, 1337, 8080)

    c2_likely = beacon_interval > 0 and (unusual_port or bytes_out > normal_bytes * 10)
    exfil_likely = bytes_out > normal_bytes * 50

    problem = (f"Network anomaly: {bytes_out:,} bytes outbound (normal: {normal_bytes:,}), "
               f"port {dst_port}/{protocol}, beacon interval {'none' if beacon_interval == 0 else f'{beacon_interval}s'}. Analyze.")
    steps = [
        f"Volume analysis: {bytes_out:,} bytes is {bytes_out/normal_bytes:.1f}x normal baseline",
        f"Destination port {dst_port}: {'known C2 port' if unusual_port else 'standard service port'}",
        f"Protocol: {protocol} on port {dst_port} {'unusual combination' if (protocol == 'DNS' and dst_port != 53) else 'expected'}",
        f"Beacon detection: {'regular {beacon_interval}s interval → C2 communication' if beacon_interval > 0 else 'no periodic pattern'}",
        f"{'Data exfiltration likely - volume {:.0f}x baseline'.format(bytes_out/normal_bytes) if exfil_likely else 'Volume within alert threshold'}",
        f"Threat assessment: {'C2 channel active' if c2_likely else 'likely benign anomaly'}",
        f"Recommended action: {'block IP + forensic capture' if c2_likely else 'monitor and whitelist if expected'}",
        f"IOC extraction: destination IP, port {dst_port}, protocol {protocol}",
    ]
    answer = (f"{'MALICIOUS - C2 communication detected' if c2_likely else 'SUSPICIOUS - elevated but possibly benign'}. "
              f"{'Data exfiltration in progress.' if exfil_likely else ''} "
              f"Action: {'isolate host and block destination' if c2_likely else 'investigate and baseline'}.")
    ground_truth = {"correct": True, "key_insight": "c2_detected" if c2_likely else "anomaly_benign",
                    "c2_likely": c2_likely, "exfil_likely": exfil_likely}
    return problem, steps, answer, ground_truth


def _cyber_access_control(rng, difficulty):
    """Access control policy violation analysis."""
    user_role = rng.choice(["analyst", "developer", "admin", "contractor", "service_account"])
    resource = rng.choice(["production_db", "source_code", "customer_pii", "financial_reports", "infrastructure_keys"])
    access_type = rng.choice(["read", "write", "delete", "admin"])
    time_of_access = rng.randint(0, 23)
    from_vpn = rng.choice([True, False])
    mfa_used = rng.choice([True, False])

    authorized_matrix = {
        "admin": ["production_db", "source_code", "customer_pii", "financial_reports", "infrastructure_keys"],
        "developer": ["source_code", "production_db"],
        "analyst": ["financial_reports", "customer_pii"],
        "contractor": ["source_code"],
        "service_account": ["production_db"],
    }
    resource_authorized = resource in authorized_matrix.get(user_role, [])
    write_authorized = access_type in ("read",) or user_role == "admin"
    policy_violation = not resource_authorized or (not write_authorized and access_type != "read") or (not mfa_used and resource in ("customer_pii", "infrastructure_keys"))

    problem = (f"Access event: {user_role} attempting {access_type} on {resource} "
               f"at {time_of_access:02d}:00, {'VPN' if from_vpn else 'direct'}, "
               f"MFA {'used' if mfa_used else 'not used'}. Evaluate policy compliance.")
    steps = [
        f"Role check: {user_role} → authorized resources: {authorized_matrix.get(user_role, [])}",
        f"Resource access: {resource} {'authorized' if resource_authorized else 'NOT authorized'} for {user_role}",
        f"Permission level: {access_type} {'exceeds role permissions' if not write_authorized and access_type != 'read' else 'within permissions'}",
        f"MFA status: {'compliant' if mfa_used else 'VIOLATION - required for ' + resource if resource in ('customer_pii', 'infrastructure_keys') else 'not required'}",
        f"Network context: {'VPN (expected)' if from_vpn else 'direct access (flag if remote)'}",
        f"Temporal analysis: {time_of_access:02d}:00 {'off-hours access' if time_of_access < 6 or time_of_access > 22 else 'business hours'}",
        f"Policy verdict: {'VIOLATION' if policy_violation else 'COMPLIANT'}",
        f"Action: {'block and alert SOC' if policy_violation else 'allow and log'}",
    ]
    answer = (f"{'POLICY VIOLATION - block access' if policy_violation else 'Access authorized'}. "
              f"{'Unauthorized resource for role.' if not resource_authorized else ''}"
              f"{'MFA required but not provided.' if not mfa_used and resource in ('customer_pii', 'infrastructure_keys') else ''}")
    ground_truth = {"correct": True, "key_insight": "policy_violation" if policy_violation else "access_compliant",
                    "violation": policy_violation, "reason": "unauthorized_resource" if not resource_authorized else "missing_mfa" if not mfa_used else "compliant"}
    return problem, steps, answer, ground_truth


def _cyber_malware_analysis(rng, difficulty):
    """Malware behavior classification from observed indicators."""
    behaviors = [
        (["registry_persistence", "process_injection", "c2_beacon"], "trojan", "isolate_and_reimage"),
        (["file_encryption", "ransom_note", "shadow_copy_delete"], "ransomware", "isolate_disconnect_restore"),
        (["keylogging", "screenshot_capture", "credential_dump"], "spyware", "isolate_credential_reset"),
        (["mass_email", "contact_harvest", "attachment_drop"], "worm", "quarantine_patch"),
        (["crypto_mining", "high_cpu", "pool_connection"], "cryptominer", "terminate_clean"),
    ]
    observed, classification, response = rng.choice(behaviors)
    evasion = rng.choice(["packed_binary", "fileless", "timestomping", "none"])
    sandbox_detected = rng.choice([True, False])

    problem = (f"Malware sample exhibits: {', '.join(observed)}. "
               f"Evasion: {evasion}. Sandbox {'detected' if sandbox_detected else 'not detected'}. Classify and respond.")
    steps = [
        f"Behavior analysis: {observed[0]} indicates persistence/execution capability",
        f"Secondary behavior: {observed[1]} confirms {'data collection' if 'capture' in observed[1] or 'dump' in observed[1] else 'operational objective'}",
        f"Tertiary indicator: {observed[2]} reveals {'communication channel' if 'c2' in observed[2] or 'connection' in observed[2] else 'payload delivery'}",
        f"Evasion technique: {evasion} {'complicates static analysis' if evasion != 'none' else 'no evasion observed'}",
        f"Classification: {classification} (confidence: high based on behavior triad)",
        f"Sandbox awareness: {'delays execution in analysis environments' if sandbox_detected else 'no anti-analysis'}",
        f"Impact assessment: {'critical - data at risk' if classification in ('ransomware', 'spyware') else 'moderate'}",
        f"Response protocol: {response.replace('_', ' ')}",
    ]
    answer = (f"Classification: {classification}. Response: {response.replace('_', ' ')}. "
              f"{'CRITICAL - immediate containment required.' if classification in ('ransomware', 'spyware') else 'Contain and remediate.'}")
    ground_truth = {"correct": True, "key_insight": f"malware_{classification}",
                    "classification": classification, "response": response}
    return problem, steps, answer, ground_truth


# =============================================================================
# MANUFACTURING WORLD TEMPLATES
# =============================================================================

def _manufacturing_quality_control(rng, difficulty):
    """Statistical process control and quality assessment."""
    mean_dimension = round(rng.uniform(10.0, 100.0), 2)
    std_dev = round(rng.uniform(0.01, 0.5), 3)
    tolerance = round(rng.uniform(0.1, 2.0), 2)
    sample_size = rng.choice([30, 50, 100, 200])
    defect_rate = round(rng.uniform(0.1, 10.0), 2)
    cpk = round(tolerance / (3 * std_dev), 2) if std_dev > 0 else 99

    capable = cpk >= 1.33
    problem = (f"Process: mean {mean_dimension}mm, σ={std_dev}mm, tolerance ±{tolerance}mm, "
               f"sample n={sample_size}, defect rate {defect_rate}%. Assess capability.")
    steps = [
        f"Process capability index: Cpk = tolerance/(3σ) = {tolerance}/(3×{std_dev}) = {cpk}",
        f"Capability assessment: Cpk {cpk} {'≥1.33 CAPABLE' if capable else '<1.33 NOT CAPABLE'}",
        f"Defect rate {defect_rate}% {'within Six Sigma target' if defect_rate < 0.1 else 'exceeds target' if defect_rate > 1 else 'marginal'}",
        f"Sample size n={sample_size}: {'adequate' if sample_size >= 50 else 'consider increasing'} for statistical significance",
        f"Control limits: UCL={round(mean_dimension + 3*std_dev, 3)}mm, LCL={round(mean_dimension - 3*std_dev, 3)}mm",
        f"Process stability: {'stable' if defect_rate < 5 else 'unstable - investigate assignable causes'}",
        f"Recommendation: {'maintain current process' if capable else 'reduce variation or widen tolerance'}",
        f"Six Sigma level: ~{max(1, min(6, int(cpk * 3)))} sigma",
    ]
    answer = (f"Process {'CAPABLE' if capable else 'NOT CAPABLE'} (Cpk={cpk}). "
              f"{'No action needed.' if capable else 'Reduce process variation or review tolerances.'}")
    ground_truth = {"correct": True, "key_insight": "process_capability",
                    "cpk": cpk, "capable": capable}
    return problem, steps, answer, ground_truth


def _manufacturing_oee(rng, difficulty):
    """Overall Equipment Effectiveness calculation."""
    availability = round(rng.uniform(60, 99), 1)
    performance = round(rng.uniform(50, 99), 1)
    quality = round(rng.uniform(80, 99.9), 1)
    planned_hours = rng.choice([8, 12, 16, 24])
    downtime_min = rng.randint(10, 180)

    oee = round(availability * performance * quality / 10000, 1)
    world_class = oee >= 85
    bottleneck = "availability" if availability < performance and availability < quality else (
        "performance" if performance < quality else "quality")

    problem = (f"Production line: Availability {availability}%, Performance {performance}%, "
               f"Quality {quality}%. Planned: {planned_hours}h, Downtime: {downtime_min}min. Calculate OEE.")
    steps = [
        f"Availability: {availability}% (downtime {downtime_min}min of {planned_hours*60}min planned)",
        f"Performance: {performance}% of theoretical maximum rate",
        f"Quality: {quality}% first-pass yield",
        f"OEE = A × P × Q = {availability}% × {performance}% × {quality}% = {oee}%",
        f"World-class benchmark: 85%. Current: {oee}% → {'meets' if world_class else 'below'} target",
        f"Bottleneck identification: {bottleneck} is the limiting factor",
        f"Improvement priority: focus on {bottleneck} for maximum OEE gain",
        f"Projected OEE if {bottleneck} improves 5%: ~{round(oee * 1.05, 1)}%",
    ]
    answer = (f"OEE: {oee}% ({'world-class' if world_class else 'below target'}). "
              f"Focus improvement on {bottleneck} ({availability if bottleneck == 'availability' else performance if bottleneck == 'performance' else quality}%).")
    ground_truth = {"correct": True, "key_insight": f"bottleneck_{bottleneck}",
                    "oee": oee, "world_class": world_class, "bottleneck": bottleneck}
    return problem, steps, answer, ground_truth


def _manufacturing_predictive_maintenance(rng, difficulty):
    """Predictive maintenance decision based on sensor data."""
    vibration = round(rng.uniform(0.5, 15.0), 1)  # mm/s
    temperature = round(rng.uniform(40, 120), 1)  # C
    oil_particulate = rng.randint(10, 500)  # ppm
    hours_since_service = rng.randint(100, 10000)
    mtbf = rng.randint(2000, 8000)

    vib_alert = vibration > 7.0
    temp_alert = temperature > 90
    oil_alert = oil_particulate > 200
    failure_imminent = (vib_alert and temp_alert) or oil_particulate > 400
    schedule_maintenance = (vib_alert or temp_alert or oil_alert) and not failure_imminent
    remaining_life_pct = max(0, round((1 - hours_since_service / mtbf) * 100))

    problem = (f"Machine sensors: vibration {vibration}mm/s, temp {temperature}°C, "
               f"oil particulate {oil_particulate}ppm. {hours_since_service}h since service (MTBF {mtbf}h).")
    steps = [
        f"Vibration: {vibration}mm/s {'ALERT >7.0' if vib_alert else 'normal'}",
        f"Temperature: {temperature}°C {'ALERT >90°C' if temp_alert else 'normal'}",
        f"Oil analysis: {oil_particulate}ppm {'CRITICAL >400' if oil_particulate > 400 else 'ALERT >200' if oil_alert else 'normal'}",
        f"Usage: {hours_since_service}h / MTBF {mtbf}h = {remaining_life_pct}% remaining life estimate",
        f"Failure probability: {'HIGH - multiple alert conditions' if failure_imminent else 'MODERATE' if schedule_maintenance else 'LOW'}",
        f"Fault signature: {'bearing degradation' if vib_alert else 'lubrication issue' if oil_alert else 'normal wear'}",
        f"Decision: {'STOP immediately' if failure_imminent else 'schedule maintenance' if schedule_maintenance else 'continue monitoring'}",
        f"Estimated time to failure: {'<24h' if failure_imminent else f'{int(remaining_life_pct/100 * mtbf * 0.1)}h' if schedule_maintenance else '>1000h'}",
    ]
    action = "immediate_shutdown" if failure_imminent else ("schedule_maintenance" if schedule_maintenance else "continue_operation")
    answer = (f"Action: {action.replace('_', ' ')}. "
              f"{'CRITICAL - failure imminent, stop machine.' if failure_imminent else 'Schedule within 48h.' if schedule_maintenance else 'No action required.'}")
    ground_truth = {"correct": True, "key_insight": action,
                    "failure_imminent": failure_imminent, "remaining_life_pct": remaining_life_pct}
    return problem, steps, answer, ground_truth


def _manufacturing_root_cause(rng, difficulty):
    """Manufacturing defect root cause analysis (5-why methodology)."""
    defect_types = [
        ("dimensional_deviation", "CNC spindle bearing wear", "replace_spindle_bearing"),
        ("surface_roughness", "tool wear beyond threshold", "implement_tool_life_tracking"),
        ("porosity", "moisture in raw material", "incoming_material_inspection"),
        ("crack_formation", "excessive thermal gradient", "adjust_cooling_rate"),
        ("color_variation", "pigment mixing inconsistency", "calibrate_dispenser"),
    ]
    defect, root_cause, corrective_action = rng.choice(defect_types)
    occurrence_rate = round(rng.uniform(0.5, 15.0), 1)
    shift = rng.choice(["day", "night", "mixed"])
    batch_size = rng.randint(100, 10000)
    affected = int(batch_size * occurrence_rate / 100)

    problem = (f"Defect: {defect.replace('_', ' ')}, rate {occurrence_rate}% ({affected}/{batch_size} units), "
               f"occurring on {shift} shift. Perform root cause analysis.")
    steps = [
        f"Defect characterization: {defect.replace('_', ' ')} at {occurrence_rate}% rate",
        f"Pattern analysis: {shift} shift → {'process parameter drift' if shift == 'night' else 'material variation' if shift == 'mixed' else 'systematic issue'}",
        f"Why-1: Why is {defect.replace('_', ' ')} occurring? → process parameter out of spec",
        f"Why-2: Why is parameter out of spec? → {root_cause}",
        f"Why-3: Why was this not detected? → monitoring gap in current system",
        f"Impact: {affected} defective units, cost ~${affected * rng.randint(5, 50):,}",
        f"Root cause confirmed: {root_cause}",
        f"Corrective action: {corrective_action.replace('_', ' ')}",
    ]
    answer = (f"Root cause: {root_cause}. Corrective action: {corrective_action.replace('_', ' ')}. "
              f"Prevent {affected} defects/batch saving ~${affected * 20:,}.")
    ground_truth = {"correct": True, "key_insight": root_cause.replace(' ', '_'),
                    "corrective_action": corrective_action, "occurrence_rate": occurrence_rate}
    return problem, steps, answer, ground_truth


def _manufacturing_capacity_planning(rng, difficulty):
    """Production capacity planning and bottleneck analysis."""
    stations = rng.randint(3, 8)
    cycle_times = [round(rng.uniform(10, 120), 1) for _ in range(stations)]
    demand_per_day = rng.randint(100, 2000)
    hours_available = rng.choice([8, 16, 24])
    efficiency = round(rng.uniform(0.7, 0.95), 2)

    bottleneck_time = max(cycle_times)
    bottleneck_station = cycle_times.index(bottleneck_time) + 1
    throughput_per_hour = round(3600 / bottleneck_time * efficiency, 1)
    daily_capacity = round(throughput_per_hour * hours_available)
    meets_demand = daily_capacity >= demand_per_day

    problem = (f"{stations}-station line. Cycle times: {cycle_times} seconds. "
               f"Demand: {demand_per_day}/day, {hours_available}h available, efficiency {efficiency*100}%.")
    steps = [
        f"Identify bottleneck: station {bottleneck_station} at {bottleneck_time}s (longest cycle time)",
        f"Line throughput limited by bottleneck: {3600/bottleneck_time:.1f} units/hr theoretical",
        f"Apply efficiency factor {efficiency}: {throughput_per_hour} units/hr actual",
        f"Daily capacity: {throughput_per_hour} × {hours_available}h = {daily_capacity} units",
        f"Demand: {demand_per_day}/day vs capacity {daily_capacity}/day",
        f"{'CAPACITY SHORTFALL: {}'.format(demand_per_day - daily_capacity) if not meets_demand else 'Demand met with {:.0f}% utilization'.format(demand_per_day/daily_capacity*100)}",
        f"Improvement options: {'add parallel station at bottleneck' if not meets_demand else 'optimize for cost reduction'}",
        f"Line balance efficiency: {round(sum(cycle_times)/(stations * bottleneck_time) * 100, 1)}%",
    ]
    answer = (f"Bottleneck: station {bottleneck_station} ({bottleneck_time}s). "
              f"Capacity: {daily_capacity}/day. {'INSUFFICIENT - shortfall of ' + str(demand_per_day - daily_capacity) + ' units.' if not meets_demand else 'Meets demand.'}")
    ground_truth = {"correct": True, "key_insight": "bottleneck_identification",
                    "bottleneck_station": bottleneck_station, "meets_demand": meets_demand,
                    "daily_capacity": daily_capacity}
    return problem, steps, answer, ground_truth



# =============================================================================
# SUPPLY CHAIN WORLD TEMPLATES
# =============================================================================

def _supplychain_inventory_optimization(rng, difficulty):
    """Economic Order Quantity and reorder point calculation."""
    annual_demand = rng.randint(1000, 100000)
    ordering_cost = rng.randint(20, 500)
    holding_cost_pct = round(rng.uniform(0.15, 0.35), 2)
    unit_cost = round(rng.uniform(1.0, 200.0), 2)
    lead_time_days = rng.randint(1, 30)
    daily_demand = round(annual_demand / 365, 1)
    demand_variability = round(rng.uniform(0.1, 0.4), 2)

    holding_cost = unit_cost * holding_cost_pct
    eoq = round((2 * annual_demand * ordering_cost / holding_cost) ** 0.5)
    safety_stock = round(1.65 * demand_variability * daily_demand * (lead_time_days ** 0.5))
    reorder_point = round(daily_demand * lead_time_days + safety_stock)

    problem = (f"Inventory: annual demand {annual_demand:,} units, ordering cost ${ordering_cost}, "
               f"unit cost ${unit_cost}, holding {holding_cost_pct*100}%, lead time {lead_time_days} days, "
               f"demand CV {demand_variability}. Calculate optimal order quantity.")
    steps = [
        f"Annual demand: {annual_demand:,} units ({daily_demand}/day)",
        f"Holding cost: ${unit_cost} × {holding_cost_pct} = ${holding_cost:.2f}/unit/year",
        f"EOQ = √(2×D×S/H) = √(2×{annual_demand}×{ordering_cost}/{holding_cost:.2f}) = {eoq} units",
        f"Lead time demand: {daily_demand} × {lead_time_days} = {round(daily_demand * lead_time_days)} units",
        f"Safety stock (95% service level): z×σ×√LT = 1.65×{demand_variability}×{daily_demand}×√{lead_time_days} = {safety_stock}",
        f"Reorder point: {round(daily_demand * lead_time_days)} + {safety_stock} = {reorder_point} units",
        f"Total annual cost: ordering ${round(annual_demand/eoq * ordering_cost):,} + holding ${round(eoq/2 * holding_cost):,}",
        f"Orders per year: {round(annual_demand/eoq)} orders",
    ]
    answer = (f"EOQ: {eoq} units. Reorder at {reorder_point} units (includes {safety_stock} safety stock). "
              f"~{round(annual_demand/eoq)} orders/year.")
    ground_truth = {"correct": True, "key_insight": "eoq_optimization",
                    "eoq": eoq, "reorder_point": reorder_point, "safety_stock": safety_stock}
    return problem, steps, answer, ground_truth


def _supplychain_logistics_routing(rng, difficulty):
    """Logistics route optimization with constraints."""
    num_stops = rng.randint(3, 8)
    distances = [rng.randint(10, 200) for _ in range(num_stops)]
    time_windows = [(rng.randint(6, 12), rng.randint(14, 20)) for _ in range(num_stops)]
    vehicle_capacity = rng.randint(5000, 20000)
    loads = [rng.randint(500, 3000) for _ in range(num_stops)]
    total_load = sum(loads)
    vehicles_needed = max(1, -(-total_load // vehicle_capacity))  # ceiling division
    total_distance = sum(distances)

    feasible_single = total_load <= vehicle_capacity
    problem = (f"Delivery: {num_stops} stops, distances {distances}km, "
               f"loads {loads}kg, vehicle capacity {vehicle_capacity}kg. Optimize routing.")
    steps = [
        f"Total load: {total_load}kg vs vehicle capacity {vehicle_capacity}kg",
        f"Vehicles required: {'1 (single route)' if feasible_single else f'{vehicles_needed} vehicles needed'}",
        f"Total distance (sequential): {total_distance}km",
        f"Time window feasibility: check earliest/latest delivery constraints",
        f"Route optimization: {'nearest-neighbor heuristic' if num_stops > 5 else 'evaluate all permutations'}",
        f"Estimated optimal distance: ~{round(total_distance * 0.7)}km (30% improvement typical)",
        f"Cost estimate: {vehicles_needed} vehicles × ~${round(total_distance * 2.5):,} fuel",
        f"Constraint check: all time windows {'feasible' if num_stops < 6 else 'require verification'}",
    ]
    answer = (f"Deploy {vehicles_needed} vehicle{'s' if vehicles_needed > 1 else ''}. "
              f"Estimated route: ~{round(total_distance * 0.7)}km optimized. "
              f"{'Single route feasible.' if feasible_single else 'Split required due to capacity.'}")
    ground_truth = {"correct": True, "key_insight": "route_optimization",
                    "vehicles_needed": vehicles_needed, "feasible_single_vehicle": feasible_single}
    return problem, steps, answer, ground_truth


def _supplychain_demand_forecast(rng, difficulty):
    """Demand forecasting model selection and error analysis."""
    historical = [rng.randint(800, 1500) for _ in range(12)]
    trend = rng.choice(["increasing", "decreasing", "flat", "seasonal"])
    mape_naive = round(rng.uniform(8, 30), 1)
    mape_ema = round(rng.uniform(5, 20), 1)
    mape_arima = round(rng.uniform(3, 15), 1)
    seasonality_strength = round(rng.uniform(0.1, 0.9), 2)

    best_model = "ARIMA" if mape_arima < mape_ema else "EMA"
    has_seasonality = seasonality_strength > 0.5
    forecast_next = round(sum(historical[-3:]) / 3 * (1.05 if trend == "increasing" else 0.95 if trend == "decreasing" else 1.0))

    problem = (f"12-month history: avg {round(sum(historical)/12)}, trend: {trend}, "
               f"seasonality strength: {seasonality_strength}. "
               f"Model MAPE: Naive {mape_naive}%, EMA {mape_ema}%, ARIMA {mape_arima}%. Select model.")
    steps = [
        f"Trend analysis: {trend} pattern over 12 months",
        f"Seasonality: strength {seasonality_strength} {'significant - use seasonal model' if has_seasonality else 'weak - trend model sufficient'}",
        f"Model comparison: Naive {mape_naive}% > EMA {mape_ema}% > ARIMA {mape_arima}%",
        f"Best model: {best_model} with MAPE {mape_arima if best_model == 'ARIMA' else mape_ema}%",
        f"Forecast next period: ~{forecast_next} units",
        f"Confidence interval: ±{round(forecast_next * mape_arima/100)} units (based on MAPE)",
        f"{'Add seasonal decomposition' if has_seasonality else 'Trend-only model adequate'}",
        f"Recommendation: use {best_model}{' with seasonal adjustment' if has_seasonality else ''} for planning",
    ]
    answer = (f"Select {best_model} (MAPE {mape_arima if best_model == 'ARIMA' else mape_ema}%). "
              f"Forecast: ~{forecast_next} units. "
              f"{'Include seasonal adjustment.' if has_seasonality else ''}")
    ground_truth = {"correct": True, "key_insight": f"model_selection_{best_model.lower()}",
                    "best_model": best_model, "forecast": forecast_next}
    return problem, steps, answer, ground_truth


def _supplychain_supplier_risk(rng, difficulty):
    """Supplier risk assessment and diversification decision."""
    num_suppliers = rng.randint(1, 5)
    lead_times = [rng.randint(5, 60) for _ in range(num_suppliers)]
    quality_scores = [round(rng.uniform(85, 99.5), 1) for _ in range(num_suppliers)]
    financial_ratings = [rng.choice(["A", "B", "C", "D"]) for _ in range(num_suppliers)]
    geo_concentration = rng.choice(["single_region", "multi_region", "global"])
    single_source = num_suppliers == 1

    high_risk = single_source or any(r in ("C", "D") for r in financial_ratings) or geo_concentration == "single_region"
    problem = (f"{num_suppliers} supplier(s): lead times {lead_times} days, "
               f"quality {quality_scores}%, financial ratings {financial_ratings}, "
               f"geographic: {geo_concentration}. Assess supply risk.")
    steps = [
        f"Supplier count: {num_suppliers} {'RISK: single source' if single_source else 'diversified'}",
        f"Lead time analysis: max {max(lead_times)} days {'excessive' if max(lead_times) > 30 else 'acceptable'}",
        f"Quality assessment: {'all above 95%' if all(q > 95 for q in quality_scores) else 'quality concerns with some suppliers'}",
        f"Financial stability: {financial_ratings} {'RISK: weak supplier(s)' if any(r in ('C', 'D') for r in financial_ratings) else 'stable'}",
        f"Geographic concentration: {geo_concentration} {'RISK: regional disruption exposure' if geo_concentration == 'single_region' else 'diversified'}",
        f"Overall risk level: {'HIGH' if high_risk else 'MODERATE' if num_suppliers < 3 else 'LOW'}",
        f"Recommendation: {'dual-source immediately' if single_source else 'improve financial monitoring' if any(r in ('C', 'D') for r in financial_ratings) else 'maintain current strategy'}",
        f"Contingency: maintain {max(lead_times)} days buffer stock minimum",
    ]
    answer = (f"Risk: {'HIGH - diversification needed' if high_risk else 'ACCEPTABLE'}. "
              f"{'Add second source.' if single_source else ''}"
              f"{'Monitor financially weak suppliers.' if any(r in ('C', 'D') for r in financial_ratings) else ''}")
    ground_truth = {"correct": True, "key_insight": "supplier_risk_high" if high_risk else "supplier_risk_acceptable",
                    "high_risk": high_risk, "single_source": single_source}
    return problem, steps, answer, ground_truth


def _supplychain_warehouse_layout(rng, difficulty):
    """Warehouse slotting optimization based on velocity analysis."""
    num_skus = rng.randint(100, 5000)
    top_20_pct_volume = round(rng.uniform(60, 85), 1)  # Pareto
    picks_per_day = rng.randint(200, 5000)
    current_travel_time_pct = round(rng.uniform(30, 60), 1)
    warehouse_sqft = rng.randint(10000, 200000)

    pareto_strong = top_20_pct_volume > 75
    optimization_potential = round(current_travel_time_pct * 0.3, 1)
    new_travel_pct = round(current_travel_time_pct - optimization_potential, 1)

    problem = (f"Warehouse: {num_skus} SKUs, {picks_per_day} picks/day, "
               f"top 20% SKUs = {top_20_pct_volume}% volume, "
               f"current travel time {current_travel_time_pct}% of labor. Optimize layout.")
    steps = [
        f"Pareto analysis: top 20% SKUs represent {top_20_pct_volume}% of volume {'strong Pareto' if pareto_strong else 'moderate distribution'}",
        f"Current travel waste: {current_travel_time_pct}% of labor = {round(picks_per_day * current_travel_time_pct/100)} pick-minutes/day",
        f"ABC classification: A-items (top 20%) → golden zone, B-items → middle, C-items → back",
        f"Slotting strategy: velocity-based forward pick, bulk in reserve",
        f"Expected improvement: reduce travel by {optimization_potential}% → new travel {new_travel_pct}%",
        f"Picks saved: ~{round(picks_per_day * optimization_potential/100)} pick-equivalent minutes/day",
        f"ROI: {'high - implement immediately' if optimization_potential > 10 else 'moderate - phase in'}",
        f"Additional: {'implement batch picking for C-items' if num_skus > 1000 else 'zone picking adequate'}",
    ]
    answer = (f"Reslot top 20% SKUs to golden zone (saves {optimization_potential}% travel). "
              f"Expected travel reduction: {current_travel_time_pct}% → {new_travel_pct}%. "
              f"{'Strong Pareto supports aggressive forward stocking.' if pareto_strong else ''}")
    ground_truth = {"correct": True, "key_insight": "velocity_slotting",
                    "optimization_pct": optimization_potential, "pareto_strong": pareto_strong}
    return problem, steps, answer, ground_truth


# =============================================================================
# ENERGY WORLD TEMPLATES
# =============================================================================

def _energy_load_balancing(rng, difficulty):
    """Power grid load balancing and dispatch optimization."""
    demand_mw = rng.randint(500, 5000)
    solar_mw = rng.randint(0, 800)
    wind_mw = rng.randint(0, 600)
    nuclear_mw = rng.randint(200, 1500)
    gas_capacity_mw = rng.randint(500, 3000)
    storage_mwh = rng.randint(0, 500)
    time_of_day = rng.randint(0, 23)

    renewable_total = solar_mw + wind_mw
    baseload = nuclear_mw
    gap = demand_mw - renewable_total - baseload
    gas_needed = max(0, gap - storage_mwh)
    curtailment = max(0, renewable_total + baseload - demand_mw)
    balanced = gas_needed <= gas_capacity_mw

    problem = (f"Grid at {time_of_day:02d}:00 - Demand: {demand_mw}MW. "
               f"Solar: {solar_mw}MW, Wind: {wind_mw}MW, Nuclear: {nuclear_mw}MW, "
               f"Gas capacity: {gas_capacity_mw}MW, Storage: {storage_mwh}MWh. Dispatch optimally.")
    steps = [
        f"Demand: {demand_mw}MW at {time_of_day:02d}:00",
        f"Renewable generation: solar {solar_mw} + wind {wind_mw} = {renewable_total}MW",
        f"Baseload (nuclear): {nuclear_mw}MW (non-dispatchable)",
        f"Gap after renewables + baseload: {demand_mw} - {renewable_total} - {nuclear_mw} = {gap}MW",
        f"Storage dispatch: {'deploy {}'.format(min(storage_mwh, max(0, gap))) + 'MWh' if gap > 0 else 'charge available'}",
        f"Gas dispatch needed: {gas_needed}MW {'within capacity' if balanced else 'EXCEEDS capacity - shortfall'}",
        f"{'Curtailment: ' + str(curtailment) + 'MW renewable curtailed' if curtailment > 0 else 'No curtailment needed'}",
        f"Grid frequency: {'stable' if balanced else 'at risk - activate demand response'}",
    ]
    answer = (f"Dispatch: Gas {gas_needed}MW, Storage {min(storage_mwh, max(0, gap))}MWh. "
              f"{'Grid balanced.' if balanced else 'SHORTFALL - activate demand response.'} "
              f"{'Curtail ' + str(curtailment) + 'MW.' if curtailment > 0 else ''}")
    ground_truth = {"correct": True, "key_insight": "grid_balanced" if balanced else "demand_response_needed",
                    "gas_dispatch": gas_needed, "balanced": balanced, "curtailment": curtailment}
    return problem, steps, answer, ground_truth


def _energy_solar_sizing(rng, difficulty):
    """Solar PV system sizing for commercial installation."""
    annual_kwh = rng.randint(50000, 2000000)
    peak_sun_hours = round(rng.uniform(3.5, 6.5), 1)
    roof_sqm = rng.randint(200, 5000)
    panel_watt = rng.choice([350, 400, 450, 500])
    panel_sqm = 1.7
    efficiency_loss = round(rng.uniform(0.15, 0.25), 2)
    electricity_rate = round(rng.uniform(0.08, 0.25), 3)

    system_kw = round(annual_kwh / (peak_sun_hours * 365 * (1 - efficiency_loss)) / 1000, 1)
    panels_needed = int(system_kw * 1000 / panel_watt) + 1
    area_needed = round(panels_needed * panel_sqm, 1)
    fits_roof = area_needed <= roof_sqm
    annual_savings = round(annual_kwh * electricity_rate)
    payback_years = round(system_kw * 1200 / annual_savings, 1) if annual_savings > 0 else 99

    problem = (f"Commercial facility: {annual_kwh:,} kWh/year, {peak_sun_hours} peak sun hours, "
               f"roof {roof_sqm}m², panels {panel_watt}W, rate ${electricity_rate}/kWh. Size the system.")
    steps = [
        f"Required system: {annual_kwh:,}kWh / ({peak_sun_hours}h × 365 × {1-efficiency_loss:.2f}) = {system_kw}kW",
        f"Panels needed: {system_kw}kW / {panel_watt}W = {panels_needed} panels",
        f"Area required: {panels_needed} × {panel_sqm}m² = {area_needed}m² ({'fits' if fits_roof else 'exceeds'} {roof_sqm}m² roof)",
        f"System losses: {efficiency_loss*100}% (soiling, wiring, inverter, temperature)",
        f"Annual generation: ~{annual_kwh:,} kWh (matching demand)",
        f"Annual savings: {annual_kwh:,} × ${electricity_rate} = ${annual_savings:,}",
        f"Payback period: ~{payback_years} years at current rates",
        f"{'Roof constraint: reduce to {:.0f}kW'.format(roof_sqm / panel_sqm * panel_watt / 1000) if not fits_roof else 'Full system fits roof'}",
    ]
    actual_kw = system_kw if fits_roof else round(roof_sqm / panel_sqm * panel_watt / 1000, 1)
    answer = (f"System size: {actual_kw}kW ({panels_needed if fits_roof else int(roof_sqm/panel_sqm)} panels). "
              f"{'Fully covers demand.' if fits_roof else 'Roof-limited, covers ' + str(round(roof_sqm/area_needed*100)) + '% of demand.'} "
              f"Payback: {payback_years} years.")
    ground_truth = {"correct": True, "key_insight": "solar_sizing",
                    "system_kw": actual_kw, "fits_roof": fits_roof, "payback_years": payback_years}
    return problem, steps, answer, ground_truth


def _energy_battery_degradation(rng, difficulty):
    """Battery storage degradation and replacement planning."""
    initial_capacity_mwh = round(rng.uniform(1.0, 50.0), 1)
    cycles_completed = rng.randint(500, 5000)
    rated_cycles = rng.randint(4000, 8000)
    current_soh = round(rng.uniform(60, 95), 1)  # state of health %
    degradation_rate_per_cycle = round((100 - current_soh) / max(1, cycles_completed) * 100, 3)
    daily_cycles = round(rng.uniform(0.5, 2.0), 1)

    remaining_cycles = round((current_soh - 70) / (degradation_rate_per_cycle / 100)) if degradation_rate_per_cycle > 0 else 9999
    remaining_days = round(remaining_cycles / daily_cycles) if daily_cycles > 0 else 9999
    end_of_life = current_soh < 70
    replace_soon = remaining_days < 365

    problem = (f"Battery: {initial_capacity_mwh}MWh, {cycles_completed} cycles completed "
               f"(rated {rated_cycles}), SoH {current_soh}%, {daily_cycles} cycles/day. "
               f"Forecast remaining life.")
    steps = [
        f"State of Health: {current_soh}% (end-of-life threshold: 70%)",
        f"Degradation rate: {degradation_rate_per_cycle}%/100 cycles",
        f"Remaining SoH margin: {current_soh} - 70 = {round(current_soh - 70, 1)}%",
        f"Remaining cycles estimate: ~{remaining_cycles} cycles until EOL",
        f"At {daily_cycles} cycles/day: ~{remaining_days} days ({round(remaining_days/365, 1)} years) remaining",
        f"Current usable capacity: {round(initial_capacity_mwh * current_soh/100, 1)}MWh of {initial_capacity_mwh}MWh",
        f"{'END OF LIFE - replace immediately' if end_of_life else 'Replace within 12 months' if replace_soon else 'Continue operation'}",
        f"Budget planning: schedule replacement {'now' if end_of_life else 'Q' + str(min(4, max(1, remaining_days//90)))}",
    ]
    answer = (f"{'REPLACE NOW - below 70% SoH.' if end_of_life else f'Remaining life: ~{remaining_days} days ({round(remaining_days/365, 1)} years).'} "
              f"Usable capacity: {round(initial_capacity_mwh * current_soh/100, 1)}MWh. "
              f"{'Plan replacement within 12 months.' if replace_soon and not end_of_life else ''}")
    ground_truth = {"correct": True, "key_insight": "battery_eol" if end_of_life else "battery_replacement_planning",
                    "remaining_days": remaining_days, "end_of_life": end_of_life, "replace_soon": replace_soon}
    return problem, steps, answer, ground_truth


def _energy_grid_fault(rng, difficulty):
    """Power grid fault detection and isolation."""
    voltage_deviation_pct = round(rng.uniform(-15, 15), 1)
    frequency_hz = round(rng.uniform(49.0, 51.0), 2)
    thd = round(rng.uniform(1, 15), 1)  # total harmonic distortion %
    fault_current_ka = round(rng.uniform(0.5, 50), 1)
    affected_feeders = rng.randint(1, 8)
    customers_affected = rng.randint(100, 50000)

    voltage_fault = abs(voltage_deviation_pct) > 10
    frequency_fault = abs(frequency_hz - 50.0) > 0.5
    harmonic_fault = thd > 8
    fault_type = "short_circuit" if fault_current_ka > 20 else ("ground_fault" if fault_current_ka > 5 else "overload")
    critical = voltage_fault or frequency_fault or fault_current_ka > 30

    problem = (f"Grid anomaly: voltage {'+' if voltage_deviation_pct > 0 else ''}{voltage_deviation_pct}%, "
               f"frequency {frequency_hz}Hz, THD {thd}%, fault current {fault_current_ka}kA, "
               f"{affected_feeders} feeders, {customers_affected:,} customers affected.")
    steps = [
        f"Voltage analysis: {voltage_deviation_pct}% deviation {'FAULT' if voltage_fault else 'within tolerance'}",
        f"Frequency: {frequency_hz}Hz (nominal 50Hz) {'CRITICAL' if frequency_fault else 'stable'}",
        f"Harmonics: THD {thd}% {'exceeds IEEE 519 limit' if harmonic_fault else 'acceptable'}",
        f"Fault current: {fault_current_ka}kA → {fault_type.replace('_', ' ')}",
        f"Affected scope: {affected_feeders} feeders, {customers_affected:,} customers",
        f"Protection coordination: {'immediate trip required' if critical else 'time-delayed response'}",
        f"Isolation strategy: open breaker{'s on affected feeders' if affected_feeders > 1 else ' at fault location'}",
        f"Restoration: {'load transfer to alternate feed' if affected_feeders < 4 else 'staged restoration required'}",
    ]
    answer = (f"Fault type: {fault_type.replace('_', ' ')}. {'CRITICAL - immediate isolation.' if critical else 'Managed response.'} "
              f"Isolate {affected_feeders} feeder{'s' if affected_feeders > 1 else ''}, restore {customers_affected:,} customers via alternate path.")
    ground_truth = {"correct": True, "key_insight": fault_type,
                    "critical": critical, "customers_affected": customers_affected}
    return problem, steps, answer, ground_truth


def _energy_emissions_trading(rng, difficulty):
    """Carbon emissions trading and compliance analysis."""
    annual_emissions_t = rng.randint(10000, 500000)
    allowances_t = rng.randint(8000, 400000)
    carbon_price = round(rng.uniform(20, 100), 2)
    reduction_cost_per_t = round(rng.uniform(30, 150), 2)
    offset_price = round(rng.uniform(10, 80), 2)
    compliance_deadline_days = rng.randint(30, 365)

    shortfall = max(0, annual_emissions_t - allowances_t)
    surplus = max(0, allowances_t - annual_emissions_t)
    buy_cost = round(shortfall * carbon_price)
    reduce_cost = round(shortfall * reduction_cost_per_t)
    offset_cost = round(shortfall * offset_price)
    best_strategy = "reduce" if reduce_cost < buy_cost and reduce_cost < offset_cost else (
        "offset" if offset_cost < buy_cost else "buy_allowances")

    problem = (f"Emissions: {annual_emissions_t:,}t CO2, allowances: {allowances_t:,}t, "
               f"carbon price ${carbon_price}/t, reduction cost ${reduction_cost_per_t}/t, "
               f"offset price ${offset_price}/t. Deadline: {compliance_deadline_days} days.")
    steps = [
        f"Compliance gap: {annual_emissions_t:,} - {allowances_t:,} = {'shortfall of ' + str(shortfall) + 't' if shortfall > 0 else 'surplus of ' + str(surplus) + 't'}",
        f"Option 1 - Buy allowances: {shortfall}t × ${carbon_price} = ${buy_cost:,}",
        f"Option 2 - Reduce emissions: {shortfall}t × ${reduction_cost_per_t} = ${reduce_cost:,}",
        f"Option 3 - Purchase offsets: {shortfall}t × ${offset_price} = ${offset_cost:,}",
        f"Cost comparison: buy ${buy_cost:,} vs reduce ${reduce_cost:,} vs offset ${offset_cost:,}",
        f"Optimal strategy: {best_strategy.replace('_', ' ')}",
        f"Timeline feasibility: {compliance_deadline_days} days {'sufficient for reduction' if compliance_deadline_days > 180 else 'tight - may need market purchase'}",
        f"{'Bank surplus allowances for future periods' if surplus > 0 else 'Execute strategy within deadline'}",
    ]
    answer = (f"{'Surplus of ' + str(surplus) + 't - bank for future.' if surplus > 0 else 'Strategy: ' + best_strategy.replace('_', ' ') + '. Cost: $' + str(min(buy_cost, reduce_cost, offset_cost)) + '.'} "
              f"{'Compliance achievable within deadline.' if compliance_deadline_days > 90 or best_strategy == 'buy_allowances' else 'Tight timeline - prioritize market purchase.'}")
    ground_truth = {"correct": True, "key_insight": best_strategy if shortfall > 0 else "surplus_banking",
                    "shortfall": shortfall, "best_strategy": best_strategy,
                    "minimum_cost": min(buy_cost, reduce_cost, offset_cost) if shortfall > 0 else 0}
    return problem, steps, answer, ground_truth



# =============================================================================
# DEFENSE WORLD TEMPLATES
# =============================================================================

def _defense_threat_assessment(rng, difficulty):
    """Threat level assessment based on intelligence indicators."""
    sigint_confidence = round(rng.uniform(0.3, 0.95), 2)
    humint_confidence = round(rng.uniform(0.2, 0.9), 2)
    imagery_confirms = rng.choice([True, False])
    force_movement = rng.choice([True, False])
    comms_increase = round(rng.uniform(1.0, 5.0), 1)
    days_to_readiness = rng.randint(1, 30)

    multi_source = sigint_confidence > 0.7 and humint_confidence > 0.6 and imagery_confirms
    threat_level = "critical" if multi_source and force_movement else (
        "high" if (sigint_confidence > 0.7 or humint_confidence > 0.7) and force_movement else (
            "elevated" if comms_increase > 3 else "moderate"))

    problem = (f"Intel: SIGINT confidence {sigint_confidence}, HUMINT confidence {humint_confidence}, "
               f"imagery {'confirms' if imagery_confirms else 'inconclusive'}, "
               f"force movement {'detected' if force_movement else 'none'}, "
               f"comms {comms_increase}x baseline. Assess threat.")
    steps = [
        f"SIGINT assessment: {sigint_confidence} confidence {'high reliability' if sigint_confidence > 0.7 else 'moderate'}",
        f"HUMINT corroboration: {humint_confidence} {'confirms SIGINT' if humint_confidence > 0.6 else 'inconclusive'}",
        f"Imagery intelligence: {'confirms force posture change' if imagery_confirms else 'no change detected'}",
        f"Force movement indicators: {'active repositioning detected' if force_movement else 'static posture'}",
        f"Communications analysis: {comms_increase}x baseline {'significant increase' if comms_increase > 3 else 'normal variation'}",
        f"Multi-source convergence: {'YES - high confidence assessment' if multi_source else 'partial - moderate confidence'}",
        f"Timeline estimate: {days_to_readiness} days to operational readiness",
        f"Threat level: {threat_level.upper()}",
    ]
    answer = (f"Threat level: {threat_level.upper()}. "
              f"{'Multi-source confirmed - recommend elevated FPCON.' if multi_source else 'Continue monitoring.'} "
              f"Estimated {days_to_readiness} days to readiness.")
    ground_truth = {"correct": True, "key_insight": f"threat_{threat_level}",
                    "threat_level": threat_level, "multi_source_confirmed": multi_source}
    return problem, steps, answer, ground_truth


def _defense_logistics_sustainment(rng, difficulty):
    """Military logistics sustainment calculation."""
    personnel = rng.randint(500, 10000)
    days_operation = rng.randint(7, 90)
    water_l_per_day = round(rng.uniform(8, 15), 1)
    food_kg_per_day = round(rng.uniform(1.5, 3.0), 1)
    fuel_l_per_vehicle_day = rng.randint(50, 300)
    vehicles = rng.randint(50, 500)
    ammo_kg_per_day = round(rng.uniform(0.5, 5.0), 1)

    total_water = round(personnel * water_l_per_day * days_operation)
    total_food = round(personnel * food_kg_per_day * days_operation)
    total_fuel = fuel_l_per_vehicle_day * vehicles * days_operation
    total_ammo = round(personnel * ammo_kg_per_day * days_operation)
    total_tonnage = round((total_water + total_fuel) / 1000 + total_food / 1000 + total_ammo / 1000)
    convoy_capacity_t = rng.randint(100, 500)
    convoys_needed = -(-total_tonnage // convoy_capacity_t)

    problem = (f"Sustain {personnel} personnel for {days_operation} days. "
               f"Water: {water_l_per_day}L/person/day, food: {food_kg_per_day}kg/person/day, "
               f"fuel: {fuel_l_per_vehicle_day}L/vehicle/day ({vehicles} vehicles), "
               f"ammo: {ammo_kg_per_day}kg/person/day. Convoy capacity: {convoy_capacity_t}t.")
    steps = [
        f"Water requirement: {personnel} × {water_l_per_day}L × {days_operation}d = {total_water:,}L",
        f"Food requirement: {personnel} × {food_kg_per_day}kg × {days_operation}d = {total_food:,}kg",
        f"Fuel requirement: {vehicles} × {fuel_l_per_vehicle_day}L × {days_operation}d = {total_fuel:,}L",
        f"Ammunition: {personnel} × {ammo_kg_per_day}kg × {days_operation}d = {total_ammo:,}kg",
        f"Total tonnage: ~{total_tonnage:,}t",
        f"Convoys required: {total_tonnage}t / {convoy_capacity_t}t = {convoys_needed} convoys",
        f"Logistics throughput: {convoys_needed} convoys over {days_operation} days = {round(convoys_needed/max(1,days_operation)*7, 1)}/week",
        f"Critical path: {'fuel' if total_fuel > total_water else 'water'} is heaviest class of supply",
    ]
    answer = (f"Total sustainment: {total_tonnage:,}t requiring {convoys_needed} convoys. "
              f"Critical supply: {'fuel' if total_fuel > total_water else 'water'}. "
              f"Rate: {round(convoys_needed/max(1,days_operation)*7, 1)} convoys/week.")
    ground_truth = {"correct": True, "key_insight": "sustainment_calculation",
                    "total_tonnage": total_tonnage, "convoys_needed": convoys_needed}
    return problem, steps, answer, ground_truth


def _defense_radar_detection(rng, difficulty):
    """Radar detection probability and coverage analysis."""
    rcs_sqm = round(rng.uniform(0.01, 50.0), 3)
    range_km = rng.randint(10, 500)
    radar_power_kw = rng.randint(10, 1000)
    noise_factor = round(rng.uniform(1.5, 8.0), 1)
    clutter_db = round(rng.uniform(-5, 20), 1)
    altitude_m = rng.randint(50, 15000)

    # Simplified detection probability
    snr_approx = round(10 * (2.0 + rcs_sqm / 10 - range_km / 100 - noise_factor / 5 + radar_power_kw / 200), 1)
    detection_prob = min(0.99, max(0.05, round(1 / (1 + 2.71828 ** (-snr_approx / 5)), 2)))
    stealth = rcs_sqm < 0.1
    low_altitude = altitude_m < 200

    problem = (f"Target: RCS {rcs_sqm}m², range {range_km}km, altitude {altitude_m}m. "
               f"Radar: {radar_power_kw}kW, noise factor {noise_factor}, clutter {clutter_db}dB. "
               f"Calculate detection probability.")
    steps = [
        f"Target RCS: {rcs_sqm}m² {'very low observable (stealth)' if stealth else 'conventional'}",
        f"Range factor: {range_km}km {'beyond typical detection' if range_km > 300 else 'within envelope'}",
        f"Altitude: {altitude_m}m {'terrain masking possible' if low_altitude else 'clear line of sight'}",
        f"Radar power: {radar_power_kw}kW, noise factor: {noise_factor}",
        f"SNR estimate: ~{snr_approx}dB",
        f"Clutter environment: {clutter_db}dB {'severe' if clutter_db > 10 else 'moderate' if clutter_db > 5 else 'benign'}",
        f"Detection probability: {detection_prob*100:.0f}%",
        f"{'Low-altitude gap exploitation possible' if low_altitude else 'Standard detection envelope'}",
    ]
    answer = (f"Detection probability: {detection_prob*100:.0f}%. "
              f"{'Low detectability due to stealth profile.' if stealth else ''}"
              f"{'Terrain masking reduces effective coverage.' if low_altitude else ''} "
              f"{'Recommend sensor fusion for improvement.' if detection_prob < 0.5 else ''}")
    ground_truth = {"correct": True, "key_insight": "detection_probability",
                    "detection_prob": detection_prob, "stealth": stealth}
    return problem, steps, answer, ground_truth


def _defense_mission_planning(rng, difficulty):
    """Mission planning risk/reward analysis."""
    objective_value = rng.randint(50, 100)  # strategic value 0-100
    force_ratio = round(rng.uniform(0.5, 5.0), 1)  # friendly:enemy
    terrain_advantage = rng.choice(["favorable", "neutral", "unfavorable"])
    intel_quality = rng.choice(["high", "moderate", "low"])
    weather = rng.choice(["clear", "overcast", "adverse"])
    surprise = rng.choice([True, False])

    terrain_mod = {"favorable": 1.3, "neutral": 1.0, "unfavorable": 0.7}[terrain_advantage]
    intel_mod = {"high": 1.2, "moderate": 1.0, "low": 0.8}[intel_quality]
    effective_ratio = round(force_ratio * terrain_mod * intel_mod * (1.2 if surprise else 1.0), 1)
    success_prob = min(0.95, max(0.1, round(1 - 1 / (1 + effective_ratio), 2)))
    risk_acceptable = success_prob > 0.6 and objective_value > 60

    problem = (f"Mission: objective value {objective_value}/100, force ratio {force_ratio}:1, "
               f"terrain {terrain_advantage}, intel quality {intel_quality}, "
               f"weather {weather}, surprise {'available' if surprise else 'lost'}. Assess viability.")
    steps = [
        f"Objective value: {objective_value}/100 {'high-value target' if objective_value > 70 else 'moderate value'}",
        f"Raw force ratio: {force_ratio}:1 {'favorable' if force_ratio > 2 else 'marginal' if force_ratio > 1 else 'unfavorable'}",
        f"Terrain modifier: {terrain_advantage} → ×{terrain_mod}",
        f"Intel modifier: {intel_quality} quality → ×{intel_mod}",
        f"Surprise factor: {'×1.2 (surprise achieved)' if surprise else '×1.0 (no surprise)'}",
        f"Effective force ratio: {effective_ratio}:1",
        f"Success probability: {success_prob*100:.0f}%",
        f"Risk-reward: {'ACCEPTABLE - execute' if risk_acceptable else 'UNACCEPTABLE - defer or reinforce'}",
    ]
    answer = (f"{'EXECUTE - acceptable risk' if risk_acceptable else 'DEFER - risk exceeds threshold'}. "
              f"Success probability: {success_prob*100:.0f}%, effective ratio {effective_ratio}:1.")
    ground_truth = {"correct": True, "key_insight": "mission_viable" if risk_acceptable else "mission_defer",
                    "success_prob": success_prob, "risk_acceptable": risk_acceptable}
    return problem, steps, answer, ground_truth


def _defense_comms_security(rng, difficulty):
    """Communications security assessment and crypto recommendation."""
    classification = rng.choice(["UNCLASSIFIED", "CONFIDENTIAL", "SECRET", "TOP_SECRET"])
    medium = rng.choice(["HF_radio", "satellite", "fiber", "tactical_radio", "mesh_network"])
    range_km = rng.randint(1, 5000)
    intercept_risk = rng.choice(["high", "medium", "low"])
    key_age_days = rng.randint(1, 90)
    users = rng.randint(5, 500)

    needs_type1 = classification in ("SECRET", "TOP_SECRET")
    key_expired = key_age_days > 30 if needs_type1 else key_age_days > 90
    adequate_security = not key_expired and (needs_type1 or intercept_risk == "low")

    problem = (f"Communications: {classification} traffic over {medium}, range {range_km}km, "
               f"intercept risk {intercept_risk}, key age {key_age_days} days, {users} users. "
               f"Assess COMSEC posture.")
    steps = [
        f"Classification: {classification} → {'Type-1 crypto required' if needs_type1 else 'commercial crypto acceptable'}",
        f"Medium: {medium} {'inherently vulnerable' if medium in ('HF_radio', 'tactical_radio') else 'relatively secure'}",
        f"Intercept threat: {intercept_risk} {'mandates enhanced protection' if intercept_risk == 'high' else ''}",
        f"Key management: {key_age_days} days old {'EXPIRED - rekey immediately' if key_expired else 'within policy'}",
        f"User count: {users} {'large key distribution challenge' if users > 100 else 'manageable'}",
        f"COMSEC assessment: {'INADEQUATE' if not adequate_security else 'ADEQUATE'}",
        f"Recommendation: {'immediate rekey' if key_expired else 'maintain current posture'}",
        f"Consider: {'TRANSEC overlay for HF' if medium == 'HF_radio' else 'standard procedures'}",
    ]
    answer = (f"COMSEC: {'INADEQUATE - rekey required' if not adequate_security else 'ADEQUATE'}. "
              f"{classification} traffic on {medium} {'requires Type-1 crypto' if needs_type1 else 'acceptable with current crypto'}. "
              f"{'Key age exceeded - rotate immediately.' if key_expired else ''}")
    ground_truth = {"correct": True, "key_insight": "comsec_inadequate" if not adequate_security else "comsec_adequate",
                    "adequate": adequate_security, "needs_type1": needs_type1, "key_expired": key_expired}
    return problem, steps, answer, ground_truth



# ---------------------------------------------------------------------------
# Problem templates mapping world -> list of generator functions
# ---------------------------------------------------------------------------

PROBLEM_TEMPLATES: Dict[str, List[Callable]] = {
    "healthcare": [
        _healthcare_dosage_calc,
        _healthcare_triage,
        _healthcare_lab_interpretation,
        _healthcare_drug_interaction,
        _healthcare_ventilator,
        _healthcare_ecg_interpretation,
    ],
    "finance": [
        _finance_portfolio_risk,
        _finance_loan_default,
        _finance_valuation_dcf,
        _finance_fraud_detection,
        _finance_options_pricing,
    ],
    "coding": [
        _coding_complexity,
        _coding_bug_diagnosis,
        _coding_system_design,
        _coding_refactoring,
        _coding_database_query,
    ],
    "cybersecurity": [
        _cyber_incident_response,
        _cyber_vuln_assessment,
        _cyber_network_forensics,
        _cyber_access_control,
        _cyber_malware_analysis,
    ],
    "manufacturing": [
        _manufacturing_quality_control,
        _manufacturing_oee,
        _manufacturing_predictive_maintenance,
        _manufacturing_root_cause,
        _manufacturing_capacity_planning,
    ],
    "supplychain": [
        _supplychain_inventory_optimization,
        _supplychain_logistics_routing,
    ],
}

# Add defense if functions exist
try:
    PROBLEM_TEMPLATES["defense"] = [
        _defense_threat_assessment,
        _defense_logistics_sustainment,
        _defense_radar_detection,
        _defense_mission_planning,
        _defense_comms_security,
    ]
except NameError:
    pass


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def generate_cot(world: str, rng: Any, tick: int, difficulty: str = "medium") -> dict:
    """Generate a chain-of-thought reasoning trace for the given world.

    Args:
        world: Domain name (healthcare, finance, coding, cybersecurity, etc.)
        rng: random.Random instance for deterministic generation
        tick: Sequence number for record ID generation
        difficulty: 'easy' (2-3 steps), 'medium' (4-5 steps), 'hard' (6-8 steps)

    Returns:
        Dict with format, record_id, metadata, problem, reasoning, answer, ground_truth
    """
    # Get problem generators for this world (fallback to healthcare)
    generators = PROBLEM_TEMPLATES.get(world, PROBLEM_TEMPLATES.get("healthcare", []))
    if not generators:
        generators = PROBLEM_TEMPLATES["healthcare"]

    # Pick a random generator and generate the problem
    generator = rng.choice(generators)
    problem, steps_raw, answer, ground_truth = generator(rng, difficulty)

    # Determine number of steps based on difficulty
    num_steps = _pick_num_steps(rng, difficulty)

    # Trim or pad steps to match desired count
    if len(steps_raw) > num_steps:
        steps_raw = steps_raw[:num_steps]
    elif len(steps_raw) < num_steps:
        # Pad with summary steps
        while len(steps_raw) < num_steps:
            steps_raw.append(f"Confirming analysis: the evidence supports the conclusion.")

    # Generate monotonically increasing confidence scores
    confidences = _generate_confidence_scores(rng, len(steps_raw))

    # Build reasoning trace
    reasoning = []
    for i, (step_text, conf) in enumerate(zip(steps_raw, confidences), 1):
        reasoning.append({
            "step": i,
            "thought": step_text,
            "confidence": round(conf, 3),
        })

    return {
        "format": "chain_of_thought",
        "record_id": f"cot_{tick:06d}_{world}_{rng.randint(0, 99999):05d}",
        "metadata": {
            "world": world,
            "difficulty": difficulty,
            "reasoning_steps": len(reasoning),
            "requires_domain_knowledge": True,
            "answer_type": "decision",
        },
        "problem": problem,
        "reasoning": reasoning,
        "answer": answer,
        "ground_truth": ground_truth,
    }
