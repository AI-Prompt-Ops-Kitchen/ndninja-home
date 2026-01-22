```markdown
# Documentation Generator

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

> Automated documentation generation system that creates comprehensive, professional documentation by analyzing your project data, codebase, and tasks.

## Overview

Documentation Generator is an intelligent automation tool that eliminates the tedious task of writing project documentation. By analyzing your workspace database, git repository, and project tasks, it automatically generates polished, professional README files and other documentation formats using Claude AI.

The system combines multiple data sources to create contextually rich documentation that accurately represents your project's current state, features, and structure.

## ✨ Key Features

- **🤖 AI-Powered Generation**: Leverages Claude API for intelligent, context-aware documentation
- **📊 Multi-Source Analysis**: Combines workspace database, git history, and task management data
- **📝 Template-Based System**: Customizable templates for consistent documentation style
- **🎨 Enhanced Markdown**: Supports callouts, highlights, and rich formatting
- **📤 Multiple Output Formats**: Generate local README files or push directly to Craft documents
- **🔍 Codebase Intelligence**: Analyzes project structure, dependencies, and programming languages
- **📈 Task Integration**: Incorporates project status, roadmap, and task completion metrics
- **🔄 Automatic Updates**: Keep documentation in sync with project evolution

## 🛠️ Tech Stack

- **AI/ML**: Claude API (Anthropic)
- **Languages**: Python (primary), Shell scripting
- **Data Sources**: Git, SQLite/PostgreSQL (workspace DB), Markdown
- **Output Formats**: Markdown, Craft documents
- **APIs**: Claude API, Craft API (optional)

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Git installed and configured
- Claude API key from Anthropic
- (Optional) Craft account for document export

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/documentation-generator.git
   cd documentation-generator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```env
   CLAUDE_API_KEY=your_claude_api_key_here
   WORKSPACE_DB_PATH=/path/to/your/workspace.db
   CRAFT_API_TOKEN=your_craft_token_here  # Optional
   ```

4. **Verify installation**
   ```bash
   python docgen.py --version
   ```

## 🚀 Usage

### Basic Documentation Generation

Generate a README for your current project:

```bash
python docgen.py --project-path /path/to/your/project
```

### Advanced Options

**Specify output format:**
```bash
# Generate local README.md
python docgen.py --project-path ./my-project --output local

# Push to Craft document
python docgen.py --project-path ./my-project --output craft --craft-space "Engineering"
```

**Use custom templates:**
```bash
python docgen.py --project-path ./my-project --template ./templates/detailed.md
```

**Include specific data sources:**
```bash
# Only analyze git history
python docgen.py --project-path ./my-project --sources git

# Combine workspace DB and git analysis
python docgen.py --project-path ./my-project --sources workspace,git,tasks
```

### Example Output

The generator creates documentation with sections including:

- Project overview and purpose
- Feature highlights with visual indicators
- Technology stack breakdown
- Installation and setup instructions
- Usage examples with code blocks
- Project structure visualization
- Development status and roadmap
- Contributing guidelines

### Python API

Use Documentation Generator programmatically:

```python
from docgen import DocumentationGenerator

# Initialize generator
generator = DocumentationGenerator(
    claude_api_key="your_api_key",
    workspace_db="./workspace.db"
)

# Generate documentation
result = generator.generate(
    project_path="./my-project",
    output_format="local",
    template="default"
)

print(f"Documentation generated: {result.output_path}")
```

## 📁 Project Structure

```
documentation-generator/
├── docgen.py              # Main CLI entry point
├── core/
│   ├── analyzer.py        # Project analysis engine
│   ├── generator.py       # Documentation generation logic
│   └── claude_client.py   # Claude API integration
├── sources/
│   ├── git_analyzer.py    # Git repository analysis
│   ├── workspace_db.py    # Workspace database reader
│   └── task_parser.py     # Task management integration
├── templates/
│   ├── default.md         # Default README template
│   ├── detailed.md        # Comprehensive template
│   └── minimal.md         # Minimal template
├── formatters/
│   ├── markdown.py        # Markdown formatting utilities
│   └── craft_export.py    # Craft document exporter
├── tests/
│   └── test_*.py          # Unit tests
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🎯 Development Status

**Current Version**: 1.0.0 (Active Development)

The project is actively maintained and fully functional. The core documentation generation pipeline is stable and production-ready.

### Completed Features
- ✅ Multi-source data gathering
- ✅ Claude API integration
- ✅ Template-based generation
- ✅ Local file output
- ✅ Enhanced markdown support
- ✅ Git analysis integration

### Roadmap

- 🔄 Real-time documentation updates via file watchers
- 🔄 Support for additional AI models (GPT-4, Gemini)
- 🔄 Interactive CLI with project selection
- 🔄 Documentation versioning and history
- 🔄 Multi-language documentation generation
- 🔄 API documentation from code comments
- 🔄 Visual diagram generation

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows the project's coding standards and includes appropriate tests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Powered by [Claude AI](https://www.anthropic.com/claude) from Anthropic
- Inspired by the need for always-current project documentation
- Built for developers who value automation

## 📧 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/documentation-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/documentation-generator/discussions)
- **Email**: support@docgen.dev

---

**Made with ❤️ by developers, for developers**

*Keep your documentation fresh, accurate, and comprehensive - automatically.*
```