1. Create `/srv/data/hello.txt` containing exactly `hello from the sandbox`
   (with a trailing newline).
2. Start an HTTP server in the background serving the `/srv/data` directory on
   port 8000. The server must still be running and answering requests after
   your command returns (hint: run it detached, e.g. with `nohup ... &`).
