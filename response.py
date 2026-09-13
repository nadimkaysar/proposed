import openai
from openai import OpenAI
import json
import streamlit as st


OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
def SubsetSelection(prompt):
    client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key=OPENAI_API_KEY,
        )

    chat_completion = client.chat.completions.create(
            model="gpt-4o",
            temperature = 0.7,
            response_format={ "type": "json_object" },
            messages=[
                    {"role": "system", "content": "Follow user Prompt"},
                    {"role": "user", "content": prompt}
                ]
        )
    chat_completion = str(chat_completion.choices[0].message.content)
    return chat_completion




schema_behaviour = '''
{
  "input": {
    "user_previous_utterance": "string",
    "user_last_utterance": "string",
    "emotional_state": {
      "emotions": [
        {
          "type": "string",
          "intensity": "string"
        }
      ]
    },
    "context": "First session. No specific incidents mentioned"
  },
  "predictions": {
    "Mindfulness": {
      "possible_states": [
        {
          "mental_state": "Emotion: 'string'; Thought: 'string'; Symptoms: 'string'",
          "behaviors": [
            {
              "behavior_description": "string",
              "reward": "number"
            }
          ],
          "probability": "number"
        }
      ]
    },
    "Distress_Tolerance": {
      "possible_states": [
        {
          "mental_state": "Emotion: 'string'; Thought: 'string'; Symptoms: 'string'",
          "behaviors": [
            {
              "behavior_description": "string",
              "reward": "number"
            }
          ],
          "probability": "number"
        }
      ]
    },
    "Interpersonal_Effectiveness": {
      "possible_states": [
        {
          "mental_state": "Emotion: 'string'; Thought: 'string'; Symptoms: 'string'",
          "behaviors": [
            {
              "behavior_description": "string",
              "reward": "number"
            }
          ],
          "probability": "number"
        }
      ]
    },
    "Emotion_Regulation": {
      "possible_states": [
        {
          "mental_state": "Emotion: 'string'; Thought: 'string'; Symptoms: 'string'",
          "behaviors": [
            {
              "behavior_description": "string",
              "reward": "number"
            }
          ],
          "probability": "number"
        }
      ]
    },
    "IsSuicide": "number"
  }
}
'''

