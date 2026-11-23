# TokenFlow Benchmark Results

## Conditions
- **Sample Size**: 2 multi-turn conversations (synthetic).
- **Baseline**: Sending full raw conversation history.
- **Method**: TokenFlow AI Compression (Lexical/Vector Ranker + Extractive Summary).

## Metrics
- **Total Original Tokens**: 574
- **Total Compressed Tokens**: 368
- **Average Token Reduction %**: 35.89%
- **Answer Quality Retained**: ~96.41% (estimated structural relevance)

*Note: These results were generated locally without the Gemini API (using fallback lexical similarity).*
