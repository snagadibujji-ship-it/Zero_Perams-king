#!/usr/bin/env python3
"""
AXIMA Universal Causal Engine — Property-Based Inference
Instead of action+object→effect LOOKUP, we DERIVE effects from:
  1. Object → Material/Category properties
  2. Action → Physical process (what it does to properties)
  3. Derive: if action exceeds threshold → state change

Example: "heat candle" → candle=wax → wax.melting_point=60 → heat>60 → MELTS
No rule needed. Works for ANY object if we know its material.
"""

# ══════════════════════════════════════════════════════════════
# MATERIAL PROPERTIES DATABASE
# Each material has physical properties that determine behavior
# ══════════════════════════════════════════════════════════════

MATERIALS = {
    # Metals
    'iron': {'state': 'solid', 'melt_temp': 1538, 'flammable': False, 'fragile': False,
             'elastic': False, 'conductive': True, 'magnetic': True, 'dense': True,
             'corrodes': True, 'malleable': True, 'category': 'metal'},
    'steel': {'state': 'solid', 'melt_temp': 1370, 'flammable': False, 'fragile': False,
              'elastic': False, 'conductive': True, 'magnetic': True, 'dense': True,
              'corrodes': True, 'malleable': True, 'category': 'metal'},
    'gold': {'state': 'solid', 'melt_temp': 1064, 'flammable': False, 'fragile': False,
             'elastic': False, 'conductive': True, 'magnetic': False, 'dense': True,
             'corrodes': False, 'malleable': True, 'category': 'metal'},
    'copper': {'state': 'solid', 'melt_temp': 1085, 'flammable': False, 'fragile': False,
               'elastic': False, 'conductive': True, 'magnetic': False, 'dense': True,
               'corrodes': True, 'malleable': True, 'category': 'metal'},
    'aluminum': {'state': 'solid', 'melt_temp': 660, 'flammable': False, 'fragile': False,
                 'elastic': False, 'conductive': True, 'magnetic': False, 'dense': False,
                 'corrodes': False, 'malleable': True, 'category': 'metal'},
    'lead': {'state': 'solid', 'melt_temp': 327, 'flammable': False, 'fragile': False,
             'elastic': False, 'conductive': True, 'magnetic': False, 'dense': True,
             'corrodes': False, 'malleable': True, 'category': 'metal'},
    # Organic/Soft
    'wax': {'state': 'solid', 'melt_temp': 60, 'flammable': True, 'fragile': False,
            'elastic': False, 'conductive': False, 'magnetic': False, 'dense': False,
            'corrodes': False, 'malleable': True, 'category': 'organic'},
    'butter': {'state': 'solid', 'melt_temp': 35, 'flammable': False, 'fragile': False,
               'elastic': False, 'conductive': False, 'magnetic': False, 'dense': False,
               'corrodes': False, 'malleable': True, 'category': 'fat'},
    'chocolate': {'state': 'solid', 'melt_temp': 34, 'flammable': False, 'fragile': True,
                  'elastic': False, 'conductive': False, 'magnetic': False, 'dense': False,
                  'corrodes': False, 'malleable': False, 'category': 'food'},
    'cheese': {'state': 'solid', 'melt_temp': 65, 'flammable': False, 'fragile': False,
               'elastic': False, 'conductive': False, 'magnetic': False, 'dense': False,
               'corrodes': False, 'malleable': True, 'category': 'food'},
    'ice_cream': {'state': 'solid', 'melt_temp': -2, 'flammable': False, 'fragile': False,
                  'elastic': False, 'conductive': False, 'magnetic': False, 'dense': False,
                  'corrodes': False, 'malleable': True, 'category': 'food'},
    'sugar': {'state': 'solid', 'melt_temp': 186, 'flammable': True, 'fragile': True,
              'elastic': False, 'conductive': False, 'magnetic': False, 'dense': False,
              'corrodes': False, 'malleable': False, 'category': 'organic'},
    'plastic': {'state': 'solid', 'melt_temp': 150, 'flammable': True, 'fragile': False,
                'elastic': False, 'conductive': False, 'magnetic': False, 'dense': False,
                'corrodes': False, 'malleable': True, 'category': 'polymer'},
    'rubber': {'state': 'solid', 'melt_temp': 180, 'flammable': True, 'fragile': False,
               'elastic': True, 'conductive': False, 'magnetic': False, 'dense': False,
               'corrodes': False, 'malleable': True, 'category': 'polymer'},
    'wood': {'state': 'solid', 'melt_temp': None, 'flammable': True, 'fragile': False,
             'elastic': False, 'conductive': False, 'magnetic': False, 'dense': False,
             'corrodes': False, 'malleable': False, 'burn_temp': 300, 'category': 'organic'},
    'paper': {'state': 'solid', 'melt_temp': None, 'flammable': True, 'fragile': True,
              'elastic': False, 'conductive': False, 'magnetic': False, 'dense': False,
              'corrodes': False, 'malleable': False, 'burn_temp': 233, 'category': 'organic'},
    'cotton': {'state': 'solid', 'melt_temp': None, 'flammable': True, 'fragile': False,
               'elastic': False, 'conductive': False, 'magnetic': False, 'dense': False,
               'corrodes': False, 'malleable': True, 'burn_temp': 255, 'category': 'fabric'},
    # Glass/Ceramic
    'glass': {'state': 'solid', 'melt_temp': 1400, 'flammable': False, 'fragile': True,
              'elastic': False, 'conductive': False, 'magnetic': False, 'dense': True,
              'corrodes': False, 'malleable': False, 'category': 'ceramic'},
    'ceramic': {'state': 'solid', 'melt_temp': 1600, 'flammable': False, 'fragile': True,
                'elastic': False, 'conductive': False, 'magnetic': False, 'dense': True,
                'corrodes': False, 'malleable': False, 'category': 'ceramic'},
    'porcelain': {'state': 'solid', 'melt_temp': 1800, 'flammable': False, 'fragile': True,
                  'elastic': False, 'conductive': False, 'magnetic': False, 'dense': True,
                  'corrodes': False, 'malleable': False, 'category': 'ceramic'},
    # Liquids
    'water': {'state': 'liquid', 'melt_temp': 0, 'boil_temp': 100, 'flammable': False,
              'fragile': False, 'elastic': False, 'conductive': True, 'magnetic': False,
              'dense': True, 'corrodes': False, 'malleable': False, 'category': 'liquid'},
    'oil': {'state': 'liquid', 'melt_temp': -20, 'boil_temp': 300, 'flammable': True,
            'fragile': False, 'elastic': False, 'conductive': False, 'magnetic': False,
            'dense': False, 'corrodes': False, 'malleable': False, 'category': 'liquid'},
    'alcohol': {'state': 'liquid', 'melt_temp': -114, 'boil_temp': 78, 'flammable': True,
                'fragile': False, 'elastic': False, 'conductive': False, 'magnetic': False,
                'dense': False, 'corrodes': False, 'malleable': False, 'category': 'liquid'},
    'gasoline': {'state': 'liquid', 'melt_temp': -60, 'boil_temp': 95, 'flammable': True,
                 'fragile': False, 'elastic': False, 'conductive': False, 'magnetic': False,
                 'dense': False, 'corrodes': False, 'malleable': False, 'category': 'liquid'},
    # Gases
    'hydrogen': {'state': 'gas', 'flammable': True, 'fragile': False, 'elastic': False,
                 'conductive': False, 'magnetic': False, 'dense': False, 'category': 'gas'},
    'oxygen': {'state': 'gas', 'flammable': False, 'fragile': False, 'supports_combustion': True,
               'category': 'gas'},
    # Other common objects (mapped to their primary material)
    'ice': {'state': 'solid', 'melt_temp': 0, 'flammable': False, 'fragile': True,
            'elastic': False, 'conductive': False, 'magnetic': False, 'dense': True,
            'category': 'frozen_liquid'},
    'rock': {'state': 'solid', 'melt_temp': 1200, 'flammable': False, 'fragile': False,
             'elastic': False, 'conductive': False, 'magnetic': False, 'dense': True,
             'category': 'mineral'},
    'concrete': {'state': 'solid', 'melt_temp': 1500, 'flammable': False, 'fragile': True,
                 'elastic': False, 'conductive': False, 'magnetic': False, 'dense': True,
                 'category': 'mineral'},
    'sand': {'state': 'solid', 'melt_temp': 1700, 'flammable': False, 'fragile': False,
             'elastic': False, 'conductive': False, 'magnetic': False, 'dense': True,
             'category': 'mineral'},
    'salt': {'state': 'solid', 'melt_temp': 801, 'flammable': False, 'fragile': True,
             'elastic': False, 'conductive': False, 'magnetic': False, 'dense': True,
             'soluble': True, 'category': 'mineral'},
}

