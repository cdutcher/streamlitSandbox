from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime, timedelta

# Create base class for declarative models
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    username = Column(String, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    flashcards = relationship("Flashcard", back_populates="user")

class Flashcard(Base):
    __tablename__ = 'flashcards'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.username'))
    question = Column(String)
    answer = Column(String)
    box_number = Column(Integer, default=1)  # Leitner box number (1-5)
    next_review = Column(DateTime)
    last_difficulty = Column(String)  # easy, medium, hard
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="flashcards")

class UserDB:
    def __init__(self):
        # Create PostgreSQL connection URL from secrets
        conn_str = (f"postgresql://{st.secrets['postgres']['user']}:"
                   f"{st.secrets['postgres']['password']}@"
                   f"{st.secrets['postgres']['host']}:"
                   f"{st.secrets['postgres']['port']}/"
                   f"{st.secrets['postgres']['database']}")
        
        self.engine = create_engine(conn_str)
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def get_user_credentials(self):
        users = self.session.query(User).all()
        
        credentials = {
            'usernames': {
                user.username: {
                    'email': user.email,
                    'name': user.name,
                    'password': user.password
                } for user in users
            }
        }
        return credentials
    
    def add_user(self, username, email, name, password):
        try:
            hashed_password = stauth.Hasher([password]).generate()[0]
            new_user = User(
                username=username,
                email=email,
                name=name,
                password=hashed_password
            )
            self.session.add(new_user)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e
    
    def get_user(self, username):
        return self.session.query(User).filter(User.username == username).first()
    
    def delete_user(self, username):
        user = self.get_user(username)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False
    
    def validate_signup(self, username, email, password):
        if not username or not email or not password:
            raise ValueError("All fields are required")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        if '@' not in email:
            raise ValueError("Invalid email format")
        
        # Check if username already exists
        existing_user = self.get_user(username)
        if existing_user:
            raise ValueError("Username already exists")
    
    def save_flashcard_result(self, username, question, answer, is_correct, difficulty):
        card = self.session.query(Flashcard).filter(
            Flashcard.user_id == username,
            Flashcard.question == question
        ).first()
        
        if not card:
            card = Flashcard(
                user_id=username,
                question=question,
                answer=answer,
                box_number=1  # Initialize box_number for new cards
            )
            self.session.add(card)
        
        # Update box number based on Leitner system
        if is_correct:
            if difficulty == "easy":
                card.box_number = min(5, card.box_number + 1)
            elif difficulty == "medium":
                card.box_number = min(5, card.box_number)
        else:
            card.box_number = max(1, card.box_number - 1)
        
        # Set next review date based on box number
        intervals = {
            1: timedelta(days=1),
            2: timedelta(days=3),
            3: timedelta(days=7),
            4: timedelta(days=14),
            5: timedelta(days=30)
        }
        card.next_review = datetime.utcnow() + intervals[card.box_number]
        card.last_difficulty = difficulty
        
        self.session.commit()
    
    def __del__(self):
        # Close session when object is destroyed
        self.session.close() 