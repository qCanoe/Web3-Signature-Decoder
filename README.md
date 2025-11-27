# Signature Semantic Decoder

A lightweight parsing toolkit for interpreting Web3 wallet signature requests. This project provides modular decoders for common Ethereum signing methods, including EIP-712 typed data, personal_sign, and eth_sendTransaction. Each parser extracts key fields, reconstructs structural meaning, and supports basic semantic classification to help reveal the intent behind opaque signature payloads.

The codebase is designed for research on signature transparency and can serve as a backend component for systems that aim to improve user comprehension and security during wallet interactions.

## Project Structure

```txt
├── src/                    # New architecture (production)
│   ├── core/              # Core processing pipeline
│   │   ├── input/         # Input adaptation layer
│   │   │   ├── adapter.py          # Input adapter (EIP-712, transaction, personal_sign)
│   │   │   ├── definitions.py     # Intermediate representation definitions
│   │   │   └── validators.py      # Input validation (EIP-712 schema, EIP-191)
│   │   ├── processing/    # Classification, structure, interpretation
│   │   │   ├── classifier.py      # Signature classification (bridge, delegation, etc.)
│   │   │   ├── structure.py       # Actor-Action-Object structure extraction
│   │   │   ├── interpreter.py     # Semantic interpretation (templates + LLM)
│   │   │   ├── risk.py            # Multi-dimensional risk assessment
│   │   │   ├── knowledge_base.py  # Contract/function signature knowledge base
│   │   │   ├── transaction_decoder.py  # ABI decoder for transactions
│   │   │   ├── extractors.py      # Parameter extraction utilities
│   │   │   └── data/              # JSON knowledge base files
│   │   │       ├── function_signatures.json
│   │   │       ├── eip712_types.json
│   │   │       ├── known_contracts.json
│   │   │       ├── token_metadata.json
│   │   │       ├── protocol_patterns.json
│   │   │       └── ...
│   │   ├── output/        # Presentation and formatting
│   │   │   ├── presenter.py       # Result formatting and UI output
│   │   │   └── highlighter.py     # Text highlighting utilities
│   │   ├── utils/         # Utility modules
│   │   │   ├── logger.py          # Unified logging system
│   │   │   └── exceptions.py     # Custom exception classes
│   │   ├── config.py      # Configuration management
│   │   └── pipeline.py    # Main orchestration class
│   └── web/               # Web UI (Flask)
│       ├── app.py         # Flask application
│       ├── templates/     # HTML templates
│       └── static/        # Static assets (CSS, JS, images)
│
├── tests/                 # Standardized tests
│   ├── test_core.py       # Unit tests for core logic
│   └── test_pipeline.py   # Integration tests for pipeline
└── src/utils/mock_data.py # Shared test data
```

## Research MVP Disclaimer

Please note that this project is currently developed as a **Research MVP (Minimum Viable Product)**. It is primarily designed to demonstrate the feasibility of semantic interpretation for blockchain signatures within an academic or experimental context.

While the core pipeline effectively handles common signature types, many advanced features and production-grade implementations are intentionally simplified or scoped out for this version. The current implementation serves as a standard baseline for research purposes, and there are significant opportunities for further development and optimization.

**Examples of areas for future improvement include:**

* **Deep ABI Parsing:** Currently relies on function selectors and partial decoding. A production version would integrate full ABI retrieval (e.g., via Etherscan API) and support complex `multicall` recursion.
* **Dynamic Threat Intelligence:** The risk engine uses static heuristics. Future iterations could integrate real-time threat feeds (e.g., Chainabuse) and transaction simulation (e.g., Tenderly) to detect phishing campaigns dynamically.
* **Expanded Knowledge Base:** The semantic interpreter's effectiveness depends on its knowledge base. Expanding coverage to include more Layer-2 protocols, niche DeFi contracts, and non-standard NFT standards would significantly enhance interpretation accuracy.
* **Visual Semantics:** Moving beyond text-based explanations to generate visual asset flow diagrams (e.g., "Your Wallet -> [100 USDC] -> Uniswap Pool") would further improve user comprehension.

This repository stands as a foundational framework, inviting researchers and developers to build upon these concepts to create fully robust, production-ready signature transparency tools.
