import streamlit as st
from langgraph_backend3 import chatbot
from langchain_core.messages import HumanMessage
import uuid
import response
import gameTree
import json
from datetime import datetime, timezone

def generate_thread_id():
    return str(uuid.uuid4())

def get_current_time():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def reset_chat():

    thread_id = generate_thread_id()

    st.session_state["thread_id"] = thread_id

    add_thread(thread_id)

    st.session_state["message_history"] = []

def load_conversation(thread_id):

    try:

        state = chatbot.get_state(
            config={
                "configurable": {
                    "thread_id": str(thread_id)
                }
            }
        )
        if state:
            return state.values.get(
                "messages",
                []
            )
        return []

    except Exception as e:

        st.sidebar.error(
            f"Could not load conversation: {e}"
        )
        return []

# def create_conversation_txt(thread_id):

#     # IMPORTANT:
#     # Use CURRENT session_state.
#     # Do not call load_conversation() here.

#     messages = st.session_state.get(
#         "message_history",
#         []
#     )

#     if not messages:

#         return "No conversation history found."


#     lines = []

#     lines.append(
#         f"Thread ID: {thread_id}"
#     )

#     lines.append(
#         f"Downloaded: {get_current_time()}"
#     )

#     lines.append("=" * 70)

#     lines.append("")


#     # ========================================================
#     # Messages
#     # ========================================================

#     for index, message in enumerate(
#         messages,
#         start=1
#     ):

#         role = message.get(
#             "role",
#             "unknown"
#         )

#         content = message.get(
#             "content",
#             ""
#         )

#         timestamp = message.get(
#             "time",
#             "Time not available"
#         )


#         if role == "user":

#             speaker = "USER"

#         elif role == "assistant":

#             speaker = "AI ASSISTANT"

#         else:

#             speaker = role.upper()


#         lines.append(
#             f"TURN {index}"
#         )

#         lines.append(
#             f"Speaker: {speaker}"
#         )

#         lines.append(
#             f"Time: {timestamp}"
#         )

#         lines.append(
#             "Utterance:"
#         )

#         lines.append(
#             str(content)
#         )

#         lines.append("")

#         lines.append(
#             "-" * 70
#         )

#         lines.append("")


#     # ========================================================
#     # Footer
#     # ========================================================
#     lines.append("=" * 70)
#     lines.append(
#         "END OF CONVERSATION"
#     )
#     lines.append("=" * 70)
#     return "\n".join(lines)

# def create_conversation_txt(thread_id):
#     messages = st.session_state.get(
#         "message_history",
#         []
#     )
#     if not messages:
#         return "No conversation history found."
#     lines = []
#     for message in messages:
#         timestamp = message.get(
#             "time",
#             " "
#         )

#         role = message.get(
#             "role",
#             "unknown"
#         )
#         content = message.get(
#             "content",
#             ""
#         )

#         if role == "user":
#             speaker = "User"

#         elif role == "assistant":
#             speaker = "Assistant"

#         else:
#             speaker = role.capitalize()

#         lines.append(
#             f"{timestamp}, {speaker}: {content}"
#         )

#     return "\n".join(lines)

def create_conversation_txt(thread_id):

    messages = st.session_state.get(
        "message_history",
        []
    )
    if not messages:
        return "No conversation history found."
    lines = []
    for message in messages:

        timestamp = message.get(
            "time",
            " "
        )

        role = message.get(
            "role",
            "unknown"
        )

        content = message.get(
            "content",
            ""
        )

        if role == "user":

            lines.append(
                f"{timestamp}, User: , {content}"
            )

        elif role == "assistant":

            component = message.get(
                "component",
                "Not specified"
            )

            lines.append(
                f"{timestamp}, {component}, Assistant:, {content}"
            )

        else:

            lines.append(
                f"{timestamp}, {role.capitalize()}, {content}"
            )

    return "\n".join(lines)

# ============================================================
# Session Setup
# ============================================================

# if "message_history" not in st.session_state:

#     st.session_state["message_history"] = []


# if "thread_id" not in st.session_state:

#     st.session_state["thread_id"] = (
#         generate_thread_id()
#     )


# if "chat_threads" not in st.session_state:

#     st.session_state["chat_threads"] = (
#         retrieve_all_threads()
#     )

# add_thread(
#     st.session_state["thread_id"]
# )

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

# IMPORTANT:
# Each Streamlit browser session gets its own thread list.
# Do NOT load all threads from PostgreSQL here.
if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = []

# Add the current thread to THIS browser session only
add_thread(
    st.session_state["thread_id"]
)

