You are a sysadmin reclaiming disk on a full server.

The directory `/srv/logs` contains a mix of log files. You need to audit and reorganize them.

**Your tasks:**

1. Write a Python script (you may save it anywhere) that:
   - Counts the total number of **lines**, **words**, and **bytes** across all files matching the glob `/srv/logs/*.log` (sorted by filename for determinism).
   - Writes a report to `/output/audit.txt` in exactly this format (with a trailing newline):
     ```
     files=<N>
     lines=<L>
     words=<W>
     bytes=<B>
     ```
   - Creates a tar archive at `/output/archive.tar` containing all those `.log` files (paths inside the archive should be just the filenames, e.g. `app.log`, not full paths).
   - Sets the permissions of `/output/archive.tar` to **640** (owner read+write, group read, others none).
   - Sets the owner of `/output/archive.tar` to **root:root** (it likely already is, but ensure it explicitly).

2. Run your script to produce `/output/audit.txt` and `/output/archive.tar`.

The counts must reflect only the `.log` files in `/srv/logs/` (no subdirectories, no other extensions).