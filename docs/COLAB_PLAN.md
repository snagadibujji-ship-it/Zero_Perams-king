# AXIMA Colab Plan — 50 Million Facts
## Google Colab Training for Massive Knowledge Expansion

---

## Goal
Expand AXIMA's knowledge from **4,700 facts → 50,000,000 facts** using Google Colab's free GPU/RAM.

## Current State
- 4,700 facts in `user_data/knowledge.json`
- Each fact: `{"subject": "...", "predicate": "...", "object": "..."}`
- Compressed with 27-character codes
- Causal reasoning: 600 materials

---

## Data Sources (Total: 50M+ facts)

### 1. Wikidata Triples (30M facts)
- **Source**: `dumps.wikimedia.org/wikidatawiki/entities/latest-truthy.nt.gz`
- **Size**: ~22 GB compressed, ~120M entities, ~700M triples
- **Format**: N-Triples (subject predicate object)
- **What we extract**: 
  - All "instance of" relations (X is a Y)
  - All "subclass of" (taxonomy)
  - Geographic facts (capital, population, area, location)
  - Scientific facts (chemical elements, species, physics constants)
  - Historical facts (birth/death dates, inventions, events)
  - Cultural facts (artists, works, awards)
- **Filter**: English labels only, skip administrative/bot edits
- **Target**: 30M high-quality triples

### 2. DBpedia (10M facts)
- **Source**: `downloads.dbpedia.org/wiki/dbpedia_en/latest/`
- **Format**: N-Triples extracted from Wikipedia infoboxes
- **Key files**:
  - `mappingbased-objects_lang=en.ttl.bz2` (structured relations)
  - `infobox-properties_lang=en.ttl.bz2` (all infobox data)
  - `instance-types_lang=en.ttl.bz2` (type hierarchy)
- **Target**: 10M facts about people, places, organizations, events

### 3. ConceptNet (5M facts)
- **Source**: `https://s3.amazonaws.com/conceptnet/downloads/2019/edges/conceptnet-assertions-5.7.0.csv.gz`
- **Format**: CSV with (relation, head, tail, weight)
- **What we use**:
  - IsA, HasProperty, CapableOf, UsedFor, AtLocation
  - Causes, HasPrerequisite, MotivatedByGoal
  - RelatedTo, PartOf, MadeOf
- **Target**: 5M commonsense relations

### 4. Wikipedia Summaries (3M facts)
- **Source**: `huggingface.co/datasets/wikipedia` (English, latest)
- **Processing**: Extract first paragraph → subject-predicate-object extraction
- **NLP**: Simple pattern matching (X is Y, X was born in Y, X invented Y)
- **Target**: 3M factual claims from first paragraphs

### 5. Scientific Data (2M facts)
- **Source**: PubChem (chemistry), UniProt (biology), NASA (astronomy)
- **What**: 
  - Chemical compounds: formula, molecular weight, properties (PubChem: 100M+ compounds)
  - Protein functions, gene associations
  - Astronomical objects: coordinates, magnitudes, distances
  - Physics: all SI units, conversions, element properties
- **Target**: 2M scientific facts

---

## Processing Pipeline (Colab Notebook)

```python
# STEP 1: Download and stream (don't load all in memory)
# Use streaming decompression + line-by-line processing

import gzip, json, os
from google.colab import drive
drive.mount('/content/drive')  # Save results to Drive

OUTPUT_DIR = '/content/drive/MyDrive/AXIMA_50M/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# STEP 2: Process Wikidata (streaming)
def process_wikidata():
    """Stream wikidata dump, extract English triples."""
    import urllib.request
    url = "https://dumps.wikimedia.org/wikidatawiki/entities/latest-truthy.nt.gz"
    # Download in chunks, process each entity
    facts = []
    batch_num = 0
    
    with gzip.open('wikidata.nt.gz', 'rt') as f:
        for line in f:
            # Parse N-triple: <subject> <predicate> <object> .
            parts = line.strip().split(' ', 3)
            if len(parts) >= 3:
                subj = extract_label(parts[0])
                pred = extract_predicate(parts[1])
                obj = extract_label(parts[2])
                if subj and pred and obj and is_english(obj):
                    facts.append({"s": subj, "p": pred, "o": obj})
            
            if len(facts) >= 100000:  # Save every 100K
                save_batch(facts, batch_num, OUTPUT_DIR)
                batch_num += 1
                facts = []

# STEP 3: Compress into AXIMA format
def compress_to_axima(facts):
    """Convert raw facts to AXIMA's compressed 27-char code format."""
    # Subject → 9-char hash
    # Predicate → 3-char code (lookup table)
    # Object → 15-char compressed
    PRED_CODES = {
        "instance_of": "IOF", "subclass_of": "SCO", "capital": "CAP",
        "country": "CTR", "born_in": "BRN", "died_in": "DID",
        "population": "POP", "area": "ARE", "located_in": "LOC",
        "part_of": "PRT", "has_property": "HPR", "used_for": "USE",
        "capable_of": "CAN", "causes": "CSE", "made_of": "MAD",
        "invented_by": "INV", "discovered": "DIS", "written_by": "WRT",
        "founded": "FND", "is_a": "ISA", "has_color": "CLR",
        "weighs": "WGH", "temperature": "TMP", "formula": "FML",
    }
    # ... compression logic ...

# STEP 4: Build optimized index
def build_index(output_dir):
    """Create inverted index for fast lookup."""
    # word → list of fact IDs
    # This is what AXIMA uses at runtime
    index = {}
    for batch_file in sorted(os.listdir(output_dir)):
        if batch_file.startswith('facts_'):
            with open(f'{output_dir}/{batch_file}') as f:
                facts = json.load(f)
                for i, fact in enumerate(facts):
                    for word in tokenize(fact['s'] + ' ' + fact['o']):
                        if word not in index:
                            index[word] = []
                        index[word].append(f"{batch_file}:{i}")
    
    # Save compressed index
    with open(f'{output_dir}/index.json', 'w') as f:
        json.dump(index, f)
```

