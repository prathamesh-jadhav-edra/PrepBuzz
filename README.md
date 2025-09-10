# PrepBuzz - CAT Questions RAG System

**An intelligent educational video generation system that creates AI-powered explanations for CAT (Common Admission Test) questions with automated video production.**

## 🌟 Overview

PrepBuzz is a comprehensive RAG (Retrieval-Augmented Generation) system designed to generate educational videos from CAT exam questions. The system features both **standard processing** and **intelligent agentic mode** that adapts processing strategies based on question complexity and content analysis.

## 🏗️ System Architecture

### Simplified Unified Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PrepBuzz CLI                             │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐  │
│  │  Standard Mode  │  │        Agentic Mode                 │  │
│  │  (Traditional)  │  │   (Intelligent Processing)         │  │
│  └─────────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   UnifiedFlowEngine                             │
│  • execute_pipeline(agentic=False) - Standard processing       │
│  • execute_pipeline(agentic=True)  - Intelligent processing    │
│  • Built-in SimpleAgent for content analysis & optimization    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Processing Pipeline                          │
│  ┌──────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Question   │  │ Reasoning   │  │      LLM Processing     │ │
│  │  Selection   │─▶│ Extraction  │─▶│     (AI Analysis)       │ │
│  │    Flow      │  │    Flow     │  │                         │ │
│  └──────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                              │                  │
│                                              ▼                  │
│                    ┌─────────────────────────────────────────┐  │
│                    │         Video Generation               │  │
│                    │    (Slides + Audio + Assembly)         │  │
│                    └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Storage Layer                           │
│  ┌─────────────┐           ┌─────────────────────────────────┐   │
│  │   SQLite    │           │          Qdrant                 │   │
│  │ (Questions, │           │   (Vector Embeddings for        │   │
│  │  Metadata)  │           │    Semantic Search)             │   │
│  └─────────────┘           └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🧠 Agentic Intelligence Features

### SimpleAgent Capabilities
- **Content Analysis**: Assesses question complexity, subject patterns, and processing requirements
- **Strategy Planning**: Selects optimal processing approach (performance/quality/balanced)
- **Intelligent Execution**: Monitors pipeline execution with adaptive parameter optimization
- **Quality Assessment**: Provides confidence scoring and performance metrics

### Processing Modes

#### Standard Mode
- Traditional pipeline processing
- Fixed parameters and configurations
- Reliable, predictable execution
- Usage: `python main.py generate --subject Quant --count 1`

#### Agentic Mode  
- Intelligent content analysis and strategy planning
- Adaptive parameter optimization based on question complexity
- Real-time execution monitoring and quality assessment
- Enhanced insights and confidence scoring
- Usage: `python main.py generate --subject Quant --count 1 --agentic`

## 📁 Project Structure

```
PrepBuzz/
├── 📄 main.py                          # CLI entry point (simplified)
├── 📄 pyproject.toml                   # Poetry dependencies 
├── 📄 .env.example                     # Environment variables template
├── 📄 AGENTIC_ARCHITECTURE.md          # Detailed architecture documentation
├── 📄 SIMPLIFICATION_SUMMARY.md        # System simplification details
│
├── 📁 src/                             # Source code
│   ├── 📁 core/                        # Core system components
│   │   ├── 📄 __init__.py
│   │   ├── 📄 unified_flow_engine.py   # Unified engine (standard + agentic)
│   │   ├── 📄 database.py              # SQLite + Qdrant integration
│   │   ├── 📄 llm_factory.py           # LLM provider abstraction
│   │   └── 📄 math_solver.py           # Mathematical problem solving
│   │
│   ├── 📁 flows/                       # Processing pipeline flows
│   │   ├── 📄 __init__.py
│   │   ├── 📄 question_flow.py         # Question selection logic
│   │   ├── 📄 reasoning_flow.py        # Reasoning extraction with search
│   │   ├── 📄 llm_flow.py              # AI processing pipeline
│   │   └── 📄 video_flow.py            # Video generation engine
│   │
│   └── 📁 utils/                       # Utilities and configuration
│       ├── 📄 __init__.py
│       ├── 📄 config.py                # Pydantic configuration management
│       └── 📄 google_search.py         # Simplified search utilities
│
├── 📁 rules/                           # Agent behavior rules (preserved)
│   ├── 📄 architect-planner.mdc
│   ├── 📄 feature-planner.mdc
│   ├── 📄 implementer.mdc
│   └── 📄 claude.md
│
├── 📁 data/                            # Database files
│   └── 📄 cat_questions.db             # SQLite database (auto-created)
│
├── 📁 output/                          # Generated content
│   ├── 📁 videos/                      # Final video outputs
│   ├── 📁 temp/                        # Temporary processing files
│   └── 📁 logs/                        # System logs
│
└── 📁 qdrant_storage/                  # Qdrant vector database files
```

## 🚀 Quick Start Guide

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd PrepBuzz

# Install dependencies using Poetry
poetry install

