# app.py
from flask import Flask, render_template, request, send_file
from pytube import YouTube
import os
import shutil
import tempfile
import atexit

# --- Configuration ---
# Set template_folder to the current directory ('.') so Flask finds index.html
# Set static_folder to the current directory as well (though not strictly needed
# since CSS is embedded in index.html, it's good practice for single-folder structure)
app = Flask(__name__, template_folder='.', static_folder='.')

# Create a private, automatically cleaned up temporary directory for downloads
TEMP_DIR = tempfile.mkdtemp()
# Register cleanup function to delete the temporary folder when the app exits
atexit.register(lambda: shutil.rmtree(TEMP_DIR, ignore_errors=True))

@app.route('/', methods=['GET', 'POST'])
def index():
    """Renders the main page and handles URL submission."""
    error = None
    streams = None
    video_url = request.form.get('url') if request.method == 'POST' else ''
    video_title = None

    if request.method == 'POST':
        action = request.form.get('action')
        
        if not video_url:
            error = "Please enter a valid YouTube URL."
        else:
            try:
                yt = YouTube(video_url)
                # Sanitize title for filename safety
                video_title = yt.title.replace("/", "_").replace("\\", "_") 
                
                if action == 'fetch':
                    # Filter for progressive streams (video + audio combined)
                    available_streams = yt.streams.filter(
                        progressive=True, 
                        file_extension='mp4'
                    ).order_by('resolution').desc()
                    
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

                            # Stream the file to the user
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
                # Catch general PyTube/network errors
                error = f"An error occurred: Invalid URL or video not available. ({str(e).splitlines()[0]})"
                print(f"Error: {e}")

    # Render the index.html template with current variables
    return render_template(
        'index.html', 
        error=error, 
        streams=streams, 
        video_url=video_url, 
        video_title=video_title
    )

if __name__ == '__main__':
    print(f"Temporary download files will be stored in: {TEMP_DIR}")
    app.run(debug=True)

