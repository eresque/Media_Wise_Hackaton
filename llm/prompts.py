from langchain_core.prompts.prompt import PromptTemplate

PROMPTS = {
    "llm_instructions": """
                            Ты — умный, внимательный и ответственный русскоязычный автоматический ассистент.
                            """,

    "question": PromptTemplate(
        template="""
                            {context}
                            {prompt}
                            """,
        input_variables=["context", "prompt"]
    ),
}
