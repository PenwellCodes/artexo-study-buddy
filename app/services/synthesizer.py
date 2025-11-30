from typing import List
import pandas as pd
from pydantic import BaseModel, Field
from services.llm_factory import LLMFactory


class SynthesizedResponse(BaseModel):
    thought_process: List[str] = Field(
        description="List of thoughts that the AI assistant had while synthesizing the answer"
    )
    answer: str = Field(description="The synthesized answer to the user's question")
    enough_context: bool = Field(
        description="Whether the assistant has enough context to answer the question"
    )


class Synthesizer:
    SYSTEM_PROMPT = """
    # Role and Purpose
    You are an AI study assistant for a learning application. Your task is to synthesize a coherent and helpful answer 
    based on the given question and relevant context retrieved from study materials (books) stored in a knowledge database.

    # Guidelines:
    1. Provide a clear, educational, and comprehensive answer to the question.
    2. Use only the information from the relevant context (book excerpts) to support your answer.
    3. The context is retrieved based on cosine similarity from multiple books, so some information might be missing or irrelevant.
    4. When multiple books contain relevant information, synthesize the information coherently.
    5. Be transparent when there is insufficient information to fully answer the question.
    6. Do not make up or infer information not present in the provided context.
    7. If you cannot answer the question based on the given context, clearly state that and suggest what information might be needed.
    8. Maintain an educational and supportive tone appropriate for a study assistant.
    9. Cite which book(s) the information comes from when multiple books are referenced.
    10. Help the student understand the concepts clearly, not just provide answers.
    
    Review the question from the user:
    """

    @staticmethod
    def generate_response(question: str, context: pd.DataFrame) -> SynthesizedResponse:
        """Generates a synthesized response based on the question and context.

        Args:
            question: The user's question.
            context: The relevant context retrieved from the knowledge base.

        Returns:
            A SynthesizedResponse containing thought process and answer.
        """
        context_str = Synthesizer.dataframe_to_json(
            context, columns_to_keep=["content", "book_title"]
        )

        messages = [
            {"role": "system", "content": Synthesizer.SYSTEM_PROMPT},
            {"role": "user", "content": f"# User question:\n{question}"},
            {
                "role": "assistant",
                "content": f"# Retrieved information:\n{context_str}",
            },
        ]

        llm = LLMFactory("gemini")
        return llm.create_completion(
            response_model=SynthesizedResponse,
            messages=messages,
        )

    @staticmethod
    def dataframe_to_json(
        context: pd.DataFrame,
        columns_to_keep: List[str],
    ) -> str:
        """
        Convert the context DataFrame to a JSON string.

        Args:
            context (pd.DataFrame): The context DataFrame.
            columns_to_keep (List[str]): The columns to include in the output.

        Returns:
            str: A JSON string representation of the selected columns.
        """
        return context[columns_to_keep].to_json(orient="records", indent=2)
