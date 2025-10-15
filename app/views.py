from django.http import HttpResponse

def home(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>MediaVanced Extractor</title>
        <!-- Bootstrap CDN -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background-color: #ffffff;
                color: #333;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container-box {
                max-width: 600px;
                width: 100%;
                padding: 30px;
                background: #f8f9fa;
                border-radius: 10px;
                box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            h1 {
                color: #007bff;
                font-weight: bold;
            }
            .footer {
                margin-top: 20px;
                font-size: 0.9em;
                color: #666;
            }
            a {
                color: #007bff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .path-list {
                text-align: left;
                padding: 0;
                list-style: none;
            }
            .path-list li {
                background: #e9ecef;
                margin: 5px 0;
                padding: 10px;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container-box">
            <h1>Welcome to MediaVanced Extractor</h1>
            <p>
                This video extractor is a proprietary tool developed by 
                <a href="https://github.com/yogesh-hacker/MediaVanced" target="_blank"><strong>MediaVanced</strong></a>.
            </p>
            <p>
                It is for <b>personal and research use only</b> and must comply with copyright laws.
            </p>
            <p>
                Unauthorized redistribution, modification, or commercial use is strictly prohibited.
                MediaVanced does not support piracy.
            </p>

            <h3>Available Paths:</h3>
            <ul class="path-list">
                <li><b>/</b> - Home Page</li>
                <li><b>/proxy/?url=</b> - Proxies an <b>M3U8 URL</b> for streaming.</li>
                <li><b>/api/?url=</b> - Extracts an <b>M3U8 link</b> from Multimovies.</li>
            </ul>

            <p class="footer">
                &copy; 2025 <a href="https://github.com/yogesh-hacker/MediaVanced" target="_blank">MediaVanced</a>. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content, content_type="text/html")


def site_paused(request, *args, **kwargs):
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Site Temporarily Paused</title>
        <style>
            body {
                margin: 0;
                height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1e293b, #0f172a);
                color: #e2e8f0;
                text-align: center;
                overflow: hidden;
            }
            h1 {
                font-size: 2rem;
                margin-bottom: 0.5rem;
                color: #facc15;
                text-shadow: 0 0 10px #facc15;
                animation: pulse 2s infinite;
            }
            p {
                font-size: 1.1rem;
                color: #cbd5e1;
                max-width: 400px;
                line-height: 1.6;
            }
            .loader {
                margin-top: 30px;
                border: 4px solid #334155;
                border-top: 4px solid #facc15;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }
            footer {
                position: absolute;
                bottom: 15px;
                font-size: 0.9rem;
                color: #64748b;
            }
        </style>
    </head>
    <body>
        <h1>🚧 Site Temporarily Paused 🚧</h1>
        <p>Due to over-usage of bandwidth, this site is temporarily paused<br>
        to keep other personal projects running smoothly.</p>
        <div class="loader"></div>
        <footer>— Powered by Hacker India ⚡</footer>
    </body>
    </html>
    """
    return HttpResponse(html, content_type="text/html", status=503)