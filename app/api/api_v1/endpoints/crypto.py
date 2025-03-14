from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.crud.crypto import fetch_crypto_data_crud, fetch_historical_data, fetch_stock_data_crud, fetch_stock_data_crud_gbp


router = APIRouter()


@router.get("/usd")
async def get_crypto_data_usd(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, alias="offset"),
    limit: int = Query(10),
):
    
    crypto_symbols = [
        {
            "symbol": "BTC",
            "id": "bitcoin",
            "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
        },
        {
            "symbol": "ETH",
            "id": "ethereum",
            "image": "https://assets.coingecko.com/coins/images/279/large/ethereum.png",
        },
        {
            "symbol": "BNB",
            "id": "binancecoin",
            "image": "https://assets.coingecko.com/coins/images/825/large/binance-coin-logo.png",
        },
        {
            "symbol": "SOL",
            "id": "solana",
            "image": "https://assets.coingecko.com/coins/images/4128/large/solana.png",
        },
        {
            "symbol": "XRP",
            "id": "ripple",
            "image": "https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png",
        },
        {
            "symbol": "ADA",
            "id": "cardano",
            "image": "https://assets.coingecko.com/coins/images/975/large/cardano.png",
        },
        {
            "symbol": "AVAX",
            "id": "avalanche-2",
            "image": "https://assets.coingecko.com/coins/images/12559/large/coin-round-red.png",
        },
        {
            "symbol": "DOGE",
            "id": "dogecoin",
            "image": "https://assets.coingecko.com/coins/images/5/large/dogecoin.png",
        },
        {
            "symbol": "DOT",
            "id": "polkadot",
            "image": "https://assets.coingecko.com/coins/images/12171/large/polkadot.png",
        },
        {
            "symbol": "MATIC",
            "id": "matic-network",
            "image": "https://assets.coingecko.com/coins/images/4713/large/matic-token-icon.png",
        },
        {
            "symbol": "LINK",
            "id": "chainlink",
            "image": "https://assets.coingecko.com/coins/images/877/large/chainlink-new-logo.png",
        },
        {
            "symbol": "LTC",
            "id": "litecoin",
            "image": "https://assets.coingecko.com/coins/images/2/large/litecoin.png",
        },
        {
            "symbol": "UNI",
            "id": "uniswap",
            "image": "https://assets.coingecko.com/coins/images/12504/large/uniswap-uni.png",
        },
        {
            "symbol": "SHIB",
            "id": "shiba-inu",
            "image": "https://assets.coingecko.com/coins/images/11939/large/shiba.png",
        },
        {
            "symbol": "TRX",
            "id": "tron",
            "image": "https://assets.coingecko.com/coins/images/1094/large/tron-logo.png",
        },
        {
            "symbol": "XLM",
            "id": "stellar",
            "image": "https://assets.coingecko.com/coins/images/100/large/Stellar_symbol_black_RGB.png",
        },
        {
            "symbol": "ATOM",
            "id": "cosmos",
            "image": "https://assets.coingecko.com/coins/images/1481/large/cosmos_hub.png",
        },
        {
            "symbol": "CRO",
            "id": "crypto-com-chain",
            "image": "https://assets.coingecko.com/coins/images/7310/large/cro_token_logo.png",
        },
        {
            "symbol": "BCH",
            "id": "bitcoin-cash",
            "image": "https://assets.coingecko.com/coins/images/780/large/bitcoin-cash-circle.png",
        },
        {
            "symbol": "ALGO",
            "id": "algorand",
            "image": "https://assets.coingecko.com/coins/images/4380/large/download.png",
        },
        {
            "symbol": "ETC",
            "id": "ethereum-classic",
            "image": "https://assets.coingecko.com/coins/images/453/large/ethereum-classic-logo.png",
        },
        {
            "symbol": "FIL",
            "id": "filecoin",
            "image": "https://assets.coingecko.com/coins/images/12817/large/filecoin.png",
        },
        {
            "symbol": "VET",
            "id": "vechain",
            "image": "https://assets.coingecko.com/coins/images/1578/large/VeChain-Logo-1.png",
        },
        {
            "symbol": "MANA",
            "id": "decentraland",
            "image": "https://assets.coingecko.com/coins/images/878/large/decentraland-mana.png",
        },
        {
            "symbol": "THETA",
            "id": "theta-token",
            "image": "https://assets.coingecko.com/coins/images/2538/large/theta-token-logo.png",
        },
        {
            "symbol": "AXS",
            "id": "axie-infinity",
            "image": "https://assets.coingecko.com/coins/images/13029/large/axie_infinity_logo.png",
        },
        {
            "symbol": "ICP",
            "id": "internet-computer",
            "image": "https://assets.coingecko.com/coins/images/14495/large/Internet_Computer_logo.png",
        },
        {
            "symbol": "FTT",
            "id": "ftx-token",
            "image": "https://assets.coingecko.com/coins/images/9026/large/F.png",
        },
        {
            "symbol": "XTZ",
            "id": "tezos",
            "image": "https://assets.coingecko.com/coins/images/976/large/Tezos-logo.png",
        },
        {
            "symbol": "EOS",
            "id": "eos",
            "image": "https://assets.coingecko.com/coins/images/738/large/eos-eos-logo.png",
        },
        {
            "symbol": "SAND",
            "id": "the-sandbox",
            "image": "https://assets.coingecko.com/coins/images/12129/large/sandbox_logo.jpg",
        },
        {
            "symbol": "AAVE",
            "id": "aave",
            "image": "https://assets.coingecko.com/coins/images/12645/large/AAVE.png",
        },
        {
            "symbol": "EGLD",
            "id": "elrond-erd-2",
            "image": "https://assets.coingecko.com/coins/images/12335/large/Elrond.png",
        },
        {
            "symbol": "HBAR",
            "id": "hedera-hashgraph",
            "image": "https://assets.coingecko.com/coins/images/3688/large/hbar.png",
        },
        {
            "symbol": "MIOTA",
            "id": "iota",
            "image": "https://assets.coingecko.com/coins/images/692/large/IOTA_Swirl.png",
        },
        {
            "symbol": "XMR",
            "id": "monero",
            "image": "https://assets.coingecko.com/coins/images/69/large/monero_logo.png",
        },
        {
            "symbol": "CAKE",
            "id": "pancakeswap-token",
            "image": "https://assets.coingecko.com/coins/images/12632/large/pancakeswap-cake-logo.png",
        },
        {
            "symbol": "FTM",
            "id": "fantom",
            "image": "https://assets.coingecko.com/coins/images/4001/large/Fantom.png",
        },
        {
            "symbol": "NEO",
            "id": "neo",
            "image": "https://assets.coingecko.com/coins/images/1376/large/NEO.png",
        },
        {
            "symbol": "KSM",
            "id": "kusama",
            "image": "https://assets.coingecko.com/coins/images/12235/large/kusama.png",
        },
        {
            "symbol": "ONE",
            "id": "harmony",
            "image": "https://assets.coingecko.com/coins/images/4344/large/Harmony.png",
        },
        {
            "symbol": "MKR",
            "id": "maker",
            "image": "https://assets.coingecko.com/coins/images/1364/large/Mark_Maker.png",
        },
        {
            "symbol": "ENJ",
            "id": "enjincoin",
            "image": "https://assets.coingecko.com/coins/images/1105/large/Enjin.png",
        },
        {
            "symbol": "RUNE",
            "id": "thorchain",
            "image": "https://assets.coingecko.com/coins/images/6595/large/THORChain.png",
        },
        {
            "symbol": "ZEC",
            "id": "zcash",
            "image": "https://assets.coingecko.com/coins/images/486/large/Zcash.png",
        },
        {
            "symbol": "CHZ",
            "id": "chiliz",
            "image": "https://assets.coingecko.com/coins/images/8834/large/Chiliz.png",
        },
        {
            "symbol": "QNT",
            "id": "quant-network",
            "image": "https://assets.coingecko.com/coins/images/3370/large/Quant.png",
        },
        {
            "symbol": "HOT",
            "id": "holo",
            "image": "https://assets.coingecko.com/coins/images/3348/large/Holo.png",
        },
        {
            "symbol": "BAT",
            "id": "basic-attention-token",
            "image": "https://assets.coingecko.com/coins/images/677/large/BAT.png",
        },
        {
            "symbol": "DASH",
            "id": "dash",
            "image": "https://assets.coingecko.com/coins/images/19/large/Dash.png",
        },
        {
            "symbol": "WAVES",
            "id": "waves",
            "image": "https://assets.coingecko.com/coins/images/425/large/Waves.png",
        },
        {
            "symbol": "AMP",
            "id": "amp-token",
            "image": "https://assets.coingecko.com/coins/images/12409/large/Amp.png",
        },
        {
            "symbol": "COMP",
            "id": "compound-governance-token",
            "image": "https://assets.coingecko.com/coins/images/10775/large/Compound.png",
        },
        {
            "symbol": "STX",
            "id": "stacks",
            "image": "https://assets.coingecko.com/coins/images/2069/large/Stacks.png",
        },
        {
            "symbol": "CELO",
            "id": "celo",
            "image": "https://assets.coingecko.com/coins/images/11090/large/Celo.png",
        },
        {
            "symbol": "AR",
            "id": "arweave",
            "image": "https://assets.coingecko.com/coins/images/4343/large/Arweave.png",
        },
        {
            "symbol": "KLAY",
            "id": "klaytn",
            "image": "https://assets.coingecko.com/coins/images/9672/large/Klaytn.png",
        },
        {
            "symbol": "LRC",
            "id": "loopring",
            "image": "https://assets.coingecko.com/coins/images/913/large/Loopring.png",
        },
        {
            "symbol": "HNT",
            "id": "helium",
            "image": "https://assets.coingecko.com/coins/images/4284/large/Helium.png",
        },
        {
            "symbol": "DCR",
            "id": "decred",
            "image": "https://assets.coingecko.com/coins/images/329/large/Decred.png",
        },
        {
            "symbol": "TFUEL",
            "id": "theta-fuel",
            "image": "https://assets.coingecko.com/coins/images/8029/large/Theta_Fuel.png",
        },
        {
            "symbol": "YFI",
            "id": "yearn-finance",
            "image": "https://assets.coingecko.com/coins/images/11849/large/yearn-finance.png",
        },
        {
            "symbol": "ICX",
            "id": "icon",
            "image": "https://assets.coingecko.com/coins/images/1060/large/ICON.png",
        },
        {
            "symbol": "OMG",
            "id": "omisego",
            "image": "https://assets.coingecko.com/coins/images/776/large/OMG.png",
        },
        {
            "symbol": "1INCH",
            "id": "1inch",
            "image": "https://assets.coingecko.com/coins/images/13469/large/1inch.png",
        },
        {
            "symbol": "KNC",
            "id": "kyber-network-crystal",
            "image": "https://assets.coingecko.com/coins/images/14899/large/Kyber_Network_Crystal.png",
        },
        {
            "symbol": "CRV",
            "id": "curve-dao-token",
            "image": "https://assets.coingecko.com/coins/images/12124/large/Curve.png",
        },
        {
            "symbol": "ZEN",
            "id": "zencash",
            "image": "https://assets.coingecko.com/coins/images/691/large/ZenCash.png",
        },
        {
            "symbol": "QTUM",
            "id": "qtum",
            "image": "https://assets.coingecko.com/coins/images/684/large/Qtum.png",
        },
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
        {
            "symbol": "BTC",
            "id": "bitcoin",
            "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
        },
        {
            "symbol": "ETH",
            "id": "ethereum",
            "image": "https://assets.coingecko.com/coins/images/279/large/ethereum.png",
        },
        {
            "symbol": "BNB",
            "id": "binancecoin",
            "image": "https://assets.coingecko.com/coins/images/825/large/binance-coin-logo.png",
        },
        {
            "symbol": "SOL",
            "id": "solana",
            "image": "https://assets.coingecko.com/coins/images/4128/large/solana.png",
        },
        {
            "symbol": "XRP",
            "id": "ripple",
            "image": "https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png",
        },
        {
            "symbol": "ADA",
            "id": "cardano",
            "image": "https://assets.coingecko.com/coins/images/975/large/cardano.png",
        },
        {
            "symbol": "AVAX",
            "id": "avalanche-2",
            "image": "https://assets.coingecko.com/coins/images/12559/large/coin-round-red.png",
        },
        {
            "symbol": "DOGE",
            "id": "dogecoin",
            "image": "https://assets.coingecko.com/coins/images/5/large/dogecoin.png",
        },
        {
            "symbol": "DOT",
            "id": "polkadot",
            "image": "https://assets.coingecko.com/coins/images/12171/large/polkadot.png",
        },
        {
            "symbol": "MATIC",
            "id": "matic-network",
            "image": "https://assets.coingecko.com/coins/images/4713/large/matic-token-icon.png",
        },
        {
            "symbol": "LINK",
            "id": "chainlink",
            "image": "https://assets.coingecko.com/coins/images/877/large/chainlink-new-logo.png",
        },
        {
            "symbol": "LTC",
            "id": "litecoin",
            "image": "https://assets.coingecko.com/coins/images/2/large/litecoin.png",
        },
        {
            "symbol": "UNI",
            "id": "uniswap",
            "image": "https://assets.coingecko.com/coins/images/12504/large/uniswap-uni.png",
        },
        {
            "symbol": "SHIB",
            "id": "shiba-inu",
            "image": "https://assets.coingecko.com/coins/images/11939/large/shiba.png",
        },
        {
            "symbol": "TRX",
            "id": "tron",
            "image": "https://assets.coingecko.com/coins/images/1094/large/tron-logo.png",
        },
        {
            "symbol": "XLM",
            "id": "stellar",
            "image": "https://assets.coingecko.com/coins/images/100/large/Stellar_symbol_black_RGB.png",
        },
        {
            "symbol": "ATOM",
            "id": "cosmos",
            "image": "https://assets.coingecko.com/coins/images/1481/large/cosmos_hub.png",
        },
        {
            "symbol": "CRO",
            "id": "crypto-com-chain",
            "image": "https://assets.coingecko.com/coins/images/7310/large/cro_token_logo.png",
        },
        {
            "symbol": "BCH",
            "id": "bitcoin-cash",
            "image": "https://assets.coingecko.com/coins/images/780/large/bitcoin-cash-circle.png",
        },
        {
            "symbol": "ALGO",
            "id": "algorand",
            "image": "https://assets.coingecko.com/coins/images/4380/large/download.png",
        },
        {
            "symbol": "ETC",
            "id": "ethereum-classic",
            "image": "https://assets.coingecko.com/coins/images/453/large/ethereum-classic-logo.png",
        },
        {
            "symbol": "FIL",
            "id": "filecoin",
            "image": "https://assets.coingecko.com/coins/images/12817/large/filecoin.png",
        },
        {
            "symbol": "VET",
            "id": "vechain",
            "image": "https://assets.coingecko.com/coins/images/1578/large/VeChain-Logo-1.png",
        },
        {
            "symbol": "MANA",
            "id": "decentraland",
            "image": "https://assets.coingecko.com/coins/images/878/large/decentraland-mana.png",
        },
        {
            "symbol": "THETA",
            "id": "theta-token",
            "image": "https://assets.coingecko.com/coins/images/2538/large/theta-token-logo.png",
        },
        {
            "symbol": "AXS",
            "id": "axie-infinity",
            "image": "https://assets.coingecko.com/coins/images/13029/large/axie_infinity_logo.png",
        },
        {
            "symbol": "ICP",
            "id": "internet-computer",
            "image": "https://assets.coingecko.com/coins/images/14495/large/Internet_Computer_logo.png",
        },
        {
            "symbol": "FTT",
            "id": "ftx-token",
            "image": "https://assets.coingecko.com/coins/images/9026/large/F.png",
        },
        {
            "symbol": "XTZ",
            "id": "tezos",
            "image": "https://assets.coingecko.com/coins/images/976/large/Tezos-logo.png",
        },
        {
            "symbol": "EOS",
            "id": "eos",
            "image": "https://assets.coingecko.com/coins/images/738/large/eos-eos-logo.png",
        },
        {
            "symbol": "SAND",
            "id": "the-sandbox",
            "image": "https://assets.coingecko.com/coins/images/12129/large/sandbox_logo.jpg",
        },
        {
            "symbol": "AAVE",
            "id": "aave",
            "image": "https://assets.coingecko.com/coins/images/12645/large/AAVE.png",
        },
        {
            "symbol": "EGLD",
            "id": "elrond-erd-2",
            "image": "https://assets.coingecko.com/coins/images/12335/large/Elrond.png",
        },
        {
            "symbol": "HBAR",
            "id": "hedera-hashgraph",
            "image": "https://assets.coingecko.com/coins/images/3688/large/hbar.png",
        },
        {
            "symbol": "MIOTA",
            "id": "iota",
            "image": "https://assets.coingecko.com/coins/images/692/large/IOTA_Swirl.png",
        },
        {
            "symbol": "XMR",
            "id": "monero",
            "image": "https://assets.coingecko.com/coins/images/69/large/monero_logo.png",
        },
        {
            "symbol": "CAKE",
            "id": "pancakeswap-token",
            "image": "https://assets.coingecko.com/coins/images/12632/large/pancakeswap-cake-logo.png",
        },
        {
            "symbol": "FTM",
            "id": "fantom",
            "image": "https://assets.coingecko.com/coins/images/4001/large/Fantom.png",
        },
        {
            "symbol": "NEO",
            "id": "neo",
            "image": "https://assets.coingecko.com/coins/images/1376/large/NEO.png",
        },
        {
            "symbol": "KSM",
            "id": "kusama",
            "image": "https://assets.coingecko.com/coins/images/12235/large/kusama.png",
        },
        {
            "symbol": "ONE",
            "id": "harmony",
            "image": "https://assets.coingecko.com/coins/images/4344/large/Harmony.png",
        },
        {
            "symbol": "MKR",
            "id": "maker",
            "image": "https://assets.coingecko.com/coins/images/1364/large/Mark_Maker.png",
        },
        {
            "symbol": "ENJ",
            "id": "enjincoin",
            "image": "https://assets.coingecko.com/coins/images/1105/large/Enjin.png",
        },
        {
            "symbol": "RUNE",
            "id": "thorchain",
            "image": "https://assets.coingecko.com/coins/images/6595/large/THORChain.png",
        },
        {
            "symbol": "ZEC",
            "id": "zcash",
            "image": "https://assets.coingecko.com/coins/images/486/large/Zcash.png",
        },
        {
            "symbol": "CHZ",
            "id": "chiliz",
            "image": "https://assets.coingecko.com/coins/images/8834/large/Chiliz.png",
        },
        {
            "symbol": "QNT",
            "id": "quant-network",
            "image": "https://assets.coingecko.com/coins/images/3370/large/Quant.png",
        },
        {
            "symbol": "HOT",
            "id": "holo",
            "image": "https://assets.coingecko.com/coins/images/3348/large/Holo.png",
        },
        {
            "symbol": "BAT",
            "id": "basic-attention-token",
            "image": "https://assets.coingecko.com/coins/images/677/large/BAT.png",
        },
        {
            "symbol": "DASH",
            "id": "dash",
            "image": "https://assets.coingecko.com/coins/images/19/large/Dash.png",
        },
        {
            "symbol": "WAVES",
            "id": "waves",
            "image": "https://assets.coingecko.com/coins/images/425/large/Waves.png",
        },
        {
            "symbol": "AMP",
            "id": "amp-token",
            "image": "https://assets.coingecko.com/coins/images/12409/large/Amp.png",
        },
        {
            "symbol": "COMP",
            "id": "compound-governance-token",
            "image": "https://assets.coingecko.com/coins/images/10775/large/Compound.png",
        },
        {
            "symbol": "STX",
            "id": "stacks",
            "image": "https://assets.coingecko.com/coins/images/2069/large/Stacks.png",
        },
        {
            "symbol": "CELO",
            "id": "celo",
            "image": "https://assets.coingecko.com/coins/images/11090/large/Celo.png",
        },
        {
            "symbol": "AR",
            "id": "arweave",
            "image": "https://assets.coingecko.com/coins/images/4343/large/Arweave.png",
        },
        {
            "symbol": "KLAY",
            "id": "klaytn",
            "image": "https://assets.coingecko.com/coins/images/9672/large/Klaytn.png",
        },
        {
            "symbol": "LRC",
            "id": "loopring",
            "image": "https://assets.coingecko.com/coins/images/913/large/Loopring.png",
        },
        {
            "symbol": "HNT",
            "id": "helium",
            "image": "https://assets.coingecko.com/coins/images/4284/large/Helium.png",
        },
        {
            "symbol": "DCR",
            "id": "decred",
            "image": "https://assets.coingecko.com/coins/images/329/large/Decred.png",
        },
        {
            "symbol": "TFUEL",
            "id": "theta-fuel",
            "image": "https://assets.coingecko.com/coins/images/8029/large/Theta_Fuel.png",
        },
        {
            "symbol": "YFI",
            "id": "yearn-finance",
            "image": "https://assets.coingecko.com/coins/images/11849/large/yearn-finance.png",
        },
        {
            "symbol": "ICX",
            "id": "icon",
            "image": "https://assets.coingecko.com/coins/images/1060/large/ICON.png",
        },
        {
            "symbol": "OMG",
            "id": "omisego",
            "image": "https://assets.coingecko.com/coins/images/776/large/OMG.png",
        },
        {
            "symbol": "1INCH",
            "id": "1inch",
            "image": "https://assets.coingecko.com/coins/images/13469/large/1inch.png",
        },
        {
            "symbol": "KNC",
            "id": "kyber-network-crystal",
            "image": "https://assets.coingecko.com/coins/images/14899/large/Kyber_Network_Crystal.png",
        },
        {
            "symbol": "CRV",
            "id": "curve-dao-token",
            "image": "https://assets.coingecko.com/coins/images/12124/large/Curve.png",
        },
        {
            "symbol": "ZEN",
            "id": "zencash",
            "image": "https://assets.coingecko.com/coins/images/691/large/ZenCash.png",
        },
        {
            "symbol": "QTUM",
            "id": "qtum",
            "image": "https://assets.coingecko.com/coins/images/684/large/Qtum.png",
        },
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


@router.get("/stocks/usd")
async def get_stock_data_usd(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, alias="offset"),
    limit: int = Query(10),
):
    stock_symbols = [
        {
            "company_name": "Apple Inc.",
            "symbol": "AAPL",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Apple-Logo.png",
        },
        {
            "company_name": "Microsoft Corporation",
            "symbol": "MSFT",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/10/Microsoft-Logo.png",
        },
        {
            "company_name": "Alphabet Inc. (Class A)",
            "symbol": "GOOGL",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/10/Alphabet-Logo.png",
        },
        {
            "company_name": "Amazon.com, Inc.",
            "symbol": "AMZN",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Amazon-Logo.png",
        },
        {
            "company_name": "NVIDIA Corporation",
            "symbol": "NVDA",
            "logo_url": "https://1000logos.net/wp-content/uploads/2020/08/Nvidia-Logo.png",
        },
        {
            "company_name": "Meta Platforms, Inc.",
            "symbol": "META",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/11/Facebook-Meta-Logo.png",
        },
        {
            "company_name": "Tesla, Inc.",
            "symbol": "TSLA",
            "logo_url": "https://1000logos.net/wp-content/uploads/2018/03/Tesla-Logo.png",
        },
        {
            "company_name": "Taiwan Semiconductor Manufacturing Company Limited",
            "symbol": "TSM",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/06/TSMC-Logo.png",
        },
        {
            "company_name": "Samsung Electronics Co., Ltd.",
            "symbol": "005930.KS",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/06/Samsung-Logo.png",
        },
        {
            "company_name": "Intel Corporation",
            "symbol": "INTC",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Intel-Logo.png",
        },
        {
            "company_name": "JPMorgan Chase & Co.",
            "symbol": "JPM",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/JPMorgan-Chase-Logo.png",
        },
        {
            "company_name": "Procter & Gamble Co.",
            "symbol": "PG",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Procter-Gamble-Logo.png",
        },
        {
            "company_name": "Johnson & Johnson",
            "symbol": "JNJ",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Johnson-Johnson-Logo.png",
        },
        {
            "company_name": "Berkshire Hathaway Inc. (Class B)",
            "symbol": "BRK.B",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/Berkshire-Hathaway-Logo.png",
        },
        {
            "company_name": "Nestlé S.A.",
            "symbol": "NESN.SW",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Nestle-Logo.png",
        },
        {
            "company_name": "Alibaba Group Holding Limited",
            "symbol": "BABA",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/02/Alibaba-Logo.png",
        },
        {
            "company_name": "Tencent Holdings Ltd.",
            "symbol": "0700.HK",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/02/Tencent-Logo.png",
        },
        {
            "company_name": "Industrial and Commercial Bank of China Limited",
            "symbol": "1398.HK",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/ICBC-Logo.png",
        },
        {
            "company_name": "Exxon Mobil Corporation",
            "symbol": "XOM",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/ExxonMobil-Logo.png",
        },
        {
            "company_name": "Bank of America Corporation",
            "symbol": "BAC",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Bank-of-America-Logo.png",
        },
        {
            "company_name": "Wells Fargo & Company",
            "symbol": "WFC",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Wells-Fargo-Logo.png",
        },
        {
            "company_name": "Pfizer Inc.",
            "symbol": "PFE",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Pfizer-Logo.png",
        },
        {
            "company_name": "Roche Holding AG",
            "symbol": "ROG.SW",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Roche-Logo.png",
        },
        {
            "company_name": "Novartis AG",
            "symbol": "NOVN.SW",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Novartis-Logo.png",
        },
        {
            "company_name": "Merck & Co., Inc.",
            "symbol": "MRK",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Merck-Logo.png",
        },
        {
            "company_name": "AbbVie Inc.",
            "symbol": "ABBV",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/AbbVie-Logo.png",
        },
        {
            "company_name": "Chevron Corporation",
            "symbol": "CVX",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Chevron-Logo.png",
        },
        {
            "company_name": "Shell plc",
            "symbol": "SHEL",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Shell-Logo.png",
        },
        {
            "company_name": "TotalEnergies SE",
            "symbol": "TTE",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/TotalEnergies-Logo.png",
        },
        {
            "company_name": "BP p.l.c.",
            "symbol": "BP",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/BP-Logo.png",
        },
        {
            "company_name": "ConocoPhillips",
            "symbol": "COP",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/ConocoPhillips-Logo.png",
        },
        {
            "company_name": "Petróleo Brasileiro S.A. - Petrobras",
            "symbol": "PBR",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/Petrobras-Logo.png",
        },
        {
            "company_name": "Eni S.p.A.",
            "symbol": "ENI.MI",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Eni-Logo.png",
        },
        {
            "company_name": "LVMH Moët Hennessy Louis Vuitton SE",
            "symbol": "MC.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/12/LVMH-Logo.png",
        },
        {
            "company_name": "ASML Holding N.V.",
            "symbol": "ASML",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/08/ASML-Logo.png",
        },
        {
            "company_name": "Home Depot",
            "symbol": "HD",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/12/Home-Depot-Logo.png",
        },
        {
            "company_name": "The Coca-Cola Company",
            "symbol": "KO",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/04/Coca-Cola-Logo.png",
        },
        {
            "company_name": "Walmart Inc.",
            "symbol": "WMT",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Walmart-Logo.png",
        },
        {
            "company_name": "UnitedHealth Group Incorporated",
            "symbol": "UNH",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/08/UnitedHealth-Logo.png",
        },
        {
            "company_name": "Visa Inc.",
            "symbol": "V",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Visa-Logo.png",
        },
        {
            "company_name": "Mastercard Incorporated",
            "symbol": "MA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Mastercard-Logo.png",
        },
        {
            "company_name": "Toyota Motor Corporation",
            "symbol": "TM",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Toyota-Logo.png",
        },
        {
            "company_name": "Accenture plc",
            "symbol": "ACN",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Accenture-Logo.png",
        },
        {
            "company_name": "SAP SE",
            "symbol": "SAP",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/09/SAP-Logo.png",
        },
        {
            "company_name": "Oracle Corporation",
            "symbol": "ORCL",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/06/Oracle-Logo.png",
        },
        {
            "company_name": "Salesforce, Inc.",
            "symbol": "CRM",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/09/Salesforce-Logo.png",
        },
        {
            "company_name": "Adobe Inc.",
            "symbol": "ADBE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/04/Adobe-Logo.png",
        },
        {
            "company_name": "Cisco Systems, Inc.",
            "symbol": "CSCO",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Cisco-Logo.png",
        },
        {
            "company_name": "Thermo Fisher Scientific Inc.",
            "symbol": "TMO",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Thermo-Fisher-Scientific-Logo.png",
        },
        {
            "company_name": "Danaher Corporation",
            "symbol": "DHR",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Danaher-Logo.png",
        },
        {
            "company_name": "Linde plc",
            "symbol": "LIN",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/08/Linde-Logo.png",
        },
        {
            "company_name": "McDonald's Corporation",
            "symbol": "MCD",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/McDonalds-Logo.png",
        },
        {
            "company_name": "PepsiCo, Inc.",
            "symbol": "PEP",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Pepsi-Logo.png",
        },
        {
            "company_name": "The Walt Disney Company",
            "symbol": "DIS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Disney-Logo.png",
        },
        {
            "company_name": "Netflix, Inc.",
            "symbol": "NFLX",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/04/Netflix-Logo.png",
        },
        {
            "company_name": "Comcast Corporation",
            "symbol": "CMCSA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Comcast-Logo.png",
        },
        {
            "company_name": "Nike, Inc.",
            "symbol": "NKE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/04/Nike-Logo.png",
        },
        {
            "company_name": "Starbucks Corporation",
            "symbol": "SBUX",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Starbucks-Logo.png",
        },
        {
            "company_name": "Costco Wholesale Corporation",
            "symbol": "COST",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Costco-Logo.png",
        },
        {
            "company_name": "L'Oréal S.A.",
            "symbol": "OR.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/12/LOreal-Logo.png",
        },
        {
            "company_name": "AstraZeneca PLC",
            "symbol": "AZN",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/AstraZeneca-Logo.png",
        },
        {
            "company_name": "GlaxoSmithKline plc",
            "symbol": "GSK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/GSK-Logo.png",
        },
        {
            "company_name": "Eli Lilly and Company",
            "symbol": "LLY",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Eli-Lilly-Logo.png",
        },
        {
            "company_name": "Novo Nordisk A/S",
            "symbol": "NVO",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Novo-Nordisk-Logo.png",
        },
        {
            "company_name": "Sanofi S.A.",
            "symbol": "SNY",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Sanofi-Logo.png",
        },
        {
            "company_name": "CVS Health Corporation",
            "symbol": "CVS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/CVS-Health-Logo.png",
        },
        {
            "company_name": "Anthem, Inc.",
            "symbol": "ELV",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Anthem-Logo.png",
        },
        {
            "company_name": "Ping An Insurance",
            "symbol": "2318.HK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Ping-An-Insurance-Logo.png",
        },
        {
            "company_name": "China Construction Bank",
            "symbol": "0939.HK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/China-Construction-Bank-Logo.png",
        },
        {
            "company_name": "Agricultural Bank of China",
            "symbol": "1288.HK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Agricultural-Bank-of-China-Logo.png",
        },
        {
            "company_name": "Bank of China",
            "symbol": "3988.HK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Bank-of-China-Logo.png",
        },
        {
            "company_name": "Toyota Motor Corporation",
            "symbol": "7203.T",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Toyota-Logo.png",
        },
        {
            "company_name": "Sony Group Corporation",
            "symbol": "6758.T",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Sony-Logo.png",
        },
        {
            "company_name": "Keyence Corporation",
            "symbol": "6861.T",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Keyence-Logo.png",
        },
        {
            "company_name": "Mitsubishi UFJ Financial Group",
            "symbol": "8306.T",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Mitsubishi-UFJ-Financial-Group-Logo.png",
        },
        {
            "company_name": "SoftBank Group Corp.",
            "symbol": "9984.T",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/SoftBank-Logo.png",
        },
        {
            "company_name": "Commonwealth Bank",
            "symbol": "CBA.AX",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Commonwealth-Bank-Logo.png",
        },
        {
            "company_name": "BHP Group",
            "symbol": "BHP",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/BHP-Logo.png",
        },
        {
            "company_name": "Rio Tinto Group",
            "symbol": "RIO",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Rio-Tinto-Logo.png",
        },
        {
            "company_name": "CSL Limited",
            "symbol": "CSL.AX",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/CSL-Limited-Logo.png",
        },
        {
            "company_name": "Telstra Corporation Limited",
            "symbol": "TLS.AX",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Telstra-Logo.png",
        },
        {
            "company_name": "Bayer AG",
            "symbol": "BAYN.DE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Bayer-Logo.png",
        },
        {
            "company_name": "Siemens AG",
            "symbol": "SIE.DE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Siemens-Logo.png",
        },
        {
            "company_name": "Allianz SE",
            "symbol": "ALV.DE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Allianz-Logo.png",
        },
        {
            "company_name": "Volkswagen AG",
            "symbol": "VOW3.DE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Volkswagen-Logo.png",
        },
        {
            "company_name": "Daimler AG",
            "symbol": "MBG.DE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Mercedes-Benz-Logo.png",
        },
        {
            "company_name": "TotalEnergies SE",
            "symbol": "TTE.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/TotalEnergies-Logo.png",
        },
        {
            "company_name": "BNP Paribas SA",
            "symbol": "BNP.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/BNP-Paribas-Logo.png",
        },
        {
            "company_name": "Airbus SE",
            "symbol": "AIR.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Airbus-Logo.png",
        },
        {
            "company_name": "Schneider Electric SE",
            "symbol": "SU.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Schneider-Electric-Logo.png",
        },
        {
            "company_name": "EssilorLuxottica SA",
            "symbol": "EL.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/EssilorLuxottica-Logo.png",
        },
        {
            "company_name": "Diageo plc",
            "symbol": "DGE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Diageo-Logo.png",
        },
        {
            "company_name": "Unilever PLC",
            "symbol": "ULVR.L",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Unilever-Logo.png",
        },
        {
            "company_name": "HSBC Holdings plc",
            "symbol": "HSBA.L",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/HSBC-Logo.png",
        },
        {
            "company_name": "AIA Group Limited",
            "symbol": "1299.HK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/AIA-Group-Logo.png",
        },
        {
            "company_name": "HDFC Bank Limited",
            "symbol": "HDFCBANK.NS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/HDFC-Bank-Logo.png",
        },
        {
            "company_name": "Reliance Industries Limited",
            "symbol": "RELIANCE.NS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Reliance-Industries-Logo.png",
        },
        {
            "company_name": "Tata Consultancy Services Limited",
            "symbol": "TCS.NS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Tata-Consultancy-Services-Logo.png",
        },
        {
            "company_name": "ICICI Bank Limited",
            "symbol": "ICICIBANK.NS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/ICICI-Bank-Logo.png",
        },
        {
            "company_name": "Infosys Limited",
            "symbol": "INFY.NS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Infosys-Logo.png",
        },
    ][skip : skip + limit]

    data = await fetch_stock_data_crud(db, stock_symbols)
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data


