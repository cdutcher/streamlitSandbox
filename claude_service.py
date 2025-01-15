from anthropic import Anthropic
import streamlit as st

class ClaudeService:
    def __init__(self):
        self.client = Anthropic(api_key=st.secrets["anthropic_api_key"])
    
    def create_flashcards(self, topic):
        prompt = f"""Generate 10 flashcards about {topic}.
        You MUST respond with ONLY a JSON array in this EXACT format:
        [
            {{"question":"What is X?","answer":"X is Y"}},
            {{"question":"How does Z work?","answer":"Z works by W"}},
            {{"question":"Define A?","answer":"A is B"}},
            {{"question":"Explain C?","answer":"C means D"}},
            {{"question":"Why is E important?","answer":"E matters because F"}}
        ]

        Critical requirements:
        - EXACT format: no spaces after colons, no newlines
        - EXACTLY 10 flashcards
        - NO extra text before or after the JSON
        - NO TextBlock wrapper
        - NO escaped quotes
        - Single quotes are NOT allowed
        - Questions end with question mark
        - Answers are complete sentences
        """
        
        message = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.7,
            system="You are a JSON generator. ONLY output valid, minified JSON arrays.",
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        return message.content 

    def create_feedback(self, prompt):
        evaluation_prompt = f"""Evaluate if this answer is correct.
        You MUST respond with ONLY a JSON object in this EXACT format, with NO other text:
        {{"correct":true,"explanation":"Correct because..."}}
        or
        {{"correct":false,"explanation":"Incorrect because..."}}

        Critical requirements:
        - EXACT format shown above
        - NO spaces after colons
        - NO newlines in output
        - NO TextBlock wrapper
        - NO escaped quotes
        - Single quotes are NOT allowed
        - Explanation must be clear but brief
        - ONLY output the JSON object
        - NO additional text or formatting
        - NO markdown
        - NO line breaks

        Question: {prompt['question']}
        Correct answer: {prompt['answer']}
        User answer: {prompt['user_answer']}

        Compare meaning, not exact wording. User answer is correct if core concepts match.
        """
        
        message = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=150,
            temperature=0.3,
            system="You are a JSON generator. ONLY output valid, minified JSON objects with NO extra text or formatting.",
            messages=[{
                "role": "user",
                "content": evaluation_prompt
            }]
        )
        return message.content 