import streamlit as st

from langgraph_backend3 import (
    chatbot,
    register_thread,
    retrieve_threads_for_patient,
    thread_belongs_to_patient,
)

from langchain_core.messages import HumanMessage

import uuid
import response
import gameTree
import json

from datetime import datetime, timezone


# ============================================================
# THREAD ID
# ============================================================

def generate_thread_id():

    return str(
        uuid.uuid4()
    )


# ============================================================
# CURRENT TIME
# ============================================================

def get_current_time():

    return datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# ADD THREAD TO CURRENT SESSION
# ============================================================

def add_thread(thread_id):

    if "chat_threads" not in st.session_state:

        st.session_state[
            "chat_threads"
        ] = []

    if thread_id not in st.session_state[
        "chat_threads"
    ]:

        st.session_state[
            "chat_threads"
        ].append(
            thread_id
        )


# ============================================================
# CREATE NEW THREAD
# ============================================================

def create_new_thread(patient_id):

    thread_id = generate_thread_id()

    st.session_state[
        "thread_id"
    ] = thread_id

    st.session_state[
        "message_history"
    ] = []

    st.session_state[
        "history"
    ] = []

    st.session_state[
        "action"
    ] = []

    add_thread(
        thread_id
    )

    # Save PatientID <-> ThreadID relationship
    register_thread(
        thread_id,
        patient_id
    )

    return thread_id


# ============================================================
# RESET CHAT
# ============================================================

def reset_chat():

    patient_id = st.session_state.get(
        "patient_id",
        ""
    ).strip()

    if not patient_id:

        return

    create_new_thread(
        patient_id
    )


# ============================================================
# LOAD CONVERSATION
# ============================================================

