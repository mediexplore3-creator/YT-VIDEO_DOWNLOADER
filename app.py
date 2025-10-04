# app.py
from flask import Flask, request, send_file
from pytube import YouTube
import os
import shutil
import tempfile
import atexit

# --- Configuration ---
# Create a temporary directory that will be automatically cleaned up on exit
TEMP_DIR = tempfile.mkdtemp()
atexit.register(lambda: shutil.rmtree(TEMP_DIR, ignore_errors=True))

app = Flask(__name__)
# The application now only serves the main logic and downloads from the current folder.
# No need to configure template_folder or static_folder since we're using embedded HTML/CSS.

# --- Embedded HTML and CSS (Single File Requirement) ---
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        /* Embedded CSS from previous style.css */
        :root {
            --primary-color: #1e88e5; /* Blue accent */
            --primary-color-hover: #1565c0; /* Darker blue */
            --text-color: #333;
            --card-bg: #fff;
            --bg-color: #f8f9fa; /* Light grey background */
            --border-color: #ced4da;
            --error-color: #dc3545;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Roboto', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }

        header {
            background-color: var(--primary-color);
            color: #fff;
            padding: 1rem 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .header-content h1 {
            font-weight: 500;
            text-align: center;
        }

        .container {
            width: 90%;
            max-width: 1200px;
            margin: 0 auto;
        }

        main {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem 0;
        }

        .card {
            background-color: var(--card-bg);
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 600px;
            text-align: center;
        }

        .card h2 {
            margin-bottom: 1.5rem;
            font-weight: 400;
            color: var(--primary-color);
        }

        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 1.5rem;
        }

        .input-group input[type="url"],
        .input-group select {
            flex-grow: 1;
            padding: 0.75rem 1rem;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.2s;
        }

        .input-group input[type="url"]:focus,
        .input-group select:focus {
            border-color: var(--primary-color);
            outline: none;
            box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.2);
        }

        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: background-color 0.2s, box-shadow 0.2s;
            white-space: nowrap;
        }

        .primary-btn {
            background-color: var(--primary-color);
            color: white;
        }

        .primary-btn:hover:not(:disabled) {
            background-color: var(--primary-color-hover);
        }

        .download-btn {
            background-color: #4CAF50;
            color: white;
        }

        .download-btn:hover:not(:disabled) {
            background-color: #388E3C;
        }

        .btn:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }

        .video-info {
            margin-top: 1rem;
            padding: 1rem 0;
            border-top: 1px solid #eee;
        }

        .video-info h3 {
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: var(--text-color);
        }

        .video-title {
            font-weight: 700;
        }

        .resolution-prompt {
            font-size: 0.95rem;
            color: #555;
            margin-bottom: 1rem;
        }

        .download-group {
            align-items: center; 
        }

        .alert {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            font-size: 0.95rem;
            text-align: left;
        }

        .error-message {
            background-color: #f8d7da;
            color: var(--error-color);
            border: 1px solid #f5c6cb;
        }

        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top: 3px solid #fff;
            border-radius: 50%;
            width: 15px;
            height: 15px;
            animation: spin 1s linear infinite;
            display: inline-block;
            vertical-align: middle;
            margin-right: 5px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        footer {
            padding: 1rem;
            text-align: center;
            background-color: #eee;
            color: #6c757d;
            font-size: 0.8rem;
        }

        @media (max-width: 650px) {
            .card {
                margin: 1rem;
                padding: 1.5rem;
            }
            
            .input-group:not(.download-group) {
                flex-direction: column;
            }
            
            .input-group input[type="url"] {
                margin-bottom: 5px;
            }
            
            .download-group {
                 flex-direction: column;
            }

            .download-group select,
            .download-group button {
                width: 100%;
                margin-bottom: 5px;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container header-content">
            <h1>YouTube Downloader</h1>
        </div>
    </header>

    <main class="container">
        <div class="card">
            <h2>Paste Your YouTube Link 👇</h2>
            
            {{ content }}

        </div>
    </main>

    <footer>
        <p>&copy; 2024 YouTube Downloader | Built with Flask & Pytube</p>
    </footer>

    <script>
        const fetchForm = document.getElementById('fetch-form');
        const fetchBtn = document.getElementById('fetch-btn');
        const downloadForm = document.getElementById('download-form');
        const downloadBtn = document.getElementById('download-btn');
        const urlInput = document.getElementById('url');

        function setLoading(button, text) {
            button.disabled = true;
            button.innerHTML = `<span class="spinner"></span> ${text}`;
        }

        function resetButtons() {
            if (fetchBtn) {
                fetchBtn.disabled = false;
                fetchBtn.innerHTML = 'Fetch Qualities';
            }
            if (downloadBtn) {
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = 'Download';
            }
        }

        if (fetchForm) {
            fetchForm.addEventListener('submit', function() {
                if (urlInput.checkValidity()) {
                    setLoading(fetchBtn, 'Fetching video info...');
                }
            });
        }

        if (downloadForm) {
            downloadForm.addEventListener('submit', function() {
                setLoading(downloadBtn, 'Downloading...');
            });
        }
        
        // Reset buttons on page load (in case of navigation/error)
        window.addEventListener('load', resetButtons);
        
    </script>
</body>
</html>
"""

def generate_html_content(error=None, streams=None, video_url=None, video_title=None):
    """Generates the dynamic portion of the HTML template."""
    
    error_html = f'<div class="alert error-message">{error}</div>' if error else ''
    
    # Form 1: URL Input and Fetch
    fetch_form = f"""
        <form id="fetch-form" action="/" method="POST">
            <input type="hidden" name="action" value="fetch">
            <div class="input-group">
                <input type="url" id="url" name="url" placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ" required 
                       value="{video_url if video_url else ''}">
                <button type="submit" class="btn primary-btn" id="fetch-btn">
                    Fetch Qualities
                </button>
            </div>
        </form>
    """
    
    stream_options = '\n'.join([
        f'<option value="{s["itag"]}">{s["resolution"]} (MP4)</option>'
        for s in streams
    ]) if streams else ''
    
    # Dynamic Section: Quality Selection (only shown if streams are available)
    download_section = ""
    if streams:
        download_section = f"""
            <div class="video-info">
                <h3>Video: <span class="video-title">{video_title}</span></h3>
                <p class="resolution-prompt">Select desired resolution:</p>
            </div>

            <form id="download-form" action="/" method="POST">
                <input type="hidden" name="action" value="download">
                <input type="hidden" name="url" value="{video_url}">
                
                <div class="input-group download-group">
                    <select id="quality-select" name="itag" required>
                        <option value="">-- Select Quality --</option>
                        {stream_options}
                    </select>
                    <button type="submit" class="btn download-btn" id="download-btn">
                        Download
                    </button>
                </div>
            </form>
        """
        
    return error_html + fetch_form + download_section


@app.route('/', methods=['GET', 'POST'])
def index():
    """Renders the main page and handles URL submission."""
    error = None
    streams = None
    video_url = request.form.get('url') if request.method == 'POST' else None
    video_title = None

    if request.method == 'POST':
        action = request.form.get('action')
        
        if not video_url:
            error = "Please enter a valid YouTube URL."
            # Fall through to render the page with error
        else:
            try:
                # The video title is sanitized to be safe for filenames
                yt = YouTube(video_url)
                video_title = yt.title.replace("/", "_").replace("\\", "_") 
                
                if action == 'fetch':
                    available_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
                    
                    streams = []
                    added_resolutions = set() 
                    for s in available_streams:
                        if s.resolution and s.resolution not in added_resolutions:
                            streams.append({
                                'resolution': s.resolution,
                                'itag': s.itag
                            })
                            added_resolutions.add(s.resolution)

                    if not streams:
                        error = "No progressive MP4 streams found for this video."
                
                elif action == 'download':
                    itag = request.form.get('itag')
                    if not itag:
                        error = "Please select a download quality."
                    else:
                        stream = yt.streams.get_by_itag(itag)
                        if not stream:
                            error = f"Stream with ITAG {itag} not found."
                        else:
                            # Create a safe filename and path within the temp directory
                            filename = f"{video_title}_{stream.resolution}.mp4"
                            temp_file_path = os.path.join(TEMP_DIR, filename)
                            
                            # Download to the temporary location
                            stream.download(output_path=TEMP_DIR, filename=filename)

                            # Stream the file to the user and ensure it's removed immediately after
                            response = send_file(
                                temp_file_path, 
                                as_attachment=True, 
                                download_name=filename,
                                mimetype="video/mp4"
                            )
                            # Cleanup the specific file immediately after sending
                            @response.call_on_close
                            def on_close():
                                try:
                                    os.unlink(temp_file_path)
                                except Exception as e:
                                    print(f"Error cleaning up temp file {temp_file_path}: {e}")
                            
                            return response
                            
            except Exception as e:
                error = f"An error occurred: Invalid URL or video not available. ({str(e).splitlines()[0]})"
                print(f"Error: {e}")

    # Render the main HTML by injecting the dynamic content
    dynamic_content = generate_html_content(error=error, streams=streams, video_url=video_url, video_title=video_title)
    return INDEX_HTML.replace('{{ content }}', dynamic_content)

if __name__ == '__main__':
    # The cleanup is handled by atexit.register, so no need for extra cleanup here.
    print(f"Temporary download files will be stored in: {TEMP_DIR}")
    app.run(debug=True)
