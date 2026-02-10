-- Seed Data for Prompt Toolkit
-- 50 High-Quality Starter Prompts across 5 Categories
-- Author: Neurodivergent Ninja
-- Created: 2026-02-10

-- ============================================================================
-- SEED USER (System user for seed prompts)
-- ============================================================================

INSERT INTO users (id, email, name, avatar_url, bio) VALUES
('00000000-0000-0000-0000-000000000001', 'system@prompttoolkit.dev', 'Prompt Toolkit', NULL, 'Official seed prompts from Prompt Toolkit');

-- ============================================================================
-- MARKETING PROMPTS (10)
-- ============================================================================

-- 1. Cold Email Outreach
INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status, is_featured) VALUES
('10000000-0000-0000-0000-000000000001',
'Cold Email Outreach - B2B Sales',
'cold-email-b2b-sales',
'Professional cold email template for B2B sales outreach with personalization hooks',
'Write a cold email for [PRODUCT_NAME], a [PRODUCT_DESCRIPTION].

Target: [TARGET_ROLE] at [TARGET_COMPANY_TYPE] companies
Pain Point: [PAIN_POINT]
Value Proposition: [VALUE_PROP]

Tone: [TONE]
Length: [LENGTH] words

Include:
- Personalized opening hook
- Problem acknowledgment
- Solution introduction
- Social proof mention
- Clear CTA',
'marketing', 'intermediate', 'universal',
ARRAY['email', 'sales', 'b2b', 'outreach'],
'00000000-0000-0000-0000-000000000001', 'published', true);

INSERT INTO prompt_variables (prompt_id, name, label, helper_text, suggestions, required, variable_type, "order") VALUES
('10000000-0000-0000-0000-000000000001', 'PRODUCT_NAME', 'Product Name', 'Your product or service name', NULL, true, 'text', 1),
('10000000-0000-0000-0000-000000000001', 'PRODUCT_DESCRIPTION', 'Product Description', 'Brief description (1-2 sentences)', NULL, true, 'textarea', 2),
('10000000-0000-0000-0000-000000000001', 'TARGET_ROLE', 'Target Role', 'Decision maker role', ARRAY['CEO', 'CTO', 'VP Sales', 'Marketing Director'], true, 'select', 3),
('10000000-0000-0000-0000-000000000001', 'TARGET_COMPANY_TYPE', 'Company Type', 'Type of company', ARRAY['SaaS', 'E-commerce', 'Enterprise', 'Startup'], true, 'select', 4),
('10000000-0000-0000-0000-000000000001', 'PAIN_POINT', 'Pain Point', 'Specific problem they face', NULL, true, 'textarea', 5),
('10000000-0000-0000-0000-000000000001', 'VALUE_PROP', 'Value Proposition', 'How you solve their problem', NULL, true, 'textarea', 6),
('10000000-0000-0000-0000-000000000001', 'TONE', 'Tone', 'Email tone', ARRAY['professional', 'casual', 'friendly', 'authoritative'], true, 'select', 7),
('10000000-0000-0000-0000-000000000001', 'LENGTH', 'Length', 'Word count', ARRAY['100', '150', '200'], true, 'select', 8);

INSERT INTO prompt_dna (prompt_id, component_type, highlight_start, highlight_end, explanation, "order") VALUES
('10000000-0000-0000-0000-000000000001', 'persona', 0, 20, 'Sets clear context for B2B sales email generation', 1),
('10000000-0000-0000-0000-000000000001', 'constraints', 190, 240, 'Specifies tone and length requirements for professional communication', 2),
('10000000-0000-0000-0000-000000000001', 'format', 250, 330, 'Defines email structure with 5 key components for effective outreach', 3);

-- 2. Social Media Post - Product Launch
INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status) VALUES
('10000000-0000-0000-0000-000000000002',
'Social Media Post - Product Launch',
'social-media-product-launch',
'Engaging social media announcement for product launches across platforms',
'Create a [PLATFORM] post announcing the launch of [PRODUCT_NAME].

Product: [PRODUCT_DESCRIPTION]
Key Feature: [KEY_FEATURE]
Target Audience: [AUDIENCE]

Style: [STYLE]
Include: [INCLUDE_ELEMENTS]

Make it engaging, include relevant emojis, and end with a clear CTA.',
'marketing', 'beginner', 'universal',
ARRAY['social-media', 'product-launch', 'announcement'],
'00000000-0000-0000-0000-000000000001', 'published');

