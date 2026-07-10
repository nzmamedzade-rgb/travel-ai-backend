# backend/database.py

import datetime
import os
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# Configures a lightweight local SQLite database file inside the backend directory
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travel_ai.db")

# Create the engine to interact with our database file
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# Set up a session factory to generate clean database transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models to inherit from
Base = declarative_base()


class SavedTrip(Base):
    """
    Database table schema layout for saving finalized AI travel records.
    Maps complex structural itineraries cleanly to columns.
    """
    __tablename__ = "saved_trips"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    trip_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    destination = Column(String, nullable=False)
    allocated_budget = Column(Float, nullable=False)
    
    # Stores the complex structured nested dictionary output from the AI as a plain string
    itinerary_json = Column(Text, nullable=False)
    
    # Optional fields for better querying
    total_cost = Column(Float, nullable=True)
    total_days = Column(Integer, nullable=True)
    eco_score = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class UserProfile(Base):
    """
    Database table for storing user profiles and preferences.
    """
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    profile_json = Column(Text, nullable=False)  # Stores user preferences as JSON
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


def init_database():
    """
    Initializes and sets up database infrastructure tables on disk.
    Called directly by main.py at app boot up.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


def get_database_session() -> Generator[Session, None, None]:
    """
    FastAPI Dependency Injector function. Yields an active transactional database 
    connection session per API request and safely terminates it when done.
    """
    database_session = SessionLocal()
    try:
        yield database_session
    finally:
        database_session.close()


# ============= Helper CRUD Functions =============

def save_trip(db: Session, trip_data: dict) -> SavedTrip:
    """
    Save a new trip to the database.
    
    Args:
        db: Database session
        trip_data: Dictionary containing trip information
        
    Returns:
        SavedTrip: The saved trip object
    """
    new_trip = SavedTrip(
        trip_id=trip_data.get("trip_id"),
        user_id=trip_data.get("user_id"),
        destination=trip_data.get("destination"),
        allocated_budget=trip_data.get("allocated_budget"),
        itinerary_json=trip_data.get("itinerary_json"),
        total_cost=trip_data.get("total_cost"),
        total_days=trip_data.get("total_days"),
        eco_score=trip_data.get("eco_score")
    )
    
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    return new_trip


def get_trip_by_id(db: Session, trip_id: str) -> SavedTrip:
    """
    Get a trip by its ID.
    
    Args:
        db: Database session
        trip_id: Trip identifier
        
    Returns:
        SavedTrip: The trip object or None
    """
    return db.query(SavedTrip).filter(SavedTrip.trip_id == trip_id).first()


def get_user_trips(db: Session, user_id: str, limit: int = 10) -> list:
    """
    Get all trips for a user.
    
    Args:
        db: Database session
        user_id: User identifier
        limit: Maximum number of trips to return
        
    Returns:
        list: List of trip objects
    """
    return db.query(SavedTrip).filter(
        SavedTrip.user_id == user_id
    ).order_by(
        SavedTrip.created_at.desc()
    ).limit(limit).all()


def delete_trip(db: Session, trip_id: str) -> bool:
    """
    Delete a trip by its ID.
    
    Args:
        db: Database session
        trip_id: Trip identifier
        
    Returns:
        bool: True if deleted, False if not found
    """
    trip = db.query(SavedTrip).filter(SavedTrip.trip_id == trip_id).first()
    if trip:
        db.delete(trip)
        db.commit()
        return True
    return False


def save_user_profile(db: Session, user_id: str, profile_data: dict) -> UserProfile:
    """
    Save or update a user profile.
    
    Args:
        db: Database session
        user_id: User identifier
        profile_data: Profile data as dictionary
        
    Returns:
        UserProfile: The saved profile object
    """
    import json
    
    # Check if profile exists
    existing = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if existing:
        # Update existing
        existing.profile_json = json.dumps(profile_data)
        existing.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        new_profile = UserProfile(
            user_id=user_id,
            profile_json=json.dumps(profile_data)
        )
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        return new_profile


def get_user_profile(db: Session, user_id: str) -> dict:
    """
    Get a user profile.
    
    Args:
        db: Database session
        user_id: User identifier
        
    Returns:
        dict: Profile data or empty dict
    """
    import json
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        return json.loads(profile.profile_json)
    return {}


# ============= Test Function =============

if __name__ == "__main__":
    print("🗄️ Testing Database...")
    
    # Initialize database
    init_database()
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Test: Create and save a trip
        import json
        import uuid
        
        test_trip = {
            "trip_id": str(uuid.uuid4()),
            "user_id": "test_user_123",
            "destination": "Paris",
            "allocated_budget": 1500.0,
            "itinerary_json": json.dumps({
                "destination": "Paris",
                "activities": ["Eiffel Tower", "Louvre"],
                "total_cost": 1200.0
            }),
            "total_cost": 1200.0,
            "total_days": 3,
            "eco_score": 78
        }
        
        saved = save_trip(db, test_trip)
        print(f"✅ Trip saved: {saved.trip_id}")
        
        # Test: Retrieve trip
        retrieved = get_trip_by_id(db, saved.trip_id)
        if retrieved:
            print(f"✅ Trip retrieved: {retrieved.destination}")
            print(f"   Budget: ${retrieved.allocated_budget}")
            print(f"   Created: {retrieved.created_at}")
        
        # Test: Get user trips
        user_trips = get_user_trips(db, "test_user_123")
        print(f"✅ User has {len(user_trips)} trips")
        
        # Test: Delete trip
        deleted = delete_trip(db, saved.trip_id)
        print(f"✅ Trip deleted: {deleted}")
        
        # Test: Save user profile
        profile = save_user_profile(db, "test_user_123", {
            "preferences": {
                "budget": "medium",
                "eco_interest": "high"
            },
            "past_trips": ["Paris", "Rome"]
        })
        print(f"✅ Profile saved for user: {profile.user_id}")
        
        # Test: Get user profile
        retrieved_profile = get_user_profile(db, "test_user_123")
        print(f"✅ Profile retrieved: {retrieved_profile}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n✅ Database tests complete!")