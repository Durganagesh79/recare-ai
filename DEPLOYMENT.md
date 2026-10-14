# ReCare AI — Production Deployment Guide

**Predict Earlier. Prioritize Smarter. Prevent Avoidable Readmissions.**

This guide covers deploying the ReCare AI full-stack platform to **Render** (FastAPI ML Backend) and **Vercel** (React 19 / Vite Frontend) using GitHub.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Vercel (Static / SPA)     |
                      |   React 19 + Vite Dashboard |
                      +--------------+--------------+
                                     |
                         HTTPS API Requests (CORS)
                                     |
                                     v
                      +-----------------------------+
                      |    Render (Web Service)     |
                      |   FastAPI + Uvicorn + ML    |
                      |   SQLite / 5k Synthetic DB  |
                      +-----------------------------+
```

---

## 1. Backend Deployment on Render

### Service Settings
* **Service Type**: Web Service
* **Language / Runtime**: `Python 3`
* **Repository**: `https://github.com/Durganagesh79/recare-ai`
* **Branch**: `main`
* **Root Directory**: *(Leave empty / project root)*
* **Build Command**:
  ```bash
  pip install -r backend/requirements.txt
  ```
* **Start Command**:
  ```bash
  uvicorn backend.main:app --host 0.0.0.0 --port $PORT
  ```
* **Plan**: Free ($0 / month)

### Environment Variables
| Key | Value | Notes |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` | Ensures exact Python runtime |
| `ENVIRONMENT` | `production` | Enables production mode |

### Verified Endpoints
Once deployed, verify:
* Health Check: `https://<YOUR-RENDER-BACKEND>.onrender.com/health`
* Swagger Docs: `https://<YOUR-RENDER-BACKEND>.onrender.com/docs`
* Dashboard Summary: `https://<YOUR-RENDER-BACKEND>.onrender.com/api/dashboard/summary`
* Monday Call List: `https://<YOUR-RENDER-BACKEND>.onrender.com/api/call-list/current`

---

## 2. Frontend Deployment on Vercel

### Project Settings
* **Framework Preset**: `Vite`
* **Root Directory**: `frontend`
* **Build Command**: `npm run build`
* **Output Directory**: `dist`
* **Install Command**: `npm install`

### Environment Variables
| Key | Value |
| :--- | :--- |
| `VITE_API_BASE_URL` | `https://<YOUR-RENDER-BACKEND>.onrender.com` |
| `VITE_API_URL` | `https://<YOUR-RENDER-BACKEND>.onrender.com` |

### SPA Routing Fallback
Handled by `frontend/vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

---

## 3. Production Verification Checklist

1. [x] **Disclaimer Banner**: Visible at top indicating synthetic clinical decision-support demonstration.
2. [x] **Overview Dashboard**: Displays 5,000 synthetic discharges, 701 high-risk patients, and Monday Morning Call List (50/50 cap).
3. [x] **Model Evaluation**: Calibration curves (ECE: 1.08%), AUC-PR (0.3608), Brier Score (0.1348).
4. [x] **Monday Morning Call List**: 50 unique patient capacity roster, risk-benefit optimization, and editable notes.
5. [x] **CORS Policy**: Configured to dynamically authorize all Vercel domains (`https://*.vercel.app`) with credentials.
