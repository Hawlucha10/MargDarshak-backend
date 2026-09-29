import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.ingest_tag_2026 import ingest

try:
    asyncio.run(ingest())
except Exception as e:
    print("\n--- CAUGHT EXCEPTION ---")
    print("Type:", type(e))
    print("Message:", repr(e))
    import traceback
    traceback.print_exc()
