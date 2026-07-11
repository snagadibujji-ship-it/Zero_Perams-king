#!/usr/bin/env python3
"""
RSE — Recursive Self-Evolution
The system that makes itself smarter every hour without human intervention.
Monitor → Diagnose → Acquire → Verify → Optimize → Report
"""
import os, json, time

class RecursiveSelfEvolution:
    """Axima gets smarter automatically. No retraining needed."""
    
    def __init__(self, data_dir='user_data'):
        self.data_dir = data_dir
        self.metrics_file = os.path.join(data_dir, 'rse_metrics.json')
        self.gaps_file = os.path.join(data_dir, 'rse_gaps.json')
        os.makedirs(data_dir, exist_ok=True)
        self.metrics = self._load_metrics()
    
    def _load_metrics(self):
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file) as f:
                    return json.load(f)
        except: pass
        return {
            'total_queries': 0, 'answered': 0, 'failed': 0,
            'avg_confidence': 0.0, 'topics_failed': {},
            'improvement_history': [], 'knowledge_size': 0,
            'session_count': 0, 'last_diagnosis': None,
        }
    
    def _save_metrics(self):
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except: pass
    
    # ── PHASE 1: MONITOR (every query) ──
    def record_query(self, query, answered, confidence, topic=None):
        """Record every query outcome."""
        self.metrics['total_queries'] += 1
        if answered:
            self.metrics['answered'] += 1
        else:
            self.metrics['failed'] += 1
            if topic:
                self.metrics['topics_failed'][topic] = self.metrics['topics_failed'].get(topic, 0) + 1
        
        # Running average confidence
        n = self.metrics['total_queries']
        old_avg = self.metrics['avg_confidence']
        self.metrics['avg_confidence'] = old_avg + (confidence - old_avg) / n
        
        self._save_metrics()
    
    # ── PHASE 2: DIAGNOSE (on demand or periodic) ──
    def diagnose(self):
        """Identify knowledge gaps and weak areas."""
        diagnosis = {
            'answer_rate': self.metrics['answered'] / max(self.metrics['total_queries'], 1),
            'top_gaps': sorted(self.metrics['topics_failed'].items(), key=lambda x: -x[1])[:10],
            'avg_confidence': self.metrics['avg_confidence'],
            'total_queries': self.metrics['total_queries'],
            'recommendations': [],
        }
        
        # Generate recommendations
        if diagnosis['answer_rate'] < 0.8:
            diagnosis['recommendations'].append("Answer rate below 80% — need more knowledge")
        
        for topic, count in diagnosis['top_gaps'][:3]:
            if count >= 3:
                diagnosis['recommendations'].append(f"Topic '{topic}' failed {count}x — auto-learn recommended")
        
        if diagnosis['avg_confidence'] < 0.7:
            diagnosis['recommendations'].append("Average confidence low — knowledge may be shallow")
        
        self.metrics['last_diagnosis'] = time.strftime('%Y-%m-%d %H:%M')
        self._save_metrics()
        return diagnosis
    
    # ── PHASE 3: ACQUIRE (fill gaps) ──
    def get_learning_targets(self, max_targets=10):
        """Return top topics that should be learned next."""
        gaps = sorted(self.metrics['topics_failed'].items(), key=lambda x: -x[1])
        return [topic for topic, count in gaps[:max_targets] if count >= 2]
    
    def mark_learned(self, topic):
        """Mark a topic as successfully learned (remove from gaps)."""
        if topic in self.metrics['topics_failed']:
            del self.metrics['topics_failed'][topic]
        self._save_metrics()
    
    # ── PHASE 4: VERIFY (check improvement) ──
    def get_improvement_rate(self):
        """Calculate improvement over time."""
        history = self.metrics.get('improvement_history', [])
        if len(history) < 2:
            return 0
        recent = history[-1]
        previous = history[-2] if len(history) > 1 else history[0]
        return recent - previous
    
    def snapshot(self):
        """Take a snapshot of current performance for tracking."""
        rate = self.metrics['answered'] / max(self.metrics['total_queries'], 1)
        self.metrics.setdefault('improvement_history', []).append(round(rate, 3))
        if len(self.metrics['improvement_history']) > 100:
            self.metrics['improvement_history'] = self.metrics['improvement_history'][-100:]
        self._save_metrics()
    
    # ── PHASE 5: REPORT ──
    def report(self):
        """Generate human-readable status report."""
        d = self.diagnose()
        lines = [
            f"=== RSE Self-Evolution Report ===",
            f"  Queries: {self.metrics['total_queries']}",
            f"  Answer rate: {d['answer_rate']*100:.1f}%",
            f"  Avg confidence: {d['avg_confidence']:.2f}",
            f"  Knowledge gaps: {len(self.metrics['topics_failed'])}",
            f"  Top gaps: {', '.join(t for t,_ in d['top_gaps'][:5]) or 'none'}",
            f"  Improvement: {self.get_improvement_rate():+.3f}",
        ]
        if d['recommendations']:
            lines.append(f"  Recommendations:")
            for r in d['recommendations']:
                lines.append(f"    → {r}")
        return '\n'.join(lines)


