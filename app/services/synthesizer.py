from typing import List, Optional
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
    11. After explaining a concept, you may offer test questions to help the student practice and reinforce their understanding.
    12. You can ask clarifying questions if the student's question is ambiguous or needs more context.
    13. Maintain conversation context - refer back to previous messages when relevant to provide coherent responses.
    
    Review the question from the user:
    """

    @staticmethod
    def generate_response(
        question: str,
        context: pd.DataFrame,
        conversation_history: Optional[List[dict]] = None,
    ) -> SynthesizedResponse:
        """Generates a synthesized response based on the question and context.

        Args:
            question: The user's question.
            context: The relevant context retrieved from the knowledge base.
            conversation_history: Optional list of previous messages in the conversation.

        Returns:
            A SynthesizedResponse containing thought process and answer.
        """
        # Handle empty context
        if context.empty or len(context) == 0:
            context_str = "No relevant context found in the knowledge base."
        else:
            # Check which columns are available
            available_columns = context.columns.tolist()
            columns_to_keep = []

            # Add content column if available
            if "content" in available_columns:
                columns_to_keep.append("content")

            # Add book_title if available
            if "book_title" in available_columns:
                columns_to_keep.append("book_title")

            # If no expected columns, use all available columns
            if not columns_to_keep:
                columns_to_keep = available_columns[:5]  # Limit to first 5 columns

            try:
                context_str = Synthesizer.dataframe_to_json(
                    context, columns_to_keep=columns_to_keep
                )
            except Exception as e:
                # Fallback if JSON conversion fails
                import logging

                logging.warning(f"Failed to convert context to JSON: {str(e)}")
                context_str = "Context retrieved but could not be formatted properly."

        # Build messages list with conversation history
        messages = [{"role": "system", "content": Synthesizer.SYSTEM_PROMPT}]

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                # Only include role and content, skip timestamp
                messages.append(
                    {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                )

        # Add current question and context
        messages.append({"role": "user", "content": f"# User question:\n{question}"})
        messages.append(
            {
                "role": "assistant",
                "content": f"# Retrieved information:\n{context_str}",
            }
        )

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
