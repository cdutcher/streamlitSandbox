from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime

# Create base class for declarative models
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    username = Column(String, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    
    def __del__(self):
        # Close session when object is destroyed
        self.session.close() 