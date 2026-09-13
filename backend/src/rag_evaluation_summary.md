# 3.43 RAG Evaluation Summary

## Overall Quality

- Questions evaluated: 5
- Average correctness: 0.60
- Average grounding: 1.00
- Average citation accuracy: 0.50
- Overall quality: 0.70
- Failures: 5

## Scoring Approach

Correctness measures whether expected answer points appear in the generated answer.

Grounding measures whether retrieved context and valid citations support the generated answer.

Citation accuracy measures whether cited sources match the expected supporting sources.

## Failures

### Failure 1

**Question:** When does an exporter need an export license?

- Correctness: 1.00
- Grounding: 1.00
- Citation accuracy: 0.50
- Grounding cause: The answer had retrieved context and valid citations supporting the response.
- Citation cause: At least one expected source was cited, but additional sources were also cited.

### Failure 2

**Question:** What documents are required for customs clearance?

- Correctness: 0.50
- Grounding: 1.00
- Citation accuracy: 0.50
- Grounding cause: The answer had retrieved context and valid citations supporting the response.
- Citation cause: At least one expected source was cited, but additional sources were also cited.

### Failure 3

**Question:** What should an importer check before importing goods?

- Correctness: 0.50
- Grounding: 1.00
- Citation accuracy: 0.50
- Grounding cause: The answer had retrieved context and valid citations supporting the response.
- Citation cause: At least one expected source was cited, but additional sources were also cited.

### Failure 4

**Question:** What should an exporter verify before shipment?

- Correctness: 0.50
- Grounding: 1.00
- Citation accuracy: 0.50
- Grounding cause: The answer had retrieved context and valid citations supporting the response.
- Citation cause: At least one expected source was cited, but additional sources were also cited.

### Failure 5

**Question:** What are the main requirements for shipping documentation?

- Correctness: 0.50
- Grounding: 1.00
- Citation accuracy: 0.50
- Grounding cause: The answer had retrieved context and valid citations supporting the response.
- Citation cause: At least one expected source was cited, but additional sources were also cited.

## Improvement Plan

The weakest dimension is **citation accuracy**.

Improve source metadata, citation mapping, and citation validation.
