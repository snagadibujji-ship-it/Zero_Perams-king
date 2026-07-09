"""
Tool-use / ReAct format generator for Hybrid-HybridAI.

Generates synthetic training records that follow the ReAct (Reason + Act) pattern:
    thought -> action -> observation (repeating)

Each record contains:
- A set of available tools scoped to a specific world domain
- A task description
- A full trajectory of thought/action/observation steps
- A final answer summarizing the outcome

Supports 10+ worlds with world-specific tool registries and task templates.
Deterministic output given same (rng, tick, world, difficulty) inputs.

Usage:
    import random
    rng = random.Random(42)
    record = generate_tool_use("cybersecurity", rng, tick=1, difficulty="hard")
"""

from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# WORLD_TOOLS: dict mapping world -> list of tool definitions
# Each tool has: name, description, parameters (with types)
# ---------------------------------------------------------------------------

WORLD_TOOLS: Dict[str, List[Dict[str, Any]]] = {
    "cybersecurity": [
        {"name": "query_siem", "description": "Query SIEM for log events", "parameters": {"query": "string", "time_range": "string", "limit": "integer"}},
        {"name": "check_ioc", "description": "Check indicator against threat intel", "parameters": {"indicator": "string", "type": "string"}},
        {"name": "isolate_host", "description": "Isolate a host from network", "parameters": {"hostname": "string", "reason": "string"}},
        {"name": "scan_vulnerability", "description": "Run vulnerability scan on target", "parameters": {"target": "string", "scan_type": "string"}},
        {"name": "block_ip", "description": "Block IP address at firewall", "parameters": {"ip": "string", "duration": "string", "reason": "string"}},
        {"name": "analyze_malware", "description": "Submit file hash for malware analysis", "parameters": {"hash": "string", "sandbox": "string"}},
    ],
    "healthcare": [
        {"name": "lookup_patient", "description": "Retrieve patient record by ID", "parameters": {"patient_id": "string", "fields": "string"}},
        {"name": "check_drug_interaction", "description": "Check for drug-drug interactions", "parameters": {"drug_a": "string", "drug_b": "string"}},
        {"name": "order_lab", "description": "Order laboratory test for patient", "parameters": {"patient_id": "string", "test_code": "string", "priority": "string"}},
        {"name": "review_imaging", "description": "Retrieve imaging study results", "parameters": {"patient_id": "string", "study_type": "string", "date": "string"}},
        {"name": "consult_specialist", "description": "Request specialist consultation", "parameters": {"patient_id": "string", "specialty": "string", "reason": "string"}},
        {"name": "prescribe_medication", "description": "Prescribe medication to patient", "parameters": {"patient_id": "string", "medication": "string", "dosage": "string", "frequency": "string"}},
    ],
    "finance": [
        {"name": "check_position", "description": "Check current portfolio position", "parameters": {"symbol": "string", "account": "string"}},
        {"name": "run_risk_model", "description": "Run VaR or stress test model", "parameters": {"portfolio": "string", "model": "string", "horizon": "string"}},
        {"name": "execute_trade", "description": "Execute a trade order", "parameters": {"symbol": "string", "side": "string", "quantity": "integer", "order_type": "string"}},
        {"name": "check_compliance", "description": "Verify trade against compliance rules", "parameters": {"trade_id": "string", "rule_set": "string"}},
        {"name": "query_market_data", "description": "Get real-time or historical market data", "parameters": {"symbol": "string", "interval": "string", "lookback": "string"}},
        {"name": "calculate_margin", "description": "Calculate margin requirements", "parameters": {"portfolio": "string", "scenario": "string"}},
    ],
    "coding": [
        {"name": "run_tests", "description": "Execute test suite", "parameters": {"path": "string", "filter": "string", "verbose": "string"}},
        {"name": "read_file", "description": "Read contents of a source file", "parameters": {"path": "string", "start_line": "integer", "end_line": "integer"}},
        {"name": "search_codebase", "description": "Search codebase for pattern", "parameters": {"query": "string", "file_type": "string", "max_results": "integer"}},
        {"name": "execute_command", "description": "Execute shell command", "parameters": {"command": "string", "working_dir": "string"}},
        {"name": "check_lint", "description": "Run linter on file or directory", "parameters": {"path": "string", "fix": "string"}},
        {"name": "deploy", "description": "Deploy application to environment", "parameters": {"service": "string", "environment": "string", "version": "string"}},
    ],
    "manufacturing": [
        {"name": "check_sensor", "description": "Read sensor value from equipment", "parameters": {"sensor_id": "string", "equipment": "string"}},
        {"name": "adjust_parameter", "description": "Adjust process parameter", "parameters": {"parameter": "string", "value": "string", "equipment": "string"}},
        {"name": "stop_line", "description": "Emergency stop production line", "parameters": {"line_id": "string", "reason": "string"}},
        {"name": "run_diagnostic", "description": "Run diagnostic test on equipment", "parameters": {"equipment": "string", "test_type": "string"}},
        {"name": "schedule_maintenance", "description": "Schedule maintenance window", "parameters": {"equipment": "string", "maintenance_type": "string", "date": "string"}},
        {"name": "query_production_log", "description": "Query production event logs", "parameters": {"line_id": "string", "time_range": "string", "event_type": "string"}},
    ],
}

# Additional worlds (continued)
WORLD_TOOLS["supplychain"] = [
    {"name": "check_inventory", "description": "Check inventory levels at location", "parameters": {"sku": "string", "warehouse": "string"}},
    {"name": "track_shipment", "description": "Track shipment status", "parameters": {"tracking_id": "string", "carrier": "string"}},
    {"name": "create_po", "description": "Create purchase order", "parameters": {"supplier": "string", "items": "string", "quantity": "integer", "urgency": "string"}},
    {"name": "query_forecast", "description": "Query demand forecast", "parameters": {"sku": "string", "horizon": "string", "region": "string"}},
    {"name": "alert_supplier", "description": "Send alert to supplier", "parameters": {"supplier_id": "string", "message": "string", "priority": "string"}},
    {"name": "route_shipment", "description": "Calculate optimal shipping route", "parameters": {"origin": "string", "destination": "string", "weight": "string"}},
]

WORLD_TOOLS["devops"] = [
    {"name": "check_service_health", "description": "Check health of a deployed service", "parameters": {"service": "string", "environment": "string"}},
    {"name": "view_logs", "description": "View application logs", "parameters": {"service": "string", "severity": "string", "time_range": "string"}},
    {"name": "scale_service", "description": "Scale service replicas", "parameters": {"service": "string", "replicas": "integer", "environment": "string"}},
    {"name": "rollback_deploy", "description": "Rollback to previous deployment", "parameters": {"service": "string", "version": "string"}},
    {"name": "run_pipeline", "description": "Trigger CI/CD pipeline", "parameters": {"repo": "string", "branch": "string", "stage": "string"}},
    {"name": "update_config", "description": "Update service configuration", "parameters": {"service": "string", "key": "string", "value": "string"}},
]

WORLD_TOOLS["legal"] = [
    {"name": "search_cases", "description": "Search legal case database", "parameters": {"query": "string", "jurisdiction": "string", "date_range": "string"}},
    {"name": "review_contract", "description": "Analyze contract clause", "parameters": {"contract_id": "string", "section": "string"}},
    {"name": "check_regulation", "description": "Check applicable regulations", "parameters": {"topic": "string", "jurisdiction": "string"}},
    {"name": "draft_clause", "description": "Draft contract clause", "parameters": {"clause_type": "string", "parameters": "string"}},
    {"name": "calculate_damages", "description": "Estimate potential damages", "parameters": {"case_id": "string", "model": "string"}},
    {"name": "file_document", "description": "File document with court system", "parameters": {"case_id": "string", "document_type": "string", "content": "string"}},
]

WORLD_TOOLS["energy"] = [
    {"name": "read_meter", "description": "Read smart meter data", "parameters": {"meter_id": "string", "interval": "string"}},
    {"name": "check_grid_status", "description": "Check power grid segment status", "parameters": {"segment_id": "string", "metric": "string"}},
    {"name": "dispatch_crew", "description": "Dispatch field crew to location", "parameters": {"location": "string", "issue_type": "string", "priority": "string"}},
    {"name": "adjust_generation", "description": "Adjust power generation output", "parameters": {"plant_id": "string", "target_mw": "string"}},
    {"name": "forecast_demand", "description": "Forecast energy demand", "parameters": {"region": "string", "horizon": "string"}},
    {"name": "toggle_breaker", "description": "Toggle circuit breaker remotely", "parameters": {"breaker_id": "string", "state": "string", "reason": "string"}},
]

WORLD_TOOLS["agriculture"] = [
    {"name": "check_soil_moisture", "description": "Read soil moisture sensor", "parameters": {"field_id": "string", "depth": "string"}},
    {"name": "get_weather_forecast", "description": "Get weather forecast for location", "parameters": {"location": "string", "days": "integer"}},
    {"name": "activate_irrigation", "description": "Activate irrigation system", "parameters": {"zone_id": "string", "duration_min": "integer", "flow_rate": "string"}},
    {"name": "analyze_crop_image", "description": "Analyze drone/satellite crop image", "parameters": {"field_id": "string", "image_date": "string", "analysis_type": "string"}},
    {"name": "apply_treatment", "description": "Schedule treatment application", "parameters": {"field_id": "string", "treatment": "string", "quantity": "string"}},
    {"name": "check_equipment", "description": "Check farm equipment status", "parameters": {"equipment_id": "string", "diagnostic": "string"}},
]

WORLD_TOOLS["customer_support"] = [
    {"name": "lookup_customer", "description": "Look up customer account", "parameters": {"customer_id": "string", "email": "string"}},
    {"name": "check_order_status", "description": "Check order status", "parameters": {"order_id": "string"}},
    {"name": "issue_refund", "description": "Issue refund for order", "parameters": {"order_id": "string", "amount": "string", "reason": "string"}},
    {"name": "create_ticket", "description": "Create support ticket", "parameters": {"customer_id": "string", "category": "string", "description": "string", "priority": "string"}},
    {"name": "check_product_availability", "description": "Check product stock", "parameters": {"product_id": "string", "location": "string"}},
    {"name": "send_notification", "description": "Send notification to customer", "parameters": {"customer_id": "string", "channel": "string", "message": "string"}},
]


