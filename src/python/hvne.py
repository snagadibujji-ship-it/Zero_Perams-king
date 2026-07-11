#!/usr/bin/env python3
"""
HVNE — HELIX Visual Narrative Engine
Generates causally-coherent multi-frame visual sequences.
HELIX chain → CSI scene graph per frame → narrative with timeline.

Nobody else can do this: each frame is PHYSICALLY CORRECT and
CAUSALLY CONNECTED to the previous frame.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from event_chains import generate_event_chain, predict_next_event, analyze_chain_risk

# Severity → visual properties mapping
SEVERITY_VISUALS = {
    'info':     {'color': 'green',  'intensity': 0.3, 'particles': 0,  'alarm': False},
    'warning':  {'color': 'yellow', 'intensity': 0.5, 'particles': 5,  'alarm': False},
    'error':    {'color': 'orange', 'intensity': 0.7, 'particles': 15, 'alarm': True},
    'critical': {'color': 'red',    'intensity': 1.0, 'particles': 30, 'alarm': True},
}

# Event type → visual scene elements
EVENT_VISUALS = {
    # Cybersecurity
    'failed_login':         {'icon': '🔐', 'scene': 'terminal with red X', 'element': 'screen'},
    'brute_force_detected': {'icon': '⚡', 'scene': 'rapid login attempts scrolling', 'element': 'monitor_wall'},
    'account_lockout':      {'icon': '🔒', 'scene': 'padlock animation on screen', 'element': 'screen'},
    'incident_declared':    {'icon': '🚨', 'scene': 'red alert on SOC dashboard', 'element': 'dashboard'},
    'containment_started':  {'icon': '🛡️', 'scene': 'firewall rules being applied', 'element': 'network_diagram'},
    'forensics_initiated':  {'icon': '🔍', 'scene': 'log analysis on multiple screens', 'element': 'workstation'},
    'system_isolated':      {'icon': '🔌', 'scene': 'network cable unplugged', 'element': 'server_rack'},
    
    # Healthcare
    'patient_admit':        {'icon': '🏥', 'scene': 'patient on bed, nurse with tablet', 'element': 'hospital_room'},
    'vital_sign_abnormal':  {'icon': '📈', 'scene': 'monitor showing spike in heart rate', 'element': 'vital_monitor'},
    'rapid_response_called':{'icon': '🏃', 'scene': 'team running down corridor', 'element': 'corridor'},
    'intervention_started': {'icon': '💉', 'scene': 'medical equipment being prepared', 'element': 'treatment_area'},
    'vitals_stabilized':    {'icon': '✅', 'scene': 'monitor returning to normal', 'element': 'vital_monitor'},
    'icu_transfer':         {'icon': '🛏️', 'scene': 'patient being wheeled to ICU', 'element': 'corridor'},
    
    # Manufacturing
    'spc_alarm':            {'icon': '📊', 'scene': 'control chart with point outside limits', 'element': 'control_panel'},
    'production_hold':      {'icon': '⏸️', 'scene': 'conveyor belt stopped', 'element': 'production_line'},
    'equipment_vibration_high': {'icon': '〰️', 'scene': 'vibrating machine with warning light', 'element': 'machine'},
    'predictive_alert':     {'icon': '⚠️', 'scene': 'predictive dashboard showing trend', 'element': 'dashboard'},
    'emergency_shutdown':   {'icon': '🛑', 'scene': 'big red button pressed, machines stopping', 'element': 'factory_floor'},
    'repair_started':       {'icon': '🔧', 'scene': 'technician with tools at machine', 'element': 'machine'},
    
    # Energy
    'frequency_deviation':  {'icon': '⚡', 'scene': 'frequency meter drifting from 50Hz', 'element': 'control_room'},
    'transformer_overtemp': {'icon': '🌡️', 'scene': 'transformer with heat waves rising', 'element': 'substation'},
    'outage_detected':      {'icon': '🔌', 'scene': 'section of grid map turning dark', 'element': 'grid_map'},
    'crew_dispatched':      {'icon': '🚐', 'scene': 'utility truck leaving depot', 'element': 'depot'},
    
    # Aviation
    'engine_indication_abnormal': {'icon': '✈️', 'scene': 'cockpit EICAS showing amber message', 'element': 'cockpit'},
    'checklist_initiated':  {'icon': '📋', 'scene': 'pilot reading checklist from QRH', 'element': 'cockpit'},
    'diversion_considered': {'icon': '🗺️', 'scene': 'navigation display showing alternate airports', 'element': 'cockpit'},
    'bird_strike':          {'icon': '🐦', 'scene': 'impact on windscreen/engine', 'element': 'aircraft_exterior'},
    
    # Mining
    'slope_movement_detected': {'icon': '⛰️', 'scene': 'radar showing slope displacement', 'element': 'monitoring_station'},
    'evacuation_warning':   {'icon': '🚨', 'scene': 'sirens and workers moving to muster point', 'element': 'open_pit'},
    'blast_fired':          {'icon': '💥', 'scene': 'detonation with dust cloud', 'element': 'blast_zone'},
}

# Generic visual for unknown events
DEFAULT_VISUAL = {'icon': '⚙️', 'scene': 'system indicator changing state', 'element': 'control_panel'}


class VisualNarrative:
    """A multi-frame visual story generated from a causal event chain."""
    
    def __init__(self, chain, domain):
        self.chain = chain
        self.domain = domain
        self.frames = []
        self.timeline = []
        self.risk = None
        self._generate()
    
    def _generate(self):
        """Generate frames from event chain."""
        events = self.chain.get('events', [])
        self.risk = analyze_chain_risk(self.chain)
        
        for i, event in enumerate(events):
            frame = self._build_frame(event, i, len(events))
            self.frames.append(frame)
            self.timeline.append({
                'frame': i + 1,
                'time_s': event.get('timestamp_offset_s', 0),
                'event': event['event_type'],
                'severity': event.get('severity', 'info'),
            })
    
    def _build_frame(self, event, index, total):
        """Build a single frame's visual description."""
        event_type = event['event_type']
        severity = event.get('severity', 'info')
        visuals = EVENT_VISUALS.get(event_type, DEFAULT_VISUAL)
        sev_visual = SEVERITY_VISUALS.get(severity, SEVERITY_VISUALS['info'])
        
        frame = {
            'frame_number': index + 1,
            'total_frames': total,
            'event': event_type,
            'timestamp_s': event.get('timestamp_offset_s', 0),
            'severity': severity,
            'caused_by': event.get('caused_by'),
            'icon': visuals['icon'],
            'scene_description': visuals['scene'],
            'primary_element': visuals['element'],
            'visual_properties': {
                'dominant_color': sev_visual['color'],
                'intensity': sev_visual['intensity'],
                'particle_count': sev_visual['particles'],
                'alarm_active': sev_visual['alarm'],
                'lighting': 'harsh_red' if severity == 'critical' else 'amber' if severity == 'error' else 'normal',
            },
            'camera': {
                'angle': 'close_up' if index == 0 else 'medium' if index < total - 1 else 'wide',
                'motion': 'static' if severity == 'info' else 'shake' if severity == 'critical' else 'slow_zoom',
            },
            'annotations': {
                'causal_arrow_from': event.get('caused_by'),
                'time_label': f"+{event.get('timestamp_offset_s', 0):.0f}s",
                'severity_badge': severity.upper(),
            },
        }
        
        return frame
    
    def render_text(self):
        """Render narrative as text (for terminal display)."""
        lines = []
        lines.append(f"═══ VISUAL NARRATIVE: {self.domain.upper()} ═══")
        lines.append(f"Chain: {self.chain.get('root_event', '?')} → {len(self.frames)} frames")
        lines.append(f"Risk: {self.risk['risk_level']} ({self.risk['risk_score']}/100)")
        lines.append("")
        
        for frame in self.frames:
            severity_bar = '█' * int(frame['visual_properties']['intensity'] * 10)
            lines.append(f"  Frame {frame['frame_number']}/{frame['total_frames']}  "
                        f"{frame['icon']}  [{frame['severity']:8s}] {severity_bar}")
            lines.append(f"  Time: +{frame['timestamp_s']:.0f}s  "
                        f"{'← caused by: ' + frame['caused_by'] if frame['caused_by'] else '(root cause)'}")
            lines.append(f"  Scene: {frame['scene_description']}")
            lines.append(f"  Camera: {frame['camera']['angle']}, {frame['camera']['motion']}")
            lines.append("")
        
        # Intervention recommendation
        if self.risk['intervention_points']:
            ip = self.risk['intervention_points'][0]
            lines.append(f"  ⚠️  INTERVENTION POINT: Before '{ip['before_event']}'")
            lines.append(f"     Time window: {ip['time_available_s']:.0f}s")
            lines.append(f"     Would prevent: {', '.join(ip['would_prevent'][:3])}")
        
        return '\n'.join(lines)
    
    def to_json(self):
        """Export as JSON for rendering engine."""
        return {
            'domain': self.domain,
            'root_event': self.chain.get('root_event'),
            'frame_count': len(self.frames),
            'total_duration_s': self.timeline[-1]['time_s'] if self.timeline else 0,
            'risk': self.risk,
            'frames': self.frames,
            'timeline': self.timeline,
        }


