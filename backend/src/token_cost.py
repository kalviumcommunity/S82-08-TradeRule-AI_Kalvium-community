import tiktoken


# Tokenizer used for the assignment.
enc = tiktoken.get_encoding("cl100k_base")


# Simple project-related samples with different lengths.
SAMPLES = {
    "SHORT QUESTION": (
        "What documents are needed for an international shipment?"
    ),

    "PARAGRAPH": (
        "International shipments commonly require documents such as a "
        "commercial invoice, packing list, bill of lading or air waybill, "
        "certificate of origin, and applicable import or export licenses. "
        "The exact requirements can vary depending on the countries, goods, "
        "carrier, and shipment route."
    ),

    "LONG DOCUMENT": (
        "International shipment compliance requires accurate documentation "
        "throughout the shipping process. A commercial invoice provides the "
        "transaction details, including the seller, buyer, description of "
        "goods, quantities, values, currency, and terms of sale. A packing "
        "list describes how the goods are packaged and helps customs and "
        "carriers identify the contents of each package. A bill of lading "
        "or air waybill provides transportation details and acts as an "
        "important shipping record. A certificate of origin identifies "
        "where goods were produced and may be required for customs or "
        "preferential trade treatment. Depending on the product and "
        "destination, additional licenses, permits, certificates, or "
        "restricted-goods documentation may be required. Compliance teams "
        "should verify the applicable requirements before shipment rather "
        "than assuming that every destination follows the same rules."
    ), 
        "LONG WORDS": (
        "internationalization pseudonymization refundable "
        "documentation classification authorization"
    ),

    "CODE": (
        "def calculate_cost(tokens, rate): "
        "return (tokens / 1000) * rate"
    ),
}


# Example pricing rates per 1,000 tokens.
INPUT_RATE = 0.0005
OUTPUT_RATE = 0.0015


def count_tokens(text: str) -> int:
    """Return the number of tokens in a text string."""
    return len(enc.encode(text))


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate cost using separate input and output token rates."""
    input_cost = (input_tokens / 1000) * INPUT_RATE
    output_cost = (output_tokens / 1000) * OUTPUT_RATE
    return input_cost + output_cost


def main():
    print("=" * 70)
    print("TRADE RULE AI — TOKEN COUNT & COST ESTIMATION")
    print("=" * 70)

    total_tokens = 0

    for name, text in SAMPLES.items():
        character_count = len(text)
        word_count = len(text.split())
        token_count = count_tokens(text)

        total_tokens += token_count

        print(f"\n{name}")
        print("-" * 70)
        print(f"Characters : {character_count}")
        print(f"Words      : {word_count}")
        print(f"Tokens     : {token_count}")

    print("\n" + "=" * 70)
    print("COST ESTIMATE")
    print("=" * 70)

    # Treat the combined samples as input and assume a sample output.
    input_tokens = total_tokens
    output_tokens = 150

    cost = estimate_cost(input_tokens, output_tokens)

    print(f"Input tokens     : {input_tokens}")
    print(f"Output tokens    : {output_tokens}")
    print(f"Input rate / 1K  : ${INPUT_RATE}")
    print(f"Output rate / 1K : ${OUTPUT_RATE}")
    print(f"Estimated cost   : ${cost:.6f}")

    print("\n" + "=" * 70)
    print("LENGTH → TOKEN RELATIONSHIP")
    print("=" * 70)

    print(
        "Characters and words generally increase as token count increases, "
        "but the relationship is not exactly proportional because tokenizers "
        "split text into variable-sized pieces."
    )


if __name__ == "__main__":
    main()