# ---------------------------------------------------------------------------
# TASK_TEMPLATES: dict mapping world -> list of task scenarios
# Each scenario contains:
#   - task: description of the task
#   - trajectory: list of (type, content/tool/arguments) steps
#   - final_answer: summary of outcome
#   - tools_used: list of tool names used (subset of world tools)
# ---------------------------------------------------------------------------

TASK_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {}

TASK_TEMPLATES["cybersecurity"] = [
    {
        "task": "Investigate the alert: Multiple failed login attempts from IP 10.0.3.47 targeting domain admin accounts.",
        "tools_used": ["query_siem", "check_ioc", "isolate_host"],
        "trajectory": [
            {"type": "thought", "content": "I need to investigate this potential brute force attack. Let me check the SIEM for more context."},
            {"type": "action", "tool": "query_siem", "arguments": {"query": "src_ip=10.0.3.47 event_type=authentication", "time_range": "24h", "limit": 100}},
            {"type": "observation", "content": "Found 847 failed attempts across 12 accounts in 2 hours. All targeting *-admin accounts."},
            {"type": "thought", "content": "This is clearly automated. 847 attempts in 2h is about 7/min. Let me check if this IP is known malicious."},
            {"type": "action", "tool": "check_ioc", "arguments": {"indicator": "10.0.3.47", "type": "ip"}},
            {"type": "observation", "content": "IP is internal (workstation WS-MKTG-047). No prior alerts. Assigned to user j.smith."},
            {"type": "thought", "content": "Internal IP doing credential stuffing is suspicious - could be compromised workstation. Isolate immediately."},
            {"type": "action", "tool": "isolate_host", "arguments": {"hostname": "WS-MKTG-047", "reason": "Credential stuffing from internal host - possible compromise"}},
            {"type": "observation", "content": "Host isolated successfully. User j.smith notified."},
            {"type": "thought", "content": "Host isolated. Now I need to determine root cause - was this malware or insider threat?"},
        ],
        "final_answer": "Isolated compromised workstation WS-MKTG-047. Automated credential stuffing detected (847 attempts/2h). Escalated to Tier 2 for forensic analysis.",
    },
    {
        "task": "Analyze suspicious outbound traffic spike from server DB-PROD-02 to external IP 185.220.101.34.",
        "tools_used": ["query_siem", "check_ioc", "scan_vulnerability", "block_ip"],
        "trajectory": [
            {"type": "thought", "content": "Outbound traffic spike from a production DB server is alarming. Let me check what data is flowing."},
            {"type": "action", "tool": "query_siem", "arguments": {"query": "src_host=DB-PROD-02 dst_ip=185.220.101.34", "time_range": "6h", "limit": 50}},
            {"type": "observation", "content": "12GB transferred over port 443 in last 4 hours. Connection established at 02:14 UTC. Encrypted payload."},
            {"type": "thought", "content": "12GB exfiltration from DB server is critical. Let me check if the destination is a known threat."},
            {"type": "action", "tool": "check_ioc", "arguments": {"indicator": "185.220.101.34", "type": "ip"}},
            {"type": "observation", "content": "Known Tor exit node. Associated with APT29 infrastructure. Confidence: HIGH."},
            {"type": "thought", "content": "This is a confirmed data exfiltration to APT29 infra. Need to block and scan for the entry point."},
            {"type": "action", "tool": "block_ip", "arguments": {"ip": "185.220.101.34", "duration": "permanent", "reason": "Active data exfiltration to APT29 C2"}},
            {"type": "observation", "content": "IP blocked at perimeter firewall. Active connections terminated."},
            {"type": "thought", "content": "Now I need to check how they got in. Let me scan the server for vulnerabilities."},
            {"type": "action", "tool": "scan_vulnerability", "arguments": {"target": "DB-PROD-02", "scan_type": "full"}},
            {"type": "observation", "content": "Critical: CVE-2024-3094 (XZ backdoor) present. OpenSSH version vulnerable. Patch missing since March."},
            {"type": "thought", "content": "Root cause identified - unpatched XZ vulnerability. This is a P1 incident requiring immediate response."},
        ],
        "final_answer": "Confirmed data exfiltration (12GB) from DB-PROD-02 to APT29 infrastructure via Tor exit node. Root cause: CVE-2024-3094. Blocked C2, initiated P1 incident response.",
    },
    {
        "task": "Triage phishing email reported by user containing suspicious attachment invoice_Q4.pdf.exe.",
        "tools_used": ["analyze_malware", "query_siem", "block_ip"],
        "trajectory": [
            {"type": "thought", "content": "Double extension .pdf.exe is a classic social engineering trick. Let me analyze the file hash."},
            {"type": "action", "tool": "analyze_malware", "arguments": {"hash": "a1b2c3d4e5f6789012345678abcdef01", "sandbox": "windows10"}},
            {"type": "observation", "content": "Verdict: MALICIOUS. Family: Emotet. Behavior: drops payload from hxxp://evil.example[.]com/stage2.dll, establishes persistence via registry."},
            {"type": "thought", "content": "Confirmed Emotet dropper. Need to check if anyone else received this and if the C2 is active in our network."},
            {"type": "action", "tool": "query_siem", "arguments": {"query": "email_attachment_hash=a1b2c3d4e5f6789012345678abcdef01 OR dst_domain=evil.example.com", "time_range": "72h", "limit": 200}},
            {"type": "observation", "content": "Email delivered to 23 users. 4 users clicked attachment. No outbound connections to C2 domain detected yet."},
            {"type": "thought", "content": "4 users executed it but no C2 callback yet - might be sandbox-aware. Block the C2 preemptively."},
            {"type": "action", "tool": "block_ip", "arguments": {"ip": "198.51.100.44", "duration": "permanent", "reason": "Emotet C2 infrastructure - evil.example.com"}},
            {"type": "observation", "content": "IP and domain blocked at DNS and firewall layers. 23 email quarantine actions initiated."},
            {"type": "thought", "content": "C2 blocked and emails quarantined. The 4 machines that executed need forensic examination."},
        ],
        "final_answer": "Emotet dropper identified. Blocked C2 infrastructure, quarantined 23 emails. 4 endpoints require forensic analysis - no successful C2 callback detected.",
    },
    {
        "task": "Respond to ransomware encryption detected on file server FS-CORP-01.",
        "tools_used": ["query_siem", "isolate_host", "scan_vulnerability", "check_ioc", "block_ip"],
        "trajectory": [
            {"type": "thought", "content": "Ransomware on a file server is critical. I need to isolate immediately then investigate the attack chain."},
            {"type": "action", "tool": "isolate_host", "arguments": {"hostname": "FS-CORP-01", "reason": "Active ransomware encryption detected"}},
            {"type": "observation", "content": "Host isolated. Warning: 340 SMB connections forcibly terminated."},
            {"type": "thought", "content": "Isolated. Now let me trace how the ransomware got in - check lateral movement patterns."},
            {"type": "action", "tool": "query_siem", "arguments": {"query": "dst_host=FS-CORP-01 event_type=login success=true", "time_range": "48h", "limit": 50}},
            {"type": "observation", "content": "Unusual RDP login from WS-FIN-012 at 01:47 UTC using svc_backup account. No prior RDP from this source."},
            {"type": "thought", "content": "Lateral movement via compromised service account. Let me check the initial entry point workstation."},
            {"type": "action", "tool": "scan_vulnerability", "arguments": {"target": "WS-FIN-012", "scan_type": "compromise_assessment"}},
            {"type": "observation", "content": "Cobalt Strike beacon detected in memory. Initial infection via macro-enabled document opened 36h ago."},
            {"type": "thought", "content": "Full attack chain: phishing -> Cobalt Strike -> lateral movement -> ransomware. Check for C2."},
            {"type": "action", "tool": "check_ioc", "arguments": {"indicator": "cdn-update.azureedge-cdn.net", "type": "domain"}},
            {"type": "observation", "content": "Known Cobalt Strike C2 domain. Associated with FIN7 group. First seen: 2024-09."},
            {"type": "thought", "content": "Confirmed FIN7 operation. Must block C2 and isolate the initial compromise point."},
            {"type": "action", "tool": "block_ip", "arguments": {"ip": "203.0.113.99", "duration": "permanent", "reason": "FIN7 Cobalt Strike C2 - cdn-update.azureedge-cdn.net"}},
            {"type": "observation", "content": "Domain and IP blocked. DNS sinkhole configured."},
            {"type": "thought", "content": "Attack chain contained. Need to assess encryption damage and begin recovery from backups."},
        ],
        "final_answer": "Ransomware contained. Attack chain: phishing -> Cobalt Strike (FIN7) -> lateral movement via svc_backup -> encryption. Both hosts isolated, C2 blocked. Recovery from backups initiated.",
    },
]

