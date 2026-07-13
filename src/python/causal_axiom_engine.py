#!/usr/bin/env python3
"""
AXIMA Causal Axiom Engine (CAE) — 8-Layer Universal Reasoning
Invention: Derives causal effects from PHYSICS LAWS, not lookup tables.
Works for ANY object in the universe — even ones never seen before.

Architecture:
  Layer 1: 15 Axiomatic Physics Laws
  Layer 2: Decomposition (suffix + compound split)
  Layer 3: Analogical (nearest known in semantic space)
  Layer 4: Contextual (parse adjectives/modifiers)
  Layer 5: Compositional (multi-object reactions)
  Layer 6: Systemic (social/economic laws)
  Layer 7: Auto-Learn (web → extract → CSE compress → store)
  Layer 8: Honest Gap (admit unknown)

Owner: Ghias / Gowtham Sangadi
"""
import os, json, re, math, hashlib
from typing import Dict, List, Tuple, Optional

# ══════════════════════════════════════════════════════════════
# LAYER 1: 12 AXIOMATIC PHYSICS LAWS
# These are UNIVERSAL — they work for ALL matter, no exceptions
# ══════════════════════════════════════════════════════════════

class PhysicsLaws:
    """15 universal laws that govern all causal physical interactions."""
    
    @staticmethod
    def law_state_change(props, action):
        """LAW 1: Matter transitions solid↔liquid↔gas based on temperature."""
        state = props.get('state', 'solid')
        melt = props.get('melt_temp')
        boil = props.get('boil_temp')
        
        if action in ('heat', 'warm', 'cook', 'bake', 'fry', 'microwave', 'roast', 'grill'):
            if state == 'solid' and melt is not None:
                return f"melts (transitions from solid to liquid at {melt}°C)", 0.95
            cook = props.get('cook_temp')
            if cook is not None:
                return f"cooks — internal structure changes at {cook}°C (proteins denature, texture changes)", 0.92
            if state == 'liquid' and boil is not None:
                return f"boils and evaporates (transitions to gas at {boil}°C)", 0.93
            if state == 'gas':
                return "expands as molecules gain kinetic energy", 0.85
        
        if action in ('cool', 'freeze', 'chill', 'refrigerate'):
            if state == 'liquid':
                fp = melt if melt is not None else 0
                return f"freezes into solid (at {fp}°C)", 0.93
            if state == 'gas':
                bp = boil if boil is not None else 100
                return f"condenses into liquid (at {bp}°C)", 0.90
            if state == 'solid':
                return "becomes more brittle as molecular motion decreases", 0.6
        return None
    
    @staticmethod
    def law_force_fracture(props, action):
        """LAW 2: Force exceeding structural strength → breakage/deformation."""
        fragile = props.get('fragile', False)
        malleable = props.get('malleable', False)
        elastic = props.get('elastic', False)
        
        if action in ('drop', 'hit', 'smash', 'throw', 'slam', 'punch', 'kick', 'strike'):
            if fragile:
                return "shatters or breaks — structure too brittle to absorb impact", 0.92
            if elastic:
                return "absorbs impact and bounces back — elastic structure stores and releases energy", 0.87
            if malleable:
                return "dents or deforms — material yields without breaking", 0.82
            return "withstands impact but may sustain surface damage", 0.65
        return None
    
    @staticmethod
    def law_combustion(props, action):
        """LAW 4: Organic material + O2 + ignition → CO2 + H2O + energy."""
        flammable = props.get('flammable', False)
        burn_temp = props.get('burn_temp')
        
        if action in ('burn', 'ignite', 'light', 'set_fire'):
            if flammable:
                t = f" (ignites at {burn_temp}°C)" if burn_temp else ""
                return f"burns — undergoes rapid oxidation releasing heat, light, smoke, and ash{t}", 0.94
            return "resists burning — not flammable (insufficient organic content or too stable)", 0.88
        
        if action in ('heat', 'warm', 'cook') and flammable and burn_temp:
            # Heat can cause combustion if object is flammable and has no melt point
            if props.get('melt_temp') is None:
                return f"catches fire and burns (auto-ignition at {burn_temp}°C)", 0.88
        return None
    
    @staticmethod
    def law_dissolution(props, action):
        """LAW 5: Similar dissolves similar. Polar in polar, nonpolar in nonpolar."""
        soluble = props.get('soluble', False)
        state = props.get('state', 'solid')
        
        if action in ('dissolve', 'mix_in_water', 'submerge', 'soak'):
            if soluble:
                return "dissolves — ionic/polar bonds break apart in solvent", 0.93
            if state == 'solid' and props.get('category') in ('metal', 'ceramic', 'mineral'):
                return "does not dissolve — molecular structure too stable for solvent", 0.90
        return None
    
    @staticmethod
    def law_gravity(props, action):
        """LAW 6: Mass attracted toward center of gravity. Dense sinks in fluid."""
        dense = props.get('dense', False)
        state = props.get('state', 'solid')
        
        if action in ('submerge', 'put_in_water', 'drop_in_water', 'place_in_liquid'):
            if dense:
                return "sinks — density exceeds surrounding fluid", 0.88
            if state == 'solid' and not dense:
                return "floats — density less than surrounding fluid", 0.83
        return None
    
    @staticmethod
    def law_elasticity(props, action):
        """LAW 7: Below yield point → returns. Above → permanent deformation."""
        elastic = props.get('elastic', False)
        fragile = props.get('fragile', False)
        malleable = props.get('malleable', False)
        
        if action in ('stretch', 'pull', 'bend', 'compress', 'squeeze', 'twist'):
            if elastic:
                return "deforms elastically and returns to original shape — stored energy released", 0.90
            if fragile:
                return "snaps or fractures — brittle materials cannot flex", 0.88
            if malleable:
                return "permanently deforms into new shape — material yields past breaking point", 0.82
            return "resists deformation — rigid structure", 0.65
        return None
    
    @staticmethod
    def law_conductivity(props, action):
        """LAW 8: Free electrons → conducts electricity. No free electrons → insulates."""
        conductive = props.get('conductive', False)
        
        if action in ('electrify', 'shock', 'zap', 'apply_current', 'electrocute'):
            if conductive:
                return "conducts electricity — free electrons carry current (can heat up, spark, or damage)", 0.91
            return "insulates — blocks current flow (no free charge carriers)", 0.88
        return None
    
    @staticmethod
    def law_magnetism(props, action):
        """LAW 9: Ferromagnetic materials (unpaired d-electrons) → attracted by magnets."""
        magnetic = props.get('magnetic', False)
        
        if action in ('magnetize', 'magnet', 'apply_magnet', 'magnetic_field'):
            if magnetic:
                return "attracted to magnet and sticks — ferromagnetic domains align with field", 0.93
            return "not affected by magnet — no ferromagnetic properties", 0.90
        return None
    
    @staticmethod
    def law_oxidation(props, action):
        """LAW 10: Reactive metal + O2 + time → oxide layer."""
        corrodes = props.get('corrodes', False)
        category = props.get('category', '')
        
        if action in ('expose_to_air', 'leave_outside', 'wet', 'expose_to_water'):
            if corrodes:
                return "oxidizes over time — forms rust/tarnish layer on surface", 0.82
            if category == 'metal' and not corrodes:
                return "remains unchanged — resistant to oxidation (noble metal or protective layer)", 0.85
        return None
    
    @staticmethod
    def law_pressure(props, action):
        """LAW 11: Confined gas: less volume → more pressure → more temperature."""
        state = props.get('state', 'solid')
        
        if action in ('compress', 'squeeze', 'pressurize'):
            if state == 'gas':
                return "pressure and temperature increase — gas molecules forced closer together (PV=nRT)", 0.93
            if state == 'liquid':
                return "barely compresses — liquids are nearly incompressible", 0.87
        return None
    
    @staticmethod
    def law_cutting(props, action):
        """Supplemental: Shear force separates material."""
        fragile = props.get('fragile', False)
        category = props.get('category', '')
        
        if action in ('cut', 'slice', 'chop', 'tear', 'saw'):
            if category in ('fabric', 'paper', 'organic', 'food', 'fat'):
                return "cuts easily — soft/fibrous material separates cleanly", 0.93
            if fragile:
                return "splits or shatters along fracture lines", 0.85
            if category in ('metal',):
                return "requires significant force — metallic bonds resist shearing", 0.75
            if category in ('mineral', 'ceramic'):
                return "chips or cracks — crystalline structure fractures along planes", 0.80
            return "separates when sufficient force applied", 0.70
        return None

    @staticmethod
    def law_pour(props, action):
        """LAW: Pouring liquid onto object — effects depend on liquid and target properties."""
        if action not in ('pour', 'pour_water', 'pour_acid', 'splash', 'douse', 'drench'):
            return None
        
        category = props.get('category', '')
        flammable = props.get('flammable', False)
        conductive = props.get('conductive', False)
        soluble = props.get('soluble', False)
        state = props.get('state', 'solid')
        
        # If the object IS liquid (water/acid being poured), describe the pouring effect
        if state == 'liquid':
            if category in ('acid',):
                return "acid dissolves the target — corrosive reaction on contact", 0.88
            return "liquid spreads over target — may extinguish fire, cause short circuits, or dissolve soluble materials", 0.80
        
        # Pour water on fire/flammable burning → extinguish
        if flammable and category in ('organic', 'fabric', 'paper'):
            return "extinguishes if burning — water removes heat and smothers flames", 0.88
        
        # Pour water on electronics/conductive → short circuit
        if conductive and category in ('metal', 'electronic', 'polymer'):
            return "causes short circuit — water bridges electrical contacts, potentially destroying the device", 0.90
        
        # Pour acid → dissolves
        if category in ('metal',):
            return "acid dissolves the metal — produces hydrogen gas and a salt", 0.88
        if category in ('mineral', 'carbonate'):
            return "acid dissolves it with fizzing — produces carbon dioxide gas", 0.87
        if soluble:
            return "dissolves — substance breaks apart in the liquid", 0.85
        
        return None

    @staticmethod
    def law_throw(props, action):
        """LAW: Throwing object at target — similar to drop but with directed force."""
        if action not in ('throw', 'hurl', 'fling', 'toss', 'launch', 'pitch'):
            return None
        
        fragile = props.get('fragile', False)
        dense = props.get('dense', False)
        elastic = props.get('elastic', False)
        malleable = props.get('malleable', False)
        
        if fragile:
            return "shatters on impact — thrown force exceeds structural integrity", 0.92
        if dense and not elastic:
            return "dents or damages the target on impact — heavy mass transfers kinetic energy", 0.85
        if elastic:
            return "bounces off target — elastic material absorbs and redirects energy", 0.83
        if malleable:
            return "deforms on impact — soft material flattens against target", 0.80
        return "impacts target with force proportional to mass and velocity", 0.70


    @staticmethod
    def law_pour(props, action):
        """Supplemental: Pouring liquid onto something."""
        if action not in ('pour', 'splash', 'spill', 'drench'):
            return None
        flammable = props.get('flammable', False)
        conductive = props.get('conductive', False)
        state = props.get('state', 'solid')
        if state == 'gas':
            return "liquid passes through — gas is displaced momentarily", 0.7
        if conductive:
            return "can cause short circuit if electronics — water and electricity don't mix", 0.85
        if flammable and props.get('burn_temp'):
            return "if currently burning, fire is extinguished (water removes heat)", 0.9
        return "gets wet — surface absorbs or repels liquid depending on material", 0.7

    @staticmethod
    def law_throw(props, action):
        """Supplemental: Throwing object at a target (impact)."""
        if action not in ('throw', 'hurl', 'toss', 'launch', 'fling'):
            return None
        fragile = props.get('fragile', False)
        dense = props.get('dense', False)
        elastic = props.get('elastic', False)
        if fragile:
            return "shatters or breaks on impact — fragile material cannot survive collision", 0.9
        if elastic:
            return "bounces off — elastic material absorbs and redirects energy", 0.8
        if dense:
            return "hits hard and may damage the target — heavy dense object carries more momentum", 0.85
        return "hits the target — impact force depends on mass and velocity", 0.7

    @staticmethod
    def law_biological(props, action):
        """Supplemental: Eating, washing, biological actions."""
        category = props.get('category', '')
        if action in ('eat', 'ingest', 'swallow', 'consume'):
            if category == 'food':
                cook_temp = props.get('cook_temp')
                if cook_temp:
                    return "safe to eat when properly cooked — raw may contain harmful bacteria", 0.8
                return "can be consumed — provides nutrition", 0.8
            if props.get('flammable') and category not in ('food', 'organic'):
                return "TOXIC — do not eat. Can cause poisoning, organ damage, or death", 0.95
            return "NOT food — ingesting this material is harmful or dangerous", 0.9
        if action in ('wash', 'rinse', 'clean'):
            if category in ('fabric', 'organic'):
                return "gets clean — water and soap remove dirt and oils", 0.85
            if category == 'metal' and props.get('corrodes'):
                return "clean but may rust later if not dried — water triggers oxidation", 0.8
            return "surface gets cleaned — water removes contaminants", 0.75
        return None

    @staticmethod
    def law_deformation(props, action):
        """Supplemental: Bending, twisting, shaking, inflating."""
        elastic = props.get('elastic', False)
        fragile = props.get('fragile', False)
        malleable = props.get('malleable', False)
        if action in ('bend', 'twist', 'fold'):
            if elastic:
                return "flexes and returns to shape — material is elastic", 0.88
            if malleable:
                return "permanently bends — ductile material deforms without breaking", 0.85
            if fragile:
                return "snaps or cracks — brittle material cannot flex", 0.88
            return "resists bending — rigid structure", 0.65
        if action in ('shake', 'vibrate', 'rattle'):
            if fragile:
                return "can crack or break — vibration weakens brittle structure", 0.7
            if props.get('state') == 'liquid':
                return "sloshes around — liquid moves freely within container", 0.85
            return "vibrates but holds together — solid structure absorbs motion", 0.7
        if action in ('inflate', 'pump', 'blow_up'):
            if elastic:
                return "expands as air fills it — stretches until pressure equalizes or it bursts", 0.88
            if fragile:
                return "can rupture — pressure exceeds structural strength", 0.8
            return "resists inflation — material is not flexible enough", 0.6
        if action in ('explode', 'detonate', 'blow_up'):
            if props.get('flammable'):
                return "explodes violently — rapid combustion releases enormous energy as shockwave", 0.9
            return "destroyed by the blast — shockwave shatters or deforms material", 0.85
        return None

    def apply_all(self, props, action):
        """Try all laws. Return first match with highest confidence."""
        laws = [
            self.law_state_change,
            self.law_force_fracture,
            self.law_combustion,
            self.law_dissolution,
            self.law_gravity,
            self.law_elasticity,
            self.law_conductivity,
            self.law_magnetism,
            self.law_oxidation,
            self.law_pressure,
            self.law_cutting,
            self.law_pour,
            self.law_throw,
            self.law_biological,
            self.law_deformation,
            self.law_pour,
            self.law_throw,
        ]
        
        results = []
        for law_fn in laws:
            result = law_fn(props, action)
            if result:
                effect, conf = result
                results.append((effect, conf, law_fn.__doc__.split(':')[0].strip()))
        
        if not results:
            return None
        
        # Return highest confidence
        results.sort(key=lambda x: x[1], reverse=True)
        return results[0]


