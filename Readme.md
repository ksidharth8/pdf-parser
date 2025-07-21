# PDF Outline Extractor

This project extracts structured outlines from PDF files and saves them as `.json`. It uses font size, boldness, and layout heuristics to classify headings (`title`, `H1`, `H2`, `H3`) and ignores body text or tables.

---

## 📌 Approach

The extractor works as follows:

1. **Parse all PDFs** in the `/app/input` directory using `PyMuPDF`.
2. **Extract spans** of text along with font metadata: font size, weight, position, etc.
3. **Merge multiline headings** using horizontal and vertical proximity.
4. **Assign heading levels**:
   - Largest font: `title`
   - Next: `H1`, then `H2`, then `H3` (only if needed and above minimum font size).
5. **Ignore table rows** using heuristics (short repeated tokens, multi-space gaps, etc.).
6. **Save results** into `/app/output/filename.json`.

---

## 🧠 Libraries Used

- [`PyMuPDF`](https://pymupdf.readthedocs.io/en/latest/) (`fitz`) – for PDF parsing
- `os`, `re`, `json`, `collections` – built-in Python utilities

All dependencies are listed in [`requirements.txt`](./requirements.txt).

---

## 🐳 Docker Build & Run Instructions

Ensure your Docker is using **amd64 architecture**.

### 🔧 Build Image

```bash
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
```

### 🚀 Run Container

```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  mysolutionname:somerandomidentifier
```

✅ This will process all `.pdf` files in `/input` and generate corresponding `.json` files in `/output`.

---

## 📂 Folder Structure

```
.
├── input/                  # Place your input .pdf files here
├── output/                 # Extracted .json files will appear here
├── main.py                 # Main script for PDF parsing
├── Dockerfile              # Dockerfile (AMD64-compatible)
├── requirements.txt        # Python dependencies
├── .gitignore              # Ignores venv, __pycache__, output, etc.
└── README.md               # Project documentation
```

---

## 📤 Sample Output

For a PDF with headings like:

```
1. Introduction
1.1 Background
1.1.1 Scope
```

You will get:

```json
{
  "title": "Sample PDF Document",
  "outline": [
    {
      "level": "H1",
      "text": "1. Introduction",
      "page": 1
    },
    {
      "level": "H2",
      "text": "1.1 Background",
      "page": 2
    },
    {
      "level": "H3",
      "text": "1.1.1 Scope",
      "page": 3
    }
  ]
}
```

---

## ✅ Highlights

- ✅ Fully **offline**
- ✅ No internet or API calls
- ✅ No GPU required
- ✅ Works on **amd64 (x86_64)** CPUs
- ✅ Model-free, rule-based logic
- ✅ Lightweight (under 200MB)

---

## 🛠️ Customization

- Font-level classification can be tuned in `main.py`
- Merge thresholds can be adjusted: `x_gap_threshold`, `y_tolerance`
- `is_probable_table_row()` can be extended with more rules

---

## 📝 License

MIT License.