INSERT INTO prompt_variables (prompt_id, name, label, helper_text, suggestions, required, variable_type, "order") VALUES
('10000000-0000-0000-0000-000000000002', 'PLATFORM', 'Platform', 'Social media platform', ARRAY['Twitter/X', 'LinkedIn', 'Instagram', 'Facebook'], true, 'select', 1),
('10000000-0000-0000-0000-000000000002', 'PRODUCT_NAME', 'Product Name', NULL, NULL, true, 'text', 2),
('10000000-0000-0000-0000-000000000002', 'PRODUCT_DESCRIPTION', 'Product Description', 'What does it do?', NULL, true, 'textarea', 3),
('10000000-0000-0000-0000-000000000002', 'KEY_FEATURE', 'Key Feature', 'Most exciting feature', NULL, true, 'text', 4),
('10000000-0000-0000-0000-000000000002', 'AUDIENCE', 'Target Audience', NULL, ARRAY['developers', 'marketers', 'entrepreneurs', 'designers'], true, 'select', 5),
('10000000-0000-0000-0000-000000000002', 'STYLE', 'Style', 'Post style', ARRAY['hype/excitement', 'professional', 'casual/friendly', 'educational'], true, 'select', 6),
('10000000-0000-0000-0000-000000000002', 'INCLUDE_ELEMENTS', 'Include', 'What to include', ARRAY['statistics', 'testimonial', 'demo link', 'limited offer'], false, 'select', 7);

-- 3-10: Additional Marketing Prompts
INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status) VALUES
('10000000-0000-0000-0000-000000000003', 'SEO Blog Post Outline', 'seo-blog-post-outline', 'SEO-optimized blog post structure with keyword targeting', 'Create an SEO-optimized blog post outline for: [TOPIC]\n\nTarget Keyword: [KEYWORD]\nSearch Intent: [INTENT]\nWord Count: [WORD_COUNT]\n\nInclude: Title options (H1), H2 subheadings, key points, internal linking suggestions, and meta description.', 'marketing', 'intermediate', 'universal', ARRAY['seo', 'blog', 'content'], '00000000-0000-0000-0000-000000000001', 'published'),

('10000000-0000-0000-0000-000000000004', 'Facebook Ad Copy', 'facebook-ad-copy', 'High-converting Facebook ad copy with pain-agitate-solution framework', 'Write Facebook ad copy for [PRODUCT].\n\nTarget Audience: [AUDIENCE]\nPain Point: [PAIN]\nBenefit: [BENEFIT]\nOffer: [OFFER]\n\nUse pain-agitate-solution framework. Include emoji. Max 125 characters for primary text.', 'marketing', 'intermediate', 'universal', ARRAY['ads', 'facebook', 'ppc'], '00000000-0000-0000-0000-000000000001', 'published'),

('10000000-0000-0000-0000-000000000005', 'Product Landing Page Copy', 'landing-page-copy', 'Conversion-focused landing page copy with hero, features, and CTA', 'Write landing page copy for [PRODUCT].\n\nValue Prop: [VALUE_PROP]\nTarget Customer: [CUSTOMER]\nKey Features: [FEATURES]\nPrice Point: [PRICE]\n\nSections needed: Hero headline, subheadline, 3 benefit points, features section, testimonial placeholder, CTA.', 'marketing', 'advanced', 'universal', ARRAY['copywriting', 'landing-page', 'conversion'], '00000000-0000-0000-0000-000000000001', 'published'),

('10000000-0000-0000-0000-000000000006', 'Email Newsletter Template', 'email-newsletter-template', 'Engaging email newsletter with news, tips, and CTAs', 'Create an email newsletter for [COMPANY].\n\nTheme: [THEME]\nNews Item: [NEWS]\nTip/Resource: [TIP]\nPromo: [PROMO]\n\nTone: [TONE]\n\nInclude: catchy subject line, preview text, sections, and CTA button copy.', 'marketing', 'beginner', 'universal', ARRAY['email', 'newsletter', 'content'], '00000000-0000-0000-0000-000000000001', 'published'),

