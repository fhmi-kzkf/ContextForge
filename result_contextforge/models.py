from pydantic import BaseModel
from typing import Any, List, Optional, Dict


class PredictRequest(BaseModel):
    
    
    X: Any # TODO: refine type
    
    

class ScoreRequest(BaseModel):
    
    
    X: Any # TODO: refine type
    
    
    
    y: Any # TODO: refine type
    
    
    
    sample_weight: Any # TODO: refine type
    
    


# Default fallback if no entry points were detected properly
if not hasattr(locals(), 'PredictRequest'):
    class PredictRequest(BaseModel):
        data: Any # TODO: refine type

class PredictResponse(BaseModel):
    status: str
    function: str
    result: Any
    metadata: Optional[Dict[str, Any]] = None