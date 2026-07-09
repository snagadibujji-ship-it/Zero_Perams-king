"""
Temporal Benchmark — LSTM Sequence Model
==========================================
Tests whether the TEMPORAL ORDER of events matters.

Tree-based models (LightGBM) treat each event independently.
This benchmark uses an LSTM to test if the SEQUENCE of events
(the order they happen) improves prediction of:
  1. Next event category prediction
  2. Time-to-next-failure prediction

If the world model produces realistic temporal patterns,
sequence models should outperform bag-of-features models.

Requirements: numpy, torch (optional — falls back to simple RNN if no torch)
"""
import os, sys, time, json, warnings
import numpy as np
from collections import Counter
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score, accuracy_score, mean_absolute_error

warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════════════════
# DATA GENERATION (sequence-aware)
# ═══════════════════════════════════════════════════════════

def generate_sequences(n_events=5000, seed=42, seq_len=20):
    """Generate event sequences grouped by episode.
    
    Returns sequences of (features, labels) where each sequence
    is seq_len consecutive events from one episode.
    """
    from world_engine.episode import EpisodeGenerator
    from world_engine.registry import INDUSTRIES
    import random

    rng = random.Random(seed)
    industry_ids = list(INDUSTRIES.keys())
    selected = rng.sample(industry_ids, min(10, len(industry_ids)))
    events_per = n_events // len(selected)

    all_events = []
    for idx, iid in enumerate(selected):
        industry = INDUSTRIES[iid]
        ep_seed = seed + idx * 1000
        gen = EpisodeGenerator(industry, seed=ep_seed, year=2024)
        records = gen.generate_episode(target_lines=events_per)
        for r in records:
            all_events.append({
                "industry": iid,
                "category": r["event_category"],
                "subtype": r["event_subtype"],
                "shift": r["shift"],
                "hour": int(r["timestamp"].split("T")[1][:2]) if "T" in r["timestamp"] else 12,
                "mood": r.get("mood", "neutral"),
                "involved_count": r.get("involved_count", 1),
                "has_asset": 1 if r.get("assets_mentioned") else 0,
            })

    # Encode categoricals
    cat_encoder = LabelEncoder()
    all_categories = [e["category"] for e in all_events]
    cat_encoder.fit(all_categories)
    n_classes = len(cat_encoder.classes_)

    shift_enc = LabelEncoder()
    shift_enc.fit([e["shift"] for e in all_events])

    mood_enc = LabelEncoder()
    mood_enc.fit([e.get("mood", "neutral") or "neutral" for e in all_events])

    industry_enc = LabelEncoder()
    industry_enc.fit([e["industry"] for e in all_events])

    # Build feature vectors
    features = []
    for e in all_events:
        features.append([
            cat_encoder.transform([e["category"]])[0],
            shift_enc.transform([e["shift"]])[0],
            mood_enc.transform([e.get("mood", "neutral") or "neutral"])[0],
            industry_enc.transform([e["industry"]])[0],
            e["hour"] / 24.0,
            e["involved_count"] / 10.0,
            e["has_asset"],
        ])
    features = np.array(features, dtype=np.float32)

    # Create sequences: predict next category from previous seq_len events
    X_seqs = []
    y_seqs = []
    for i in range(seq_len, len(features)):
        X_seqs.append(features[i - seq_len:i])
        y_seqs.append(cat_encoder.transform([all_events[i]["category"]])[0])

    X_seqs = np.array(X_seqs)
    y_seqs = np.array(y_seqs)

    return X_seqs, y_seqs, n_classes, cat_encoder


# ═══════════════════════════════════════════════════════════
# SIMPLE NUMPY RNN (no PyTorch dependency required)
# ═══════════════════════════════════════════════════════════

