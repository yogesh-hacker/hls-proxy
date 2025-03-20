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