# ══════════════════════════════════════════════════════════════
# LAYER 2: DECOMPOSITION — Figure out properties from the WORD
# ══════════════════════════════════════════════════════════════

# Suffix → likely category (checked longest first)
SUFFIX_MAP = [
    ('ium', 'metal'), ('inum', 'metal'), ('steel', 'metal'),
    ('ite', 'mineral'), ('ite', 'mineral'), ('ite', 'mineral'),
    ('glass', 'ceramic'), ('ware', 'ceramic'), ('crete', 'mineral'),
    ('wood', 'organic'), ('bark', 'organic'), ('fiber', 'fabric'),
    ('stone', 'mineral'), ('ite', 'mineral'),
    ('ene', 'organic'), ('ane', 'organic'), ('yne', 'organic'), ('ol', 'organic'),
    ('ide', 'chemical'), ('ate', 'chemical'),
]

# Prefix/component → property hints
COMPONENT_HINTS = {
    'ice': {'state': 'solid', 'melt_temp': 0, 'fragile': True, 'category': 'frozen_liquid'},
    'snow': {'state': 'solid', 'melt_temp': 0, 'fragile': True, 'category': 'frozen_liquid'},
    'frozen': {'state': 'solid', 'melt_temp': 0, 'category': 'frozen_liquid'},
    'glass': {'fragile': True, 'melt_temp': 1400, 'category': 'ceramic'},
    'crystal': {'fragile': True, 'category': 'ceramic'},
    'metal': {'conductive': True, 'magnetic': True, 'malleable': True, 'dense': True, 'category': 'metal'},
    'steel': {'conductive': True, 'malleable': True, 'dense': True, 'category': 'metal', 'melt_temp': 1370},
    'iron': {'conductive': True, 'magnetic': True, 'dense': True, 'corrodes': True, 'category': 'metal'},
    'gold': {'conductive': True, 'dense': True, 'malleable': True, 'category': 'metal'},
    'rubber': {'elastic': True, 'flammable': True, 'category': 'polymer'},
    'plastic': {'flammable': True, 'melt_temp': 150, 'category': 'polymer'},
    'wood': {'flammable': True, 'burn_temp': 300, 'category': 'organic'},
    'paper': {'flammable': True, 'fragile': True, 'burn_temp': 233, 'category': 'organic'},
    'stone': {'dense': True, 'fragile': False, 'melt_temp': 1200, 'category': 'mineral'},
    'rock': {'dense': True, 'fragile': False, 'category': 'mineral'},
    'silk': {'flammable': True, 'fragile': False, 'category': 'fabric'},
    'cotton': {'flammable': True, 'burn_temp': 255, 'category': 'fabric'},
    'leather': {'flammable': True, 'category': 'organic'},
    'ceramic': {'fragile': True, 'melt_temp': 1600, 'category': 'ceramic'},
    'wax': {'melt_temp': 60, 'flammable': True, 'category': 'organic'},
    'candle': {'melt_temp': 60, 'flammable': True, 'category': 'organic'},
    'oil': {'flammable': True, 'state': 'liquid', 'category': 'liquid'},
    'acid': {'state': 'liquid', 'category': 'acid'},
    'water': {'state': 'liquid', 'boil_temp': 100, 'melt_temp': 0},
    'foam': {'fragile': True, 'elastic': True, 'dense': False},
    'concrete': {'dense': True, 'fragile': True, 'category': 'mineral'},
    'brick': {'fragile': True, 'dense': True, 'category': 'ceramic'},
    'bungee': {'elastic': True, 'category': 'polymer'},
    'elastic': {'elastic': True, 'category': 'polymer'},
    'spring': {'elastic': True, 'category': 'metal'},
    'sponge': {'elastic': True, 'fragile': False, 'dense': False},
    'balloon': {'elastic': True, 'fragile': True, 'category': 'polymer'},
    'tire': {'elastic': True, 'flammable': True, 'category': 'polymer'},
    'cord': {'category': 'fabric'},
    'helium': {'state': 'gas', 'flammable': False, 'dense': False, 'category': 'gas'},
    'hydrogen': {'state': 'gas', 'flammable': True, 'category': 'gas'},
    'oxygen': {'state': 'gas', 'flammable': False, 'category': 'gas'},
    'nitrogen': {'state': 'gas', 'flammable': False, 'category': 'gas'},
    'air': {'state': 'gas', 'flammable': False, 'category': 'gas'},
    'gas': {'state': 'gas', 'category': 'gas'},
    'wire': {'conductive': True, 'malleable': True, 'category': 'metal'},
    'chain': {'conductive': True, 'malleable': False, 'category': 'metal'},
    'pipe': {'conductive': True, 'category': 'metal'},
    'blade': {'category': 'metal', 'conductive': True},
    'cloth': {'flammable': True, 'category': 'fabric'},
    'fabric': {'flammable': True, 'category': 'fabric'},
    'juice': {'state': 'liquid', 'melt_temp': -2, 'boil_temp': 100},
    'milk': {'state': 'liquid', 'melt_temp': -1, 'boil_temp': 100},
    'soup': {'state': 'liquid', 'melt_temp': -2, 'boil_temp': 100},
    'cream': {'state': 'liquid', 'melt_temp': -2},
    'yogurt': {'state': 'solid', 'melt_temp': -5},
    'butter': {'state': 'solid', 'melt_temp': 35},
    'chocolate': {'state': 'solid', 'melt_temp': 34},
    'cheese': {'state': 'solid', 'melt_temp': 65, 'flammable': False},
    'cat': {'state': 'solid', 'elastic': True, 'fragile': False, 'category': 'living'},
    'dog': {'state': 'solid', 'elastic': True, 'fragile': False, 'category': 'living'},
    'human': {'state': 'solid', 'fragile': True, 'category': 'living'},
    'bird': {'state': 'solid', 'fragile': True, 'dense': False, 'category': 'living'},
    'fish': {'state': 'solid', 'elastic': True, 'category': 'living'},
    'insect': {'state': 'solid', 'fragile': True, 'dense': False, 'category': 'living'},
    'plant': {'state': 'solid', 'fragile': True, 'flammable': True, 'category': 'living'},
}

