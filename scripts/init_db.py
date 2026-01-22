#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from sage_mode.database import engine, Base
def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")
if __name__ == "__main__":
    init_db()
