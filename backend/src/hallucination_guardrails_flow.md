\# 3.41 Hallucination Guardrails \& Refusal Handling



\## Purpose



TradeRule AI must avoid generating confident answers when the

retrieved evidence is missing, weak, or insufficiently relevant.



Because the system deals with international trade compliance,

unsupported claims can create financial, legal, and operational risk.



The hallucination guardrail therefore checks retrieval quality

before allowing the language model to generate an answer.



\---



\## Guardrail Flow



```text

User Question

&#x20;     |

&#x20;     v

Query Embedding

&#x20;     |

&#x20;     v

Qdrant Similarity Search

&#x20;     |

&#x20;     v

Retrieval Quality Evaluation

&#x20;     |

&#x20;     +-----------------------------+

&#x20;     |                             |

&#x20;     v                             v

Strong Context                 Weak / Empty Context

&#x20;     |                             |

&#x20;     v                             v

Build Citation Map             Safe Refusal

&#x20;     |                         No LLM Call

&#x20;     v

Grounded Prompt

&#x20;     |

&#x20;     v

Gemini Generation

&#x20;     |

&#x20;     v

Citation Validation

&#x20;     |

&#x20;     +-----------------------------+

&#x20;     |                             |

&#x20;     v                             v

Valid Citations              Invalid Citation

&#x20;     |                             |

&#x20;     v                             v

Answer + Sources              Safe Refusal