('10000000-0000-0000-0000-000000000007', 'Brand Voice Guidelines', 'brand-voice-guidelines', 'Define brand voice characteristics and writing examples', 'Create brand voice guidelines for [COMPANY].\n\nIndustry: [INDUSTRY]\nTarget Audience: [AUDIENCE]\nBrand Personality: [PERSONALITY]\nValues: [VALUES]\n\nDefine: Voice attributes (3-5), dos and don'ts, tone variations by context, example phrases.', 'marketing', 'advanced', 'universal', ARRAY['branding', 'voice', 'guidelines'], '00000000-0000-0000-0000-000000000001', 'published'),

('10000000-0000-0000-0000-000000000008', 'Press Release', 'press-release', 'Professional press release for company announcements', 'Write a press release for [ANNOUNCEMENT].\n\nCompany: [COMPANY]\nDate: [DATE]\nLocation: [LOCATION]\nQuote from: [SPOKESPERSON]\nKey Details: [DETAILS]\n\nFollow AP style. Include headline, dateline, boilerplate, and media contact.', 'marketing', 'intermediate', 'universal', ARRAY['pr', 'press-release', 'announcement'], '00000000-0000-0000-0000-000000000001', 'published'),

('10000000-0000-0000-0000-000000000009', 'Customer Case Study', 'customer-case-study', 'Compelling customer success story with before/after results', 'Write a case study for [CUSTOMER].\n\nIndustry: [INDUSTRY]\nChallenge: [CHALLENGE]\nSolution: [SOLUTION]\nResults: [RESULTS]\n\nStructure: Background, Challenge, Solution, Results (with metrics), Testimonial quote.', 'marketing', 'intermediate', 'universal', ARRAY['case-study', 'testimonial', 'sales'], '00000000-0000-0000-0000-000000000001', 'published'),

('10000000-0000-0000-0000-000000000010', 'Video Script - Explainer', 'video-script-explainer', '60-second explainer video script for products/services', 'Write a 60-second explainer video script for [PRODUCT].\n\nProblem: [PROBLEM]\nSolution: [SOLUTION]\nHow It Works: [STEPS]\nBenefit: [BENEFIT]\n\nInclude: Hook (0-5s), Problem (5-20s), Solution (20-45s), CTA (45-60s). Add scene descriptions.', 'marketing', 'advanced', 'universal', ARRAY['video', 'script', 'explainer'], '00000000-0000-0000-0000-000000000001', 'published');

-- ============================================================================
-- CODE PROMPTS (10)
-- ============================================================================

INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status, is_featured) VALUES
('20000000-0000-0000-0000-000000000001',
'Code Review Checklist',
'code-review-checklist',
'Comprehensive code review with best practices and security checks',
'Review the following [LANGUAGE] code for a [COMPONENT_TYPE]:

```[LANGUAGE]
[CODE]
```

Check for:
1. Code quality (readability, maintainability)
2. Performance issues
3. Security vulnerabilities
4. Best practices for [FRAMEWORK]
5. Error handling
6. Test coverage suggestions

Provide specific feedback with line references.',
'code', 'intermediate', 'claude',
ARRAY['code-review', 'quality', 'security'],
'00000000-0000-0000-0000-000000000001', 'published', true);

INSERT INTO prompt_variables (prompt_id, name, label, helper_text, suggestions, required, variable_type, "order") VALUES
('20000000-0000-0000-0000-000000000001', 'LANGUAGE', 'Programming Language', NULL, ARRAY['JavaScript', 'Python', 'TypeScript', 'Go', 'Rust', 'Java'], true, 'select', 1),
('20000000-0000-0000-0000-000000000001', 'COMPONENT_TYPE', 'Component Type', NULL, ARRAY['API endpoint', 'React component', 'database query', 'utility function', 'class', 'module'], true, 'select', 2),
('20000000-0000-0000-0000-000000000001', 'CODE', 'Code to Review', 'Paste your code here', NULL, true, 'textarea', 3),
('20000000-0000-0000-0000-000000000001', 'FRAMEWORK', 'Framework', 'Optional framework context', ARRAY['React', 'Vue', 'Django', 'Flask', 'Express', 'FastAPI', 'None'], false, 'select', 4);

INSERT INTO prompt_dna (prompt_id, component_type, highlight_start, highlight_end, explanation, "order") VALUES
('20000000-0000-0000-0000-000000000001', 'context', 0, 60, 'Provides language and component type for targeted review', 1),
('20000000-0000-0000-0000-000000000001', 'constraints', 95, 235, 'Defines 6 specific review criteria for comprehensive analysis', 2);

-- 2-10: Additional Code Prompts
INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status) VALUES
('20000000-0000-0000-0000-000000000002', 'API Endpoint Generator', 'api-endpoint-generator', 'Generate RESTful API endpoint with validation and error handling', 'Generate a [METHOD] API endpoint in [FRAMEWORK] for [RESOURCE].\n\nEndpoint: /api/[ENDPOINT]\nAuth: [AUTH_TYPE]\nValidation: [VALIDATION_RULES]\nResponse Format: [FORMAT]\n\nInclude: route handler, input validation, error handling, response structure, and JSDoc/docstring.', 'code', 'intermediate', 'claude', ARRAY['api', 'backend', 'rest'], '00000000-0000-0000-0000-000000000001', 'published'),

('20000000-0000-0000-0000-000000000003', 'SQL Query Optimizer', 'sql-query-optimizer', 'Optimize SQL queries for performance', 'Optimize this SQL query:\n\n```sql\n[QUERY]\n```\n\nDatabase: [DATABASE]\nTable Size: [SIZE]\nCurrent Performance: [PERFORMANCE]\n\nProvide: optimized query, explanation of changes, index recommendations, and estimated improvement.', 'code', 'advanced', 'claude', ARRAY['sql', 'database', 'optimization'], '00000000-0000-0000-0000-000000000001', 'published'),

('20000000-0000-0000-0000-000000000004', 'React Component Builder', 'react-component-builder', 'Build React component with TypeScript and best practices', 'Create a React component: [COMPONENT_NAME]\n\nPurpose: [PURPOSE]\nProps: [PROPS]\nState: [STATE]\nStyling: [STYLING_APPROACH]\n\nRequirements: TypeScript, functional component, proper prop types, accessibility, error boundaries if needed.', 'code', 'intermediate', 'claude', ARRAY['react', 'typescript', 'frontend'], '00000000-0000-0000-0000-000000000001', 'published'),