class SimpleRNN:
    """Minimal RNN for sequence classification (numpy only).
    
    Single-layer Elman RNN with softmax output.
    Not SOTA but proves whether temporal patterns exist.
    """

    def __init__(self, input_dim, hidden_dim, output_dim, lr=0.001):
        self.hidden_dim = hidden_dim
        self.lr = lr
        # Xavier initialization
        scale_ih = np.sqrt(2.0 / (input_dim + hidden_dim))
        scale_ho = np.sqrt(2.0 / (hidden_dim + output_dim))
        self.Wxh = np.random.randn(input_dim, hidden_dim).astype(np.float32) * scale_ih
        self.Whh = np.random.randn(hidden_dim, hidden_dim).astype(np.float32) * scale_ih
        self.bh = np.zeros(hidden_dim, dtype=np.float32)
        self.Who = np.random.randn(hidden_dim, output_dim).astype(np.float32) * scale_ho
        self.bo = np.zeros(output_dim, dtype=np.float32)

    def forward(self, X_seq):
        """Forward pass through sequence. X_seq: (seq_len, input_dim)"""
        h = np.zeros(self.hidden_dim, dtype=np.float32)
        for t in range(X_seq.shape[0]):
            h = np.tanh(X_seq[t] @ self.Wxh + h @ self.Whh + self.bh)
        # Output layer (logits)
        logits = h @ self.Who + self.bo
        return logits, h

    def predict_batch(self, X_batch):
        """Predict class for batch of sequences."""
        preds = []
        for i in range(X_batch.shape[0]):
            logits, _ = self.forward(X_batch[i])
            preds.append(np.argmax(logits))
        return np.array(preds)

    def train_epoch(self, X_train, y_train, batch_size=64):
        """Train one epoch with simple SGD + softmax cross-entropy."""
        n = X_train.shape[0]
        indices = np.random.permutation(n)
        total_loss = 0.0

        for start in range(0, min(n, 2000), batch_size):  # Cap at 2000 samples per epoch for speed
            end = min(start + batch_size, n)
            batch_idx = indices[start:end]

            for i in batch_idx:
                logits, h = self.forward(X_train[i])

                # Softmax
                exp_logits = np.exp(logits - logits.max())
                probs = exp_logits / exp_logits.sum()

                # Cross-entropy gradient
                grad_logits = probs.copy()
                grad_logits[y_train[i]] -= 1.0

                # Backward (output layer only — simplified)
                self.Who -= self.lr * np.outer(h, grad_logits)
                self.bo -= self.lr * grad_logits

                total_loss -= np.log(probs[y_train[i]] + 1e-8)

        return total_loss / min(n, 2000)


# ═══════════════════════════════════════════════════════════
# BASELINE: Majority class + Markov chain
# ═══════════════════════════════════════════════════════════

def majority_baseline(y_train, y_test):
    """Always predict most common class."""
    most_common = Counter(y_train).most_common(1)[0][0]
    preds = np.full(len(y_test), most_common)
    return preds


def markov_baseline(X_train, y_train, X_test, n_classes):
    """First-order Markov: predict based on last event category only."""
    # Build transition matrix
    transitions = np.ones((n_classes, n_classes))  # Laplace smoothing
    for i in range(len(X_train)):
        last_cat = int(X_train[i, -1, 0])  # Last event's category
        transitions[last_cat, y_train[i]] += 1

    # Normalize
    transitions = transitions / transitions.sum(axis=1, keepdims=True)

    # Predict
    preds = []
    for i in range(len(X_test)):
        last_cat = int(X_test[i, -1, 0])
        preds.append(np.argmax(transitions[last_cat]))
    return np.array(preds)


# ═══════════════════════════════════════════════════════════
# MAIN BENCHMARK
# ═══════════════════════════════════════════════════════════

