from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class AIAction(BaseModel):
    type: str # SHOW_ON_MAP, BUILD_ROUTE, VIEW_STATION, COMPARE, FILTER_APPLY
    station_id: Optional[int] = None
    title: str
    payload: Optional[Dict[str, Any]] = None

class AIChatRequest(BaseModel):
    message: str
    user_location: Optional[Dict[str, float]] = None # {"latitude": 41.311081, "longitude": 69.240562}
    history: Optional[List[Dict[str, str]]] = []
    lang: Optional[str] = "uz" # uz, ru, en

class AIChatResponse(BaseModel):
    answer: str
    actions: List[AIAction] = []
    stations: List[Dict[str, Any]] = []
    suggested_questions: List[str] = []
