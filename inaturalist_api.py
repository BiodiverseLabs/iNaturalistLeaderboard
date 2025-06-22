import requests
import time
from typing import Dict, List, Optional
import streamlit as st

class iNaturalistAPI:
    """Client for interacting with the iNaturalist API v1"""
    
    def __init__(self):
        self.base_url = "https://api.inaturalist.org/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'iNaturalist-Dashboard/1.0',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to the iNaturalist API with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            raise
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            raise
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information by username"""
        try:
            response = self._make_request("/users/autocomplete", {"q": username})
            
            # Find exact username match
            if response.get('results'):
                for user in response['results']:
                    if user.get('login', '').lower() == username.lower():
                        return user
                
                # If no exact match, check if there's a close match
                for user in response['results']:
                    if username.lower() in user.get('login', '').lower():
                        return user
            
            return None
            
        except Exception as e:
            st.error(f"Error fetching user info: {str(e)}")
            return None
    
    def get_user_observation_count(self, user_id: int) -> int:
        """Get total observation count for a user"""
        try:
            response = self._make_request("/observations", {
                "user_id": user_id,
                "per_page": 1,
                "only_id": "true"
            })
            return response.get('total_results', 0)
            
        except Exception as e:
            st.error(f"Error fetching observation count: {str(e)}")
            return 0
    
    def get_user_observations_by_species(self, user_id: int, limit: int = 200) -> List[Dict]:
        """Get user's observations grouped by species"""
        try:
            all_species = []
            page = 1
            
            while len(all_species) < limit:
                response = self._make_request("/observations/species_counts", {
                    "user_id": user_id,
                    "per_page": min(200, limit - len(all_species)),
                    "page": page
                })
                
                results = response.get('results', [])
                if not results:
                    break
                
                all_species.extend(results)
                page += 1
                
                # Add small delay to be respectful to the API
                time.sleep(0.1)
            
            return all_species[:limit]
            
        except Exception as e:
            st.error(f"Error fetching user observations by species: {str(e)}")
            return []
    
    def get_top_observer_species(self, user_id: int, progress_callback=None) -> List[Dict]:
        """
        Get species where the user is the top observer globally.
        This checks each species the user has observed to see if they're #1 globally.
        """
        try:
            # Get user's observed species (limit to top 50 to reduce API calls)
            user_species = self.get_user_observations_by_species(user_id, 50)
            
            top_observer_species = []
            
            # For each species, check if this user is the top observer
            for i, species in enumerate(user_species):
                if progress_callback and i % 5 == 0:  # Update progress every 5 species
                    progress_callback(f"Checking species {i+1} of {len(user_species)}...")
                
                taxon = species.get('taxon', {})
                taxon_id = taxon.get('id')
                user_count = species.get('count', 0)
                
                if not taxon_id or user_count == 0:
                    continue
                
                # Get the top observers for this species
                observers = self.get_species_observers_leaderboard(taxon_id)
                
                if observers and len(observers) > 0:
                    # Check if our user is the top observer
                    top_observer = observers[0]
                    if top_observer.get('user_id') == user_id:
                        top_observer_species.append({
                            'scientific_name': taxon.get('name', 'Unknown'),
                            'common_name': taxon.get('preferred_common_name', 'No common name'),
                            'observation_count': user_count,
                            'taxon_id': taxon_id,
                            'rank': taxon.get('rank', 'unknown'),
                            'global_rank': 1
                        })
                
                # Add delay to be respectful to API
                time.sleep(0.15)
            
            return top_observer_species
            
        except Exception as e:
            st.error(f"Error fetching top observer species: {str(e)}")
            return []
    
    def get_user_identifications_by_species(self, user_id: int, limit: int = 200) -> List[Dict]:
        """Get user's identifications grouped by species"""
        try:
            all_species = []
            page = 1
            
            while len(all_species) < limit:
                response = self._make_request("/identifications/species_counts", {
                    "user_id": user_id,
                    "per_page": min(200, limit - len(all_species)),
                    "page": page
                })
                
                results = response.get('results', [])
                if not results:
                    break
                
                all_species.extend(results)
                page += 1
                
                # Add small delay to be respectful to the API
                time.sleep(0.1)
            
            return all_species[:limit]
            
        except Exception as e:
            st.error(f"Error fetching user identifications by species: {str(e)}")
            return []
    
    def get_top_identifier_species(self, user_id: int, progress_callback=None) -> List[Dict]:
        """
        Get species where the user is a top identifier globally.
        This checks each species the user has identified to see if they're #1 globally.
        """
        try:
            # Get user's identified species (limit to top 50 to reduce API calls)
            user_species = self.get_user_identifications_by_species(user_id, 50)
            
            top_identifier_species = []
            
            # For each species, check if this user is the top identifier
            for i, species in enumerate(user_species):
                if progress_callback and i % 5 == 0:  # Update progress every 5 species
                    progress_callback(f"Checking species {i+1} of {len(user_species)}...")
                
                taxon = species.get('taxon', {})
                taxon_id = taxon.get('id')
                user_count = species.get('count', 0)
                
                if not taxon_id or user_count == 0:
                    continue
                
                # Get the top identifiers for this species
                identifiers = self.get_species_identifiers_leaderboard(taxon_id)
                
                if identifiers and len(identifiers) > 0:
                    # Check if our user is the top identifier
                    top_identifier = identifiers[0]
                    if top_identifier.get('user_id') == user_id:
                        top_identifier_species.append({
                            'scientific_name': taxon.get('name', 'Unknown'),
                            'common_name': taxon.get('preferred_common_name', 'No common name'),
                            'identification_count': user_count,
                            'taxon_id': taxon_id,
                            'rank': taxon.get('rank', 'unknown'),
                            'global_rank': 1
                        })
                
                # Add delay to be respectful to API
                time.sleep(0.15)
            
            return top_identifier_species
            
        except Exception as e:
            st.error(f"Error fetching top identifier species: {str(e)}")
            return []
    
    def get_species_observers_leaderboard(self, taxon_id: int, place_id: Optional[int] = None) -> List[Dict]:
        """Get leaderboard of observers for a specific species"""
        try:
            params = {
                "taxon_id": taxon_id,
                "per_page": 100,
                "verifiable": "true"
            }
            
            if place_id:
                params["place_id"] = place_id
            
            response = self._make_request("/observations/observers", params)
            return response.get('results', [])
            
        except Exception as e:
            st.error(f"Error fetching species observers leaderboard: {str(e)}")
            return []
    
    def get_species_identifiers_leaderboard(self, taxon_id: int, place_id: Optional[int] = None) -> List[Dict]:
        """Get leaderboard of identifiers for a specific species"""
        try:
            params = {
                "taxon_id": taxon_id,
                "per_page": 100
            }
            
            if place_id:
                params["place_id"] = place_id
            
            response = self._make_request("/identifications/identifiers", params)
            return response.get('results', [])
            
        except Exception as e:
            st.error(f"Error fetching species identifiers leaderboard: {str(e)}")
            return []