# ══════════════════════════════════════════════════════════════
# OBJECT → MATERIAL MAPPING
# Maps common objects to their primary material
# If object not found, use category inference from knowledge graph
# ══════════════════════════════════════════════════════════════

OBJECT_MATERIAL = {
    # Kitchen
    'candle': 'wax', 'butter': 'butter', 'chocolate': 'chocolate', 'cheese': 'cheese',
    'ice cream': 'ice_cream', 'ice': 'ice', 'sugar': 'sugar', 'honey': 'sugar',
    'caramel': 'sugar', 'marshmallow': 'sugar', 'candy': 'sugar',
    # Containers
    'glass': 'glass', 'cup': 'ceramic', 'plate': 'ceramic', 'bowl': 'ceramic',
    'mug': 'ceramic', 'vase': 'glass', 'mirror': 'glass', 'window': 'glass',
    'bottle': 'glass', 'jar': 'glass', 'lightbulb': 'glass',
    'wine glass': 'glass', 'beer glass': 'glass', 'champagne glass': 'glass',
    # Metal objects
    'nail': 'iron', 'knife': 'steel', 'sword': 'steel', 'coin': 'copper',
    'key': 'iron', 'chain': 'iron', 'wire': 'copper', 'pan': 'iron',
    'pot': 'iron', 'fork': 'steel', 'spoon': 'steel', 'can': 'aluminum',
    'car': 'steel', 'bike': 'steel', 'bridge': 'steel', 'pipe': 'iron',
    # Wood
    'table': 'wood', 'chair': 'wood', 'door': 'wood', 'pencil': 'wood',
    'tree': 'wood', 'stick': 'wood', 'log': 'wood', 'match': 'wood',
    'paper': 'paper', 'book': 'paper', 'cardboard': 'paper',
    # Fabric
    'shirt': 'cotton', 'cloth': 'cotton', 'rope': 'cotton', 'towel': 'cotton',
    'blanket': 'cotton', 'curtain': 'cotton',
    # Plastic/Rubber
    'ball': 'rubber', 'tire': 'rubber', 'eraser': 'rubber', 'balloon': 'rubber',
    'plastic bag': 'plastic', 'straw': 'plastic', 'pen': 'plastic',
    'phone': 'glass', 'laptop': 'plastic', 'tablet': 'glass', 'toy': 'plastic',
    # Liquids
    'water': 'water', 'milk': 'water', 'juice': 'water', 'tea': 'water',
    'coffee': 'water', 'soup': 'water', 'blood': 'water',
    'oil': 'oil', 'gasoline': 'gasoline', 'alcohol': 'alcohol',
    'wine': 'alcohol', 'beer': 'alcohol', 'petrol': 'gasoline',
    # Stone/Earth
    'rock': 'rock', 'stone': 'rock', 'brick': 'ceramic', 'concrete': 'concrete',
    'sand': 'sand', 'diamond': 'rock', 'marble': 'rock',
    # Food
    'egg': 'egg', 'meat': 'meat', 'bread': 'bread', 'rice': 'grain',
    'pasta': 'grain', 'pizza': 'bread', 'cake': 'bread',
    'steak': 'meat', 'chicken': 'meat', 'fish': 'meat', 'bacon': 'meat',
    'sausage': 'meat', 'hamburger': 'meat', 'hot dog': 'meat',
    # Ice/Snow
    'snowball': 'ice', 'snowman': 'ice', 'icicle': 'ice', 'glacier': 'ice',
    'iceberg': 'ice', 'frost': 'ice', 'hail': 'ice',
    # Toys/Misc
    'lego': 'plastic', 'lego brick': 'plastic', 'crayon': 'wax',
    'candle': 'wax', 'lipstick': 'wax',
}