('20000000-0000-0000-0000-000000000005', 'Unit Test Generator', 'unit-test-generator', 'Generate comprehensive unit tests with edge cases', 'Generate unit tests for this [LANGUAGE] function:\n\n```[LANGUAGE]\n[FUNCTION_CODE]\n```\n\nTest Framework: [FRAMEWORK]\nCoverage Needed: [COVERAGE]\n\nInclude: happy path, edge cases, error cases, mocks if needed. Target [COVERAGE]% coverage.', 'code', 'intermediate', 'claude', ARRAY['testing', 'unit-tests', 'tdd'], '00000000-0000-0000-0000-000000000001', 'published'),

('20000000-0000-0000-0000-000000000006', 'Regex Pattern Builder', 'regex-pattern-builder', 'Build and explain regex patterns for validation', 'Create a regex pattern to match: [REQUIREMENT]\n\nLanguage: [LANGUAGE]\nValidation Rules: [RULES]\nExamples: [EXAMPLES]\n\nProvide: regex pattern, explanation, test cases (valid/invalid), and code snippet for implementation.', 'code', 'beginner', 'universal', ARRAY['regex', 'validation', 'patterns'], '00000000-0000-0000-0000-000000000001', 'published'),

('20000000-0000-0000-0000-000000000007', 'Docker Configuration', 'docker-configuration', 'Generate Dockerfile and docker-compose for applications', 'Create Docker configuration for [APP_TYPE] application.\n\nLanguage/Framework: [STACK]\nServices: [SERVICES]\nEnvironment: [ENVIRONMENT]\nPorts: [PORTS]\n\nInclude: Dockerfile (multi-stage if appropriate), docker-compose.yml, .dockerignore, and deployment notes.', 'code', 'intermediate', 'claude', ARRAY['docker', 'devops', 'deployment'], '00000000-0000-0000-0000-000000000001', 'published'),

('20000000-0000-0000-0000-000000000008', 'Git Commit Message', 'git-commit-message', 'Generate conventional commit messages from code changes', 'Generate a commit message for these changes:\n\nType: [TYPE]\nScope: [SCOPE]\nSummary: [SUMMARY]\nBreaking Changes: [BREAKING]\n\nFollow Conventional Commits format. Explain WHY, not WHAT. Keep under 72 characters for first line.', 'code', 'beginner', 'universal', ARRAY['git', 'commit', 'version-control'], '00000000-0000-0000-0000-000000000001', 'published'),

('20000000-0000-0000-0000-000000000009', 'Algorithm Explainer', 'algorithm-explainer', 'Explain algorithms with code examples and complexity analysis', 'Explain the [ALGORITHM] algorithm.\n\nContext: [USE_CASE]\nLanguage: [LANGUAGE]\n\nProvide: concept explanation, code implementation, time/space complexity, visual example, real-world use cases.', 'code', 'intermediate', 'claude', ARRAY['algorithms', 'education', 'explanation'], '00000000-0000-0000-0000-000000000001', 'published'),

('20000000-0000-0000-0000-000000000010', 'Code Documentation', 'code-documentation', 'Generate comprehensive documentation for code', 'Document this [LANGUAGE] code:\n\n```[LANGUAGE]\n[CODE]\n```\n\nStyle: [DOC_STYLE]\nAudience: [AUDIENCE]\n\nInclude: purpose, parameters, return values, exceptions, examples, complexity notes, and any gotchas.', 'code', 'beginner', 'universal', ARRAY['documentation', 'comments', 'jsdoc'], '00000000-0000-0000-0000-000000000001', 'published');

-- ============================================================================
-- WRITING PROMPTS (10)
-- ============================================================================

INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status, is_featured) VALUES
('30000000-0000-0000-0000-000000000001',
'Blog Post Writer',
'blog-post-writer',
'Comprehensive blog post with SEO optimization and engaging content',
'Write a blog post about [TOPIC].

Target Audience: [AUDIENCE]
Word Count: [WORD_COUNT]
Tone: [TONE]
Keywords: [KEYWORDS]

Include:
- Engaging introduction with hook
- Clear subheadings (H2/H3)
- Actionable insights
- Examples or statistics
- Conclusion with CTA

Optimize for SEO and readability.',
'writing', 'intermediate', 'universal',
ARRAY['blog', 'content-writing', 'seo'],
'00000000-0000-0000-0000-000000000001', 'published', true);

INSERT INTO prompt_variables (prompt_id, name, label, helper_text, suggestions, required, variable_type, "order") VALUES
('30000000-0000-0000-0000-000000000001', 'TOPIC', 'Topic', 'Main subject of the blog post', NULL, true, 'text', 1),
('30000000-0000-0000-0000-000000000001', 'AUDIENCE', 'Target Audience', NULL, ARRAY['beginners', 'intermediate', 'experts', 'general public'], true, 'select', 2),
('30000000-0000-0000-0000-000000000001', 'WORD_COUNT', 'Word Count', NULL, ARRAY['500', '1000', '1500', '2000'], true, 'select', 3),
('30000000-0000-0000-0000-000000000001', 'TONE', 'Tone', NULL, ARRAY['professional', 'casual', 'friendly', 'authoritative', 'conversational'], true, 'select', 4),
('30000000-0000-0000-0000-000000000001', 'KEYWORDS', 'SEO Keywords', 'Comma-separated keywords', NULL, false, 'text', 5);

