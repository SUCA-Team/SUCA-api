import asyncpg

db = None

async def connect_db(app):
    global db
    db = await asyncpg.connect(
        user="ciferia",
        database="jmdict",
        host="127.0.0.1",
        port="5432"
    )
    app.state.db = db

async def close_db(app):
    await db.close()