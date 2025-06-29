import os
import streamlit as st
import faiss
import numpy as np
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# ========== CONFIG ==========
os.environ["MISTRAL_API_KEY"] = "P5Ya1Is7YS4AM2dVkBU0KrV9Bz0BU0KU"
api_key = os.getenv("MISTRAL_API_KEY")
client = MistralClient(api_key=api_key)

# ========== DATA ==========
mental_health_texts = [
    "When you're feeling overwhelmed, take a few deep breaths. Inhale for 4 seconds, hold for 4, exhale for 4. Repeat slowly to help calm your nervous system.",
    "Talking to someone you trust can relieve emotional pressure. Consider reaching out to a friend, counselor, or support group.",
    "It’s okay to feel sad sometimes. Allow yourself to experience emotions without judgment. Feelings pass like clouds.",
    "Getting quality sleep is essential for mental health. Try a bedtime routine, avoid screens before sleep, and keep your environment quiet and dark.",
    "When anxious thoughts arise, try grounding techniques like naming 5 things you see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste.",
    "Exercise helps release endorphins. A short walk, stretch, or dance break can improve mood and reduce stress.",
    "You’re not alone. Many people struggle with similar feelings. Seeking help is a sign of strength, not weakness.",
    "Practice self-compassion. Speak to yourself the way you’d speak to a friend going through the same thing.",
    "Journaling can help organize thoughts and feelings. Even writing a few lines daily can create emotional clarity.",
    "Try to stay hydrated and eat balanced meals. Physical health supports emotional balance too."
]

# ========== EMBEDDINGS ==========
def create_embeddings(text_list):
    try:
        st.write("🔍 Creating embeddings with Mistral...")
        response = client.embeddings(model="mistral-embed", input=text_list)
        return np.array([r.embedding for r in response.data])
    except Exception as e:
        st.warning(f"⚠️ Falling back to dummy embeddings: {e}")
        return np.random.rand(len(text_list), 384)  # dummy vector fallback

def setup_faiss_index(text_chunks):
    embeddings = create_embeddings(text_chunks)
    if embeddings is None:
        return None
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index

def fetch_relevant_chunks(query, index, chunks, num_chunks=3):
    query_embedding = create_embeddings([query])
    if query_embedding is None or index is None:
        return []
    _, indices = index.search(query_embedding, num_chunks)
    return [chunks[i] for i in indices[0]]

# ========== UI SETUP ==========
st.set_page_config(page_title="Mental Health Chatbot Sakina AI", page_icon="🧠")
st.title("🧠 Mental Health Support Chatbot Sakina AI")
st.markdown("_This tool provides general mental health support and is **not** a substitute for professional help._")

# ========== SESSION STATE ==========
if "faiss_index" not in st.session_state:
    st.write("⚙️ Initializing FAISS index...")
    try:
        index = setup_faiss_index(mental_health_texts)
        st.session_state["faiss_index"] = index
        st.session_state["chunks"] = mental_health_texts
        st.success("✅ FAISS index ready.")
    except Exception as e:
        st.session_state["faiss_index"] = None
        st.session_state["chunks"] = mental_health_texts
        st.error(f"❌ FAISS setup failed: {e}")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ========== DISPLAY CHAT ==========
st.markdown("### 🧾 Chat History")
if st.session_state["chat_history"]:
    for chat in st.session_state["chat_history"]:
        st.markdown(f"**You:** {chat['user']}")
        st.markdown(f"**Sakina AI:** {chat['assistant']}")
        st.markdown("---")
else:
    st.info("Start chatting to see responses here.")

# ========== INPUT AT BOTTOM ==========
st.markdown("### 💬 Your Message:")
col1, col2 = st.columns([6, 1])
with col1:
    user_query = st.text_input("Type your message...", key="user_input", label_visibility="collapsed")
with col2:
    send_clicked = st.button("Send")

if send_clicked and user_query.strip():
    try:
        # Get context
        context_chunks = fetch_relevant_chunks(user_query, st.session_state["faiss_index"], st.session_state["chunks"])
        context = "\n".join(context_chunks)

        # Prepare message history
        messages = []
        for chat in st.session_state["chat_history"]:
            messages.append(ChatMessage(role="user", content=chat["user"]))
            messages.append(ChatMessage(role="assistant", content=chat["assistant"]))

        # Add current prompt
        prompt = (
            f"You are a supportive mental health assistant. Use the context below to help the user.\n\n"
            f"Context:\n{context}\n\n"
            f"User: {user_query}\nAssistant:"
        )
        messages.append(ChatMessage(role="user", content=prompt))

        # Get Mistral response
        response = client.chat(model="mistral-large-latest", messages=messages)
        reply = response.choices[0].message.content

        # Update chat history
        st.session_state["chat_history"].append({
            "user": user_query,
            "assistant": reply
        })

        st.rerun()
          # Auto-scroll

    except Exception as e:
        st.error(f"⚠️ Error: {e}")

# ========== RESET ==========
if st.button("Reset Conversation"):
    st.session_state["chat_history"] = []
    st.experimental_rerun()
