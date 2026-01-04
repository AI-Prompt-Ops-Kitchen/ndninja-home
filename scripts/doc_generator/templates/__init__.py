"""Documentation templates"""
from templates.readme_template import ReadmeTemplate


def get_template(doc_type):
    """
    Get template instance for specified doc type

    Args:
        doc_type: Type of documentation (README, API, ARCHITECTURE, REPORT)

    Returns:
        Template instance

    Raises:
        ValueError: If doc_type is not supported
    """
    template_map = {
        'README': ReadmeTemplate,
        # 'API': ApiTemplate,           # Future
        # 'ARCHITECTURE': ArchitectureTemplate,  # Future
        # 'REPORT': ReportTemplate,      # Future
    }

    if doc_type not in template_map:
        supported = ', '.join(template_map.keys())
        raise ValueError(
            f"Unsupported doc type: {doc_type}\n"
            f"Supported types: {supported}"
        )

    return template_map[doc_type]()