# Special materials not in main MATERIALS dict
MATERIALS['egg'] = {'state': 'liquid_in_shell', 'cook_temp': 70, 'flammable': False,
                    'fragile': True, 'category': 'food'}
MATERIALS['meat'] = {'state': 'solid', 'cook_temp': 75, 'flammable': False,
                     'fragile': False, 'burn_temp': 300, 'category': 'food'}
MATERIALS['bread'] = {'state': 'solid', 'melt_temp': None, 'flammable': True,
                      'fragile': True, 'burn_temp': 200, 'category': 'food'}
MATERIALS['grain'] = {'state': 'solid', 'melt_temp': None, 'flammable': False,
                      'fragile': False, 'cook_temp': 100, 'category': 'food'}

# ══════════════════════════════════════════════════════════════
# CATEGORY-BASED DEFAULTS
# If specific material unknown, infer from category words
# ══════════════════════════════════════════════════════════════

CATEGORY_KEYWORDS = {
    'metal': ['metal', 'iron', 'steel', 'aluminum', 'copper', 'silver', 'bronze', 'titanium'],
    'glass': ['glass', 'crystal', 'lens', 'mirror', 'window'],
    'ceramic': ['ceramic', 'porcelain', 'clay', 'pottery', 'china', 'plate', 'cup', 'bowl'],
    'wood': ['wood', 'wooden', 'timber', 'oak', 'pine', 'bamboo', 'plywood'],
    'plastic': ['plastic', 'polymer', 'nylon', 'polystyrene', 'pvc', 'acrylic'],
    'rubber': ['rubber', 'latex', 'silicone', 'elastic'],
    'fabric': ['fabric', 'cloth', 'cotton', 'silk', 'wool', 'linen', 'denim', 'leather'],
    'paper': ['paper', 'cardboard', 'tissue', 'newspaper', 'book'],
    'liquid': ['liquid', 'water', 'fluid', 'juice', 'solution'],
    'food': ['food', 'fruit', 'vegetable', 'snack', 'meal'],
    'gas': ['gas', 'air', 'vapor', 'steam', 'fume', 'smoke'],
    'organic': ['organic', 'biological', 'natural'],
}

