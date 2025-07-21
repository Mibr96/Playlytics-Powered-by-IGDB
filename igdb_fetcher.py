import os
import json
import requests
from dotenv import load_dotenv
from time import sleep
from datetime import datetime, timezone

load_dotenv()

CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

AUTH_URL = "https://id.twitch.tv/oauth2/token"
GAME_URL = "https://api.igdb.com/v4/games"
WEBSITE_URL = "https://api.igdb.com/v4/websites"
GENRE_URL = "https://api.igdb.com/v4/genres"
COMPANY_URL = "https://api.igdb.com/v4/involved_companies"
COMPANY_INFO_URL = "https://api.igdb.com/v4/companies"
ENGINE_URL = "https://api.igdb.com/v4/game_engines"
THEME_URL = "https://api.igdb.com/v4/themes"
PLATFORM_URL = "https://api.igdb.com/v4/platforms"
GAME_MODE_URL = "https://api.igdb.com/v4/game_modes"
ACHIEVEMENT_URL = "https://api.igdb.com/v4/achievements"
AGE_RATING_URL = "https://api.igdb.com/v4/age_ratings"
VIDEO_URL = "https://api.igdb.com/v4/game_videos"
GAME_VERSIONS_URL = "https://api.igdb.com/v4/game_versions"

def get_access_token():
    res = requests.post(AUTH_URL, data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    })
    res.raise_for_status()
    return res.json()['access_token']

def convert_timestamp(ts):
    if not ts:
        return None
    try:
        if ts < 0 or ts > 32503680000:
            return None
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d')
    except (OSError, OverflowError, ValueError):
        return None


def batch_fetch(token, endpoint_url, ids, fields='*'):
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}',
    }
    results = []
    batch_size = 300
    ids = list(set(ids))
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        query = f'fields {fields}; where id = ({" ,".join(map(str, batch_ids))}); limit {batch_size};'
        res = requests.post(endpoint_url, headers=headers, data=query)
        if res.status_code == 200:
            results.extend(res.json())
            print(f"Fetched {len(results)} items so far from {endpoint_url.split('/')[-1]}...")
        else:
            print(f"Failed to fetch {endpoint_url.split('/')[-1]} batch {i}: {res.text}")
        sleep(0.25)
    return results

def fetch_dict(token, url, field):
    return {e['id']: e.get(field, "Unknown") for e in batch_fetch(token, url, range(1, 1000), fields=f'id,{field}')}

def fetch_company_websites(token, website_ids):
    if not website_ids:
        return {}
    website_data = batch_fetch(token, WEBSITE_URL, website_ids, fields='id,url,category')
    return {w['id']: w['url'] for w in website_data}

def fetch_companies(token, involved_ids):
    involved_raw = batch_fetch(token, COMPANY_URL, involved_ids, fields='id,company,developer,publisher')
    company_ids = list(set(i['company'] for i in involved_raw if 'company' in i))

    fields = (
        'id,name,slug,change_date,change_date_format,changed_company_id,checksum,country,created_at,'
        'description,developed,published,logo.image_id,parent,start_date,start_date_format,status,updated_at,url,websites'
    )

    company_info = batch_fetch(token, COMPANY_INFO_URL, company_ids, fields=fields)
    company_dict = {c['id']: c for c in company_info}

    all_website_ids = []
    for c in company_info:
        all_website_ids.extend(c.get('websites', []))
    website_url_map = fetch_company_websites(token, all_website_ids)

    for c in company_info:
        c['website_urls'] = [website_url_map.get(wid) for wid in c.get('websites', []) if wid in website_url_map]

    return {i['id']: company_dict.get(i.get('company')) for i in involved_raw}

def fetch_game_names(token, ids):
    raw = batch_fetch(token, GAME_URL, ids, fields='id,name')
    return {g['id']: g['name'] for g in raw}

