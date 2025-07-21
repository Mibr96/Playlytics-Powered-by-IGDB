from flask import Flask, render_template, jsonify, abort, request
import json
import os
from datetime import datetime
import math
from urllib.parse import urlparse

app = Flask(__name__)

AGE_RATING_CATEGORIES = {
    1: "ESRB",
    2: "PEGI"
}
AGE_RATING_LABELS = {
    1: "3",
    2: "7",
    3: "12",
    4: "16",
    5: "18",
    6: "RP",
    7: "EC",
    8: "E",
    9: "E10",
    10: "T",
    11: "M",
    12: "AO"
}

country_file = os.path.join("data", "iso_countries.json")
if os.path.exists(country_file):
    with open(country_file, "r", encoding="utf-8") as f:
        country_data = json.load(f)
else:
    country_data = []

country_lookup = {item["Country"]: item["Country name"] for item in country_data}

@app.template_filter('country_name')
def country_name(code):
    if code is None:
        return "Unknown"
    try:
        code_int = int(code)
        return country_lookup.get(code_int, f"Unknown ({code})")
    except Exception:
        return f"Invalid code ({code})"

@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        return datetime.utcfromtimestamp(int(value)).strftime('%Y-%m-%d')
    except:
        return "Unknown"

def parse_age_ratings(age_ratings):
    parsed = []
    if isinstance(age_ratings, list):
        for ar in age_ratings:
            if isinstance(ar, dict):
                category = AGE_RATING_CATEGORIES.get(ar.get("category"), "Unknown")
                rating = AGE_RATING_LABELS.get(ar.get("rating"), "Unknown")
                parsed.append(f"{category}: {rating}")
            elif isinstance(ar, int):
                parsed.append(f"ID: {ar}")
    return parsed

data_file = os.path.join("data", "games_output.json")
if os.path.exists(data_file):
    with open(data_file, "r", encoding="utf-8") as f:
        all_games = json.load(f)
else:
    all_games = []

all_genres = sorted({genre for g in all_games for genre in g.get("genre_names", []) if genre})
all_themes = sorted({theme for g in all_games for theme in g.get("theme_names", []) if theme})
all_engines = sorted({engine for g in all_games for engine in g.get("engine_names", []) if engine})
all_platforms = sorted({platform for g in all_games for platform in g.get("platform_names", []) if platform})
all_game_modes = sorted({mode for g in all_games for mode in g.get("game_mode_names", []) if mode})

all_publishers_developers = set()
for game in all_games:
    companies = game.get("involved_companies", [])
    if isinstance(companies, list):
        for comp in companies:
            if isinstance(comp, dict) and "name" in comp:
                all_publishers_developers.add(comp["name"])
all_publishers_developers = sorted(all_publishers_developers)

def prepare_games(games):
    for game in games:
        image_id = game.get("image_id")
        if image_id:
            game["cover_url"] = f"https://images.igdb.com/igdb/image/upload/t_1080p/{image_id}.jpg"
        else:
            game["cover_url"] = None

        if "rating" in game and game["rating"]:
            game["rating_display"] = round(game["rating"], 1)
        elif "aggregated_rating" in game and game["aggregated_rating"]:
            game["rating_display"] = round(game["aggregated_rating"], 1)
        else:
            game["rating_display"] = None

        if "website_urls" in game and game["website_urls"]:
            game["official_website"] = game["website_urls"][0]
            game["websites"] = [{"url": url, "name": "Website"} for url in game["website_urls"]]
        else:
            game["official_website"] = None
            game["websites"] = []

        game["age_ratings_parsed"] = parse_age_ratings(game.get("age_ratings"))

        release_ts = game.get("first_release_date")
        if isinstance(release_ts, (int, float)) and release_ts > 0:
            try:
                game["release_year"] = datetime.utcfromtimestamp(release_ts).year
            except Exception:
                game["release_year"] = "Unknown"
        else:
            game["release_year"] = "Unknown"

        screenshots = game.get("screenshots", [])
        game["screenshot_urls"] = [
            f"https://images.igdb.com/igdb/image/upload/t_screenshot_huge/{s['image_id']}.jpg"
            for s in screenshots if isinstance(s, dict) and "image_id" in s
        ]

        videos = game.get("videos", [])
        game["video_urls"] = [
            f"https://www.youtube.com/embed/{v['video_id']}"
            for v in videos if isinstance(v, dict) and "video_id" in v
        ]

        for dev in game.get("developer_publisher_details", []):
            dev["country_name"] = country_lookup.get(dev.get("country"), "Unknown")

    return games