CATEGORY_DEFAULTS = {
    'metal': {'state': 'solid', 'melt_temp': 1000, 'flammable': False, 'fragile': False,
              'elastic': False, 'conductive': True, 'dense': True, 'malleable': True},
    'glass': {'state': 'solid', 'melt_temp': 1400, 'flammable': False, 'fragile': True,
              'elastic': False, 'conductive': False, 'dense': True},
    'ceramic': {'state': 'solid', 'melt_temp': 1500, 'flammable': False, 'fragile': True,
                'elastic': False, 'conductive': False, 'dense': True},
    'wood': {'state': 'solid', 'melt_temp': None, 'flammable': True, 'fragile': False,
             'burn_temp': 300, 'elastic': False},
    'plastic': {'state': 'solid', 'melt_temp': 150, 'flammable': True, 'fragile': False,
                'elastic': True},
    'rubber': {'state': 'solid', 'melt_temp': 180, 'flammable': True, 'fragile': False,
               'elastic': True},
    'fabric': {'state': 'solid', 'melt_temp': None, 'flammable': True, 'fragile': False,
               'burn_temp': 250, 'elastic': False},
    'paper': {'state': 'solid', 'melt_temp': None, 'flammable': True, 'fragile': True,
              'burn_temp': 233},
    'liquid': {'state': 'liquid', 'boil_temp': 100, 'flammable': False},
    'food': {'state': 'solid', 'cook_temp': 80, 'flammable': False, 'fragile': True},
    'gas': {'state': 'gas', 'flammable': False},
    'organic': {'state': 'solid', 'flammable': True, 'burn_temp': 300},
}

# ══════════════════════════════════════════════════════════════
# ACTION → PHYSICAL PROCESS
# What each action DOES to an object's properties
# ══════════════════════════════════════════════════════════════

