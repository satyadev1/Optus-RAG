# Quick Start Guide - NEXUS-50206 Testing

## Prerequisites ✓

- [x] Nexus running on port 8081/8082
- [x] IQ Server/Insight running on port 8070
- [x] Docker Desktop running
- [x] All images deleted (clean slate)

---

## Step 1: Enable Firewall on dockerp (REQUIRED!)

### Via Web UI:

1. **Open**: http://localhost:8081
2. **Login**: admin / admin123
3. **Go to**: Settings (⚙️) → Repositories → **dockerp** → Edit
4. **Scroll to "Firewall" section**
5. **Configure**:
   ```
   ☑️ Analyze with Sonatype Repository Firewall
   IQ Application Name: docker-test
   ☑️ Audit and Quarantine
   ☐ Quarantine  ← UNCHECK (bug scenario!)
   ```
6. **Save**

### Verify IQ Connection:

- Settings → System → IQ Server
- Click "Verify connection"
- Should show: ✓ Connected

---

## Step 2: Create IQ Application

1. **Open**: http://localhost:8070
2. **Login** with IQ credentials
3. **Create Application**:
   - Name: `docker-test`
   - Application ID: `docker-test`
4. **Save**

---

## Step 3: Pull Vulnerable Images

### Option A: Use Script (Recommended)

```bash
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal"

# Interactive script - choose 1, 2, or 3
./pull-critical-images.sh
```

Select:
- **1** = 5 critical images (~800MB, 2 minutes)
- **2** = 10 high-risk images (~2GB, 5 minutes)
- **3** = 15 vulnerable images (~4GB, 10 minutes)

### Option B: Manual Pull (Quick Test)

```bash
# Pull 5 most critical images
docker pull host.docker.internal:8082/library/nginx:1.14.0
docker pull host.docker.internal:8082/library/ubuntu:14.04
docker pull host.docker.internal:8082/library/python:2.7
docker pull host.docker.internal:8082/library/httpd:2.4.38
docker pull host.docker.internal:8082/library/redis:4.0.0
```

---

## Step 4: Verify Images Work (Not Quarantined)

```bash
# Test that images are usable
docker run --rm host.docker.internal:8082/library/nginx:1.14.0 nginx -v
docker run --rm host.docker.internal:8082/library/ubuntu:14.04 cat /etc/os-release
docker run --rm host.docker.internal:8082/library/python:2.7 python --version
```

All should work! This proves quarantine is disabled.

---

## Step 5: Check IQ Server for the Bug

1. **Open IQ Server**: http://localhost:8070
2. **Navigate to**: Applications → `docker-test`
3. **Find**: dockerp repository or Components view
4. **Look at image status**:

   **THE BUG:**
   ```
   nginx:1.14.0    Status: "Quarantined"  ← WRONG!
   ubuntu:14.04    Status: "Quarantined"  ← WRONG!
   python:2.7      Status: "Quarantined"  ← WRONG!
   ```

   But you can still pull and run them!

---

## Expected vs Actual

### Configuration:
- ✓ Firewall: Enabled
- ✓ Audit and Quarantine: Enabled
- ✗ Quarantine: **Disabled**

### Expected Behavior:
- Images scanned ✓
- Vulnerabilities detected ✓
- Status shows: "Vulnerable" or "Policy Violation"
- Images are pullable ✓

### Actual Behavior (BUG):
- Images scanned ✓
- Vulnerabilities detected ✓
- Status shows: **"Quarantined"** ✗ (INCORRECT!)
- Images are pullable ✓

**The UI incorrectly displays "Quarantined" when quarantine is disabled.**

---

## Troubleshooting

### "I don't see Firewall option in Nexus"
- Firewall requires Nexus Pro license
- Check: Settings → System → Licensing

### "Images not showing in IQ Server"
1. Verify Firewall enabled on dockerp
2. Check IQ Server connection: Settings → IQ Server → Verify
3. Re-pull images AFTER enabling Firewall
4. Wait 1-2 minutes for scan to complete

### "Images fail to pull"
1. Verify Nexus is running: `curl http://localhost:8081`
2. Check port 8082: `curl http://localhost:8082/v2/`
3. Restart Docker Desktop if needed

### "Can't login to IQ Server"
- URL: http://localhost:8070
- Check your Insight service is running
- Verify credentials

---

## All Files Created

| File | Purpose |
|------|---------|
| `VULNERABLE-IMAGES-LIST.md` | Complete list of 100+ vulnerable images |
| `pull-critical-images.sh` | Interactive script to pull test images |
| `pull-vulnerable-images.sh` | Pull multiple images automatically |
| `QUICK-START.md` | This guide |
| `FIREWALL-SETUP-GUIDE.md` | Detailed Firewall configuration |
| `NEXUS-50206-TESTING-COMPLETE.md` | Full testing documentation |
| `enable-firewall-on-dockerp.sh` | Enable Firewall via API |
| `test-with-curl.sh` | Test registry without Docker |
| `fetch_nexus_issue.py` | Fetch JIRA issue details |
| `NEXUS_50206_details.json` | Issue details from JIRA |

---

## Quick Commands Reference

```bash
# Pull 5 critical images (interactive)
./pull-critical-images.sh

# Pull single image
docker pull host.docker.internal:8082/library/nginx:1.14.0

# List all pulled images
docker images | grep host.docker.internal:8082

# Test image works
docker run --rm host.docker.internal:8082/library/nginx:1.14.0 nginx -v

# Delete all images
docker rmi $(docker images --format '{{.Repository}}:{{.Tag}}' | grep host.docker.internal:8082)
```

---

## Summary Checklist

- [ ] Firewall enabled on dockerp repository
- [ ] IQ Application created (docker-test)
- [ ] Quarantine setting: **DISABLED** (bug scenario)
- [ ] Vulnerable images pulled
- [ ] Images verified to work (not actually quarantined)
- [ ] Checked IQ Server UI for incorrect "Quarantined" status
- [ ] Bug reproduced!

---

**Start with Step 1 (Enable Firewall) - this is the most important step!**

**Without Firewall enabled, nothing will show in IQ Server UI.**
