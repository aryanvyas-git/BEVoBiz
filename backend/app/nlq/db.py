"""A dedicated database engine for the NLQ safe executor only.

Deliberately separate from app.database.engine (which the rest of the app
uses): this one connects as `bevobiz_nlq_reader`, a Postgres role that can
only ever SELECT from products/sales/businesses and has no write grant
anywhere (see db/init/002_nlq_readonly_role.sql). Nothing outside
app.nlq.executor should import this — it exists so that even a bug in the
application-level safety layer still can't produce a write, because the
role itself is incapable of one.
"""
from sqlalchemy import create_engine

from app.config import settings

nlq_engine = create_engine(settings.NLQ_DATABASE_URL, pool_pre_ping=True)