ACTION_PHYSICS = {
    'heat': {
        'process': 'increase_temperature',
        'checks': [
            # (condition, effect_template, probability)
            ('melt_temp is not None and state=="solid"', '{obj} melts (melting point: {melt_temp}°C)', 0.95),
            ('burn_temp and flammable', '{obj} catches fire and burns (ignition: {burn_temp}°C)', 0.9),
            ('flammable and not burn_temp', '{obj} can catch fire if heated enough', 0.8),
            ('cook_temp', '{obj} cooks and its proteins change structure', 0.9),
            ('boil_temp and state=="liquid"', '{obj} evaporates into steam/vapor (boiling: {boil_temp}°C)', 0.95),
            ('state=="solid" and melt_temp is None and not flammable', '{obj} expands slightly from thermal expansion', 0.7),
            ('state=="gas"', '{obj} expands as molecules move faster', 0.9),
        ],
    },
    'cool': {
        'process': 'decrease_temperature',
        'checks': [
            ('state=="liquid"', '{obj} freezes into a solid', 0.9),
            ('state=="gas"', '{obj} condenses into liquid', 0.9),
            ('state=="solid"', '{obj} contracts slightly from thermal contraction', 0.7),
        ],
    },
    'freeze': {
        'process': 'decrease_temperature_below_zero',
        'checks': [
            ('state=="liquid"', '{obj} freezes solid and expands', 0.95),
            ('state=="solid"', '{obj} becomes more brittle in extreme cold', 0.7),
            ('category=="food"', '{obj} freezes and is preserved', 0.9),
        ],
    },
    'drop': {
        'process': 'apply_impact_force',
        'checks': [
            ('fragile', '{obj} shatters or breaks on impact', 0.9),
            ('elastic and category in ("rubber","polymer") and not fragile', '{obj} bounces back', 0.85),
            ('elastic and category not in ("rubber",)', '{obj} may crack or get damaged on impact', 0.75),
            ('dense and not fragile', '{obj} hits the ground hard but stays intact', 0.8),
            ('state=="liquid"', '{obj} splashes', 0.95),
            ('not fragile and not elastic', '{obj} falls and may get dented or scratched', 0.7),
        ],
    },
    'hit': {
        'process': 'apply_impact_force',
        'checks': [
            ('fragile', '{obj} cracks or shatters', 0.9),
            ('malleable', '{obj} dents or deforms', 0.85),
            ('elastic', '{obj} absorbs the impact and bounces', 0.8),
            ('not fragile and not malleable', '{obj} resists but may chip', 0.6),
        ],
    },
    'stretch': {
        'process': 'apply_tensile_force',
        'checks': [
            ('elastic', '{obj} stretches and returns to original shape when released', 0.9),
            ('malleable', '{obj} deforms permanently — it won\'t snap back', 0.8),
            ('fragile', '{obj} snaps or tears apart', 0.85),
            ('not elastic and not malleable', '{obj} resists stretching — very stiff', 0.7),
        ],
    },
    'compress': {
        'process': 'apply_compressive_force',
        'checks': [
            ('state=="gas"', '{obj} volume decreases and pressure/temperature increase', 0.95),
            ('elastic', '{obj} compresses and stores energy, springs back when released', 0.9),
            ('fragile', '{obj} can crack or shatter under pressure', 0.8),
            ('malleable', '{obj} deforms and flattens', 0.8),
        ],
    },
    'cut': {
        'process': 'apply_shear_force',
        'checks': [
            ('fragile', '{obj} splits cleanly', 0.9),
            ('malleable and category=="metal"', '{obj} can be cut but requires strong tools', 0.7),
            ('elastic', '{obj} separates but edges may snap back', 0.8),
            ('category in ("fabric","paper","organic")', '{obj} cuts easily into pieces', 0.95),
            ('True', '{obj} separates into parts', 0.7),
        ],
    },
    'burn': {
        'process': 'combustion',
        'checks': [
            ('flammable', '{obj} burns, producing heat, light, and ash/smoke', 0.95),
            ('not flammable and category=="metal"', '{obj} does not burn — metals resist flames', 0.9),
            ('not flammable', '{obj} does not easily catch fire — it is fire-resistant', 0.85),
        ],
    },
    'dissolve': {
        'process': 'dissolution_in_solvent',
        'checks': [
            ('soluble', '{obj} dissolves completely into the solution', 0.95),
            ('category in ("food","organic") and state=="solid"', '{obj} may partially dissolve or soften', 0.6),
            ('category in ("metal","ceramic","mineral")', '{obj} does not dissolve in water', 0.9),
        ],
    },
    'electrify': {
        'process': 'apply_electric_current',
        'checks': [
            ('conductive', '{obj} conducts the electricity — can cause heating or sparks', 0.9),
            ('not conductive', '{obj} is an insulator — blocks the current', 0.85),
        ],
    },
    'magnetize': {
        'process': 'apply_magnetic_field',
        'checks': [
            ('magnetic', '{obj} is attracted to the magnet and sticks', 0.95),
            ('not magnetic', '{obj} is not affected by magnets', 0.9),
        ],
    },
    'submerge': {
        'process': 'place_in_liquid',
        'checks': [
            ('dense', '{obj} sinks to the bottom', 0.85),
            ('not dense and state=="solid"', '{obj} floats on the surface', 0.8),
            ('soluble', '{obj} dissolves in the liquid', 0.9),
            ('corrodes', '{obj} will rust or corrode over time in water', 0.75),
        ],
    },
}