def decompose_object(name):
    """Layer 2: Extract properties from word structure."""
    name_lower = name.lower().strip()
    props = {'state': 'solid'}  # default
    confidence = 0.0
    
    # Strategy 1: Check if name contains a known component
    for component, hints in COMPONENT_HINTS.items():
        if component in name_lower:
            props.update(hints)
            confidence = max(confidence, 0.75)
    
    # Strategy 2: Suffix analysis (only match when word is long enough to avoid false positives)
    for suffix, category in SUFFIX_MAP:
        if name_lower.endswith(suffix) and len(name_lower) > 6 and len(name_lower) - len(suffix) > 2:
            props['category'] = category
            # Apply category defaults
            cat_defaults = {
                'metal': {'conductive': True, 'dense': True, 'malleable': True, 'melt_temp': 1000, 'magnetic': True},
                'mineral': {'dense': True, 'fragile': True, 'melt_temp': 1200},
                'ceramic': {'fragile': True, 'melt_temp': 1500},
                'organic': {'flammable': True, 'burn_temp': 300},
                'fabric': {'flammable': True, 'burn_temp': 250},
                'chemical': {'state': 'liquid'},
            }
            if category in cat_defaults:
                for k, v in cat_defaults[category].items():
                    if k not in props:
                        props[k] = v
            confidence = max(confidence, 0.7)
            break
    
    # Strategy 3: Compound word split (hyphen, space, camelCase)
    parts = re.split(r'[-_ ]', name_lower)
    if len(parts) == 1 and len(name_lower) > 6:
        # Try known prefixes
        for i in range(3, len(name_lower)-2):
            prefix = name_lower[:i]
            suffix_part = name_lower[i:]
            if prefix in COMPONENT_HINTS:
                props.update(COMPONENT_HINTS[prefix])
                confidence = max(confidence, 0.7)
                break
            if suffix_part in COMPONENT_HINTS:
                props.update(COMPONENT_HINTS[suffix_part])
                confidence = max(confidence, 0.7)
                break
    elif len(parts) > 1:
        for part in parts:
            if part in COMPONENT_HINTS:
                props.update(COMPONENT_HINTS[part])
                confidence = max(confidence, 0.8)
    
    return props, confidence


