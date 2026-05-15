from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.tiktok.com/',
}

@app.route('/')
def home():
    return jsonify({"status": "Server shaqeynayaa!"})

@app.route('/download', methods=['POST', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        data = request.json
        url = data.get('url', '').strip()
        dl_type = data.get('type', 'video')

        if not url:
            return jsonify({"error": "URL ma jirto"}), 400

        # Resolve short URL
        try:
            r = requests.head(url, allow_redirects=True, timeout=10, headers=HEADERS)
            url = r.url
        except:
            pass

        # TikTok API
        if 'tiktok.com' in url:
            api_url = f"https://tikwm.com/api/?url={url}"
            r = requests.get(api_url, headers=HEADERS, timeout=15)
            d = r.json()

            if d.get('code') == 0:
                obj = d['data']
                images = obj.get('images', [])

                if images and dl_type == 'video':
                    media_url = images[0]
                    filename = "tiktok_photo.jpg"
                    mime = "image/jpeg"
                elif dl_type == 'audio':
                    media_url = obj.get('music', '')
                    filename = "tiktok_audio.mp3"
                    mime = "audio/mpeg"
                else:
                    media_url = obj.get('play', '')
                    filename = "tiktok_video.mp4"
                    mime = "video/mp4"

                # Stream to user
                media_r = requests.get(
                    media_url,
                    headers=HEADERS,
                    stream=True,
                    timeout=60
                )

                def generate():
                    for chunk in media_r.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk

                response = Response(
                    generate(),
                    mimetype=mime,
                    headers={
                        'Content-Disposition': f'attachment; filename="{filename}"',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Expose-Headers': 'Content-Disposition, Content-Type',
                        'Cache-Control': 'no-cache',
                    }
                )
                return response

            else:
                return jsonify({"error": "TikTok link khalad - URL hubi"}), 400

        # YouTube / Others - yt-dlp
        else:
            try:
                import yt_dlp
                import tempfile

                with tempfile.TemporaryDirectory() as tmpdir:
                    fmt = 'bestaudio/best' if dl_type == 'audio' else 'best[ext=mp4]/best'
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
                        title = info.get('title', 'media')[:40]

                    files = os.listdir(tmpdir)
                    if not files:
                        return jsonify({"error": "File ma jirto"}), 500

                    filepath = os.path.join(tmpdir, files[0])
                    ext = files[0].split('.')[-1]
                    mime = 'audio/mpeg' if dl_type == 'audio' else 'video/mp4'
                    filename = f"{title}.{ext}"

                    with open(filepath, 'rb') as f:
                        data_bytes = f.read()

                response = Response(
                    data_bytes,
                    mimetype=mime,
                    headers={
                        'Content-Disposition': f'attachment; filename="{filename}"',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Expose-Headers': 'Content-Disposition, Content-Type',
                    }
                )
                return response

            except Exception as e:
                return jsonify({"error": f"YouTube khalad: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