def load_conversation(
    thread_id,
    patient_id
):

    # Security check:
    # Only load a thread belonging to this patient.
    if not thread_belongs_to_patient(
        thread_id,
        patient_id
    ):

        st.sidebar.error(
            "This conversation does not belong to this Patient ID."
        )

        return []

    try:

        state = chatbot.get_state(
            config={
                "configurable": {
                    "thread_id": str(
                        thread_id
                    )
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


# ============================================================
# CONVERSATION TXT
# ============================================================

def create_conversation_txt(
    thread_id
):

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

    return "\n".join(
        lines
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "DBT-wellMind-GameTree"
)


# ============================================================
# PATIENT ID
# ============================================================

PatinetID = st.sidebar.text_input(
    "Enter Your ID",
    key="patient_id"
)

PatinetID = PatinetID.strip()


# ============================================================
# INITIAL SESSION VARIABLES
# ============================================================

if "message_history" not in st.session_state:

    st.session_state[
        "message_history"
    ] = []


if "history" not in st.session_state:

    st.session_state[
        "history"
    ] = []


if "action" not in st.session_state:

    st.session_state[
        "action"
    ] = []


if "chat_threads" not in st.session_state:

    st.session_state[
        "chat_threads"
    ] = []


if "thread_id" not in st.session_state:

    st.session_state[
        "thread_id"
    ] = None


if "active_patient_id" not in st.session_state:

    st.session_state[
        "active_patient_id"
    ] = None


# ============================================================
# PATIENT ID CHANGE / INITIALIZATION
# ============================================================

if PatinetID:

    # First time entering PatientID
    # OR PatientID has changed.
    if (
        st.session_state[
            "active_patient_id"
        ]
        != PatinetID
    ):

        st.session_state[
            "active_patient_id"
        ] = PatinetID

        # Get only this patient's conversations
        st.session_state[
            "chat_threads"
        ] = retrieve_threads_for_patient(
            PatinetID
        )

        # Start a new active conversation.
        create_new_thread(
            PatinetID
        )

else:

    st.session_state[
        "active_patient_id"
    ] = None

    st.session_state[
        "chat_threads"
    ] = []

    st.session_state[
        "thread_id"
    ] = None

    st.session_state[
        "message_history"
    ] = []

    st.session_state[
        "history"
    ] = []

    st.session_state[
        "action"
    ] = []


# ============================================================
# NEW CHAT
# ============================================================

if st.sidebar.button(
    "➕ New Chat",
    use_container_width=True
):

    if not PatinetID:

        st.sidebar.warning(
            "Please enter your Patient ID first."
        )

    else:

        reset_chat()

        st.rerun()


# ============================================================
# MY CONVERSATIONS
# ============================================================

st.sidebar.header(
    "My Conversations"
)


for thread_id in (
    st.session_state[
        "chat_threads"
    ][::-1]
):

    if st.sidebar.button(
        str(thread_id),
        key=f"thread_{thread_id}",
        use_container_width=True
    ):

        # ----------------------------------------------------
        # Verify ownership before loading
        # ----------------------------------------------------

        if not thread_belongs_to_patient(
            thread_id,
            PatinetID
        ):

            st.sidebar.error(
                "Invalid conversation."
            )

            continue


        # ----------------------------------------------------
        # Change active thread
        # ----------------------------------------------------

        st.session_state[
            "thread_id"
        ] = thread_id


        # ----------------------------------------------------
        # Load conversation
        # ----------------------------------------------------

        messages = load_conversation(
            thread_id,
            PatinetID
        )


        # ----------------------------------------------------
        # Convert LangChain messages
        # ----------------------------------------------------

        temp_messages = []

        history = []


        for msg in messages:

            if isinstance(
                msg,
                HumanMessage
            ):

                role = "user"

            else:

                role = "assistant"


            # ------------------------------------------------
            # Timestamp
            # ------------------------------------------------

            timestamp = (
                "Time not available"
            )

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


            # ------------------------------------------------
            # Component
            # ------------------------------------------------

            component = None

            if hasattr(
                msg,
                "additional_kwargs"
            ):

                component = (
                    msg.additional_kwargs.get(
                        "component"
                    )
                )


            # ------------------------------------------------
            # Message history
            # ------------------------------------------------

            temp_message = {
                "role": role,
                "content": msg.content,
                "time": timestamp
            }


            if (
                role == "assistant"
                and component
            ):

                temp_message[
                    "component"
                ] = component


            temp_messages.append(
                temp_message
            )


            # ------------------------------------------------
            # History for reward/game tree
            # ------------------------------------------------

            history.append({
                "role": role,
                "content": msg.content
            })


        st.session_state[
            "message_history"
        ] = temp_messages


        st.session_state[
            "history"
        ] = history


        # Reset action.
        # The next user message will select a new action.
        st.session_state[
            "action"
        ] = []


        st.rerun()


# ============================================================
# MAIN UI
# ============================================================

st.title(
    "Self-Esteem Improvement Chatbot"
)


# ============================================================
# PATIENT ID REQUIRED
# ============================================================

if not PatinetID:

    st.info(
        "Please enter your Patient ID in the sidebar to start."
    )


# ============================================================
# DISPLAY EXISTING MESSAGES
# ============================================================

for message in (
    st.session_state[
        "message_history"
    ]
):

    with st.chat_message(
        message["role"]
    ):

        st.text(
            message["content"]
        )


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Type here..."
)


# ============================================================
# PROCESS USER MESSAGE
# ============================================================

if user_input:

    # --------------------------------------------------------
    # Check PatientID
    # --------------------------------------------------------

    if not PatinetID:

        st.error(
            "Please enter your Patient ID first."
        )

        st.stop()


    # --------------------------------------------------------
    # Check active thread
    # --------------------------------------------------------

    if not st.session_state.get(
        "thread_id"
    ):

        create_new_thread(
            PatinetID
        )


    # --------------------------------------------------------
    # Verify active thread ownership
    # --------------------------------------------------------

    if not thread_belongs_to_patient(
        st.session_state["thread_id"],
        PatinetID
    ):

        create_new_thread(
            PatinetID
        )


    # --------------------------------------------------------
    # USER TIMESTAMP
    # --------------------------------------------------------

    user_time = get_current_time()


    # --------------------------------------------------------
    # USER MESSAGE DISPLAY
    # --------------------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.text(
            user_input
        )


    # --------------------------------------------------------
    # REWARD / BEHAVIOR SELECTION
    # --------------------------------------------------------

    Subset_prompt = (
        response.determine_reward_with_behaviour(
            st.session_state["history"],
            user_input,
            st.session_state["action"]
        )
    )

    print(
        "Reward Prompt",
        Subset_prompt
    )


    actual_reward = (
        response.SubsetSelection(
            Subset_prompt
        )
    )


    reward_data = json.loads(
        actual_reward
    )


    # --------------------------------------------------------
    # GAME TREE
    # --------------------------------------------------------

    best_action = gameTree.dataImport(
        user_input,
        reward_data
    )

    print(
        "DBT Component",
        best_action
    )


    st.session_state[
        "action"
    ] = best_action


    # --------------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------------

    st.session_state[
        "message_history"
    ].append({
        "time": user_time,
        "role": "user",
        "content": user_input
    })


    st.session_state[
        "history"
    ].append({
        "role": "user",
        "content": user_input
    })


    # ========================================================
    # LANGGRAPH CONFIG
    # ========================================================

    current_thread_id = (
        st.session_state[
            "thread_id"
        ]
    )


    CONFIG = {

        "configurable": {

            "thread_id":
                current_thread_id
        },

        "metadata": {

            "thread_id":
                current_thread_id,

            "patient_id":
                PatinetID
        },

        "run_name": "chat_turn"
    }


    # ========================================================
    # AI RESPONSE
    # ========================================================

    with st.chat_message(
        "assistant"
    ):

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

                    "component":
                        best_action
                },

                config=CONFIG,

                stream_mode="messages"
            )
        )


    # ========================================================
    # ASSISTANT TIMESTAMP
    # ========================================================

    assistant_time = (
        get_current_time()
    )


    # ========================================================
    # SAVE ASSISTANT MESSAGE
    # ========================================================

    st.session_state[
        "message_history"
    ].append({

        "time":
            assistant_time,

        "component":
            best_action,

        "role":
            "assistant",

        "content":
            ai_message,
    })


    st.session_state[
        "history"
    ].append({

        "role":
            "assistant",

        "content":
            ai_message
    })


# ============================================================
# DOWNLOAD SECTION
# ============================================================

st.sidebar.divider()

st.sidebar.header(
    "Download Conversation"
)


# ============================================================
# CREATE TXT
# ============================================================

conversation_txt = (
    create_conversation_txt(
        st.session_state.get(
            "thread_id",
            ""
        )
    )
)


# ============================================================
# DOWNLOAD
# ============================================================

if PatinetID:

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
