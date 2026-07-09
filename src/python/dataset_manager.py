#!/usr/bin/env python3
"""
Image Dataset Manager — Indexes, categorizes, labels, and organizes images
from Google Drive into training-ready datasets for the vision micro-models.

Features:
  - Auto-categorize images by folder structure, filename patterns, or content
  - Manual labeling interface
  - Train/val/test split generation
  - Dataset versioning and metadata tracking
  - Augmentation-aware batch generation
  - Category statistics and balance reports
"""
import os
import io
import json
import time
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import Counter, defaultdict

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from cloud_storage import GoogleDriveConnector, DriveFile

# Also support Rclone connector
try:
    from cloud_storage import RcloneDriveConnector
except ImportError:
    RcloneDriveConnector = None


# ═══ Constants ═══
DATASETS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'datasets')
DATASET_INDEX_FILE = "dataset_index.json"
DEFAULT_TRAIN_SPLIT = 0.7
DEFAULT_VAL_SPLIT = 0.15
DEFAULT_TEST_SPLIT = 0.15
MIN_IMAGES_PER_CATEGORY = 10
SUPPORTED_SIZES = [(64, 64), (128, 128), (224, 224), (299, 299)]


@dataclass
class ImageRecord:
    """A single image record in a dataset."""
    file_id: str           # Google Drive file ID
    filename: str
    category: str          # Assigned category/label
    subcategory: str = ""
    split: str = ""        # train/val/test
    source_path: str = ""  # Original path on Drive
    size_bytes: int = 0
    width: int = 0
    height: int = 0
    hash_md5: str = ""
    tags: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    added_time: str = ""
    local_cache_path: str = ""


@dataclass
class DatasetMetadata:
    """Metadata for a training dataset."""
    name: str
    description: str = ""
    version: str = "1.0.0"
    created: str = ""
    modified: str = ""
    total_images: int = 0
    categories: Dict[str, int] = field(default_factory=dict)
    splits: Dict[str, int] = field(default_factory=dict)
    target_size: Tuple[int, int] = (224, 224)
    source_folders: List[str] = field(default_factory=list)
    auto_categorized: bool = False



