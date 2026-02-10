"""README template for project documentation"""
from templates.base_template import BaseTemplate


class ReadmeTemplate(BaseTemplate):
    """Template for generating README.md documentation"""

    @property
    def required_sources(self):
        return ['db', 'git']

    @property
    def system_prompt(self):
        return """You are a technical documentation expert specializing in README files.

Generate clear, comprehensive, professional README documentation that includes:
- **Project Overview**: What the project does and why it exists
- **Key Features**: Bullet list of main capabilities
- **Tech Stack**: Technologies and languages used
- **Installation/Setup**: Step-by-step setup instructions
- **Usage**: How to use the project with examples
- **Project Structure**: Overview of directory organization
- **Development Status**: Current state and roadmap
- **Contributing**: Guidelines if applicable

Style guidelines:
- Use clear, concise language
- Include code blocks with proper syntax highlighting
- Use bullet points and numbered lists for readability
- Add badges if relevant (build status, version, etc.)
- Structure with proper markdown headers (##, ###)
- Keep it scannable and organized
- Be professional but friendly in tone

Format the output as a complete, production-ready README.md file."""

    def build_prompt(self, project, data):
        """Build prompt from project data and gathered sources"""
        git_data = data.get('git', {})
        db_data = data.get('db', {})

        # Extract git information
        git_available = git_data.get('available', False)
        if git_available:
            languages = ', '.join(git_data.get('languages', []))
            structure = git_data.get('structure', 'N/A')
            recent_commits = git_data.get('recent_commits', [])
            dependencies = git_data.get('dependencies', {})
            file_count = git_data.get('file_count', 0)

            commits_summary = f"{len(recent_commits)} recent commits"
            if recent_commits:
                latest_commit = recent_commits[0]
                commits_summary += f"\nLatest: {latest_commit['message']} ({latest_commit['date']})"
        else:
            languages = "Not available"
            structure = "Git repository not found"
            commits_summary = "N/A"
            dependencies = {}
            file_count = "Unknown"

        # Extract database information
        tasks_summary = db_data.get('tasks_summary', 'No tasks')
        tasks = db_data.get('tasks', [])
        related_docs = db_data.get('related_docs', [])
        knowledge_items = db_data.get('knowledge_items', [])

        # Build comprehensive prompt
        prompt = f"""Generate a comprehensive README.md for the following project:

# PROJECT INFORMATION

**Title**: {project['title']}
**Description**: {project.get('body', 'No description provided')[:800]}
**Status**: {project.get('status', 'Unknown')}
**Category**: {project.get('category', 'N/A')}

# CODEBASE ANALYSIS

**Programming Languages**: {languages}
**Total Files**: {file_count}

**Dependencies**:
{self._format_dependencies(dependencies)}

**Directory Structure**:
```
{structure}
```

**Git Activity**:
{commits_summary}

# PROJECT TASKS

{tasks_summary}

**Key Tasks**:
{self._format_tasks(tasks[:10])}

# RELATED DOCUMENTATION

{len(related_docs)} existing documentation files
{self._format_related_docs(related_docs)}

# KNOWLEDGE BASE

{len(knowledge_items)} related knowledge items
{self._format_knowledge(knowledge_items)}

---

Based on all the information above, generate a complete, professional README.md file.

Requirements:
1. Infer setup/installation steps from the dependencies and project structure
2. Create realistic usage examples based on the project description
3. Highlight key features extracted from tasks and description
4. Include a project structure section based on the directory tree
5. Add a development status section based on task completion
6. If there are many pending tasks, include a roadmap section
7. Make it comprehensive but concise - aim for 800-1200 words
8. Use proper markdown formatting throughout

Generate the complete README.md now:"""

        return prompt

    def _format_dependencies(self, deps):
        """Format dependency information"""
        if not deps:
            return "No dependency files found"

        formatted = []
        for lang, dep_list in deps.items():
            if lang == 'python' and dep_list:
                formatted.append(f"**Python** ({len(dep_list)} packages):")
                formatted.append("  " + ", ".join(dep_list[:10]))
            elif lang == 'node' and dep_list:
                main_deps = dep_list.get('dependencies', [])
                formatted.append(f"**Node.js** ({len(main_deps)} packages):")
                formatted.append("  " + ", ".join(main_deps[:10]))
            elif lang == 'go' and dep_list:
                formatted.append(f"**Go** ({len(dep_list)} modules):")
                formatted.append("  " + ", ".join(dep_list[:10]))

        return "\n".join(formatted) if formatted else "No dependencies found"

    def _format_tasks(self, tasks):
        """Format task list"""
        if not tasks:
            return "No active tasks"

        formatted = []
        for task in tasks[:10]:
            status_icon = "✅" if task['status'] == 'completed' else "⏳"
            priority = task.get('priority', 'medium')
            priority_badge = f"[{priority.upper()}]" if priority == 'high' else ""
            formatted.append(f"{status_icon} {priority_badge} {task['title']}")

        return "\n".join(formatted)

    def _format_related_docs(self, docs):
        """Format related documentation"""
        if not docs:
            return ""

        formatted = []
        for doc in docs[:5]:
            category = doc.get('category', 'Doc')
            formatted.append(f"- {category}: {doc['title']}")

        return "\n".join(formatted) if formatted else ""

    def _format_knowledge(self, knowledge):
        """Format knowledge items"""
        if not knowledge:
            return ""

        formatted = []
        for item in knowledge[:3]:
            title = item['title']
            body_preview = item.get('body', '')[:100]
            formatted.append(f"- {title}: {body_preview}...")

        return "\n".join(formatted) if formatted else ""
