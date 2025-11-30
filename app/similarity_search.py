from datetime import datetime
from database.vector_store import VectorStore
from services.synthesizer import Synthesizer
from timescale_vector import client

# Initialize VectorStore
vec = VectorStore()

# --------------------------------------------------------------
# Study question - relevant to study materials
# --------------------------------------------------------------

relevant_question = "What is the main concept discussed in chapter 3?"
results = vec.search(relevant_question, limit=3)

response = Synthesizer.generate_response(question=relevant_question, context=results)

print(f"\nQuestion: {relevant_question}")
print(f"\nAnswer:\n{response.answer}")
print("\nThought process:")
for thought in response.thought_process:
    print(f"- {thought}")
print(f"\nHas enough context: {response.enough_context}")

# --------------------------------------------------------------
# Irrelevant question - not related to study materials
# --------------------------------------------------------------

irrelevant_question = "What is the weather in Tokyo?"

results = vec.search(irrelevant_question, limit=3)

response = Synthesizer.generate_response(question=irrelevant_question, context=results)

print(f"\n\nQuestion: {irrelevant_question}")
print(f"\nAnswer:\n{response.answer}")
print("\nThought process:")
for thought in response.thought_process:
    print(f"- {thought}")
print(f"\nHas enough context: {response.enough_context}")

# --------------------------------------------------------------
# Metadata filtering by book title
# --------------------------------------------------------------

metadata_filter = {"book_title": "Introduction to Machine Learning"}

results = vec.search(relevant_question, limit=3, metadata_filter=metadata_filter)

response = Synthesizer.generate_response(question=relevant_question, context=results)

print(f"\n\nQuestion (filtered by book): {relevant_question}")
print(f"\nAnswer:\n{response.answer}")
print("\nThought process:")
for thought in response.thought_process:
    print(f"- {thought}")
print(f"\nHas enough context: {response.enough_context}")

# --------------------------------------------------------------
# Advanced filtering using Predicates
# --------------------------------------------------------------

# Filter by specific book
predicates = client.Predicates("book_title", "==", "Introduction to Machine Learning")
results = vec.search(relevant_question, limit=3, predicates=predicates)

# Filter by multiple books (OR)
predicates = client.Predicates("book_title", "==", "Introduction to Machine Learning") | client.Predicates(
    "book_title", "==", "Deep Learning Fundamentals"
)
results = vec.search(relevant_question, limit=3, predicates=predicates)

# Filter by book and date (AND)
predicates = client.Predicates("book_title", "==", "Introduction to Machine Learning") & client.Predicates(
    "created_at", ">", "2024-09-01"
)
results = vec.search(relevant_question, limit=3, predicates=predicates)

# --------------------------------------------------------------
# Time-based filtering
# --------------------------------------------------------------

# September — Returning results
time_range = (datetime(2024, 9, 1), datetime(2024, 9, 30))
results = vec.search(relevant_question, limit=3, time_range=time_range)

# August — Not returning any results
time_range = (datetime(2024, 8, 1), datetime(2024, 8, 30))
results = vec.search(relevant_question, limit=3, time_range=time_range)
