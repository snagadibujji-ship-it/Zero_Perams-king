"""
Industry-Specific Jargon & Communication Style
================================================
Each industry has its own vocabulary and way of communicating.
A refinery worker says "turnaround" not "maintenance shutdown".
A developer says "LGTM" not "looks good to me".

This module provides:
1. Industry-specific word replacements (generic → specific)
2. Industry-specific short responses (instead of generic "ok")
3. Communication style modifiers (formal, radio-style, casual, etc.)

Research sources:
- Oil & Gas: Glossary of oilfield jargon (Wikipedia), EIA slang guide
- Software: GitHub comment analysis (20%+ jargon usage), Slack communication studies
- Mining: Mining terminology databases, DGMS regulations
- Healthcare: Medical abbreviations and nursing communication standards
- Construction: Site communication protocols, crane signal terminology
"""
import random
from typing import Optional, Dict, List, Tuple


# ═══════════════════════════════════════════════════════════════════
# INDUSTRY JARGON — Word replacements that make messages authentic
# Format: "generic_word": "industry_specific_word"
# ═══════════════════════════════════════════════════════════════════

INDUSTRY_JARGON: Dict[str, Dict[str, str]] = {
    "ai_research_lab": {
        "equipment": "GPU cluster",
        "started": "kicked off",
        "stopped": "killed",
        "running": "training",
        "output": "inference output",
        "error": "NaN loss",
        "broken": "OOMing",
        "working": "converging",
        "not working": "diverging",
        "check": "eval",
        "result": "metrics",
        "good": "SOTA",
        "bad": "garbage",
        "fix": "hotfix",
        "test": "ablation",
        "slow": "bottlenecked",
        "fast": "optimized",
        "done": "converged",
        "restart": "resume from checkpoint",
        "shutdown": "kill the job",
        "maintenance": "scheduled downtime",
    },
    "oil_refining": {
        "shutdown": "turnaround",
        "equipment": "unit",
        "started": "brought online",
        "stopped": "shut in",
        "pipe": "header",
        "tank": "vessel",
        "worker": "operator",
        "alarm": "trip",
        "check": "round",
        "problem": "upset",
        "leak": "weep",
        "broken": "down",
        "working": "online",
        "temperature": "skin temp",
        "pressure": "back pressure",
        "fix": "isolate and repair",
        "test": "bench test",
        "meeting": "toolbox talk",
        "safety": "PTW",
        "new person": "greenhand",
    },
    "coal_mining": {
        "elevator": "cage",
        "underground area": "face",
        "roof": "top",
        "floor": "pavement",
        "air": "ventilation",
        "gas": "CH4",
        "explosion": "outburst",
        "collapse": "fall of ground",
        "tunnel": "roadway",
        "supervisor": "deputy",
        "worker": "collier",
        "shift start": "descent",
        "shift end": "ascent",
        "drill": "shot firing",
        "conveyor": "belt",
        "pump": "lodgement pump",
        "check": "examination",
        "equipment": "plant",
        "danger": "danger zone",
        "safe": "gas-free",
    },
    "software_company": {
        "approve": "LGTM",
        "looks good": "ship it",
        "small issue": "nit",
        "problem": "bug",
        "big problem": "P0",
        "working on": "in progress",
        "done": "merged",
        "check": "review",
        "meeting": "standup",
        "broken": "borked",
        "fix": "hotfix",
        "temporary fix": "hack",
        "test": "CI",
        "release": "deploy",
        "error": "exception",
        "slow": "perf regression",
        "old code": "legacy",
        "unnecessary work": "bikeshedding",
        "complicated": "spaghetti",
        "simple": "clean",
        "discussion": "RFC",
    },
    "hospital": {
        "emergency": "code blue",
        "patient died": "expired",
        "normal": "WNL",
        "blood pressure": "BP",
        "heart rate": "HR",
        "immediately": "stat",
        "doctor": "attending",
        "medicine": "meds",
        "injection": "shot",
        "IV fluid": "drip",
        "xray": "film",
        "surgery": "OT",
        "report": "chart",
        "check": "vitals",
        "shift": "posting",
        "blood test": "CBC",
        "send home": "discharge",
        "admit": "admit under",
        "getting worse": "deteriorating",
        "getting better": "improving",
    },
    "semiconductor_fab": {
        "dust": "particle",
        "clean": "Class 1",
        "defect": "killer defect",
        "batch": "lot",
        "container": "FOUP",
        "quality": "yield",
        "good": "in-spec",
        "bad": "excursion",
        "machine": "tool",
        "process": "recipe",
        "check": "metrology",
        "inspection": "review",
        "maintenance": "PM",
        "test wafer": "monitor wafer",
        "production": "in-line",
        "error": "misprocess",
        "contamination": "contamination event",
        "fix": "requalify",
        "small": "sub-nm",
        "layer": "film",
    },
    "automobile_assembly": {
        "speed": "JPH",
        "stop": "andon",
        "problem": "defect",
        "worker": "team member",
        "helper": "TL",
        "fix": "rework",
        "inspection": "quality gate",
        "part": "component",
        "delivery": "JIT",
        "robot": "cell",
        "painting": "topcoat",
        "welding": "spot",
        "assembly": "trim",
        "test": "audit",
        "good": "first time through",
        "bad": "scrap",
        "customer complaint": "warranty claim",
        "target": "takt",
        "behind schedule": "below line rate",
        "overtime": "mandatory OT",
    },
    "construction": {
        "meeting": "toolbox talk",
        "crane": "tower crane",
        "rope": "sling",
        "hook": "shackle",
        "concrete": "pour",
        "worker": "fitter",
        "height": "working at height",
        "platform": "scaffold",
        "drawing": "GA drawing",
        "check": "snag list",
        "error": "punch item",
        "fix": "rectify",
        "approval": "IFC",
        "safety": "method statement",
        "plan": "programme",
        "delay": "slippage",
        "done": "completed and signed off",
        "building": "structure",
        "floor": "slab",
        "pillar": "column",
    },
    "call_center": {
        "answer": "pickup",
        "phone call": "interaction",
        "hang up": "disconnect",
        "customer": "caller",
        "angry customer": "escalation",
        "script": "talk track",
        "supervisor": "floor lead",
        "break": "aux time",
        "not available": "on aux",
        "waiting": "in queue",
        "transfer": "warm transfer",
        "quality": "QA score",
        "target": "SLA",
        "speed": "AHT",
        "good": "within SLA",
        "bad": "SLA breach",
        "recording": "call recording",
        "training": "OJT",
        "new person": "new batch",
        "resign": "attrition",
    },
    "logistics_warehouse": {
        "order": "pick ticket",
        "find item": "pick",
        "store item": "putaway",
        "shelf": "rack location",
        "forklift": "MHE",
        "truck": "trailer",
        "loading": "staging",
        "error": "mispick",
        "check": "cycle count",
        "scan": "RF scan",
        "full": "at capacity",
        "empty": "zero stock",
        "rush": "hot order",
        "return": "RMA",
        "damage": "damaged goods",
        "label": "LPN",
        "area": "zone",
        "move": "replenishment",
        "system": "WMS",
        "barcode": "SKU",
    },
}