def determine_reward_with_behaviour(utterance,last_utterace,previous_action):
    NextTask_prompt = f"""
    Context: You are part of a mental health dialogue management system with Dialectical Behavior Therapy-based therapeutic intervention for student and you are working in process of for selecting the most appropriate DBT component based on the user's current utterance, and conversation context. 
    The selecting process is by using game theoretic process with game tree. In this DBT component selection game process, there are four DBT component as actions and each action effectiveness will evaluate by generated mental state, behaviour, reward and probability using below evaluation guideline of task instruction. 
    Finally, the selected best action is responsible for next response generation by utilizing the own responsibility and skills. Therefore, the mental states, behaviour, reward and probability generation is your current goal/task by utilizing below task instructions.
    Please output your predictions for each DBT component's potential outcomes in the following JSON format. Moreover, you are specialized in DBT.

      Conversation Context:
      <Context> {utterance} and {last_utterace}</Context>
      
      Task instruction Below:
      
      Think step by step as a Dialactical Behaviour Therapist specilist with thinking loop for each DBT component. Repeat the following reasoning process independently for each DBT component (Emotion Regulation, Distress Tolerance, Mindfulness, and Interpersonal Effectiveness): 
      1 Generate possible mental states. 2 For each mental state, generate possible behaviors. 3 Estimate the reward for each behavior. 4 Estimate the probability of each mental state. 5 After completing the current DBT component, repeat Steps 1–4 for the next DBT component.
        
        Previous action
            - If there is no previous previous_action, consider it start of tree as a root.
            - Need to consider previous action {previous_action} as a root for game tree.

        Now, second step of thinking, you need to detect possible mental state here for every DBT component to measuring effectiveness of following component to address mental state and  mental state generation guideline is below. For each DBT component, perform an independent thinking loop to generate mental states and it's probability. Then perform an independent thinking loop to generate behavior and its reward for each mental state. 
        
        Possible Mental State Generation Detection Guidline are below:
            - You need to generate or include at least two possible mental states per component with no upper limit.
            - You have specialization in Dialactical Behaviour Therapy and you are skilled in every DBT component.
            - Need to generate mental state of each DBT component by utilizing each DBT component skills.
            - You need understand patient previous conversation context and last utterance from the <Context><Context> XML tag. After that, you need to detect patient "emotion", "Thoughts" and "symptoms" by using DBT specialization and skills.
            - You have to add emotion, thoughts and symptoms in "mental_state" of the json schema. As example,"Emotion: 'sad' Thought's: 'I am not good' Symptoms: 'hopeless and tried for lots of assignment which indicator of depression'"
        
        Now, third step of thinking, you need to detect possible patient's / Human's behaviour here to address behaviour and behaviour generation guidline is below.
            
            - You need understand and analysis patient's or Human's full conversation context from the <Context><Context> XML tag to detect patient's behaviour. 
            - You need to generate or include at least two behaviour per mental state with no upper limit.
            - You need to predict patient current behaviour from the <Context><Context> XML tag.
            - Behaviour can be what the patient are doing or saying in conversation context. Behaviour Example: (e.g., “stuck....“, “avoids…”, “interrupts…”, “checks phone repeatedly…”)
            - Each behavior must be grounded in specific evidence from the conversation context.
            - Behaviour descriptions should be specific and behaviorally oriented.
        
        Now, fourth step of thinking, you need to evalaute each DBT component using previous detected behaviours by giving reward value. Guideline are below.
        
        Reward Value Guideline & Rules are below:
            - Need to consider and understand the conversation context from the <Context><Context> XML tag to generate reward by evalaute DBT compoent.
            - Reward value should consider Dialectical Behavior Therapy-based psychological principles for each DBT component and for balance self-thought view of patient.
            - You have to generate reward for within 0.0 to 1.0 by follow bellow rules:
                - 1.0: Optimal therapeutic effect achievable by the following DBT component for balancing self-reflective views.
                - 0.8-0.9: Significant positive improvement expected and balance self-thought view positively by the following DBT component.
                - 0.6-0.7: Moderate improvement expected and balance the self-thought view of the patient by the following DBT component.
                - 0.4-0.5: Slight improvement expected and balance the self-thought view of the patient  by following the DBT component.
                - 0.2-0.3: Minimal improvement expected and balance the self-thought view of the patient by following the DBT component.
                - 0.0-0.1: Potential negative effect by that following DBT component.
            - Reward values should consider both immediate emotional relief and long-term therapeutic benefits by following DBT component for current conversation context.
            - Reward value consider following DBT component effectiveness to address patinet's thinking pattern.
            - Reward value consider following DBT component effectiveness to symptom reduction and address possible mental states for current conversation context.
            - Reward value consider following DBT component effectiveness and significance of responsibility and skills to handle the patient current behavioural situation which is given in the <Context><Context> XML tag. The each DBT component responsibility and skills are given in the <responsibility & skills></ responsibility & skills > XML tag.
        
        Now, fifth step of thinking, you need to evalaute each DBT component using previous detected mental state by giving probability value. Guideline are below.
        
        Probability Value Guideline & Rules are below:
            - Need to consider and understand the conversation context from the <Context><Context> XML tag to generate probability.
            - You have to generate propability for within 0.0 to 1.0.
            - The sum of probabilities within each component's possible mental states must equal 1.0.
            - Probability value should consider Dialectical Behavior Therapy-based psychological principles for each DBT component.
            - Propability value should considering following DBT component reliability, effectiveness to address patient current mental state situation is in the given <Context><Context> XML tag.
            - Propability value should consider user's behaviar adressing capability by Dialectical Behavior Therapy component.
          
        Instruction for User Uttereance
            - you need to append "{last_utterace}" in user_last_utterence of the output json_schema.
            - you need to append all context = "{utterance}" in user_previous_utterance of the output json_schema.

        Risk detection:
        Finally and again, you need to analyze the text that in the below <lastutterence> </lastutterence> XML Tag.  If user/patient have suicidal thought and attempt it in the below <lastutterence> </lastutterence> XML Tag, then you need to return 1 else 0 in 'IsSuicide' as a json.
          <lastutterence> {last_utterace} </lastutterence>

        <responsibility & skills>
        Key Skills for all DBT component:
        Mindfulness: Observe: Notice what’s happening, Non-judgmental stance: Avoid labeling thoughts or feelings as “good” or “bad.”, One-mindfully: Focus on one thing at a time,  Wise Mind: Balancing emotion mind and reason mind.
        Distress Tolerance: TIPP skills, Radical Acceptance: Accepting reality as it is.
        Emotion Regulation: Check the facts: Determine if emotions fit the situation, Opposite action: Do the opposite of what the emotion urges when it's not effective.
                            Build positive experiences: Short-term and long-term planing for positive outcomes.
        Interpersonal Effectiveness: GIVE, DEAR MAN (for asking/assertiveness): Describe, Express, Assert, Reinforce, Mindful, Appear confident, Negotiate.

        Responsibility:
      - Mindfulness responsibility is helps patient become more aware of their thoughts, focus in single thing, by using Non-judgmental stance, One Mindful, and Non-judgmental stance skills.
      - Emotion Regulation responsibility is helps patient identify and regulate their emotions by Check the facts, Opposite Action, and Build positive experiences skills.
      - Distress Tolerance responsibility is helps patient cope with distressing emotions without harmful behaviors in  extremely stressful situation by using TIIP, and STOP skills. 
      - Interpersonal Effectiveness responsibility is helps patient improve communication and relationship-building by using DEAR-MAN, GIVE skills.
        </ responsibility & skills > 

      You have to return by following json schema as like ={json.dumps(schema_behaviour)}. I repeat, You have to return by follwing json schema as like ={json.dumps(schema_behaviour)}
      """

    return NextTask_prompt
	
