mport os
import streamlit as st
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import networkx as nx

# ========== CONFIG ==========
os.environ["MISTRAL_API_KEY"] = "P5Ya1Is7YS4AM2dVkBU0KrV9Bz0BU0KU"
api_key = os.getenv("MISTRAL_API_KEY")
client = MistralClient(api_key=api_key)

# ========== BUILD KNOWLEDGE GRAPH ==========
def build_knowledge_graph():
    triples = [
        ("Deep breathing", "helps with", "Anxiety"),
        ("Talking to someone", "reduces", "Emotional pressure"),
        ("Quality sleep", "improves", "Mental health"),
        ("Journaling", "promotes", "Emotional clarity"),
        ("Exercise", "releases", "Endorphins"),
        ("Grounding technique", "reduces", "Anxious thoughts"),
        ("Self-compassion", "encourages", "Emotional resilience"),
        ("Hydration", "supports", "Emotional balance"),
        ("Balanced meals", "enhance", "Physical health"),
        ("Physical health", "supports", "Mental stability"),
        ("Support group", "is a type of", "Social connection"),
        ("Social connection", "reduces", "Loneliness")
    ]
    G = nx.DiGraph()
    for subj, pred, obj in triples:
        G.add_edge(subj, obj, label=pred)
    return G

# ========== RETRIEVE CONTEXT ==========
def get_context_from_kg(query, G):
    context_nodes = set()
    for node in G.nodes():
        if node.lower() in query.lower():
            context_nodes.add(node)
            context_nodes.update(G.successors(node))
            context_nodes.update(G.predecessors(node))
i
    if not context_nodes:
        return ["I'm here to support you. Could you tell me a bit more about what you're feeling?"]

    context_lines = []
    for u, v, data in G.edges(data=True):
        if u in context_nodes or v in context_nodes:
            context_lines.append(f"{u} {data['label']} {v}.")
    return context_lines

# ========== UI ==========
st.set_page_config(page_title="Sakina AI - Knowledge Graph", page_icon="🧠")
st.title("🧠 Mental Health Support Chatbot Sakina AI")
st.markdown("_This version uses a mental health Knowledge Graph to retrieve context for replies._")

# Initialize graph
if "kg" not in st.session_state:
    st.session_state.kg = build_knowledge_graph()

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ========== DISPLAY CHAT ==========
st.markdown("### 🧾 Chat History")
if st.session_state.chat_history:
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['user']}")
        st.markdown(f"**Sakina AI:** {chat['assistant']}")
        st.markdown("---")
else:
    st.info("Start chatting to see responses here.")

# ========== INPUT AREA ==========
st.markdown("### 💬 Your Message:")
col1, col2 = st.columns([6, 1])
with col1:
    user_query = st.text_input("Type your message...", key="user_input", label_visibility="collapsed")
with col2:
    send_clicked = st.button("Send")

# ========== RESPONSE ==========
if send_clicked and user_query.strip():
    context_chunks = get_context_from_kg(user_query, st.session_state.kg)
    context = "\n".join(context_chunks)

    messages = []
    for chat in st.session_state.chat_history:
        messages.append(ChatMessage(role="user", content=chat["user"]))
        messages.append(ChatMessage(role="assistant", content=chat["assistant"]))

    prompt = (
        f"You are a culturally aware and compassionate mental health assistant. "
        f"Use the context from the knowledge graph below to support the user's message.\n\n"
        f"Context:\n{context}\n\n"
        f"User: {user_query}\nAssistant:"
    )
    messages.append(ChatMessage(role="user", content=prompt))

    try:
        response = client.chat(model="mistral-large-latest", messages=messages)
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"Sorry, there was an error contacting the AI: {e}"

    st.session_state.chat_history.append({
        "user": user_query,
        "assistant": reply
    })
    st.rerun()

# ========== RESET ==========
if st.button("Reset Conversation"):
    st.session_state.chat_history = []
    st.rerun()
