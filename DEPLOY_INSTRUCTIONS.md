# Debug Deployment Instructions

## Current Configuration

Your app is now configured for debug deployment:
- **App name:** `pharmacy-finder-debug`
- **Debug URL:** `https://pharmacy-finder-debug.fly.dev`
- **Environment:** `debug`
- **New debug endpoints added to main.py**

## Manual Deployment Steps

Run these commands in order:

### 1. Create Debug App (if doesn't exist)
```bash
fly apps create pharmacy-finder-debug --org personal
```

### 2. Create Volume for Debug App
```bash
fly volumes create pharmacy_data --region mia --size 1 --app pharmacy-finder-debug
```

### 3. Deploy Debug Application
```bash
fly deploy --app pharmacy-finder-debug
```

### 4. Test Debug Endpoints

Once deployed, test these URLs:

**Volume Diagnostics:**
```bash
curl "https://pharmacy-finder-debug.fly.dev/admin/volume-debug"
```

**Force Database Update:**
```bash
curl -X POST "https://pharmacy-finder-debug.fly.dev/admin/force-volume-update"
```

**Database Status:**
```bash
curl "https://pharmacy-finder-debug.fly.dev/admin/database-status"
```

**Basic Stats:**
```bash
curl "https://pharmacy-finder-debug.fly.dev/api/stats"
```

## What to Look For

### Volume Debug Response Should Show:
- `volume_exists: true`
- `volume_writable: true` 
- `can_write_files: true`
- `db_connection: "success"`
- `pharmacy_count: > 0` (after successful update)

### Common Issues to Check:
1. **Volume not mounted:** `volume_exists: false`
2. **Permission issues:** `volume_writable: false` or `can_write_files: false`
3. **Database access:** `db_connection` has errors
4. **Import failure:** `pharmacy_count: 0` after force update

## Cleanup After Testing

To remove the debug app when done:
```bash
fly apps destroy pharmacy-finder-debug
```

## Restore Production Config

When ready to apply fixes to production, change fly.toml back:
```toml
app = "pharmacy-finder-chile"
ENV = "production"
APP_NAME = "Farmacias Chile"
```

Then deploy to production:
```bash
fly deploy --app pharmacy-finder-chile
```