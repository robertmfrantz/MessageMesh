"""
Simple MessageMesh gallery and uploader.

This app serves a small web UI for browsing and uploading images to the
server-side image directory that can also be shared by the FTP server.
"""

from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse
import html
import mimetypes
import os
import posixpath
import secrets


HOST = "127.0.0.1"
PORT = 8000
IMAGE_DIRECTORY = Path(__file__).resolve().parent / "shared_images"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
TEMP_UPLOAD_SUFFIX = ".uploading"


def ensure_image_directory():
    IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename):
    name = Path(filename).name.strip()
    if not name:
        return ""

    safe_name = "".join(
        character
        for character in name
        if character.isalnum() or character in ("-", "_", ".", " ")
    ).strip(" .")
    return safe_name


def is_allowed_image(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def list_images():
    ensure_image_directory()
    return sorted(
        (
            path
            for path in IMAGE_DIRECTORY.iterdir()
            if path.is_file()
            and path.suffix.lower() in ALLOWED_EXTENSIONS
            and not path.name.endswith(TEMP_UPLOAD_SUFFIX)
        ),
        key=lambda path: path.name.lower(),
    )


def render_page(message=""):
    image_cards = []
    for image_path in list_images():
        image_name = html.escape(image_path.name)
        image_url = f"/images/{quote(image_path.name)}"
        image_cards.append(
            f"""
            <article class="card">
              <img src="{image_url}" alt="{image_name}" loading="lazy">
              <div class="meta">
                <span>{image_name}</span>
              </div>
            </article>
            """
        )

    gallery_markup = "\n".join(image_cards) or """
        <div class="empty-state">
          <p>No images uploaded yet.</p>
          <p>Use the form above to add the first one.</p>
        </div>
    """

    message_markup = (
        f'<p class="status">{html.escape(message)}</p>' if message else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MessageMesh Gallery</title>
  <style>
    :root {{
      --sand: #f4efe6;
      --paper: #fffaf2;
      --ink: #1f2933;
      --accent: #d96c3d;
      --accent-dark: #a64d2a;
      --line: #dfd2bf;
      --shadow: rgba(67, 45, 28, 0.12);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(217, 108, 61, 0.16), transparent 28%),
        linear-gradient(180deg, var(--paper), var(--sand));
      min-height: 100vh;
    }}

    main {{
      width: min(1100px, calc(100% - 2rem));
      margin: 0 auto;
      padding: 2rem 0 3rem;
    }}

    .hero {{
      display: grid;
      gap: 1rem;
      margin-bottom: 2rem;
    }}

    .hero h1 {{
      margin: 0;
      font-size: clamp(2rem, 5vw, 4rem);
      line-height: 0.95;
      letter-spacing: -0.03em;
    }}

    .hero p {{
      margin: 0;
      max-width: 50rem;
      font-size: 1.05rem;
    }}

    .upload-panel {{
      background: rgba(255, 250, 242, 0.86);
      border: 1px solid var(--line);
      border-radius: 1.25rem;
      box-shadow: 0 20px 45px var(--shadow);
      padding: 1.25rem;
      backdrop-filter: blur(6px);
    }}

    form {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: center;
    }}

    input[type="file"] {{
      flex: 1 1 260px;
      padding: 0.7rem;
      border: 1px dashed var(--line);
      border-radius: 0.9rem;
      background: #fff;
    }}

    button {{
      border: 0;
      border-radius: 999px;
      padding: 0.8rem 1.25rem;
      background: var(--accent);
      color: #fff;
      font: inherit;
      cursor: pointer;
    }}

    button:hover {{
      background: var(--accent-dark);
    }}

    .status {{
      margin: 0 0 1rem;
      color: var(--accent-dark);
      font-weight: bold;
    }}

    .gallery {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin-top: 1.5rem;
    }}

    .card {{
      overflow: hidden;
      border-radius: 1.25rem;
      background: rgba(255, 255, 255, 0.74);
      border: 1px solid rgba(223, 210, 191, 0.95);
      box-shadow: 0 18px 30px var(--shadow);
    }}

    .card img {{
      display: block;
      width: 100%;
      aspect-ratio: 4 / 3;
      object-fit: cover;
      background: #eadfce;
    }}

    .meta {{
      padding: 0.85rem 1rem;
      font-size: 0.95rem;
      word-break: break-word;
    }}

    .empty-state {{
      padding: 2rem;
      border: 1px dashed var(--line);
      border-radius: 1.25rem;
      background: rgba(255, 255, 255, 0.58);
      text-align: center;
    }}

    @media (max-width: 640px) {{
      main {{
        width: min(100% - 1rem, 100%);
      }}

      .upload-panel {{
        padding: 1rem;
      }}

      form {{
        align-items: stretch;
      }}

      button {{
        width: 100%;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>MessageMesh Image Gallery</h1>
      <p>Uploads land in <code>{html.escape(str(IMAGE_DIRECTORY))}</code>, which can also be used as the shared folder for your FTP server.</p>
    </section>

    <section class="upload-panel">
      {message_markup}
      <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="image" accept=".png,.jpg,.jpeg,.gif,.webp" required>
        <button type="submit">Upload image</button>
      </form>
    </section>

    <section class="gallery">
      {gallery_markup}
    </section>
  </main>
</body>
</html>
"""


class GalleryRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/":
            query = parse_qs(parsed_url.query)
            message = query.get("message", [""])[0]
            self.send_html(render_page(message))
            return

        if parsed_url.path.startswith("/images/"):
            image_name = unquote(parsed_url.path[len("/images/"):])
            self.serve_image(image_name)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self):
        if self.path != "/upload":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        try:
            message = self.handle_upload()
        except ValueError as error:
            message = str(error)

        self.redirect_with_message(message)

    def handle_upload(self):
        ensure_image_directory()

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            raise ValueError("Upload failed: expected multipart form data.")

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        parsed_message = BytesParser(policy=default).parsebytes(
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
            + body
        )

        for part in parsed_message.iter_parts():
            if part.get_content_disposition() != "form-data":
                continue

            if part.get_param("name", header="content-disposition") != "image":
                continue

            filename = sanitize_filename(part.get_filename() or "")
            if not filename:
                raise ValueError("Upload failed: choose an image file first.")
            if not is_allowed_image(filename):
                raise ValueError("Upload failed: unsupported image type.")

            final_path = IMAGE_DIRECTORY / filename
            if final_path.exists():
                stem = final_path.stem
                suffix = final_path.suffix
                final_path = IMAGE_DIRECTORY / (
                    f"{stem}-{secrets.token_hex(4)}{suffix}"
                )

            temp_path = final_path.with_name(final_path.name + TEMP_UPLOAD_SUFFIX)
            payload = part.get_payload(decode=True) or b""

            with open(temp_path, "wb") as image_file:
                image_file.write(payload)

            os.replace(temp_path, final_path)
            return f"Uploaded {final_path.name}"

        raise ValueError("Upload failed: no image file was received.")

    def serve_image(self, image_name):
        normalized_path = Path(posixpath.normpath("/" + image_name).lstrip("/"))
        image_directory = IMAGE_DIRECTORY.resolve()
        image_path = (image_directory / normalized_path).resolve()

        if image_directory not in image_path.parents:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        if (
            not image_path.is_file()
            or not is_allowed_image(image_path.name)
            or image_path.name.endswith(TEMP_UPLOAD_SUFFIX)
        ):
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_type, _ = mimetypes.guess_type(image_path.name)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(image_path.stat().st_size))
        self.end_headers()

        with open(image_path, "rb") as image_file:
            self.wfile.write(image_file.read())

    def send_html(self, markup):
        payload = markup.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def redirect_with_message(self, message):
        location = f"/?message={quote(message)}"
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def log_message(self, format_string, *args):
        return


def run():
    ensure_image_directory()
    server = ThreadingHTTPServer((HOST, PORT), GalleryRequestHandler)
    print(f"Serving MessageMesh gallery at http://{HOST}:{PORT}")
    print(f"Shared image folder: {IMAGE_DIRECTORY}")
    server.serve_forever()


if __name__ == "__main__":
    run()
