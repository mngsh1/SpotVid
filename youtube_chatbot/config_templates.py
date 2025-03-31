CHUNK_SUMMARY_TEMPLATE = """
Summarize this video chunk: {text}

Instructions:
- Avoid [Music] as it indicate that music is played 

"""


QUERY_TEMPLATE = """
Answer the question based strictly on the following context. Do not include any information outside of this context.
Context: {context}
Question: {question}
Answer in a helpful and concise manner. Use bullets for multi-point answers.
"""