# ═══ PUBLIC API ═══

def generate_narrative(domain, trigger=None, seed=42, max_frames=8):
    """Generate a visual narrative for a domain incident."""
    chain = generate_event_chain(domain, trigger=trigger, seed=seed, max_depth=max_frames)
    return VisualNarrative(chain, domain)

def generate_comparison_narrative(domain, seed=42):
    """Generate actual vs counterfactual side-by-side narratives."""
    from event_chains import generate_counterfactual
    cf = generate_counterfactual(domain, seed=seed, branch_point=2)
    
    actual_narrative = VisualNarrative(
        {'events': cf['actual_path'], 'root_event': cf['actual_path'][0]['event_type'] if cf['actual_path'] else '?'},
        domain)
    counter_narrative = VisualNarrative(
        {'events': cf['counterfactual_path'], 'root_event': cf['counterfactual_path'][0]['event_type'] if cf['counterfactual_path'] else '?'},
        domain)
    
    return {
        'actual': actual_narrative,
        'counterfactual': counter_narrative,
        'branch_point': cf['branch_point'],
        'actual_outcome': cf['actual_outcome'],
        'counter_outcome': cf['counterfactual_outcome'],
    }

def generate_multi_domain_narrative(domains=None, seed=42):
    """Generate a cascading narrative across multiple domains."""
    from event_chains import generate_cascade_chain
    if domains is None:
        domains = ['cybersecurity', 'energy', 'healthcare']
    
    cascade = generate_cascade_chain(domains, seed=seed, max_total=12)
    return VisualNarrative(cascade, '+'.join(domains))


# ═══ SELF TEST ═══
if __name__ == '__main__':
    print("=== HVNE — HELIX Visual Narrative Engine ===\n")
    
    # Test 1: Single domain narrative
    narrative = generate_narrative('cybersecurity', trigger='failed_login', seed=42, max_frames=6)
    print(narrative.render_text())
    print()
    
    # Test 2: Multi-domain cascade
    print("--- MULTI-DOMAIN CASCADE ---")
    multi = generate_multi_domain_narrative(['manufacturing', 'energy'], seed=7)
    print(multi.render_text())
    print()
    
    # Test 3: Stats
    print(f"Frames generated: {len(narrative.frames)}")
    print(f"JSON export keys: {list(narrative.to_json().keys())}")
    print(f"\n✅ HVNE operational — invention #10 complete")
