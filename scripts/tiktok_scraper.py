#!/usr/bin/env python3
"""
LOTUS Snack 2026 — TikTok Scraper (yt-dlp)
Scrape views, likes, shares, comments, saves, followers from TikTok video links.
Uses yt-dlp for reliable JSON metadata extraction.
Usage: python3 scripts/tiktok_scraper.py [output_json]
"""

import json
import os
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
#  PHASE 1 — KOL LINKS
# ============================================================
KOL_LINKS = {
    "markc.boardgame": "https://vt.tiktok.com/ZS9aPr8MX/",
    "minkmories": "https://vt.tiktok.com/ZS9bLxokr/",
    "dairyparty": "https://www.tiktok.com/@dairyparty/video/7637753510116740360",
    "narongrit11414": "https://vt.tiktok.com/ZS9EsqqWw/",
    "tanawatpankaew": "https://vt.tiktok.com/ZS9KqJggx/",
    "fford._.mini": "https://vt.tiktok.com/ZS9bMV5M5/",
    "ledswu": "https://vt.tiktok.com/ZS9G9rGKX/",
    "debuam012": "https://vt.tiktok.com/ZS9bFpyNh/",
    "saruanly": "https://vt.tiktok.com/ZS9a2kjxW/",
    "tuajeed.office": "https://vt.tiktok.com/ZSxjfekwg/",
    "miinez_": "https://vt.tiktok.com/ZS9tk5kKo/",
    "gonsalosol": "https://vt.tiktok.com/ZSx8JCwkq/",
    "sharkwow.ch": "https://vt.tiktok.com/ZS9Kq6Fbf/",
    "witbenmoreallright": "https://vt.tiktok.com/ZS9aABnfe/",
    "gampamao": "https://vt.tiktok.com/ZS9aSw6mn/",
    "tatatomang": "https://vt.tiktok.com/ZS9KbaK3n/",
    "taloncamp_sg": "https://vt.tiktok.com/ZS9bmgMM2/",
    "sarun_kritaterakul": "https://vt.tiktok.com/ZS9aBHdoY/",
    "nattienote": "https://vt.tiktok.com/ZS9vSfoWE/"
}