TASK_TEMPLATES["healthcare"] = [
    {
        "task": "Patient P-4521 presents with chest pain and shortness of breath. Evaluate for acute coronary syndrome.",
        "tools_used": ["lookup_patient", "order_lab", "review_imaging"],
        "trajectory": [
            {"type": "thought", "content": "Chest pain with dyspnea requires urgent ACS workup. Let me review the patient's history first."},
            {"type": "action", "tool": "lookup_patient", "arguments": {"patient_id": "P-4521", "fields": "history,medications,allergies,vitals"}},
            {"type": "observation", "content": "Male, 58yo. Hx: HTN, DM2, hyperlipidemia. Meds: metformin, lisinopril, atorvastatin. BP: 158/94, HR: 102, SpO2: 94%. No drug allergies."},
            {"type": "thought", "content": "High-risk profile for ACS. Need troponin and ECG. SpO2 94% is concerning - may need supplemental O2."},
            {"type": "action", "tool": "order_lab", "arguments": {"patient_id": "P-4521", "test_code": "TROP_I_SERIAL", "priority": "STAT"}},
            {"type": "observation", "content": "Order placed. Initial troponin I: 0.89 ng/mL (normal <0.04). STAT ECG shows ST elevation in leads II, III, aVF."},
            {"type": "thought", "content": "Troponin markedly elevated and STEMI pattern in inferior leads. This is an acute MI. Need cardiology STAT."},
            {"type": "action", "tool": "review_imaging", "arguments": {"patient_id": "P-4521", "study_type": "echocardiogram", "date": "today"}},
            {"type": "observation", "content": "Bedside echo: inferior wall hypokinesis, EF estimated 40%. No pericardial effusion. RV function preserved."},
            {"type": "thought", "content": "Confirmed inferior STEMI with reduced EF. Cath lab activation is required immediately."},
        ],
        "final_answer": "Inferior STEMI confirmed. Troponin 0.89, ST elevation II/III/aVF, inferior hypokinesis on echo. Cath lab activated for emergent PCI. Started heparin and dual antiplatelet therapy.",
    },
    {
        "task": "Review medication reconciliation for patient P-8833 being started on warfarin. Check for interactions.",
        "tools_used": ["lookup_patient", "check_drug_interaction", "prescribe_medication"],
        "trajectory": [
            {"type": "thought", "content": "Before starting warfarin, I need to review current medications for dangerous interactions."},
            {"type": "action", "tool": "lookup_patient", "arguments": {"patient_id": "P-8833", "fields": "medications,diagnoses,labs"}},
            {"type": "observation", "content": "Female, 72yo. Meds: amiodarone 200mg daily, aspirin 81mg, omeprazole 20mg. Dx: AFib, GERD. INR baseline: 1.0, CrCl: 52mL/min."},
            {"type": "thought", "content": "Amiodarone is a major interaction with warfarin - it significantly increases INR. Need to check severity."},
            {"type": "action", "tool": "check_drug_interaction", "arguments": {"drug_a": "warfarin", "drug_b": "amiodarone"}},
            {"type": "observation", "content": "MAJOR interaction. Amiodarone inhibits CYP2C9 and CYP3A4. Warfarin dose should be reduced 30-50%. Requires close INR monitoring. Risk of major bleeding."},
            {"type": "thought", "content": "Must reduce starting dose. Standard is 5mg but with amiodarone and age 72, should start at 2.5mg with frequent INR checks."},
            {"type": "action", "tool": "prescribe_medication", "arguments": {"patient_id": "P-8833", "medication": "warfarin", "dosage": "2.5mg", "frequency": "once daily"}},
            {"type": "observation", "content": "Prescription created. Alert added: INR check in 3 days. Interaction warning documented in chart. Pharmacy notified."},
            {"type": "thought", "content": "Low dose initiated with monitoring plan. Patient needs education on bleeding signs and dietary vitamin K."},
        ],
        "final_answer": "Warfarin started at reduced dose (2.5mg) due to amiodarone interaction (CYP2C9 inhibition). INR monitoring scheduled every 3 days. Patient counseled on bleeding precautions.",
    },
    {
        "task": "Patient P-1197 with recurring headaches and new visual disturbances. Rule out space-occupying lesion.",
        "tools_used": ["lookup_patient", "review_imaging", "consult_specialist", "order_lab"],
        "trajectory": [
            {"type": "thought", "content": "New visual disturbances with headaches are red flags for intracranial pathology. Need neuroimaging urgently."},
            {"type": "action", "tool": "lookup_patient", "arguments": {"patient_id": "P-1197", "fields": "history,symptoms,vitals,neuro_exam"}},
            {"type": "observation", "content": "Female, 34yo. 6-week progressive headaches, worse in morning. New right homonymous hemianopia on exam. Papilledema present. No prior neuro history."},
            {"type": "thought", "content": "Papilledema and visual field deficit strongly suggest raised ICP and a lesion. MRI brain with contrast needed urgently."},
            {"type": "action", "tool": "review_imaging", "arguments": {"patient_id": "P-1197", "study_type": "MRI_brain_contrast", "date": "today"}},
            {"type": "observation", "content": "3.2cm enhancing mass in left occipital lobe with surrounding edema and midline shift of 4mm. Possible high-grade glioma vs metastasis."},
            {"type": "thought", "content": "Significant mass with edema and midline shift. Need neurosurgery consult and labs to rule out metastatic source."},
            {"type": "action", "tool": "order_lab", "arguments": {"patient_id": "P-1197", "test_code": "TUMOR_MARKERS_PANEL", "priority": "STAT"}},
            {"type": "observation", "content": "Labs ordered. CBC, CMP normal. CEA: 1.2 (normal), CA-125: normal, AFP: normal. No obvious primary malignancy markers."},
            {"type": "thought", "content": "Tumor markers negative suggests primary brain tumor rather than metastasis. Neurosurgery must evaluate for biopsy/resection."},
            {"type": "action", "tool": "consult_specialist", "arguments": {"patient_id": "P-1197", "specialty": "neurosurgery", "reason": "3.2cm left occipital mass with midline shift, possible high-grade glioma, needs surgical evaluation"}},
            {"type": "observation", "content": "Neurosurgery consult accepted. Dr. Patel will evaluate within 2 hours. Dexamethasone 10mg IV started for edema."},
            {"type": "thought", "content": "Patient stabilized on steroids, neurosurgery engaged. Will need stereotactic biopsy and likely resection planning."},
        ],
        "final_answer": "3.2cm left occipital mass identified with midline shift. Likely primary brain tumor (glioma). Steroids started, neurosurgery consulted for urgent biopsy/resection planning.",
    },
]

TASK_TEMPLATES["finance"] = [
    {
        "task": "Evaluate risk exposure for concentrated NVDA position in portfolio GROWTH-A1 ahead of earnings.",
        "tools_used": ["check_position", "run_risk_model", "query_market_data"],
        "trajectory": [
            {"type": "thought", "content": "Need to assess the concentration risk before earnings. Let me check the current position size."},
            {"type": "action", "tool": "check_position", "arguments": {"symbol": "NVDA", "account": "GROWTH-A1"}},
            {"type": "observation", "content": "NVDA: 15,000 shares at avg cost $425. Current price: $890. Position value: $13.35M. Portfolio weight: 34.2%."},
            {"type": "thought", "content": "34% concentration is well above our 20% limit. Need to model downside scenarios for earnings miss."},
            {"type": "action", "tool": "run_risk_model", "arguments": {"portfolio": "GROWTH-A1", "model": "earnings_stress", "horizon": "1d"}},
            {"type": "observation", "content": "Stress test results - NVDA earnings miss scenario: Portfolio VaR(95%): -$2.8M (7.2%). Max drawdown if -20% gap: -$4.1M. Margin call threshold breached at -15% move."},
            {"type": "thought", "content": "Margin call risk at -15% is unacceptable. Let me check options market for hedging costs."},
            {"type": "action", "tool": "query_market_data", "arguments": {"symbol": "NVDA", "interval": "options_chain", "lookback": "current"}},
            {"type": "observation", "content": "NVDA 30-day IV: 62% (vs 35% historical). Put spread $850/$800: $12.50 cost per contract. Collar $850P/$950C: net credit $1.20."},
            {"type": "thought", "content": "IV is elevated pre-earnings. Collar strategy gives free downside protection while capping upside. Recommend collar or partial trim."},
        ],
        "final_answer": "NVDA position at 34.2% exceeds concentration limit. Margin call risk at -15% move. Recommend collar strategy ($850P/$950C at net credit) or trim to 20% weight before earnings.",
    },
    {
        "task": "Execute rebalancing trade for fixed income portfolio BOND-Q2: reduce duration by selling long-dated treasuries.",
        "tools_used": ["check_position", "check_compliance", "execute_trade", "run_risk_model"],
        "trajectory": [
            {"type": "thought", "content": "Need to reduce duration exposure. Let me see what long-dated holdings we have."},
            {"type": "action", "tool": "check_position", "arguments": {"symbol": "TLT", "account": "BOND-Q2"}},
            {"type": "observation", "content": "TLT (20+ Year Treasury ETF): 50,000 shares. Market value: $4.85M. Duration contribution: 4.2 years of total 6.8yr portfolio duration."},
            {"type": "thought", "content": "TLT contributes 4.2yr of 6.8yr total. Selling half would bring duration to ~4.7yr. Check compliance first."},
            {"type": "action", "tool": "check_compliance", "arguments": {"trade_id": "PENDING-TLT-SELL-25K", "rule_set": "fixed_income_mandate"}},
            {"type": "observation", "content": "Compliance check PASSED. Resulting duration (4.7yr) within mandate range (3-7yr). No wash sale issues. Settlement: T+1."},
            {"type": "thought", "content": "Compliance approved. Let me execute the sell order as a limit to avoid market impact."},
            {"type": "action", "tool": "execute_trade", "arguments": {"symbol": "TLT", "side": "sell", "quantity": 25000, "order_type": "limit"}},
            {"type": "observation", "content": "Order placed: SELL 25,000 TLT @ limit $97.10. Order ID: FI-20240315-001. Status: WORKING. Estimated proceeds: $2.43M."},
            {"type": "thought", "content": "Order working. Let me verify the post-trade risk metrics look correct."},
            {"type": "action", "tool": "run_risk_model", "arguments": {"portfolio": "BOND-Q2", "model": "duration_analysis", "horizon": "post_trade"}},
            {"type": "observation", "content": "Post-trade duration: 4.68yr (target: <5yr). DV01 reduced from $68,000 to $47,200. Yield pickup: +12bps from reinvestment into short-end."},
            {"type": "thought", "content": "Duration successfully reduced below 5yr target. DV01 risk down 31%. Rebalancing objective achieved."},
        ],
        "final_answer": "Sold 25,000 TLT shares to reduce portfolio duration from 6.8yr to 4.68yr. DV01 reduced 31%. Compliance approved, order working. Proceeds to be reinvested in short-duration instruments.",
    },
    {
        "task": "Investigate unusual options activity in ACME Corp (ACME) ahead of unannounced merger. Check for insider trading signals.",
        "tools_used": ["query_market_data", "check_position", "check_compliance"],
        "trajectory": [
            {"type": "thought", "content": "Unusual options activity before M&A can indicate information leakage. Let me check the flow data."},
            {"type": "action", "tool": "query_market_data", "arguments": {"symbol": "ACME", "interval": "options_flow", "lookback": "5d"}},
            {"type": "observation", "content": "Call volume 8x average. 12,000 Jan $50 calls bought for $2.10 (stock at $38). Total premium: $2.52M. 73% from 3 accounts. Implied vol jumped from 28% to 55%."},
            {"type": "thought", "content": "Massive directional call buying concentrated in few accounts is highly suspicious. Need to identify if any are our clients."},
            {"type": "action", "tool": "check_position", "arguments": {"symbol": "ACME", "account": "ALL_MANAGED"}},
            {"type": "observation", "content": "2 managed accounts hold ACME positions: HEDGE-7 (500 shares, long-term hold) and SPEC-12 (8,000 Jan $50 calls, opened 3 days ago). SPEC-12 PM: R. Chen."},
            {"type": "thought", "content": "SPEC-12 matches the suspicious pattern - 8000 of the 12000 calls. Need immediate compliance review."},
            {"type": "action", "tool": "check_compliance", "arguments": {"trade_id": "SPEC12-ACME-CALLS-0312", "rule_set": "insider_trading_surveillance"}},
            {"type": "observation", "content": "RED FLAG: R. Chen's spouse works at advisory firm representing ACME acquisition target. Trade placed 2 days after deal entered exclusivity. Restricting account pending investigation."},
            {"type": "thought", "content": "Clear compliance violation. Account must be frozen and reported to legal and regulators immediately."},
        ],
        "final_answer": "Suspected insider trading identified. PM R. Chen purchased $1.68M in ACME calls; spouse connected to deal advisory firm. Account restricted, referred to legal and SEC/FINRA for investigation.",
    },
]

