import os
import random
import asyncio
import httpx
import asyncpg
import aiomysql
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# --- FastAPI App Initialization ---
app = FastAPI()

# --- Application Configuration ---
APP_PORT = int(os.getenv("APP_PORT", 8000))
NUM_PRODUCTS_TO_SEED = int(os.getenv("NUM_PRODUCTS_TO_SEED", 50000))

# --- Database Configurations ---
PG_HOST = os.getenv("PG_HOST", "postgres-db")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_NAME = os.getenv("PG_NAME", "ec2_db_quick_test")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASS = os.getenv("PG_PASS", "postgres")

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql-db")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_NAME = os.getenv("MYSQL_NAME", "ec2_db_quick_test")
MYSQL_USER = os.getenv("MYSQL_USER", "mysql_user")
MYSQL_PASS = os.getenv("MYSQL_PASS", "mysql_password")

# --- Database Initialization & Seeding with Retry Logic ---

async def init_postgres_db():
    """Initializes and seeds PostgreSQL, retrying until the DB is ready."""
    retries = 10
    delay = 6  # 6 seconds delay
    for i in range(retries):
        conn = None
        try:
            print(f"Attempting to connect to PostgreSQL (attempt {i+1}/{retries})...")
            conn = await asyncpg.connect(user=PG_USER, password=PG_PASS, database=PG_NAME, host=PG_HOST, port=PG_PORT)
            print("✅ PostgreSQL connected. Initializing schema...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS web_visits (id SERIAL PRIMARY KEY, visit_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    category VARCHAR(50),
                    price NUMERIC(10, 2)
                );
            """)
            count = await conn.fetchval('SELECT COUNT(*) FROM products')
            if count == 0:
                print(f"Seeding PostgreSQL 'products' table with {NUM_PRODUCTS_TO_SEED} rows...")
                categories = ['electronics', 'books', 'home', 'toys', 'sports']
                products_data = [(f'Product {i}', random.choice(categories), random.uniform(10.0, 500.0)) for i in range(NUM_PRODUCTS_TO_SEED)]
                await conn.copy_records_to_table('products', records=products_data, columns=['name', 'category', 'price'])
                print("✅ PostgreSQL seeding complete.")
            print("✅ PostgreSQL initialization complete.")
            return
        except Exception as e:
            print(f"🔴 PostgreSQL initialization failed on attempt {i+1}: {e}")
            if i < retries - 1:
                await asyncio.sleep(delay)
            else:
                print("🔴 All PostgreSQL initialization attempts failed.")
        finally:
            if conn:
                await conn.close()

async def init_mysql_db():
    """Initializes and seeds MySQL, retrying until the DB is ready."""
    retries = 10
    delay = 6
    for i in range(retries):
        conn = None
        try:
            print(f"Attempting to connect to MySQL (attempt {i+1}/{retries})...")
            conn = await aiomysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, db=MYSQL_NAME, autocommit=True)
            print("✅ MySQL connected. Initializing schema...")
            async with conn.cursor() as cur:
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS web_visits_mysql (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100),
                        category VARCHAR(50),
                        price DECIMAL(10, 2)
                    );
                """)
                await cur.execute('SELECT COUNT(*) FROM products')
                (count,) = await cur.fetchone()
                if count == 0:
                    print(f"Seeding MySQL 'products' table with {NUM_PRODUCTS_TO_SEED} rows...")
                    categories = ['electronics', 'books', 'home', 'toys', 'sports']
                    products_data = [(f'Product {i}', random.choice(categories), round(random.uniform(10.0, 500.0), 2)) for i in range(NUM_PRODUCTS_TO_SEED)]
                    await cur.executemany("INSERT INTO products (name, category, price) VALUES (%s, %s, %s)", products_data)
                    print("✅ MySQL seeding complete.")
            print("✅ MySQL initialization complete.")
            return
        except Exception as e:
            print(f"🔴 MySQL initialization failed on attempt {i+1}: {e}")
            if i < retries - 1:
                await asyncio.sleep(delay)
            else:
                print("🔴 All MySQL initialization attempts failed.")
        finally:
            if conn:
                conn.close()


@app.on_event("startup")
async def startup_event():
    # Run initializations concurrently
    await asyncio.gather(
        init_postgres_db(),
        init_mysql_db()
    )