def paginate_items(items, page, per_page):
    total = len(items)
    total_pages = math.ceil(total / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total, total_pages

@app.route('/')
def home():
    if not all_games:
        return "No game data found. Please run igdb_fetcher.py first."

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 55, type=int) #55 is the correct count for HD res. Will be missing 1 on 2k, now sure how to fix that yet.

    query = request.args.get('q', '').lower()
    selected_genre = request.args.get('genre', '')
    selected_year = request.args.get('year', '')
    sort_option = request.args.get('sort', '')
    selected_publisher = request.args.get('publisher', '')
    selected_theme = request.args.get('theme', '')
    selected_engine = request.args.get('engine', '')
    selected_platform = request.args.get('platform', '')
    selected_mode = request.args.get('mode', '')
    include_dlcs = request.args.get('include_dlcs') == 'on'

    for game in all_games:
        if "first_release_date" in game:
            game["release_year"] = datetime.utcfromtimestamp(game["first_release_date"]).year
        else:
            game["release_year"] = "Unknown"

    filtered_games = [g for g in all_games if include_dlcs or not g.get("is_dlc", False)]

    if query:
        filtered_games = [g for g in filtered_games if query in g.get('name', '').lower()]

    if selected_genre:
        filtered_games = [g for g in filtered_games if selected_genre in g.get("genre_names", [])]
    if selected_year:
        filtered_games = [g for g in filtered_games if str(g.get("release_year")) == selected_year]
    if selected_publisher:
        filtered_games = [
            g for g in filtered_games
            if selected_publisher in [c.get("name") for c in g.get("involved_companies", []) if isinstance(c, dict)]
        ]
    if selected_theme:
        filtered_games = [g for g in filtered_games if selected_theme in g.get("theme_names", [])]
    if selected_engine:
        filtered_games = [g for g in filtered_games if selected_engine in g.get("engine_names", [])]
    if selected_platform:
        filtered_games = [g for g in filtered_games if selected_platform in g.get("platform_names", [])]
    if selected_mode:
        filtered_games = [g for g in filtered_games if selected_mode in g.get("game_mode_names", [])]

    if sort_option == "rating_desc":
        sorted_games = sorted(filtered_games, key=lambda g: g.get("rating") or -1, reverse=True)
    elif sort_option == "rating_asc":
        sorted_games = sorted(filtered_games, key=lambda g: g.get("rating") or 9999)
    elif sort_option == "release_asc":
        sorted_games = sorted(filtered_games, key=lambda g: g.get("first_release_date") or float('inf'))
    elif sort_option == "release_desc":
        sorted_games = sorted(filtered_games, key=lambda g: g.get("first_release_date") or 0, reverse=True)
    else:
        sorted_games = sorted(filtered_games, key=lambda g: g.get("first_release_date") or 0, reverse=True)

    games_copy = prepare_games(sorted_games.copy())
    paginated_games, total, total_pages = paginate_items(games_copy, page, per_page)

    release_years = sorted(
        {str(g.get("release_year")) for g in all_games if g.get("release_year") != "Unknown"},
        reverse=True
    )

    return render_template(
        "index.html",
        games=paginated_games,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        query=query,
        genres=all_genres,
        selected_genre=selected_genre,
        release_years=release_years,
        selected_year=selected_year,
        sort_option=sort_option,
        publishers=all_publishers_developers,
        selected_publisher=selected_publisher,
        themes=all_themes,
        selected_theme=selected_theme,
        engines=all_engines,
        selected_engine=selected_engine,
        platforms=all_platforms,
        selected_platform=selected_platform,
        modes=all_game_modes,
        selected_mode=selected_mode,
        include_dlcs = request.args.get("include_dlcs", "off") == "on"
    )


@app.route('/stats/<int:game_id>')
def stats(game_id):
    if not all_games:
        abort(404, description="Game data not found")

    game = next((g for g in all_games if g.get("id") == game_id), None)
    if not game:
        abort(404, description="Game not found")

    ratings_distribution = {
        "labels": ["0-20", "21-40", "41-60", "61-80", "81-100"],
        "data": [5, 15, 40, 25, 15]
    }
    platform_share = {
        "labels": ["PC", "Xbox", "PlayStation", "Switch", "Mobile"],
        "data": [30, 25, 20, 15, 10]
    }
    monthly_active_users = {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "data": [100, 120, 150, 130, 170, 160]
    }

    return render_template(
        "stats.html",
        game=game,
        ratings_distribution=ratings_distribution,
        platform_share=platform_share,
        monthly_active_users=monthly_active_users
    )

@app.route('/game/<int:game_id>')
def game_detail(game_id):
    if not all_games:
        abort(404, description="Game data not loaded.")

    game = next((g for g in all_games if g.get("id") == game_id), None)
    if not game:
        abort(404, description="Game not found.")

    game = prepare_games([game])[0]
    return render_template("game_detail.html", game=game)

@app.template_filter('url_domain')
def url_domain(value):
    try:
        parsed_url = urlparse(value)
        return parsed_url.netloc.replace('www.', '')
    except Exception:
        return value

if __name__ == '__main__':
    app.run(debug=False)
