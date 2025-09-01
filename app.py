import os
import asyncio
import random
import httpx
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
import asyncpg
import logging

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI()

# --- Database Configuration ---
# Fetch DB config from environment variables.
# The default DB_HOST is now 'db' to match the docker-compose service name.
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "ec2_db_quick_test")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DATABASE_URL = f"postgres://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# --- Database Pool ---
# A connection pool is created at startup and managed by FastAPI
db_pool = None

@app.on_event("startup")
async def startup_event():
    """
    On application startup, connect to the database and create the necessary table.
    Includes a retry mechanism to handle the database container starting up slower than the app.
    """
    global db_pool
    attempts = 5
    while attempts > 0:
        try:
            db_pool = await asyncpg.create_pool(DATABASE_URL)
            async with db_pool.acquire() as connection:
                logger.info("✅ Database connection established.")
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS web_visits (
                        id SERIAL PRIMARY KEY,
                        visit_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("✅ Database initialized successfully.")
                return # Exit the loop on success
        except Exception as e:
            attempts -= 1
            logger.error(f"🔴 Could not connect to database: {e}. Retrying in 5 seconds... ({attempts} attempts left)")
            await asyncio.sleep(5)
    
    # If all attempts fail
    db_pool = None
    logger.critical("🔴 All attempts to connect to the database failed. The application will run without database connectivity.")


@app.on_event("shutdown")
async def shutdown_event():
    """
    On application shutdown, close the database connection pool.
    """
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed.")

# --- HTML Template for the Homepage ---
HTML_TEMPLATE_STRING = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>EC2 DB Quick Test App</title>
    <!-- ⬇️ PASTE YOUR VENDOR'S RUM SNIPPET HERE ⬇️ -->

    <!-- ⬆️ PASTE YOUR VENDOR'S RUM SNIPPET HERE ⬆️ -->
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #2b2d42; color: #edf2f4; margin: 40px; line-height: 1.6; }
        h1, h2 { color: #8d99ae; border-bottom: 1px solid #4a4c6a; padding-bottom: 10px; }
        a { color: #ef233c; text-decoration: none; font-weight: bold; }
        a:hover { text-decoration: underline; }
        .container { max-width: 800px; margin: auto; background-color: #43455f; padding: 20px 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        ul { list-style: none; padding-left: 0; }
        li { background-color: #2b2d42; margin-bottom: 10px; padding: 10px 15px; border-radius: 5px; }
        code { background-color: #1a1b26; padding: 2px 5px; border-radius: 3px; font-family: "SF Mono", "Fira Code", "Consolas", monospace; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 EC2 DB Quick Test App</h1>
        <p>Use these endpoints to generate telemetry data for your observability platform.</p>
        <h2>API Endpoints:</h2>
        <ul>
            <li><a href="/" target="_blank"><code>/</code></a> - Renders this page for RUM & basic APM trace.</li>
            <li><a href="/db_interaction" target="_blank"><code>/db_interaction</code></a> - Inserts a record and reads the last 10 from PostgreSQL.</li>
            <li><a href="/cpu_intensive" target="_blank"><code>/cpu_intensive</code></a> - Simulates a high CPU workload.</li>
            <li><a href="/error" target="_blank"><code>/error</code></a> - Triggers a 500 error for error tracking.</li>
        </ul>
        <h2>Actions:</h2>
        <p><a href="/generate_load">/generate_load</a> - Click to start a 60-second load generation task in the background.</p>
    </div>
</body>
</html>
"""

# --- FastAPI Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def home():
    """Homepage endpoint. This is where you'll test RUM."""
    return HTMLResponse(content=HTML_TEMPLATE_STRING)

@app.get("/db_interaction")
async def db_interaction():
    """
    Connects to the database via the pool, inserts a new visit,
    and retrieves the last 10 visits asynchronously.
    """
    if not db_pool:
        return {"error": "Database connection pool not available"}, 503

    async with db_pool.acquire() as connection:
        # Write and Read operations
        await connection.execute("INSERT INTO web_visits DEFAULT VALUES;")
        records = await connection.fetch("SELECT id, visit_time FROM web_visits ORDER BY visit_time DESC LIMIT 10;")
    
    return [{"id": r['id'], "time": r['visit_time'].isoformat()} for r in records]


@app.get("/cpu_intensive")
async def cpu_intensive_task():
    """
    Simulates a CPU-bound task.
    This runs in a separate thread pool to avoid blocking the async event loop.
    """
    def sync_cpu_task():
        # A simple, inefficient calculation to consume CPU
        return sum(i*i for i in range(2_000_000))

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, sync_cpu_task)
    
    return {
        "message": "CPU intensive task complete",
        "result": result
    }

@app.get("/error")
async def trigger_error():
    """Raises an exception to test error tracking."""
    raise ValueError("This is an intentional test error from the FastAPI app!")

# --- Load Generation ---

async def run_load_generation_task():
    """The actual load generation logic."""
    logger.info("🚦 Starting load generation for 60 seconds...")
    # The app is running inside the docker network, so it can refer to itself as 'web'
    base_url = "http://web:8000"
    endpoints = [
        f"{base_url}/",
        f"{base_url}/db_interaction",
        f"{base_url}/cpu_intensive",
        f"{base_url}/error"
    ]
    start_time = asyncio.get_event_loop().time()
    
    async with httpx.AsyncClient() as client:
        while asyncio.get_event_loop().time() - start_time < 60:
            try:
                endpoint = random.choice(endpoints)
                await client.get(endpoint, timeout=5.0)
            except httpx.RequestError as e:
                logger.warning(f"Request failed (as expected for error endpoint or timeout): {e}")
            await asyncio.sleep(random.uniform(0.1, 0.4))
            
    logger.info("🏁 Load generation finished.")

@app.get("/generate_load")
async def generate_load(background_tasks: BackgroundTasks):
    """
    Starts the load generation as a background task.
    Responds immediately to the user.
    """
    background_tasks.add_task(run_load_generation_task)
    return {"message": "🚀 Load generation started in the background for 60 seconds!"}
