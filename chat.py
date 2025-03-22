import os
import streamlit as st
from dotenv import load_dotenv
from chat_manager import ChatManager
import time

# Page configuration
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better chat appearance
st.markdown("""
<style>
.stTextInput>div>div>input {
    background-color: #f0f2f6;
}
.chat-message {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
}
.chat-message.user {
    background-color: #e3f2fd;
}
.chat-message.assistant {
    background-color: #f5f5f5;
}
.chat-message .message-content {
    margin-top: 0.5rem;
}
.context-box {
    background-color: #f8f9fa;
    border-left: 4px solid #007bff;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 0.25rem;
}
.confidence-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    font-weight: 500;
    margin-left: 0.5rem;
}
.confidence-high {
    background-color: #d4edda;
    color: #155724;
}
.confidence-medium {
    background-color: #fff3cd;
    color: #856404;
}
.confidence-low {
    background-color: #f8d7da;
    color: #721c24;
}
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = None
    if 'show_context' not in st.session_state:
        st.session_state.show_context = False

def get_confidence_class(confidence: float) -> str:
    """Get CSS class based on confidence score"""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    return "confidence-low"

def create_chat_message(role, content, chat_response=None):
    """Create a styled chat message"""
    with st.container():
        # Display the message with confidence score if it's an assistant message
        if role == "assistant" and chat_response:
            confidence_class = get_confidence_class(chat_response.confidence)
            st.markdown(f"""
            <div class="chat-message {role}">
                <div class="message-header">
                    <b>Assistant</b>
                    <span class="confidence-badge {confidence_class}">
                        Confidence: {chat_response.confidence:.2%}
                    </span>
                </div>
                <div class="message-content">
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message {role}">
                <div class="message-header">
                    <b>{'You' if role == 'user' else 'Assistant'}</b>
                </div>
                <div class="message-content">
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Display sources if enabled
        if chat_response and st.session_state.show_context:
            st.markdown("### Sources Used:")
            for i, source in enumerate(chat_response.sources, 1):
                st.markdown(f"""
                <div class="context-box">
                    <b>Source {i}</b> (Score: {source['score']:.2f})<br>
                    {source['text']}
                </div>
                """, unsafe_allow_html=True)

def initialize_chat_manager():
    """Initialize the chat manager with proper error handling"""
    try:
        load_dotenv()
        required_vars = ['GEMINI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_ENVIRONMENT']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            st.info("Please check your .env file and ensure all required variables are set.")
            return False
        
        if st.session_state.chat_manager is None:
            with st.spinner("Initializing chatbot..."):
                st.session_state.chat_manager = ChatManager()
                time.sleep(1)  # Add a small delay for better UX
        return True
    except Exception as e:
        st.error(f"Error initializing chatbot: {str(e)}")
        return False

def main():
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 AI Chatbot")
        st.markdown("---")
        st.markdown("""
        ### About
        This is an AI chatbot powered by Google's Gemini model and Pinecone for context management.
        
        ### How to Use
        1. Type your message in the input box below
        2. Press Enter or click Send
        3. Wait for the AI's response
        
        ### Settings
        """)
        
        # Toggle for showing context
        st.session_state.show_context = st.checkbox("Show sources used", value=False)
        
        if st.button("Clear Chat", type="primary"):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    st.title("Chat with AI")
    
    # Initialize chat manager
    if not initialize_chat_manager():
        st.stop()
    
    # Display chat messages
    for message in st.session_state.messages:
        create_chat_message(
            message["role"], 
            message["content"],
            message.get("chat_response")
        )
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        create_chat_message("user", prompt)
        
        # Get AI response
        with st.spinner("Thinking..."):
            try:
                chat_response = st.session_state.chat_manager.search_and_respond(prompt)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": chat_response.answer,
                    "chat_response": chat_response
                })
                create_chat_message("assistant", chat_response.answer, chat_response)
            except Exception as e:
                error_message = f"Error: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                create_chat_message("assistant", error_message)

if __name__ == "__main__":
    main() 