-- 2-10: Additional Writing Prompts
INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status) VALUES
('30000000-0000-0000-0000-000000000002', 'Professional Email', 'professional-email', 'Business email for various professional situations', 'Write a professional email:\n\nPurpose: [PURPOSE]\nRecipient: [RECIPIENT]\nContext: [CONTEXT]\nDesired Action: [ACTION]\nTone: [TONE]\n\nInclude appropriate greeting, clear subject line, and professional closing.', 'writing', 'beginner', 'universal', ARRAY['email', 'business', 'communication'], '00000000-0000-0000-0000-000000000001', 'published'),

('30000000-0000-0000-0000-000000000003', 'Story Outline', 'story-outline', 'Creative story outline with plot structure and character arcs', 'Create a story outline:\n\nGenre: [GENRE]\nPremise: [PREMISE]\nProtagonist: [PROTAGONIST]\nConflict: [CONFLICT]\nSetting: [SETTING]\n\nProvide: 3-act structure, character arcs, key plot points, potential themes, and resolution options.', 'writing', 'intermediate', 'universal', ARRAY['creative-writing', 'storytelling', 'fiction'], '00000000-0000-0000-0000-000000000001', 'published'),

('30000000-0000-0000-0000-000000000004', 'LinkedIn Post', 'linkedin-post', 'Engaging LinkedIn post for professional networking', 'Write a LinkedIn post about [TOPIC].\n\nGoal: [GOAL]\nAudience: [AUDIENCE]\nLength: [LENGTH]\nStyle: [STYLE]\n\nInclude hook, personal insight or story, value/lesson, and engagement question. Format for readability.', 'writing', 'beginner', 'universal', ARRAY['linkedin', 'professional', 'social-media'], '00000000-0000-0000-0000-000000000001', 'published'),

('30000000-0000-0000-0000-000000000005', 'Technical Documentation', 'technical-documentation', 'Clear technical documentation for products or APIs', 'Write technical documentation for [PRODUCT/API].\n\nAudience: [AUDIENCE]\nComplexity: [COMPLEXITY]\nSections: [SECTIONS]\n\nInclude: overview, prerequisites, step-by-step guide, code examples, troubleshooting, and FAQs.', 'writing', 'advanced', 'claude', ARRAY['technical-writing', 'documentation', 'tutorial'], '00000000-0000-0000-0000-000000000001', 'published'),

('30000000-0000-0000-0000-000000000006', 'Product Description', 'product-description', 'Compelling product description for e-commerce', 'Write a product description for [PRODUCT].\n\nCategory: [CATEGORY]\nKey Features: [FEATURES]\nTarget Customer: [CUSTOMER]\nPrice Point: [PRICE_RANGE]\n\nInclude: headline, bullet points, benefits (not just features), and urgency element. 150-200 words.', 'writing', 'beginner', 'universal', ARRAY['ecommerce', 'product', 'copywriting'], '00000000-0000-0000-0000-000000000001', 'published'),

('30000000-0000-0000-0000-000000000007', 'Speech Writer', 'speech-writer', 'Engaging speech for various occasions', 'Write a speech for [OCCASION].\n\nSpeaker: [SPEAKER_ROLE]\nAudience: [AUDIENCE]\nDuration: [DURATION] minutes\nKey Message: [MESSAGE]\nTone: [TONE]\n\nStructure: opening hook, main points (3-5), stories/examples, and memorable closing.', 'writing', 'advanced', 'universal', ARRAY['speech', 'public-speaking', 'presentation'], '00000000-0000-0000-0000-000000000001', 'published'),

('30000000-0000-0000-0000-000000000008', 'Resume Bullet Points', 'resume-bullet-points', 'Achievement-focused resume bullet points with metrics', 'Write resume bullet points for [JOB_TITLE].\n\nResponsibilities: [RESPONSIBILITIES]\nAchievements: [ACHIEVEMENTS]\nSkills Used: [SKILLS]\n\nUse action verbs, quantify results, follow STAR method. 3-5 bullets per role.', 'writing', 'intermediate', 'universal', ARRAY['resume', 'career', 'job-search'], '00000000-0000-0000-0000-000000000001', 'published'),

('30000000-0000-0000-0000-000000000009', 'Podcast Script', 'podcast-script', 'Conversational podcast episode script with structure', 'Write a podcast script:\n\nTopic: [TOPIC]\nFormat: [FORMAT]\nLength: [LENGTH] minutes\nGuest: [GUEST]\nKey Points: [POINTS]\n\nInclude: intro music cue, host intro, topic introduction, segments, questions, transitions, outro with CTA.', 'writing', 'intermediate', 'universal', ARRAY['podcast', 'script', 'audio'], '00000000-0000-0000-0000-000000000001', 'published'),

