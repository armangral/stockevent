from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, stocks, watchlists, crypto

api_router = APIRouter()


api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["Watchlist"])
api_router.include_router(crypto.router, prefix="/crypto", tags=["Crypto"])
# api_router.include_router(superadmin.router, prefix="/superadmin", tags=["Superadmin"])
