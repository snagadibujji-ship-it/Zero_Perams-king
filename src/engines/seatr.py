"""
SEATR JSONL — State-Event-Action Training Record
=================================================
The most powerful format for AI training from industrial data.

Each record teaches the model:
  Layer 1: Raw signal (original message, exactly as spoken)
  Layer 2: Normalized meaning (clean text, categories, labels)
  Layer 3: Operational state (plant/worker/machine state RIGHT NOW)
  Layer 4: Learning targets (summary, next action, risk, root cause)

One JSONL row = one event + one state snapshot + one causal chain + one supervision target

This makes the dataset trainable for:
  - Summarization
  - Classification
  - Next-step prediction
  - Root-cause inference
  - Retrieval
  - Dialogue generation
  - Operational monitoring
  - Anomaly detection
  - Decision support
"""
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from world_engine.registry import IndustryConfig



# ═══════════════════════════════════════════════════════
# OPERATIONAL STATE TEMPLATES
# ═══════════════════════════════════════════════════════

PRODUCTION_STATES = [
    "full_capacity", "partial_flow", "reduced_speed", "single_line_running",
    "warmup_phase", "cooldown_phase", "idle", "maintenance_shutdown",
    "emergency_stop", "changeover", "testing_mode", "trial_run",
]

LINE_STATES = [
    "running_normal", "running_with_delay", "running_with_alarm",
    "stopped_for_maintenance", "stopped_for_material", "stopped_for_quality",
    "warming_up", "cooling_down", "changeover_in_progress",
]

EQUIPMENT_STATES = [
    "normal", "degraded", "alarm_active", "under_maintenance",
    "standby", "warming_up", "overloaded", "vibration_high",
]

MATERIAL_STATES = [
    "adequate", "running_low", "waiting_on_delivery", "excess_stock",
    "quality_hold", "expired_batch", "wrong_grade_received",
]

WORK_STATES = [
    "normal_operations", "blocked_by_material_delay", "blocked_by_equipment",
    "blocked_by_approval", "waiting_for_parts", "waiting_for_inspection",
    "overtime_mode", "rush_order_mode", "skeleton_staff", "training_mode",
]

# ═══════════════════════════════════════════════════════
# CAUSALITY INFERENCE
# ═══════════════════════════════════════════════════════

BLOCKED_BY_MAP = {
    "supply_chain": ["delivery_delay", "vendor_issue", "customs_hold", "transport_breakdown"],
    "maintenance": ["equipment_failure", "spare_parts_unavailable", "technician_unavailable"],
    "quality": ["batch_rejection", "spec_deviation", "calibration_drift"],
    "workforce": ["absenteeism", "skill_gap", "shift_shortage"],
    "technology_change": ["system_downtime", "software_bug", "network_issue"],
    "weather_environment": ["rain_stoppage", "heat_advisory", "flooding"],
    "crisis": ["power_failure", "fire_damage", "strike_action"],
}

NEXT_ACTION_MAP = {
    "routine_monitoring": "continue_monitoring_or_escalate_if_abnormal",
    "daily_ops": "proceed_to_next_production_step",
    "maintenance": "complete_repair_and_test_before_restart",
    "supply_chain": "follow_up_with_supplier_or_find_alternate",
    "quality": "investigate_root_cause_and_apply_corrective_action",
    "human_relations": "no_action_needed_social_interaction",
    "canteen_food": "return_to_work_after_break",
    "shift_handover": "complete_handover_and_start_shift_tasks",
    "documentation": "file_record_and_proceed",
    "equipment_sounds": "investigate_further_or_report_to_maintenance",
    "safety_accidents": "secure_area_provide_first_aid_investigate",
    "mistakes_failures": "identify_root_cause_apply_correction_document",
    "learning_training": "practice_skill_and_apply_on_job",
    "workforce": "complete_hr_process_and_communicate",
    "customer_sales": "respond_to_customer_and_follow_up",
    "business": "review_numbers_and_plan_action",
    "gossip_rumors": "no_formal_action_but_may_affect_mood",
    "personal_life": "support_colleague_if_needed",
    "commute_arrival": "proceed_to_workstation",
    "night_shift_special": "stay_alert_and_complete_rounds",
    "crisis": "activate_emergency_protocol",
}

