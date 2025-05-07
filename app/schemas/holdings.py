from pydantic import BaseModel


class HoldingCreate(BaseModel):
    shares: float
    # average_cost: float


class HoldingResponse(BaseModel):
    shares: float
    total_pnl: float
    total_value: float