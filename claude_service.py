from anthropic import Anthropic
import streamlit as st
import re
import json

class ClaudeService:
    def __init__(self):
        self.client = Anthropic(api_key=st.secrets["anthropic_api_key"])
        # Get config or use default
        self.cards_per_session = st.session_state.get('config', {}).get('flashcards_per_session', 2)
        if st.session_state.get('debug_mode', False):
            st.sidebar.write("Cards per session:", self.cards_per_session)
    
    def extract_claude_content(self, response):
        """Helper method to extract text content from Claude API response"""
        if hasattr(response, 'content') and hasattr(response.content[0], 'text'):
            return response.content[0].text
        return str(response)

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
        
        return self.extract_claude_content(message)

    def create_feedback(self, prompt):
        evaluation_prompt = f"""Evaluate this flashcard answer by completing this JSON template - do NOT modify the structure, only replace the values:

        {{
            "correct": false,  // replace with true/false
            "explanation": "Type your explanation here with quotes"  // KEEP the quotes, replace this text
        }}

        Question: {prompt['question']}
        Correct answer: {prompt['answer']}
        User answer: {prompt['user_answer']}

        Rules:
        1. Keep the exact JSON structure with all quotes and braces
        2. Set "correct" to true if main concepts are understood
        3. Set "correct" to false if key concepts are missing
        4. Put your explanation between the quotes
        5. Do not remove any quotes or braces
        6. No comments or extra text - ONLY the JSON object
        """
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=150,
                temperature=0.1,
                system="You are a JSON template filler. Keep all quotes and braces, only replace the values inside the quotes.",
                messages=[{
                    "role": "user",
                    "content": evaluation_prompt
                }]
            )
            
            content = self.extract_claude_content(response)
            
            if st.session_state.get('debug_mode', False):
                st.write("DEBUG: Claude raw response:", content)
            
            # Simple JSON parsing - the response should be a clean JSON object
            try:
                result = json.loads(str(content).strip())
                result['correct'] = bool(result.get('correct', False))
                return json.dumps(result)
            except json.JSONDecodeError as e:
                if st.session_state.get('debug_mode', False):
                    st.write("DEBUG: JSON parse error:", str(e))
                raise ValueError("Response was not valid JSON - missing quotes or braces")
            
        except Exception as e:
            if st.session_state.get('debug_mode', False):
                st.write("DEBUG: Error in create_feedback:", str(e))
            raise