class KnowledgeFusionReactor:
    """KFR — Grow knowledge from multiple sources simultaneously."""
    
    def __init__(self, data_dir='/root/hybrid-ai/src/data'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'fused_knowledge.txt')
    
    def fuse_from_inference(self, concepts, relations):
        """Generate new facts via transitive closure + sibling inference."""
        new_facts = []
        
        # Transitive: if A is_a B and B is_a C → A is_a C
        for a, rel, b in relations:
            if rel == 'is_a':
                for b2, rel2, c in relations:
                    if b2 == b and rel2 == 'is_a' and c != a:
                        new_facts.append(f"{a} is a type of {c}")
        
        # Sibling inference: if 80% of X's siblings have property P, X probably has P
        # (simplified version)
        
        return new_facts
    
    def fuse_from_web(self, search_results):
        """Extract facts from web search results."""
        import re
        facts = []
        for result in search_results:
            if isinstance(result, str):
                sentences = re.split(r'(?<=[.!?])\s+', result)
                for s in sentences[:3]:
                    clean = s.strip()
                    if len(clean) > 20 and len(clean) < 200:
                        facts.append(clean)
        return facts
    
    def fuse_from_user(self, statement):
        """Extract fact from user teaching."""
        # "Remember that X is Y" → "X is Y"
        for prefix in ['remember that ', 'note that ', 'know that ']:
            if statement.lower().startswith(prefix):
                return statement[len(prefix):]
        return statement
    
    def save_fused(self, facts):
        """Append new facts to knowledge source file."""
        if not facts: return 0
        with open(self.output_file, 'a') as f:
            for fact in facts:
                clean = fact.encode('ascii', 'ignore').decode('ascii').strip()
                if len(clean) > 10:
                    f.write(clean + '\n')
        return len(facts)
    
    def get_growth_stats(self):
        """Report knowledge growth."""
        if os.path.exists(self.output_file):
            with open(self.output_file) as f:
                lines = f.readlines()
            return {'fused_facts': len(lines), 'file_size_kb': os.path.getsize(self.output_file) / 1024}
        return {'fused_facts': 0, 'file_size_kb': 0}


# Self test
if __name__ == '__main__':
    rse = RecursiveSelfEvolution('/tmp/rse_test')
    rse.record_query("What is water?", True, 0.95, "water")
    rse.record_query("What is dark matter?", False, 0.0, "dark_matter")
    rse.record_query("What is dark matter?", False, 0.0, "dark_matter")
    rse.record_query("What is dark matter?", False, 0.0, "dark_matter")
    rse.snapshot()
    print(rse.report())
    print(f"\nLearning targets: {rse.get_learning_targets()}")
    
    kfr = KnowledgeFusionReactor('/tmp')
    facts = kfr.fuse_from_web(["Water is a liquid. It boils at 100C. H2O is its formula."])
    print(f"\nKFR fused: {facts}")
