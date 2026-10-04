# TokenFlow Benchmark Results

## Conditions
- **Sample Size**: 2 multi-turn conversations (synthetic).
- **Baseline**: Sending full raw conversation history.
- **Method**: TokenFlow AI Compression (Lexical/Vector Ranker + Extractive Summary).

## Metrics
- **Total Original Tokens**: 370
- **Total Compressed Tokens**: 221
- **Average Token Reduction %**: 40.27%
- **Answer Quality Retained**: ~95.97% (estimated structural relevance)

*Note: These results were generated locally without the Gemini API (using fallback lexical similarity).*