('30000000-0000-0000-0000-000000000010', 'Grant Proposal', 'grant-proposal', 'Structured grant proposal with problem statement and budget', 'Write a grant proposal for [PROJECT].\n\nOrganization: [ORGANIZATION]\nAmount Requested: [AMOUNT]\nPurpose: [PURPOSE]\nImpact: [IMPACT]\n\nSections: Executive summary, need statement, project description, budget, evaluation plan, and sustainability.', 'writing', 'advanced', 'universal', ARRAY['grant', 'nonprofit', 'funding'], '00000000-0000-0000-0000-000000000001', 'published');

-- ============================================================================
-- RESEARCH PROMPTS (10)
-- ============================================================================

INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status, is_featured) VALUES
('40000000-0000-0000-0000-000000000001',
'Research Summary',
'research-summary',
'Comprehensive research summary with sources and key findings',
'Summarize research on [TOPIC].

Scope: [SCOPE]
Key Questions: [QUESTIONS]
Sources: [SOURCES]
Depth: [DEPTH]

Provide:
- Executive summary
- Key findings (bullet points)
- Methodology notes
- Conflicting viewpoints if any
- Implications
- Further research suggestions

Include source citations.',
'research', 'intermediate', 'claude',
ARRAY['research', 'summary', 'analysis'],
'00000000-0000-0000-0000-000000000001', 'published', true);

INSERT INTO prompt_variables (prompt_id, name, label, helper_text, suggestions, required, variable_type, "order") VALUES
('40000000-0000-0000-0000-000000000001', 'TOPIC', 'Research Topic', NULL, NULL, true, 'text', 1),
('40000000-0000-0000-0000-000000000001', 'SCOPE', 'Scope', NULL, ARRAY['broad overview', 'focused analysis', 'specific question'], true, 'select', 2),
('40000000-0000-0000-0000-000000000001', 'QUESTIONS', 'Key Questions', 'What are you trying to answer?', NULL, true, 'textarea', 3),
('40000000-0000-0000-0000-000000000001', 'SOURCES', 'Source Types', NULL, ARRAY['academic papers', 'industry reports', 'news articles', 'government data', 'mixed'], true, 'select', 4),
('40000000-0000-0000-0000-000000000001', 'DEPTH', 'Analysis Depth', NULL, ARRAY['high-level', 'detailed', 'comprehensive'], true, 'select', 5);

-- 2-10: Additional Research Prompts
INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status) VALUES
('40000000-0000-0000-0000-000000000002', 'Competitive Analysis', 'competitive-analysis', 'Comprehensive competitive analysis framework', 'Analyze competitors for [COMPANY/PRODUCT].\n\nIndustry: [INDUSTRY]\nCompetitors: [COMPETITORS]\nDimensions: [DIMENSIONS]\n\nProvide: competitive matrix, SWOT for each, market positioning, pricing comparison, feature gaps, and strategic recommendations.', 'research', 'advanced', 'claude', ARRAY['competitive-analysis', 'market-research', 'business'], '00000000-0000-0000-0000-000000000001', 'published'),

('40000000-0000-0000-0000-000000000003', 'Literature Review', 'literature-review', 'Academic literature review with synthesis', 'Conduct a literature review on [TOPIC].\n\nField: [FIELD]\nTime Period: [PERIOD]\nFocus: [FOCUS]\n\nProvide: thematic synthesis, key authors/papers, theoretical frameworks, research gaps, and future directions. Use academic tone.', 'research', 'expert', 'claude', ARRAY['academic', 'literature-review', 'synthesis'], '00000000-0000-0000-0000-000000000001', 'published'),

('40000000-0000-0000-0000-000000000004', 'Market Research Summary', 'market-research-summary', 'Market research synthesis with trends and insights', 'Summarize market research for [MARKET].\n\nIndustry: [INDUSTRY]\nGeography: [GEOGRAPHY]\nTime Frame: [TIMEFRAME]\nMetrics: [METRICS]\n\nInclude: market size, growth trends, key players, customer segments, opportunities, and threats.', 'research', 'intermediate', 'claude', ARRAY['market-research', 'trends', 'business-intelligence'], '00000000-0000-0000-0000-000000000001', 'published'),

('40000000-0000-0000-0000-000000000005', 'Data Analysis Narrative', 'data-analysis-narrative', 'Transform data findings into compelling narrative', 'Create a narrative from this data:\n\nData Set: [DATASET_DESCRIPTION]\nKey Findings: [FINDINGS]\nAudience: [AUDIENCE]\nPurpose: [PURPOSE]\n\nTransform into story: context, insights, visualizations needed, implications, and recommendations.', 'research', 'intermediate', 'claude', ARRAY['data-analysis', 'storytelling', 'insights'], '00000000-0000-0000-0000-000000000001', 'published'),

