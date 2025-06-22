import requests
import time
from typing import Dict, List, Optional
import streamlit as st
from database import DatabaseManager

class iNaturalistAPI:
    """Client for interacting with the iNaturalist API v1"""
    
    def __init__(self):
        self.base_url = "https://api.inaturalist.org/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'iNaturalist-Dashboard/1.0',
            'Accept': 'application/json'
        })
        try:
            self.db = DatabaseManager()
        except Exception as e:
            st.warning(f"Database connection failed: {str(e)}. Running without cache.")
            self.db = None
    
    def _make_request(self, endpoint: str, params: Dict = None, retry_count: int = 3) -> Dict:
        """Make a request to the iNaturalist API with error handling and retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retry_count):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                # Handle rate limiting
                if response.status_code == 429:
                    # Log detailed rate limit information
                    headers_info = []
                    for header, value in response.headers.items():
                        if 'rate' in header.lower() or 'limit' in header.lower() or 'retry' in header.lower():
                            headers_info.append(f"{header}: {value}")
                    
                    error_msg = f"Rate limit hit (429). Headers: {', '.join(headers_info) if headers_info else 'No rate limit headers found'}"
                    st.error(error_msg)
                    
                    # Also log the full response for debugging
                    try:
                        if hasattr(response, 'text'):
                            st.error(f"429 Response body: {response.text[:300]}")
                    except:
                        pass
                    
                    if attempt < retry_count - 1:
                        wait_time = (attempt + 1) * 10  # Exponential backoff: 10s, 20s, 30s
                        st.warning(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        st.error("Rate limit exceeded. Please try again later.")
                        raise requests.exceptions.HTTPError("429 Too Many Requests")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429 and attempt < retry_count - 1:
                    continue
                
                # Enhanced error logging
                error_details = [
                    f"Endpoint: {endpoint}",
                    f"Status: {response.status_code}",
                    f"Error: {str(e)}",
                    f"Attempt: {attempt + 1}/{retry_count}"
                ]
                
                # Log response headers
                if hasattr(response, 'headers'):
                    relevant_headers = {k: v for k, v in response.headers.items() 
                                      if any(keyword in k.lower() for keyword in ['rate', 'limit', 'retry', 'content-type'])}
                    if relevant_headers:
                        error_details.append(f"Headers: {relevant_headers}")
                
                # Log response body if small enough
                try:
                    if hasattr(response, 'text') and len(response.text) < 500:
                        error_details.append(f"Response: {response.text}")
                except:
                    pass
                
                st.error(f"API request failed: {' | '.join(error_details)}")
                raise
            except requests.exceptions.RequestException as e:
                if attempt < retry_count - 1:
                    st.warning(f"Request failed (attempt {attempt + 1}/{retry_count}): {str(e)}. Retrying in 1 second...")
                    time.sleep(1)  # Brief wait before retry
                    continue
                
                # Enhanced error logging for final failure
                error_details = [
                    f"Endpoint: {endpoint}",
                    f"Error Type: {type(e).__name__}",
                    f"Error: {str(e)}",
                    f"Final attempt: {attempt + 1}/{retry_count}"
                ]
                st.error(f"API request failed after {retry_count} attempts: {' | '.join(error_details)}")
                raise
            except Exception as e:
                error_details = [
                    f"Endpoint: {endpoint}",
                    f"Error Type: {type(e).__name__}",
                    f"Error: {str(e)}",
                    f"Attempt: {attempt + 1}/{retry_count}"
                ]
                st.error(f"Unexpected API error: {' | '.join(error_details)}")
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
            # Check cache first
            if self.db:
                cached_data = self.db.get_user_species_cache(user_id, 'observations')
                if cached_data:
                    st.info("Using cached observation data")
                    return cached_data[:limit]
            
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
                
                # If we hit the limit, break
                if len(all_species) >= limit:
                    break
            
            # Cache the results
            if self.db and all_species:
                self.db.cache_user_species(user_id, 'observations', all_species)
            
            return all_species[:limit]
            
        except Exception as e:
            st.error(f"Error fetching user observations by species: {str(e)}")
            return []
    
    def get_observer_rankings(self, user_id: int, progress_callback=None) -> Dict[int, List[Dict]]:
        """
        Get species where the user is ranked in top 3 globally as an observer.
        Returns a dictionary with rankings: {1: [...], 2: [...], 3: [...]}
        """
        try:
            # Get user's observed species (reasonable limit to avoid rate limiting)
            user_species = self.get_user_observations_by_species(user_id, 500)
            
            rankings = {1: [], 2: [], 3: []}
            total_species = len(user_species)
            
            # For each species, check the user's global ranking
            for i, species in enumerate(user_species):
                taxon = species.get('taxon', {})
                taxon_id = taxon.get('id')
                user_count = species.get('count', 0)
                
                if not taxon_id or user_count == 0:
                    # Update progress for skipped species
                    if progress_callback:
                        remaining_species = total_species - i - 1
                        estimated_remaining = remaining_species * 2.0  # Conservative estimate
                        progress_callback(i + 1, total_species, estimated_remaining)
                    continue
                
                # Update progress BEFORE API call to avoid counting during retries
                if progress_callback:
                    remaining_species = total_species - i - 1
                    
                    if self.db:
                        # Sample upcoming species to estimate cache hit ratio
                        cached_count = 0
                        api_needed_count = 0
                        
                        for check_idx in range(i + 1, min(i + 11, total_species)):
                            if check_idx < len(user_species):
                                check_taxon = user_species[check_idx].get('taxon', {})
                                check_taxon_id = check_taxon.get('id')
                                if check_taxon_id:
                                    cached_data = self.db.get_species_leaderboard(check_taxon_id, 'observers')
                                    if cached_data:
                                        cached_count += 1
                                    else:
                                        api_needed_count += 1
                        
                        # Calculate time based on cache ratio and rate limiting
                        if cached_count + api_needed_count > 0:
                            cache_ratio = cached_count / (cached_count + api_needed_count)
                            estimated_api_calls = remaining_species * (1 - cache_ratio)
                            estimated_remaining = (estimated_api_calls * 2.0) + (remaining_species * cache_ratio * 0.1)
                        else:
                            estimated_remaining = remaining_species * 2.0
                    else:
                        estimated_remaining = remaining_species * 2.0
                    
                    progress_callback(i + 1, total_species, estimated_remaining)
                
                # Get the top observers for this species (uses cache if available)
                observers = self.get_species_observers_leaderboard(taxon_id)
                
                if observers and len(observers) >= 3:
                    # Check if our user is in top 3
                    for rank, observer in enumerate(observers[:3], 1):
                        if observer.get('user_id') == user_id:
                            rankings[rank].append({
                                'scientific_name': taxon.get('name', 'Unknown'),
                                'common_name': taxon.get('preferred_common_name', 'No common name'),
                                'observation_count': user_count,
                                'taxon_id': taxon_id,
                                'rank': taxon.get('rank', 'unknown'),
                                'global_rank': rank
                            })
                            break
                
                # No delay here - delays are handled inside the leaderboard functions
            
            # Final progress update
            if progress_callback:
                progress_callback(total_species, total_species, 0)
            
            return rankings
            
        except Exception as e:
            error_details = [
                f"Function: get_observer_rankings",
                f"User ID: {user_id}",
                f"Error Type: {type(e).__name__}",
                f"Error: {str(e)}"
            ]
            st.error(f"Observer rankings failed: {' | '.join(error_details)}")
            return {1: [], 2: [], 3: []}
    
    def get_user_identifications_by_species(self, user_id: int, limit: int = 200) -> List[Dict]:
        """Get user's identifications grouped by species"""
        try:
            # Check cache first
            if self.db:
                cached_data = self.db.get_user_species_cache(user_id, 'identifications')
                if cached_data:
                    st.info("Using cached identification data")
                    return cached_data[:limit]
            
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
                
                # If we hit the limit, break
                if len(all_species) >= limit:
                    break
            
            # Cache the results
            if self.db and all_species:
                self.db.cache_user_species(user_id, 'identifications', all_species)
            
            return all_species[:limit]
            
        except Exception as e:
            st.error(f"Error fetching user identifications by species: {str(e)}")
            return []
    
    def get_identifier_rankings(self, user_id: int, progress_callback=None) -> Dict[int, List[Dict]]:
        """
        Get species where the user is ranked in top 3 globally as an identifier.
        Returns a dictionary with rankings: {1: [...], 2: [...], 3: [...]}
        """
        try:
            # Get user's identified species (reasonable limit to avoid rate limiting)
            user_species = self.get_user_identifications_by_species(user_id, 500)
            
            rankings = {1: [], 2: [], 3: []}
            total_species = len(user_species)
            
            # For each species, check the user's global ranking
            for i, species in enumerate(user_species):
                taxon = species.get('taxon', {})
                taxon_id = taxon.get('id')
                user_count = species.get('count', 0)
                
                if not taxon_id or user_count == 0:
                    # Update progress for skipped species
                    if progress_callback:
                        remaining_species = total_species - i - 1
                        estimated_remaining = remaining_species * 2.0  # Conservative estimate
                        progress_callback(i + 1, total_species, estimated_remaining)
                    continue
                
                # Update progress BEFORE API call to avoid counting during retries
                if progress_callback:
                    remaining_species = total_species - i - 1
                    
                    if self.db:
                        # Sample upcoming species to estimate cache hit ratio
                        cached_count = 0
                        api_needed_count = 0
                        
                        for check_idx in range(i + 1, min(i + 11, total_species)):
                            if check_idx < len(user_species):
                                check_taxon = user_species[check_idx].get('taxon', {})
                                check_taxon_id = check_taxon.get('id')
                                if check_taxon_id:
                                    cached_data = self.db.get_species_leaderboard(check_taxon_id, 'identifiers')
                                    if cached_data:
                                        cached_count += 1
                                    else:
                                        api_needed_count += 1
                        
                        # Calculate time based on cache ratio and rate limiting
                        if cached_count + api_needed_count > 0:
                            cache_ratio = cached_count / (cached_count + api_needed_count)
                            estimated_api_calls = remaining_species * (1 - cache_ratio)
                            estimated_remaining = (estimated_api_calls * 2.0) + (remaining_species * cache_ratio * 0.1)
                        else:
                            estimated_remaining = remaining_species * 2.0
                    else:
                        estimated_remaining = remaining_species * 2.0
                    
                    progress_callback(i + 1, total_species, estimated_remaining)
                
                # Get the top identifiers for this species (uses cache if available)
                identifiers = self.get_species_identifiers_leaderboard(taxon_id)
                
                if identifiers and len(identifiers) >= 3:
                    # Check if our user is in top 3
                    for rank, identifier in enumerate(identifiers[:3], 1):
                        if identifier.get('user_id') == user_id:
                            rankings[rank].append({
                                'scientific_name': taxon.get('name', 'Unknown'),
                                'common_name': taxon.get('preferred_common_name', 'No common name'),
                                'identification_count': user_count,
                                'taxon_id': taxon_id,
                                'rank': taxon.get('rank', 'unknown'),
                                'global_rank': rank
                            })
                            break
                
                # No delay here - delays are handled inside the leaderboard functions
            
            # Final progress update
            if progress_callback:
                progress_callback(total_species, total_species, 0)
            
            return rankings
            
        except Exception as e:
            error_details = [
                f"Function: get_identifier_rankings",
                f"User ID: {user_id}",
                f"Error Type: {type(e).__name__}",
                f"Error: {str(e)}"
            ]
            st.error(f"Identifier rankings failed: {' | '.join(error_details)}")
            return {1: [], 2: [], 3: []}
    
    def get_species_observers_leaderboard(self, taxon_id: int, place_id: Optional[int] = None) -> List[Dict]:
        """Get leaderboard of observers for a specific species"""
        try:
            # Check cache first
            if self.db and not place_id:  # Only cache global leaderboards for now
                cached_data = self.db.get_species_leaderboard(taxon_id, 'observers')
                if cached_data:
                    return cached_data
            
            params = {
                "taxon_id": taxon_id,
                "per_page": 100,
                "verifiable": "true"
            }
            
            if place_id:
                params["place_id"] = place_id
            
            response = self._make_request("/observations/observers", params)
            results = response.get('results', [])
            
            # Cache the results (only for global leaderboards)
            if self.db and not place_id and results:
                self.db.cache_species_leaderboard(taxon_id, 'observers', results)
            
            # Add delay after API call to respect rate limits
            time.sleep(2.0)  # Conservative: 30 calls per minute max
            
            return results
            
        except Exception as e:
            error_details = [
                f"Function: get_species_observers_leaderboard",
                f"Taxon ID: {taxon_id}",
                f"Place ID: {place_id}",
                f"Error Type: {type(e).__name__}",
                f"Error: {str(e)}"
            ]
            st.error(f"Species observers leaderboard failed: {' | '.join(error_details)}")
            return []
    
    def get_species_identifiers_leaderboard(self, taxon_id: int, place_id: Optional[int] = None) -> List[Dict]:
        """Get leaderboard of identifiers for a specific species"""
        try:
            # Check cache first
            if self.db and not place_id:  # Only cache global leaderboards for now
                cached_data = self.db.get_species_leaderboard(taxon_id, 'identifiers')
                if cached_data:
                    return cached_data
            
            params = {
                "taxon_id": taxon_id,
                "per_page": 100
            }
            
            if place_id:
                params["place_id"] = place_id
            
            response = self._make_request("/identifications/identifiers", params)
            results = response.get('results', [])
            
            # Cache the results (only for global leaderboards)
            if self.db and not place_id and results:
                self.db.cache_species_leaderboard(taxon_id, 'identifiers', results)
            
            return results
            
        except Exception as e:
            error_details = [
                f"Function: get_species_identifiers_leaderboard",
                f"Taxon ID: {taxon_id}",
                f"Place ID: {place_id}",
                f"Error Type: {type(e).__name__}",
                f"Error: {str(e)}"
            ]
            st.error(f"Species identifiers leaderboard failed: {' | '.join(error_details)}")
            return []