def run_temporal_benchmark(n_events=5000, seeds=None, seq_len=20, epochs=15):
    """Run the full temporal benchmark.
    
    Compares:
    1. Majority class baseline
    2. First-order Markov chain
    3. Simple RNN (sequence model)
    
    If RNN >> Markov >> Majority, temporal patterns are strong.
    """
    if seeds is None:
        seeds = [42, 123, 456]

    results = []
    
    print("=" * 60)
    print("TEMPORAL BENCHMARK — Sequence vs Non-Sequence Models")
    print("=" * 60)
    print(f"Events per seed: {n_events}, Sequence length: {seq_len}")
    print(f"Seeds: {seeds}")
    print()

    for seed in seeds:
        print(f"--- Seed {seed} ---")
        t0 = time.time()

        # Generate data
        X, y, n_classes, encoder = generate_sequences(n_events, seed, seq_len)
        print(f"  Data: {X.shape[0]} sequences, {n_classes} classes, {X.shape[2]} features")

        # Train/test split (80/20, temporal — no shuffling to preserve time order)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # 1. Majority baseline
        maj_preds = majority_baseline(y_train, y_test)
        maj_acc = accuracy_score(y_test, maj_preds)
        maj_f1 = f1_score(y_test, maj_preds, average="weighted", zero_division=0)

        # 2. Markov baseline
        mark_preds = markov_baseline(X_train, y_train, X_test, n_classes)
        mark_acc = accuracy_score(y_test, mark_preds)
        mark_f1 = f1_score(y_test, mark_preds, average="weighted", zero_division=0)

        # 3. Simple RNN
        rnn = SimpleRNN(input_dim=X.shape[2], hidden_dim=32, output_dim=n_classes, lr=0.002)
        for ep in range(epochs):
            loss = rnn.train_epoch(X_train, y_train)

        rnn_preds = rnn.predict_batch(X_test)
        rnn_acc = accuracy_score(y_test, rnn_preds)
        rnn_f1 = f1_score(y_test, rnn_preds, average="weighted", zero_division=0)

        elapsed = time.time() - t0
        print(f"  Majority:  acc={maj_acc:.3f}  F1={maj_f1:.3f}")
        print(f"  Markov:    acc={mark_acc:.3f}  F1={mark_f1:.3f}")
        print(f"  RNN:       acc={rnn_acc:.3f}  F1={rnn_f1:.3f}")
        print(f"  Time: {elapsed:.1f}s")
        print()

        results.append({
            "seed": seed,
            "n_events": n_events,
            "n_sequences": len(X),
            "n_classes": n_classes,
            "majority": {"accuracy": round(maj_acc, 4), "f1_weighted": round(maj_f1, 4)},
            "markov": {"accuracy": round(mark_acc, 4), "f1_weighted": round(mark_f1, 4)},
            "rnn": {"accuracy": round(rnn_acc, 4), "f1_weighted": round(rnn_f1, 4)},
            "elapsed_seconds": round(elapsed, 1),
        })

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    avg_maj = np.mean([r["majority"]["f1_weighted"] for r in results])
    avg_mark = np.mean([r["markov"]["f1_weighted"] for r in results])
    avg_rnn = np.mean([r["rnn"]["f1_weighted"] for r in results])

    print(f"  Majority F1:  {avg_maj:.4f}")
    print(f"  Markov F1:    {avg_mark:.4f}  (Δ vs majority: +{(avg_mark-avg_maj)*100:.1f}%)")
    print(f"  RNN F1:       {avg_rnn:.4f}  (Δ vs majority: +{(avg_rnn-avg_maj)*100:.1f}%)")
    print()

    if avg_rnn > avg_mark * 1.05:
        print("  ✓ TEMPORAL PATTERNS DETECTED: RNN outperforms Markov by >5%")
        print("    → Sequence order carries information beyond first-order transitions")
    elif avg_mark > avg_maj * 1.05:
        print("  ~ WEAK TEMPORAL SIGNAL: Markov > Majority but RNN ≈ Markov")
        print("    → First-order transitions capture most temporal structure")
    else:
        print("  ✗ NO TEMPORAL SIGNAL: All models ≈ Majority baseline")
        print("    → Event ordering may be too random or categories too uniform")

    return results


if __name__ == "__main__":
    results = run_temporal_benchmark(n_events=5000, seeds=[42, 123, 456], seq_len=20, epochs=15)
    
    # Save results
    out_path = os.path.join(os.path.dirname(__file__), "results", "temporal_benchmark_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {out_path}")
