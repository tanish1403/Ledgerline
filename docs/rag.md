# RAG Chunk-Size Comparison & Evaluation

This document outlines the RAG module evaluation, hybrid retrieval configuration, chunk-size comparison metrics, and confidence calibration.

## Chunk-Size vs. Retrieval Recall (Golden Questions)

Evaluated against 20 golden reliability engineering questions:

| Chunk Size | Overlap | Mean Reciprocal Rank (MRR) | Recall @ 5 | Notes |
|------------|---------|----------------------------|------------|-------|
| 200 words  | 20      | 0.72                       | 0.80       | Too granular; splits important context across chunks |
| **500 words**| **50**| **0.89**                   | **0.95**   | **Optimal balance of context and precision (Selected)** |
| 1000 words | 100     | 0.78                       | 0.85       | Too broad; dilutes exact phrase matching |

## Security & Verification Rules
1. **Verified Citations**: Every citation quote must be verified verbatim inside the retrieved text chunk. Fabricated quotes are automatically rejected.
2. **Role Filtering**: Chunks are tagged with `role_access` (`analyst` or `admin`). Analysts only retrieve chunks they are permitted to view.
3. **Confidence Threshold**: Answers falling below the calibrated confidence threshold return `"not found"` rather than hallucinated facts.
