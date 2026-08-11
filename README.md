# CROUS Nice Housing Watcher

Checks the CROUS "Trouver un logement" search for Nice every 30 seconds and
sends you a free push notification the moment a listing appears.

## Setup (5 minutes, no coding required)

### 1. Get a notification "topic" on ntfy.sh (free, no account)
ntfy.sh is a free push-notification service. Pick a **random, hard-to-guess**
name for your topic (anyone who knows the name can see your notifications),
e.g. `nice-crous-alert-x7q2f9`.

- On your phone: install the **ntfy** app (iOS App Store / Google Play),
  open it, and subscribe to your topic name.
- Or on desktop: just open `https://ntfy.sh/your-topic-name` in a browser tab
  and leave it open (or use the app for real push notifications).

### 2. Create a GitHub repository
1. Go to https://github.com and create a free account if you don't have one.
2. Click "New repository". Make it **Public** (public repos get unlimited
   free GitHub Actions minutes — private repos only get ~33 hours/month,
   not enough for 24/7 monitoring).
3. Upload these three files/folders into the repo, keeping the folder
   structure:
   - `monitor.py`
   - `requirements.txt`
   - `.github/workflows/watch.yml`

   (Easiest way: on the repo page, click "Add file" → "Upload files", drag
   in `monitor.py` and `requirements.txt`, commit. Then create the folder
   path `.github/workflows/watch.yml` the same way — GitHub lets you type a
   path with slashes when naming a new file and it creates the folders.)

### 3. Add your ntfy topic as a secret
In your repo: **Settings → Secrets and variables → Actions → New repository
secret**
- Name: `NTFY_TOPIC`
- Value: the topic name you picked in step 1 (e.g. `nice-crous-alert-x7q2f9`)

### 4. (Optional) Override the search URL
If you ever want to change the search (different city, different bounds),
go to **Settings → Secrets and variables → Actions → Variables tab → New
repository variable**, name it `CROUS_URL`, and paste the search URL. If you
skip this, it defaults to the Nice search you gave me.

### 5. Start it
Go to the **Actions** tab in your repo → click "Crous Watcher" on the left →
click **Run workflow** (green button) to start it immediately for testing.
After that, it restarts itself automatically every 6 hours forever, checking
every 30 seconds the whole time.

## How it avoids spamming you
It remembers which listings it has already alerted you about (saved in
`seen_listings.json`, committed back to the repo). You'll only get a
notification when a *new* listing appears, not on every single check.

## Cost
$0. GitHub Actions is free for public repos, ntfy.sh is free.

## Notes / limitations
- Checks happen every 30 seconds *while a run is active*. GitHub Actions
  jobs can't run forever, so the workflow restarts every 6 hours — there's
  a gap of at most a minute or two between runs while GitHub spins up the
  next one.
- The bot pushes a commit every ~6 hours, which also keeps GitHub from
  disabling the scheduled workflow for inactivity (it auto-disables
  schedules after 60 days with zero repo activity — this won't happen here).
- If CROUS redesigns their site's HTML, the listing-detection selector
  (`fr-card`) might need updating.