TASK_TEMPLATES["coding"] = [
    {
        "task": "Debug failing CI pipeline for auth-service. Tests pass locally but fail in CI with timeout errors.",
        "tools_used": ["read_file", "search_codebase", "run_tests"],
        "trajectory": [
            {"type": "thought", "content": "Tests pass locally but timeout in CI - likely an environment difference. Let me check the CI config first."},
            {"type": "action", "tool": "read_file", "arguments": {"path": ".github/workflows/ci.yml", "start_line": 1, "end_line": 50}},
            {"type": "observation", "content": "CI uses ubuntu-latest, Node 18. Test command: 'npm test -- --timeout 5000'. Services: postgres:14 on port 5432. No Redis service defined."},
            {"type": "thought", "content": "No Redis in CI but tests might depend on it. Let me search for Redis usage in the auth-service tests."},
            {"type": "action", "tool": "search_codebase", "arguments": {"query": "redis|createClient|ioredis", "file_type": "*.ts", "max_results": 10}},
            {"type": "observation", "content": "Found in: src/session/store.ts:12 (Redis session store), tests/auth.integration.test.ts:8 (imports session store), src/config.ts:34 (REDIS_URL with no fallback)."},
            {"type": "thought", "content": "Confirmed: tests use Redis session store but CI has no Redis service. Tests hang waiting for connection. Let me verify by running with a mock."},
            {"type": "action", "tool": "run_tests", "arguments": {"path": "tests/auth.integration.test.ts", "filter": "session", "verbose": "true"}},
            {"type": "observation", "content": "TIMEOUT after 5000ms in 'should persist session after login'. Connection refused on 127.0.0.1:6379. 8 tests affected."},
            {"type": "thought", "content": "Confirmed root cause. Fix: add Redis service to CI workflow or use ioredis-mock in test environment."},
        ],
        "final_answer": "CI failure caused by missing Redis service. Tests depend on Redis session store (8 tests affected). Fix: add redis:7 service to CI workflow and set REDIS_URL env var.",
    },
    {
        "task": "Optimize slow database query in user-search endpoint taking 4.2s average response time.",
        "tools_used": ["read_file", "execute_command", "search_codebase", "run_tests"],
        "trajectory": [
            {"type": "thought", "content": "4.2s is extremely slow for a search endpoint. Let me find the query and analyze it."},
            {"type": "action", "tool": "search_codebase", "arguments": {"query": "user-search|userSearch|searchUsers", "file_type": "*.ts", "max_results": 10}},
            {"type": "observation", "content": "src/routes/users.ts:45 - router.get('/search', searchUsers), src/services/user.service.ts:78 - async searchUsers(query), src/repositories/user.repo.ts:23 - raw SQL query."},
            {"type": "thought", "content": "Let me look at the actual SQL query in the repository layer."},
            {"type": "action", "tool": "read_file", "arguments": {"path": "src/repositories/user.repo.ts", "start_line": 20, "end_line": 45}},
            {"type": "observation", "content": "SELECT * FROM users WHERE LOWER(name) LIKE '%' || $1 || '%' OR LOWER(email) LIKE '%' || $1 || '%' ORDER BY created_at DESC; -- No index usage, full table scan on 2.3M rows."},
            {"type": "thought", "content": "LIKE with leading wildcard prevents index usage. Table has 2.3M rows. Need to add trigram index or use full-text search. Let me check existing indexes."},
            {"type": "action", "tool": "execute_command", "arguments": {"command": "psql -c \"SELECT indexname, indexdef FROM pg_indexes WHERE tablename='users';\"", "working_dir": "/app"}},
            {"type": "observation", "content": "Indexes: users_pkey (id), users_email_unique (email). No index on name. No GIN/GiST indexes for text search."},
            {"type": "thought", "content": "Solution: Add pg_trgm GIN indexes on name and email for LIKE queries. This should reduce from full scan to index scan. Let me verify tests pass after the optimization."},
            {"type": "action", "tool": "run_tests", "arguments": {"path": "tests/user-search.test.ts", "filter": "", "verbose": "true"}},
            {"type": "observation", "content": "All 12 tests pass. Average query time with trigram index: 45ms (down from 4200ms). 98.9% improvement."},
            {"type": "thought", "content": "Trigram index reduced query time from 4.2s to 45ms. Migration script needed for production deployment."},
        ],
        "final_answer": "Added GIN trigram indexes on users.name and users.email. Query time reduced from 4.2s to 45ms (98.9% improvement). Migration script created for production deployment.",
    },
    {
        "task": "Deploy hotfix for critical XSS vulnerability in comment rendering. Patch, test, and ship to production.",
        "tools_used": ["read_file", "run_tests", "check_lint", "deploy"],
        "trajectory": [
            {"type": "thought", "content": "XSS in comments is critical - need to find the vulnerable rendering code and apply sanitization."},
            {"type": "action", "tool": "read_file", "arguments": {"path": "src/components/Comment.tsx", "start_line": 1, "end_line": 30}},
            {"type": "observation", "content": "Line 18: <div dangerouslySetInnerHTML={{__html: comment.body}} />. No sanitization applied before rendering."},
            {"type": "thought", "content": "Classic XSS - raw HTML injection via dangerouslySetInnerHTML. Need DOMPurify sanitization. Let me run existing tests first to establish baseline."},
            {"type": "action", "tool": "run_tests", "arguments": {"path": "tests/components/Comment.test.tsx", "filter": "", "verbose": "true"}},
            {"type": "observation", "content": "6/6 tests pass. No XSS-specific tests exist. Test coverage: rendering, markdown formatting, author display."},
            {"type": "thought", "content": "After adding DOMPurify sanitization to the component, need to verify lint passes and tests still work."},
            {"type": "action", "tool": "check_lint", "arguments": {"path": "src/components/Comment.tsx", "fix": "false"}},
            {"type": "observation", "content": "No lint errors. Security audit: 1 warning resolved (dangerouslySetInnerHTML now wrapped with DOMPurify.sanitize). ESLint security plugin: PASS."},
            {"type": "thought", "content": "Fix applied and verified. This is a P0 security fix - deploying directly to production with expedited review."},
            {"type": "action", "tool": "deploy", "arguments": {"service": "web-frontend", "environment": "production", "version": "2.4.1-hotfix"}},
            {"type": "observation", "content": "Deployment successful. Version 2.4.1-hotfix live on production. Health checks passing. Rollback available: v2.4.0."},
            {"type": "thought", "content": "Hotfix deployed. Need to add XSS regression tests and update security advisory."},
        ],
        "final_answer": "XSS vulnerability patched with DOMPurify sanitization. Deployed v2.4.1-hotfix to production. All tests passing, lint clean. Security advisory to be published.",
    },
]

