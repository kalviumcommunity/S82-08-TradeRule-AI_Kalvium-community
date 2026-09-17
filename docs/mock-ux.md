# TradeRule AI — Mock UX

## 1. Query Interface

The main interface allows a user to provide shipment context and ask a natural-language compliance question.

```text
+------------------------------------------------------+
|                    TradeRule AI                      |
+------------------------------------------------------+
| Shipment Context                                     |
|                                                      |
| Origin: CN              Destination: US              |
| Product: Electronics    Freight: Ocean              |
| Weight: 1,250 kg                                     |
|                                                      |
| Question                                             |
| +--------------------------------------------------+ |
| | When does an exporter need an export license?   | |
| +--------------------------------------------------+ |
|                                                      |
|                  [ Ask TradeRule AI ]                |
+------------------------------------------------------+
```

## 2. Grounded Answer

The generated answer is displayed separately from the evidence.

```text
+------------------------------------------------------+
| Grounded Answer                                      |
+------------------------------------------------------+
| An exporter may require an export license before     |
| shipment for certain controlled products, depending  |
| on destination and classification [1].               |
+------------------------------------------------------+
```

## 3. Retrieved Sources

Users can inspect the evidence retrieved from the knowledge base.

```text
+------------------------------------------------------+
| Retrieved Sources                                    |
+------------------------------------------------------+
| [1] license_rules.txt                                |
| Chunk ID: license-0                                  |
| Section: export licensing                            |
|                                                      |
| Retrieved source text:                               |
| Certain controlled products may require an export   |
| license before shipment depending on destination    |
| and classification.                                  |
+------------------------------------------------------+
```

Additional retrieved documents can be displayed below the first source.

## 4. Retrieval Information

The interface displays retrieval information such as:

```text
+------------------------------------------------------+
| Retrieval Details                                    |
+------------------------------------------------------+
| Retrieved: 5                                         |
| Top score: 0.795                                     |
| Supporting chunks: 2                                 |
| Status: answered                                     |
+------------------------------------------------------+
```

This gives the user visibility into the retrieval stage.

## 5. Streaming Response

For streaming queries, the answer is progressively displayed while the response is generated.

The citation and retrieved evidence are displayed alongside the final answer.

```text
+------------------------------------------------------+
| Grounded Answer                                      |
+------------------------------------------------------+
| An exporter may require an export license before     |
| shipment for certain controlled products...          |
|                                                      |
| ✓ Answer completed and citations were validated.     |
+------------------------------------------------------+
```

## 6. Insufficient Context State

When retrieval does not provide sufficiently reliable evidence, the application shows a safe refusal instead of generating an unsupported answer.

```text
+------------------------------------------------------+
| Unable to provide a reliable answer                  |
+------------------------------------------------------+
| I don't have enough reliable context to answer       |
| that.                                                |
+------------------------------------------------------+
```

## 7. User Flow

```text
User
 ↓
Open TradeRule AI
 ↓
Provide shipment context
 ↓
Ask compliance question
 ↓
Generate query embedding
 ↓
Retrieve relevant Qdrant chunks
 ↓
Check retrieval guardrails
 ↓
Augment generation context
 ↓
Generate grounded answer
 ↓
Validate citations
 ↓
Display answer + sources
```

## 8. Document Upload Flow

```text
Upload Document
      ↓
Validate File
      ↓
Store Document
      ↓
Extract Text
      ↓
Clean Text
      ↓
Create Chunks
      ↓
Generate Embeddings
      ↓
Index in Qdrant
      ↓
Document Available for Queries
```

## 9. Main UX Components

### Shipment Context

The user can provide relevant shipment information such as:

- Origin
- Destination
- Product
- Freight type
- Shipment weight

### Question Input

A dedicated question field allows the user to ask a natural-language trade compliance question.

### Grounded Answer

The generated answer is displayed prominently and contains citation markers such as `[1]`.

### Retrieved Sources

The sources retrieved from Qdrant are displayed below the answer so the user can verify the evidence.

### Retrieval Details

The interface provides retrieval information including:

- Number of retrieved chunks
- Top similarity score
- Supporting chunk count
- Answer status
- Retrieval explanation

### Error Handling

The interface provides clear feedback for:

- Failed requests
- Insufficient retrieval context
- Invalid responses
- Citation validation failures

## 10. UX Goals

- Keep compliance questions simple to submit.
- Clearly distinguish the generated answer from source evidence.
- Make citations easy to inspect.
- Show the documents and chunks used for retrieval.
- Provide transparent retrieval information.
- Give users a safe response when reliable context is unavailable.
- Make the RAG process understandable to the user.
