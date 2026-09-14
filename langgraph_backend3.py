from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated

from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
)

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.message import add_messages

from psycopg_pool import ConnectionPool

import streamlit as st


# ============================================================
# API KEYS
# ============================================================

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
db_API_KEY = st.secrets["DB_API_KEY"]


# ============================================================
# LLM
# ============================================================

llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.6,
    openai_api_key=OPENAI_API_KEY
)


# ============================================================
# CHAT STATE
# ============================================================

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    component: str

def systemPrompt(component):
    SYSTEM_PROMPT1 = f"""Context: You are a dialactical behaviour specialist mental health psychologist.To counseling you have to work in two phases: 1 problem_understanding_phase, 2 counseling_phase.
    In first phase, your goal is to understand the student's academic related problem which reason for self-esteem, understand their context and collect key symptoms/concerns  step by step / one at a time by follow the instructions in <problem_understanding_phase></problem_understanding_phase> XML tag for understand the student's problem.
    In second phase, your goal is to give support the execute of all instructions step by step and one by one by follow the instruction in <counseling_phase></counseling_phase> XML tag. 
    After complete problem_understanding_phase, then you need to go counseling_phase. You can't show the name of phase in your generate response. You can chat with in English, japanese and Bengla Language.
    I repeat, After complete problem_understanding_phase, then you need to go counseling_phase. Only chat for academic related problem of student.
    
    <problem_understanding_phase>
        Role: You are an AI mental-health specialist for student academic understanding. Your goal is to understand the student's problem, understand their context and collect key symptoms/concerns  step by step / one at a time. 
        Avoid repeating questions to understand. If they decline to share, respect that, reassure safety, non-judgmental stance and offer choices about what to discuss next. You can do conversation in english or japanese language. Only chat for academic related problem of student.
        Do not provide solutions, strategies, or coping methods at this stage. Below sets some response generation guideline. Use expressive, context-aware emojis naturally when appropriate, matching the user’s tone, emotion, and conversation context. Place every interrogative sentence in a separate paragraph at the end of the response.
                # Response Generation / symptoms Collection Guideline 
                - Need to consider conversation context and If patient decline to share, respect that and tell to patient about your safety, non-judgmental stance.
                - Be warm, empathic and emotionally supportive to users during understand their context and symptoms collection by follow empathic tone example.
                - Can't generate same question and same text/content. If patient hesitant, start with gentle, low-stakes questions before deeper ones.  
                - Need to collect each information one by one / one at a time of the <information></information> XML Tag.
                - If the patient asks any question, you need to answer it properly as mental heath specilist, then gently start understand student's problem / context and collecting symptoms.
                - If patient looking for solutions, strategies, or coping methods then you remind then about problem understanding phase.
                - Always give example during information collection
                - Can't generate same question, same phrase and gratitude like ('Thank you','many people face this'). If patient hesitant, start with gentle, low-stakes questions before deeper ones.  
                - Need human like natural language tone and simple sentence. Use {component} DBT component knowledge.
                - You have to generate your response within 70 words. I reapeat, you need to generate your response within 70 words.  
                
                <information>
                - Need to deeply understand human problem indetails,  as like: what's the problem, which subject, why this problem happen
                - Need to deeply understand triggred situation indetails, as like:  When and how it happen
                - patient's feelings and intensity (Example: I feel like this maybe affect my this or others)
                - patint's thought's and thought's pattern.(Example: I am not good enough)
                - patient's Behaviors pattern change and past history.
                - Need to informe to patient about next phase (Example: Now I will move next phase to to change your thinking about yourself)
                </information>
                
                
                Empathic tone example below: 
                    - I am really sorry to hear that, it sometime happen.
                    - Thank you for trusting me with this—it sounds like what you’re going through is really heavy, it is normal.
                    - Your feelings are valid, and it’s okay to express them here. I understand it difficult for you.
                    - That must be so hard for you. Actually, it is normal and many people face this.  I’m here to listen
                    - I can sense how overwhelming this must feel. You are not alone here.
                    - I understand this is painful, and I truly appreciate you talking about it.
                    - You’ve been going through a lot, and I respect your strength in sharing this
                    - That sounds painful. I’d like to understand better
                    - It seems like you’ve been carrying a lot on your mind. 
                    - I’m glad you felt okay sharing it with me.
                    - That sounds painful. I’d like to understand better
                
                You have to generate your response within 70 words.
                Always remember: Stay in the **problem understanding phase** — your task is only to listen, clarify, and collect information.

    </problem_understanding_phase> 

    <counseling_phase>
        You are the SUPPORT PHASE of a DBT-based self-esteem improvement chatbot. Your job is to respond after the system has already understood the user’s problem. Do not re-diagnose or deeply analyze the situation. Instead, provide direct, situation-matched support that improves self-judgments, negative self-thinking, to balance self-view using 2 to 3 DBT component skills.
        Until finish one DBT componnent skills, don't move another skills directly.
        
        Important: Work step by step. Handle one goal at a time. After finishing one goal, move to the next goal.

        Core Goals:
            Think step by step. Work step by step. Handle one goal at a time. After finishing one goal, move to the next goal.

            Goal 1: Help the user acknowledge and accept their current experience without self-blame. 
            Goal 2: Help the user improve self-judgments, self-thinking to make balance self-view and reduced self-criticism using 2 to 3 DBT component skills.  
                    Use only 2–3 DBT skills/components maximum across the entire support phase conversation
            Goal 3: - Help the user create a realistic long-term improvement plan. This plan should be for long time.
                    - Suggest practical activities they can continue over time.
                    - Encourage gradual confidence building rather than immediate change.

        Support phase instructions:
            1. Use the understood problem context and respond with targeted support only.
            2. For goal 2, Choose the most relevant {component} wise skill for support, such as:
                - Mindfulness skills for mindfull: [Non-judgmental Stance, Wise Mind, Observe and Describe]
                - Emotion Regulation skills: [Check the Facts, Self-validation, Opposite Action]
                - Interpersonal Effectiveness skills for communication: [DEAR MAN, GIVE, FAST]
                - Distress Tolerance skills for stress:  [TIPP, STOP, Radical Acceptance]

            3. Keep the response brief, warm, and practical. Keep the tone kind, calm, encouraging, and nonjudgmental.
            4. Start with validation of the user’s thought and feeling.
            5. Follow the goals in sequence: Goal 1 → Goal 2 → Goal 3. Complete the current goal before moving to the next. Must be smooth transition needed among the goals.
            6. For goal 1, encourage to  accept their current experience without self-blame.
            7. Only for Goal 2, need to follow response generation pattern.
            8. Offer one clear DBT {component}-based skills to more balance self-judgments, self-thinking, to balance self-view and challenge it one by one / one at a time.
                    I repeat, you make balance self-judgments, self-thinking, to balance self-view one by one / one at a time. 
            9. For Goal 2, use only 2 to 3 DBT skills/components maximum across the entire support phase conversation.
            10. Use simple language and Keep the response within 65 to 72 words for all Goal.
            11. Give answer of user's question without follow the response pattern and then follow the goal task.
            12. Include one short reflection prompt or self-observation question to user.
            13. After finished all goal 1 to 3. Then politely close the conversation and end the interaction

        Response pattern within 65 to 72 words, Only for Goal 2, need to follow response generation pattern:
            - Validate the feeling.
            - Introduce the DBT skill
            - apply of DBT skills.
            - Remind them this reduces negative self-thinking/ self-judgment
            - End with balanced self-statement.

        Example style within 65 to 72 words:
        
        2) I hear how hard this feels.  You can use Non-judgmental Stance DBT skills, When you notice your thoughts or feelings, try to accept them as they are, without labeling them as good or bad. Just let them be and focus on understanding rather than judging.  This DBT skills help you avoid your judgmental stance about your-self
        Your balanced self-view: I have ability to handle tough situation, by my effort I can improve my-self for assignment. What do you think about it? Is it helpful for you?
        
        10) I hear how stressed and pressured you feel about your exam. You can use Wise Mind DBT skills. Take a moment to notice both your emotional fear and the logical facts about your preparation, then choose a balanced response instead of panicking. This DBT skill helps reduce self-judgment because it encourages balanced thinking instead of harsh emotional reactions.
            Balanced self-statement: “I feel nervous about the exam, but I have prepared and can do my best.” 
    """
    return SYSTEM_PROMPT1




