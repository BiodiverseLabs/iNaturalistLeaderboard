# iNaturalist User Leaderboards Dashboard

## Overview

This project is a Streamlit-based web application that provides comprehensive leaderboards and analytics for iNaturalist users. The application allows users to search for specific iNaturalist accounts and view detailed statistics about their observations and identifications, including species-specific data and community rankings.

## System Architecture

The application follows a simple client-server architecture:

- **Frontend**: Streamlit web interface for user interaction and data visualization
- **Backend**: Python-based data processing using the iNaturalist REST API
- **Data Source**: Real-time data fetched from iNaturalist's public API (no local database)
- **Deployment**: Configured for Replit's autoscale deployment target

## Key Components

### 1. Main Application (`app.py`)
- **Purpose**: Primary Streamlit application entry point
- **Functionality**: User interface, session state management, and data presentation
- **Key Features**:
  - User search functionality
  - Leaderboard displays for observers and identifiers
  - Species-specific statistics
  - Interactive dashboard with expandable details

### 2. API Client (`inaturalist_api.py`)
- **Purpose**: Abstraction layer for iNaturalist API interactions
- **Functionality**: HTTP request handling, error management, and data parsing
- **Key Features**:
  - RESTful API client with proper error handling
  - User information retrieval
  - Rate limiting consideration
  - Timeout management for reliable API calls

### 3. Configuration Files
- **`.replit`**: Defines the Python 3.11 runtime environment and deployment settings
- **`pyproject.toml`**: Manages project dependencies (Streamlit, Pandas, Requests)
- **`.streamlit/config.toml`**: Streamlit server configuration for headless operation

## Data Flow

1. **User Input**: Username entered through Streamlit interface
2. **API Request**: Username validated and sent to iNaturalist API via custom client
3. **Data Processing**: Raw API responses processed and formatted for display
4. **State Management**: User data cached in Streamlit session state
5. **Visualization**: Processed data rendered in interactive dashboard components

## External Dependencies

### Core Dependencies
- **Streamlit**: Web application framework for the user interface
- **Pandas**: Data manipulation and analysis for processing API responses
- **Requests**: HTTP library for making API calls to iNaturalist

### External API
- **iNaturalist API v1**: Primary data source for user information, observations, and identifications
- **API Base URL**: `https://api.inaturalist.org/v1`
- **Rate Limiting**: Implemented through session management and timeout controls

## Deployment Strategy

The application is configured for deployment on Replit's platform:

- **Target**: Autoscale deployment for automatic scaling based on demand
- **Runtime**: Python 3.11 with Nix package management
- **Port Configuration**: Streamlit server runs on port 5000
- **Process Management**: Parallel workflow execution for the Streamlit server
- **Environment**: Headless server configuration optimized for cloud deployment

### Deployment Considerations
- No database dependencies for simplified deployment
- Stateless design with session-based caching
- Environment variables not required (uses public API endpoints)
- Automatic dependency resolution through uv.lock

## Recent Changes

- **June 22, 2025 - Optimized Database Caching**: Enhanced PostgreSQL caching to maximize API call reduction:
  - Cache user species data for 7 days to avoid repeated lookups
  - Cache species leaderboards for 30 days - shared across ALL users for the same species
  - Species leaderboard data persisted in PostgreSQL database, not memory cache
  - Intelligent delay logic: only wait 1 second after fresh API calls, skip delays for cached data
  - Database shows 66+ species already cached, dramatically reducing future API calls
  - Automatic cleanup of old cache entries after 7 days

- **June 22, 2025 - Enhanced Error Logging & Rate Limiting**: Comprehensive debugging and API optimization:
  - Added detailed error logging with endpoint, status code, headers, and response body
  - Enhanced retry logic with detailed attempt tracking and warning messages
  - Function-specific error context (user ID, taxon ID, data sizes)
  - Database error logging with operation details and data metrics
  - Set delays to 1 second between API calls (60 calls per minute, under iNat's 100/min limit)
  - Added exponential backoff retry logic for 429 errors (5s, 10s, 15s)

- **June 22, 2025 - Added Top 3 Global Rankings**: Expanded dashboard to show comprehensive ranking data:
  - Added #2 and #3 global ranking panels for both observers and identifiers
  - Medal-style UI with gold, silver, bronze indicators for rankings
  - Separate expandable lists for each ranking position
  - Enhanced progress tracking to show breakdown of all ranking discoveries

- **June 22, 2025 - Enhanced Progress Tracking**: Added comprehensive progress bars with real-time tracking showing:
  - Total species to process vs. completed
  - Estimated time remaining based on processing speed
  - Visual progress bar for both observer and identifier analysis
  - Improved user experience during long processing times

- **June 22, 2025 - Fixed Global Leaderboard Logic**: Updated API client to properly check global leaderboards:
  - Each species is verified against iNaturalist's global observer/identifier rankings
  - Users are only shown as "top" when they are actually ranked #1 globally for that species
  - Replaced simple "most observed" lists with true global leadership positions

- **June 22, 2025 - Initial Setup**: Created basic dashboard structure and API integration

## User Preferences

```
Preferred communication style: Simple, everyday language.
```

### Technical Notes

- The application uses session state for caching user data to reduce API calls
- Error handling is implemented throughout the API client for robust operation
- The design prioritizes real-time data over local storage for accuracy
- Streamlit's built-in caching mechanisms are leveraged for performance optimization