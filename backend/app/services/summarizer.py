# app/services/summarizer.py

import re
import math
from collections import defaultdict
import numpy as np

# Preprocessing
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=\w)- (?=\w)", "", text)  # fix broken hyphen words
    return text.strip()


# Sentence Tokenization
def split_into_sentences(text: str):
    # Split at periods but keep them
    sentences = re.split(r'(?<=[.!?]) +', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    return sentences


# Word Tokenization (for similarity)
def tokenize(sentence: str):
    sentence = sentence.lower()
    words = re.findall(r"[a-zA-Z]{3,}", sentence)  # only words >=3 letters
    return words


# Sentence Similarity (Cosine similarity)

def sentence_similarity(sent1, sent2):
    words1 = tokenize(sent1)
    words2 = tokenize(sent2)

    if not words1 or not words2:
        return 0

    freq1 = defaultdict(int)
    freq2 = defaultdict(int)

    for w in words1:
        freq1[w] += 1
    for w in words2:
        freq2[w] += 1

    all_words = list(set(words1 + words2))

    v1 = np.array([freq1[w] for w in all_words])
    v2 = np.array([freq2[w] for w in all_words])

    denom = (np.linalg.norm(v1) * np.linalg.norm(v2))
    if denom == 0:
        return 0

    return np.dot(v1, v2) / denom


# Build Similarity Graph
def build_similarity_matrix(sentences):
    n = len(sentences)
    sim_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            sim_matrix[i][j] = sentence_similarity(sentences[i], sentences[j])

    # Normalize rows
    for i in range(n):
        if sim_matrix[i].sum() != 0:
            sim_matrix[i] /= sim_matrix[i].sum()

    return sim_matrix


# TextRank (PageRank)
def textrank(sentences, eps=1e-4, d=0.85):
    n = len(sentences)
    scores = np.ones(n) / n
    sim_matrix = build_similarity_matrix(sentences)

    while True:
        new_scores = (1 - d) + d * sim_matrix.T.dot(scores)
        if np.abs(new_scores - scores).sum() <= eps:
            break
        scores = new_scores

    scored_sentences = list(enumerate(scores))
    ranked = sorted(scored_sentences, key=lambda x: x[1], reverse=True)
    return ranked


# Final Summarizer
# ---------------------------------------------------------
def textrank_summarize(text: str, max_sentences: int = 8) -> str:
    if len(text) < 500:
        return text  # no need to summarize short text

    sentences = split_into_sentences(text)
    if len(sentences) <= max_sentences:
        return text  # not enough content

    ranked = textrank(sentences)
    top_indices = [idx for idx, _ in ranked[:max_sentences]]
    top_indices.sort()  # keep original order

    summary = " ".join([sentences[i] for i in top_indices])
    return summary