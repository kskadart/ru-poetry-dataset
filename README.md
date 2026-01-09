# ru-poetry-dataset

Russian poetry dataset (31k poems) with merge/validation scripts.

## Dataset

The dataset contains ~31,000 Russian poems with the following columns:
- `author` - Author name in canonical format (Фамилия Имя Отчество)
- `poem_name` - Poem title
- `text` - Full poem text

Dataset file: `datasets/ru_poems_31k_v1.0.0.csv` (stored with Git LFS)

## Installation

```bash
# Clone repository (requires Git LFS)
git lfs install
git clone git@github.com:kskadart/ru-poetry-dataset.git
cd ru-poetry-dataset

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Validate existing dataset

```bash
python -m src.main --validate-only
```

### Merge source datasets

Place source CSV files in `datasets/`:
- `poems.csv` (columns: writer, poem, text)
- `russianPoetryWithTheme.csv` (columns: author, name, text)

Then run:

```bash
python -m src.main
```

## Project Structure

```
ru-poetry-dataset/
├── datasets/
│   └── ru_poems_31k_v1.0.0.csv   # Main dataset (LFS)
├── src/
│   ├── consts.py                 # Constants and author mapping
│   ├── normalizers.py            # Text normalization functions
│   ├── validators.py             # Dataset validation
│   ├── merge.py                  # Merge logic
│   └── main.py                   # CLI entry point
├── .gitattributes                # Git LFS config
├── requirements.txt
└── README.md
```

## License

MIT