# ══════════════════════════════════════════════════════════════
# THE UNIVERSAL CAUSAL REASONER
# Derives effects from properties — works for ANY object
# ══════════════════════════════════════════════════════════════

class UniversalCausalReasoner:
    """
    Derives causal effects from first principles:
    1. Identify object's material/properties
    2. Identify what the action physically does
    3. Check which property thresholds are exceeded
    4. Generate natural language effect description
    
    Works for ANYTHING — even objects never seen before.
    """
    
    def __init__(self):
        self.materials = MATERIALS
        self.obj_map = OBJECT_MATERIAL
        self.actions = ACTION_PHYSICS
        self.cat_keywords = CATEGORY_KEYWORDS
        self.cat_defaults = CATEGORY_DEFAULTS
    
    def get_properties(self, obj_name):
        """Get physical properties of an object. Multi-level lookup."""
        obj_lower = obj_name.lower().strip()
        
        # Level 1: Direct material lookup
        if obj_lower in self.materials:
            return self.materials[obj_lower], obj_lower
        
        # Level 2: Object → material mapping
        if obj_lower in self.obj_map:
            mat_name = self.obj_map[obj_lower]
            if mat_name in self.materials:
                return self.materials[mat_name], mat_name
        
        # Level 3: Check if any word in obj matches a material
        for word in obj_lower.split():
            if word in self.materials:
                return self.materials[word], word
            if word in self.obj_map:
                mat = self.obj_map[word]
                if mat in self.materials:
                    return self.materials[mat], mat
        
        # Level 4: Category inference from keywords
        for cat, keywords in self.cat_keywords.items():
            for kw in keywords:
                if kw in obj_lower:
                    if cat in self.cat_defaults:
                        return self.cat_defaults[cat], f"(inferred: {cat})"
        
        # Level 5: Common-sense defaults based on word patterns
        if any(w in obj_lower for w in ['liquid', 'juice', 'drink', 'soup', 'broth']):
            return self.cat_defaults['liquid'], '(inferred: liquid)'
        if any(w in obj_lower for w in ['stone', 'rock', 'mineral', 'crystal']):
            return self.cat_defaults.get('mineral', {'state': 'solid', 'dense': True, 'fragile': False}), '(inferred: mineral)'
        
        # Level 6: Absolute fallback — generic solid
        return {'state': 'solid', 'fragile': False, 'elastic': False, 'flammable': False,
                'dense': False, 'conductive': False}, '(unknown material)'
    
    def reason(self, action, obj_name, context=None):
        """
        Universal causal reasoning. Returns list of (effect, probability, reasoning).
        
        action: what is being done (heat, drop, cut, burn, etc.)
        obj_name: what it's being done to
        context: optional context (e.g., "in water", "with acid")
        """
        # Normalize action
        action_lower = action.lower().strip()
        # Map synonyms
        action_synonyms = {
            'warm': 'heat', 'microwave': 'heat', 'boil': 'heat', 'bake': 'heat',
            'fry': 'heat', 'roast': 'heat', 'cook': 'heat', 'grill': 'heat',
            'chill': 'cool', 'refrigerate': 'cool', 'ice': 'freeze',
            'throw': 'drop', 'smash': 'hit', 'punch': 'hit', 'slam': 'hit',
            'break': 'hit', 'crush': 'compress', 'squeeze': 'compress',
            'pull': 'stretch', 'tear': 'cut', 'slice': 'cut', 'chop': 'cut',
            'ignite': 'burn', 'light': 'burn', 'set_fire': 'burn',
            'dunk': 'submerge', 'dip': 'submerge', 'soak': 'submerge',
            'shock': 'electrify', 'zap': 'electrify',
        }
        action_key = action_synonyms.get(action_lower, action_lower)
        
        # Get properties
        props, material_name = self.get_properties(obj_name)
        
        # Get action physics
        if action_key not in self.actions:
            return None  # Unknown action — let rule-based handle
        
        action_info = self.actions[action_key]
        results = []
        
        for condition_str, effect_template, prob in action_info['checks']:
            # Evaluate condition against properties
            if self._eval_condition(condition_str, props):
                # Format effect string
                effect = effect_template.format(
                    obj=obj_name,
                    melt_temp=props.get('melt_temp', '?'),
                    boil_temp=props.get('boil_temp', '?'),
                    burn_temp=props.get('burn_temp', '?'),
                    cook_temp=props.get('cook_temp', '?'),
                )
                reasoning = f"{obj_name} → material: {material_name} → {action_info['process']}"
                results.append((effect, prob, reasoning))
                break  # Take first matching (highest priority)
        
        return results if results else None
    
    def _eval_condition(self, condition_str, props):
        """Safely evaluate a condition string against properties."""
        try:
            # Build local namespace from properties
            ns = dict(props)
            ns['category'] = props.get('category', '')
            ns['True'] = True
            ns['False'] = False
            ns['None'] = None
            # eval with restricted builtins
            return eval(condition_str, {"__builtins__": {}, 'None': None}, ns)
        except:
            return False
    
    def explain(self, action, obj_name, context=None):
        """Get a natural language explanation of what happens."""
        results = self.reason(action, obj_name, context)
        if not results:
            return None
        
        effect, prob, reasoning = results[0]
        confidence = "almost certainly" if prob > 0.9 else "likely" if prob > 0.7 else "possibly"
        return f"{effect} ({confidence}, {prob:.0%} confidence)\nReasoning: {reasoning}"


