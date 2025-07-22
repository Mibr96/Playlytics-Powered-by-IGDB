# Playlytics - Game Analytics Website

**Playlytics** is a web platform that lets you explore detailed game information powered by the IGDB API. You can search, filter, and visualize data about your favorite games — like ratings, media, screenshots, and more. Whether you're a gamer looking to discover new titles or a data nerd diving into game stats, Playlytics has you covered.

---

## 🚀 Features

- 🔍 **Game Details**: View in-depth information including ratings, genres, themes, engines, time-to-beat, and more.
- 🎞️ **Media Carousels**: Browse screenshots and trailers in a dynamic media viewer.
- 📊 **Interactive Stats**: Explore trends and game analytics visualized using Chart.js. ( WORK IN PROGRESS ) 
- 🎯 **Search & Filters**: Easily find games with advanced filters like platform, developer, and multiplayer support.

<img width="3337" height="1249" alt="image" src="https://github.com/user-attachments/assets/84b31608-8c40-454a-9daf-fac3c3d9f5ed" />


---

## 🛠️ Tech Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS, Bootstrap
- **API**: IGDB API (by Twitch)
- **Data Viz**: Chart.js ( WORK IN PROGRESS ) 
- **Other Tools**: PySpark (for backend data prep), Jinja2 (templating)

---

## ⚙️ Installation

To run Playlytics locally:

<pre><code>bash # 1. Clone the repo git clone https://github.com/yourusername/playlytics.git 
  # 2. Navigate into the project directory cd playlytics 
  # 3. Install dependencies pip install Flask requests python-dotenv 
  # 4. Run the Flask development server python app.py</code></pre>

## ⚠️ Make sure to set up a .env file in the root directory with your IGDB API credentials:

<pre><code>CLIENT_ID=your_igdb_client_id
ACCESS_TOKEN=your_igdb_access_token</code></pre>

## How to get the API key: 

In order to use the API, you must have a Twitch Account.
Sign Up with Twitch for a free account
Ensure you have Two Factor Authentication enabled
Register your application in the Twitch Developer Portal
The OAuth Redirect URL field is not used by IGDB. Please add ’localhost’ to continue.
The Client Type must be set to Confidential to generate Client Secrets
Manage your newly created application
Generate a Client Secret by pressing [New Secret]
Take note of the Client ID and Client Secret

The IGDB.com API is free for non-commercial usage under the terms of the Twitch Developer Service Agreement.

## 🧩 TODO
Add user login & favorites system
Implement game comparisons
Implement Analytics
Improve responsiveness on mobile
Add more filters (e.g. time-to-beat, release year)


## 🤝 Contributing
Pull requests are welcome! Feel free to fork this repo and submit a PR with suggestions, improvements, or new features. Let's make Playlytics even better together!

## Updated Screenshots as I go.
<img width="3400" height="1246" alt="image" src="https://github.com/user-attachments/assets/7330319b-389d-4af2-93ab-69a252ecd0c3" />

<img width="3418" height="1222" alt="image" src="https://github.com/user-attachments/assets/b7dff079-e733-40dc-8dfb-5714d35bc2a8" />


