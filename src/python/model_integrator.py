#!/usr/bin/env python3
"""
Model Integrator — Bridges trained micro-models with the VisionEngine.

Loads .micv weight files and extends the classical vision engine with
learned classifiers. Maintains the zero-parameter philosophy for the
base system while adding learned knowledge from user's images.

Features:
  - Auto-discovers trained models in user_data/models/
  - Hot-reloads models without restarting the engine
  - Combines classical CV results with neural predictions
  - Confidence-aware fusion (neural overrides classical only when confident)
  - Model versioning and A/B comparison
  - Inference benchmarking (<5ms target per model)
"""
import os
import io
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


from vision_trainer import MicroCNN, MODEL_CONFIGS

# ═══ Constants ═══
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'models')
MIN_CONFIDENCE_THRESHOLD = 0.6   # Below this, neural prediction is ignored
HIGH_CONFIDENCE_THRESHOLD = 0.85  # Above this, neural prediction overrides classical


@dataclass
class ModelSlot:
    """A loaded model ready for inference."""
    name: str
    model: "MicroCNN"
    categories: List[str]
    model_type: str = "classifier"  # classifier, detector, style, feature
    input_size: Tuple[int, int] = (64, 64)
    loaded_at: float = 0.0
    inference_count: int = 0
    avg_inference_ms: float = 0.0
    version: str = "1.0"


@dataclass
class IntegratedResult:
    """Combined result from classical CV + neural models."""
    # Classical vision analysis
    classical: Dict = field(default_factory=dict)
    # Neural model predictions
    neural: Dict = field(default_factory=dict)
    # Fused/final result
    fused: Dict = field(default_factory=dict)
    # Metadata
    models_used: List[str] = field(default_factory=list)
    inference_time_ms: float = 0.0
    confidence: float = 0.0