---

## Colab Resource Usage

| Step | Time (est.) | RAM | Disk |
|------|-------------|-----|------|
| Download Wikidata dump | 30 min | 2 GB | 22 GB |
| Stream + extract English | 4 hours | 8 GB | 15 GB |
| Download DBpedia | 10 min | 2 GB | 5 GB |
| Process DBpedia | 1 hour | 4 GB | 3 GB |
| Download ConceptNet | 2 min | 1 GB | 1 GB |
| Process ConceptNet | 20 min | 3 GB | 1 GB |
| Wikipedia extraction | 2 hours | 6 GB | 4 GB |
| Compression + indexing | 2 hours | 12 GB | 8 GB |
| **TOTAL** | **~10 hours** | **12 GB peak** | **~60 GB** |

**Fits in Colab Pro ($10/month) or split across multiple free sessions.**

---

## Compression Strategy

### Current Compressor
- 27-character codes per fact
- 4,700 facts × 27 = ~127 KB total
- Fast lookup via in-memory hash

### Upgraded Compressor for 50M
- **Trie-based prefix compression**: common subjects share prefix → 40% smaller
- **Predicate codebook**: 100 most common predicates → 2-byte codes
- **Object quantization**: numbers → range buckets, strings → dictionary codes
- **Sharded storage**: 50M facts in 500 shards of 100K each
- **Memory-mapped files**: Only load relevant shards at runtime
- **Bloom filter index**: O(1) "does this entity exist?" check before disk lookup

### Target Sizes
| Facts | Uncompressed | Compressed | In-memory index |
|-------|-------------|-----------|----------------|
| 4,700 | 200 KB | 127 KB | 50 KB |
| 50M | ~10 GB | ~2 GB | 200 MB |

**Phone deployment**: Use top-1M most-asked facts in-memory (30 MB), rest on SD card with memory-mapped access.

---

## What 50M Facts Enables

### Knowledge Coverage
- Every country, city, person, event in Wikipedia
- Chemical elements + 100K compounds with properties
- All Nobel prizes, inventions, discoveries
- Full taxonomy (what is a X? → all "instance of" chains)
- Commonsense (fire is hot, ice is cold, dogs have legs)
- Scientific facts (speed of light, boiling points, distances)

### Expected Accuracy Improvement
| Category | Current (4.7K) | With 50M |
|----------|---------------|---------|
| Factual (who/what/where) | 65% | **95%+** |
| Scientific | 70% | **92%** |
| Commonsense | 60% | **90%** |
| Reasoning chains | 50% | **85%** |
| Overall | 84% | **93%+** |

---

## Colab Notebook Structure

```
AXIMA_50M_Training.ipynb:
├── Cell 1: Setup (install deps, mount Drive)
├── Cell 2: Download sources (wget + progress bar)
├── Cell 3: Process Wikidata (streaming, ~4 hours)
├── Cell 4: Process DBpedia (~1 hour)
├── Cell 5: Process ConceptNet (~20 min)
├── Cell 6: Extract Wikipedia summaries (~2 hours)
├── Cell 7: Merge + deduplicate
├── Cell 8: Compress to AXIMA format
├── Cell 9: Build inverted index
├── Cell 10: Verify (sample 1000, check quality)
├── Cell 11: Package for deployment
└── Cell 12: Upload to GitHub release / Drive
```

---

## Deployment After Training

```bash
# Download from Drive/GitHub Release
wget https://github.com/snagadibujji-ship-it/Zero_Perams-king/releases/download/v3.2/facts_50M.tar.gz
tar xzf facts_50M.tar.gz -C user_data/

# AXIMA auto-detects expanded knowledge
python3 src/python/hybrid_ai.py
# → "Loaded 50,000,000 facts from 500 shards"
```

---

## Alternative: Incremental Approach

If 50M is too much for one session:

1. **Session 1**: Wikidata core (10M facts) — most important
2. **Session 2**: DBpedia + ConceptNet (15M)
3. **Session 3**: Wikipedia + Scientific (25M)
4. **Session 4**: Full merge + index (50M)

Each session saves to Google Drive. Next session picks up where you left off.

---

## Files to Create

- `scripts/colab_50m_training.py` — Main Colab processing script
- `src/python/compressor_v2.py` — Upgraded compressor for 50M scale
- `src/python/shard_loader.py` — Memory-mapped shard reader

---

*Target: 50M facts → 93%+ accuracy on all factual questions.*
*Time: ~10 hours on Colab Pro. Cost: $10 one-time.*
