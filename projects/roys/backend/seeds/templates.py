TEMPLATES = [
    {
        "name": "Standard 7-Section",
        "description": "Full SOP template with all standard sections",
        "sections": [
            {"number": "1", "title": "Purpose"},
            {"number": "2", "title": "Scope"},
            {"number": "3", "title": "Responsibilities"},
            {"number": "4", "title": "Definitions"},
            {"number": "5", "title": "Procedure"},
            {"number": "6", "title": "References"},
            {"number": "7", "title": "Revision History"},
        ],
        "is_default": True,
    },
    {
        "name": "Abbreviated 4-Section",
        "description": "Compact SOP template for simpler procedures",
        "sections": [
            {"number": "1", "title": "Purpose & Scope"},
            {"number": "2", "title": "Responsibilities"},
            {"number": "3", "title": "Procedure"},
            {"number": "4", "title": "References"},
        ],
        "is_default": False,
    },
    {
        "name": "Work Instruction",
        "description": "Step-by-step work instruction format",
        "sections": [
            {"number": "1", "title": "Objective"},
            {"number": "2", "title": "Materials & Equipment"},
            {"number": "3", "title": "Step-by-Step Instructions"},
            {"number": "4", "title": "Acceptance Criteria"},
        ],
        "is_default": False,
    },
]
