import streamlit as st
import pandas as pd
import requests
from inaturalist_api import iNaturalistAPI
import time

# Page configuration
st.set_page_config(
    page_title="iNaturalist User Leaderboards",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'top_observer_species' not in st.session_state:
    st.session_state.top_observer_species = []
if 'top_identifier_species' not in st.session_state:
    st.session_state.top_identifier_species = []
if 'total_observations' not in st.session_state:
    st.session_state.total_observations = 0
if 'show_observer_details' not in st.session_state:
    st.session_state.show_observer_details = False
if 'show_identifier_details' not in st.session_state:
    st.session_state.show_identifier_details = False

# Initialize API client
api_client = iNaturalistAPI()

def reset_session_state():
    """Reset all session state variables"""
    st.session_state.user_data = None
    st.session_state.top_observer_species = []
    st.session_state.top_identifier_species = []
    st.session_state.total_observations = 0
    st.session_state.show_observer_details = False
    st.session_state.show_identifier_details = False

def fetch_user_data(username):
    """Fetch comprehensive user data from iNaturalist API"""
    try:
        # Get user basic info
        with st.spinner(f"Looking up user: {username}..."):
            user_info = api_client.get_user_info(username)
            if not user_info:
                st.error(f"User '{username}' not found. Please check the username and try again.")
                return False
        
        st.success(f"Found user: {user_info.get('name', username)}")
        
        # Get user's total observations
        with st.spinner("Getting observation count..."):
            total_obs = api_client.get_user_observation_count(user_info['id'])
        
        # Observer analysis with detailed progress
        st.info("⏳ Analyzing species where user is top observer globally...")
        observer_progress_bar = st.progress(0)
        observer_status = st.empty()
        observer_time_remaining = st.empty()
        
        def observer_progress_callback(current, total, time_remaining):
            progress = current / total if total > 0 else 0
            observer_progress_bar.progress(progress)
            observer_status.text(f"Processing species {current} of {total}")
            if time_remaining > 0:
                minutes = int(time_remaining // 60)
                seconds = int(time_remaining % 60)
                observer_time_remaining.text(f"Estimated time remaining: {minutes}m {seconds}s")
            else:
                observer_time_remaining.text("")
        
        # Get species where user is top observer
        top_observer_species = api_client.get_top_observer_species(user_info['id'], observer_progress_callback)
        observer_status.success(f"✅ Found {len(top_observer_species)} species where user is top observer")
        observer_time_remaining.empty()
        
        # Identifier analysis with detailed progress
        st.info("⏳ Analyzing species where user is top identifier globally...")
        identifier_progress_bar = st.progress(0)
        identifier_status = st.empty()
        identifier_time_remaining = st.empty()
        
        def identifier_progress_callback(current, total, time_remaining):
            progress = current / total if total > 0 else 0
            identifier_progress_bar.progress(progress)
            identifier_status.text(f"Processing species {current} of {total}")
            if time_remaining > 0:
                minutes = int(time_remaining // 60)
                seconds = int(time_remaining % 60)
                identifier_time_remaining.text(f"Estimated time remaining: {minutes}m {seconds}s")
            else:
                identifier_time_remaining.text("")
        
        # Get species where user is top identifier  
        top_identifier_species = api_client.get_top_identifier_species(user_info['id'], identifier_progress_callback)
        identifier_status.success(f"✅ Found {len(top_identifier_species)} species where user is top identifier")
        identifier_time_remaining.empty()
        
        # Update session state
        st.session_state.user_data = user_info
        st.session_state.total_observations = total_obs
        st.session_state.top_observer_species = top_observer_species
        st.session_state.top_identifier_species = top_identifier_species
        
        # Clear progress elements
        observer_progress_bar.empty()
        identifier_progress_bar.empty()
        
        return True
        
    except Exception as e:
        st.error(f"Error fetching user data: {str(e)}")
        return False

def display_species_panel(title, species_list, detail_key, icon):
    """Display a species panel with count and expandable details"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader(f"{icon} {title}")
    
    with col2:
        st.metric("Count", len(species_list))
    
    if species_list:
        if st.button(f"View Details", key=f"btn_{detail_key}"):
            st.session_state[f'show_{detail_key}_details'] = not st.session_state[f'show_{detail_key}_details']
        
        if st.session_state[f'show_{detail_key}_details']:
            st.write("---")
            df = pd.DataFrame(species_list)
            if not df.empty:
                # Format the dataframe for better display
                if 'scientific_name' in df.columns:
                    df_display = df[['scientific_name', 'common_name', 'observation_count']].copy()
                    df_display.columns = ['Scientific Name', 'Common Name', 'Observations']
                    df_display = df_display.fillna('-')
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No species data available.")
    else:
        st.info(f"No species found where user is top {detail_key.replace('_', ' ')}.")

def main():
    # Header
    st.title("🔍 iNaturalist User Leaderboards")
    st.markdown("Enter an iNaturalist username to view their leaderboard statistics")
    
    # Username input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        username = st.text_input(
            "iNaturalist Username", 
            placeholder="Enter username (e.g., stevilkinevil)",
            help="Enter the exact username as it appears on iNaturalist"
        )
    
    with col2:
        st.write("")  # Add some spacing
        search_button = st.button("Search", type="primary", use_container_width=True)
    
    # Handle search
    if search_button and username:
        reset_session_state()
        if fetch_user_data(username):
            st.success(f"Data loaded successfully for user: {username}")
            st.rerun()
    elif search_button and not username:
        st.warning("Please enter a username to search.")
    
    # Display user data if available
    if st.session_state.user_data:
        user = st.session_state.user_data
        
        # User info header
        st.write("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.subheader(f"👤 {user.get('name', user.get('login', 'Unknown User'))}")
            if user.get('login'):
                st.caption(f"@{user['login']}")
        
        st.write("---")
        
        # Main dashboard panels
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.container():
                st.markdown("### 👁️ Top Observer")
                st.metric("Species Count", len(st.session_state.top_observer_species))
                if st.session_state.top_observer_species:
                    if st.button("View Species List", key="observer_details"):
                        st.session_state.show_observer_details = not st.session_state.show_observer_details
                else:
                    st.info("No species found where user is top observer")
        
        with col2:
            with st.container():
                st.markdown("### 🏷️ Top Identifier")
                st.metric("Species Count", len(st.session_state.top_identifier_species))
                if st.session_state.top_identifier_species:
                    if st.button("View Species List", key="identifier_details"):
                        st.session_state.show_identifier_details = not st.session_state.show_identifier_details
                else:
                    st.info("No species found where user is top identifier")
        
        with col3:
            with st.container():
                st.markdown("### 📊 Total Observations")
                st.metric("Observation Count", f"{st.session_state.total_observations:,}")
                if user.get('observations_count'):
                    st.caption(f"Profile shows: {user['observations_count']:,}")
        
        # Detailed species lists
        if st.session_state.show_observer_details and st.session_state.top_observer_species:
            st.write("---")
            st.subheader("👁️ Species Where User is Top Observer")
            df_observer = pd.DataFrame(st.session_state.top_observer_species)
            if not df_observer.empty:
                # Format the dataframe for better display
                display_cols = ['scientific_name', 'common_name', 'observation_count', 'rank']
                df_display = df_observer[display_cols].copy()
                df_display.columns = ['Scientific Name', 'Common Name', 'Observations', 'Taxonomic Rank']
                df_display['Common Name'] = df_display['Common Name'].fillna('No common name')
                st.dataframe(df_display, use_container_width=True)
                st.caption(f"Showing {len(df_observer)} species where this user has the most observations globally")
            else:
                st.info("No detailed data available.")
        
        if st.session_state.show_identifier_details and st.session_state.top_identifier_species:
            st.write("---")
            st.subheader("🏷️ Species Where User is Top Identifier")
            df_identifier = pd.DataFrame(st.session_state.top_identifier_species)
            if not df_identifier.empty:
                # Format the dataframe for better display
                display_cols = ['scientific_name', 'common_name', 'identification_count', 'rank']
                df_display = df_identifier[display_cols].copy()
                df_display.columns = ['Scientific Name', 'Common Name', 'Identifications', 'Taxonomic Rank']
                df_display['Common Name'] = df_display['Common Name'].fillna('No common name')
                st.dataframe(df_display, use_container_width=True)
                st.caption(f"Showing {len(df_identifier)} species where this user has provided the most identifications globally")
            else:
                st.info("No detailed data available.")
    
    # Footer
    st.write("---")
    st.markdown(
        "Data sourced from [iNaturalist API](https://api.inaturalist.org/v1/docs/). "
        "This application helps users explore their contributions to citizen science."
    )

if __name__ == "__main__":
    main()
