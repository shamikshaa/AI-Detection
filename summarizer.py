#!/usr/bin/env python3
"""Word Document Summarizer & Q&A

Summarizes a .docx file (paragraphs and/or tables) with facebook/bart-large-cnn
and lets you ask questions about its content using simple keyword matching.

Usage:
    python summarizer.py report.docx
    python summarizer.py report.docx --source tables
    python summarizer.py report.docx --source both --no-qa
"""
import argparse
import re
import sys

import docx

MODEL_NAME = "facebook/bart-large-cnn"
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "of", "in", "on", "at", "to",
    "and", "or", "for", "with", "what", "who", "when", "where", "which", "how",
    "does", "do", "did", "this", "that", "it", "by", "from", "as", "be",
}


# ---------------------------------------------------------------------------
# Reading the document
# ---------------------------------------------------------------------------
def extract_paragraph_text(doc):
    """Return all non-empty paragraph text joined by spaces."""
    return " ".join(p.text.strip() for p in doc.paragraphs if p.text.strip())


def extract_table_text(doc):
    """Return table rows as 'cell | cell | cell' lines (merged cells de-duplicated)."""
    rows = []
    for table in doc.tables:
        for row in table.rows:
            cells = []
            for cell in row.cells:
                text = cell.text.strip()
                if text and (not cells or cells[-1] != text):
                    cells.append(text)
            if cells:
                rows.append(" | ".join(cells))
    return "\n".join(rows)


def read_document(path, source="paragraphs"):
    """Load a .docx file and return its text. source: paragraphs | tables | both."""
    doc = docx.Document(path)
    parts = []
    if source in ("paragraphs", "both"):
        parts.append(extract_paragraph_text(doc))
    if source in ("tables", "both"):
        parts.append(extract_table_text(doc))
    return "\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Summarization
# ---------------------------------------------------------------------------
def split_into_sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def chunk_text(text, max_chars=1000):
    """Group whole sentences into chunks of at most max_chars characters."""
    chunks, current = [], ""
    for sentence in split_into_sentences(text):
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def summarize_text(text, max_length=100, min_length=40):
    """Summarize text chunk by chunk and join the partial summaries."""
    from transformers import pipeline  # imported lazily: heavy import

    print(f"Loading model '{MODEL_NAME}' (first run downloads ~1.6 GB)...")
    summarizer = pipeline("summarization", model=MODEL_NAME)

    summaries = []
    for chunk in chunk_text(text):
        words = len(chunk.split())
        upper = min(max_length, max(10, int(words * 0.8)))
        lower = min(min_length, upper - 5)
        result = summarizer(chunk, max_length=upper, min_length=lower, do_sample=False)
        summaries.append(result[0]["summary_text"])
    return " ".join(summaries)


# ---------------------------------------------------------------------------
# Question answering (keyword overlap)
# ---------------------------------------------------------------------------
def tokenize(text):
    return {w for w in re.findall(r"\w+", text.lower()) if w not in STOPWORDS}


def answer_question(question, sentences):
    """Return the sentence sharing the most keywords with the question."""
    q_words = tokenize(question)
    best_sentence, best_score = "", 0
    for sentence in sentences:
        score = len(q_words & tokenize(sentence))
        if score > best_score:
            best_sentence, best_score = sentence, score
    return best_sentence or "No relevant answer found in the document."


def interactive_qa(text):
    sentences = split_into_sentences(text)
    print("\nAsk questions about the document. Type 'exit' to stop.\n")
    while True:
        try:
            question = input("Ask a question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() == "exit":
            break
        if question:
            print("Answer:", answer_question(question, sentences), "\n")
    print("Finished.")


# ---------------------------------------------------------------------------
# Command line interface
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Summarize a Word document and ask questions about it.")
    parser.add_argument("file", help="path to a .docx file")
    parser.add_argument(
        "--source", choices=["paragraphs", "tables", "both"], default="paragraphs",
        help="which part of the document to read (default: paragraphs)",
    )
    parser.add_argument("--no-qa", action="store_true", help="skip the interactive Q&A session")
    args = parser.parse_args()

    try:
        text = read_document(args.file, args.source)
    except Exception as exc:  # missing file, not a .docx, etc.
        sys.exit(f"Could not read '{args.file}': {exc}")

    if not text.strip():
        sys.exit(f"No text found in '{args.file}' for source '{args.source}'.")

    print(f"Document loaded: {len(text)} characters")
    print("\nGenerating summary...")
    summary = summarize_text(text)
    print("\n===== DOCUMENT SUMMARY =====\n")
    print(summary)

    if not args.no_qa:
        interactive_qa(text)


if __name__ == "__main__":
    main()
