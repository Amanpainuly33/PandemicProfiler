# PandemicProfiler

A web application for COVID-19 data analysis and prediction, featuring a React frontend and a Flask backend with machine learning models.

---

## Project Structure

```
PandemicProfiler/
├── backend/      # Flask API (Python)
├── frontend/     # React app (TypeScript, Vite)
├── model/        # ML models and data
├── pyproject.toml
├── uv.lock
└── .python-version
```



---

## Backend Setup (Flask + uv)

1. **Install uv (if not already):**
   ```sh
   pip install uv
   ```

2. **Sync dependencies:**
   ```sh
   uv sync
   ```

3. **Run the backend:**
   ```sh
   cd backend
   uv run python app.py
   ```
   or
   ```sh
   source .venv/bin/activate
   cd backend
   python app.py
   ```
   The backend will start on `http://localhost:5000`.

   Note: when adding any dependencies:
   ```sh
   uv add <dependency name>
   ```
---

## Frontend Setup (React + Vite)

1. **Install dependencies:**
   ```sh
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```sh
   npm run dev
   ```
   The frontend will start on `http://localhost:5173` (or another port if in use).

---

## Environment Variables

- **Frontend:**  
  If deploying, set `VITE_API_URL` to your backend URL (e.g., on Vercel).
- **Backend:**  
  For production, set allowed CORS origins in `app.py` or via environment variable.

---

## Production Deployment

### Frontend (Vercel)
- Set project root to `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Install command: `npm install`
- Set `VITE_API_URL` to your backend’s public URL

### Backend (Render)
- Set project root to `backend`
- Start command: `uvicorn app:app` or `python app.py` (for Flask, use `gunicorn app:app` if needed)
- Python version: 3.9
- Add any required environment variables

---

## Notes

- The backend uses data and models from the `model/` directory.
- `.DS_Store` and other system files should be ignored via `.gitignore`.
- For local development, ensure both frontend and backend are running.

---

## Troubleshooting

- If you see CORS errors, check the CORS configuration in `backend/app.py`.
- If you see Python import errors, ensure you ran `uv sync` and are using the correct Python version.

---

Let me know if you want this written to a `README.md` file or need further customization!
