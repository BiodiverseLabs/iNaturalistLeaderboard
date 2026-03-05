# iNaturalist Leaderboards Dashboard

## Overview

This project is a [Streamlit](https://streamlit.io/)-based web application providing comprehensive leaderboards and analytics for [iNaturalist](https://www.inaturalist.org/) users. It allows users to search for any iNaturalist user and view detailed statistics about their observations, identifications, and global species rankings.

---

## Features

- **Global rankings:** Find out where you (or any user) rank globally as an observer or identifier for every species.
- **Detailed dashboards:** Interactive statistics about a user’s activity (by species, observation counts, identifications, and more).
- **Leaderboard views:** Leaderboards for both observers and identifiers, including top 1, 2, and 3 positions (with gold, silver, bronze indicators).
- **CSV export:** Download comprehensive rankings for spreadsheet analysis.
- **Intelligent optimization:** Reduces unnecessary API calls by detecting species unlikely to yield top 100 rankings.
- **Caching:** Dramatic speedup for repeat users thanks to database-backed caching.

---

## Code Structure

```
/
├── app.py                # Main Streamlit dashboard & app entrypoint.
├── database.py           # Handles caching, database storage of leaderboards/user data.
├── inaturalist_api.py    # API client abstraction for robust iNaturalist API access.
├── pyproject.toml        # Python dependencies & project metadata.
├── .replit               # Runtime settings for Replit platform (Python 3.11).
├── replit.md             # In-depth architecture & changelog (project documentation).
├── uv.lock               # Dependency lock file for reproducible builds.
├── attached_assets/      # Directory for any attached media/assets.
├── .streamlit/           # Streamlit server configuration (e.g., headless mode).
```

### Main Components

- **app.py**  
  _Streamlit dashboard. Handles the UI, user input, display of statistics/leaderboards, and CSV export. Manages session state and orchestrates API interactions and database caching._

- **inaturalist_api.py**  
  _Python abstraction for the iNaturalist REST API. Handles HTTP requests, rate limiting, retry logic, user/species/statistics lookups, and error handling._

- **database.py**  
  _Implements efficient caching of user statistics and leaderboard results. Uses PostgreSQL or similar for persistent storage, improving dashboard performance for returning users._

- **pyproject.toml**  
  _Specifies dependencies:_  
  - `streamlit` (UI/dashboard)  
  - `pandas` (data processing)  
  - `requests` (HTTP API calls)  
  - `sqlalchemy`, `psycopg2-binary` (database handling)

- **.streamlit/config.toml** (in the `.streamlit/` directory)  
  _Optional headless server config for Streamlit._

---

## Data Flow

1. **User submits an iNaturalist username** via the Streamlit dashboard.
2. **API requests** fetch and validate data from the iNaturalist REST API.
3. **Intermediate results are cached** (in database) for speed; raw responses are parsed using `pandas`.
4. **Processed data is displayed** in an interactive leaderboard/dashboard.
5. **Results can be exported** as CSV for private analysis.

---

## Deployment & Usage

- Designed for deployment on [Replit](https://replit.com/), but works locally with Python ≥3.11.
- No private keys or API secrets required (all data public).
- No need for environment variables.
- Stateless except for short-term session/database caching.

### Local Quickstart

1. **Clone the repo:**
   ```sh
   git clone https://github.com/BiodiverseLabs/iNaturalistLeaderboard.git
   cd iNaturalistLeaderboard
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   # or, if using pyproject.toml:
   pip install .
   ```
3. **Run the app:**
   ```sh
   streamlit run app.py
   ```
4. Visit [http://localhost:5000](http://localhost:5000) (or the Streamlit localhost URL).

---

## API Reference

Uses:
- [iNaturalist API v1](https://api.inaturalist.org/v1) for observations, identifications, and user metadata.
- Handles API rate-limiting and retry policy automatically.

---

## Contributing

Contributions are welcome!  
- Please open issues or pull requests for bugs, enhancements, or questions.
- See [`replit.md`](./replit.md) for detailed architecture & changelog.

---

## Acknowledgments

- Built by [BiodiverseLabs](https://github.com/BiodiverseLabs).
- Powered by the open iNaturalist community and API.

---

## License

MIT License (see LICENSE).

---

*Last updated: 2026-03-05*