# ══════════════════════════════════════════════════════════════
# LAYER 3: ANALOGICAL — Find nearest known concept
# ══════════════════════════════════════════════════════════════

def analogical_transfer(name, knowledge_store):
    """Layer 3: Find nearest known material by character similarity."""
    if not knowledge_store:
        return {}, 0.0
    
    name_lower = name.lower()
    best_match = None
    best_score = 0.0
    
    for known_name, known_props in knowledge_store.items():
        # LCS ratio (our semantic brain technique)
        score = _lcs_ratio(name_lower, known_name.lower())
        if score > best_score:
            best_score = score
            best_match = known_props
    
    if best_score > 0.6 and best_match:
        # Transfer with confidence decay
        transferred = {}
        for k, v in best_match.items():
            transferred[k] = v
        return transferred, best_score * 0.8  # 80% of match confidence
    
    return {}, 0.0

def _lcs_ratio(a, b):
    """Longest common subsequence ratio."""
    if not a or not b:
        return 0.0
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    lcs_len = dp[m][n]
    return (2.0 * lcs_len) / (m + n)


# ══════════════════════════════════════════════════════════════
# LAYER 4: CONTEXTUAL — Parse the question for property clues
# ══════════════════════════════════════════════════════════════

ADJECTIVE_PROPERTIES = {
    'frozen': {'state': 'solid', 'melt_temp': 0},
    'cold': {'state': 'solid', 'melt_temp': 0},
    'icy': {'state': 'solid', 'melt_temp': 0, 'fragile': True},
    'hot': {'state': 'liquid'},
    'molten': {'state': 'liquid'},
    'liquid': {'state': 'liquid'},
    'solid': {'state': 'solid'},
    'heavy': {'dense': True},
    'light': {'dense': False},
    'thin': {'fragile': True},
    'thick': {'fragile': False},
    'brittle': {'fragile': True},
    'fragile': {'fragile': True},
    'flexible': {'elastic': True},
    'elastic': {'elastic': True},
    'rigid': {'elastic': False, 'malleable': False},
    'soft': {'malleable': True},
    'hard': {'malleable': False},
    'metal': {'conductive': True, 'dense': True, 'category': 'metal'},
    'metallic': {'conductive': True, 'dense': True, 'category': 'metal'},
    'wooden': {'flammable': True, 'burn_temp': 300, 'category': 'organic'},
    'glass': {'fragile': True, 'category': 'ceramic'},
    'rubber': {'elastic': True, 'category': 'polymer'},
    'plastic': {'melt_temp': 150, 'category': 'polymer'},
    'paper': {'flammable': True, 'fragile': True, 'category': 'organic'},
    'ceramic': {'fragile': True, 'category': 'ceramic'},
    'porcelain': {'fragile': True, 'category': 'ceramic'},
    'crystal': {'fragile': True, 'category': 'ceramic'},
    'stone': {'dense': True, 'category': 'mineral'},
    'steel': {'conductive': True, 'dense': True, 'category': 'metal'},
    'iron': {'conductive': True, 'magnetic': True, 'category': 'metal'},
    'copper': {'conductive': True, 'category': 'metal'},
    'wet': {'state': 'liquid'},
    'dry': {},
    'flammable': {'flammable': True},
    'explosive': {'flammable': True},
    'magnetic': {'magnetic': True},
    'old': {'corrodes': True},
    'rusty': {'corrodes': True},
    'new': {},
    'large': {},
    'small': {},
    'tiny': {'fragile': True},
    'massive': {'dense': True},
}