# --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>O11y Test App</title>
<style>
body{font-family:sans-serif;background-color:#2b2d42;color:#edf2f4;margin:40px}h1,h2{color:#8d99ae}a{color:#93c5fd;text-decoration:none;font-weight:700}a:hover{text-decoration:underline}.container{max-width:800px;margin:auto;background-color:#43455f;padding:20px;border-radius:8px}
</style></head><body><div class="container"><h1>🚀 O11y Test Application</h1>
<p>Use these endpoints to generate complex database telemetry data.</p>
<h2>Database Scenarios:</h2><ul>
<li><a href="/postgresql_interaction" target="_blank">/postgresql_interaction</a> - Runs slow, waiting, and blocking queries against PostgreSQL.</li>
<li><a href="/mysql_interaction" target="_blank">/mysql_interaction</a> - Runs slow, waiting, and blocking queries against MySQL.</li>
</ul><h2>Other Endpoints:</h2><ul>
<li><a href="/cpu_intensive" target="_blank">/cpu_intensive</a> - Simulates high CPU load.</li>
<li><a href="/error" target="_blank">/error</a> - Triggers a 500 error.</li>
</ul><h2>Actions:</h2><p><a href="/generate_load">/generate_load</a> - Click to start a 60-second load generation task.</p>
</div></body></html>
"""

# --- Scenario Implementations ---

# PostgreSQL Scenarios
async def _pg_normal_query(pool):
    async with pool.acquire() as conn:
        return await conn.fetchval("INSERT INTO web_visits DEFAULT VALUES RETURNING id;")
async def _pg_slow_query(pool):
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM products WHERE category = 'electronics';")
async def _pg_wait_query(pool):
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT pg_sleep(0.5);")
async def _pg_blocking_scenario(pool):
    product_id_to_lock = random.randint(1, 100)
    async def blocker(conn):
        async with conn.transaction():
            await conn.execute("SELECT * FROM products WHERE id = $1 FOR UPDATE;", product_id_to_lock)
            await asyncio.sleep(1)
    async def blocked(conn):
        return await conn.fetchval("SELECT price FROM products WHERE id = $1;", product_id_to_lock)
    async with pool.acquire() as conn1, pool.acquire() as conn2:
        _, result = await asyncio.gather(blocker(conn1), blocked(conn2))
        return result

# MySQL Scenarios
async def _mysql_normal_query(pool):
    async with pool.acquire() as conn, conn.cursor() as cur:
        await cur.execute("INSERT INTO web_visits_mysql () VALUES ();")
        return cur.lastrowid
async def _mysql_slow_query(pool):
    async with pool.acquire() as conn, conn.cursor() as cur:
        await cur.execute("SELECT COUNT(*) FROM products WHERE category = 'electronics';")
        (count,) = await cur.fetchone()
        return count
async def _mysql_wait_query(pool):
    async with pool.acquire() as conn, conn.cursor() as cur:
        await cur.execute("SELECT SLEEP(0.5);")
        return "Slept for 0.5s"
async def _mysql_blocking_scenario(pool):
    product_id_to_lock = random.randint(1, 100)
    async def blocker(conn):
        async with conn.cursor() as cur:
            await conn.begin()
            await cur.execute("SELECT * FROM products WHERE id = %s FOR UPDATE;", (product_id_to_lock,))
            await asyncio.sleep(1)
            await conn.commit()
    async def blocked(conn):
        async with conn.cursor() as cur:
            await cur.execute("SELECT price FROM products WHERE id = %s;", (product_id_to_lock,))
            (price,) = await cur.fetchone()
            return price
    async with pool.acquire() as conn1, pool.acquire() as conn2:
        _, result = await asyncio.gather(blocker(conn1), blocked(conn2))
        return result

# --- FastAPI Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def home(): return HTML_TEMPLATE

@app.get("/postgresql_interaction")
async def postgresql_interaction():
    pool = await asyncpg.create_pool(user=PG_USER, password=PG_PASS, database=PG_NAME, host=PG_HOST, port=PG_PORT, min_size=5)
    try:
        results = await asyncio.gather(
            _pg_normal_query(pool),
            _pg_slow_query(pool),
            _pg_wait_query(pool),
            _pg_blocking_scenario(pool)
        )
        return {"normal_insert_id": results[0], "slow_query_count": results[1], "wait_result": "Slept for 0.5s", "blocking_read_price": float(results[3])}
    finally:
        await pool.close()

@app.get("/mysql_interaction")
async def mysql_interaction():
    pool = await aiomysql.create_pool(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, db=MYSQL_NAME, minsize=5)
    try:
        results = await asyncio.gather(
            _mysql_normal_query(pool),
            _mysql_slow_query(pool),
            _mysql_wait_query(pool),
            _mysql_blocking_scenario(pool)
        )
        return {"normal_insert_id": results[0], "slow_query_count": results[1], "wait_result": results[2], "blocking_read_price": float(results[3])}
    finally:
        pool.close()

@app.get("/cpu_intensive")
async def cpu_intensive_task():
    result = sum(i*i for i in range(2_000_000))
    return {"message": "CPU intensive task complete", "result": result}

@app.get("/error")
async def trigger_error():
    raise ValueError("This is an intentional test error!")

async def run_load_generation():
    print("🚦 Starting complex load generation for 60 seconds...")
    endpoints = [
        f"http://localhost:{APP_PORT}/postgresql_interaction",
        f"http://localhost:{APP_PORT}/mysql_interaction",
        f"http://localhost:{APP_PORT}/cpu_intensive",
        f"http://localhost:{APP_PORT}/error"
    ]
    async with httpx.AsyncClient() as client:
        start_time = asyncio.time()
        while asyncio.time() - start_time < 60:
            try:
                await client.get(random.choice(endpoints), timeout=20)
            except httpx.RequestError as e:
                print(f"Request failed: {e}")
            await asyncio.sleep(random.uniform(0.2, 0.8))
    print("🏁 Load generation finished.")

@app.get("/generate_load")
async def generate_load():
    asyncio.create_task(run_load_generation())
    return {"message": "🚀 Complex load generation started in the background for 60 seconds!"}