def fetch_game_versions(token, game_ids):
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}',
    }
    all_versions = []
    batch_size = 300
    for i in range(0, len(game_ids), batch_size):
        batch = game_ids[i:i+batch_size]
        query = f'fields id,game,games,features,url; where game = ({",".join(map(str,batch))}); limit {batch_size};'
        res = requests.post(GAME_VERSIONS_URL, headers=headers, data=query)
        if res.status_code == 200:
            all_versions.extend(res.json())
        else:
            print(f"Failed fetching game_versions batch {i}: {res.text}")
        sleep(0.25)
    return all_versions

def fetch_game_data(token, total_limit=100, batch_size=500):
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}',
    }
    all_games, offset = [], 0
    release_timestamp = 1451606400 # Starting from a known point in time (January 1, 2016)
    fields_to_fetch = (
        'id,name,summary,rating,rating_count,follows,hypes,cover.image_id,artworks.image_id,age_ratings,'
        'alternative_names,collections,dlcs,expansions,forks,remakes,remasters,ports,game_engines,'
        'game_localizations,game_modes,game_status,involved_companies,multiplayer_modes,similar_games,'
        'themes,videos,websites,genres,first_release_date,platforms,screenshots.image_id,dlcs,'
        'franchise, parent_game'
    )
    while len(all_games) < total_limit:
        query = f'fields {fields_to_fetch}; where first_release_date > {release_timestamp}; limit {batch_size}; offset {offset};'
        res = requests.post(GAME_URL, headers=headers, data=query)
        if res.status_code != 200:
            print("Error fetching games:", res.text)
            break
        games_batch = res.json()
        if not games_batch:
            break
        all_games.extend(games_batch)
        offset += batch_size
        print(f"Fetched {len(all_games)} games so far...")
        sleep(0.25)
    print(f"Finished fetching games. Total fetched: {len(all_games)}")
    return all_games[:total_limit]

def tag_dlc(game): # Standalone Expansions and DLC's are practically the same thing. Therefore I will filter it off. 
    dlc_categories = [1, 2, 4] # 0: Main Game, 1: DLC, 2: Expansion, 3: Bundle, 4: Standalone Expansion
    if game.get("category") in dlc_categories:
        return True
    if game.get("parent_game"):
        return True
    return False

