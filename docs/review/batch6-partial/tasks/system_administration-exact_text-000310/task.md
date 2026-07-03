You are an on-call SRE and `/var/log/app/` is filling up the disk.

**Your job (write the result to `/output/disk_report.txt`):**

1. Delete every file under `/var/log/app/` whose name ends in `.log` and that is **older than 7 days** (use the file modification time).
2. Count how many `.log` files **remain** after pruning.
3. Write `/output/disk_report.txt` with exactly this content (substitute real values):

```
pruned=<N>
remaining=<R>
owner=<USER>
```

- `<N>` — number of `.log` files deleted  
- `<R>` — number of `.log` files still present  
- `<USER>` — the owning user of the `/var/log/app/` directory  

No trailing spaces; exactly three lines each ending with `\n`.