# Installation Guide

## Option 1: Conda (Recommended)

### Prerequisites
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/) installed

### Steps

```bash
# 1. Navigate to project
cd paper-trend-tracking

# 2. Create conda environment
conda env create -f environment.yml

# 3. Activate environment
conda activate paper-trends

# 4. Download spaCy model
python -m spacy download en_core_web_sm

# 5. Verify installation
python test_keyword_extraction.py
```

### Update Environment

```bash
conda env update -f environment.yml --prune
```

### Remove Environment

```bash
conda env remove -n paper-trends
```

---

## Option 2: Pip + Virtual Environment

### Prerequisites
- Python 3.10+ installed
- pip installed

### Steps

```bash
# 1. Navigate to project
cd paper-trend-tracking

# 2. Create virtual environment
python -m venv venv

# 3. Activate environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Download spaCy model
python -m spacy download en_core_web_sm

# 6. Verify installation
python test_keyword_extraction.py
```

---

## Option 3: Pip (System-wide, Not Recommended)

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

⚠️ **Warning:** This installs packages system-wide. Use a virtual environment instead.

---

## Verify Installation

Run the test script:

```bash
python test_keyword_extraction.py
```

Expected output:
```
🧪 Keyword Extraction Tests

============================================================
Testing YAKE Extractor
============================================================

Extracted 10 keywords:

   1. Machine learning approaches                (score: 0.9234)
   2. drug discovery                             (score: 0.8912)
   ...

✅ All tests complete!
```

---

## Troubleshooting

### "Command 'conda' not found"

Install Miniconda:
```bash
# Download and install
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
# Restart terminal
```

### "Package not found" errors

```bash
# Update conda
conda update -n base -c defaults conda

# Try creating environment again
conda env create -f environment.yml --force
```

### "spaCy model not found"

```bash
python -m spacy download en_core_web_sm
```

### "YAKE not installed"

```bash
conda activate paper-trends
pip install yake
```

### Dependency conflicts

```bash
# Create fresh environment
conda env remove -n paper-trends
conda env create -f environment.yml
```

---

## Optional Dependencies

### For LLM-based keyword extraction

```bash
conda activate paper-trends
pip install openai anthropic
```

### For advanced graph analysis

```bash
conda activate paper-trends
conda install python-igraph leidenalg
```

### For development

```bash
conda activate paper-trends
pip install pytest black mypy pylint
```

---

## Check Installation

```bash
conda activate paper-trends
python -c "
import yake
import networkx as nx
import plotly
import sqlalchemy
import spacy
print('✅ All packages installed successfully!')
print(f'  - YAKE: {yake.__version__}')
print(f'  - NetworkX: {nx.__version__}')
print(f'  - Plotly: {plotly.__version__}')
print(f'  - SQLAlchemy: {sqlalchemy.__version__}')
print(f'  - spaCy: {spacy.__version__}')
"
```