def contextual_extraction(full_question, obj_name):
    """Layer 4: Parse adjectives and modifiers from the question text."""
    props = {}
    confidence = 0.0
    
    # Get words before the object name
    q_lower = full_question.lower()
    obj_lower = obj_name.lower()
    
    # Find words around the object
    words = q_lower.split()
    
    for word in words:
        if word in ADJECTIVE_PROPERTIES:
            props.update(ADJECTIVE_PROPERTIES[word])
            confidence = max(confidence, 0.7)
    
    # Also check if object name itself contains material hints
    # "glass bottle" → glass properties
    # "rubber duck" → rubber properties
    for word in obj_lower.split():
        if word in ADJECTIVE_PROPERTIES:
            props.update(ADJECTIVE_PROPERTIES[word])
            confidence = max(confidence, 0.8)
    
    return props, confidence


# ══════════════════════════════════════════════════════════════
# LAYER 5: COMPOSITIONAL — Multi-object reactions
# ══════════════════════════════════════════════════════════════

REACTIVE_PAIRS = {
    # (category_A, category_B): effect
    ('acid', 'base'): "neutralization reaction — produces water and salt",
    ('acid', 'metal'): "produces hydrogen gas and a salt — metal dissolves",
    ('oxidizer', 'fuel'): "combustion or explosion — rapid energy release",
    ('water', 'alkali_metal'): "violent explosion — produces hydrogen gas and heat",
    ('acid', 'carbonate'): "fizzing — produces carbon dioxide gas",
    ('bleach', 'acid'): "produces toxic chlorine gas — extremely dangerous",
    ('bleach', 'ammonia'): "produces toxic chloramine gas — lethal in enclosed spaces",
}

SUBSTANCE_CATEGORIES = {
    'vinegar': 'acid', 'lemon juice': 'acid', 'hydrochloric acid': 'acid',
    'sulfuric acid': 'acid', 'citric acid': 'acid', 'battery acid': 'acid',
    'baking soda': 'base', 'sodium hydroxide': 'base', 'lye': 'base',
    'ammonia': 'ammonia', 'bleach': 'bleach',
    'sodium': 'alkali_metal', 'potassium': 'alkali_metal', 'lithium': 'alkali_metal',
    'gasoline': 'fuel', 'oil': 'fuel', 'alcohol': 'fuel', 'propane': 'fuel',
    'hydrogen peroxide': 'oxidizer', 'oxygen': 'oxidizer',
    'water': 'water', 'limestone': 'carbonate', 'chalk': 'carbonate',
    'marble': 'carbonate', 'sodium bicarbonate': 'carbonate',
}

def compositional_reaction(obj_a, obj_b):
    """Layer 5: Check if mixing two substances causes a reaction."""
    cat_a = SUBSTANCE_CATEGORIES.get(obj_a.lower())
    cat_b = SUBSTANCE_CATEGORIES.get(obj_b.lower())
    
    if not cat_a or not cat_b:
        return None
    
    # Check both orderings
    key1 = (cat_a, cat_b)
    key2 = (cat_b, cat_a)
    
    if key1 in REACTIVE_PAIRS:
        return REACTIVE_PAIRS[key1], 0.92
    if key2 in REACTIVE_PAIRS:
        return REACTIVE_PAIRS[key2], 0.92
    
    return None


# ══════════════════════════════════════════════════════════════
# LAYER 6: SYSTEMIC — Social/Economic/Organizational causality
# ══════════════════════════════════════════════════════════════