TASK_TEMPLATES["manufacturing"] = [
    {
        "task": "Investigate rising reject rate on Assembly Line 3. Defect rate increased from 0.5% to 3.2% in last shift.",
        "tools_used": ["check_sensor", "query_production_log", "run_diagnostic"],
        "trajectory": [
            {"type": "thought", "content": "6x increase in defect rate is significant. Let me check environmental sensors on Line 3 for anomalies."},
            {"type": "action", "tool": "check_sensor", "arguments": {"sensor_id": "TEMP-L3-SOLDER", "equipment": "wave_solder_3"}},
            {"type": "observation", "content": "Current temp: 248°C. Setpoint: 260°C. Delta: -12°C. Trend: declining over last 4 hours. Min threshold: 255°C."},
            {"type": "thought", "content": "Solder temperature 12°C below setpoint explains cold solder joint defects. Let me check when this drift started."},
            {"type": "action", "tool": "query_production_log", "arguments": {"line_id": "LINE-3", "time_range": "8h", "event_type": "parameter_change"}},
            {"type": "observation", "content": "02:15 - Heating element zone 2 alarm suppressed by operator J.Rodriguez. 02:30 - Temp began declining. 04:00 - First quality hold triggered."},
            {"type": "thought", "content": "Operator suppressed a heating element alarm which masked the degradation. Need diagnostic on the heating element."},
            {"type": "action", "tool": "run_diagnostic", "arguments": {"equipment": "wave_solder_3", "test_type": "heating_element_integrity"}},
            {"type": "observation", "content": "Zone 2 heating element: resistance 45 ohms (nominal: 12 ohms). Element degraded. Replacement required. Estimated remaining life: <2 hours before complete failure."},
            {"type": "thought", "content": "Root cause identified: degraded heating element in zone 2. Need immediate replacement to prevent complete line stoppage."},
        ],
        "final_answer": "Root cause: Wave solder zone 2 heating element degraded (45 vs 12 ohm nominal). Temperature dropped 12°C below setpoint causing cold joints. Maintenance dispatched for element replacement. Operator retraining on alarm suppression required.",
    },
    {
        "task": "CNC Mill M-07 vibration alarm triggered. Assess if immediate shutdown is required or can continue to shift end.",
        "tools_used": ["check_sensor", "run_diagnostic", "schedule_maintenance"],
        "trajectory": [
            {"type": "thought", "content": "Vibration alarms on CNC mills can indicate bearing failure, tool wear, or spindle issues. Need to assess severity."},
            {"type": "action", "tool": "check_sensor", "arguments": {"sensor_id": "VIB-M07-SPINDLE", "equipment": "cnc_mill_07"}},
            {"type": "observation", "content": "Vibration: 7.2 mm/s RMS (warning: 6.0, critical: 10.0). Frequency spectrum shows peak at 142Hz (bearing defect frequency). Trending upward at 0.3 mm/s per hour."},
            {"type": "thought", "content": "At 7.2 mm/s trending up 0.3/hr, we'll hit critical (10.0) in about 9 hours. Shift ends in 4 hours. But bearing defect frequency is concerning - let me run full diagnostic."},
            {"type": "action", "tool": "run_diagnostic", "arguments": {"equipment": "cnc_mill_07", "test_type": "bearing_analysis"}},
            {"type": "observation", "content": "Bearing BPFO defect confirmed on spindle bearing #2. Stage: early spalling. Estimated remaining useful life: 18-24 hours at current load. Catastrophic failure risk: LOW if load reduced 30%."},
            {"type": "thought", "content": "Can continue at reduced load for the shift. Schedule bearing replacement for next maintenance window."},
            {"type": "action", "tool": "schedule_maintenance", "arguments": {"equipment": "cnc_mill_07", "maintenance_type": "spindle_bearing_replacement", "date": "next_shift"}},
            {"type": "observation", "content": "Maintenance scheduled: tomorrow 06:00. Parts available (SKF 7214 BECBP). Estimated downtime: 3 hours. Production notified of reduced capacity until then."},
            {"type": "thought", "content": "Safe to continue at reduced load. Bearing replacement scheduled. No immediate shutdown required."},
        ],
        "final_answer": "Spindle bearing #2 early spalling confirmed. Safe to continue current shift at 70% load (RUL: 18-24h). Bearing replacement scheduled next shift (3h downtime). No immediate shutdown required.",
    },
    {
        "task": "Emergency: Hydraulic pressure loss detected on Press Line 1. Multiple safety sensors triggered.",
        "tools_used": ["check_sensor", "stop_line", "run_diagnostic", "schedule_maintenance"],
        "trajectory": [
            {"type": "thought", "content": "Hydraulic pressure loss with safety sensor triggers is potentially dangerous. Need to assess immediately and likely stop the line."},
            {"type": "action", "tool": "check_sensor", "arguments": {"sensor_id": "HYD-PRESS-PL1-MAIN", "equipment": "press_line_1"}},
            {"type": "observation", "content": "Main hydraulic pressure: 850 PSI (nominal: 3000 PSI). Rate of loss: 200 PSI/min. Accumulator pre-charge: 400 PSI. Oil temp: 95°C (max: 80°C). Level sensor: LOW."},
            {"type": "thought", "content": "Catastrophic pressure loss - down to 850 from 3000 PSI and dropping fast. Oil overheating and low level indicates major leak. Must stop immediately."},
            {"type": "action", "tool": "stop_line", "arguments": {"line_id": "PRESS-LINE-1", "reason": "Catastrophic hydraulic pressure loss - 850/3000 PSI, major leak suspected, oil overtemp at 95C"}},
            {"type": "observation", "content": "EMERGENCY STOP executed. Press rams secured in UP position. Lockout initiated. All personnel cleared from area. Line status: STOPPED."},
            {"type": "thought", "content": "Line safely stopped. Now need to identify the leak source to plan repair."},
            {"type": "action", "tool": "run_diagnostic", "arguments": {"equipment": "press_line_1", "test_type": "hydraulic_system_integrity"}},
            {"type": "observation", "content": "Leak detected: main supply hose station 3 (burst failure). Oil loss estimated: 120 liters. Secondary damage: contamination on station 3 die. No structural damage to press frame."},
            {"type": "thought", "content": "Burst hose at station 3. Need hose replacement, oil refill, die cleaning, and system bleed before restart."},
            {"type": "action", "tool": "schedule_maintenance", "arguments": {"equipment": "press_line_1", "maintenance_type": "hydraulic_hose_replacement_and_system_restore", "date": "immediate"}},
            {"type": "observation", "content": "Emergency maintenance team dispatched. Parts ETA: 45 minutes (hose in stock). Full restoration estimated: 4-6 hours including oil fill, bleed, and pressure test."},
            {"type": "thought", "content": "Emergency contained. 4-6 hour downtime for full repair. Production planning notified to reroute critical jobs."},
        ],
        "final_answer": "Press Line 1 emergency stopped. Burst hydraulic hose at station 3 caused catastrophic pressure loss (120L oil). Repair team dispatched, 4-6 hour restoration. No personnel injuries. Production rerouting initiated.",
    },
]

TASK_TEMPLATES["supplychain"] = [
    {
        "task": "Critical component SKU-7742 (MCU chips) inventory at dangerously low levels. Assess shortage risk and expedite.",
        "tools_used": ["check_inventory", "query_forecast", "alert_supplier"],
        "trajectory": [
            {"type": "thought", "content": "Low MCU chip inventory can halt production. Let me check exact levels across all warehouses."},
            {"type": "action", "tool": "check_inventory", "arguments": {"sku": "SKU-7742", "warehouse": "ALL"}},
            {"type": "observation", "content": "Total on-hand: 2,340 units. WH-East: 890, WH-West: 1,450. Daily consumption: 800 units. Days of supply: 2.9 days. Safety stock: 5 days (4,000 units). Reorder point breached."},
            {"type": "thought", "content": "Under 3 days supply with 5-day safety stock breached. Need to check if demand is increasing and when next shipment arrives."},
            {"type": "action", "tool": "query_forecast", "arguments": {"sku": "SKU-7742", "horizon": "30d", "region": "ALL"}},
            {"type": "observation", "content": "Forecast: demand increasing 15% next 2 weeks (new product ramp). Next PO delivery: 12 days out (5,000 units from TechSupply Co). Gap: ~7,200 units short before delivery."},
            {"type": "thought", "content": "12-day delivery won't arrive in time. We'll run out in 3 days. Need to expedite with supplier immediately."},
            {"type": "action", "tool": "alert_supplier", "arguments": {"supplier_id": "TECHSUPPLY-001", "message": "URGENT: SKU-7742 critical shortage. Request air freight expedite of pending PO or partial early shipment of 3000+ units within 48 hours. Production line stoppage imminent.", "priority": "critical"}},
            {"type": "observation", "content": "Supplier acknowledged. Can expedite 3,500 units via air freight, delivery in 36 hours. Additional cost: $18,200 for air vs ocean. Remaining 1,500 units ship standard (12 days)."},
            {"type": "thought", "content": "Air expedite of 3,500 solves the immediate crisis. $18.2K premium is justified vs production line stoppage costs (~$200K/day)."},
        ],
        "final_answer": "MCU chip shortage critical (2.9 days supply). Expedited 3,500 units via air freight (36hr delivery, $18.2K premium). Prevents production stoppage worth $200K/day. Standard shipment covers remaining demand.",
    },
    {
        "task": "Shipment TRACK-89921 containing temperature-sensitive vaccines delayed at customs. Monitor and reroute if needed.",
        "tools_used": ["track_shipment", "check_inventory", "route_shipment", "alert_supplier"],
        "trajectory": [
            {"type": "thought", "content": "Temperature-sensitive vaccines delayed at customs is time-critical. Need to check current status and cold chain integrity."},
            {"type": "action", "tool": "track_shipment", "arguments": {"tracking_id": "TRACK-89921", "carrier": "MedLogistics"}},
            {"type": "observation", "content": "Status: HELD AT CUSTOMS (Port Miami). Duration: 18 hours. Cold chain: ACTIVE (2-8°C maintained). Estimated release: 24-48 hours pending FDA docs. Battery life remaining on cooler: 36 hours."},
            {"type": "thought", "content": "36 hours battery remaining but 24-48 hours customs hold. Risk of cold chain break. Check if we have alternate stock to serve immediate demand."},
            {"type": "action", "tool": "check_inventory", "arguments": {"sku": "VAC-MRNA-2024", "warehouse": "COLD-STORAGE-ATL"}},
            {"type": "observation", "content": "Atlanta cold storage: 12,000 doses available. Committed: 8,000 (hospital orders due in 3 days). Available: 4,000 doses. Shelf life: 45 days remaining."},
            {"type": "thought", "content": "4,000 doses available as bridge stock. But if customs takes full 48 hours, cold chain fails. Let me check if we can reroute through a faster port."},
            {"type": "action", "tool": "route_shipment", "arguments": {"origin": "Port Miami Customs", "destination": "COLD-STORAGE-ATL", "weight": "450kg"}},
            {"type": "observation", "content": "Reroute not possible while in customs hold. Alternative: Request priority FDA review (4-6 hour expedite available for temperature-sensitive biologics). Cost: $2,400 expedite fee."},
            {"type": "thought", "content": "Priority FDA review is the best option - 4-6 hours vs 24-48. Cold chain preserved. Alert the supplier to prepare documentation."},
            {"type": "action", "tool": "alert_supplier", "arguments": {"supplier_id": "MEDLOG-INTL", "message": "Request priority FDA review for TRACK-89921 (temperature-sensitive biologics). Cold chain battery: 36hr remaining. Please submit expedite docs immediately.", "priority": "high"}},
            {"type": "observation", "content": "MedLogistics confirmed: Priority review submitted. FDA expedite approved. Estimated release: 6 hours. Courier arranged for immediate transport post-release."},
            {"type": "thought", "content": "Crisis averted. Shipment will clear in 6 hours with 30 hours of cold chain remaining. No need to tap bridge stock."},
        ],
        "final_answer": "Vaccine shipment customs hold resolved via FDA priority review (6hr release vs 48hr standard). Cold chain integrity maintained (30hr battery remaining post-release). No bridge stock needed. Expedite cost: $2,400.",
    },
    {
        "task": "Quarterly demand forecast shows 40% spike in SKU-2201 (EV battery cells). Plan procurement to meet demand.",
        "tools_used": ["query_forecast", "check_inventory", "create_po"],
        "trajectory": [
            {"type": "thought", "content": "40% demand spike for battery cells requires careful procurement planning. Let me verify the forecast details."},
            {"type": "action", "tool": "query_forecast", "arguments": {"sku": "SKU-2201", "horizon": "90d", "region": "ALL"}},
            {"type": "observation", "content": "Current monthly demand: 50,000 cells. Forecast next quarter: 70,000/month (+40%). Driver: 2 new EV model launches. Confidence: 85%. Lead time from supplier: 45 days."},
            {"type": "thought", "content": "Need 20,000 additional cells/month = 60,000 extra over quarter. With 45-day lead time, must order now. Check current inventory buffer."},
            {"type": "action", "tool": "check_inventory", "arguments": {"sku": "SKU-2201", "warehouse": "ALL"}},
            {"type": "observation", "content": "On-hand: 82,000 cells. Incoming POs: 50,000 (arriving in 20 days). Committed: 45,000. Available: 87,000 total. At new run rate, covers only 37 days."},
            {"type": "thought", "content": "37 days coverage with 45-day lead time means we'll gap out. Need to place a large PO immediately for the incremental demand."},
            {"type": "action", "tool": "create_po", "arguments": {"supplier": "CellTech-Korea", "items": "SKU-2201-EV-PRISMATIC", "quantity": 75000, "urgency": "high"}},
            {"type": "observation", "content": "PO-2024-4471 created. 75,000 units @ $42.50/cell = $3.19M. Supplier confirmed capacity available. Delivery: 50,000 in 40 days, 25,000 in 55 days. Payment terms: Net 60."},
            {"type": "thought", "content": "PO placed to cover the demand spike plus rebuild safety stock. Split delivery aligns with ramp schedule."},
        ],
        "final_answer": "Placed PO for 75,000 EV battery cells ($3.19M) with split delivery to match demand ramp. Current inventory covers 37 days; new PO arrives day 40. No production gap expected.",
    },
]

