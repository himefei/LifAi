improvement_options = [
    "Fix spelling",
    "Improve writing quality",
    "Make text more polite and friendly",
    "Make it simple and easy to read",
    "Summarize context",
    "Analyze context and generate response",
    "Translate to Simplified Chinese"
]

llm_prompts = {
    "Fix spelling": """Please fix any spelling errors in the following text, maintaining the original meaning and style:
{text}""",
    
    "Improve writing quality": """Please improve the writing quality of the following text, making it more concise, clear, and engaging while preserving the original meaning:
{text}""",
    
    "Make text more polite and friendly": """Please rewrite the following text to be more polite and friendly, while still conveying the same information:
{text}""",
    
    "Make it simple and easy to read": """Please simplify the following text, making it easier to understand for a wider audience, while retaining the core message:
{text}""",
    
    "Summarize context": """Please provide a concise summary of the following text:
{text}""",
    
    "Analyze context and generate response": """Please analyze the following text and generate a relevant and insightful response:
{text}""",
    
    "Translate to Simplified Chinese": """Please translate the following text to Simplified Chinese:
{text}"""
} 