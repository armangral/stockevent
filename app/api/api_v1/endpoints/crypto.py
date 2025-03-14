from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.crud.crypto import fetch_crypto_data_crud, fetch_historical_data


router = APIRouter()


@router.get("/usd")
async def get_crypto_data_usd(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, alias="offset"),
    limit: int = Query(10),
):
    
    crypto_symbols = [
    {"symbol": "BTC", "id": "bitcoin"},
    {"symbol": "ETH", "id": "ethereum"},
    {"symbol": "BNB", "id": "binancecoin"},
    {"symbol": "SOL", "id": "solana"},
    {"symbol": "XRP", "id": "ripple"},
    {"symbol": "ADA", "id": "cardano"},
    {"symbol": "AVAX", "id": "avalanche-2"},
    {"symbol": "DOGE", "id": "dogecoin"},
    {"symbol": "DOT", "id": "polkadot"},
    {"symbol": "MATIC", "id": "matic-network"},
    {"symbol": "LINK", "id": "chainlink"},
    {"symbol": "LTC", "id": "litecoin"},
    {"symbol": "UNI", "id": "uniswap"},
    {"symbol": "SHIB", "id": "shiba-inu"},
    {"symbol": "TRX", "id": "tron"},
    {"symbol": "XLM", "id": "stellar"},
    {"symbol": "ATOM", "id": "cosmos"},
    {"symbol": "CRO", "id": "crypto-com-chain"},
    {"symbol": "BCH", "id": "bitcoin-cash"},
    {"symbol": "ALGO", "id": "algorand"},
    {"symbol": "ETC", "id": "ethereum-classic"},
    {"symbol": "FIL", "id": "filecoin"},
    {"symbol": "VET", "id": "vechain"},
    {"symbol": "MANA", "id": "decentraland"},
    {"symbol": "THETA", "id": "theta-token"},
    {"symbol": "AXS", "id": "axie-infinity"},
    {"symbol": "ICP", "id": "internet-computer"},
    {"symbol": "FTT", "id": "ftx-token"},
    {"symbol": "XTZ", "id": "tezos"},
    {"symbol": "EOS", "id": "eos"},
    {"symbol": "SAND", "id": "the-sandbox"},
    {"symbol": "AAVE", "id": "aave"},
    {"symbol": "EGLD", "id": "elrond-erd-2"},
    {"symbol": "HBAR", "id": "hedera-hashgraph"},
    {"symbol": "MIOTA", "id": "iota"},
    {"symbol": "XMR", "id": "monero"},
    {"symbol": "CAKE", "id": "pancakeswap-token"},
    {"symbol": "FTM", "id": "fantom"},
    {"symbol": "NEO", "id": "neo"},
    {"symbol": "KSM", "id": "kusama"},
    {"symbol": "ONE", "id": "harmony"},
    {"symbol": "MKR", "id": "maker"},
    {"symbol": "ENJ", "id": "enjincoin"},
    {"symbol": "RUNE", "id": "thorchain"},
    {"symbol": "ZEC", "id": "zcash"},
    {"symbol": "CHZ", "id": "chiliz"},
    {"symbol": "QNT", "id": "quant-network"},
    {"symbol": "HOT", "id": "holo"},
    {"symbol": "BAT", "id": "basic-attention-token"},
    {"symbol": "DASH", "id": "dash"},
    {"symbol": "WAVES", "id": "waves"},
    {"symbol": "AMP", "id": "amp-token"},
    {"symbol": "COMP", "id": "compound-governance-token"},
    {"symbol": "STX", "id": "stacks"},
    {"symbol": "CELO", "id": "celo"},
    {"symbol": "AR", "id": "arweave"},
    {"symbol": "KLAY", "id": "klaytn"},
    {"symbol": "LRC", "id": "loopring"},
    {"symbol": "HNT", "id": "helium"},
    {"symbol": "DCR", "id": "decred"},
    {"symbol": "TFUEL", "id": "theta-fuel"},
    {"symbol": "YFI", "id": "yearn-finance"},
    {"symbol": "ICX", "id": "icon"},
    {"symbol": "OMG", "id": "omisego"},
    {"symbol": "1INCH", "id": "1inch"},
    {"symbol": "KNC", "id": "kyber-network-crystal"},
    {"symbol": "CRV", "id": "curve-dao-token"},
    {"symbol": "ZEN", "id": "zencash"},
    {"symbol": "QTUM", "id": "qtum"},
    ][skip : skip + limit]

    data = await fetch_crypto_data_crud(db, crypto_symbols, currency="USD")
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data


@router.get("/gbp")
async def get_crypto_data_gbp(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, alias="offset"),
    limit: int = Query(10),
):
    crypto_symbols = [
        "BTC",
        "ETH",
        "BNB",
        "SOL",
        "XRP",
        "ADA",
        "AVAX",
        "DOGE",
        "DOT",
        "MATIC",
        "LINK",
        "LTC",
        "UNI",
        "SHIB",
        "TRX",
        "XLM",
        "ATOM",
        "CRO",
        "BCH",
        "ALGO",
        "ETC",
        "FIL",
        "VET",
        "MANA",
        "THETA",
        "AXS",
        "ICP",
        "FTT",
        "XTZ",
        "EOS",
        "SAND",
        "AAVE",
        "EGLD",
        "HBAR",
        "MIOTA",
        "XMR",
        "CAKE",
        "FTM",
        "NEO",
        "KSM",
        "ONE",
        "MKR",
        "ENJ",
        "RUNE",
        "ZEC",
        "CHZ",
        "QNT",
        "HOT",
        "BAT",
        "DASH",
        "WAVES",
        "AMP",
        "COMP",
        "STX",
        "CELO",
        "AR",
        "KLAY",
        "LRC",
        "HNT",
        "DCR",
        "TFUEL",
        "YFI",
        "ICX",
        "OMG",
        "1INCH",
        "KNC",
        "CRV",
        "ZEN",
        "QTUM",
        "SUSHI",
        "ZIL",
        "ANKR",
        "IOTX",
        "RVN",
        "BAKE",
        "SNX",
        "GRT",
        "BNT",
        "SC",
        "STORJ",
        "ONT",
        "IOST",
        "CELR",
        "REN",
        "DGB",
        "SKL",
        "RSR",
        "OGN",
        "LUNA",
        "CKB",
        "NKN",
        "PERP",
        "SRM",
        "KDA",
        "CTSI",
        "ERG",
        "CFX",
    ][skip : skip + limit]

    data = await fetch_crypto_data_crud(db, crypto_symbols, currency="GBP")
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data


@router.get("/usd/{symbol}")
async def get_crypto_statistics_usd(symbol: str):
    return fetch_historical_data(symbol, currency="USD")

@router.get("/gbp/{symbol}")
async def get_crypto_statistics_gbp(symbol: str):
    return fetch_historical_data(symbol, currency="GBP")