TASK_TEMPLATES["devops"] = [
    {
        "task": "Production API gateway returning 503 errors. Service mesh shows 40% failure rate on /api/v2/orders endpoint.",
        "tools_used": ["check_service_health", "view_logs", "scale_service"],
        "trajectory": [
            {"type": "thought", "content": "503 errors indicate backend unavailability. Let me check the orders service health first."},
            {"type": "action", "tool": "check_service_health", "arguments": {"service": "orders-api", "environment": "production"}},
            {"type": "observation", "content": "orders-api: 3/5 pods healthy. 2 pods in CrashLoopBackOff. Memory usage: 94% on healthy pods. CPU: 78%. Last restart: 12 minutes ago."},
            {"type": "thought", "content": "Memory at 94% with pods crashing suggests OOM kills. Let me check logs for confirmation."},
            {"type": "action", "tool": "view_logs", "arguments": {"service": "orders-api", "severity": "error", "time_range": "30m"}},
            {"type": "observation", "content": "OOMKilled events at 14:23, 14:31. 'JavaScript heap out of memory' in pod orders-api-7f8b9. Memory leak in connection pool - 847 idle connections (max: 100)."},
            {"type": "thought", "content": "Connection pool leak causing OOM. Immediate fix: scale up to handle load while the leak is patched."},
            {"type": "action", "tool": "scale_service", "arguments": {"service": "orders-api", "replicas": 8, "environment": "production"}},
            {"type": "observation", "content": "Scaled orders-api to 8 replicas. 5 new pods starting. ETA to healthy: 45 seconds. Memory pressure distributed. Error rate dropping: 40% -> 12% -> 2%."},
            {"type": "thought", "content": "Immediate crisis resolved by scaling. Root cause is connection pool leak - needs code fix for permanent resolution."},
        ],
        "final_answer": "503 errors resolved by scaling orders-api to 8 replicas. Root cause: connection pool memory leak (847 idle connections). Error rate reduced from 40% to 2%. Code fix needed for permanent resolution.",
    },
    {
        "task": "Failed deployment of payments-service v3.2.1 causing transaction failures. Assess and rollback if needed.",
        "tools_used": ["check_service_health", "view_logs", "rollback_deploy"],
        "trajectory": [
            {"type": "thought", "content": "Transaction failures after deployment is critical for a payments service. Need to assess damage and decide on rollback quickly."},
            {"type": "action", "tool": "check_service_health", "arguments": {"service": "payments-service", "environment": "production"}},
            {"type": "observation", "content": "payments-service v3.2.1: All 6 pods running. Health checks PASSING. But downstream metric: transaction success rate dropped from 99.7% to 84.2%. Latency p99: 12s (normal: 800ms)."},
            {"type": "thought", "content": "Pods healthy but transactions failing - likely an application logic bug, not infrastructure. Let me check error patterns."},
            {"type": "action", "tool": "view_logs", "arguments": {"service": "payments-service", "severity": "error", "time_range": "15m"}},
            {"type": "observation", "content": "Repeated error: 'InvalidSchemaError: field currency_code expected string(3), got string(2)'. New validation in v3.2.1 rejecting legacy 2-char currency codes (e.g., 'US' instead of 'USD'). 15.8% of transactions affected."},
            {"type": "thought", "content": "Breaking change in validation - rejecting valid legacy data. This wasn't caught in testing. Must rollback immediately to stop revenue loss."},
            {"type": "action", "tool": "rollback_deploy", "arguments": {"service": "payments-service", "version": "3.2.0"}},
            {"type": "observation", "content": "Rollback to v3.2.0 complete. All 6 pods replaced. Transaction success rate recovering: 84.2% -> 96.1% -> 99.5%. Estimated revenue impact during incident: $47,200."},
            {"type": "thought", "content": "Rollback successful. The v3.2.1 release needs a migration path for legacy currency codes before redeployment."},
        ],
        "final_answer": "Rolled back payments-service to v3.2.0. Breaking change in currency validation rejected 15.8% of transactions. Revenue impact: ~$47,200. v3.2.1 needs data migration before re-release.",
    },
    {
        "task": "Prepare and execute blue-green deployment of notification-service v2.0 with new message queue backend.",
        "tools_used": ["run_pipeline", "check_service_health", "update_config", "view_logs"],
        "trajectory": [
            {"type": "thought", "content": "Blue-green deployment for a major backend change. Need to deploy green, validate, then switch traffic."},
            {"type": "action", "tool": "run_pipeline", "arguments": {"repo": "notification-service", "branch": "release/v2.0", "stage": "deploy-green"}},
            {"type": "observation", "content": "Pipeline triggered: build -> test -> deploy-green. Build: SUCCESS. Tests: 342/342 passed. Green deployment: 4 pods running on green cluster. Not receiving traffic yet."},
            {"type": "thought", "content": "Green is deployed and tests pass. Let me verify it's healthy before switching traffic."},
            {"type": "action", "tool": "check_service_health", "arguments": {"service": "notification-service-green", "environment": "production"}},
            {"type": "observation", "content": "notification-service-green v2.0: 4/4 pods healthy. Readiness checks passing. Message queue connection: ESTABLISHED (RabbitMQ cluster). Synthetic test messages processed successfully."},
            {"type": "thought", "content": "Green is healthy and processing test messages. Now switch traffic by updating the routing config."},
            {"type": "action", "tool": "update_config", "arguments": {"service": "api-gateway", "key": "notification-service.target", "value": "notification-service-green"}},
            {"type": "observation", "content": "Config updated. Traffic routing switched to green. Blue (v1.8) still running as fallback. Current traffic split: 100% green."},
            {"type": "thought", "content": "Traffic switched. Let me monitor the green deployment for errors under real load."},
            {"type": "action", "tool": "view_logs", "arguments": {"service": "notification-service-green", "severity": "error", "time_range": "5m"}},
            {"type": "observation", "content": "No errors in last 5 minutes. Throughput: 1,247 messages/min (matches blue baseline). Latency p95: 23ms (blue was 45ms). Zero failed deliveries."},
            {"type": "thought", "content": "Green performing better than blue (23ms vs 45ms p95). Deployment successful. Blue can be decommissioned after soak period."},
        ],
        "final_answer": "Blue-green deployment of notification-service v2.0 complete. Green cluster healthy, processing 1,247 msg/min with improved latency (23ms vs 45ms). Blue retained as fallback for 24h soak period.",
    },
]