SYSTEMIC_RULES = [
    # (trigger_patterns, effect, probability)
    (['insult', 'disrespect', 'offend'], 'authority',
     "provokes anger and potential punishment proportional to their power", 0.85),
    (['insult', 'disrespect', 'offend'], 'friend',
     "damages the relationship — trust is hard to rebuild", 0.80),
    (['ignore', 'neglect'], 'warning',
     "increases probability of the warned danger occurring", 0.88),
    (['ignore', 'neglect'], 'responsibility',
     "consequences accumulate until they become unmanageable", 0.82),
    (['lie', 'deceive', 'cheat'], 'person',
     "erodes trust — once discovered, credibility is destroyed", 0.87),
    (['steal', 'rob', 'take'], 'property',
     "legal consequences + loss of trust + potential conflict", 0.90),
    (['help', 'assist', 'support'], 'person',
     "builds goodwill, strengthens relationship, creates reciprocity", 0.80),
    (['save', 'invest'], 'money',
     "grows over time through compound interest/returns", 0.75),
    (['spend', 'waste'], 'money',
     "depletes resources — poverty if continued without income", 0.80),
    (['study', 'practice', 'train'], 'skill',
     "improves over time — mastery follows deliberate practice", 0.85),
    (['ignore', 'skip'], 'exercise',
     "health deteriorates gradually — muscle atrophy, weight gain", 0.75),
    (['overpromise', 'underdeliver'], 'reputation',
     "credibility erodes — people stop trusting your word", 0.82),
    (['monopolize', 'dominate'], 'market',
     "prices rise, innovation slows, consumers suffer", 0.78),
    (['educate', 'teach'], 'population',
     "economic productivity rises, crime drops, health improves", 0.80),
    (['censor', 'suppress'], 'information',
     "public loses trust in institutions, underground channels form", 0.75),
    (['tax', 'regulate'], 'industry',
     "slows growth short-term but may stabilize long-term", 0.65),
    (['deforest', 'pollute', 'dump'], 'environment',
     "ecosystem degrades — biodiversity loss, climate effects, health risks", 0.88),
    (['vaccinate'], 'population',
     "disease spread slows dramatically — herd immunity reached at 70-95%", 0.90),
]

def systemic_reasoning(action, target):
    """Layer 6: Apply social/economic/organizational causal laws."""
    action_lower = action.lower()
    target_lower = target.lower()
    
    for triggers, target_type, effect, prob in SYSTEMIC_RULES:
        if any(t in action_lower for t in triggers):
            if target_type in target_lower or target_lower in target_type:
                return effect, prob
    
    # Broader match: just action triggers
    for triggers, target_type, effect, prob in SYSTEMIC_RULES:
        if any(t in action_lower for t in triggers):
            return f"{effect} (when applied to {target})", prob * 0.7
    
    return None


# ══════════════════════════════════════════════════════════════
# LAYER 7: AUTO-LEARN — Search web, extract, compress, store
# ══════════════════════════════════════════════════════════════

class CausalKnowledgeStore:
    """CSE-compressed material knowledge. Unified with cse_knowledge.py."""
    
    STORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'causal_knowledge.json')
    
    def __init__(self):
        self.materials = {}  # name → {properties}
        # Try CSE unified store first
        try:
            from cse_knowledge import get_knowledge
            self._cse = get_knowledge()
            self._use_cse = True
        except:
            self._cse = None
            self._use_cse = False
            self._load()
    
    def _load(self):
        """Load from legacy JSON (fallback if CSE unavailable)."""
        if os.path.isfile(self.STORE_PATH):
            try:
                with open(self.STORE_PATH, 'r') as f:
                    self.materials = json.load(f)
            except:
                self.materials = {}
    
    def _save(self):
        """Save to disk."""
        try:
            os.makedirs(os.path.dirname(self.STORE_PATH), exist_ok=True)
            with open(self.STORE_PATH, 'w') as f:
                json.dump(self.materials, f, separators=(',', ':'))
        except:
            pass
    
    def get(self, name):
        """Lookup material properties. CSE first, then JSON fallback."""
        if self._use_cse:
            props = self._cse.get_material_props(name)
            if props:
                return props
        return self.materials.get(name.lower())
    
    def store(self, name, properties):
        """Store new material (goes to JSON for now, CSE rebuild needed)."""
        self.materials[name.lower()] = properties
        self._save()
    
    def has(self, name):
        if self._use_cse and self._cse.has(name):
            return True
        return name.lower() in self.materials
    
    def size(self):
        if self._use_cse:
            return self._cse.size()
        return len(self.materials)
    
    def all_names(self):
        if self._use_cse:
            return set(k for k in self._cse._cache.keys())
        return set(self.materials.keys())


def auto_learn_material(obj_name, store):
    """Layer 7: Search web for material properties, extract, store in CSE."""
    try:
        from online_search import search_multi
    except ImportError:
        try:
            from web_search import search_web
            def search_multi(q, **kw):
                r = search_web(q)
                return r if r else None
        except:
            return None
    
    # Targeted query for physical properties
    query = f"{obj_name} material properties physical"
    try:
        result = search_multi(query, max_sources=2, timeout=5)
    except:
        result = None
    
    if not result:
        return None
    
    # Extract properties from text using pattern matching
    text = str(result).lower() if result else ""
    props = {'state': 'solid'}  # default
    
    # Extract melting point
    m = re.search(r'melt(?:ing)?\s*(?:point|temp).*?(\d+)\s*°?[ck°]', text)
    if m:
        props['melt_temp'] = int(m.group(1))
    
    # Extract boiling point
    m = re.search(r'boil(?:ing)?\s*(?:point|temp).*?(\d+)\s*°?[ck°]', text)
    if m:
        props['boil_temp'] = int(m.group(1))
    
    # Detect flammability
    if any(w in text for w in ['flammable', 'combustible', 'burns easily', 'catches fire']):
        props['flammable'] = True
    elif any(w in text for w in ['non-flammable', 'fire-resistant', 'fireproof']):
        props['flammable'] = False
    
    # Detect fragility
    if any(w in text for w in ['brittle', 'fragile', 'breaks easily', 'shatters']):
        props['fragile'] = True
    
    # Detect density
    if any(w in text for w in ['dense', 'heavy', 'high density']):
        props['dense'] = True
    elif any(w in text for w in ['lightweight', 'light', 'low density', 'ultralight']):
        props['dense'] = False
    
    # Detect elasticity
    if any(w in text for w in ['elastic', 'flexible', 'stretchy', 'rubber-like']):
        props['elastic'] = True
    
    # Detect conductivity
    if any(w in text for w in ['conducts', 'conductive', 'conductor']):
        props['conductive'] = True
    elif any(w in text for w in ['insulator', 'insulating', 'non-conductive']):
        props['conductive'] = False
    
    # Detect category
    if any(w in text for w in ['metal', 'alloy', 'metallic']):
        props['category'] = 'metal'
    elif any(w in text for w in ['ceramic', 'porcelain', 'clay']):
        props['category'] = 'ceramic'
    elif any(w in text for w in ['polymer', 'plastic', 'resin']):
        props['category'] = 'polymer'
    elif any(w in text for w in ['organic', 'biological', 'carbon-based']):
        props['category'] = 'organic'
    elif any(w in text for w in ['mineral', 'rock', 'geological']):
        props['category'] = 'mineral'
    
    # Detect state
    if any(w in text for w in ['liquid at room', 'fluid']):
        props['state'] = 'liquid'
    elif any(w in text for w in ['gas at room', 'gaseous']):
        props['state'] = 'gas'
    
    # Only store if we extracted meaningful properties (more than just state)
    if len(props) > 1:
        store.store(obj_name, props)
        return props
    
    return None


