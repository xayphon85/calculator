import math
from collections import deque
from datetime import datetime, timezone
from typing import List, Optional, Union

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from asteval import Interpreter

from calculator import expand_percent

HISTORY_MAX = 1000
history = deque(maxlen=HISTORY_MAX)

app = FastAPI(title="Mini Calculator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Safe evaluator ----------
aeval = Interpreter(minimal=True, usersyms={"pi": math.pi, "e": math.e})

# ---------- Models ----------
class HistoryItem(BaseModel):
    expr: str                    # what user entered (pretty string your UI sends)
    result: Union[int, float, str]
    ts: str                      # ISO timestamp (UTC)
@app.post("/calculate")
def calculate(expr: str):
    try:
        code = expand_percent(expr)
        result = aeval(code)
        if aeval.error:
            msg = "; ".join(str(e.get_error()) for e in aeval.error)
            aeval.error.clear()
            return {"ok": False, "expr": expr, "result": "", "error": msg}

        # TODO: Add history
           # ---- Add to history on success ----
        item = HistoryItem(
            expr=expr,
            result=result,
            ts=datetime.now(timezone.utc).isoformat()
        )
        history.append(item.model_dict())

        return {"ok": True, "expr": expr, "result": result, "error": ""}
    except Exception as e:
        return {"ok": False, "expr": expr, "error": str(e)}
        
        # ================
        
    

# TODO GET /hisory

# TODO DELETE /history
# ---------- History: get / add / clear ----------
@app.get("/history", response_model=List[HistoryItem])
def get_history(limit: Optional[int] = Query(default=50, ge=1)):
    """
    Return most-recent-first history items, up to `limit`.
    """
    items = list(history)[-limit:][::-1]
    return items


@app.post("/history", response_model=HistoryItem)
def add_history(item: HistoryItem):
    """
    Optional manual insert (not used by your UI, but handy for tests).
    """
    history.append(item.model_dict())
    return item