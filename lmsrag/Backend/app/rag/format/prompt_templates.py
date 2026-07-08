from app.rag.format.types import OutputFormat

class OneShotExample:
    def __init__(self, userQuery: str, expectedOutput: str):
        self.userQuery = userQuery
        self.expectedOutput = expectedOutput

class FormatTemplate:
    def __init__(self, format: OutputFormat, systemInstructions: str, formatRules: list, validationHints: list, oneShot: OneShotExample = None):
        self.format = format
        self.systemInstructions = systemInstructions
        self.formatRules = formatRules
        self.validationHints = validationHints
        self.oneShot = oneShot

class PromptTemplateBuilder:
    BASE_INSTRUCTIONS = """You are an intelligent teaching assistant for a Learning Management System.
Your task is to answer the student's question using the provided context."""

    COMPLIANCE_WARNING = """
CRITICAL: You MUST follow the specified format EXACTLY. Failure to comply will require regeneration."""

    def get_template(self, format: OutputFormat) -> FormatTemplate:
        f_val = format.value if isinstance(format, OutputFormat) else format
        if f_val == OutputFormat.TABLE.value:
            return self.get_table_template()
        elif f_val == OutputFormat.LIST.value:
            return self.get_list_template()
        elif f_val == OutputFormat.JSON.value:
            return self.get_json_template()
        elif f_val == OutputFormat.SUMMARY.value:
            return self.get_summary_template()
        elif f_val == OutputFormat.STEPS.value:
            return self.get_steps_template()
        elif f_val == OutputFormat.COMPARISON.value:
            return self.get_comparison_template()
        else:
            return self.get_paragraph_template()

    def build_prompt(
        self,
        format: OutputFormat,
        context: str,
        query: str,
        include_one_shot: bool = True
    ) -> str:
        template = self.get_template(format)

        prompt = f"{self.BASE_INSTRUCTIONS}\n"
        prompt += f"{template.systemInstructions}\n"
        prompt += self.COMPLIANCE_WARNING + "\n\n"

        prompt += "## FORMAT RULES:\n"
        for rule in template.formatRules:
            prompt += f"- {rule}\n"
        prompt += "\n"

        if include_one_shot and template.oneShot:
            prompt += "## EXAMPLE:\n"
            prompt += f"Question: {template.oneShot.userQuery}\n"
            prompt += f"Answer:\n{template.oneShot.expectedOutput}\n\n"

        prompt += "## CONTEXT FROM COURSE MATERIALS:\n"
        prompt += context + "\n\n"

        prompt += f"## STUDENT'S QUESTION:\n{query}\n\n"
        prompt += "## YOUR ANSWER:\n"

        return prompt

    def get_table_template(self) -> FormatTemplate:
        return FormatTemplate(
            format=OutputFormat.TABLE,
            systemInstructions="""You MUST present the answer as a Markdown table.
Tables are ideal for structured data, comparisons, and organized information.""",
            formatRules=[
                'You MUST use Markdown table format with | pipes and --- separators',
                'Include a header row with column names',
                'Each row must have the same number of columns',
                'Keep cell content concise and clear',
                'Do NOT include any text before or after the table unless absolutely necessary for context',
                'If multiple tables are needed, separate them with a brief label'
            ],
            oneShot=OneShotExample(
                userQuery='Show me the sales data in tabular format',
                expectedOutput="""| Quarter | Revenue | Growth |
|---------|---------|--------|
| Q1 2024 | $1.2M | +15% |
| Q2 2024 | $1.5M | +25% |
| Q3 2024 | $1.8M | +20% |"""
            ),
            validationHints=['|', '---', 'header row']
        )

    def get_list_template(self) -> FormatTemplate:
        return FormatTemplate(
            format=OutputFormat.LIST,
            systemInstructions="""You MUST present the answer as a bullet point list.
Lists are ideal for enumerating items, features, or distinct points.""",
            formatRules=[
                'Use bullet points (- or •) for unordered lists',
                'Use numbers (1. 2. 3.) for ordered/sequential items',
                'Each list item should be concise and focused',
                'Use nested bullets for sub-items when needed',
                'Start each item with a key term or action when appropriate',
                'Do NOT write long paragraphs - break into list items'
            ],
            oneShot=OneShotExample(
                userQuery='What are the benefits of exercise?',
                expectedOutput="""- **Improved cardiovascular health** - Strengthens heart and improves circulation
- **Weight management** - Burns calories and boosts metabolism
- **Mental health benefits** - Reduces stress, anxiety, and depression
- **Better sleep quality** - Promotes deeper, more restful sleep
- **Increased energy levels** - Improves stamina and reduces fatigue"""
            ),
            validationHints=['-', '•', '1.', '*']
        )

    def get_json_template(self) -> FormatTemplate:
        return FormatTemplate(
            format=OutputFormat.JSON,
            systemInstructions="""You MUST return the answer as valid JSON.
JSON format is required for structured, machine-readable output.""",
            formatRules=[
                'Return ONLY valid JSON - no markdown code blocks',
                'Use proper JSON syntax with double quotes for strings',
                'Include meaningful keys that describe the data',
                'Use arrays for lists of items',
                'Use nested objects for hierarchical data',
                'Do NOT include any text outside the JSON object'
            ],
            oneShot=OneShotExample(
                userQuery='Give me the project status in JSON format',
                expectedOutput="""{
  "project": "LMS Development",
  "status": "in_progress",
  "completion": 75,
  "milestones": [
    {"name": "Design", "status": "completed"},
    {"name": "Development", "status": "in_progress"},
    {"name": "Testing", "status": "pending"}
  ]
}"""
            ),
            validationHints=['{', '}', '":', '[']
        )

    def get_summary_template(self) -> FormatTemplate:
        return FormatTemplate(
            format=OutputFormat.SUMMARY,
            systemInstructions="""You MUST provide a concise summary of the key information.
Summaries should capture the essential points without unnecessary detail.""",
            formatRules=[
                'Keep the summary brief - ideally 2-4 sentences',
                'Focus on the most important points only',
                'Use clear, direct language',
                'Avoid filler words and redundancy',
                'Start with the main conclusion or key finding',
                'End with any critical caveats or context if needed'
            ],
            oneShot=OneShotExample(
                userQuery='Summarize the causes of World War I',
                expectedOutput="World War I was triggered by a complex web of factors including militarism, alliance systems, imperialism, and nationalism across European powers. The assassination of Archduke Franz Ferdinand in 1914 served as the immediate catalyst, setting off a chain reaction of declarations of war due to binding alliance treaties."
            ),
            validationHints=[]
        )

    def get_steps_template(self) -> FormatTemplate:
        return FormatTemplate(
            format=OutputFormat.STEPS,
            systemInstructions="""You MUST present the answer as numbered sequential steps.
Step-by-step format is ideal for procedures, instructions, and processes.""",
            formatRules=[
                'Use numbered steps (1. 2. 3.) in sequential order',
                'Each step should be a clear, actionable instruction',
                'Start each step with a verb when possible',
                'Include any warnings or tips as sub-points',
                'Keep steps atomic - one action per step',
                'Add brief explanations after the action if needed'
            ],
            oneShot=OneShotExample(
                userQuery='How do I create a GitHub repository step by step?',
                expectedOutput="""1. **Log in to GitHub** - Navigate to github.com and sign in to your account
2. **Click the "+" icon** - Located in the top-right corner of the page
3. **Select "New repository"** - From the dropdown menu
4. **Enter repository details**
   - Choose a descriptive name
   - Add an optional description
   - Select public or private visibility
5. **Initialize the repository** - Optionally add README, .gitignore, and license
6. **Click "Create repository"** - Your new repository is now ready to use"""
            ),
            validationHints=['1.', '2.', '3.']
        )

    def get_comparison_template(self) -> FormatTemplate:
        return FormatTemplate(
            format=OutputFormat.COMPARISON,
            systemInstructions="""You MUST present a structured comparison between the items.
Use a table or side-by-side format to clearly show differences and similarities.""",
            formatRules=[
                'Use a comparison table with clear categories/criteria',
                'Include both similarities and differences',
                'Be objective and balanced in the comparison',
                'Use consistent criteria for all items being compared',
                'Highlight key differentiators',
                'Optionally include a brief conclusion or recommendation'
            ],
            oneShot=OneShotExample(
                userQuery='Compare React and Vue',
                expectedOutput="""| Aspect | React | Vue |
|--------|-------|-----|
| Learning Curve | Steeper, requires JSX knowledge | Gentler, HTML-based templates |
| Performance | Virtual DOM, excellent | Virtual DOM, excellent |
| Ecosystem | Massive, many choices | Growing, more opinionated |
| State Management | Redux, Zustand, etc. | Vuex (built-in solution) |
| Company Backing | Meta (Facebook) | Community-driven |

**Summary:** React offers more flexibility and a larger ecosystem, while Vue provides a more approachable learning curve and cohesive tooling."""
            ),
            validationHints=['|', 'vs', 'React', 'Vue']
        )

    def get_paragraph_template(self) -> FormatTemplate:
        return FormatTemplate(
            format=OutputFormat.PARAGRAPH,
            systemInstructions="""Provide a clear, well-structured explanation.
Use paragraphs for detailed explanations and comprehensive answers.""",
            formatRules=[
                'Write in clear, well-organized paragraphs',
                'Use topic sentences to start each paragraph',
                'Provide examples when they aid understanding',
                'Keep language accessible and educational',
                'Use formatting (bold, headers) to improve readability when helpful',
                'Synthesize information from multiple sources if available'
            ],
            validationHints=[]
        )
