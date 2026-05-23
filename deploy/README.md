# deploy/

Templates for running Dog of Bitcoin on the AWS box.

| File | Where it goes |
|---|---|
| `dob-backend.service` | `/etc/systemd/system/dob-backend.service` |
| `nginx.conf` | `/etc/nginx/sites-available/dog-of-bitcoin.conf`, then symlink to `sites-enabled/` |

After copying:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now dob-backend
sudo nginx -t && sudo systemctl reload nginx
```

See `docs/RUNNING.md` for the full setup.