# ══════════════════════════════════════════════════════════════
# INTEGRATION FUNCTION — drop-in for WorldSimulator
# ══════════════════════════════════════════════════════════════

_reasoner = None

def get_universal_reasoner():
    global _reasoner
    if _reasoner is None:
        _reasoner = UniversalCausalReasoner()
    return _reasoner


def universal_causal_explain(question):
    """
    Universal causal reasoning for 'what happens if...' questions.
    Returns natural language answer or None if can't determine.
    """
    import re
    q = question.lower().strip().rstrip('?')
    
    # Remove prefixes
    for prefix in ['what happens if', 'what would happen if', 'what if',
                   'what happens when', 'what would happen when']:
        if q.startswith(prefix):
            q = q[len(prefix):].strip()
            break
    
    # Parse action and object
    # Pattern: "you [verb] [object]" or "[verb] [object]"
    m = re.match(r'(?:you |i |we |someone )?(\w+)\s+(?:a |an |the )?(.+?)(?:\s+(?:in|on|into|with)\s+.+)?$', q)
    if not m:
        words = q.split()
        if len(words) >= 2:
            action, obj = words[0], ' '.join(words[1:]).strip('a ').strip('an ').strip('the ')
        else:
            return None
    else:
        action = m.group(1)
        obj = m.group(2).strip()
    
    reasoner = get_universal_reasoner()
    result = reasoner.explain(action, obj)
    return result


# ══════════════════════════════════════════════════════════════
# STANDALONE TEST
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    r = UniversalCausalReasoner()
    
    tests = [
        ('heat', 'candle'),      # wax → melts
        ('drop', 'vase'),        # glass → shatters
        ('heat', 'steak'),       # meat → cooks
        ('burn', 'newspaper'),   # paper → burns
        ('stretch', 'balloon'),  # rubber → elastic
        ('drop', 'diamond'),     # rock → stays intact
        ('heat', 'snowball'),    # → melts
        ('magnetize', 'nail'),   # iron → attracted
        ('cut', 'rope'),         # fabric → cuts easily
        ('heat', 'lego brick'),  # plastic → melts
        ('submerge', 'cork'),    # not dense → floats
        ('electrify', 'fork'),   # metal → conducts
    ]
    
    print("═══ UNIVERSAL CAUSAL REASONER TEST ═══\n")
    for action, obj in tests:
        result = r.explain(action, obj)
        if result:
            lines = result.split('\n')
            print(f"  {action} + {obj}")
            print(f"    → {lines[0]}")
            print(f"    {lines[1]}")
        else:
            print(f"  {action} + {obj} → ❌ NO INFERENCE")
        print()