TASK_TEMPLATES["legal"] = [
    {
        "task": "Review force majeure clause in supplier contract CT-2024-0891 for applicability to current port strike disruption.",
        "tools_used": ["review_contract", "search_cases", "check_regulation"],
        "trajectory": [
            {"type": "thought", "content": "Need to determine if the port strike qualifies under the contract's force majeure definition. Let me review the clause first."},
            {"type": "action", "tool": "review_contract", "arguments": {"contract_id": "CT-2024-0891", "section": "force_majeure"}},
            {"type": "observation", "content": "Section 14.1: Force Majeure includes 'acts of God, war, terrorism, government action, epidemic, labor disputes affecting third parties.' Notice required within 5 business days. Must demonstrate causation and mitigation efforts."},
            {"type": "thought", "content": "Labor disputes affecting third parties is explicitly listed. Port workers are third parties to this contract. Let me check relevant case law for port strike precedents."},
            {"type": "action", "tool": "search_cases", "arguments": {"query": "force majeure port strike labor dispute supply chain", "jurisdiction": "US_Federal", "date_range": "2019-2024"}},
            {"type": "observation", "content": "Key case: Pacific Shipping v. TechCorp (2022) - port strike held valid force majeure where alternate ports existed but at 3x cost. Court required 'commercially reasonable' mitigation, not 'all possible' mitigation."},
            {"type": "thought", "content": "Precedent supports our position. Alternate routing at 3x cost is not commercially reasonable. Let me verify no regulatory override applies."},
            {"type": "action", "tool": "check_regulation", "arguments": {"topic": "force_majeure_commercial_contracts", "jurisdiction": "US_Delaware"}},
            {"type": "observation", "content": "Delaware law: Force majeure clauses strictly construed. Must be specifically enumerated. 'Labor disputes' is sufficiently specific per Restatement (Second) §261. 5-day notice period is enforceable."},
            {"type": "thought", "content": "Strong legal basis. Port strike qualifies, precedent supports, Delaware law upholds. Key requirement: timely notice within 5 business days."},
        ],
        "final_answer": "Force majeure clause applies. Port strike covered under 'labor disputes affecting third parties.' Supported by Pacific Shipping v. TechCorp (2022). Must file notice within 5 business days and document mitigation efforts.",
    },
    {
        "task": "Assess liability exposure for data breach affecting 50,000 customer records. Determine notification obligations.",
        "tools_used": ["check_regulation", "search_cases", "calculate_damages"],
        "trajectory": [
            {"type": "thought", "content": "50K records breached triggers multiple regulatory frameworks. Need to identify all applicable notification laws."},
            {"type": "action", "tool": "check_regulation", "arguments": {"topic": "data_breach_notification_requirements", "jurisdiction": "US_Multi_State"}},
            {"type": "observation", "content": "Applicable laws: California CCPA (30-day notice, AG notification >500 records), NY SHIELD Act (expeditious notice), GDPR Art.33 (72-hour supervisory authority notification for EU residents). 23 states with individual timelines. FTC Section 5 applies."},
            {"type": "thought", "content": "Multiple overlapping obligations. GDPR 72-hour clock is most urgent if any EU residents affected. Let me check precedent for damages in similar breaches."},
            {"type": "action", "tool": "search_cases", "arguments": {"query": "data breach 50000 records damages settlement consumer class action", "jurisdiction": "US_Federal", "date_range": "2020-2024"}},
            {"type": "observation", "content": "Comparable settlements: DataCorp (2023, 45K records): $3.2M ($71/record). RetailX (2022, 62K records): $4.8M ($77/record). Average class action settlement: $65-85/record. Regulatory fines additional: $100K-$2M range."},
            {"type": "thought", "content": "Exposure range is significant. Let me calculate our specific liability estimate based on the data types exposed."},
            {"type": "action", "tool": "calculate_damages", "arguments": {"case_id": "BREACH-2024-INT-001", "model": "data_breach_liability"}},
            {"type": "observation", "content": "Estimated total exposure: $3.5M - $6.2M. Breakdown: Class action settlement: $2.8-4.5M, Regulatory fines: $400K-1.2M, Remediation costs: $300K-500K. Credit monitoring for affected: $1.2M. Insurance coverage: $5M policy applies."},
            {"type": "thought", "content": "Total exposure up to $6.2M but insurance covers $5M. Net exposure: $1.2M worst case. Priority: meet 72hr GDPR deadline."},
        ],
        "final_answer": "Total liability exposure: $3.5-6.2M. Insurance covers $5M. Immediate actions: GDPR 72hr notification (if EU residents), CCPA 30-day notice, retain breach counsel. Net uninsured exposure: up to $1.2M.",
    },
    {
        "task": "Draft non-compete clause for senior engineering hire. Must be enforceable in California and New York.",
        "tools_used": ["check_regulation", "search_cases", "draft_clause"],
        "trajectory": [
            {"type": "thought", "content": "Non-competes have very different enforceability between CA and NY. California essentially bans them. Need to find an enforceable alternative."},
            {"type": "action", "tool": "check_regulation", "arguments": {"topic": "non_compete_enforceability_employment", "jurisdiction": "US_California"}},
            {"type": "observation", "content": "California Bus. & Prof. Code §16600: Non-compete clauses are VOID and unenforceable. Exception only for sale of business. Can use: NDA, non-solicitation of customers (narrow), invention assignment. FTC proposed nationwide ban pending."},
            {"type": "thought", "content": "Non-compete won't work for CA. Need alternative protective mechanisms. Let me check what NY allows for comparison."},
            {"type": "action", "tool": "search_cases", "arguments": {"query": "non-solicitation non-compete senior engineer technology enforceable", "jurisdiction": "US_New_York", "date_range": "2021-2024"}},
            {"type": "observation", "content": "NY: Non-competes enforceable if reasonable (typically 12 months, limited geography/scope). But trend toward restriction. Non-solicitation of clients/employees more reliably enforced. Garden leave provisions strengthened enforceability."},
            {"type": "thought", "content": "Best dual-state approach: non-solicitation (works in both) + garden leave + robust NDA. Let me draft the clause."},
            {"type": "action", "tool": "draft_clause", "arguments": {"clause_type": "non_solicitation_with_garden_leave", "parameters": "duration=12months, scope=clients_and_employees, garden_leave=3months_full_pay, confidentiality=perpetual_trade_secrets"}},
            {"type": "observation", "content": "Clause drafted: 12-month non-solicitation of clients/employees with whom engineer had material contact. 3-month garden leave at full compensation. Perpetual trade secret NDA. Severability clause for multi-state enforcement. Choice of law: Delaware."},
            {"type": "thought", "content": "This structure is enforceable in both states. Non-solicitation works in CA, full package works in NY. Garden leave adds consideration."},
        ],
        "final_answer": "Non-compete unenforceable in CA. Drafted alternative: 12-month non-solicitation + 3-month garden leave (full pay) + perpetual trade secret NDA. Enforceable in both CA and NY. Includes severability clause.",
    },
]

TASK_TEMPLATES["energy"] = [
    {
        "task": "Grid segment GS-NE-14 reporting voltage instability. Frequency deviation detected at 59.92Hz (nominal 60Hz).",
        "tools_used": ["check_grid_status", "forecast_demand", "adjust_generation"],
        "trajectory": [
            {"type": "thought", "content": "Frequency below 60Hz indicates demand exceeding supply. 59.92Hz is concerning but not yet critical (59.5Hz triggers load shed). Need to assess the segment."},
            {"type": "action", "tool": "check_grid_status", "arguments": {"segment_id": "GS-NE-14", "metric": "all"}},
            {"type": "observation", "content": "Frequency: 59.92Hz. Load: 4,850MW. Generation: 4,720MW. Deficit: 130MW. Wind farm WF-03 output dropped 40% (wind speed decline). Solar at 0% (nighttime). Reserve margin: 2.1% (critical threshold: 3%)."},
            {"type": "thought", "content": "130MW deficit from wind drop-off at night. Need to bring additional generation online. Let me check if demand is expected to increase further."},
            {"type": "action", "tool": "forecast_demand", "arguments": {"region": "NE-14", "horizon": "4h"}},
            {"type": "observation", "content": "Demand forecast: rising to 5,100MW by 02:00 (cold front arriving, heating load). Peak deficit expected: 380MW if wind stays low. Probability of sustained low wind: 78%."},
            {"type": "thought", "content": "Situation will worsen - need 380MW additional capacity. Gas peaker plant GP-NE-02 can provide 400MW. Dispatch immediately."},
            {"type": "action", "tool": "adjust_generation", "arguments": {"plant_id": "GP-NE-02", "target_mw": "400"}},
            {"type": "observation", "content": "Gas peaker GP-NE-02 dispatched. Ramp-up time: 12 minutes. Target: 400MW. Grid frequency recovering: 59.92Hz -> 59.96Hz. Projected stable at 60.0Hz in 15 minutes."},
            {"type": "thought", "content": "Peaker dispatched, frequency recovering. Will cover the forecasted demand increase from the cold front."},
        ],
        "final_answer": "Grid frequency restored. 130MW deficit caused by wind drop-off resolved by dispatching gas peaker GP-NE-02 (400MW). Covers forecasted cold front demand increase to 5,100MW. Reserve margin restored to 6.8%.",
    },
    {
        "task": "Smart meter cluster in district D-44 showing zero readings for 200+ meters. Investigate potential outage vs meter failure.",
        "tools_used": ["read_meter", "check_grid_status", "dispatch_crew"],
        "trajectory": [
            {"type": "thought", "content": "200+ meters reading zero could be an actual outage or a communication failure. Need to check if the grid segment is energized."},
            {"type": "action", "tool": "read_meter", "arguments": {"meter_id": "D44-CLUSTER-HEAD", "interval": "15min"}},
            {"type": "observation", "content": "Cluster head meter D44-CH: last successful reading 47 minutes ago (3.2kW). Current: NO DATA. Communication status: OFFLINE. 217 downstream meters affected. Mesh network: DOWN."},
            {"type": "thought", "content": "Communication is down but that doesn't confirm outage. Let me check the grid segment feeding this district."},
            {"type": "action", "tool": "check_grid_status", "arguments": {"segment_id": "FEEDER-D44-A", "metric": "power_flow"}},
            {"type": "observation", "content": "Feeder D44-A: ENERGIZED. Current flow: 12A (normal for this time: 180A). Upstream breaker: CLOSED. Downstream recloser RC-D44-3: OPEN (tripped). Fault current detected: 4,200A at 22:51."},
            {"type": "thought", "content": "Recloser tripped on fault current. This is an actual outage, not meter communication issue. 4,200A fault suggests downed line or equipment failure. Need crew dispatched."},
            {"type": "action", "tool": "dispatch_crew", "arguments": {"location": "District D-44, Recloser RC-D44-3", "issue_type": "overcurrent_fault_recloser_trip", "priority": "high"}},
            {"type": "observation", "content": "Crew Alpha-7 dispatched. ETA: 22 minutes. 847 customers affected (estimated from meter count). Restoration estimate: 1-3 hours depending on fault type. Customer notification sent via automated system."},
            {"type": "thought", "content": "Crew dispatched. Outage confirmed - recloser tripped on 4,200A fault. Likely downed conductor or transformer failure."},
        ],
        "final_answer": "Confirmed outage in District D-44. Recloser RC-D44-3 tripped on 4,200A fault at 22:51. 847 customers affected. Field crew dispatched (ETA 22 min). Restoration: 1-3 hours.",
    },
    {
        "task": "Solar farm SF-West-12 output 35% below expected for clear sky conditions. Investigate performance degradation.",
        "tools_used": ["read_meter", "check_grid_status", "dispatch_crew", "forecast_demand"],
        "trajectory": [
            {"type": "thought", "content": "35% below expected on a clear day is major. Could be inverter failure, panel soiling, or grid curtailment. Let me check generation data."},
            {"type": "action", "tool": "read_meter", "arguments": {"meter_id": "SF-W12-MAIN-GEN", "interval": "5min"}},
            {"type": "observation", "content": "Expected output: 45MW. Actual: 29.2MW. Delta: -15.8MW. Inverter bank status: INV-1 through INV-4 normal, INV-5 and INV-6: OUTPUT ZERO. String monitoring: 40% of strings on INV-5/6 showing ground fault."},
            {"type": "thought", "content": "Two inverter banks offline with ground faults. This accounts for the 35% loss (2 of 6 banks = 33%). Let me verify grid isn't curtailing us."},
            {"type": "action", "tool": "check_grid_status", "arguments": {"segment_id": "SF-W12-POI", "metric": "curtailment"}},
            {"type": "observation", "content": "Point of interconnection: No curtailment active. Grid can accept full 45MW. Voltage at POI: normal. No grid-side constraints."},
            {"type": "thought", "content": "Confirmed plant-side issue, not curtailment. Ground faults on 2 inverter banks need immediate investigation - could be water ingress, cable damage, or panel failure."},
            {"type": "action", "tool": "dispatch_crew", "arguments": {"location": "Solar Farm SF-West-12, Inverter Banks 5 and 6", "issue_type": "ground_fault_multiple_strings", "priority": "high"}},
            {"type": "observation", "content": "Solar maintenance crew dispatched. ETA: 45 minutes. Preliminary remote diagnosis suggests possible cable tray flooding from last night's rain. Thermal imaging drone requested."},
            {"type": "thought", "content": "Likely water-related ground faults post-rain. Let me check if this lost generation affects today's demand coverage."},
            {"type": "action", "tool": "forecast_demand", "arguments": {"region": "WEST-GRID", "horizon": "8h"}},
            {"type": "observation", "content": "Regional demand: well-supplied. 15.8MW shortfall covered by other solar assets and gas reserves. No reliability concern. Revenue loss: ~$1,900/hour at current LMP."},
            {"type": "thought", "content": "No grid reliability impact but revenue loss of $1,900/hr motivates fast repair. Crew should prioritize INV-5/6 restoration."},
        ],
        "final_answer": "Solar farm underperformance caused by ground faults on inverter banks 5 and 6 (likely water ingress post-rain). 15.8MW lost, no grid impact. Maintenance crew dispatched. Revenue loss: $1,900/hr until restored.",
    },
]

