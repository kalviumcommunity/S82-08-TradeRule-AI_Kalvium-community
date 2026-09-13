\# 3.40 Source Citation \& Attribution



\## Overview



TradeRule AI attaches citations to grounded answers so that users can

trace factual claims back to the retrieved source documents and the

exact chunks used during retrieval.



The citation system preserves:



\- Source document name

\- Chunk ID

\- Chunk index

\- Section metadata when available

\- Original retrieved chunk text



This makes generated answers verifiable instead of merely plausible.



\---



\## Citation Flow



```text

User Question

&#x20;     |

&#x20;     v

Query Embedding

&#x20;     |

&#x20;     v

Qdrant Retrieval

&#x20;     |

&#x20;     v

Retrieved Chunks

&#x20;     |

&#x20;     v

Token-Budget Selection

&#x20;     |

&#x20;     v

Citation Map

&#x20;     |

&#x20;     +----------------------------+

&#x20;     |                            |

&#x20;     v                            v

Source Metadata             Original Chunk Text

&#x20;     |                            |

&#x20;     +-------------+--------------+

&#x20;                   |

&#x20;                   v

&#x20;             Cited Prompt

&#x20;                   |

&#x20;                   v

&#x20;            Gemini Generation

&#x20;                   |

&#x20;                   v

&#x20;             Cited Answer

&#x20;                   |

&#x20;                   v

&#x20;           Citation Validation

&#x20;                   |

&#x20;                   v

&#x20;         Answer + Citation Map

