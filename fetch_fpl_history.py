import os
import json
import httpx
from tqdm import tqdm
from typing import List, Dict, Any
import asyncio

# Directory to save data
DATA_DIR = os.path.join(os.path.dirname(__file__), 'app', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# List of seasons to fetch (2017/18 onwards; 2016/17 and earlier are not available via API)
SEASONS = [
    (2017, '2017-18'),
    (2018, '2018-19'),
    (2019, '2019-20'),
    (2020, '2020-21'),
    (2021, '2021-22'),
    (2022, '2022-23'),
    (2023, '2023-24'),
]

BASE_URL = 'https://fantasy.premierleague.com/api'

async def fetch_season_player_histories(season_id: int, season_label: str) -> None:
    if season_id == 2023:
        bootstrap_url = f'{BASE_URL}/bootstrap-static/'
        summary_url = f'{BASE_URL}/element-summary/{{player_id}}/'
    else:
        bootstrap_url = f'{BASE_URL}/{season_id}/bootstrap-static/'
        summary_url = f'{BASE_URL}/{season_id}/element-summary/{{player_id}}/'
    async with httpx.AsyncClient() as client:
        print(f'Fetching player list for {season_label}...')
        try:
            r = await client.get(bootstrap_url)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"Skipping {season_label}: {e}")
            return
        data = r.json()
        players: List[Dict[str, Any]] = data['elements']
        out: List[Dict[str, Any]] = []
        for p in tqdm(players, desc=f'Players {season_label}'):
            pid = p['id']
            try:
                r2 = await client.get(summary_url.format(player_id=pid))
                r2.raise_for_status()
                details = r2.json()
                out.append({
                    'id': pid,
                    'first_name': p.get('first_name', ''),
                    'second_name': p.get('second_name', ''),
                    'team': p.get('team', ''),
                    'element_type': p.get('element_type', ''),
                    'history': details.get('history', []),
                })
            except Exception as e:
                print(f'Failed for player {pid} in {season_label}: {e}')
        # Save to file
        out_path = os.path.join(DATA_DIR, f'{season_label}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2)
        print(f'Saved {len(out)} players for {season_label} to {out_path}')

async def main() -> None:
    for season_id, season_label in SEASONS:
        await fetch_season_player_histories(season_id, season_label)

if __name__ == '__main__':
    asyncio.run(main())