class ModelIntegrator:
    """
    Integrates trained micro-models with the existing VisionEngine.
    
    The integration strategy:
      1. Classical CV always runs first (baseline, never wrong)
      2. Neural models provide additional predictions
      3. Fusion logic combines them based on confidence
      4. Neural overrides classical ONLY when highly confident
    
    Usage:
        from vision import VisionEngine
        from model_integrator import ModelIntegrator
        
        vision = VisionEngine()
        integrator = ModelIntegrator()
        integrator.load_all_models()
        
        # Analyze with both classical + neural
        result = integrator.analyze(image_path, vision_engine=vision)
        
        print(result.fused)       # Best combined answer
        print(result.classical)   # Pure classical CV
        print(result.neural)      # Pure neural predictions
    """

    def __init__(self, models_dir: str = None):
        self.models_dir = models_dir or MODELS_DIR
        self.slots: Dict[str, ModelSlot] = {}  # name -> ModelSlot
        self._model_configs: Dict[str, Dict] = {}  # Cached category mappings
        
        # Performance tracking
        self.total_inferences = 0
        self.total_time_ms = 0.0

    # ═══ MODEL LOADING ═══

    def load_all_models(self) -> int:
        """
        Auto-discover and load all trained models from models directory.
        
        Returns:
            Number of models loaded
        """
        if not NUMPY_AVAILABLE:
            print("  [WARN] NumPy not available. Neural models disabled.")
            return 0

        if not os.path.exists(self.models_dir):
            return 0

        loaded = 0
        for f in os.listdir(self.models_dir):
            if f.endswith('.micv') and not f.endswith('_best.micv'):
                name = f[:-5]
                try:
                    self.load_model(name)
                    loaded += 1
                except Exception as e:
                    print(f"  [WARN] Failed to load model '{name}': {e}")

        if loaded:
            print(f"  [OK] {loaded} micro-models loaded for inference")
        return loaded

    def load_model(self, name: str, version: str = "1.0") -> bool:
        """Load a specific model by name."""
        model_path = os.path.join(self.models_dir, f"{name}.micv")
        cat_path = os.path.join(self.models_dir, f"{name}_categories.json")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Load the CNN
        model = MicroCNN.load_weights(model_path)
        
        # Load category mapping
        categories = []
        if os.path.exists(cat_path):
            with open(cat_path) as f:
                data = json.load(f)
                categories = data.get("categories", [])

        # Determine model type from name heuristics
        model_type = self._infer_model_type(name)

        slot = ModelSlot(
            name=name,
            model=model,
            categories=categories,
            model_type=model_type,
            input_size=model.input_size,
            loaded_at=time.time(),
            version=version,
        )
        
        self.slots[name] = slot
        return True

    def unload_model(self, name: str):
        """Unload a model to free memory."""
        if name in self.slots:
            del self.slots[name]

    def reload_model(self, name: str):
        """Hot-reload a model (useful after retraining)."""
        self.unload_model(name)
        self.load_model(name)


    # ═══ INFERENCE ═══

    def predict(self, image_path: str = None, image_bytes: bytes = None,
                model_name: str = None) -> Dict:
        """
        Run neural prediction on an image.
        
        Args:
            image_path: Path to image file
            image_bytes: Raw image bytes (alternative to path)
            model_name: Specific model to use (or None for all)
            
        Returns:
            Dict with predictions from each model
        """
        if not NUMPY_AVAILABLE or not PIL_AVAILABLE:
            return {"error": "NumPy and Pillow required for neural inference"}

        if not self.slots:
            return {"error": "No models loaded. Call load_all_models() first."}

        # Load image
        if image_path:
            img = Image.open(image_path).convert('RGB')
        elif image_bytes:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        else:
            return {"error": "Provide image_path or image_bytes"}

        results = {}
        models_to_run = [model_name] if model_name else list(self.slots.keys())

        for name in models_to_run:
            if name not in self.slots:
                continue
            
            slot = self.slots[name]
            start = time.perf_counter()
            
            try:
                # Resize to model's expected input
                resized = img.resize(slot.input_size, Image.LANCZOS)
                arr = np.array(resized, dtype=np.float32) / 255.0
                arr = arr.transpose(2, 0, 1)  # HWC -> CHW
                arr = arr[np.newaxis]  # Add batch dim
                
                # Run inference
                class_idx, confidence = slot.model.predict(arr)
                
                elapsed_ms = (time.perf_counter() - start) * 1000
                
                # Map to category name
                category = (slot.categories[class_idx] 
                           if class_idx < len(slot.categories) 
                           else f"class_{class_idx}")
                
                # Get top-3 predictions
                probs = slot.model.forward(arr)[0]
                top_indices = np.argsort(probs)[::-1][:3]
                top_predictions = []
                for idx in top_indices:
                    cat = (slot.categories[idx] 
                          if idx < len(slot.categories) 
                          else f"class_{idx}")
                    top_predictions.append({
                        "category": cat,
                        "confidence": round(float(probs[idx]), 4)
                    })
                
                results[name] = {
                    "prediction": category,
                    "confidence": round(float(confidence), 4),
                    "top_3": top_predictions,
                    "inference_ms": round(elapsed_ms, 2),
                    "model_type": slot.model_type,
                }
                
                # Update stats
                slot.inference_count += 1
                slot.avg_inference_ms = (
                    (slot.avg_inference_ms * (slot.inference_count - 1) + elapsed_ms)
                    / slot.inference_count
                )
                
            except Exception as e:
                results[name] = {"error": str(e)}

        self.total_inferences += 1
        return results

    def analyze(self, image_path: str, vision_engine=None) -> IntegratedResult:
        """
        Full integrated analysis: classical CV + all neural models.
        
        Args:
            image_path: Path to image
            vision_engine: VisionEngine instance (optional, for classical CV)
            
        Returns:
            IntegratedResult with classical, neural, and fused results
        """
        start = time.perf_counter()
        result = IntegratedResult()

        # 1. Classical CV analysis (always runs)
        if vision_engine:
            result.classical = vision_engine.analyze(image_path)
        
        # 2. Neural model predictions
        if self.slots:
            result.neural = self.predict(image_path=image_path)
            result.models_used = list(self.slots.keys())
        
        # 3. Fuse results
        result.fused = self._fuse_results(result.classical, result.neural)
        
        # 4. Overall confidence
        if result.neural:
            confidences = [
                v.get("confidence", 0) for v in result.neural.values()
                if isinstance(v, dict) and "confidence" in v
            ]
            result.confidence = max(confidences) if confidences else 0.0

        result.inference_time_ms = (time.perf_counter() - start) * 1000
        self.total_time_ms += result.inference_time_ms
        
        return result


    # ═══ RESULT FUSION ═══

    def _fuse_results(self, classical: Dict, neural: Dict) -> Dict:
        """
        Fuse classical CV and neural predictions into a unified result.
        
        Strategy:
          - Classical provides baseline (scene, colors, composition, etc.)
          - Neural adds learned categories with confidence scores
          - High-confidence neural predictions can override classical scene type
          - Low-confidence neural predictions are listed as "suggestions"
        """
        fused = {}
        
        # Start with classical results (always trustworthy)
        if classical:
            fused['scene'] = classical.get('scene', {})
            fused['colors'] = classical.get('colors', {})
            fused['composition'] = classical.get('composition', {})
            fused['quality'] = classical.get('quality', {})
            fused['description'] = classical.get('description', '')

        # Add neural predictions
        fused['learned_classifications'] = {}
        fused['suggestions'] = []
        
        for model_name, pred in neural.items():
            if not isinstance(pred, dict) or "error" in pred:
                continue
            
            confidence = pred.get("confidence", 0)
            prediction = pred.get("prediction", "")
            model_type = pred.get("model_type", "classifier")
            
            if confidence >= HIGH_CONFIDENCE_THRESHOLD:
                # High confidence: add as definitive classification
                fused['learned_classifications'][model_name] = {
                    'category': prediction,
                    'confidence': confidence,
                    'source': 'neural_high_confidence',
                }
                
                # Override classical scene if it's a scene classifier
                if model_type == "scene" and 'scene' in fused:
                    fused['scene']['neural_override'] = prediction
                    fused['scene']['neural_confidence'] = confidence
                    
            elif confidence >= MIN_CONFIDENCE_THRESHOLD:
                # Medium confidence: add as suggestion
                fused['suggestions'].append({
                    'model': model_name,
                    'category': prediction,
                    'confidence': confidence,
                    'top_alternatives': pred.get("top_3", []),
                })
            # Below MIN_CONFIDENCE_THRESHOLD: ignored (not reliable enough)

        # Generate enhanced description
        if fused.get('learned_classifications'):
            classifications = [
                f"{v['category']} ({v['confidence']:.0%})"
                for v in fused['learned_classifications'].values()
            ]
            fused['neural_summary'] = f"Identified as: {', '.join(classifications)}"

        return fused

    # ═══ BATCH INFERENCE ═══

    def predict_batch(self, image_paths: List[str], 
                      model_name: str = None) -> List[Dict]:
        """Run prediction on multiple images."""
        results = []
        for path in image_paths:
            results.append(self.predict(image_path=path, model_name=model_name))
        return results

    def classify_folder(self, folder_path: str, 
                        model_name: str = None) -> Dict[str, List[str]]:
        """
        Classify all images in a local folder.
        
        Returns:
            Dict mapping category -> list of filenames
        """
        from collections import defaultdict
        
        classified = defaultdict(list)
        image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif'}
        
        for f in os.listdir(folder_path):
            if Path(f).suffix.lower() in image_exts:
                path = os.path.join(folder_path, f)
                pred = self.predict(image_path=path, model_name=model_name)
                
                # Use first model's prediction
                for model, result in pred.items():
                    if isinstance(result, dict) and "prediction" in result:
                        classified[result["prediction"]].append(f)
                        break
        
        return dict(classified)


    # ═══ MODEL COMPARISON & BENCHMARKING ═══

    def benchmark(self, image_path: str, iterations: int = 100) -> Dict:
        """
        Benchmark inference speed for all loaded models.
        
        Returns:
            Dict with per-model timing stats
        """
        results = {}
        
        for name, slot in self.slots.items():
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                self.predict(image_path=image_path, model_name=name)
                times.append((time.perf_counter() - start) * 1000)
            
            results[name] = {
                'avg_ms': round(sum(times) / len(times), 3),
                'min_ms': round(min(times), 3),
                'max_ms': round(max(times), 3),
                'p95_ms': round(sorted(times)[int(len(times) * 0.95)], 3),
                'meets_target': sum(times) / len(times) < 5.0,  # <5ms target
            }
        
        return results

    def compare_models(self, image_path: str, 
                       model_a: str, model_b: str) -> Dict:
        """Compare predictions between two models on the same image."""
        pred_a = self.predict(image_path=image_path, model_name=model_a)
        pred_b = self.predict(image_path=image_path, model_name=model_b)
        
        return {
            'model_a': {
                'name': model_a,
                'result': pred_a.get(model_a, {}),
            },
            'model_b': {
                'name': model_b,
                'result': pred_b.get(model_b, {}),
            },
            'agree': (
                pred_a.get(model_a, {}).get('prediction') == 
                pred_b.get(model_b, {}).get('prediction')
            ),
        }

    # ═══ STATUS & DIAGNOSTICS ═══

    def get_status(self) -> Dict:
        """Get status of all loaded models."""
        return {
            'models_loaded': len(self.slots),
            'total_inferences': self.total_inferences,
            'avg_inference_ms': round(
                self.total_time_ms / max(self.total_inferences, 1), 2
            ),
            'models': {
                name: {
                    'type': slot.model_type,
                    'categories': len(slot.categories),
                    'input_size': slot.input_size,
                    'inferences': slot.inference_count,
                    'avg_ms': round(slot.avg_inference_ms, 2),
                    'version': slot.version,
                }
                for name, slot in self.slots.items()
            }
        }

    def get_model_info(self, name: str) -> Dict:
        """Get detailed info about a specific loaded model."""
        if name not in self.slots:
            return {"error": f"Model '{name}' not loaded"}
        
        slot = self.slots[name]
        model_path = os.path.join(self.models_dir, f"{name}.micv")
        
        return {
            'name': name,
            'type': slot.model_type,
            'categories': slot.categories,
            'num_categories': len(slot.categories),
            'input_size': slot.input_size,
            'config': slot.model.config_name,
            'file_size_kb': round(os.path.getsize(model_path) / 1024, 1) 
                           if os.path.exists(model_path) else 0,
            'inference_count': slot.inference_count,
            'avg_inference_ms': round(slot.avg_inference_ms, 2),
            'loaded_at': slot.loaded_at,
            'version': slot.version,
        }

    # ═══ HELPERS ═══

    def _infer_model_type(self, name: str) -> str:
        """Infer model type from its name."""
        name_lower = name.lower()
        if any(w in name_lower for w in ['scene', 'place', 'location', 'indoor', 'outdoor']):
            return "scene"
        elif any(w in name_lower for w in ['object', 'detect', 'thing', 'item']):
            return "detector"
        elif any(w in name_lower for w in ['style', 'art', 'genre', 'aesthetic']):
            return "style"
        elif any(w in name_lower for w in ['feature', 'embed', 'similar']):
            return "feature"
        return "classifier"