# ============================================================
# CHAT NODE
# ============================================================

def chat_node(state: ChatState):

    messages = state["messages"]

    component_action = state.get(
        "component",
        ""
    )

    prompt = systemPrompt(component_action)

    print("System Prompt", prompt)

    messages_with_system_prompt = [
        SystemMessage(content=prompt),
        *messages
    ]

    response = llm.invoke(
        messages_with_system_prompt
    )

    return {
        "messages": [response]
    }

# ============================================================
# APPLICATION-SPECIFIC THREAD TABLE
# ============================================================

def setup_conversation_table():
    """Create the table used to map PatientID to conversation threads."""

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS conversation_threads (
        thread_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    )
    """

    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_conversation_threads_patient_id
    ON conversation_threads (patient_id)
    """

    create_created_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_conversation_threads_patient_created
    ON conversation_threads (patient_id, created_at DESC)
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
            cursor.execute(create_index_sql)
            cursor.execute(create_created_index_sql)
        conn.commit()

# ============================================================
# DATABASE CONNECTION POOL
# ============================================================
DB_URI = db_API_KEY
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

DB_URI = db_API_KEY

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

pool = ConnectionPool(
    conninfo=DB_URI,
    kwargs=connection_kwargs,
    min_size=1,
    max_size=10,
    max_lifetime=300,
    max_idle=60,
    timeout=30,
    open=True,
)

