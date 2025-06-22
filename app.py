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
if 'observer_rankings' not in st.session_state:
    st.session_state.observer_rankings = {1: [], 2: [], 3: []}
if 'identifier_rankings' not in st.session_state:
    st.session_state.identifier_rankings = {1: [], 2: [], 3: []}
if 'total_observations' not in st.session_state:
    st.session_state.total_observations = 0
if 'show_observer_details' not in st.session_state:
    st.session_state.show_observer_details = {1: False, 2: False, 3: False}
if 'show_identifier_details' not in st.session_state:
    st.session_state.show_identifier_details = {1: False, 2: False, 3: False}

# Initialize API client
api_client = iNaturalistAPI()

def reset_session_state():
    """Reset all session state variables"""
    st.session_state.user_data = None
    st.session_state.observer_rankings = {1: [], 2: [], 3: []}
    st.session_state.identifier_rankings = {1: [], 2: [], 3: []}
    st.session_state.total_observations = 0
    st.session_state.show_observer_details = {1: False, 2: False, 3: False}
    st.session_state.show_identifier_details = {1: False, 2: False, 3: False}

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
        st.info("⏳ Analyzing species where user is ranked globally as observer...")
        st.caption("Checking up to 500 of the user's most observed species to find global rankings")
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
        
        # Get observer rankings (1st, 2nd, 3rd place)
        observer_rankings = api_client.get_observer_rankings(user_info['id'], observer_progress_callback)
        total_observer_species = sum(len(species_list) for species_list in observer_rankings.values())
        observer_status.success(f"✅ Found {len(observer_rankings[1])} #1, {len(observer_rankings[2])} #2, {len(observer_rankings[3])} #3 observer rankings")
        observer_time_remaining.empty()
        
        # Identifier analysis with detailed progress
        st.info("⏳ Analyzing species where user is ranked globally as identifier...")
        st.caption("Checking up to 500 of the user's most identified species to find global rankings")
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
        
        # Get identifier rankings (1st, 2nd, 3rd place)
        identifier_rankings = api_client.get_identifier_rankings(user_info['id'], identifier_progress_callback)
        total_identifier_species = sum(len(species_list) for species_list in identifier_rankings.values())
        identifier_status.success(f"✅ Found {len(identifier_rankings[1])} #1, {len(identifier_rankings[2])} #2, {len(identifier_rankings[3])} #3 identifier rankings")
        identifier_time_remaining.empty()
        
        # Update session state
        st.session_state.user_data = user_info
        st.session_state.total_observations = total_obs
        st.session_state.observer_rankings = observer_rankings
        st.session_state.identifier_rankings = identifier_rankings
        
        # Clean up old cache entries periodically
        if hasattr(api_client, 'db') and api_client.db:
            api_client.db.cleanup_old_cache()
        
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
        
        # Observer Rankings Section
        st.markdown("## 👁️ Observer Global Rankings")
        obs_col1, obs_col2, obs_col3 = st.columns(3)
        
        with obs_col1:
            with st.container():
                st.markdown("### 🥇 #1 Observer")
                count_1 = len(st.session_state.observer_rankings[1])
                st.metric("Species Count", count_1)
                if count_1 > 0:
                    if st.button("View #1 Species", key="observer_1_details"):
                        st.session_state.show_observer_details[1] = not st.session_state.show_observer_details[1]
                else:
                    st.info("No #1 rankings")
        
        with obs_col2:
            with st.container():
                st.markdown("### 🥈 #2 Observer")
                count_2 = len(st.session_state.observer_rankings[2])
                st.metric("Species Count", count_2)
                if count_2 > 0:
                    if st.button("View #2 Species", key="observer_2_details"):
                        st.session_state.show_observer_details[2] = not st.session_state.show_observer_details[2]
                else:
                    st.info("No #2 rankings")
        
        with obs_col3:
            with st.container():
                st.markdown("### 🥉 #3 Observer")
                count_3 = len(st.session_state.observer_rankings[3])
                st.metric("Species Count", count_3)
                if count_3 > 0:
                    if st.button("View #3 Species", key="observer_3_details"):
                        st.session_state.show_observer_details[3] = not st.session_state.show_observer_details[3]
                else:
                    st.info("No #3 rankings")
        
        # Identifier Rankings Section
        st.markdown("## 🏷️ Identifier Global Rankings")
        id_col1, id_col2, id_col3 = st.columns(3)
        
        with id_col1:
            with st.container():
                st.markdown("### 🥇 #1 Identifier")
                count_1 = len(st.session_state.identifier_rankings[1])
                st.metric("Species Count", count_1)
                if count_1 > 0:
                    if st.button("View #1 Species", key="identifier_1_details"):
                        st.session_state.show_identifier_details[1] = not st.session_state.show_identifier_details[1]
                else:
                    st.info("No #1 rankings")
        
        with id_col2:
            with st.container():
                st.markdown("### 🥈 #2 Identifier")
                count_2 = len(st.session_state.identifier_rankings[2])
                st.metric("Species Count", count_2)
                if count_2 > 0:
                    if st.button("View #2 Species", key="identifier_2_details"):
                        st.session_state.show_identifier_details[2] = not st.session_state.show_identifier_details[2]
                else:
                    st.info("No #2 rankings")
        
        with id_col3:
            with st.container():
                st.markdown("### 🥉 #3 Identifier")
                count_3 = len(st.session_state.identifier_rankings[3])
                st.metric("Species Count", count_3)
                if count_3 > 0:
                    if st.button("View #3 Species", key="identifier_3_details"):
                        st.session_state.show_identifier_details[3] = not st.session_state.show_identifier_details[3]
                else:
                    st.info("No #3 rankings")
        
        # Total Observations Section
        st.markdown("## 📊 Total Observations")
        st.metric("Observation Count", f"{st.session_state.total_observations:,}")
        if user.get('observations_count'):
            st.caption(f"Profile shows: {user['observations_count']:,}")
        
        # Detailed species lists for observers
        for rank in [1, 2, 3]:
            if st.session_state.show_observer_details[rank] and st.session_state.observer_rankings[rank]:
                st.write("---")
                rank_labels = {1: "🥇 #1", 2: "🥈 #2", 3: "🥉 #3"}
                st.subheader(f"👁️ Species Where User is {rank_labels[rank]} Observer Globally")
                df_observer = pd.DataFrame(st.session_state.observer_rankings[rank])
                if not df_observer.empty:
                    # Format the dataframe for better display
                    display_cols = ['scientific_name', 'common_name', 'observation_count', 'rank']
                    df_display = df_observer[display_cols].copy()
                    df_display.columns = ['Scientific Name', 'Common Name', 'Observations', 'Taxonomic Rank']
                    df_display['Common Name'] = df_display['Common Name'].fillna('No common name')
                    st.dataframe(df_display, use_container_width=True)
                    st.caption(f"Showing {len(df_observer)} species where this user is ranked #{rank} globally for observations")
                else:
                    st.info("No detailed data available.")
        
        # Detailed species lists for identifiers
        for rank in [1, 2, 3]:
            if st.session_state.show_identifier_details[rank] and st.session_state.identifier_rankings[rank]:
                st.write("---")
                rank_labels = {1: "🥇 #1", 2: "🥈 #2", 3: "🥉 #3"}
                st.subheader(f"🏷️ Species Where User is {rank_labels[rank]} Identifier Globally")
                df_identifier = pd.DataFrame(st.session_state.identifier_rankings[rank])
                if not df_identifier.empty:
                    # Format the dataframe for better display
                    display_cols = ['scientific_name', 'common_name', 'identification_count', 'rank']
                    df_display = df_identifier[display_cols].copy()
                    df_display.columns = ['Scientific Name', 'Common Name', 'Identifications', 'Taxonomic Rank']
                    df_display['Common Name'] = df_display['Common Name'].fillna('No common name')
                    st.dataframe(df_display, use_container_width=True)
                    st.caption(f"Showing {len(df_identifier)} species where this user is ranked #{rank} globally for identifications")
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
