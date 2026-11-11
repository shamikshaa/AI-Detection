# Word Document Summarizer & Q&A

A command-line tool that summarizes `.docx` files with the Hugging Face
`facebook/bart-large-cnn` model and lets you ask questions about the document.

## Features
- Reads text from **paragraphs**, **tables**, or **both**
- Sentence-aware chunking so long documents are summarized chunk by chunk
- Interactive question answering (keyword-overlap sentence retrieval)
- Runs locally, no API key needed

## Installation
```bash
git clone https://github.com/<your-username>/docx-summarizer.git
cd docx-summarizer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
```bash
python summarizer.py report.docx                    # summarize paragraphs, then Q&A
python summarizer.py report.docx --source tables    # read table content only
python summarizer.py report.docx --source both      # paragraphs + tables
python summarizer.py report.docx --no-qa            # summary only
```
The first run downloads the model (about 1.6 GB).

## How it works
1. `python-docx` extracts the text from the document.
2. The text is split into sentence-aligned chunks of ~1000 characters.
3. BART summarizes each chunk and the partial summaries are joined.
4. For Q&A, the question is matched to the sentence with the most shared keywords.

## Tech stack
Python, python-docx, Hugging Face Transformers, PyTorch

## Limitations
- Q&A is keyword-based, not a generative or semantic model.
- Very long documents produce a long combined summary.

## Possible improvements
- Semantic search for Q&A using sentence embeddings
- Support for PDF and TXT files
- A web UI with Flask or Streamlit
