\# 3.39 Grounded Answer Generation



\## Overview



TradeRule AI uses retrieval-augmented generation to produce answers that are grounded in retrieved compliance documents.



The generation stage does not rely only on the model's general knowledge. Instead, the retrieved chunks are injected into a structured prompt with explicit grounding instructions.



The model is instructed to:



\- Use only the retrieved context.

\- Avoid unsupported claims.

\- Avoid relying on outside knowledge.

\- Cite supporting context using source markers.

\- Return a fallback when the context is insufficient.



\---



\## RAG Generation Flow



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

Top-K Retrieved Chunks

&#x20;     |

&#x20;     v

Context Augmentation

&#x20;     |

&#x20;     +------------------------------+

&#x20;     |                              |

&#x20;     v                              v

Source Markers                Token Budget

&#x20;     |                              |

&#x20;     +--------------+---------------+

&#x20;                    |

&#x20;                    v

&#x20;            Grounded Prompt

&#x20;                    |

&#x20;                    v

&#x20;             Gemini 2.5 Flash

&#x20;                    |

&#x20;                    v

&#x20;           Grounded Answer

&#x20;                    |

&#x20;                    v

&#x20;            Source Citations