# ══════════════════════════════════════════════════════════════
# MAIN ENGINE: 8-Layer Causal Axiom Engine (CAE)
# ══════════════════════════════════════════════════════════════

class CausalAxiomEngine:
    """
    The complete 8-layer universal causal reasoning system.
    Works for ANY object. Gets smarter with every question.
    """
    
    def __init__(self):
        self.physics = PhysicsLaws()
        self.store = CausalKnowledgeStore()
        self._queries_answered = 0
        self._web_lookups = 0
    
    _cache = {}  # Memoization cache for repeated queries
    
    def reason(self, action, obj_name, context=None, full_question="", allow_web=False):
        """
        8-layer causal reasoning. Returns (effect, confidence, layer_used, reasoning).
        
        action: what's being done (heat, drop, cut, burn...)
        obj_name: target object
        context: optional (in water, with acid...)
        full_question: original question text for contextual clues
        allow_web: if True, Layer 7 can search web for unknown objects
        """
        self._queries_answered += 1
        
        # Cache check
        cache_key = (action, obj_name, context)
        if cache_key in self._cache:
            self._queries_answered += 1
            return self._cache[cache_key]
        
        # ─── PRE-PROCESSING: strip possessives, plurals, articles ───
        import re as _re
        obj_name = _re.sub(r'^(my|your|his|her|its|our|their|this|that|these|those|some) ', '', obj_name)
        # Try singular if not found
        obj_singular = obj_name.rstrip('s') if obj_name.endswith('s') and not obj_name.endswith('ss') else obj_name
        if obj_name.endswith('es') and len(obj_name) > 4:
            obj_singular = obj_name[:-2]
        
        # ─── LAYER 1: Check knowledge store (CSE-compressed) ───
        stored_props = self.store.get(obj_name) or self.store.get(obj_singular)
        # Try singular/plural forms if not found
        if stored_props is None:
            if obj_name.endswith('es'):
                stored_props = self.store.get(obj_name[:-2])
            if stored_props is None and obj_name.endswith('s'):
                stored_props = self.store.get(obj_name.rstrip('s'))
            if stored_props is None:
                stored_props = self.store.get(obj_name + 's')
        if stored_props:
            result = self.physics.apply_all(stored_props, action)
            if result:
                effect, conf, law = result
                return effect, conf, "L1:AXIOM+KNOWN", f"{obj_name} (known) → {law}"
        
        # ─── LAYER 2: Decomposition ───
        decomp_props, decomp_conf = decompose_object(obj_name)
        if decomp_conf >= 0.7:
            result = self.physics.apply_all(decomp_props, action)
            if result:
                effect, conf, law = result
                return effect, min(conf, decomp_conf), "L2:DECOMPOSE", f"{obj_name} decomposed → {law}"
        
        # ─── LAYER 3: Analogical transfer ───
        analog_props, analog_conf = analogical_transfer(obj_name, self.store.materials)
        if analog_conf >= 0.5:
            result = self.physics.apply_all(analog_props, action)
            if result:
                effect, conf, law = result
                return effect, min(conf, analog_conf), "L3:ANALOG", f"{obj_name} ≈ nearest known → {law}"
        
        # ─── LAYER 4: Contextual extraction ───
        if full_question:
            ctx_props, ctx_conf = contextual_extraction(full_question, obj_name)
            if ctx_conf >= 0.6:
                # Merge with any decomposition results
                merged = {**decomp_props, **ctx_props}
                result = self.physics.apply_all(merged, action)
                if result:
                    effect, conf, law = result
                    return effect, min(conf, ctx_conf), "L4:CONTEXT", f"adjectives → {law}"
        
        # ─── LAYER 5: Compositional (multi-object) ───
        if context:
            comp_result = compositional_reaction(obj_name, context)
            if comp_result:
                effect, conf = comp_result
                return effect, conf, "L5:COMPOSITE", f"{obj_name} + {context} → reaction"
        
        # ─── LAYER 6: Systemic (social/economic) ───
        sys_result = systemic_reasoning(action, obj_name)
        if sys_result:
            effect, conf = sys_result
            return effect, conf, "L6:SYSTEMIC", f"social law: {action} → {obj_name}"
        
        # ─── LAYER 7: Auto-learn from web ───
        if allow_web and not self.store.has(obj_name):
            learned = auto_learn_material(obj_name, self.store)
            if learned:
                self._web_lookups += 1
                result = self.physics.apply_all(learned, action)
                if result:
                    effect, conf, law = result
                    return effect, conf * 0.9, "L7:LEARNED", f"web → {obj_name} properties → {law}"
        
        # ─── LAYER 2 fallback: try with lower confidence ───
        if decomp_conf > 0.3:
            result = self.physics.apply_all(decomp_props, action)
            if result:
                effect, conf, law = result
                return effect, conf * 0.5, "L2:GUESS", f"{obj_name} (low confidence decomposition)"
        
        # ─── LAYER 8: Honest gap ───
        return (f"Cannot determine what happens when you {action} {obj_name} — "
                f"unknown material properties"), 0.0, "L8:GAP", "insufficient information"
    
    def explain(self, question, allow_web=False):
        """Natural language interface to the CAE."""
        action, obj, context = self._parse(question)
        if not action or not obj:
            return None
        
        effect, conf, layer, reasoning = self.reason(
            action, obj, context, full_question=question, allow_web=allow_web)
        
        if conf == 0.0:
            return None  # Layer 8 gap
        
        # Format response
        conf_word = "certainly" if conf > 0.9 else "likely" if conf > 0.75 else "probably" if conf > 0.6 else "possibly"
        return {
            'answer': f"{effect}",
            'confidence': conf,
            'confidence_word': conf_word,
            'layer': layer,
            'reasoning': reasoning,
            'formatted': f"{effect} ({conf_word}, {conf:.0%})\n[{layer}] {reasoning}"
        }
    
    def _parse(self, question):
        """Parse natural language into action + object + context."""
        q = question.lower().strip().rstrip('?')
        for prefix in ['what happens if', 'what would happen if', 'what if',
                       'what happens when', 'what would happen when']:
            if q.startswith(prefix):
                q = q[len(prefix):].strip()
                break
        
        # Strip possessives/determiners from anywhere in query
        q = re.sub(r'\b(my|your|his|her|its|our|their|this|that|some)\s+', '', q)
        
        # Strip adverbs before action verb
        adverbs = ('accidentally','quickly','slowly','suddenly','carefully',
                   'gently','roughly','violently','completely','partially',
                   'immediately','gradually','eventually','repeatedly')
        for adv in adverbs:
            if q.startswith(adv + ' '):
                q = q[len(adv)+1:]
                break
        
        # Handle passive voice: "X is heated" → action=heat, obj=X
        m_pass = re.match(r'(?:a |an |the )?(.+?)\s+(?:is|are|gets?)\s+(heated|dropped|burned|burnt|frozen|cut|stretched|compressed|melted|broken|crushed|bent|shattered|dissolved|ignited|electrified|magnetized|submerged|cooled)', q)
        if m_pass:
            obj = m_pass.group(1).strip()
            verb_map = {'heated':'heat','dropped':'drop','burned':'burn','burnt':'burn',
                        'frozen':'freeze','cut':'cut','stretched':'stretch',
                        'compressed':'compress','melted':'heat','broken':'drop',
                        'crushed':'compress','bent':'bend','shattered':'drop',
                        'dissolved':'dissolve','ignited':'burn','electrified':'electrify',
                        'magnetized':'magnetize','submerged':'submerge','cooled':'cool'}
            action = verb_map.get(m_pass.group(2), m_pass.group(2))
            return action, obj, None
        
        # Handle "mix X and Y"
        m_mix = re.match(r'(?:you )?mix\s+(?:a |an |the )?(.+?)\s+and\s+(?:a |an |the )?(.+)', q)
        if m_mix:
            return 'mix', m_mix.group(1).strip(), m_mix.group(2).strip()
        
        # Handle passive voice: "X is heated/dropped/burned" → action=heat/drop/burn, obj=X
        m_passive = re.match(r'(?:a |an |the )?(.+?)\s+(?:is|are|gets?)\s+(heated|dropped|burned|frozen|cut|stretched|compressed|melted|broken|crushed|bent|shattered)', q)
        if m_passive:
            subject = m_passive.group(1).strip()
            past_participle = m_passive.group(2).strip()
            # Convert past participle to base verb
            verb_map = {
                'heated': 'heat', 'dropped': 'drop', 'burned': 'burn',
                'frozen': 'freeze', 'cut': 'cut', 'stretched': 'stretch',
                'compressed': 'compress', 'melted': 'heat', 'broken': 'drop',
                'crushed': 'compress', 'bent': 'bend', 'shattered': 'drop',
            }
            verb_base = verb_map.get(past_participle, past_participle.rstrip('ed'))
            return verb_base, subject, None
        
        # Strip leading adverbs that get captured as action verbs
        adverbs = {'accidentally', 'quickly', 'slowly', 'suddenly', 'carefully',
                   'gently', 'roughly', 'violently', 'completely', 'partially'}
        # Strip subject pronouns first for adverb check
        q_stripped = q
        for pronoun in ('you ', 'i ', 'we ', 'someone '):
            if q_stripped.startswith(pronoun):
                q_stripped = q_stripped[len(pronoun):]
                break
        first_word = q_stripped.split()[0] if q_stripped.split() else ''
        if first_word in adverbs:
            # Remove the adverb from q (keeping the pronoun if present)
            q = re.sub(r'\b' + first_word + r'\b\s*', '', q, count=1).strip()
            q = re.sub(r'\s{2,}', ' ', q)  # normalize spaces
        
        # Standard: "you [verb] [object]"
        m = re.match(r'(?:you |i |we |someone )?(\w+)\s+(?:a |an |the )?(.+?)(?:\s+(?:in|on|into|with)\s+(?:a |an |the )?(.+))?$', q)
        if m:
            obj = m.group(2).strip()
            # Strip possessives and determiners from obj
            obj = re.sub(r'^(my|your|his|her|its|our|their|this|that|these|those|some|the|a|an)\s+', '', obj)
            context = m.group(3).strip() if m.group(3) else None
            return m.group(1), obj, context
        
        words = q.split()
        if len(words) >= 2:
            obj = ' '.join(words[1:]).strip()
            # Strip possessives and determiners from obj
            obj = re.sub(r'^(my|your|his|her|its|our|their|this|that|these|those|some|the|a|an)\s+', '', obj)
            return words[0], obj, None
        return None, None, None
    
    def stats(self):
        return {
            'materials_known': self.store.size(),
            'queries_answered': self._queries_answered,
            'web_lookups': self._web_lookups,
        }


