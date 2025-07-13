# Repository Structure

## Clean and Organized Layout

```
cmovies/
├── README.md                    # Main project documentation
├── run.py                       # Simple entry point script
├── example_usage.py             # Usage examples and demos
├── pyproject.toml              # Project configuration
├── uv.lock                     # Dependency lock file
├── .python-version             # Python version specification
├── .gitignore                  # Git ignore rules
│
├── cmovies/                    # Main package directory
│   ├── __init__.py             # Package initialization and exports
│   ├── cli.py                  # Command-line interface
│   ├── movie_search.py         # IMDb movie search functionality
│   ├── url_extractor.py        # M3U8 URL extraction logic
│   ├── utils.py                # Utility functions and validation
│   └── config.py               # Configuration constants
│
└── docs/                       # Documentation directory
    ├── USAGE.md                # Detailed usage guide
    ├── TROUBLESHOOTING.md      # Common issues and solutions
    └── IMPROVEMENTS_SUMMARY.md # Development history and improvements
```

## Key Improvements Made

### 1. **Package Structure**
- ✅ Moved all core code into `cmovies/` package
- ✅ Fixed all relative imports (`.utils`, `.config`, etc.)
- ✅ Created proper `__init__.py` with exports
- ✅ Updated `pyproject.toml` entry point

### 2. **Removed Legacy Files**
- ❌ `main.py` (replaced by `cmovies/cli.py`)
- ❌ `movie.py` (replaced by `cmovies/movie_search.py`)
- ❌ Debug and temporary files

### 3. **Clean Entry Points**
- ✅ `run.py` - Simple script to run CLI
- ✅ `python -m cmovies.cli` - Module execution
- ✅ `cmovies` command (after installation)

### 4. **Organized Documentation**
- ✅ Moved all docs to `docs/` directory
- ✅ Updated README.md with quick start
- ✅ Separated detailed guides

## Usage After Organization

### Development Mode
```bash
# Install dependencies
uv sync
playwright install chromium

# Run directly
python run.py --search
python run.py --imdb-id tt0133093

# Run as module
python -m cmovies.cli --search
```

### Package Installation
```bash
# Install as package
pip install -e .

# Use installed command
cmovies --search
cmovies --imdb-id tt0133093
```

### Import as Library
```python
from cmovies import MovieSearcher, extract_m3u8_url
from cmovies.utils import validate_imdb_id
```

## Benefits of New Structure

1. **Professional Layout**: Standard Python package structure
2. **Clear Separation**: Core code, docs, and examples separated
3. **Easy Installation**: Proper package configuration
4. **Import Flexibility**: Can be used as library or CLI
5. **Maintainable**: Logical organization for future development
6. **Clean Git History**: Removed temporary and legacy files