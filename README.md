Signature Semantic Decoder

A lightweight parsing toolkit for interpreting Web3 wallet signature requests. This project provides modular decoders for common Ethereum signing methods, including EIP-712 typed data, personal_sign, and eth_sendTransaction. Each parser extracts key fields, reconstructs structural meaning, and supports basic semantic classification to help reveal the intent behind opaque signature payloads.

The codebase is designed for research on signature transparency and can serve as a backend component for systems that aim to improve user comprehension and security during wallet interactions.

## Project Structure

```
├── src/                    # New architecture (production)
│   ├── core/              # Core processing pipeline
│   │   ├── input/         # Input adaptation layer
│   │   │   ├── adapter.py
│   │   │   ├── definitions.py
│   │   │   └── validators.py
│   │   ├── processing/    # Classification, structure, interpretation
│   │   │   ├── classifier.py
│   │   │   ├── structure.py
│   │   │   ├── interpreter.py
│   │   │   ├── risk.py
│   │   │   ├── knowledge_base.py
│   │   │   └── data/      # JSON knowledge base files
│   │   └── output/        # Presentation and formatting
│   │       ├── presenter.py
│   │       └── highlighter.py
│   ├── pipeline.py        # Main orchestration class
│   └── web/               # Web UI (Flask)
│       ├── app.py
│       ├── templates/
│       └── static/
│
└── parser_demo/           # Legacy demo version
    ├── core.py           # Original parser
    ├── web_ui.py         # Demo web interface
    ├── examples/         # Sample data and demos
    └── static/           # Demo UI assets
```
