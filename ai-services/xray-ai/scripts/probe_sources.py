import urllib.request
import json
import ssl

ctx = ssl.create_default_context()

def probe_figshare(article_id, name):
    url = f"https://api.figshare.com/v2/articles/{article_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            print(f"=== {name} (ID: {article_id}) ===")
            print("Title:", data.get("title"))
            print("License:", data.get("license", {}).get("name"))
            files = data.get("files", [])
            print(f"Total files: {len(files)}")
            for f in files[:10]:
                mb = f.get("size", 0) / (1024 * 1024)
                print(f"  - {f.get('name')} | {mb:.2f} MB | {f.get('download_url')}")
            if len(files) > 10:
                print(f"  ... and {len(files)-10} more files")
    except Exception as e:
        print(f"Error probing {name}: {e}")

if __name__ == "__main__":
    probe_figshare(22363012, "FracAtlas")
    probe_figshare(14825193, "GRAZPEDWRI-DX")
