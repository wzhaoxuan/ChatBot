import google.generativeai as genai
import pinecone
from typing import List, Dict, Optional, TypedDict
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ChatResponse:
    """Structured response from the chatbot"""
    answer: str
    sources: List[Dict[str, str]]
    confidence: float
    timestamp: str
    query: str

class ChatManager:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Pinecone
        pinecone.init(
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT')
        )
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Get or create Pinecone index
        self.index_name = "chatbot-embeddings"
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                dimension=1536,  # Dimension for text-embedding-ada-002
                metric="cosine"
            )
        self.index = pinecone.Index(self.index_name)

    def engineer_prompt(self, question: str, context: List[Dict], system_prompt: Optional[str] = None) -> str:
        """
        Engineers a structured prompt for the LLM using retrieved context and user question.
        
        Args:
            question: The user's question
            context: List of relevant documents from Pinecone
            system_prompt: Optional system prompt to guide the model's behavior
            
        Returns:
            A structured prompt string
        """
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = """You are a helpful AI assistant. Use the provided context to answer questions accurately and concisely.
            If the context doesn't contain enough information to answer the question, say so.
            Base your response only on the provided context."""
        
        # Format context documents
        formatted_context = []
        for i, doc in enumerate(context, 1):
            doc_text = doc.metadata.get('text', '')
            if doc_text:
                formatted_context.append(f"Document {i}:\n{doc_text}")
        
        # Combine all elements into a structured prompt
        prompt = f"""
        {system_prompt}

        Context Information:
        {'-' * 50}
        {'\n\n'.join(formatted_context)}
        {'-' * 50}

        Question: {question}

        Instructions:
        1. Read the context carefully
        2. Answer the question based only on the provided context
        3. If the context is insufficient, acknowledge this
        4. Keep your response concise and focused
        5. Include relevant citations from the provided documents

        Response:
        """
        
        return prompt

    def query_pinecone(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Query Pinecone for relevant embeddings
        """
        # Generate embedding for the query
        query_embedding = self.model.embed_content(query)
        
        # Search Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return results.matches

    def generate_response(self, question: str, context: List[Dict], system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using Gemini based on the question and context
        """
        # Engineer the prompt
        prompt = self.engineer_prompt(question, context, system_prompt)
        
        # Generate response using Gemini
        response = self.model.generate_content(prompt)
        return response.text

    def search_and_respond(self, query: str, top_k: int = 3, system_prompt: Optional[str] = None) -> ChatResponse:
        """
        Main method that combines search and response generation into a single structured response.
        
        Args:
            query: The user's question
            top_k: Number of relevant documents to retrieve
            system_prompt: Optional system prompt to guide the model's behavior
            
        Returns:
            ChatResponse object containing the answer, sources, and metadata
        """
        # Query Pinecone for relevant context
        relevant_context = self.query_pinecone(query, top_k)
        
        # Generate response using the context
        answer = self.generate_response(query, relevant_context, system_prompt)
        
        # Extract sources from context
        sources = []
        for doc in relevant_context:
            source = {
                'text': doc.metadata.get('text', ''),
                'score': float(doc.score),
                'metadata': {k: v for k, v in doc.metadata.items() if k != 'text'}
            }
            sources.append(source)
        
        # Calculate average confidence from source scores
        confidence = sum(doc.score for doc in relevant_context) / len(relevant_context) if relevant_context else 0.0
        
        # Create structured response
        response = ChatResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            query=query
        )
        
        return response

    def add_to_knowledge_base(self, text: str, metadata: Optional[Dict] = None):
        """
        Add new text to the knowledge base in Pinecone
        """
        # Generate embedding for the text
        embedding = self.model.embed_content(text)
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata['text'] = text
        
        # Upsert to Pinecone
        self.index.upsert(
            vectors=[{
                'id': str(hash(text)),  # Simple hash as ID
                'values': embedding,
                'metadata': metadata
            }]
        ) 