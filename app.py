import os
import random
import asyncio
import httpx
import asyncpg
import aiomysql
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

# --- FastAPI App Initialization ---
app = FastAPI()

# --- Application Configuration ---
APP_PORT = int(os.getenv("APP_PORT", 8000))

# --- PostgreSQL Configuration ---
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_NAME = os.getenv("PG_NAME", "ec2_db_quick_test")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASS = os.getenv("PG_PASS", "postgres")

# --- MySQL Configuration ---
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_NAME = os.getenv("MYSQL_NAME", "ec2_db_quick_test")
MYSQL_USER = os.getenv("MYSQL_USER", "mysql_user")
MYSQL_PASS = os.getenv("MYSQL_PASS", "mysql_password")


# --- Database Initialization ---
async def init_postgres_db():
    """Initializes PostgreSQL by creating the necessary table."""
    try:
        conn = await asyncpg.connect(user=PG_USER, password=PG_PASS, database=PG_NAME, host=PG_HOST, port=PG_PORT)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS web_visits_postgres (
                id SERIAL PRIMARY KEY,
                visit_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await conn.close()
        print("✅ PostgreSQL database initialized successfully.")
    except Exception as e:
        print(f"🔴 Could not initialize PostgreSQL database: {e}")

async def init_mysql_db():
    """Initializes MySQL by creating the necessary table."""
    try:
        conn = await aiomysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, db=MYSQL_NAME)
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS web_visits_mysql (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.close()
        print("✅ MySQL database initialized successfully.")
    except Exception as e:
        print(f"🔴 Could not initialize MySQL database: {e}")

@app.on_event("startup")
async def startup_event():
    """On application startup, initialize both databases."""
    await init_postgres_db()
    await init_mysql_db()

# --- HTML Template for the Homepage ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>O11y Test App</title>
    <!-- ⬇️ PASTE YOUR RUM SNIPPET HERE ⬇️ -->

    <!-- ⬆️ PASTE YOUR RUM SNIPPET HERE ⬆️ -->
    <style>
        body { font-family: sans-serif; background-color: #2b2d42; color: #edf2f4; margin: 40px; }
        h1, h2 { color: #8d99ae; }
        a { color: #d90429; text-decoration: none; font-weight: bold; }
        a:hover { text-decoration: underline; }
        .container { max-width: 800px; margin: auto; background-color: #43455f; padding: 20px; border-radius: 8px; }
        pre { background-color: #2b2d42; padding: 15px; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 O11y Test Application</h1>
        <p>Use these endpoints to generate telemetry data.</p>
        <h2>Endpoints:</h2>
        <ul>
            <li><a href="/" target="_blank">/ (Home)</a> - RUM & basic APM trace.</li>
            <li><a href="/postgres_interaction" target="_blank">/postgres_interaction</a> - Inserts and selects from PostgreSQL.</li>
            <li><a href="/mysql_interaction" target="_blank">/mysql_interaction</a> - Inserts and selects from MySQL.</li>
            <li><a href="/cpu_intensive" target="_blank">/cpu_intensive</a> - Simulates high CPU load.</li>
            <li><a href="/error" target="_blank">/error</a> - Triggers a 500 error to test error tracking.</li>
        </ul>
        <h2>Actions:</h2>
        <p><a href="/generate_load">/generate_load</a> - Click here to start a 60-second load generation task in the background.</p>
    </div>
</body>
</html>
"""

# --- FastAPI Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def home():
    """Homepage endpoint. This is where you'll test RUM."""
    return HTML_TEMPLATE

@app.get("/postgres_interaction")
async def postgres_interaction():
    """Connects to PostgreSQL, inserts a visit, and retrieves the last 10."""
    try:
        conn = await asyncpg.connect(user=PG_USER, password=PG_PASS, database=PG_NAME, host=PG_HOST, port=PG_PORT)
        await conn.execute("INSERT INTO web_visits_postgres DEFAULT VALUES;")
        visits = await conn.fetch("SELECT id, visit_time FROM web_visits_postgres ORDER BY visit_time DESC LIMIT 10;")
        await conn.close()
        return [{"id": v['id'], "time": v['visit_time'].isoformat()} for v in visits]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PostgreSQL connection failed: {e}")

@app.get("/mysql_interaction")
async def mysql_interaction():
    """Connects to MySQL, inserts a visit, and retrieves the last 10."""
    try:
        conn = await aiomysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, db=MYSQL_NAME)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("INSERT INTO web_visits_mysql () VALUES ();")
            await cur.execute("SELECT id, visit_time FROM web_visits_mysql ORDER BY visit_time DESC LIMIT 10;")
            visits = await cur.fetchall()
        conn.close()
        return [{"id": v['id'], "time": v['visit_time'].isoformat()} for v in visits]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL connection failed: {e}")


@app.get("/cpu_intensive")
async def cpu_intensive_task():
    """Simulates a CPU-bound task."""
    result = sum(i*i for i in range(2_000_000))
    return {"message": "CPU intensive task complete", "result": result}

@app.get("/error")
async def trigger_error():
    """Raises an exception to test error tracking."""
    raise ValueError("This is an intentional test error!")

# --- Load Generation ---
async def run_load_generation():
    """Target function for the background task to generate load."""
    print("🚦 Starting load generation for 60 seconds...")
    endpoints = [
        f"http://localhost:{APP_PORT}/",
        f"http://localhost:{APP_PORT}/postgres_interaction",
        f"http://localhost:{APP_PORT}/mysql_interaction",
        f"http://localhost:{APP_PORT}/cpu_intensive",
        f"http://localhost:{APP_PORT}/error"
    ]
    async with httpx.AsyncClient() as client:
        start_time = asyncio.time()
        while asyncio.time() - start_time < 60:
            try:
                endpoint = random.choice(endpoints)
                await client.get(endpoint, timeout=5)
            except httpx.RequestError as e:
                print(f"Request failed (as expected for error endpoint or timeout): {e}")
            await asyncio.sleep(random.uniform(0.1, 0.5))
    print("🏁 Load generation finished.")

@app.get("/generate_load")
async def generate_load():
    """Starts the load generation as a background task."""
    asyncio.create_task(run_load_generation())
    return {"message": "🚀 Load generation started in the background for 60 seconds!"}