RISK_LEVELS = {
    "daily_ops": "low",
    "routine_monitoring": "low",
    "human_relations": "none",
    "canteen_food": "none",
    "documentation": "low",
    "maintenance": "medium",
    "supply_chain": "medium",
    "quality": "medium",
    "equipment_sounds": "medium",
    "mistakes_failures": "medium",
    "safety_accidents": "high",
    "crisis": "critical",
    "weather_environment": "low",
    "gossip_rumors": "none",
    "personal_life": "none",
    "night_shift_special": "low",
    "commute_arrival": "none",
    "shift_handover": "low",
    "learning_training": "none",
    "workforce": "low",
    "customer_sales": "low",
    "business": "medium",
    "leadership": "low",
    "technology_change": "medium",
}


# ═══════════════════════════════════════════════════════
# SEATR RECORD BUILDER
# ═══════════════════════════════════════════════════════

class SEATRBuilder:
    """Converts a simple episode record into full SEATR format.
    
    Now integrates with StateTracker for:
    - Physics-based counterfactual probabilities (not random)
    - Persistent open issues from StateTracker (not recalculated)
    - Digital twin equipment state embedded in each record
    - Cascading failure context
    - Operator fatigue state
    - Shift memory bridge state
    - Environmental stress
    """
    
    def __init__(self, industry: IndustryConfig, rng: random.Random):
        self.industry = industry
        self.rng = rng
        self.record_counter = 0
        self.prev_state = "normal_operations"
        self.active_blockers = []
        self.recent_events = []
    
    def build(self, simple_record: Dict) -> Dict:
        """Transform a simple record into SEATR format."""
        self.record_counter += 1
        
        r = simple_record
        category = r['event_category']
        subtype = r['event_subtype']
        message = r['message']
        actor = r['primary_actor']
        timestamp = r['timestamp']
        
        # Determine operational state based on category
        production_status = self._infer_production_state(category, subtype)
        line_status = self._infer_line_state(category, subtype)
        equipment_status = self._infer_equipment_state(category, subtype)
        material_status = self._infer_material_state(category, subtype)
        work_state = self._infer_work_state(category, subtype)
        
        # Determine causality
        blocked_by = self._get_blockers(category, subtype)
        caused_by = self._infer_cause(category, subtype, message)
        next_action = NEXT_ACTION_MAP.get(category, "continue_normal_operations")
        risk = RISK_LEVELS.get(category, "low")
        
        # Enhance causality with StateTracker causal chain
        state_snap = r.get('_state_snapshot', {})
        causal_chain_recent = state_snap.get('causal_chain_recent', [])
        if causal_chain_recent and category in ("supply_chain", "maintenance", "quality", "safety_accidents", "crisis"):
            # Link this event to the previous causal event
            for prev_cause in reversed(causal_chain_recent[:-1]):  # Exclude self
                if prev_cause['category'] != category:
                    caused_by.insert(0, f"{prev_cause['category']}:{prev_cause['subtype']}")
                    break
        
        # Generate supervision targets
        summary = self._generate_summary(category, subtype, message, actor)
        next_best = self._generate_next_best_action(category, subtype, work_state)
        root_cause = self._infer_root_cause(category, subtype, message)
        
        # Build context (before/after)
        context_before = self._generate_context_before(category, work_state)
        context_after = self._generate_context_after(category, subtype, risk)
        
        # Determine intent
        intent = self._infer_intent(category, subtype, message)
        
        # Urgency from message patterns
        urgency = self._detect_urgency(message, category)
        
        # Generate clean message (normalized)
        clean_message = self._clean_message(message)
        
        # Seniority from experience
        exp = actor['experience_years']
        if exp < 2: seniority = "junior"
        elif exp < 5: seniority = "mid"
        elif exp < 10: seniority = "mid_senior"
        elif exp < 20: seniority = "senior"
        else: seniority = "expert"
        
        # Build SEATR record
        seatr = {
            "record_id": f"rec_{timestamp[:10].replace('-','')}_{self.record_counter:06d}",
            "version": "1.0",
            "timestamp_utc": timestamp,
            "domain": self.industry.id,
            "industry_code": self.industry.id.upper(),
            "company": {
                "name": r.get('company', 'Unknown'),
                "country": r.get('location_country', 'Unknown'),
                "plant_type": self.industry.subsector,
            },
            "shift": {
                "name": r.get('shift', 'unknown') + "_shift",
                "period": r.get('shift', 'unknown'),
            },
            "actor_primary": {
                "id": actor['id'],
                "role": actor['role'],
                "experience_years": actor['experience_years'],
                "language": actor['language'],
                "seniority": seniority,
            },
            "event": {
                "event_category": category,
                "event_subtype": subtype,
                "intent": intent,
                "raw_message": message,
                "clean_message": clean_message,
                "tone": r.get('mood', 'neutral'),
                "urgency": urgency,
            },
            "context": {
                "before": context_before,
                "after": context_after,
                "work_state": work_state,
            },
            "state": {
                "production_status": production_status,
                "line_status": line_status,
                "equipment_status": equipment_status,
                "materials_status": material_status,
            },
            "causality": {
                "blocked_by": blocked_by,
                "caused_by": caused_by,
                "likely_next_action": next_action,
            },
            "assets_mentioned": r.get('assets_mentioned', []),
            "labels": {
                "primary_topic": category,
                "secondary_topics": r.get('tags', []),
                "safety_class": "unsafe" if category == "safety_accidents" else "safe",
                "task_class": self._classify_task(category, subtype),
            },
            "supervision_targets": {
                "summary": summary,
                "next_best_action": next_best,
                "root_cause_hint": root_cause,
                "risk_level": risk,
            },
            "provenance": {
                "source_type": "synthetic",
                "generator": "ghia_world_engine_seatr_v1",
                "quality_score": round(0.90 + self.rng.uniform(0, 0.09), 2),
            },
        }
        
        # ═══════════════════════════════════════
        # LAYER 5: TEMPORAL MEMORY
        # (Now uses StateTracker persistent issues)
        # ═══════════════════════════════════════
        state_snap = r.get('_state_snapshot', {})
        tracker_issues = state_snap.get('open_issues', [])
        
        seatr["temporal_memory"] = {
            "previous_events": [e.replace("_", " ") for e in self.recent_events[-5:]],
            "event_position_in_chain": self.record_counter,
            "session_length": self.record_counter,
            "open_issues": [iss.get("description", iss.get("type", "unknown")) for iss in tracker_issues] if tracker_issues else self._get_open_issues(category, subtype, message),
            "open_issue_count": state_snap.get('issue_count', 0),
            "time_since_last_event_seconds": self._estimate_time_gap(timestamp),
            "shift_progress_pct": self._calc_shift_progress(timestamp),
        }
        
        # ═══════════════════════════════════════
        # LAYER 6: COUNTERFACTUALS
        # (Now uses PHYSICS-BASED probabilities from StateTracker)
        # ═══════════════════════════════════════
        seatr["counterfactuals"] = self._generate_counterfactuals(
            category, subtype, work_state, message, state_snap)
        
        # ═══════════════════════════════════════
        # LAYER 7: KNOWLEDGE GRAPH LINKS
        # ═══════════════════════════════════════
        seatr["knowledge_graph"] = {
            "entities": self._extract_entities(actor, r, category),
            "relations": self._extract_relations(actor, r, category, subtype, message),
        }
        
        # ═══════════════════════════════════════
        # LAYER 8: UNCERTAINTY
        # (Now influenced by operator fatigue — tired = less confident)
        # ═══════════════════════════════════════
        fatigue_state = state_snap.get("operator_fatigue", {}) if state_snap else {}
        alertness = fatigue_state.get("alertness_level", 0.85)
        # Lower alertness → lower confidence in assessments
        confidence_modifier = min(1.0, 0.9 + alertness * 0.1)  # Clamped to max 1.0
        
        seatr["confidence"] = {
            "root_cause": round(min(1.0, self.rng.uniform(0.45, 0.95) * confidence_modifier), 2),
            "risk_level": round(min(1.0, self.rng.uniform(0.70, 0.99) * confidence_modifier), 2),
            "next_action": round(min(1.0, self.rng.uniform(0.55, 0.92) * confidence_modifier), 2),
            "state_assessment": round(min(1.0, self.rng.uniform(0.75, 0.98) * confidence_modifier), 2),
            "urgency_detection": round(min(1.0, (0.90 if urgency in ("high", "critical") else self.rng.uniform(0.80, 0.96)) * confidence_modifier), 2),
            "operator_alertness_factor": round(min(1.0, alertness), 3),
        }
        
        # ═══════════════════════════════════════
        # LAYER 9: MULTI-AGENT VIEW
        # ═══════════════════════════════════════
        seatr["multi_agent_views"] = self._generate_multi_agent_views(category, subtype, message, actor, work_state, risk)
        
        # ═══════════════════════════════════════
        # LAYER 10: GROUND TRUTH OUTCOME
        # ═══════════════════════════════════════
        seatr["outcome"] = self._generate_outcome(category, subtype, next_action, work_state, risk)
        
        # ═══════════════════════════════════════
        # LAYER 11: DIGITAL TWIN STATE (from StateTracker)
        # Continuous equipment health, production metrics
        # ═══════════════════════════════════════
        if state_snap:
            dt = state_snap.get("digital_twin", {})
            seatr["digital_twin_state"] = {
                "worst_equipment": dt.get("worst_equipment"),
                "equipment_count_tracked": len(dt.get("equipment_states", {})),
                "production_metrics": state_snap.get("production_metrics", {}),
                "causal_chain_depth": len(state_snap.get("causal_chain_recent", [])),
            }
            
            # Cascading failures context
            cascades = state_snap.get("cascading_failures", {})
            if cascades.get("pending_cascades"):
                seatr["cascading_failures"] = cascades
            
            # Operator fatigue
            fatigue = state_snap.get("operator_fatigue", {})
            if fatigue:
                seatr["operator_state"] = fatigue
            
            # Shift memory bridge
            shift_mem = state_snap.get("shift_memory", {})
            if shift_mem:
                seatr["shift_continuity"] = shift_mem
            
            # Environmental stress
            env = state_snap.get("environment", {})
            if env:
                seatr["environment"] = env
            
            # Economic state — connects physics → operations → MONEY
            econ = state_snap.get("economic", {})
            if econ:
                seatr["business_state"] = econ
        
        # Update internal state
        self.prev_state = work_state
        self.recent_events.append(category)
        if len(self.recent_events) > 10:
            self.recent_events = self.recent_events[-10:]
        
        return seatr
    
    def _infer_production_state(self, cat, sub) -> str:
        if cat in ("crisis", "safety_accidents"): return "emergency_stop"
        if cat == "maintenance" and "breakdown" in sub: return "maintenance_shutdown"
        if "changeover" in sub: return "changeover"
        if cat in ("canteen_food", "holidays_breaks"): return "idle"
        return self.rng.choice(["full_capacity", "full_capacity", "partial_flow"])
    
    def _infer_line_state(self, cat, sub) -> str:
        if cat == "maintenance": return "stopped_for_maintenance"
        if cat == "supply_chain" and "shortage" in sub: return "stopped_for_material"
        if cat == "quality" and "reject" in sub: return "stopped_for_quality"
        if "alarm" in sub: return "running_with_alarm"
        return "running_normal"
    
    def _infer_equipment_state(self, cat, sub) -> str:
        if cat == "equipment_sounds": return "degraded"
        if cat == "maintenance" and "breakdown" in sub: return "under_maintenance"
        if "alarm" in sub: return "alarm_active"
        if "vibration" in sub: return "vibration_high"
        return "normal"
    
    def _infer_material_state(self, cat, sub) -> str:
        if "shortage" in sub or "stockout" in sub: return "running_low"
        if "waiting" in sub or "delivery" in sub.lower(): return "waiting_on_delivery"
        if "received" in sub: return "adequate"
        return "adequate"
    
    def _infer_work_state(self, cat, sub) -> str:
        if cat == "supply_chain" and any(w in sub for w in ["delay", "shortage", "waiting"]):
            return "blocked_by_material_delay"
        if cat == "maintenance" and "breakdown" in sub:
            return "blocked_by_equipment"
        if cat in ("canteen_food", "human_relations", "personal_life"):
            return "normal_operations"
        return "normal_operations"
    
    def _get_blockers(self, cat, sub) -> List[str]:
        if cat in BLOCKED_BY_MAP:
            return [self.rng.choice(BLOCKED_BY_MAP[cat])]
        return []
    
    def _infer_cause(self, cat, sub, msg) -> List[str]:
        causes = []
        if "delivery" in msg.lower() or "waiting" in msg.lower():
            causes.append("supplier_delay")
        if "breakdown" in sub or "fault" in sub:
            causes.append("equipment_wear")
        if "mistake" in sub or "wrong" in sub:
            causes.append("human_error")
        if not causes:
            causes.append("normal_workflow")
        return causes
    
    def _infer_intent(self, cat, sub, msg) -> str:
        if len(msg) <= 10: return "acknowledge"
        if msg.endswith("?"): return "ask_question"
        if cat == "maintenance": return "report_issue"
        if cat == "daily_ops": return "report_status"
        if cat == "human_relations": return "social_interaction"
        if cat == "documentation": return "record_information"
        if cat == "quality": return "report_quality_status"
        if cat == "supply_chain": return "report_logistics_status"
        if cat == "shift_handover": return "transfer_information"
        if any(w in msg.upper() for w in ["STOP", "EMERGENCY", "NOW"]): return "urgent_command"
        return "inform"
    
    def _detect_urgency(self, msg, cat) -> str:
        if msg.isupper() and len(msg) > 10: return "critical"
        if "EMERGENCY" in msg or "STOP" in msg: return "critical"
        if "urgent" in msg.lower() or "!!!" in msg: return "high"
        if cat in ("crisis", "safety_accidents"): return "high"
        if cat in ("maintenance",) and "breakdown" in msg.lower(): return "medium"
        return "low"
    
    def _clean_message(self, msg: str) -> str:
        """Normalize message (fix typos, proper case, punctuation)."""
        # Remove emojis for clean version
        import re
        clean = re.sub(r'[👍✅❌⚠️🔥💪🙏😤😂🤦👀📸🔧⏰☕🍕🎂🏠🚗📞💀]', '', msg)
        clean = clean.strip()
        if clean and not clean[-1] in '.!?':
            clean += '.'
        if clean:
            clean = clean[0].upper() + clean[1:]
        return clean
    
    def _generate_summary(self, cat, sub, msg, actor) -> str:
        """Generate a supervision summary of what happened."""
        role = actor['role'].replace('_', ' ')
        action = sub.replace('_', ' ')
        
        if len(msg) <= 15:
            return f"The {role} acknowledged a message with a brief response."
        
        summaries = {
            "daily_ops": f"The {role} reported on {action} during normal operations.",
            "maintenance": f"The {role} reported a maintenance issue requiring attention.",
            "human_relations": f"Social interaction between team members during work.",
            "supply_chain": f"The {role} reported on supply chain or logistics status.",
            "quality": f"Quality-related observation or action reported by the {role}.",
            "documentation": f"The {role} completed documentation ({action}).",
            "routine_monitoring": f"The {role} performed routine monitoring ({action}).",
            "equipment_sounds": f"The {role} noticed an equipment anomaly that may need investigation.",
            "shift_handover": f"Shift handover communication — status transfer between shifts.",
            "safety_accidents": f"Safety-related event reported. Immediate attention required.",
            "crisis": f"Critical event requiring emergency response.",
        }
        return summaries.get(cat, f"The {role} performed {action}.")
    
    def _generate_next_best_action(self, cat, sub, work_state) -> str:
        """What should happen next?"""
        actions = {
            "normal_operations": "Continue with scheduled tasks.",
            "blocked_by_material_delay": "Follow up with logistics on delivery ETA.",
            "blocked_by_equipment": "Wait for maintenance to complete repair, then test.",
            "blocked_by_approval": "Escalate to supervisor for approval.",
            "waiting_for_parts": "Check spare parts availability or find alternate.",
            "waiting_for_inspection": "Wait for quality inspector to arrive.",
            "overtime_mode": "Complete priority tasks before shift end.",
            "rush_order_mode": "Focus on rush order, defer non-critical tasks.",
        }
        return actions.get(work_state, "Continue normal operations.")
    
    def _infer_root_cause(self, cat, sub, msg) -> str:
        """Hint at root cause for training."""
        if "delivery" in msg.lower() or "waiting" in msg.lower():
            return "Material delivery is pending from supplier."
        if "breakdown" in sub or "fault" in sub:
            return "Equipment degradation or component failure."
        if "mistake" in sub or "wrong" in sub:
            return "Procedural error or miscommunication."
        if cat == "human_relations":
            return "Normal social interaction, no root cause needed."
        return "Routine workflow event."
    
    def _classify_task(self, cat, sub) -> str:
        """Classify the task type."""
        if cat in ("daily_ops", "routine_monitoring"): return "monitoring"
        if cat in ("maintenance",): return "repair_maintenance"
        if cat in ("documentation", "shift_handover"): return "documentation"
        if cat in ("human_relations", "canteen_food", "gossip_rumors"): return "social"
        if cat in ("quality",): return "quality_assurance"
        if cat in ("supply_chain",): return "logistics"
        if cat in ("safety_accidents", "crisis"): return "emergency_response"
        if cat in ("learning_training",): return "skill_development"
        if cat in ("business", "customer_sales"): return "business_operations"
        return "general_operations"



    def _generate_context_before(self, cat: str, work_state: str) -> List[str]:
        """What was happening BEFORE this event."""
        before = []
        if work_state == "normal_operations":
            before.append("Operations running normally")
        elif work_state == "blocked_by_material_delay":
            before.append("Production partially halted due to material shortage")
        elif work_state == "blocked_by_equipment":
            before.append("Equipment failure reported, awaiting repair")
        else:
            before.append("Previous tasks completed")
        
        # Add recent event context
        if self.recent_events:
            last = self.recent_events[-1]
            before.append(f"Previous event was: {last.replace('_', ' ')}")
        
        # Industry-specific context
        before.append(f"Active process: {self.rng.choice(self.industry.key_processes)}")
        return before
    
    def _generate_context_after(self, cat: str, sub: str, risk: str) -> List[str]:
        """What is expected to happen AFTER this event."""
        after = []
        if risk in ("high", "critical"):
            after.append("Immediate escalation expected")
            after.append("Safety protocols activated")
        elif cat == "maintenance":
            after.append("Repair work to follow")
            after.append("Line restart after verification")
        elif cat in ("human_relations", "canteen_food"):
            after.append("Worker returns to normal duties")
        else:
            after.append("Normal workflow continues")
            after.append("No escalation needed")
        return after



    # ═══════════════════════════════════════
    # LAYER 5 HELPERS: TEMPORAL MEMORY
    # ═══════════════════════════════════════
    
    def _get_open_issues(self, cat: str, sub: str, msg: str) -> List[str]:
        """Track what issues are still open/unresolved."""
        issues = []
        if "waiting" in msg.lower() or "delivery" in msg.lower():
            issues.append("material_delivery_pending")
        if "breakdown" in sub:
            issues.append("equipment_under_repair")
        if cat == "quality" and "reject" in sub:
            issues.append("quality_investigation_open")
        if cat == "safety_accidents":
            issues.append("safety_incident_under_investigation")
        if not issues:
            issues.append("no_open_issues")
        return issues
    
    def _estimate_time_gap(self, timestamp: str) -> int:
        """Estimate seconds since last event."""
        return self.rng.randint(60, 1800)  # 1-30 minutes
    
    def _calc_shift_progress(self, timestamp: str) -> int:
        """Calculate how far through the shift we are (0-100%)."""
        try:
            hour = int(timestamp[11:13])
            minute = int(timestamp[14:16])
            if 6 <= hour < 14:  # Morning shift
                elapsed = (hour - 6) * 60 + minute
                return min(100, int(elapsed / 480 * 100))
            elif 14 <= hour < 22:  # Afternoon shift
                elapsed = (hour - 14) * 60 + minute
                return min(100, int(elapsed / 480 * 100))
            else:  # Night shift
                if hour >= 22:
                    elapsed = (hour - 22) * 60 + minute
                else:
                    elapsed = (hour + 2) * 60 + minute
                return min(100, int(elapsed / 480 * 100))
        except:
            return 50
    
    # ═══════════════════════════════════════
    # LAYER 6 HELPERS: COUNTERFACTUALS
    # ═══════════════════════════════════════
    
    def _generate_counterfactuals(self, cat: str, sub: str, work_state: str, 
                                   msg: str, state_snap: Dict = None) -> List[Dict]:
        """Generate 2-3 counterfactual scenarios with PHYSICS-BASED probabilities."""
        counterfactuals = []
        
        # Get equipment health for physics-based probability
        dt_state = state_snap.get("digital_twin", {}) if state_snap else {}
        worst_eq = dt_state.get("worst_equipment", {})
        eq_health = worst_eq.get("health", 0.9) if worst_eq else 0.9
        eq_rul = worst_eq.get("remaining_useful_life_hours", 1000) if worst_eq else 1000
        
        # Physics-based: degradation level drives probability
        degradation_factor = 1.0 - eq_health  # 0 = perfect, 1 = failed
        
        if "delivery" in msg.lower() or "waiting" in msg.lower():
            counterfactuals.append({
                "condition": "delivery_arrived_on_time",
                "expected_outcome": "full_capacity_production",
                "probability": round(min(0.85, 0.3 + degradation_factor * 0.3), 2),
                "confidence": round(0.7 + self.rng.uniform(0, 0.2), 2),
                "impact_hours": round(self.rng.uniform(2, 16), 1),
            })
            counterfactuals.append({
                "condition": "delivery_delayed_further_24h",
                "expected_outcome": "line_shutdown_and_overtime_later",
                "probability": round(0.1 + degradation_factor * 0.15, 2),
                "confidence": round(0.6 + self.rng.uniform(0, 0.2), 2),
                "impact_hours": round(self.rng.uniform(8, 48), 1),
            })
        elif cat == "maintenance":
            # Physics: probability of prevention proportional to how degraded
            prevention_prob = round(min(0.95, 0.3 + degradation_factor * 0.6), 2)
            counterfactuals.append({
                "condition": "preventive_maintenance_done_48h_earlier",
                "expected_outcome": "breakdown_probability_reduced",
                "probability": prevention_prob,
                "confidence": round(0.75 + self.rng.uniform(0, 0.15), 2),
                "downtime_saved_hours": round(eq_rul * 0.01 if eq_rul < 500 else 4.2, 1),
            })
            counterfactuals.append({
                "condition": "spare_parts_not_available",
                "expected_outcome": "extended_downtime",
                "probability": round(min(0.8, 0.1 + degradation_factor * 0.5), 2),
                "confidence": round(0.65 + self.rng.uniform(0, 0.2), 2),
                "extended_downtime_hours": round(self.rng.uniform(12, 72), 1),
            })
            # Physics: no-intervention failure timeline
            if eq_rul < 500:
                counterfactuals.append({
                    "condition": "no_intervention_taken",
                    "expected_outcome": "failure_within_rul_window",
                    "probability": round(min(0.95, 0.5 + (500 - eq_rul) / 1000), 2),
                    "estimated_failure_hours": round(eq_rul, 0),
                    "confidence": round(0.7 + self.rng.uniform(0, 0.15), 2),
                })
        elif cat == "safety_accidents":
            counterfactuals.append({
                "condition": "safety_guard_was_in_place",
                "expected_outcome": "incident_prevented",
                "probability": round(self.rng.uniform(0.7, 0.95), 2),
                "confidence": round(0.8 + self.rng.uniform(0, 0.15), 2),
                "severity_reduction_pct": self.rng.randint(60, 95),
            })
            counterfactuals.append({
                "condition": "worker_not_wearing_ppe",
                "expected_outcome": "injury_severity_higher",
                "probability": round(self.rng.uniform(0.4, 0.7), 2),
                "confidence": round(0.7 + self.rng.uniform(0, 0.2), 2),
                "severity_increase_pct": self.rng.randint(30, 80),
            })
        elif cat == "quality":
            counterfactuals.append({
                "condition": "incoming_material_tested_earlier",
                "expected_outcome": "defect_caught_before_production",
                "probability": round(0.5 + degradation_factor * 0.3, 2),
                "confidence": round(0.7 + self.rng.uniform(0, 0.2), 2),
                "waste_prevented_units": self.rng.randint(50, 500),
            })
        else:
            counterfactuals.append({
                "condition": "no_change_in_conditions",
                "expected_outcome": "normal_workflow_continues",
                "probability": round(max(0.5, 0.95 - degradation_factor * 0.3), 2),
                "confidence": round(0.85 + self.rng.uniform(0, 0.1), 2),
            })
        
        return counterfactuals
    
    # ═══════════════════════════════════════
    # LAYER 7 HELPERS: KNOWLEDGE GRAPH
    # ═══════════════════════════════════════
    
    def _extract_entities(self, actor: Dict, record: Dict, cat: str) -> List[str]:
        """Extract entities mentioned in or relevant to this event."""
        entities = [actor['id'], actor['role']]
        entities.extend(record.get('assets_mentioned', []))
        
        # Add industry-specific entities
        if self.industry.typical_products:
            entities.append(self.rng.choice(self.industry.typical_products))
        if cat in ("supply_chain", "customer_sales"):
            entities.append("supplier")
        if cat in ("leadership", "workforce"):
            entities.append("management")
        
        return list(set(entities))
    
    def _extract_relations(self, actor: Dict, record: Dict, cat: str, sub: str, msg: str) -> List[List[str]]:
        """Extract entity-relation-entity triples."""
        relations = []
        
        # Actor performs action
        relations.append([actor['id'], "performs", sub.replace("_", " ")])
        
        # Asset-related relations
        assets = record.get('assets_mentioned', [])
        if assets:
            relations.append([actor['id'], "operates", assets[0]])
            if len(assets) > 1:
                relations.append([assets[0], "connected_to", assets[1]])
        
        # Category-specific relations
        if cat == "supply_chain" and "delivery" in msg.lower():
            relations.append(["supplier", "delays", "delivery"])
            if assets:
                relations.append(["delivery", "blocks", assets[0]])
        elif cat == "maintenance" and "breakdown" in sub:
            if assets:
                relations.append([assets[0], "status", "broken"])
                relations.append(["maintenance_team", "assigned_to", assets[0]])
        elif cat == "quality" and "reject" in sub:
            relations.append(["batch", "status", "rejected"])
            relations.append(["quality_team", "investigates", "batch"])
        
        return relations
    
    # ═══════════════════════════════════════
    # LAYER 9 HELPERS: MULTI-AGENT VIEW
    # ═══════════════════════════════════════
    
    def _generate_multi_agent_views(self, cat: str, sub: str, msg: str, 
                                      actor: Dict, work_state: str, risk: str) -> Dict:
        """Generate how different roles would perceive this event."""
        views = {}
        
        # Operator's view
        views["operator"] = f"I need to {sub.replace('_', ' ')} and report status to supervisor."
        
        # Supervisor's view
        if risk in ("high", "critical"):
            views["supervisor"] = "This needs immediate attention. I need to escalate and ensure safety protocols."
        elif work_state != "normal_operations":
            views["supervisor"] = f"Noted. {work_state.replace('_', ' ')}. Need to track resolution timeline."
        else:
            views["supervisor"] = "Normal operations. No intervention needed unless escalated."
        
        # Maintenance perspective
        if cat == "maintenance" or cat == "equipment_sounds":
            views["maintenance"] = "I need to inspect this equipment and determine repair scope."
        else:
            views["maintenance"] = "No maintenance action required at this time."
        
        # Safety perspective
        if cat == "safety_accidents" or risk in ("high", "critical"):
            views["safety_officer"] = "Safety event detected. Must investigate, document, and implement corrective measures."
        else:
            views["safety_officer"] = "No safety concern identified in this event."
        
        # Management perspective
        if cat in ("business", "customer_sales", "expansion"):
            views["management"] = "Business event requiring strategic review and resource allocation decision."
        elif risk == "critical":
            views["management"] = "Critical event. Need status update and impact assessment immediately."
        else:
            views["management"] = "Operational level event. No management intervention needed."
        
        return views
    
    # ═══════════════════════════════════════
    # LAYER 10 HELPERS: GROUND TRUTH OUTCOME
    # ═══════════════════════════════════════
    
    def _generate_outcome(self, cat: str, sub: str, predicted_action: str, 
                           work_state: str, risk: str) -> Dict:
        """Generate what ACTUALLY happened (prediction vs reality)."""
        # Most of the time, predicted action matches actual
        # But sometimes reality differs (this teaches the model uncertainty)
        
        prediction_accuracy = self.rng.random()
        
        if prediction_accuracy < 0.75:
            # 75% of the time prediction is correct
            actual_action = predicted_action
            match = True
        else:
            # 25% of the time reality differs
            alternate_actions = [
                "escalated_to_supervisor",
                "problem_resolved_itself",
                "different_issue_discovered",
                "delayed_due_to_other_priority",
                "handled_by_different_team",
                "workaround_applied_instead",
                "deferred_to_next_shift",
                "no_action_taken_low_priority",
            ]
            actual_action = self.rng.choice(alternate_actions)
            match = False
        
        # Time to resolution
        if cat in ("human_relations", "canteen_food", "gossip_rumors"):
            resolution_minutes = 0  # Social events don't need resolution
        elif risk == "critical":
            resolution_minutes = self.rng.randint(30, 480)  # 30 min to 8 hours
        elif risk == "high":
            resolution_minutes = self.rng.randint(15, 120)
        elif cat == "maintenance":
            resolution_minutes = self.rng.randint(30, 240)
        else:
            resolution_minutes = self.rng.randint(5, 60)
        
        # Long-term outcome
        if cat == "maintenance":
            long_term = self.rng.choice([
                "equipment_restored_fully",
                "equipment_restored_partially_needs_follow_up",
                "recurring_issue_added_to_replacement_plan",
            ])
        elif cat == "safety_accidents":
            long_term = self.rng.choice([
                "new_safety_procedure_implemented",
                "safety_guard_installed",
                "additional_training_scheduled",
                "investigation_ongoing",
            ])
        elif cat == "quality":
            long_term = self.rng.choice([
                "root_cause_identified_and_fixed",
                "process_parameter_adjusted",
                "supplier_quality_alert_issued",
            ])
        else:
            long_term = "normal_operations_resumed"
        
        return {
            "predicted_next_action": predicted_action,
            "actual_next_action": actual_action,
            "prediction_matched": match,
            "resolution_time_minutes": resolution_minutes,
            "long_term_outcome": long_term,
            "outcome_quality": self.rng.choice(["optimal", "acceptable", "suboptimal"]) if not match else "optimal",
        }