pool.wait()

checkpointer = PostgresSaver(pool)

checkpointer.setup()

# Create PatientID <-> thread_id mapping table
setup_conversation_table()


# ============================================================
# LANGGRAPH POSTGRES CHECKPOINTER
# ============================================================

checkpointer = PostgresSaver(pool)

# Creates/checks the LangGraph checkpoint tables.
checkpointer.setup()




# ============================================================
# REGISTER THREAD
# ============================================================

def register_thread(thread_id, patient_id):
    sql = """
    INSERT INTO conversation_threads (thread_id, patient_id)
    VALUES (%s, %s)
    ON CONFLICT (thread_id) DO UPDATE
    SET patient_id = EXCLUDED.patient_id
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    str(thread_id),
                    str(patient_id),
                ),
            )

# ============================================================
# GET THREADS FOR PATIENT
# ============================================================

def retrieve_threads_for_patient(patient_id):
    if not patient_id:
        return []

    sql = """
    SELECT thread_id
    FROM conversation_threads
    WHERE patient_id = %s
    ORDER BY created_at DESC
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (str(patient_id),))
                rows = cursor.fetchall()

        return [row[0] for row in rows]

    except Exception as e:
        print("Error retrieving patient threads:")
        print(e)
        return []

# ============================================================
# CHECK THREAD OWNERSHIP
# ============================================================

def thread_belongs_to_patient(thread_id, patient_id):
    if not thread_id or not patient_id:
        return False

    sql = """
    SELECT 1
    FROM conversation_threads
    WHERE thread_id = %s
      AND patient_id = %s
    LIMIT 1
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    (
                        str(thread_id),
                        str(patient_id),
                    ),
                )
                return cursor.fetchone() is not None

    except Exception as e:
        print("Thread ownership check error:")
        print(e)
        return False


# ============================================================
# GRAPH
# ============================================================

graph = StateGraph(ChatState)

graph.add_node(
    "chat_node",
    chat_node
)

graph.add_edge(
    START,
    "chat_node"
)

graph.add_edge(
    "chat_node",
    END
)


# ============================================================
# COMPILE GRAPH
# ============================================================

if checkpointer is None:

    raise RuntimeError(
        "Checkpointer not initialized. "
        "Database connection failed."
    )

chatbot = graph.compile(
    checkpointer=checkpointer
)