TASK_TEMPLATES["agriculture"] = [
    {
        "task": "Field F-12 wheat crop showing signs of stress. Soil moisture sensors reporting below threshold. Assess and respond.",
        "tools_used": ["check_soil_moisture", "get_weather_forecast", "activate_irrigation"],
        "trajectory": [
            {"type": "thought", "content": "Crop stress with low soil moisture indicates irrigation need. Let me check exact moisture levels and depth profile."},
            {"type": "action", "tool": "check_soil_moisture", "arguments": {"field_id": "F-12", "depth": "all"}},
            {"type": "observation", "content": "Depth 15cm: 18% (threshold: 25%). Depth 30cm: 22% (threshold: 28%). Depth 60cm: 31% (adequate). Root zone average: 20.3%. Wilting point: 15%. Crop stage: grain fill (critical period)."},
            {"type": "thought", "content": "Root zone well below threshold and crop is in grain fill - most water-sensitive stage. Need irrigation but let me check weather first to avoid overwatering before rain."},
            {"type": "action", "tool": "get_weather_forecast", "arguments": {"location": "F-12-GPS", "days": 5}},
            {"type": "observation", "content": "Next 5 days: Day 1-3 clear, high 34°C, ET0: 7mm/day. Day 4: 30% chance rain (2-5mm). Day 5: 60% chance rain (8-15mm). No reliable precipitation for 3 days."},
            {"type": "thought", "content": "Three more days of high evapotranspiration before any rain. At 7mm/day ET and current stress, cannot wait. Need to irrigate now to protect grain fill yields."},
            {"type": "action", "tool": "activate_irrigation", "arguments": {"zone_id": "F12-CENTER-PIVOT", "duration_min": 240, "flow_rate": "medium"}},
            {"type": "observation", "content": "Irrigation activated: Zone F12 center pivot. Duration: 4 hours at medium flow (25mm application). Estimated to bring root zone to 28% moisture. Completion: 18:30. Next irrigation recommended: 48 hours."},
            {"type": "thought", "content": "25mm application should restore root zone moisture and protect yield during grain fill. Will reassess in 48 hours after forecast rain potential."},
        ],
        "final_answer": "Irrigation activated for Field F-12 (4hr, 25mm application). Root zone critically low at 20.3% during grain fill stage. No rain expected for 3 days. Follow-up irrigation in 48 hours if rain doesn't materialize.",
    },
    {
        "task": "Drone imagery shows yellowing patches in soybean field F-08. Diagnose cause and recommend treatment.",
        "tools_used": ["analyze_crop_image", "check_soil_moisture", "apply_treatment"],
        "trajectory": [
            {"type": "thought", "content": "Yellowing in soybeans could be nutrient deficiency, disease, or water stress. Drone imagery analysis should help differentiate."},
            {"type": "action", "tool": "analyze_crop_image", "arguments": {"field_id": "F-08", "image_date": "today", "analysis_type": "ndvi_health_map"}},
            {"type": "observation", "content": "NDVI analysis: 3 distinct low-NDVI patches (0.35-0.45 vs field avg 0.72). Pattern: interveinal chlorosis, NOT random. Affected area: 4.2 hectares (12% of field). Spatial pattern suggests nutrient deficiency rather than pathogen spread."},
            {"type": "thought", "content": "Interveinal chlorosis in soybeans typically indicates iron deficiency (IDC) or manganese deficiency. Let me check soil conditions in those areas."},
            {"type": "action", "tool": "check_soil_moisture", "arguments": {"field_id": "F-08-ZONE3", "depth": "30cm"}},
            {"type": "observation", "content": "Moisture: 38% (high). pH sensor: 7.8 (high for soybeans, optimal: 6.0-6.8). EC: 2.1 dS/m. Note: affected zones correspond to calcareous soil areas mapped in 2023 survey. Iron availability reduced at pH >7.5."},
            {"type": "thought", "content": "High pH (7.8) in calcareous zones causing iron deficiency chlorosis. Classic IDC in soybeans. Need foliar iron application for immediate relief."},
            {"type": "action", "tool": "apply_treatment", "arguments": {"field_id": "F-08-ZONE3", "treatment": "chelated_iron_foliar_EDDHA", "quantity": "4.5kg_per_hectare"}},
            {"type": "observation", "content": "Treatment scheduled: Chelated iron (Fe-EDDHA) foliar spray on 4.2 hectares. Application window: tomorrow 06:00-08:00 (low wind, before heat). Expected response: 7-10 days for green-up. Repeat in 14 days if needed."},
            {"type": "thought", "content": "Foliar iron applied to affected zones. For long-term solution, consider IDC-tolerant soybean varieties in these calcareous areas next season."},
        ],
        "final_answer": "Diagnosed iron deficiency chlorosis (IDC) in 4.2ha of F-08 due to high pH (7.8) calcareous soil. Chelated iron foliar spray scheduled. Long-term: switch to IDC-tolerant varieties in affected zones.",
    },
    {
        "task": "Harvester H-03 reporting GPS drift and auto-steer errors during corn harvest. Assess equipment status.",
        "tools_used": ["check_equipment", "get_weather_forecast", "analyze_crop_image"],
        "trajectory": [
            {"type": "thought", "content": "GPS drift in auto-steer can cause crop damage from misaligned passes. Let me check the equipment diagnostics."},
            {"type": "action", "tool": "check_equipment", "arguments": {"equipment_id": "H-03", "diagnostic": "gps_autosteer_full"}},
            {"type": "observation", "content": "GPS status: RTK fix LOST. Falling back to WAAS (1-2m accuracy vs 2cm RTK). Base station BS-NORTH: signal weak (SNR: 12dB, min: 18dB). Antenna cable: impedance 68 ohm (nominal: 50 ohm). Auto-steer disabled due to accuracy loss."},
            {"type": "thought", "content": "RTK fix lost due to weak base station signal. Could be antenna cable degradation (impedance off) or atmospheric interference. Let me check if conditions could be causing ionospheric issues."},
            {"type": "action", "tool": "get_weather_forecast", "arguments": {"location": "H-03-GPS", "days": 1}},
            {"type": "observation", "content": "Space weather: geomagnetic storm G2 (Kp=6) in progress. GPS accuracy degraded region-wide. Expected duration: 6-8 hours. Impact: RTK convergence times increased 3-5x."},
            {"type": "thought", "content": "Combination of degraded antenna cable AND geomagnetic storm. Cable needs replacement but storm is temporary. Let me check if harvest timing is critical."},
            {"type": "action", "tool": "analyze_crop_image", "arguments": {"field_id": "F-15-CORN", "image_date": "today", "analysis_type": "harvest_readiness"}},
            {"type": "observation", "content": "Corn moisture: 15.2% (target: <15.5%). Maturity: R6 complete. Weather window: 2 days before rain. Recommendation: harvest immediately if possible, even at reduced speed with manual steer."},
            {"type": "thought", "content": "Crop ready and weather closing in. Recommend manual steering at reduced speed today, replace antenna cable tonight, and resume RTK harvest tomorrow before rain."},
        ],
        "final_answer": "GPS issues from geomagnetic storm (G2) + degraded antenna cable (68 vs 50 ohm). Recommend: manual steer at reduced speed today, replace cable tonight. RTK should recover as storm passes. Harvest must complete within 2 days before rain.",
    },
]


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def generate_tool_use(world: str, rng: Any, tick: int, difficulty: str = "medium") -> dict:
    """Generate a tool-use/ReAct format record for the given world.

    Args:
        world: Domain name (cybersecurity, healthcare, finance, coding, etc.)
        rng: random.Random instance for deterministic generation
        tick: Sequence number for record ID generation
        difficulty: 'easy' (1-2 tools), 'medium' (3-4 tools), 'hard' (5-7 tools)

    Returns:
        Dict with format, record_id, metadata, available_tools, task, trajectory, final_answer
    """
    # Get tools for this world (fallback to cybersecurity)
    tools = WORLD_TOOLS.get(world, WORLD_TOOLS.get("cybersecurity", []))
    if not tools:
        tools = WORLD_TOOLS["cybersecurity"]

    # Get task templates for this world
    tasks = TASK_TEMPLATES.get(world, TASK_TEMPLATES.get("cybersecurity", []))
    if not tasks:
        tasks = TASK_TEMPLATES["cybersecurity"]

    # Pick a random task
    task_template = rng.choice(tasks)

    # Get trajectory and trim based on difficulty
    trajectory = task_template.get("trajectory", [])
    tools_used_names = task_template.get("tools_used", [])

    # Determine how many tool calls based on difficulty
    if difficulty == "easy":
        max_tools = rng.randint(1, 2)
    elif difficulty == "hard":
        max_tools = rng.randint(5, 7)
    else:
        max_tools = rng.randint(3, 4)

    # Trim trajectory to match difficulty (count action steps)
    trimmed_trajectory = []
    tool_count = 0
    for step in trajectory:
        if step["type"] == "action":
            tool_count += 1
            if tool_count > max_tools:
                break
        trimmed_trajectory.append(step)

    # Count actual tools used in trimmed trajectory
    actual_tools = sum(1 for s in trimmed_trajectory if s["type"] == "action")

    return {
        "format": "tool_use",
        "record_id": f"tu_{tick:06d}_{world}_{rng.randint(0, 99999):05d}",
        "metadata": {
            "world": world,
            "difficulty": difficulty,
            "tools_used": actual_tools,
            "total_steps": len(trimmed_trajectory),
            "pattern": "ReAct",
        },
        "available_tools": tools,
        "task": task_template["task"],
        "trajectory": trimmed_trajectory,
        "final_answer": task_template["final_answer"],
    }