# ═══ CLI ═══

def main():
    """Command-line interface for model integrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vision Model Integrator")
    parser.add_argument("action", choices=["status", "predict", "benchmark", "analyze"],
                       help="Action to perform")
    parser.add_argument("--image", default=None, help="Image path")
    parser.add_argument("--model", default=None, help="Specific model name")
    
    args = parser.parse_args()
    
    integrator = ModelIntegrator()
    integrator.load_all_models()
    
    if args.action == "status":
        status = integrator.get_status()
        print(f"\n  Loaded models: {status['models_loaded']}")
        print(f"  Total inferences: {status['total_inferences']}")
        for name, info in status['models'].items():
            print(f"    {name:<20} type={info['type']:<12} "
                  f"categories={info['categories']}  avg={info['avg_ms']}ms")
        print()
    
    elif args.action == "predict":
        if not args.image:
            print("  --image required for predict action")
            return
        result = integrator.predict(image_path=args.image, model_name=args.model)
        print(json.dumps(result, indent=2))
    
    elif args.action == "benchmark":
        if not args.image:
            print("  --image required for benchmark action")
            return
        bench = integrator.benchmark(args.image)
        print("\n  Benchmark results (100 iterations):")
        for name, stats in bench.items():
            status = "PASS" if stats['meets_target'] else "SLOW"
            print(f"    {name:<20} avg={stats['avg_ms']:.2f}ms  "
                  f"p95={stats['p95_ms']:.2f}ms  [{status}]")
        print()
    
    elif args.action == "analyze":
        if not args.image:
            print("  --image required for analyze action")
            return
        
        # Try to import vision engine
        try:
            from vision import VisionEngine
            vision = VisionEngine()
        except ImportError:
            vision = None
        
        result = integrator.analyze(args.image, vision_engine=vision)
        print(f"\n  Inference time: {result.inference_time_ms:.2f}ms")
        print(f"  Models used: {result.models_used}")
        print(f"  Overall confidence: {result.confidence:.3f}")
        
        if result.fused.get('learned_classifications'):
            print(f"\n  Neural classifications:")
            for model, cls in result.fused['learned_classifications'].items():
                print(f"    {model}: {cls['category']} ({cls['confidence']:.1%})")
        
        if result.fused.get('suggestions'):
            print(f"\n  Suggestions (medium confidence):")
            for s in result.fused['suggestions']:
                print(f"    {s['model']}: {s['category']} ({s['confidence']:.1%})")
        print()


if __name__ == "__main__":
    main()
