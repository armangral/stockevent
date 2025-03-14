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


