# app/db_logging.py
import logging, os, time
from sqlalchemy import event
from sqlalchemy.engine import Engine

SLOW_MS = float(os.getenv("SQL_SLOW_MS", "300"))
slow = logging.getLogger("sql.slow")
pool = logging.getLogger("sqlalchemy.pool")

def install(engine: Engine):
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start = conn.info["query_start_time"].pop(-1)
        dur_ms = (time.perf_counter() - start) * 1000.0
        if dur_ms >= SLOW_MS:
            slow.warning(
                "slow_query",
                extra={"duration_ms": round(dur_ms, 2),
                       "statement": statement,
                       "parameters": str(parameters)[:500]},
            )

    @event.listens_for(engine, "invalidate")
    def invalidate(dbapi_conn, conn_record, exception):
        pool.warning("connection_invalidated", exc_info=exception)

    @event.listens_for(engine, "engine_connect")
    def engine_connect(conn, branch):
        pool.info("engine_connect")