@router.get("/stocks/gbp")
async def get_stock_data_gbp(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, alias="offset"),
    limit: int = Query(10),
):
    stock_symbols = [
        {
            "company_name": "Apple Inc.",
            "symbol": "AAPL",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Apple-Logo.png",
        },
        {
            "company_name": "Microsoft Corporation",
            "symbol": "MSFT",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/10/Microsoft-Logo.png",
        },
        {
            "company_name": "Alphabet Inc. (Class A)",
            "symbol": "GOOGL",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/10/Alphabet-Logo.png",
        },
        {
            "company_name": "Amazon.com, Inc.",
            "symbol": "AMZN",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Amazon-Logo.png",
        },
        {
            "company_name": "NVIDIA Corporation",
            "symbol": "NVDA",
            "logo_url": "https://1000logos.net/wp-content/uploads/2020/08/Nvidia-Logo.png",
        },
        {
            "company_name": "Meta Platforms, Inc.",
            "symbol": "META",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/11/Facebook-Meta-Logo.png",
        },
        {
            "company_name": "Tesla, Inc.",
            "symbol": "TSLA",
            "logo_url": "https://1000logos.net/wp-content/uploads/2018/03/Tesla-Logo.png",
        },
        {
            "company_name": "Taiwan Semiconductor Manufacturing Company Limited",
            "symbol": "TSM",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/06/TSMC-Logo.png",
        },
        {
            "company_name": "Samsung Electronics Co., Ltd.",
            "symbol": "005930.KS",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/06/Samsung-Logo.png",
        },
        {
            "company_name": "Intel Corporation",
            "symbol": "INTC",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Intel-Logo.png",
        },
        {
            "company_name": "JPMorgan Chase & Co.",
            "symbol": "JPM",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/JPMorgan-Chase-Logo.png",
        },
        {
            "company_name": "Procter & Gamble Co.",
            "symbol": "PG",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Procter-Gamble-Logo.png",
        },
        {
            "company_name": "Johnson & Johnson",
            "symbol": "JNJ",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Johnson-Johnson-Logo.png",
        },
        {
            "company_name": "Berkshire Hathaway Inc. (Class B)",
            "symbol": "BRK.B",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/Berkshire-Hathaway-Logo.png",
        },
        {
            "company_name": "Nestlé S.A.",
            "symbol": "NESN.SW",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Nestle-Logo.png",
        },
        {
            "company_name": "Alibaba Group Holding Limited",
            "symbol": "BABA",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/02/Alibaba-Logo.png",
        },
        {
            "company_name": "Tencent Holdings Ltd.",
            "symbol": "0700.HK",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/02/Tencent-Logo.png",
        },
        {
            "company_name": "Industrial and Commercial Bank of China Limited",
            "symbol": "1398.HK",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/ICBC-Logo.png",
        },
        {
            "company_name": "Exxon Mobil Corporation",
            "symbol": "XOM",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/ExxonMobil-Logo.png",
        },
        {
            "company_name": "Bank of America Corporation",
            "symbol": "BAC",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Bank-of-America-Logo.png",
        },
        {
            "company_name": "Wells Fargo & Company",
            "symbol": "WFC",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Wells-Fargo-Logo.png",
        },
        {
            "company_name": "Pfizer Inc.",
            "symbol": "PFE",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Pfizer-Logo.png",
        },
        {
            "company_name": "Roche Holding AG",
            "symbol": "ROG.SW",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Roche-Logo.png",
        },
        {
            "company_name": "Novartis AG",
            "symbol": "NOVN.SW",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Novartis-Logo.png",
        },
        {
            "company_name": "Merck & Co., Inc.",
            "symbol": "MRK",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Merck-Logo.png",
        },
        {
            "company_name": "AbbVie Inc.",
            "symbol": "ABBV",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/AbbVie-Logo.png",
        },
        {
            "company_name": "Chevron Corporation",
            "symbol": "CVX",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Chevron-Logo.png",
        },
        {
            "company_name": "Shell plc",
            "symbol": "SHEL",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/Shell-Logo.png",
        },
        {
            "company_name": "TotalEnergies SE",
            "symbol": "TTE",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/TotalEnergies-Logo.png",
        },
        {
            "company_name": "BP p.l.c.",
            "symbol": "BP",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/BP-Logo.png",
        },
        {
            "company_name": "ConocoPhillips",
            "symbol": "COP",
            "logo_url": "https://1000logos.net/wp-content/uploads/2016/10/ConocoPhillips-Logo.png",
        },
        {
            "company_name": "Petróleo Brasileiro S.A. - Petrobras",
            "symbol": "PBR",
            "logo_url": "https://1000logos.net/wp-content/uploads/2021/05/Petrobras-Logo.png",
        },
        {
            "company_name": "Eni S.p.A.",
            "symbol": "ENI.MI",
            "logo_url": "https://1000logos.net/wp-content/uploads/2017/03/Eni-Logo.png",
        },
        {
            "company_name": "LVMH Moët Hennessy Louis Vuitton SE",
            "symbol": "MC.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/12/LVMH-Logo.png",
        },
        {
            "company_name": "ASML Holding N.V.",
            "symbol": "ASML",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/08/ASML-Logo.png",
        },
        {
            "company_name": "Home Depot",
            "symbol": "HD",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/12/Home-Depot-Logo.png",
        },
        {
            "company_name": "The Coca-Cola Company",
            "symbol": "KO",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/04/Coca-Cola-Logo.png",
        },
        {
            "company_name": "Walmart Inc.",
            "symbol": "WMT",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Walmart-Logo.png",
        },
        {
            "company_name": "UnitedHealth Group Incorporated",
            "symbol": "UNH",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/08/UnitedHealth-Logo.png",
        },
        {
            "company_name": "Visa Inc.",
            "symbol": "V",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Visa-Logo.png",
        },
        {
            "company_name": "Mastercard Incorporated",
            "symbol": "MA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Mastercard-Logo.png",
        },
        {
            "company_name": "Toyota Motor Corporation",
            "symbol": "TM",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Toyota-Logo.png",
        },
        {
            "company_name": "Accenture plc",
            "symbol": "ACN",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Accenture-Logo.png",
        },
        {
            "company_name": "SAP SE",
            "symbol": "SAP",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/09/SAP-Logo.png",
        },
        {
            "company_name": "Oracle Corporation",
            "symbol": "ORCL",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/06/Oracle-Logo.png",
        },
        {
            "company_name": "Salesforce, Inc.",
            "symbol": "CRM",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/09/Salesforce-Logo.png",
        },
        {
            "company_name": "Adobe Inc.",
            "symbol": "ADBE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/04/Adobe-Logo.png",
        },
        {
            "company_name": "Cisco Systems, Inc.",
            "symbol": "CSCO",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Cisco-Logo.png",
        },
        {
            "company_name": "Thermo Fisher Scientific Inc.",
            "symbol": "TMO",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Thermo-Fisher-Scientific-Logo.png",
        },
        {
            "company_name": "Danaher Corporation",
            "symbol": "DHR",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Danaher-Logo.png",
        },
        {
            "company_name": "Linde plc",
            "symbol": "LIN",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/08/Linde-Logo.png",
        },
        {
            "company_name": "McDonald's Corporation",
            "symbol": "MCD",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/McDonalds-Logo.png",
        },
        {
            "company_name": "PepsiCo, Inc.",
            "symbol": "PEP",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Pepsi-Logo.png",
        },
        {
            "company_name": "The Walt Disney Company",
            "symbol": "DIS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Disney-Logo.png",
        },
        {
            "company_name": "Netflix, Inc.",
            "symbol": "NFLX",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/04/Netflix-Logo.png",
        },
        {
            "company_name": "Comcast Corporation",
            "symbol": "CMCSA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Comcast-Logo.png",
        },
        {
            "company_name": "Nike, Inc.",
            "symbol": "NKE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/04/Nike-Logo.png",
        },
        {
            "company_name": "Starbucks Corporation",
            "symbol": "SBUX",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Starbucks-Logo.png",
        },
        {
            "company_name": "Costco Wholesale Corporation",
            "symbol": "COST",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/05/Costco-Logo.png",
        },
        {
            "company_name": "L'Oréal S.A.",
            "symbol": "OR.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2020/12/LOreal-Logo.png",
        },
        {
            "company_name": "AstraZeneca PLC",
            "symbol": "AZN",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/AstraZeneca-Logo.png",
        },
        {
            "company_name": "GlaxoSmithKline plc",
            "symbol": "GSK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/GSK-Logo.png",
        },
        {
            "company_name": "Eli Lilly and Company",
            "symbol": "LLY",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Eli-Lilly-Logo.png",
        },
        {
            "company_name": "Novo Nordisk A/S",
            "symbol": "NVO",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Novo-Nordisk-Logo.png",
        },
        {
            "company_name": "Sanofi S.A.",
            "symbol": "SNY",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Sanofi-Logo.png",
        },
        {
            "company_name": "CVS Health Corporation",
            "symbol": "CVS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/CVS-Health-Logo.png",
        },
        {
            "company_name": "Anthem, Inc.",
            "symbol": "ELV",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Anthem-Logo.png",
        },
        {
            "company_name": "Ping An Insurance",
            "symbol": "2318.HK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Ping-An-Insurance-Logo.png",
        },
        {
            "company_name": "China Construction Bank",
            "symbol": "0939.HK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/China-Construction-Bank-Logo.png",
        },
        {
            "company_name": "Agricultural Bank of China",
            "symbol": "1288.HK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Agricultural-Bank-of-China-Logo.png",
        },
        {
            "company_name": "Bank of China",
            "symbol": "3988.HK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Bank-of-China-Logo.png",
        },
        {
            "company_name": "Toyota Motor Corporation",
            "symbol": "7203.T",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Toyota-Logo.png",
        },
        {
            "company_name": "Sony Group Corporation",
            "symbol": "6758.T",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Sony-Logo.png",
        },
        {
            "company_name": "Keyence Corporation",
            "symbol": "6861.T",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Keyence-Logo.png",
        },
        {
            "company_name": "Mitsubishi UFJ Financial Group",
            "symbol": "8306.T",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Mitsubishi-UFJ-Financial-Group-Logo.png",
        },
        {
            "company_name": "SoftBank Group Corp.",
            "symbol": "9984.T",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/SoftBank-Logo.png",
        },
        {
            "company_name": "Commonwealth Bank",
            "symbol": "CBA.AX",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Commonwealth-Bank-Logo.png",
        },
        {
            "company_name": "BHP Group",
            "symbol": "BHP",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/BHP-Logo.png",
        },
        {
            "company_name": "Rio Tinto Group",
            "symbol": "RIO",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Rio-Tinto-Logo.png",
        },
        {
            "company_name": "CSL Limited",
            "symbol": "CSL.AX",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/CSL-Limited-Logo.png",
        },
        {
            "company_name": "Telstra Corporation Limited",
            "symbol": "TLS.AX",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Telstra-Logo.png",
        },
        {
            "company_name": "Bayer AG",
            "symbol": "BAYN.DE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Bayer-Logo.png",
        },
        {
            "company_name": "Siemens AG",
            "symbol": "SIE.DE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Siemens-Logo.png",
        },
        {
            "company_name": "Allianz SE",
            "symbol": "ALV.DE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Allianz-Logo.png",
        },
        {
            "company_name": "Volkswagen AG",
            "symbol": "VOW3.DE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Volkswagen-Logo.png",
        },
        {
            "company_name": "Daimler AG",
            "symbol": "MBG.DE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Mercedes-Benz-Logo.png",
        },
        {
            "company_name": "TotalEnergies SE",
            "symbol": "TTE.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/TotalEnergies-Logo.png",
        },
        {
            "company_name": "BNP Paribas SA",
            "symbol": "BNP.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/BNP-Paribas-Logo.png",
        },
        {
            "company_name": "Airbus SE",
            "symbol": "AIR.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Airbus-Logo.png",
        },
        {
            "company_name": "Schneider Electric SE",
            "symbol": "SU.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Schneider-Electric-Logo.png",
        },
        {
            "company_name": "EssilorLuxottica SA",
            "symbol": "EL.PA",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/EssilorLuxottica-Logo.png",
        },
        {
            "company_name": "Diageo plc",
            "symbol": "DGE",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Diageo-Logo.png",
        },
        {
            "company_name": "Unilever PLC",
            "symbol": "ULVR.L",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Unilever-Logo.png",
        },
        {
            "company_name": "HSBC Holdings plc",
            "symbol": "HSBA.L",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/HSBC-Logo.png",
        },
        {
            "company_name": "AIA Group Limited",
            "symbol": "1299.HK",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/AIA-Group-Logo.png",
        },
        {
            "company_name": "HDFC Bank Limited",
            "symbol": "HDFCBANK.NS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/HDFC-Bank-Logo.png",
        },
        {
            "company_name": "Reliance Industries Limited",
            "symbol": "RELIANCE.NS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/Reliance-Industries-Logo.png",
        },
        {
            "company_name": "Tata Consultancy Services Limited",
            "symbol": "TCS.NS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Tata-Consultancy-Services-Logo.png",
        },
        {
            "company_name": "ICICI Bank Limited",
            "symbol": "ICICIBANK.NS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/05/ICICI-Bank-Logo.png",
        },
        {
            "company_name": "Infosys Limited",
            "symbol": "INFY.NS",
            "logo_url": "https://logos-world.net/wp-content/uploads/2021/03/Infosys-Logo.png",
        },
    ][skip : skip + limit]

    data = await fetch_stock_data_crud_gbp(db, stock_symbols,"GBP")
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data