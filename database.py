import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import streamlit as st

Base = declarative_base()

class SpeciesLeaderboard(Base):
    __tablename__ = 'species_leaderboards'
    
    id = Column(Integer, primary_key=True)
    taxon_id = Column(Integer, nullable=False)
    leaderboard_type = Column(String(20), nullable=False)  # 'observers' or 'identifiers'
    leaderboard_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for fast lookups
    __table_args__ = (
        Index('idx_taxon_type', 'taxon_id', 'leaderboard_type'),
    )

class UserSpeciesCache(Base):
    __tablename__ = 'user_species_cache'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    cache_type = Column(String(20), nullable=False)  # 'observations' or 'identifications'
    species_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for fast lookups
    __table_args__ = (
        Index('idx_user_type', 'user_id', 'cache_type'),
    )

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def get_species_leaderboard(self, taxon_id: int, leaderboard_type: str, max_age_days: int = 30):
        """Get cached leaderboard data if it exists and is recent enough"""
        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
        
        result = self.session.query(SpeciesLeaderboard).filter(
            SpeciesLeaderboard.taxon_id == taxon_id,
            SpeciesLeaderboard.leaderboard_type == leaderboard_type,
            SpeciesLeaderboard.created_at > cutoff_time
        ).first()
        
        if result:
            return json.loads(result.leaderboard_data)
        return None
    
    def cache_species_leaderboard(self, taxon_id: int, leaderboard_type: str, data: list):
        """Cache leaderboard data for a species"""
        try:
            # Remove old cache for this species/type
            self.session.query(SpeciesLeaderboard).filter(
                SpeciesLeaderboard.taxon_id == taxon_id,
                SpeciesLeaderboard.leaderboard_type == leaderboard_type
            ).delete()
            
            # Add new cache entry
            cache_entry = SpeciesLeaderboard(
                taxon_id=taxon_id,
                leaderboard_type=leaderboard_type,
                leaderboard_data=json.dumps(data)
            )
            self.session.add(cache_entry)
            self.session.commit()
        except Exception as e:
            error_details = [
                f"Function: cache_species_leaderboard",
                f"Taxon ID: {taxon_id}",
                f"Type: {leaderboard_type}",
                f"Data size: {len(data) if data else 0} items",
                f"Error: {str(e)}"
            ]
            st.warning(f"Database cache failed: {' | '.join(error_details)}")
            self.session.rollback()
    
    def get_user_species_cache(self, user_id: int, cache_type: str, max_age_days: int = 30):
        """Get cached user species data if it exists and is recent enough"""
        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
        
        result = self.session.query(UserSpeciesCache).filter(
            UserSpeciesCache.user_id == user_id,
            UserSpeciesCache.cache_type == cache_type,
            UserSpeciesCache.created_at > cutoff_time
        ).first()
        
        if result:
            return json.loads(result.species_data)
        return None
    
    def cache_user_species(self, user_id: int, cache_type: str, data: list):
        """Cache user species data"""
        try:
            # Remove old cache for this user/type
            self.session.query(UserSpeciesCache).filter(
                UserSpeciesCache.user_id == user_id,
                UserSpeciesCache.cache_type == cache_type
            ).delete()
            
            # Add new cache entry
            cache_entry = UserSpeciesCache(
                user_id=user_id,
                cache_type=cache_type,
                species_data=json.dumps(data)
            )
            self.session.add(cache_entry)
            self.session.commit()
        except Exception as e:
            error_details = [
                f"Function: cache_user_species",
                f"User ID: {user_id}",
                f"Cache type: {cache_type}",
                f"Data size: {len(data) if data else 0} items",
                f"Error: {str(e)}"
            ]
            st.warning(f"User cache failed: {' | '.join(error_details)}")
            self.session.rollback()
    
    def cleanup_old_cache(self, max_age_days: int = 30):
        """Clean up old cache entries"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
            
            # Clean up old species leaderboards
            self.session.query(SpeciesLeaderboard).filter(
                SpeciesLeaderboard.created_at < cutoff_time
            ).delete()
            
            # Clean up old user species cache
            self.session.query(UserSpeciesCache).filter(
                UserSpeciesCache.created_at < cutoff_time
            ).delete()
            
            self.session.commit()
        except Exception as e:
            st.warning(f"Failed to cleanup old cache: {str(e)}")
            self.session.rollback()
    
    def close(self):
        """Close the database session"""
        self.session.close()