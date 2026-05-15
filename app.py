from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import yt_dlp
import requests
import os
import io
import tempfile

app = Flask(__name__)
CORS(app)  # Website access u oggolow

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.tiktok.com/',
}

@app.route('/')
def home():
    return jsonify({"status": "✅ Server shaqeynayaa!"})

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.json
        url = data.get('url', '').strip()
        dl_type = data.get('type', 'video')  # video or audio

        if not url:
            return jsonify({"error": "URL ma jirto"}), 400

        # TikTok API
        if 'tiktok.com' in url or 'vt.tiktok' in url:
            # Resolve short URL
            try:
                r = requests.head(url, allow_redirects=True, timeout=10)
                url = r.url
            except:
                pass

            api_url = f"https://tikwm.com/api/?url={url}"
            r = requests.get(api_url, headers=HEADERS, timeout=15)
            d = r.json()

            if d.get('code') == 0:
                data_obj = d['data']
                images = data_obj.get('images', [])

                if images:
                    # Photo slideshow - first image
                    media_url = images[0]
                    filename = "tiktok_photo.jpg"
                    mime = "image/jpeg"
                elif dl_type == 'audio':
                    media_url = data_obj.get('music', '')
                    filename = "tiktok_audio.mp3"
                    mime = "audio/mpeg"
                else:
                    media_url = data_obj.get('play', '')
                    filename = "tiktok_video.mp4"
                    mime = "video/mp4"

                # Stream directly to user
                media_response = requests.get(media_url, headers=HEADERS, stream=True, timeout=30)

                def generate():
                    for chunk in media_response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk

                return Response(
                    generate(),
                    headers={
                        'Content-Type': mime,
                        'Content-Disposition': f'attachment; filename="{filename}"',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Expose-Headers': 'Content-Disposition'
                    }
                )
            else:
                return jsonify({"error": "TikTok link khalad"}), 400

        # YouTube / Other platforms
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                fmt = 'bestaudio/best' if dl_type == 'audio' else 'best[ext=mp4]/best'
                ext = 'mp3' if dl_type == 'audio' else 'mp4'
                mime = 'audio/mpeg' if dl_type == 'audio' else 'video/mp4'

                ydl_opts = {
                    'format': fmt,
                    'outtmpl': f'{tmpdir}/media.%(ext)s',
                    'quiet': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }] if dl_type == 'audio' else [],
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'media')[:50]

                # Find file
                files = os.listdir(tmpdir)
                if not files:
                    return jsonify({"error": "File ma jirto"}), 500

                filepath = os.path.join(tmpdir, files[0])

                with open(filepath, 'rb') as f:
                    data_bytes = f.read()

                return Response(
                    data_bytes,
                    headers={
                        'Content-Type': mime,
                        'Content-Disposition': f'attachment; filename="{title}.{ext}"',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Expose-Headers': 'Content-Disposition'
                    }
                )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/info', methods=['POST'])
def get_info():
    try:
        data = request.json
        url = data.get('url', '').strip()

        if 'tiktok.com' in url or 'vt.tiktok' in url:
            try:
                r = requests.head(url, allow_redirects=True, timeout=10)
                url = r.url
            except:
                pass

            api_url = f"https://tikwm.com/api/?url={url}"
            r = requests.get(api_url, headers=HEADERS, timeout=15)
            d = r.json()

            if d.get('code') == 0:
                obj = d['data']
                return jsonify({
                    "title": obj.get('title', 'TikTok Video'),
                    "platform": "tiktok",
                    "thumbnail": obj.get('cover', ''),
                    "duration": obj.get('duration', 0),
                    "has_images": bool(obj.get('images')),
                    "image_count": len(obj.get('images', [])),
                })

        return jsonify({"title": "Video", "platform": "other"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
