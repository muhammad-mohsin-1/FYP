# Deploying the FYP on Railway (live link)

Railway runs the whole project (backend + AI model + frontend) from one
Docker container. The `Dockerfile` builds everything automatically.

## Steps (2 minutes, on your phone or laptop)

1. Go to **railway.app** → **Login** → **Login with GitHub** (use your
   `muhammad-mohsin-1` account).
2. Click **+ New** → **GitHub Repo** → select **`FYP`**.
   (If the repo is not listed: Configure GitHub App → give access to FYP.)
3. Railway detects the `Dockerfile` and starts building (~5–10 minutes —
   it installs Python, torch CPU, and Node, then downloads the trained model).
4. When deploy shows **Active**: open the service → **Settings** →
   **Networking** → **Generate Domain**. That is your **live project link**.
5. Open the link → login page appears. Login: `admin` / `admin123`
   (change the password after first login).

## Notes

- The trained AI model (`best.pt`) downloads automatically during the build
  from Google Drive — no manual step needed.
- Database is SQLite inside the container: it resets if you redeploy.
  Fine for the demo/viva; the proposal's MySQL step is in the setup guide.
- Free tier: the app sleeps when idle and wakes on first visit (~30–60s).
- If the build fails, open the **Deploy Logs** in Railway and send me the
  error — I will fix the Dockerfile.