# ============================================================
#  PHASE 2 — KOL LINKS (เฉพาะ KOL ที่โพสต์แล้ว 23 คน)
# ============================================================
PHASE2_KOL_LINKS = {
    # ขาไก่ (10)
    "nurse.enjoyea": "https://vt.tiktok.com/ZSCXV8bxS/",
    "100lowteens": "https://vt.tiktok.com/ZSCaK4qaX/",
    "joinjoy89": "https://www.tiktok.com/@joinjoy89/video/7657534776919788807",
    "sristories.official": "https://vt.tiktok.com/ZSCmW9rtB/",
    "mayme_711": "https://vt.tiktok.com/ZSCxaqXx1/",
    "tima.chan": "https://vt.tiktok.com/ZSCuefFQf/",
    "ningninkka": "https://vt.tiktok.com/ZSCmc9UY2/",
    "pizzaplazaa": "https://vt.tiktok.com/ZSCuJN1pr/",
    "i.prim": "https://vt.tiktok.com/ZSCxGy9Ds/",
    "bolongkinn": "https://vt.tiktok.com/ZSCxNLp27/",
    # น่องไก่ (8)
    "haruyda": "https://vt.tiktok.com/ZSCmK3DTB/",
    "plaifahhahaha": "https://vt.tiktok.com/ZSCuj1FVw/",
    "chengandrock": "https://vt.tiktok.com/ZSCm7cu3t/",
    "gindaieek": "https://vt.tiktok.com/ZSCuMCC3W/",
    "googidd": "https://vt.tiktok.com/ZSCmsHPmh/",
    "pankpanq": "https://vt.tiktok.com/ZSCXsVaYU/",
    "whatpalaa": "https://vt.tiktok.com/ZSC9NddGN/",
    "sweettart.tt": "https://vt.tiktok.com/ZSCxj7s87/",
    # หนังไก่ (5)
    "11.mn.84": "https://vt.tiktok.com/ZSCvyMdnU/",
    "palmmookangrang": "https://vt.tiktok.com/ZSCuDkWrY/",
    "enjoyeatingclub": "https://vt.tiktok.com/ZSCujUmoF/",
    "ssaintst": "https://vt.tiktok.com/ZSCmwDGth/",
    "stampginra": "https://vt.tiktok.com/ZSCQT9qpH/",
    "mew_natheera": "https://vt.tiktok.com/ZSCweqNpu/",
    "faymily_": "https://vt.tiktok.com/ZSXkSk17q/",
    "mild.prapaipan": "https://vt.tiktok.com/ZSCKKRbyt/",
    "mhingkualoak": "https://vt.tiktok.com/ZSXe3jTp8/",
    "thintomorrow": "https://vt.tiktok.com/ZSXDt25E6/",
    "farbeer69": "https://vt.tiktok.com/ZSXxqjvra/",
    "ninkkieee": "https://vt.tiktok.com/ZSCoSeMU8/",
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
            ['yt-dlp', '--dump-json', '--no-download', '--no-warnings'] + 
            (['--cookies', os.environ['TIKTOK_COOKIES_FILE']] if os.environ.get('TIKTOK_COOKIES_FILE') else []) + [url],
            capture_output=True, text=True, timeout=timeout
        )

        if result.returncode != 0:
            if 'comfortable' in result.stderr or 'Log in' in result.stderr:
                print(f"    Age-restricted, retrying with --age-limit 99...")
                result = subprocess.run(
                    ['yt-dlp', '--dump-json', '--no-download', '--no-warnings',
                     '--age-limit', '99'] + 
                    (['--cookies', os.environ['TIKTOK_COOKIES_FILE']] if os.environ.get('TIKTOK_COOKIES_FILE') else []) + [url],
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


def scrape_kol_list(kol_links, output_file, phase_label="Phase 1"):
    """Scrape a dict of {username: link} and save to output_file."""
    results = {}
    active_kols = {k: v for k, v in kol_links.items() if v and str(v).strip()}

    if not active_kols:
        print(f"[{phase_label}] No KOL links to scrape. Output empty results.")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        return

    print(f"\n{'='*60}")
    print(f"[{phase_label}] Scraping {len(active_kols)} KOL(s) using yt-dlp...")
    print(f"{'='*60}")

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
            # Capture diagnostic info
            try:
                head_result = subprocess.run(
                    ['curl', '-sIL', '-A', 'Mozilla/5.0', '-o', '/dev/null', '-w', '%{url_effective}|%{http_code}', link],
                    capture_output=True, text=True, timeout=15
                )
                resolved = head_result.stdout
                ytdlp_result = subprocess.run(
                    ['yt-dlp', '--dump-json', '--no-download'] +
                    (['--cookies', os.environ['TIKTOK_COOKIES_FILE']] if os.environ.get('TIKTOK_COOKIES_FILE') else []) + [link],
                    capture_output=True, text=True, timeout=30
                )
                results[f'_debug_{username}'] = {
                    'orig_url': link,
                    'curl_resolve': resolved[:200],
                    'ytdlp_stderr': ytdlp_result.stderr[:500],
                    'ytdlp_returncode': ytdlp_result.returncode,
                }
            except Exception as e:
                results[f'_debug_{username}'] = {'orig_url': link, 'exception': str(e)}

        time.sleep(random.uniform(0.5, 1.5))

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[{phase_label}] Results saved to {output_file}")
    print(f"[{phase_label}] Successfully scraped: {len(results)}/{len(active_kols)}")


def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'scrape_results.json'

    # Phase 1
    scrape_kol_list(KOL_LINKS, output_file, "Phase 1")

    # Phase 2
    p2_output = output_file.replace('.json', '_p2.json')
    if p2_output == output_file:
        p2_output = 'scrape_results_p2.json'
    scrape_kol_list(PHASE2_KOL_LINKS, p2_output, "Phase 2")


if __name__ == '__main__':
    main()