# ═══════════════════════════════════════════════════════════════════
# INDUSTRY-SPECIFIC SHORT RESPONSES
# Instead of generic "ok", "done", "noted" — use industry style
# ═══════════════════════════════════════════════════════════════════

INDUSTRY_RESPONSES: Dict[str, List[str]] = {
    "ai_research_lab": [
        "LGTM", "ship it", "nit: naming", "ACK", "will rerun",
        "loss looks good", "merged ✅", "eval running", "OOM again 😤",
        "need more VRAM", "checkpoint saved", "diverged. reverting",
        "pushed to main", "CI passing", "needs rebase", "WIP",
    ],
    "oil_refining": [
        "copy that", "roger", "confirmed", "permit signed", "gas free",
        "isolated", "depressured", "locked out", "all clear",
        "panel green", "rounds complete", "handover done",
        "PTW closed", "swap done", "valve lined up",
        "acknowledged", "will check", "on my way", "at the panel",
        "field round done", "no leaks found", "pressures stable",
        "noted in log", "DCS checked", "alarm cleared",
        "pump running", "relief set", "sample taken",
    ],
    "coal_mining": [
        "gas clear", "roof good", "face advanced", "belt running",
        "props in", "shot fired", "all men out", "cage up",
        "deputy passed", "ventilation OK", "pump running",
        "section clear", "manriding stopped", "shift over",
    ],
    "software_company": [
        "LGTM 👍", "ship it!", "merged", "deployed ✅", "CI green",
        "fix is up", "reverted", "on it", "WIP", "will look after lunch",
        "nit but approve", "needs tests", "flaky test, re-running",
        "prod stable", "monitoring", "paged 😴", "false alarm",
        "rebased", "cherry-picked", "pushed", "draft PR up",
        "tests passing now", "good to merge", "approved",
        "checking logs", "looks clean", "needs rebase first",
        "running locally", "works on my machine 🤷", "refactoring",
        "PR updated", "addressed comments", "squashed commits",
        "syncing with main", "build passing", "lint clean",
    ],
    "hospital": [
        "noted", "vitals stable", "med given", "doctor informed",
        "patient sleeping", "BP normal", "drip running", "chart updated",
        "discharge ready", "OT prepared", "code called",
        "crash cart ready", "bloods sent", "report pending",
        "shift handover done", "round complete", "IV changed",
        "saturation normal", "temp 98.4", "patient comfortable",
        "dressing done", "injection given", "NBM confirmed",
        "consent taken", "lab called", "X-ray ordered",
        "doctor on way", "bed ready", "transfer arranged",
        "family informed", "medicine dispensed", "records updated",
    ],
    "semiconductor_fab": [
        "tool qual'd", "lot moved", "recipe loaded", "PM complete",
        "particles clear", "in spec", "SPC normal", "wafer out",
        "FOUP transferred", "chamber seasoned", "yield tracking",
        "excursion noted", "defect review done", "film OK",
    ],
    "automobile_assembly": [
        "line running", "JPH on target", "andon cleared", "quality gate passed",
        "rework done", "parts kitted", "robot OK", "takt met",
        "shift target hit", "FTT 98%", "paint good", "torque verified",
    ],
    "construction": [
        "pour done", "level checked", "scaffold tagged", "crane clear",
        "concrete cured", "rebar tied", "shuttering up", "survey done",
        "permit signed", "lift complete", "plumb checked", "snag cleared",
    ],
    "call_center": [
        "call handled", "escalated", "ticket raised", "SLA met",
        "AHT within range", "caller satisfied", "warm transfer done",
        "aux ending", "back on queue", "break over", "logged in",
    ],
    "logistics_warehouse": [
        "pick complete", "putaway done", "RF scanned", "label printed",
        "staged for dispatch", "cycle count done", "MHE parked",
        "trailer loaded", "zone clear", "stock located", "WMS updated",
    ],
}