# ══════════════════════════════════════════════════════════════
# SINGLETON + TEST
# ══════════════════════════════════════════════════════════════

_cae = None
def get_cae():
    global _cae
    if _cae is None:
        _cae = CausalAxiomEngine()
    return _cae


if __name__ == '__main__':
    engine = CausalAxiomEngine()
    
    print("═══ CAUSAL AXIOM ENGINE — 8 LAYER TEST ═══\n")
    
    tests = [
        "What happens if you heat a candle?",
        "What happens if you drop a crystal chandelier?",
        "What happens if you burn a silk scarf?",
        "What happens if you stretch a bungee cord?",
        "What happens if you heat titanium?",
        "What happens if you magnetize a paperclip?",
        "What happens if you freeze orange juice?",
        "What happens if you electrify a copper wire?",
        "What happens if you drop a porcelain doll?",
        "What happens if you heat frozen yogurt?",
        "What happens if you compress helium?",
        "What happens if you cut a leather belt?",
        "What happens if you burn a rubber tire?",
        "What happens if you insult a king?",
        "What happens if you mix vinegar and chalk?",
        "What happens if you ignore a warning?",
        "What happens if you heat an unknown alien rock?",
    ]
    
    for q in tests:
        result = engine.explain(q)
        if result:
            print(f"  Q: {q}")
            print(f"  A: {result['answer']}")
            print(f"     [{result['layer']}] {result['confidence_word']} ({result['confidence']:.0%})")
            print()
        else:
            print(f"  Q: {q}")
            print(f"  A: ❌ LAYER 8 — Cannot determine")
            print()
    
    print(f"Stats: {engine.stats()}")