('40000000-0000-0000-0000-000000000006', 'Survey Question Designer', 'survey-question-designer', 'Design effective survey questions to avoid bias', 'Design survey questions for [RESEARCH_GOAL].\n\nTarget Respondents: [RESPONDENTS]\nKey Topics: [TOPICS]\nSurvey Length: [LENGTH]\nQuestion Types: [TYPES]\n\nProvide: question text, response options, logic flow, and bias checks. Aim for [LENGTH] minutes completion.', 'research', 'intermediate', 'universal', ARRAY['survey', 'research-methods', 'ux-research'], '00000000-0000-0000-0000-000000000001', 'published'),

('40000000-0000-0000-0000-000000000007', 'Trend Analysis', 'trend-analysis', 'Identify and analyze emerging trends', 'Analyze trends in [INDUSTRY/DOMAIN].\n\nTime Period: [PERIOD]\nData Sources: [SOURCES]\nFocus Areas: [AREAS]\n\nIdentify: emerging trends, driving forces, early signals, potential impact, and timeline predictions.', 'research', 'advanced', 'claude', ARRAY['trends', 'forecasting', 'analysis'], '00000000-0000-0000-0000-000000000001', 'published'),

('40000000-0000-0000-0000-000000000008', 'User Research Synthesis', 'user-research-synthesis', 'Synthesize user research into actionable insights', 'Synthesize user research for [PRODUCT].\n\nResearch Methods: [METHODS]\nKey Findings: [FINDINGS]\nUser Segments: [SEGMENTS]\n\nProvide: user personas, pain points, needs, behavioral patterns, design implications, and priority recommendations.', 'research', 'intermediate', 'claude', ARRAY['user-research', 'ux', 'personas'], '00000000-0000-0000-0000-000000000001', 'published'),

('40000000-0000-0000-0000-000000000009', 'SWOT Analysis', 'swot-analysis', 'Comprehensive SWOT analysis framework', 'Conduct SWOT analysis for [SUBJECT].\n\nContext: [CONTEXT]\nGoal: [GOAL]\nTimeframe: [TIMEFRAME]\n\nAnalyze: Strengths (internal positives), Weaknesses (internal negatives), Opportunities (external positives), Threats (external negatives). Provide strategic recommendations.', 'research', 'beginner', 'universal', ARRAY['swot', 'strategy', 'analysis'], '00000000-0000-0000-0000-000000000001', 'published'),

('40000000-0000-0000-0000-000000000010', 'Feasibility Study', 'feasibility-study', 'Evaluate project feasibility across dimensions', 'Conduct a feasibility study for [PROJECT].\n\nObjective: [OBJECTIVE]\nConstraints: [CONSTRAINTS]\nResources: [RESOURCES]\n\nEvaluate: technical feasibility, economic viability, legal considerations, operational requirements, schedule, and risk assessment. Provide go/no-go recommendation.', 'research', 'advanced', 'claude', ARRAY['feasibility', 'project-management', 'analysis'], '00000000-0000-0000-0000-000000000001', 'published');

-- ============================================================================
-- PERSONAL PROMPTS (10)
-- ============================================================================

INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status, is_featured) VALUES
('50000000-0000-0000-0000-000000000001',
'Career Development Plan',
'career-development-plan',
'Personalized career development plan with actionable steps',
'Create a career development plan:

Current Role: [CURRENT_ROLE]
Goal Role: [GOAL_ROLE]
Timeline: [TIMELINE]
Strengths: [STRENGTHS]
Gaps: [GAPS]

Provide:
- Skill development roadmap
- Learning resources
- Networking strategies
- Milestone timeline
- Success metrics',
'personal', 'beginner', 'universal',
ARRAY['career', 'professional-development', 'goals'],
'00000000-0000-0000-0000-000000000001', 'published', true);

INSERT INTO prompt_variables (prompt_id, name, label, helper_text, suggestions, required, variable_type, "order") VALUES
('50000000-0000-0000-0000-000000000001', 'CURRENT_ROLE', 'Current Role', NULL, NULL, true, 'text', 1),
('50000000-0000-0000-0000-000000000001', 'GOAL_ROLE', 'Goal Role', 'Where do you want to be?', NULL, true, 'text', 2),
('50000000-0000-0000-0000-000000000001', 'TIMELINE', 'Timeline', NULL, ARRAY['3 months', '6 months', '1 year', '2 years', '5 years'], true, 'select', 3),
('50000000-0000-0000-0000-000000000001', 'STRENGTHS', 'Current Strengths', 'Your skills and experience', NULL, true, 'textarea', 4),
('50000000-0000-0000-0000-000000000001', 'GAPS', 'Skill Gaps', 'What do you need to learn?', NULL, true, 'textarea', 5);

-- 2-10: Additional Personal Prompts
INSERT INTO prompts (id, title, slug, description, template, category, skill_level, ai_model, tags, author_id, status) VALUES
('50000000-0000-0000-0000-000000000002', 'Weekly Review Template', 'weekly-review-template', 'Structured weekly reflection and planning', 'Weekly Review:\n\nWeek of: [DATE]\nKey Accomplishments: [ACCOMPLISHMENTS]\nChallenges: [CHALLENGES]\nLearnings: [LEARNINGS]\nNext Week Priorities: [PRIORITIES]\n\nReflect on: what worked, what didn''t, adjustments needed. Set 3-5 priorities for next week.', 'personal', 'beginner', 'universal', ARRAY['productivity', 'reflection', 'planning'], '00000000-0000-0000-0000-000000000001', 'published'),