# Family-level responses for industries without specific entries
_FAMILY_RESPONSES = {
    "heavy_industry": [
        "running normal", "pressure OK", "temp within limits", "shift handover done",
        "rounds complete", "maintenance logged", "spare parts ordered",
        "permit closed", "isolated", "all clear on floor",
    ],
    "food_processing": [
        "line running", "hygiene check done", "temp logged", "batch recorded",
        "labels verified", "metal detector passed", "CIP complete",
        "samples sent to lab", "GMP compliant", "allergen check done",
    ],
    "agriculture": [
        "watering done", "spraying complete", "all clear", "pump on",
        "field checked", "labor settled", "load sent to market",
        "weather looks ok", "crop healthy", "animals fed",
    ],
    "generic": [
        "ok", "done", "noted", "will do", "on it", "copy",
        "checking", "confirmed", "roger", "understood",
    ],
}


# Map subsectors to response style
_SUBSECTOR_RESPONSE_MAP = {
    "metallurgy": "heavy_industry", "cement": "heavy_industry",
    "chemical": "heavy_industry", "energy": "heavy_industry",
    "power_generation": "heavy_industry", "utility": "heavy_industry",
    "food_processing": "food_processing", "food_beverage": "food_processing",
    "agriculture": "agriculture", "horticulture": "agriculture",
    "livestock": "agriculture", "fisheries": "agriculture",
}


