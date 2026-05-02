#!/usr/bin/env python3
"""
LOTUS Snack 2026 — TikTok Scraper (yt-dlp)
Scrape views, likes, shares, comments, saves, followers from TikTok video links.
Uses yt-dlp for reliable JSON metadata extraction.
Usage: python3 scripts/tiktok_scraper.py [output_json]
"""

import json
import sys
import subprocess
import time
import random

# ============================================================
#  MANUAL OVERRIDE — KOL ที่ดึงยอดอัตโนมัติไม่ได้
#  (เช่น วิดีโอถูกจำกัดอายุ / ต้อง login)
#  ใส่ยอดล่าสุดที่ดูด้วยตาจาก TikTok แล้วอัปเดตเป็นระยะ
# ============================================================
MANUAL_OVERRIDE = {
    # 'username_example': {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0, 'saves': 0, 'followers': 0},
}

# ============================================================
#  KOL LINKS — สร้างจาก Excel โดย skill kol-dashboard-generator
# ============================================================
KOL_LINKS = {
    "markc.boardgame": "https://vt.tiktok.com/ZS9aPr8MX/",
    "minkmories": "",
    "dairyparty": "",
    "narongrit11414": "",
    "tanawatpankaew": "",
    "fford._.mini": "",
    "ledswu": "",
    "debuam012": "",
    "saruanly": "https://vt.tiktok.com/ZS9a2kjxW/",
    "tuajeed.office": "",
    "miinez_": "",
    "gonsalosol": "",
    "sharkwow.ch": "",
    "witbenmoreallright": "https://vt.tiktok.com/ZS9aABnfe/",
    "gampamao": "https://vt.tiktok.com/ZS9aSw6mn/",
    "tatatomang": "",
    "taloncamp_sg": "",
    "sarun_kritaterakul": "https://vt.tiktok.com/ZS9aBHdoY/",
    "nattienote": ""
}


def resolve_tiktok_url(url, timeout=15):
    """Resolve vt.tiktok.com short link to full https://www.tiktok.com/@user/video/ID URL."""
    if 'vt.tiktok.com' not in url and '/t/' not in url:
        return url
    try:
        # Use curl to follow redirects (yt-dlp can fail at redirect step)
        result = subprocess.run(
            ['curl', '-sIL', '-A', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)', url],
            capture_output=True, text=True, timeout=timeout
        )
        # Last "location:" header has the final URL
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.lower().startswith('location:'):
                final = line.split(':', 1)[1].strip()
                if '/video/' in final:
                    return final.split('?')[0]  # strip query string
        return url
    except Exception as e:
        print(f"    URL resolve failed: {e}")
        return url


def scrape_tiktok_video(url, timeout=60):
    """Extract TikTok video metadata using yt-dlp --dump-json."""
    try:
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-download', '--no-warnings', url],
            capture_output=True, text=True, timeout=timeout
        )

        if result.returncode != 0:
            if 'comfortable' in result.stderr or 'Log in' in result.stderr:
                print(f"    Age-restricted, retrying with --age-limit 99...")
                result = subprocess.run(
                    ['yt-dlp', '--dump-json', '--no-download', '--no-warnings',
                     '--age-limit', '99', url],
                    capture_output=True, text=True, timeout=timeout
                )

            if result.returncode != 0:
                print(f"    yt-dlp error: {result.stderr.strip()[:200]}")
                return None

        info = json.loads(result.stdout)

        return {
            'url': info.get('webpage_url', url),
            'views': info.get('view_count', 0) or 0,
            'likes': info.get('like_count', 0) or 0,
            'shares': info.get('repost_count', 0) or 0,
            'comments': info.get('comment_count', 0) or 0,
            'saves': (info.get('save_count')
                      or info.get('collect_count')
                      or info.get('favorite_count')
                      or info.get('bookmark_count')
                      or 0),
            'followers': info.get('channel_follower_count', 0) or 0,
        }

    except subprocess.TimeoutExpired:
        print(f"    Timeout scraping {url}")
        return None
    except json.JSONDecodeError as e:
        print(f"    JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"    Error scraping {url}: {e}")
        return None


def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'scrape_results.json'

    results = {}
    active_kols = {k: v for k, v in KOL_LINKS.items() if v and str(v).strip()}

    if not active_kols:
        print("No KOL links to scrape. Output empty results.")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        return

    print(f"Scraping {len(active_kols)} KOL(s) using yt-dlp...")

    for username, link in active_kols.items():
        if username in MANUAL_OVERRIDE:
            results[username] = MANUAL_OVERRIDE[username]
            results[username]['url'] = link
            print(f"  @{username} — manual override")
            continue

        print(f"  Scraping @{username}...")
        data = scrape_tiktok_video(link)
        if not data:
            # Retry: resolve vt link to full URL and try again
            full_url = resolve_tiktok_url(link)
            if full_url != link:
                print(f"    Retrying with resolved URL: {full_url}")
                data = scrape_tiktok_video(full_url)
        if data:
            results[username] = data
            print(f"    Views: {data['views']:,} | Likes: {data['likes']:,} | "
                  f"Shares: {data['shares']:,} | Comments: {data['comments']:,} | "
                  f"Saves: {data['saves']:,}")
        else:
            print(f"    Failed to scrape @{username}")

        time.sleep(random.uniform(0.5, 1.5))

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {output_file}")
    print(f"Successfully scraped: {len(results)}/{len(active_kols)}")


if __name__ == '__main__':
    main()