class DatasetManager:
    """
    Manages image datasets for vision training.
    
    Workflow:
        1. Connect to Google Drive via cloud_storage connector
        2. Index images (auto-categorize by folder or manual labels)
        3. Generate train/val/test splits
        4. Stream batches for training
    
    Usage:
        dm = DatasetManager()
        dm.create_dataset("animals", description="Animal classification")
        dm.auto_categorize_from_drive(connector, folder_id="abc123")
        dm.generate_splits()
        
        for batch in dm.get_training_batches("animals", batch_size=32):
            train(batch)
    """

    def __init__(self, datasets_dir: str = None):
        self.datasets_dir = datasets_dir or DATASETS_DIR
        os.makedirs(self.datasets_dir, exist_ok=True)
        self.datasets: Dict[str, DatasetMetadata] = {}
        self.records: Dict[str, List[ImageRecord]] = {}  # dataset_name -> records
        self._load_all_datasets()

    # ═══ DATASET CREATION & MANAGEMENT ═══

    def create_dataset(self, name: str, description: str = "",
                       target_size: Tuple[int, int] = (224, 224)) -> DatasetMetadata:
        """Create a new training dataset."""
        if name in self.datasets:
            print(f"  [INFO] Dataset '{name}' already exists. Returning existing.")
            return self.datasets[name]

        metadata = DatasetMetadata(
            name=name,
            description=description,
            created=datetime.now().isoformat(),
            modified=datetime.now().isoformat(),
            target_size=target_size,
        )
        
        self.datasets[name] = metadata
        self.records[name] = []
        
        # Create directory structure
        dataset_dir = os.path.join(self.datasets_dir, name)
        os.makedirs(dataset_dir, exist_ok=True)
        os.makedirs(os.path.join(dataset_dir, "train"), exist_ok=True)
        os.makedirs(os.path.join(dataset_dir, "val"), exist_ok=True)
        os.makedirs(os.path.join(dataset_dir, "test"), exist_ok=True)
        
        self._save_dataset(name)
        print(f"  [OK] Dataset '{name}' created at {dataset_dir}")
        return metadata


    def delete_dataset(self, name: str):
        """Delete a dataset and all its records."""
        if name not in self.datasets:
            print(f"  [WARN] Dataset '{name}' not found.")
            return
        
        import shutil
        dataset_dir = os.path.join(self.datasets_dir, name)
        if os.path.exists(dataset_dir):
            shutil.rmtree(dataset_dir)
        
        del self.datasets[name]
        if name in self.records:
            del self.records[name]
        
        print(f"  [OK] Dataset '{name}' deleted.")

    def list_datasets(self) -> List[Dict]:
        """List all datasets with summary info."""
        result = []
        for name, meta in self.datasets.items():
            result.append({
                'name': name,
                'description': meta.description,
                'total_images': meta.total_images,
                'categories': len(meta.categories),
                'version': meta.version,
                'modified': meta.modified,
            })
        return result

    # ═══ AUTO-CATEGORIZATION (from Drive folder structure) ═══

    def auto_categorize_from_drive(self, connector,
                                    dataset_name: str,
                                    folder_id: str = "root",
                                    folder_path: str = "",
                                    use_folder_as_category: bool = True,
                                    max_images: int = 50000) -> int:
        """
        Auto-categorize images from Google Drive based on folder structure.
        
        Each subfolder becomes a category. Images in root get category "uncategorized".
        
        Args:
            connector: Authenticated GoogleDriveConnector or RcloneDriveConnector
            dataset_name: Target dataset to populate
            folder_id: Root folder ID to scan (Google API connector)
            folder_path: Root folder path to scan (Rclone connector)
            use_folder_as_category: Use parent folder name as category
            max_images: Maximum images to index
            
        Returns:
            Number of images added
        """
        if dataset_name not in self.datasets:
            self.create_dataset(dataset_name)

        print(f"  [..] Scanning Drive folder for images...")
        
        # Support both connector types
        if hasattr(connector, 'list_images'):
            if folder_path:
                images = connector.list_images(folder_path=folder_path, max_results=max_images)
            else:
                images = connector.list_images(folder_id=folder_id, max_results=max_images)
        else:
            images = connector.list_images(folder_id=folder_id, max_results=max_images)
        
        print(f"  [OK] Found {len(images)} images")

        added = 0
        for drive_file in images:
            # Determine category from folder path
            if use_folder_as_category and drive_file.folder_path:
                # Use the immediate parent folder as category
                parts = drive_file.folder_path.strip('/').split('/')
                category = parts[-1] if parts else "uncategorized"
            else:
                category = self._guess_category_from_filename(drive_file.name)

            # Clean category name
            category = self._clean_category_name(category)

            record = ImageRecord(
                file_id=drive_file.id,
                filename=drive_file.name,
                category=category,
                source_path=drive_file.folder_path,
                size_bytes=drive_file.size,
                hash_md5=drive_file.md5_checksum,
                added_time=datetime.now().isoformat(),
            )
            
            self.records[dataset_name].append(record)
            added += 1

        # Update metadata
        self._update_metadata(dataset_name)
        self._save_dataset(dataset_name)
        
        print(f"  [OK] Added {added} images to dataset '{dataset_name}'")
        print(f"       Categories: {dict(self.datasets[dataset_name].categories)}")
        return added


    def add_labeled_images(self, dataset_name: str, 
                           files: List[DriveFile],
                           category: str,
                           tags: List[str] = None) -> int:
        """Manually add images with a specific category label."""
        if dataset_name not in self.datasets:
            self.create_dataset(dataset_name)

        category = self._clean_category_name(category)
        added = 0
        
        for drive_file in files:
            record = ImageRecord(
                file_id=drive_file.id,
                filename=drive_file.name,
                category=category,
                source_path=drive_file.folder_path,
                size_bytes=drive_file.size,
                hash_md5=drive_file.md5_checksum,
                tags=tags or [],
                added_time=datetime.now().isoformat(),
            )
            self.records[dataset_name].append(record)
            added += 1

        self._update_metadata(dataset_name)
        self._save_dataset(dataset_name)
        return added

    def relabel(self, dataset_name: str, file_ids: List[str], 
                new_category: str) -> int:
        """Relabel specific images to a different category."""
        if dataset_name not in self.records:
            return 0
        
        new_category = self._clean_category_name(new_category)
        changed = 0
        
        for record in self.records[dataset_name]:
            if record.file_id in file_ids:
                record.category = new_category
                changed += 1

        if changed:
            self._update_metadata(dataset_name)
            self._save_dataset(dataset_name)
        
        return changed

    # ═══ TRAIN/VAL/TEST SPLITS ═══

    def generate_splits(self, dataset_name: str,
                        train_ratio: float = DEFAULT_TRAIN_SPLIT,
                        val_ratio: float = DEFAULT_VAL_SPLIT,
                        test_ratio: float = DEFAULT_TEST_SPLIT,
                        stratified: bool = True,
                        seed: int = 42) -> Dict[str, int]:
        """
        Generate train/val/test splits for a dataset.
        
        Args:
            dataset_name: Dataset to split
            train_ratio: Fraction for training (default 0.7)
            val_ratio: Fraction for validation (default 0.15)
            test_ratio: Fraction for testing (default 0.15)
            stratified: Maintain category proportions in each split
            seed: Random seed for reproducibility
            
        Returns:
            Dict with split counts: {"train": N, "val": N, "test": N}
        """
        if dataset_name not in self.records:
            raise ValueError(f"Dataset '{dataset_name}' not found")

        records = self.records[dataset_name]
        if not records:
            return {"train": 0, "val": 0, "test": 0}

        rng = random.Random(seed)
        
        if stratified:
            # Split each category independently to maintain proportions
            by_category = defaultdict(list)
            for r in records:
                by_category[r.category].append(r)
            
            for category, cat_records in by_category.items():
                rng.shuffle(cat_records)
                n = len(cat_records)
                n_train = int(n * train_ratio)
                n_val = int(n * val_ratio)
                
                for i, r in enumerate(cat_records):
                    if i < n_train:
                        r.split = "train"
                    elif i < n_train + n_val:
                        r.split = "val"
                    else:
                        r.split = "test"
        else:
            rng.shuffle(records)
            n = len(records)
            n_train = int(n * train_ratio)
            n_val = int(n * val_ratio)
            
            for i, r in enumerate(records):
                if i < n_train:
                    r.split = "train"
                elif i < n_train + n_val:
                    r.split = "val"
                else:
                    r.split = "test"

        splits = Counter(r.split for r in records)
        self.datasets[dataset_name].splits = dict(splits)
        self._save_dataset(dataset_name)
        
        print(f"  [OK] Splits for '{dataset_name}': train={splits['train']}, "
              f"val={splits['val']}, test={splits['test']}")
        return dict(splits)


    # ═══ BATCH GENERATION (for training loop) ═══

    def get_training_batches(self, dataset_name: str,
                              connector: GoogleDriveConnector,
                              split: str = "train",
                              batch_size: int = 32,
                              target_size: Tuple[int, int] = None,
                              shuffle: bool = True,
                              augment: bool = False) -> "Generator":
        """
        Generate training batches by streaming from Drive.
        
        Yields:
            List of (image_bytes, category, record) tuples per batch
        """
        if dataset_name not in self.records:
            raise ValueError(f"Dataset '{dataset_name}' not found")

        records = [r for r in self.records[dataset_name] if r.split == split]
        if not records:
            print(f"  [WARN] No records in split '{split}'. Run generate_splits() first.")
            return

        if shuffle:
            random.shuffle(records)

        target = target_size or self.datasets[dataset_name].target_size
        batch = []

        for record in records:
            try:
                # Try local cache first
                if record.local_cache_path and os.path.exists(record.local_cache_path):
                    with open(record.local_cache_path, 'rb') as f:
                        img_bytes = f.read()
                else:
                    # Stream from Drive
                    img_bytes = connector._download_file_bytes(record.file_id)
                
                if img_bytes:
                    # Resize if PIL available
                    if PIL_AVAILABLE and target:
                        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
                        img = img.resize(target, Image.LANCZOS)
                        buf = io.BytesIO()
                        img.save(buf, format='JPEG', quality=90)
                        img_bytes = buf.getvalue()
                    
                    batch.append((img_bytes, record.category, record))
                    
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []

            except Exception as e:
                continue  # Skip failed images

        # Yield remaining
        if batch:
            yield batch

    def get_category_images(self, dataset_name: str, category: str,
                            split: str = None, limit: int = 100) -> List[ImageRecord]:
        """Get all records for a specific category."""
        if dataset_name not in self.records:
            return []
        
        results = []
        for r in self.records[dataset_name]:
            if r.category == category:
                if split is None or r.split == split:
                    results.append(r)
                    if len(results) >= limit:
                        break
        return results

    # ═══ DATASET STATISTICS & REPORTS ═══

    def get_stats(self, dataset_name: str) -> Dict:
        """Get comprehensive statistics for a dataset."""
        if dataset_name not in self.records:
            return {"error": f"Dataset '{dataset_name}' not found"}

        records = self.records[dataset_name]
        if not records:
            return {"total": 0, "categories": {}}

        categories = Counter(r.category for r in records)
        splits = Counter(r.split for r in records if r.split)
        total_size = sum(r.size_bytes for r in records)
        
        # Category balance analysis
        cat_counts = list(categories.values())
        avg_per_cat = sum(cat_counts) / len(cat_counts) if cat_counts else 0
        min_cat = min(cat_counts) if cat_counts else 0
        max_cat = max(cat_counts) if cat_counts else 0
        imbalance_ratio = max_cat / max(min_cat, 1)

        return {
            'total_images': len(records),
            'total_size_gb': round(total_size / (1024**3), 3),
            'num_categories': len(categories),
            'categories': dict(categories.most_common()),
            'splits': dict(splits),
            'avg_per_category': round(avg_per_cat, 1),
            'min_category_count': min_cat,
            'max_category_count': max_cat,
            'imbalance_ratio': round(imbalance_ratio, 2),
            'small_categories': [c for c, n in categories.items() 
                                if n < MIN_IMAGES_PER_CATEGORY],
            'balance_status': "balanced" if imbalance_ratio < 3 
                            else "moderate imbalance" if imbalance_ratio < 10
                            else "severe imbalance",
        }


    def get_balance_report(self, dataset_name: str) -> str:
        """Generate a human-readable balance report."""
        stats = self.get_stats(dataset_name)
        if "error" in stats:
            return stats["error"]

        lines = [
            f"\n  === Dataset: {dataset_name} ===",
            f"  Total images: {stats['total_images']}",
            f"  Categories: {stats['num_categories']}",
            f"  Total size: {stats['total_size_gb']} GB",
            f"  Balance: {stats['balance_status']} (ratio: {stats['imbalance_ratio']}x)",
            f"",
            f"  Category Distribution:",
        ]
        
        for cat, count in stats['categories'].items():
            bar_len = int(count / max(stats['max_category_count'], 1) * 30)
            bar = "#" * bar_len
            lines.append(f"    {cat:<20} {count:>5}  {bar}")
        
        if stats['small_categories']:
            lines.append(f"\n  WARNING: Categories with <{MIN_IMAGES_PER_CATEGORY} images:")
            for cat in stats['small_categories']:
                lines.append(f"    - {cat} ({stats['categories'][cat]} images)")
            lines.append("    Consider adding more images or merging with similar categories.")
        
        if stats['splits']:
            lines.append(f"\n  Splits: {stats['splits']}")
        
        return "\n".join(lines)

    # ═══ CATEGORY MANAGEMENT ═══

    def get_categories(self, dataset_name: str) -> List[str]:
        """Get list of all categories in a dataset."""
        if dataset_name not in self.records:
            return []
        return list(set(r.category for r in self.records[dataset_name]))

    def merge_categories(self, dataset_name: str, 
                         source_categories: List[str],
                         target_category: str) -> int:
        """Merge multiple categories into one."""
        if dataset_name not in self.records:
            return 0
        
        target_category = self._clean_category_name(target_category)
        merged = 0
        
        for record in self.records[dataset_name]:
            if record.category in source_categories:
                record.category = target_category
                merged += 1
        
        if merged:
            self._update_metadata(dataset_name)
            self._save_dataset(dataset_name)
            print(f"  [OK] Merged {merged} images into '{target_category}'")
        
        return merged

    def remove_category(self, dataset_name: str, category: str) -> int:
        """Remove all images in a category from the dataset."""
        if dataset_name not in self.records:
            return 0
        
        before = len(self.records[dataset_name])
        self.records[dataset_name] = [
            r for r in self.records[dataset_name] if r.category != category
        ]
        removed = before - len(self.records[dataset_name])
        
        if removed:
            self._update_metadata(dataset_name)
            self._save_dataset(dataset_name)
            print(f"  [OK] Removed {removed} images from category '{category}'")
        
        return removed

    # ═══ HELPER METHODS ═══

    def _guess_category_from_filename(self, filename: str) -> str:
        """Try to guess category from filename patterns."""
        name = Path(filename).stem.lower()
        
        # Common patterns: "category_001.jpg", "category-name-002.png"
        # Strip trailing numbers and separators
        import re
        clean = re.sub(r'[-_]?\d+$', '', name)
        clean = re.sub(r'[-_]+', ' ', clean).strip()
        
        if clean:
            return clean
        return "uncategorized"

    def _clean_category_name(self, name: str) -> str:
        """Normalize category name."""
        import re
        clean = name.strip().lower()
        clean = re.sub(r'[^\w\s-]', '', clean)
        clean = re.sub(r'[\s-]+', '_', clean)
        return clean[:50]  # Max 50 chars

    def _update_metadata(self, dataset_name: str):
        """Update dataset metadata from current records."""
        records = self.records.get(dataset_name, [])
        meta = self.datasets[dataset_name]
        
        meta.total_images = len(records)
        meta.categories = dict(Counter(r.category for r in records))
        meta.splits = dict(Counter(r.split for r in records if r.split))
        meta.modified = datetime.now().isoformat()


    # ═══ PERSISTENCE ═══

    def _save_dataset(self, name: str):
        """Save dataset metadata and records to disk."""
        dataset_dir = os.path.join(self.datasets_dir, name)
        os.makedirs(dataset_dir, exist_ok=True)
        
        # Save metadata
        meta_path = os.path.join(dataset_dir, "metadata.json")
        meta_dict = asdict(self.datasets[name])
        with open(meta_path, 'w') as f:
            json.dump(meta_dict, f, indent=2)
        
        # Save records
        records_path = os.path.join(dataset_dir, "records.json")
        records_list = [asdict(r) for r in self.records.get(name, [])]
        with open(records_path, 'w') as f:
            json.dump(records_list, f, indent=2)

    def _load_all_datasets(self):
        """Load all datasets from disk."""
        if not os.path.exists(self.datasets_dir):
            return

        for entry in os.listdir(self.datasets_dir):
            dataset_dir = os.path.join(self.datasets_dir, entry)
            if not os.path.isdir(dataset_dir):
                continue
            
            meta_path = os.path.join(dataset_dir, "metadata.json")
            records_path = os.path.join(dataset_dir, "records.json")
            
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r') as f:
                        meta_dict = json.load(f)
                    # Handle tuple conversion for target_size
                    if 'target_size' in meta_dict and isinstance(meta_dict['target_size'], list):
                        meta_dict['target_size'] = tuple(meta_dict['target_size'])
                    self.datasets[entry] = DatasetMetadata(**meta_dict)
                except Exception as e:
                    print(f"  [WARN] Failed to load dataset '{entry}': {e}")
                    continue

            if os.path.exists(records_path):
                try:
                    with open(records_path, 'r') as f:
                        records_list = json.load(f)
                    self.records[entry] = [ImageRecord(**r) for r in records_list]
                except Exception:
                    self.records[entry] = []

    # ═══ EXPORT & IMPORT ═══

    def export_manifest(self, dataset_name: str, output_path: str = None) -> str:
        """
        Export dataset as a manifest file (for external tools).
        Format: category,file_id,filename,split
        """
        if dataset_name not in self.records:
            raise ValueError(f"Dataset '{dataset_name}' not found")

        if output_path is None:
            output_path = os.path.join(self.datasets_dir, dataset_name, "manifest.csv")

        with open(output_path, 'w') as f:
            f.write("category,file_id,filename,split,size_bytes\n")
            for r in self.records[dataset_name]:
                f.write(f"{r.category},{r.file_id},{r.filename},{r.split},{r.size_bytes}\n")

        print(f"  [OK] Manifest exported to {output_path}")
        return output_path

    def import_labels(self, dataset_name: str, labels_file: str) -> int:
        """
        Import labels from a CSV file.
        Format: file_id,category (or filename,category)
        """
        if dataset_name not in self.records:
            raise ValueError(f"Dataset '{dataset_name}' not found")

        labels = {}
        with open(labels_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('file'):
                    continue
                parts = line.split(',')
                if len(parts) >= 2:
                    labels[parts[0].strip()] = parts[1].strip()

        updated = 0
        for record in self.records[dataset_name]:
            if record.file_id in labels:
                record.category = self._clean_category_name(labels[record.file_id])
                updated += 1
            elif record.filename in labels:
                record.category = self._clean_category_name(labels[record.filename])
                updated += 1

        if updated:
            self._update_metadata(dataset_name)
            self._save_dataset(dataset_name)
        
        print(f"  [OK] Updated {updated} labels from {labels_file}")
        return updated


# ═══ CLI INTERFACE ═══

def main():
    """Command-line interface for dataset management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Image Dataset Manager")
    parser.add_argument("action", choices=["create", "list", "stats", "split", "report", "export"],
                       help="Action to perform")
    parser.add_argument("--name", default="default", help="Dataset name")
    parser.add_argument("--description", default="", help="Dataset description")
    parser.add_argument("--folder", default="root", help="Drive folder ID")
    
    args = parser.parse_args()
    dm = DatasetManager()
    
    if args.action == "create":
        dm.create_dataset(args.name, description=args.description)
    
    elif args.action == "list":
        datasets = dm.list_datasets()
        if not datasets:
            print("  No datasets found. Create one with: --action create --name <name>")
        else:
            print("\n  Datasets:")
            for d in datasets:
                print(f"    {d['name']:<20} {d['total_images']:>6} images, "
                      f"{d['categories']} categories  (v{d['version']})")
    
    elif args.action == "stats":
        stats = dm.get_stats(args.name)
        print(json.dumps(stats, indent=2))
    
    elif args.action == "report":
        print(dm.get_balance_report(args.name))
    
    elif args.action == "split":
        dm.generate_splits(args.name)
    
    elif args.action == "export":
        dm.export_manifest(args.name)


if __name__ == "__main__":
    main()
