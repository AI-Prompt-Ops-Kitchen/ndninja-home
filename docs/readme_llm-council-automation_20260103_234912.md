# LLM Council Automation

[![Status](https://img.shields.io/badge/status-completed-success.svg)](https://github.com/yourusername/llm-council)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![n8n](https://img.shields.io/badge/n8n-template%2011618-orange.svg)](https://n8n.io)

> Harness the collective intelligence of multiple AI models with automated parallel querying, evaluation, and synthesis.

## Overview

LLM Council Automation is an intelligent orchestration system that queries multiple leading AI models simultaneously—GPT-4, Claude, and Gemini—and synthesizes their responses into a single, optimized answer. Built on n8n workflow automation, this project eliminates the need to manually compare outputs from different models by automatically evaluating and combining the best aspects of each response.

Think of it as having a council of AI experts deliberate on every query, ensuring you get the most comprehensive, accurate, and well-rounded answers possible.

## ✨ Key Features

- **Multi-Model Parallel Querying**: Simultaneously sends prompts to GPT-4, Claude, and Gemini
- **Intelligent Response Evaluation**: Automatically assesses each model's response for quality, accuracy, and relevance
- **Smart Synthesis**: Combines the best elements from all models into a single, superior answer
- **n8n-Powered Automation**: Built on the popular n8n workflow platform for easy customization and extension
- **Template-Based**: Uses n8n template #11618 as a foundation for rapid deployment
- **Scalable Architecture**: Easily add more AI models or modify evaluation criteria
- **Cost-Effective**: Get the benefits of multiple AI subscriptions with optimized API usage

## 🎯 What Makes This Different

| Feature | Traditional Approach | LLM Council |
|---------|---------------------|-------------|
| **Model Access** | Use one model at a time | Query all models in parallel |
| **Response Quality** | Limited to single model's perspective | Synthesized best of all models |
| **Comparison** | Manual copy-paste between interfaces | Automated evaluation and synthesis |
| **Time Investment** | Minutes per query across platforms | Seconds with single query |
| **Cost Efficiency** | Pay for multiple subscriptions | Optimized API usage |
| **Consistency** | Varies by chosen model | Always gets best combined output |

## 🛠️ Tech Stack

- **Workflow Engine**: n8n (workflow automation)
- **AI Models**: 
  - OpenAI GPT-4
  - Anthropic Claude
  - Google Gemini
- **Scripting**: Python (evaluation logic)
- **Configuration**: Markdown, Shell scripts
- **Data**: SQL (optional logging/analytics)

## 📋 Prerequisites

- n8n installed (self-hosted or cloud)
- API keys for:
  - OpenAI (GPT-4 access)
  - Anthropic (Claude access)
  - Google AI (Gemini access)
- Node.js 16+ (for n8n)
- Python 3.8+ (for evaluation scripts)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/llm-council.git
cd llm-council
```

### 2. Set Up n8n

If you don't have n8n installed:

```bash
npm install -g n8n
```

Or use Docker:

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

### 3. Configure API Keys

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_AI_API_KEY=your_google_key_here
```

### 4. Import the Workflow

1. Open n8n (default: `http://localhost:5678`)
2. Navigate to **Workflows** → **Import from File**
3. Select the workflow file from the repository
4. Configure credentials for each AI service in the workflow nodes

### 5. Install Python Dependencies (Optional)

If using custom evaluation scripts:

```bash
pip install -r requirements.txt
```

## 💡 Usage

### Basic Query

1. Open the imported workflow in n8n
2. Trigger the workflow with a query:

```json
{
  "query": "Explain quantum computing in simple terms",
  "evaluation_criteria": ["accuracy", "clarity", "completeness"]
}
```

3. The workflow will:
   - Send the query to all three models in parallel
   - Collect and evaluate responses
   - Synthesize the best answer
   - Return the combined result

### Example Response Flow

```
Input Query → [GPT-4, Claude, Gemini] → Evaluation → Synthesis → Final Answer
```

### Advanced Configuration

Customize evaluation criteria in the workflow:

```python
# evaluation_config.py
CRITERIA = {
    "accuracy": 0.4,      # 40% weight
    "clarity": 0.3,       # 30% weight
    "completeness": 0.3   # 30% weight
}
```

### API Integration

Use the webhook trigger to integrate with your applications:

```bash
curl -X POST http://localhost:5678/webhook/llm-council \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the benefits of microservices?"}'
```

## 📁 Project Structure

```
llm-council/
├── workflows/              # n8n workflow definitions
│   └── llm-council.json   # Main council workflow
├── scripts/               # Evaluation and utility scripts
│   ├── evaluate.py       # Response evaluation logic
│   └── synthesize.py     # Answer synthesis
├── config/               # Configuration files
│   └── models.json      # Model-specific settings
├── docs/                # Documentation
│   └── IMPLEMENTATION_PLAN.md
├── tests/               # Test cases and examples
├── .env.example        # Environment variables template
└── README.md          # This file
```

## 🔧 Configuration

### Model Weights

Adjust how much each model influences the final answer:

```json
{
  "model_weights": {
    "gpt4": 0.35,
    "claude": 0.35,
    "gemini": 0.30
  }
}
```

### Evaluation Parameters

Customize what makes a "good" response:

```json
{
  "evaluation": {
    "min_length": 100,
    "max_length": 2000,
    "require_citations": false,
    "prefer_structured": true
  }
}
```

## 🎯 Use Cases

- **Research**: Get comprehensive answers by combining multiple AI perspectives
- **Content Creation**: Generate richer content with diverse model insights
- **Decision Making**: Evaluate options with multi-model consensus
- **Learning**: Understand topics through different explanatory approaches
- **Code Review**: Get varied feedback on code from different AI models

## 📊 Development Status

**Current Status**: ✅ Completed

The project has reached its initial completion milestone with all core features implemented and tested. The system successfully:
- Queries all three AI models in parallel
- Evaluates responses based on configurable criteria
- Synthesizes coherent, high-quality answers
- Provides a stable API for integration

## 🗺️ Future Enhancements

- [ ] Add support for additional AI models (LLaMA, Mistral, etc.)
- [ ] Implement response caching to reduce API costs
- [ ] Create a web UI for easier interaction
- [ ] Add conversation history and context management
- [ ] Develop analytics dashboard for response quality metrics
- [ ] Support for multi-turn conversations
- [ ] Integration with popular chat platforms (Slack, Discord)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built using [n8n](https://n8n.io) workflow automation platform
- Based on n8n template #11618
- Powered by OpenAI, Anthropic, and Google AI APIs

## 📧 Contact

For questions, suggestions, or issues, please open an issue on GitHub or contact the maintainers.

---

**Note**: Remember to keep your API keys secure and never commit them to version control. Always use environment variables or secure credential management systems.