def main():
    print("Getting access token...")
    token = get_access_token()

    print("Fetching games...")
    games = fetch_game_data(token)

    print("Fetching websites...")
    website_ids = [w for game in games for w in game.get("websites", [])]
    website_data = batch_fetch(token, WEBSITE_URL, website_ids, fields='id,url,game')
    website_map = {}
    for w in website_data:
        game_id = w.get("game")
        website_map.setdefault(game_id, []).append(w.get("url"))

    print("Assigning images and websites...")
    for game in games:
        game["image_id"] = game.get("cover", {}).get("image_id") or \
                            (game.get("artworks") or [{}])[0].get("image_id")
        game["website_urls"] = website_map.get(game["id"], [])

    print("Fetching and mapping metadata...")
    genre_dict = fetch_dict(token, GENRE_URL, 'name')
    theme_dict = fetch_dict(token, THEME_URL, 'name')
    engine_dict = fetch_dict(token, ENGINE_URL, 'name')
    platform_dict = fetch_dict(token, PLATFORM_URL, 'name')
    mode_dict = fetch_dict(token, GAME_MODE_URL, 'name')

    involved_ids = [i for game in games for i in game.get("involved_companies", [])]
    company_map = fetch_companies(token, involved_ids)

    similar_ids = [sid for game in games for sid in game.get("similar_games", [])]
    related_ids = [gid for game in games for gid in game.get("collections", []) +
                   game.get("remakes", []) + game.get("remasters", []) + game.get("ports", [])]
    name_map = fetch_game_names(token, list(set(similar_ids + related_ids)))

    achievement_ids = [aid for game in games for aid in game.get("achievements", [])]
    achievements = batch_fetch(token, ACHIEVEMENT_URL, achievement_ids, fields='id,name,description,hidden')
    achievement_map = {a['id']: a for a in achievements}

    age_rating_ids = [ar for game in games for ar in game.get("age_ratings", [])]
    age_ratings_raw = batch_fetch(token, AGE_RATING_URL, age_rating_ids, fields='id,category,rating')

    dlc_ids = [dlc for game in games for dlc in game.get("dlcs", [])]
    dlc_data = batch_fetch(token, GAME_URL, list(set(dlc_ids)), fields='id,name,cover.image_id')

    dlc_map = {}
    for dlc in dlc_data:
        dlc_map[dlc['id']] = {
            "id": dlc['id'],
            "name": dlc.get('name', 'Unknown'),
            "image_id": dlc.get('cover', {}).get('image_id'),
            "is_dlc": True
        }
    
    

    AGE_RATING_CATEGORIES = {
        1: "ESRB",
        2: "PEGI",
        3: "CERO",
        4: "USK",
        5: "GRB",
        6: "ClassInd",
        7: "ACB",
        8: "OFLC",
    }

    ESRB_RATINGS = {
        1: "EC (Early Childhood)",
        2: "E (Everyone)",
        3: "E10+",
        4: "T (Teen)",
        5: "M (Mature)",
        6: "AO (Adults Only)",
        7: "RP (Rating Pending)",
    }

    PEGI_RATINGS = {
        1: "3",
        2: "7",
        3: "12",
        4: "16",
        5: "18",
    }

    RATINGS_BY_CATEGORY = {
        1: ESRB_RATINGS,
        2: PEGI_RATINGS,
    }

    age_rating_map = {}
    for ar in age_ratings_raw:
        category_name = AGE_RATING_CATEGORIES.get(ar['category'], "Unknown Category")
        rating_name = RATINGS_BY_CATEGORY.get(ar['category'], {}).get(ar['rating'], "Unknown Rating")
        age_rating_map[ar['id']] = {
            "category_id": ar['category'],
            "category_name": category_name,
            "rating_id": ar['rating'],
            "rating_name": rating_name,
        }

    print("Fetching videos...")
    video_ids = [vid for game in games for vid in game.get("videos", [])]
    video_data = batch_fetch(token, VIDEO_URL, video_ids, fields='id,video_id,name')
    video_map = {v['id']: v for v in video_data}

    print("Mapping names and videos to game objects...")
    for game in games:
        game["genre_names"] = [genre_dict.get(i, "Unknown") for i in game.get("genres", [])]
        game["theme_names"] = [theme_dict.get(i, "Unknown") for i in game.get("themes", [])]
        game["engine_names"] = [engine_dict.get(i, "Unknown") for i in game.get("game_engines", [])]
        game["platform_names"] = [platform_dict.get(i, "Unknown") for i in game.get("platforms", [])]
        game["game_mode_names"] = [mode_dict.get(i, "Unknown") for i in game.get("game_modes", [])]
        game["developer_publisher_details"] = [company_map.get(cid) for cid in game.get("involved_companies", [])]
        game["release_date"] = convert_timestamp(game.get("first_release_date"))
        game["similar_game_names"] = [name_map.get(sid, "Unknown") for sid in game.get("similar_games", [])]
        game["collection_names"] = [name_map.get(cid, "Unknown") for cid in game.get("collections", [])]
        game["remake_names"] = [name_map.get(cid, "Unknown") for cid in game.get("remakes", [])]
        game["remaster_names"] = [name_map.get(cid, "Unknown") for cid in game.get("remasters", [])]
        game["port_names"] = [name_map.get(cid, "Unknown") for cid in game.get("ports", [])]
        game["achievement_details"] = [achievement_map.get(aid) for aid in game.get("achievements", [])]
        game["age_rating_details"] = [age_rating_map.get(ar_id, {"category_name": "Unknown", "rating_name": "Unknown"}) for ar_id in game.get("age_ratings", [])]
        game["video_details"] = [video_map.get(vid) for vid in game.get("videos", [])]
        game["dlc_details"] = [dlc_map.get(dlc_id, {"id": dlc_id, "name": "Unknown", "image_id": None, "is_dlc": True}) for dlc_id in game.get("dlcs", [])]
        game["is_dlc"] = tag_dlc(game)
        

    os.makedirs("data", exist_ok=True)
    with open("data/games_output.json", "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
    print("Data saved to data/games_output.json")

if __name__ == "__main__":
    main()