# ═══════════════════════════════════════════════════════════════════
# COMMUNICATION STYLE — How each industry communicates
# ═══════════════════════════════════════════════════════════════════

COMM_STYLE: Dict[str, Dict] = {
    "oil_refining": {
        "style": "radio_procedural",  # Short, clear, protocol-based
        "avg_words": 8,
        "uses_codes": True,
        "formality": 0.7,
        "emoji_rate": 0.02,  # Very low — safety culture
    },
    "software_company": {
        "style": "slack_casual",  # Informal, emoji-heavy, meme culture
        "avg_words": 12,
        "uses_codes": True,  # LGTM, WIP, RFC
        "formality": 0.2,
        "emoji_rate": 0.25,  # High emoji usage
    },
    "ai_research_lab": {
        "style": "slack_technical",  # Casual but technical
        "avg_words": 15,
        "uses_codes": True,
        "formality": 0.3,
        "emoji_rate": 0.15,
    },
    "hospital": {
        "style": "medical_brief",  # Precise, abbreviated, urgent
        "avg_words": 6,
        "uses_codes": True,  # BP, HR, WNL, stat
        "formality": 0.6,
        "emoji_rate": 0.03,
    },
    "coal_mining": {
        "style": "radio_short",  # Very short, safety-critical
        "avg_words": 5,
        "uses_codes": True,
        "formality": 0.5,
        "emoji_rate": 0.01,
    },
    "construction": {
        "style": "site_practical",  # Direct, action-oriented
        "avg_words": 8,
        "uses_codes": False,
        "formality": 0.4,
        "emoji_rate": 0.05,
    },
    "call_center": {
        "style": "professional_scripted",  # Mix of scripted and casual
        "avg_words": 10,
        "uses_codes": True,  # AHT, SLA, FCR
        "formality": 0.5,
        "emoji_rate": 0.10,
    },
}


# ═══════════════════════════════════════════════════════════════════
# LOOKUP FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def apply_jargon(message: str, industry_id: str, rng: random.Random) -> str:
    """Replace generic words with industry-specific jargon.
    
    Only replaces ~30% of matches to avoid over-jargoning.
    """
    jargon = INDUSTRY_JARGON.get(industry_id)
    if not jargon:
        return message
    
    words = message.split()
    modified = False
    
    for i, word in enumerate(words):
        word_lower = word.lower().rstrip(".,!?")
        if word_lower in jargon and rng.random() < 0.30:
            replacement = jargon[word_lower]
            # Preserve original casing style
            if word[0].isupper():
                replacement = replacement.capitalize()
            words[i] = replacement
            modified = True
            break  # Only replace one word per message to keep it natural
    
    return " ".join(words) if modified else message


def get_industry_response(industry_id: str, subsector: str, rng: random.Random) -> str:
    """Get an industry-appropriate short response.
    
    Used instead of generic "ok", "done", "noted".
    """
    # Direct match
    if industry_id in INDUSTRY_RESPONSES:
        return rng.choice(INDUSTRY_RESPONSES[industry_id])
    
    # Family match
    family = _SUBSECTOR_RESPONSE_MAP.get(subsector)
    if family and family in _FAMILY_RESPONSES:
        return rng.choice(_FAMILY_RESPONSES[family])
    
    # Generic
    return rng.choice(_FAMILY_RESPONSES["generic"])


def get_comm_style(industry_id: str) -> Dict:
    """Get the communication style profile for an industry."""
    return COMM_STYLE.get(industry_id, {
        "style": "general",
        "avg_words": 10,
        "uses_codes": False,
        "formality": 0.5,
        "emoji_rate": 0.08,
    })