# ============================================================
# Sidebar
# ============================================================

st.sidebar.title(
    "DBT-wellMind-GameTree"
)

PatinetID = st.sidebar.text_input("Enter Your ID")
# ============================================================
# New Chat
# ============================================================

if st.sidebar.button(
    "➕ New Chat",
    use_container_width=True
):
    reset_chat()
    st.rerun()

# ============================================================
# My Conversations
# ============================================================

st.sidebar.header(
    "My Conversations"
)
for thread_id in (
    st.session_state["chat_threads"][::-1]
):
    if st.sidebar.button(
        str(thread_id),
        key=f"thread_{thread_id}",
        use_container_width=True
    ):

        # Change active thread

        st.session_state["thread_id"] = (
            thread_id
        )
        # Load conversation
        messages = load_conversation(
            thread_id
        )
        temp_messages = []
        for msg in messages:

            if isinstance(
                msg,
                HumanMessage
            ):

                role = "user"

            else:

                role = "assistant"
            # Try to get saved timestamp

            timestamp = "Time not available"
            if hasattr(
                msg,
                "additional_kwargs"
            ):

                timestamp = (
                    msg.additional_kwargs.get(
                        "timestamp",
                        "Time not available"
                    )
                )
            temp_messages.append({
                "role": role,
                "content": msg.content,
                "time": timestamp
            })
        st.session_state[
            "message_history"
        ] = temp_messages
        st.rerun()

# ============================================================
# Main UI
# ============================================================

st.title(
    "Self-Esteem Improvement Chatbot"
)
# ============================================================
# Display Existing Messages
# ============================================================

for message in (
    st.session_state["message_history"]
):

    with st.chat_message(
        message["role"]
    ):

        st.text(
            message["content"]
        )


# ============================================================
# Chat Input
# ============================================================

user_input = st.chat_input(
    "Type here..."
)

# Process User Message
# st.session_state.action =[]
if "action" not in st.session_state:
    st.session_state["action"] = []

if "history" not in st.session_state:
    st.session_state["history"] = []

if user_input:
    # USER TIMESTAMP
    user_time = get_current_time()
    selected_component = "Emotion_Regulation"
    # Display USER
    with st.chat_message("user"):

        st.text(
            user_input
        )

    Subset_prompt  = response.determine_reward_with_behaviour(st.session_state["history"],user_input,st.session_state.action)
    print("Reward Prompt",Subset_prompt)
    actual_reward = response.SubsetSelection(Subset_prompt)
    # print("Before Extract Reawrd: ",actual_reward)
    reward_data = json.loads(actual_reward)
    # print("Reward After Json Data", reward_data)

    best_action = gameTree.dataImport(user_input,reward_data)
    print("DBT Component",best_action)
    st.session_state.action = best_action
    # Save USER message
    st.session_state[
        "message_history"
    ].append({
        "time": user_time,
        "role": "user",
        "content": user_input
    })
    st.session_state["history"].append({"role": "user","content": user_input})

    # ========================================================
    # LangGraph Config
    # ========================================================

    CONFIG = {

        "configurable": {

            "thread_id":
                st.session_state[
                    "thread_id"
                ]

        },

        "metadata": {

            "thread_id":
                st.session_state[
                    "thread_id"
                ]

        },

        "run_name": "chat_turn"

    }

    # AI RESPONSE
    with st.chat_message("assistant"):

        ai_message = st.write_stream(
            message_chunk.content
            for message_chunk, metadata
            in chatbot.stream(

                {
                    "messages": [
                        HumanMessage(
                            content=user_input
                        )
                    ],

                    "component": best_action
                },

                config=CONFIG,

                stream_mode="messages"

            )

        )
    assistant_time = get_current_time()

    st.session_state[
        "message_history"
    ].append({
        "time": assistant_time,
        "component": best_action,
        "role": "assistant",
        "content": ai_message,
    })

    st.session_state["history"].append({"role": "assistant","content": ai_message})

# DOWNLOAD SECTION
st.sidebar.divider()

st.sidebar.header(
    "Download Conversation"
)

# Generate the TXT AFTER message processing
conversation_txt = create_conversation_txt(
    st.session_state["thread_id"]
)
st.sidebar.download_button(
    label="📥 Download Conversation",
    data=conversation_txt,
    file_name=(
        f"Chat_"
        f"{get_current_time()}_"
        f"{PatinetID}_"
        f"{st.session_state['thread_id']}.txt"
    ),
    mime="text/plain",
    use_container_width=True,
    key="download_conversation"
)
# print(st.session_state["message_history"])
