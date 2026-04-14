# MessageMesh

MessageMesh is split into two deployment targets:

- `server/`: runs on the central Windows or Linux machine that hosts the FTP server and the web gallery.
- `node/`: runs on each Raspberry Pi display node and pulls images from the FTP server.

## Repo Layout

- `server/web_gallery.py`: simple web gallery and uploader for the shared image folder.
- `server/shared_images/`: shared image folder that both the FTP server and web gallery should point to.
- `node/message_mesh_1.3.0.py`: Raspberry Pi slideshow client.
- `docs/`: deployment PDFs and changelog.

## Server Machine

Use the `server/shared_images` folder as the shared directory for your FTP server.

Run the gallery locally with:

```powershell
py -3 server\web_gallery.py
```

Then open `http://127.0.0.1:8000`.

## Raspberry Pi Nodes

Deploy and run:

```bash
python3 message_mesh_1.3.0.py
```

The node script lives at `node/message_mesh_1.3.0.py` in this repo and should be copied to each Pi as part of node deployment.