('50000000-0000-0000-0000-000000000003', 'Decision Making Framework', 'decision-making-framework', 'Structured approach to important decisions', 'Help me decide: [DECISION]\n\nOptions: [OPTIONS]\nFactors: [FACTORS]\nConstraints: [CONSTRAINTS]\nStakeholders: [STAKEHOLDERS]\n\nProvide: pros/cons matrix, weighted decision criteria, risk analysis, recommendation, and implementation steps.', 'personal', 'intermediate', 'claude', ARRAY['decision-making', 'analysis', 'planning'], '00000000-0000-0000-0000-000000000001', 'published'),

('50000000-0000-0000-0000-000000000004', 'Learning Plan', 'learning-plan', 'Personalized learning plan for new skills', 'Create a learning plan for [SKILL].\n\nCurrent Level: [LEVEL]\nGoal: [GOAL]\nTime Available: [TIME]\nLearning Style: [STYLE]\n\nProvide: curriculum outline, resources (free/paid), practice projects, milestones, and evaluation criteria.', 'personal', 'beginner', 'universal', ARRAY['learning', 'skills', 'education'], '00000000-0000-0000-0000-000000000001', 'published'),

('50000000-0000-0000-0000-000000000005', 'Goal Setting - SMART', 'goal-setting-smart', 'Convert vague goals into SMART goals', 'Turn this goal into SMART format: [GOAL]\n\nContext: [CONTEXT]\nWhy: [WHY]\nSuccess Looks Like: [SUCCESS]\n\nMake it: Specific, Measurable, Achievable, Relevant, Time-bound. Include action steps and accountability measures.', 'personal', 'beginner', 'universal', ARRAY['goals', 'planning', 'smart-goals'], '00000000-0000-0000-0000-000000000001', 'published'),

('50000000-0000-0000-0000-000000000006', 'Morning Routine Designer', 'morning-routine-designer', 'Design optimal morning routine based on goals', 'Design a morning routine:\n\nWake Time: [WAKE_TIME]\nMorning Duration: [DURATION]\nGoals: [GOALS]\nConstraints: [CONSTRAINTS]\nEnergy Level: [ENERGY]\n\nProvide: time-blocked routine, habit stacking suggestions, flexibility options, and first-week implementation tips.', 'personal', 'beginner', 'universal', ARRAY['habits', 'routine', 'productivity'], '00000000-0000-0000-0000-000000000001', 'published'),

('50000000-0000-0000-0000-000000000007', 'Conflict Resolution', 'conflict-resolution', 'Navigate interpersonal conflicts constructively', 'Help resolve this conflict:\n\nSituation: [SITUATION]\nParties: [PARTIES]\nYour Role: [ROLE]\nDesired Outcome: [OUTCOME]\n\nProvide: perspective analysis, communication scripts, de-escalation strategies, and win-win solutions.', 'personal', 'intermediate', 'claude', ARRAY['communication', 'conflict', 'relationships'], '00000000-0000-0000-0000-000000000001', 'published'),

('50000000-0000-0000-0000-000000000008', 'Budget Planner', 'budget-planner', 'Personal budget planning and optimization', 'Create a monthly budget:\n\nIncome: [INCOME]\nFixed Expenses: [FIXED]\nVariable Expenses: [VARIABLE]\nSavings Goal: [SAVINGS]\nFinancial Goals: [GOALS]\n\nProvide: categorized budget, savings strategy, expense optimization suggestions, and emergency fund plan.', 'personal', 'beginner', 'universal', ARRAY['finance', 'budgeting', 'planning'], '00000000-0000-0000-0000-000000000001', 'published'),

('50000000-0000-0000-0000-000000000009', 'Difficult Conversation Prep', 'difficult-conversation-prep', 'Prepare for challenging conversations', 'Prepare for conversation about: [TOPIC]\n\nWith: [PERSON]\nContext: [CONTEXT]\nYour Goal: [GOAL]\nConcerns: [CONCERNS]\n\nProvide: conversation structure, opening lines, key points, empathy phrases, boundary statements, and de-escalation strategies.', 'personal', 'intermediate', 'claude', ARRAY['communication', 'relationships', 'conflict'], '00000000-0000-0000-0000-000000000001', 'published'),

('50000000-0000-0000-0000-000000000010', 'Thank You Note', 'thank-you-note', 'Heartfelt thank you messages for various occasions', 'Write a thank you note:\n\nRecipient: [RECIPIENT]\nOccasion: [OCCASION]\nWhat They Did: [ACTION]\nImpact: [IMPACT]\nTone: [TONE]\n\nMake it sincere, specific, and memorable. Include personal touch.', 'personal', 'beginner', 'universal', ARRAY['gratitude', 'communication', 'relationships'], '00000000-0000-0000-0000-000000000001', 'published');
