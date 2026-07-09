#!/usr/bin/env python3
"""
Causal World Simulator — answers "what happens if..." questions via cause-effect chains.
Based on 2026 research: "Self-Evolving Cognitive Framework via Causal World Modeling"
"""

import re
from dataclasses import dataclass, field
@dataclass
class CausalRule:
    action: str
    obj: str
    effect: str
    probability: float = 0.9
    context: str = ""
    tags: list = field(default_factory=list)


class WorldSimulator:
    def __init__(self):
        self.rules: list[CausalRule] = []
        self.load_rules()

    def add_rule(self, action, obj, effect, prob=0.9, context="", tags=None):
        self.rules.append(CausalRule(action, obj, effect, prob, context, tags or []))

    def load_rules(self):
        """Load 200+ causal rules about how the world works."""
        # === PHYSICS (50) ===
        self.add_rule('drop', 'glass', 'breaks', 0.95, tags=['physics'])
        self.add_rule('drop', 'fragile_object', 'breaks', 0.9, tags=['physics'])
        self.add_rule('drop', 'ball', 'bounces', 0.85, tags=['physics'])
        self.add_rule('drop', 'egg', 'breaks', 0.95, tags=['physics'])
        self.add_rule('drop', 'phone', 'screen_cracks', 0.6, tags=['physics'])
        self.add_rule('drop', 'rubber', 'bounces', 0.9, tags=['physics'])
        self.add_rule('heat', 'ice', 'melts', 0.99, tags=['physics'])
        self.add_rule('heat', 'water', 'evaporates', 0.95, tags=['physics'])
        self.add_rule('heat', 'metal', 'expands', 0.9, tags=['physics'])
        self.add_rule('heat', 'chocolate', 'melts', 0.95, tags=['physics'])
        self.add_rule('heat', 'wax', 'melts', 0.95, tags=['physics'])
        self.add_rule('heat', 'plastic', 'melts', 0.85, tags=['physics'])
        self.add_rule('heat', 'gas', 'expands', 0.95, tags=['physics'])
        self.add_rule('cool', 'water', 'freezes', 0.95, tags=['physics'])
        self.add_rule('cool', 'lava', 'solidifies', 0.99, tags=['physics'])
        self.add_rule('cool', 'gas', 'condenses', 0.9, tags=['physics'])
        self.add_rule('cool', 'metal', 'contracts', 0.9, tags=['physics'])
        self.add_rule('mix', 'oil', 'separates', 0.95, context='water', tags=['physics'])
        self.add_rule('electricity', 'water', 'dangerous', 0.95, tags=['physics'])
        self.add_rule('magnet', 'iron', 'attracts', 0.99, tags=['physics'])
        self.add_rule('magnet', 'wood', 'no_effect', 0.99, tags=['physics'])
        self.add_rule('fire', 'paper', 'burns', 0.99, tags=['physics'])
        self.add_rule('fire', 'wood', 'burns', 0.95, tags=['physics'])
        self.add_rule('fire', 'water', 'extinguishes', 0.9, tags=['physics'])
        self.add_rule('fire', 'gasoline', 'explodes', 0.95, tags=['physics'])
        self.add_rule('fire', 'metal', 'heats', 0.8, tags=['physics'])
        self.add_rule('gravity', 'unsupported_object', 'falls', 0.99, tags=['physics'])
        self.add_rule('gravity', 'ball', 'falls', 0.99, tags=['physics'])
        self.add_rule('pressure', 'gas', 'compresses', 0.95, tags=['physics'])
        self.add_rule('pressure', 'balloon', 'pops', 0.8, tags=['physics'])
        self.add_rule('vacuum', 'sound', 'no_transmission', 0.99, tags=['physics'])
        self.add_rule('light', 'mirror', 'reflects', 0.99, tags=['physics'])
        self.add_rule('light', 'lens', 'focuses', 0.95, tags=['physics'])
        self.add_rule('light', 'prism', 'disperses', 0.95, tags=['physics'])
        self.add_rule('force', 'mass', 'acceleration', 0.99, tags=['physics'])
        self.add_rule('friction', 'motion', 'slowdown', 0.95, tags=['physics'])
        self.add_rule('stretch', 'rubber', 'elastic_return', 0.9, tags=['physics'])
        self.add_rule('stretch', 'glass', 'breaks', 0.95, tags=['physics'])
        self.add_rule('compress', 'spring', 'stores_energy', 0.95, tags=['physics'])
        self.add_rule('spin', 'top', 'gyroscopic_stability', 0.9, tags=['physics'])
        self.add_rule('vibrate', 'string', 'sound', 0.95, tags=['physics'])
        self.add_rule('submerge', 'wood', 'floats', 0.9, tags=['physics'])
        self.add_rule('submerge', 'stone', 'sinks', 0.95, tags=['physics'])
        self.add_rule('throw', 'ball', 'arc_trajectory', 0.9, tags=['physics'])
        self.add_rule('collide', 'billiard_balls', 'momentum_transfer', 0.95, tags=['physics'])
        self.add_rule('freeze', 'water', 'expands', 0.95, tags=['physics'])
        self.add_rule('charge', 'balloon', 'static_cling', 0.8, tags=['physics'])
        self.add_rule('wind', 'sail', 'propulsion', 0.9, tags=['physics'])
        self.add_rule('wind', 'tree', 'sways', 0.85, tags=['physics'])
        self.add_rule('impact', 'glass', 'shatters', 0.9, tags=['physics'])
        # === BIOLOGY (40) ===
        self.add_rule('no_water', 'plant', 'wilts', 0.95, tags=['biology'])
        self.add_rule('sunlight', 'plant', 'grows', 0.9, tags=['biology'])
        self.add_rule('no_food', 'animal', 'hungry', 0.99, tags=['biology'])
        self.add_rule('bacteria', 'wound', 'infection', 0.7, tags=['biology'])
        self.add_rule('vaccine', 'virus', 'immunity', 0.85, tags=['biology'])
        self.add_rule('exercise', 'body', 'stronger', 0.8, tags=['biology'])
        self.add_rule('sleep_deprivation', 'human', 'fatigue', 0.95, tags=['biology'])
        self.add_rule('overeat', 'human', 'weight_gain', 0.8, tags=['biology'])
        self.add_rule('cold_exposure', 'human', 'hypothermia', 0.7, tags=['biology'])
        self.add_rule('sunburn', 'skin', 'damage', 0.85, tags=['biology'])
        self.add_rule('poison', 'animal', 'sickness', 0.9, tags=['biology'])
        self.add_rule('antibiotics', 'bacteria', 'dies', 0.8, tags=['biology'])
        self.add_rule('dehydration', 'human', 'weakness', 0.9, tags=['biology'])
        self.add_rule('oxygen_deprivation', 'brain', 'damage', 0.95, tags=['biology'])
        self.add_rule('pollinate', 'flower', 'fruit', 0.8, tags=['biology'])
        self.add_rule('fertilize', 'soil', 'nutrient_rich', 0.85, tags=['biology'])
        self.add_rule('overwater', 'plant', 'root_rot', 0.7, tags=['biology'])
        self.add_rule('prune', 'tree', 'new_growth', 0.8, tags=['biology'])
        self.add_rule('stress', 'human', 'cortisol_increase', 0.85, tags=['biology'])
        self.add_rule('meditation', 'human', 'calm', 0.75, tags=['biology'])
        self.add_rule('alcohol', 'liver', 'damage', 0.6, tags=['biology'])
        self.add_rule('smoking', 'lungs', 'damage', 0.8, tags=['biology'])
        self.add_rule('darkness', 'plant', 'dies', 0.8, tags=['biology'])
        self.add_rule('frost', 'plant', 'dies', 0.85, tags=['biology'])
        self.add_rule('drought', 'crops', 'fail', 0.9, tags=['biology'])
        self.add_rule('flood', 'crops', 'drown', 0.85, tags=['biology'])
        self.add_rule('bite', 'human', 'pain', 0.9, tags=['biology'])
        self.add_rule('venom', 'human', 'poisoning', 0.85, tags=['biology'])
        self.add_rule('rest', 'injury', 'heals', 0.75, tags=['biology'])
        self.add_rule('contaminate', 'food', 'food_poisoning', 0.7, tags=['biology'])
        self.add_rule('age', 'human', 'weakens', 0.8, tags=['biology'])
        self.add_rule('mutation', 'cell', 'cancer_risk', 0.3, tags=['biology'])
        self.add_rule('photosynthesis', 'plant', 'oxygen', 0.95, tags=['biology'])
        self.add_rule('decompose', 'organic_matter', 'nutrients', 0.9, tags=['biology'])
        self.add_rule('hibernate', 'bear', 'survives_winter', 0.95, tags=['biology'])
        self.add_rule('migrate', 'birds', 'survive_winter', 0.9, tags=['biology'])
        self.add_rule('evolve', 'species', 'adaptation', 0.7, tags=['biology'])
        self.add_rule('starve', 'animal', 'dies', 0.9, tags=['biology'])
        self.add_rule('hydrate', 'human', 'energy', 0.8, tags=['biology'])
        self.add_rule('caffeine', 'human', 'alertness', 0.85, tags=['biology'])
        # === CHEMISTRY (30) ===
        self.add_rule('acid', 'metal', 'dissolves', 0.85, tags=['chemistry'])
        self.add_rule('acid', 'base', 'neutralizes', 0.95, tags=['chemistry'])
        self.add_rule('rust', 'iron', 'weakens', 0.8, tags=['chemistry'])
        self.add_rule('remove_oxygen', 'fire', 'extinguishes', 0.99, tags=['chemistry'])
        self.add_rule('baking_soda', 'vinegar', 'fizzes', 0.99, tags=['chemistry'])
        self.add_rule('salt', 'water', 'dissolves', 0.95, tags=['chemistry'])
        self.add_rule('bleach', 'color', 'fades', 0.9, tags=['chemistry'])
        self.add_rule('oxidize', 'iron', 'rust', 0.8, tags=['chemistry'])
        self.add_rule('electrolysis', 'water', 'hydrogen_oxygen', 0.9, tags=['chemistry'])
        self.add_rule('catalyst', 'reaction', 'speeds_up', 0.85, tags=['chemistry'])
        self.add_rule('burn', 'fuel', 'carbon_dioxide', 0.9, tags=['chemistry'])
        self.add_rule('ferment', 'sugar', 'alcohol', 0.8, tags=['chemistry'])
        self.add_rule('distill', 'mixture', 'separates', 0.9, tags=['chemistry'])
        self.add_rule('polymerize', 'monomers', 'plastic', 0.85, tags=['chemistry'])
        self.add_rule('corrode', 'metal', 'weakens', 0.8, tags=['chemistry'])
        self.add_rule('dissolve', 'sugar', 'sweet_solution', 0.95, context='water', tags=['chemistry'])
        self.add_rule('evaporate', 'solution', 'crystals', 0.8, tags=['chemistry'])
        self.add_rule('combust', 'hydrogen', 'water', 0.95, tags=['chemistry'])
        self.add_rule('react', 'sodium', 'explosion', 0.9, context='water', tags=['chemistry'])
        self.add_rule('mix', 'bleach', 'toxic_gas', 0.95, context='ammonia', tags=['chemistry'])
        self.add_rule('heat', 'sugar', 'caramelizes', 0.9, tags=['chemistry'])
        self.add_rule('freeze', 'salt_water', 'lower_freezing_point', 0.9, tags=['chemistry'])
        self.add_rule('add_salt', 'ice', 'melts', 0.85, tags=['chemistry'])
        self.add_rule('expose_air', 'apple', 'browns', 0.8, tags=['chemistry'])
        self.add_rule('mix', 'paint_colors', 'new_color', 0.95, tags=['chemistry'])
        self.add_rule('detergent', 'grease', 'dissolves', 0.85, tags=['chemistry'])
        self.add_rule('photochemical', 'silver_halide', 'darkens', 0.8, tags=['chemistry'])
        self.add_rule('reduce', 'ore', 'metal', 0.8, tags=['chemistry'])
        self.add_rule('titrate', 'acid', 'endpoint', 0.9, tags=['chemistry'])
        self.add_rule('sublime', 'dry_ice', 'gas', 0.99, tags=['chemistry'])
        # === SOCIAL (40) ===
        self.add_rule('insult', 'person', 'anger', 0.85, tags=['social'])
        self.add_rule('help', 'person', 'gratitude', 0.9, tags=['social'])
        self.add_rule('lie', 'trust', 'broken_trust', 0.9, tags=['social'])
        self.add_rule('gift', 'person', 'happiness', 0.85, tags=['social'])
        self.add_rule('ignore', 'person', 'loneliness', 0.7, tags=['social'])
        self.add_rule('praise', 'child', 'confidence', 0.8, tags=['social'])
        self.add_rule('punishment', 'behavior', 'decreases', 0.75, tags=['social'])
        self.add_rule('reward', 'behavior', 'increases', 0.85, tags=['social'])
        self.add_rule('betray', 'friend', 'broken_trust', 0.95, tags=['social'])
        self.add_rule('apologize', 'person', 'forgiveness', 0.7, tags=['social'])
        self.add_rule('listen', 'person', 'feels_valued', 0.85, tags=['social'])
        self.add_rule('criticize', 'person', 'defensiveness', 0.75, tags=['social'])
        self.add_rule('encourage', 'person', 'motivation', 0.8, tags=['social'])
        self.add_rule('threaten', 'person', 'fear', 0.9, tags=['social'])
        self.add_rule('share', 'resources', 'cooperation', 0.8, tags=['social'])
        self.add_rule('hoard', 'resources', 'resentment', 0.7, tags=['social'])
        self.add_rule('educate', 'child', 'knowledge', 0.85, tags=['social'])
        self.add_rule('neglect', 'child', 'developmental_issues', 0.8, tags=['social'])
        self.add_rule('collaborate', 'team', 'productivity', 0.8, tags=['social'])
        self.add_rule('micromanage', 'team', 'resentment', 0.75, tags=['social'])
        self.add_rule('trust', 'partner', 'strong_bond', 0.85, tags=['social'])
        self.add_rule('gossip', 'community', 'distrust', 0.7, tags=['social'])
        self.add_rule('empathy', 'person', 'connection', 0.85, tags=['social'])
        self.add_rule('bully', 'victim', 'trauma', 0.9, tags=['social'])
        self.add_rule('mentor', 'student', 'growth', 0.85, tags=['social'])
        self.add_rule('isolate', 'person', 'depression', 0.7, tags=['social'])
        self.add_rule('celebrate', 'achievement', 'motivation', 0.8, tags=['social'])
        self.add_rule('compete', 'rivals', 'innovation', 0.7, tags=['social'])
        self.add_rule('respect', 'elder', 'wisdom_shared', 0.8, tags=['social'])
        self.add_rule('discriminate', 'group', 'conflict', 0.85, tags=['social'])
        self.add_rule('include', 'outsider', 'belonging', 0.8, tags=['social'])
        self.add_rule('exclude', 'person', 'resentment', 0.8, tags=['social'])
        self.add_rule('communicate', 'couple', 'understanding', 0.8, tags=['social'])
        self.add_rule('stonewall', 'partner', 'frustration', 0.85, tags=['social'])
        self.add_rule('forgive', 'offender', 'peace', 0.7, tags=['social'])
        self.add_rule('shame', 'person', 'withdrawal', 0.8, tags=['social'])
        self.add_rule('validate', 'feelings', 'trust', 0.85, tags=['social'])
        self.add_rule('dismiss', 'feelings', 'resentment', 0.8, tags=['social'])
        self.add_rule('lead', 'group', 'direction', 0.8, tags=['social'])
        self.add_rule('abandon', 'child', 'attachment_issues', 0.9, tags=['social'])
        # === TECHNOLOGY (20) ===
        self.add_rule('power_off', 'computer', 'data_loss_unsaved', 0.6, tags=['tech'])
        self.add_rule('virus', 'computer', 'malfunction', 0.8, tags=['tech'])
        self.add_rule('water', 'electronics', 'short_circuit', 0.9, tags=['tech'])
        self.add_rule('overclock', 'cpu', 'overheats', 0.7, tags=['tech'])
        self.add_rule('drop', 'hard_drive', 'data_loss', 0.6, tags=['tech'])
        self.add_rule('surge', 'electronics', 'damage', 0.8, tags=['tech'])
        self.add_rule('update', 'software', 'bug_fixes', 0.7, tags=['tech'])
        self.add_rule('encrypt', 'data', 'secure', 0.9, tags=['tech'])
        self.add_rule('hack', 'system', 'data_breach', 0.7, tags=['tech'])
        self.add_rule('backup', 'data', 'recoverable', 0.95, tags=['tech'])
        self.add_rule('overload', 'server', 'crash', 0.8, tags=['tech'])
        self.add_rule('defragment', 'disk', 'faster', 0.6, tags=['tech'])
        self.add_rule('reboot', 'computer', 'clears_errors', 0.7, tags=['tech'])
        self.add_rule('overheat', 'laptop', 'throttles', 0.85, tags=['tech'])
        self.add_rule('dust', 'fan', 'overheats', 0.7, tags=['tech'])
        self.add_rule('charge', 'battery', 'full_power', 0.9, tags=['tech'])
        self.add_rule('discharge', 'battery', 'device_off', 0.95, tags=['tech'])
        self.add_rule('format', 'drive', 'data_erased', 0.99, tags=['tech'])
        self.add_rule('ddos', 'server', 'unavailable', 0.85, tags=['tech'])
        self.add_rule('put', 'metal', 'sparks', 0.9, context='microwave', tags=['tech'])
        # === ECONOMICS (20) ===
        self.add_rule('high_demand', 'low_supply', 'price_increase', 0.9, tags=['economics'])
        self.add_rule('inflation', 'savings', 'value_decrease', 0.85, tags=['economics'])
        self.add_rule('monopoly', 'market', 'high_prices', 0.85, tags=['economics'])
        self.add_rule('competition', 'market', 'lower_prices', 0.8, tags=['economics'])
        self.add_rule('recession', 'jobs', 'unemployment', 0.8, tags=['economics'])
        self.add_rule('invest', 'stock', 'potential_growth', 0.6, tags=['economics'])
        self.add_rule('tax_increase', 'spending', 'decreases', 0.7, tags=['economics'])
        self.add_rule('subsidy', 'industry', 'growth', 0.75, tags=['economics'])
        self.add_rule('trade_war', 'economy', 'slowdown', 0.8, tags=['economics'])
        self.add_rule('innovation', 'market', 'disruption', 0.7, tags=['economics'])
        self.add_rule('debt', 'person', 'stress', 0.8, tags=['economics'])
        self.add_rule('save', 'money', 'security', 0.8, tags=['economics'])
        self.add_rule('overspend', 'budget', 'debt', 0.85, tags=['economics'])
        self.add_rule('automate', 'jobs', 'displacement', 0.7, tags=['economics'])
        self.add_rule('deregulate', 'market', 'volatility', 0.65, tags=['economics'])
        self.add_rule('print_money', 'currency', 'inflation', 0.85, tags=['economics'])
        self.add_rule('raise_interest', 'borrowing', 'decreases', 0.8, tags=['economics'])
        self.add_rule('lower_interest', 'borrowing', 'increases', 0.8, tags=['economics'])
        self.add_rule('tariff', 'imports', 'price_increase', 0.8, tags=['economics'])
        self.add_rule('stimulus', 'economy', 'growth', 0.7, tags=['economics'])
        # === CHAINING RULES (effects that become causes) ===
        for a, o, e, p in [('breaks','glass','sharp_shards',0.9),('melts','ice','water',0.99),
            ('evaporates','water','steam',0.95),('burns','paper','ash',0.95),
            ('wilts','plant','dies',0.7),('hungry','animal','weakens',0.8),
            ('fatigue','human','errors',0.7),('infection','wound','fever',0.6),
            ('overheats','cpu','crash',0.7),('short_circuit','electronics','fire',0.4)]:
            self.add_rule(a, o, e, p, tags=['chain'])

    def simulate(self, action, object_name, context=None, max_hops=5):
        """Simulate cause-effect chain. Returns list of (effect, probability) tuples."""
        chain = []
        current_action = action.lower().strip()
        current_obj = object_name.lower().strip()
        cumulative_prob = 1.0
        seen = set()

        for _ in range(max_hops):
            matched = self._find_rule(current_action, current_obj, context)
            if not matched or matched.effect in seen:
                break
            seen.add(matched.effect)
            cumulative_prob *= matched.probability
            chain.append((matched.effect, round(cumulative_prob, 3)))
            # Chain: the effect becomes the next action, object stays or shifts
            current_action = matched.effect
            current_obj = current_obj

        return chain

    def _find_rule(self, action, obj, context=None):
        """Find best matching rule using fuzzy substring matching."""
        best = None
        best_score = 0
        for rule in self.rules:
            score = 0
            if rule.action in action or action in rule.action:
                score += 2
            if rule.obj in obj or obj in rule.obj:
                score += 2
            elif obj in rule.action:  # handle reversed matches
                score += 1
            if context and rule.context and (rule.context in context or context in rule.context):
                score += 3
            if score > best_score:
                best_score = score
                best = rule
        return best if best_score >= 3 else None

    def explain(self, question):
        """Parse and answer natural language 'what happens if...' questions."""
        q = question.lower().strip().rstrip('?')
        # Remove common prefixes
        for prefix in ['what happens if', 'what would happen if', 'what if',
                       'what happens when', 'what would happen when']:
            if q.startswith(prefix):
                q = q[len(prefix):].strip()
                break

        action, obj, context = self._parse_question(q)
        chain = self.simulate(action, obj, context)

        if not chain:
            return f"No known causal rules for '{action}' + '{obj}'. Cannot predict outcome."

        lines = [f"Q: {question}", f"Action: {action} → Object: {obj}" +
                 (f" (context: {context})" if context else ""), "Chain of effects:"]
        for i, (effect, prob) in enumerate(chain, 1):
            lines.append(f"  {i}. {effect} (probability: {prob:.1%})")
        return "\n".join(lines)

    def _parse_question(self, text):
        """Extract action, object, and optional context from text."""
        # Synonym expansion for better matching
        synonyms = {
            'deprive': 'no_water', 'starve': 'no_food', 'dehydrate': 'no_water',
            'overheat': 'heat', 'freeze': 'cool', 'electrocute': 'electricity',
        }
        # Handle "deprive X of Y" → action=no_Y, object=X
        m2 = re.search(r'(?:you )?(?:deprive|starve|rob)\s+(?:a |an |the )?(.+?)\s+of\s+(.+)', text)
        if m2:
            obj = m2.group(1).strip()
            resource = m2.group(2).strip()
            return f"no_{resource}", obj, None

        # Try pattern: "you [verb] [object] in/on/with [context]"
        m = re.search(r'(?:you |i |we |someone )?(\w+)\s+(?:a |an |the )?(.+?)(?:\s+(?:in|on|into|with|near)\s+(?:a |an |the )?(.+))?$', text)
        if m:
            action = m.group(1)
            obj = m.group(2).strip()
            context = m.group(3).strip() if m.group(3) else None
            action = synonyms.get(action, action)
            return action, obj, context

        # Fallback: split on spaces
        words = text.split()
        if len(words) >= 2:
            action = synonyms.get(words[0], words[0])
            return action, ' '.join(words[1:3]), ' '.join(words[3:]) or None
        return text, 'object', None


# === STANDALONE TEST ===
if __name__ == '__main__':
    sim = WorldSimulator()
    print(f"Loaded {len(sim.rules)} causal rules.\n")
    for q in ["What happens if you drop a glass?", "What happens if you heat ice?",
              "What would happen if you put metal in a microwave?",
              "What happens if you insult a person?",
              "What happens if you deprive a plant of water?"]:
        print("=" * 60)
        print(sim.explain(q))
        print()
    print("=" * 60)
    print("Direct simulation: fire + paper")
    for effect, prob in sim.simulate('fire', 'paper'):
        print(f"  → {effect} ({prob:.1%})")