# Activate the virtual environment
poetry shell

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys (OpenAI, Anthropic, etc.)
```

### 2. Initialize System

```bash
# Setup sample questions and database
python main.py setup

# Check system status
python main.py status
```

### 3. Generate Videos

#### Standard Mode (Traditional Processing)
```bash
# Generate single video
python main.py generate

# Generate multiple videos with subject filter
python main.py generate --subject Quant --count 3

# Test the pipeline
python main.py test
```

#### Agentic Mode (Intelligent Processing)
```bash
# Generate with intelligent analysis
python main.py generate --agentic

# Generate multiple videos with intelligent optimization
python main.py generate --subject Verbal --count 2 --agentic

# Test with intelligent processing
python main.py test --agentic
```

### 4. Expected Output

#### Standard Mode Output
```
🚀 Starting PrepBuzz video generation...
📊 Subject filter: All subjects
🎬 Videos to generate: 1
⚙️ Standard mode: Using traditional pipeline processing
📚 Found 3 questions in database

🎯 Generating video 1/1...
✅ Video generated successfully: output/videos/cat_2023_quant_001_video.mp4

📈 Generation Summary:
✅ Successful: 1/1
📁 Output directory: output/videos
```

#### Agentic Mode Output
```
🚀 Starting PrepBuzz video generation...
📊 Subject filter: Quant
🎬 Videos to generate: 1
🤖 Agentic mode: ENABLED - Using intelligent agent coordination
📚 Found 3 questions in database

🎯 Generating video 1/1...
✅ Video generated successfully: output/videos/cat_2023_quant_001_video.mp4
🧠 Analysis: Analyzed Quant question with 75% complexity
📊 Confidence: 88%
⏱️ Processing time: 67.3s

📈 Generation Summary:
✅ Successful: 1/1
📁 Output directory: output/videos
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# LLM Provider Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# System Configuration
LOG_LEVEL=INFO
OUTPUT_DIR=./output
DATABASE_PATH=./data/cat_questions.db

# Qdrant Configuration (Optional)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Supported LLM Providers

- **OpenAI**: GPT-4, GPT-3.5-turbo (recommended for best quality)
- **Anthropic**: Claude models (excellent for reasoning)
- **Local**: Free models via transformers (for development)

## 🔧 Advanced Usage

### Custom Flow Configuration

```bash
# Generate with specific processing parameters
python main.py generate --agentic --subject Logic --count 1
```

The agentic mode will automatically:
- Analyze question complexity
- Select optimal processing strategy (performance/quality/balanced)
- Optimize LLM parameters based on content
- Monitor execution and provide quality assessment

### System Status and Monitoring

```bash
# Check detailed system status
python main.py status
```

Output includes:
- Database connection and question count
- Available LLM providers
- Flow engine status
- Agent capabilities (in agentic mode)
- Output directory configuration

## 🎯 Key Features

### Intelligence Features
- **Adaptive Processing**: Automatically adjusts strategies based on question complexity
- **Quality Optimization**: Intelligent parameter tuning for better results
- **Performance Monitoring**: Real-time execution tracking and metrics
- **Confidence Scoring**: AI-powered quality assessment

### Video Generation
- **Professional Slides**: Clean, educational slide design
- **AI Narration**: Natural text-to-speech with Google TTS
- **Automated Assembly**: MoviePy-powered video compilation
- **Multiple Formats**: Configurable output formats and quality

### Data Management
- **SQLite Storage**: Efficient question and metadata storage
- **Vector Search**: Qdrant-powered semantic search capabilities
- **Flexible Querying**: Subject-based filtering and random selection

## 🧪 Testing

```bash
# Test standard pipeline
python main.py test

# Test agentic pipeline with intelligence
python main.py test --agentic

# Validate system components
python test_simplified_system.py
```

## 📊 Performance

### Standard Mode
- **Processing Time**: 45-90 seconds per video
- **Memory Usage**: ~200-400 MB
- **Reliability**: Basic error handling, predictable execution

### Agentic Mode
- **Processing Time**: 50-100 seconds per video (includes 5-15s intelligence overhead)
- **Memory Usage**: ~300-500 MB (intelligent coordination overhead)
- **Reliability**: Advanced error recovery, adaptive execution
- **Quality**: Higher success rates and better output quality

## 🤝 Contributing

This system follows clean architecture principles and industry MVP standards:

- **KISS Principle**: Keep implementations simple and understandable
- **YAGNI Approach**: Only implement what's actually needed
- **Clean Code**: Readable, maintainable, well-documented code
- **Modular Design**: Clear separation between flows and intelligence

## 📝 License

[Your license information here]

## 🔗 Related Documentation

- [AGENTIC_ARCHITECTURE.md](./AGENTIC_ARCHITECTURE.md) - Detailed system architecture and flow diagrams
- [SIMPLIFICATION_SUMMARY.md](./SIMPLIFICATION_SUMMARY.md) - System evolution and simplification details
- [rules/](./rules/) - Agent behavior rules and guidelines