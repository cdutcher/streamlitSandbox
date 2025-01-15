from anthropic import Anthropic
import streamlit as st

class ClaudeService:
    def __init__(self):
        self.client = Anthropic(api_key=st.secrets["anthropic_api_key"])
        # Get config or use default
        self.cards_per_session = st.session_state.get('config', {}).get('flashcards_per_session', 3)
    
    def create_flashcards(self, topic):
        # Create example cards based on count
        example_cards = [
            '{{"question":"What is X?","answer":"X is Y"}}',
            '{{"question":"How does Z work?","answer":"Z works by W"}}',
            '{{"question":"Define A?","answer":"A is B"}}'
        ][:self.cards_per_session]
        
        prompt = f"""Generate {self.cards_per_session} flashcards about {topic}.
        You MUST respond with ONLY a JSON array in this EXACT format:
        [
            {",".join(example_cards)}
        ]

        Critical requirements:
        - EXACT format: no spaces after colons, no newlines
        - EXACTLY {self.cards_per_session} flashcards
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
        You MUST respond with ONLY a minified JSON object in this EXACT format:
        {{"correct":false,"explanation":"Incorrect because..."}}

        Example responses:
        {{"correct":true,"explanation":"Correct! The answer demonstrates understanding of the key concepts."}}
        {{"correct":false,"explanation":"Incorrect. The answer is missing key information about..."}}

        Critical requirements:
        - Output MUST be a single line of minified JSON
        - NO whitespace after colons or between properties
        - NO line breaks or extra spaces
        - NO TextBlock wrapper
        - NO escaped quotes
        - NO markdown or formatting
        - NO additional text before or after JSON

        Question: {prompt['question']}
        Correct answer: {prompt['answer']}
        User answer: {prompt['user_answer']}

        Compare meaning and key concepts, not exact wording.
        """
        
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=150,
            temperature=0.1,  # Lower temperature for more consistent formatting
            system="You are a JSON generator. Output ONLY minified, single-line JSON objects with no extra text.",
            messages=[{
                "role": "user",
                "content": evaluation_prompt
            }]
        )
        return response.content  # Claude API returns content directly 