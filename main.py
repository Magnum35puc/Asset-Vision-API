# FastAPI
from fastapi import FastAPI, HTTPException,  Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, FileResponse

# Pydantic
from models.Portfolio import Portfolio
from models.PortfolioRequest import PortfolioRequest
from models.Asset import Asset
from models.ExchangeRate import ExchangeRate
from models.User import User


# MongoDB 
from pymongo import MongoClient, ReturnDocument, errors
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId

# GCP
from utils.secret_tools import access_secret_version
secret_key = access_secret_version("hash_key")
# Authentification
import jwt
import bcrypt

# Others
from datetime import datetime, timedelta
import pytz
import json
from typing import Union


client = MongoClient(access_secret_version("mongodb_str"))
db = client.AssetVision
assets = db.assets
portfolios = db.portfolios
users = db.users
rates = db.FX_rates

# FastAPI Configuration
tags_metadata = [
    {"name": "Authentification Methods", "description": "Everything you need to connect and make your first query."},
    {"name": "Users Methods", "description": "Create and manage users."},
    {"name": "Assets Methods", "description": "Create and manage assets."},
    {"name": "Rates Methods", "description": "Create and manage exchange rates."},
    {"name": "Portfolio Methods", "description": "Create and manage portfolios."},
]
app = FastAPI(openapi_tags=tags_metadata)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Others
CH_timezone = pytz.timezone('Europe/Zurich')

####################################################################################################
#                   Main Page
#               Color ideas : https://coolors.co/003049-d62828-f77f00-fcbf49-eae2b7
####################################################################################################
@app.get("/", include_in_schema=False)
async def root():
    with open("static/homepage.html") as f:
        content = f.read()
    return HTMLResponse(content=content)

####################################################################################################
#                   Favicon
####################################################################################################
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

####################################################################################################
#                   Documentation
####################################################################################################
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="AssetVision API",
        description="AssetVision API documentation",
    )

####################################################################################################
#                   Login
####################################################################################################
def authenticate_user(username: str, password: str):
    # logic to authenticate the user and return a user object
    # if the username and password are valid, otherwise return None
    user = users.find_one({"username": username})
    if user is None:
        return False
    try : 
         hpwd = user["hashed_password"].encode("utf-8")
    except AttributeError :
        hpwd = user["hashed_password"]
    return bool(user and bcrypt.checkpw(password.encode("utf-8"), hpwd))

def create_access_token(data: dict, expires_delta: timedelta = None):
    print(data)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(CH_timezone) + expires_delta
    else:
        expire = datetime.now(CH_timezone) + timedelta(minutes=15)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, secret_key, algorithm="HS256")

@app.post("/login", tags=["Authentification Methods"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/sample_secured", tags=["Authentification Methods"])
async def test_secured_endpoint(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]

    return {"message": f"Welcome to the secure endpoint {username}"}

####################################################################################################
#                   User interactions
####################################################################################################
@app.post("/user", tags=["Users Methods"])
async def create_user(username :str, password:str, email:Union[str, None],token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    creator = payload["sub"]
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    user = User(username=username,hashed_password=hashed_password, email=email, roles=["user"], created_at = datetime.now(CH_timezone))
    try:
        users.insert_one(user.dict())
        return {"message": f"User { username } created by {creator}"}

    except errors.DuplicateKeyError as exc:
        raise HTTPException(
            status_code=409, detail="The user already exist in the collection."
        ) from exc

@app.get("/user/{username}", tags=["Users Methods"])
async def read_user(username: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    reader = payload["sub"]
    return User(**users.find_one({"username": username}))

@app.put("/user/{username}", tags=["Users Methods"])
async def update_user(username, user_details: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    interactor = payload["sub"]
    try:
        user_details = json.loads(user_details)
        if "password" in user_details.keys():
            hashed_password = bcrypt.hashpw(str(user_details["password"]).encode("utf-8"), bcrypt.gensalt())
            user_details.pop("password")

            user_details["hashed_password"] = str(hashed_password, 'UTF-8')
        updated_user = users.find_one_and_update(
            {"username": username},
            {"$set": user_details},
            return_document=ReturnDocument.AFTER
        )
        return {"message": f"User {username} updated by {interactor}", "updated_asset" : User(**updated_user)}
    except PyMongoError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@app.delete("/user/{username}", tags=["Users Methods"])
async def delete_user(username: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    interactor = payload["sub"]
    result = users.delete_one({"username": username})
    if result.deleted_count >= 1:
        return {"message": f"User deleted by {interactor}"}
    raise HTTPException(status_code=500, detail="Something went wrong with the deletion")

@app.get("/users/", tags=["Users Methods"])
async def get_all_users(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    interactor = payload["sub"]
    return [User(**user) for user in users.find()]

####################################################################################################
#                   Unique Asset interactions
####################################################################################################
@app.post("/asset", tags=["Assets Methods"])
async def create_asset(symbol:str,name:str, currency:Union[str, None] = None, asset_class:Union[str, None] = None,geo_zone:Union[str, None] = None, industry:Union[str, None] = None,last_price:Union[float, None] = 0, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    asset = Asset(symbol=symbol,name=name, last_price=last_price, currency=currency, asset_class=asset_class,geo_zone=geo_zone, industry=industry,last_updated_by = username, created_by = username, last_updated_at = datetime.now(CH_timezone) , created_at = datetime.now(CH_timezone))
    try:
        assets.insert_one(asset.dict())
        return {"message": f"Asset { symbol } created by { username }"}
    except errors.DuplicateKeyError as exc:
        raise HTTPException(
            status_code=409,
            detail="The asset already exist in the collection.",
        ) from exc

@app.get("/asset/{asset_symbol}", tags=["Assets Methods"])
async def read_asset(asset_symbol: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    return Asset(**assets.find_one({"symbol": asset_symbol}))

@app.put("/asset/{asset_symbol}", tags=["Assets Methods"])
async def update_asset(asset_symbol, asset_details: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    try:
        asset_details = json.loads(asset_details)
        asset_details["last_updated_by"] = str(username)
        asset_details["last_updated_at"] = datetime.now(CH_timezone)
        updated_asset = assets.find_one_and_update(
            {"symbol": asset_symbol},
            {"$set": asset_details},
            return_document=ReturnDocument.AFTER
        )
        return {"message": "Asset updated", "updated_asset" : Asset(**updated_asset)}
    except PyMongoError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@app.delete("/asset/{asset_symbol}", tags=["Assets Methods"])
async def delete_asset(asset_symbol: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    result = assets.delete_one({"symbol": asset_symbol})
    if result.deleted_count >= 1:
        return {"message": "Asset deleted"}
    raise HTTPException(status_code=500, detail="Something went wrong with the deletion")

@app.get("/assets/", tags=["Assets Methods"])
async def get_all_assets(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    return [Asset(**asset) for asset in assets.find()]

####################################################################################################
#                   Unique Rates interactions
####################################################################################################
@app.post("/rate", tags=["Rates Methods"])
async def create_rate(symbol:str, last_rate:Union[float, None] = None, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    exchangerate = ExchangeRate(symbol=symbol,base_currency=symbol[:3], target_currency=symbol[-3:], last_rate=last_rate,last_updated_by = username, created_by = username, last_updated_at = datetime.now(CH_timezone) , created_at = datetime.now(CH_timezone))
    inverse_exchangerate = ExchangeRate(symbol=symbol[-3:]+symbol[:3],base_currency=symbol[-3:], target_currency=symbol[:3], last_rate=1/last_rate,last_updated_by = username, created_by = username, last_updated_at = datetime.now(CH_timezone) , created_at = datetime.now(CH_timezone))
    try:
        rates.insert_one(exchangerate.dict())
        rates.insert_one(inverse_exchangerate.dict())
        return {"message": f"ExchangeRate  { symbol } and it's inverse pair created by { username }"}

    except errors.DuplicateKeyError as exc:
        raise HTTPException(
            status_code=409, detail="The rate already exist in the collection."
        ) from exc

@app.get("/rate/{rate_symbol}", tags=["Rates Methods"])
async def read_rate(rate_symbol: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    return ExchangeRate(**rates.find_one({"symbol": rate_symbol}))

@app.put("/rate/{rate_symbol}", tags=["Rates Methods"])
async def update_rate(rate_symbol, rate_details: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    try:
        rate_details = json.loads(rate_details)
        rate_details["last_updated_by"] = str(username)
        rate_details["last_updated_at"] = datetime.now(CH_timezone)
        if "last_rate" in rate_details.keys():
            inv_rate_details = {"last_rate":1/float(rate_details["last_rate"])}
            updated_inv_rate = rates.find_one_and_update(
            {"symbol": rate_symbol[-3:]+rate_symbol[:3]},
            {"$set": inv_rate_details},
            return_document=ReturnDocument.AFTER
            )
        updated_rate = rates.find_one_and_update(
            {"symbol": rate_symbol},
            {"$set": rate_details},
            return_document=ReturnDocument.AFTER
        )
        return {"message": "Rates updated", "updated_rate" : ExchangeRate(**updated_rate), "inverse_rate_updated": ExchangeRate(**updated_inv_rate)}
    except PyMongoError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@app.delete("/rate/{rate_symbol}", tags=["Rates Methods"])
async def delete_rate(rate_symbol: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    result = rates.delete_one({"symbol": rate_symbol})
    if result.deleted_count >= 1:
        return {"message": "Rate deleted"}
    raise HTTPException(status_code=500, detail="Something went wrong with the deletion")

@app.get("/rates/", tags=["Rates Methods"])
async def get_all_rates(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    return [ExchangeRate(**rate) for rate in rates.find()]


####################################################################################################
#                   Portfolios
####################################################################################################
@app.post("/portfolio", tags=["Portfolio Methods"])
async def create_portfolio(name:str, portfolio: PortfolioRequest,  token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]

    ##User input management
    #Case Shares partially filled
    while len(portfolio.assets_symbols)> len(portfolio.shares): 
        portfolio.shares.append(0)
    #Case cost_prices partially filled
    while len(portfolio.assets_symbols)> len(portfolio.cost_prices): 
        portfolio.cost_prices.append(0)  

    #Creation of the portfolio content
    portfolio_content= []
    for (index, symb) in enumerate(portfolio.assets_symbols) : 
        symb_id = assets.find_one({"symbol": symb})["_id"]
        portfolio_content.append({"asset_id":ObjectId(symb_id),"symbol":symb,"qty":portfolio.shares[index], "cost_prices":portfolio.cost_prices[index]})

    portfolio = Portfolio(name=name, portfolio_content = portfolio_content, owner = username,portfolio_currency = portfolio.portfolio_currency,  created_at = datetime.now(CH_timezone))

    try:
        portfolios.insert_one(portfolio.dict())
        return {"message": f"Portfolio { name } created by { username }"}

    except errors.DuplicateKeyError as exc:
        raise HTTPException(
            status_code=409,
            detail="The portfolio already exist in the collection.",
        ) from exc

@app.get("/portfolio/{portfolio_name}/value", tags=["Portfolio Methods"])
async def get_portfolio_value(portfolio_name:str, owner:Union[str, None] = None, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    owner = owner or username
    result = portfolios.aggregate([
        {
            '$match': {
                'name': portfolio_name,
                'owner' : owner
            }
        }, {
            '$unwind': '$portfolio_content'
        }, {
            '$lookup': {
                'from': 'assets', 
                'localField': 'portfolio_content.symbol', 
                'foreignField': 'symbol', 
                'as': 'asset'
            }
        }, {
            '$unwind': '$asset'
        }, {
            '$addFields': {
                'asset.exch_rate': {
                    '$concat': [
                        '$asset.currency', '$portfolio_currency'
                    ]
                }
            }
        }, {
            '$lookup': {
                'from': 'FX_rates', 
                'localField': 'asset.exch_rate', 
                'foreignField': 'symbol', 
                'as': 'asset.asset_rate'
            }
        }, {
            '$unwind': '$asset.asset_rate'
        }, {
            '$group': {
                '_id': 0, 
                'name': {
                    '$first': '$name'
                }, 
                'owner': {
                    '$first': '$owner'
                }, 
                'converted_price': {
                    '$sum': {
                        '$multiply': [
                            '$asset.last_price', '$asset.asset_rate.last_rate', '$portfolio_content.qty'
                        ]
                    }
                }, 
                'currency': {
                    '$first': '$portfolio_currency'
                }
            }
        }, {
            '$unset': '_id'
        }
    ])
    return result.next()

@app.get("/portfolio/{portfolio_name}/cost", tags=["Portfolio Methods"])
async def get_portfolio_cost(portfolio_name:str, owner:Union[str, None] = None, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    owner = owner or username
    result = portfolios.aggregate([
        {
            '$match': {
                'name': portfolio_name,
                'owner': owner
            }
        }, {
            '$unwind': '$portfolio_content'
        }, {
            '$lookup': {
                'from': 'assets', 
                'localField': 'portfolio_content.symbol', 
                'foreignField': 'symbol', 
                'as': 'asset'
            }
        }, {
            '$unwind': '$asset'
        }, {
            '$addFields': {
                'asset.exch_rate': {
                    '$concat': [
                        '$asset.currency', '$portfolio_currency'
                    ]
                }
            }
        }, {
            '$lookup': {
                'from': 'FX_rates', 
                'localField': 'asset.exch_rate', 
                'foreignField': 'symbol', 
                'as': 'asset.asset_rate'
            }
        }, {
            '$unwind': '$asset.asset_rate'
        }, {
            '$group': {
                '_id': 0, 
                'name': {
                    '$first': '$name'
                }, 
                'owner': {
                    '$first': '$owner'
                }, 
                'converted_cost_price': {
                    '$sum': {
                        '$multiply': [
                            '$portfolio_content.cost_prices', '$asset.asset_rate.last_rate', '$portfolio_content.qty'
                        ]
                    }
                }, 
                'currency': {
                    '$first': '$portfolio_currency'
                }
            }
        }, {
            '$unset': '_id'
        }
    ])
    return result.next()

@app.get("/portfolio/{portfolio_name}/total_return", tags=["Portfolio Methods"])
async def get_portfolio_total_return(portfolio_name:str, owner:Union[str, None] = None, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    owner = owner or username
    result = portfolios.aggregate([
        {
            '$match': {
                'name': portfolio_name,
                'owner': owner            }
        }, {
            '$unwind': '$portfolio_content'
        }, {
            '$lookup': {
                'from': 'assets', 
                'localField': 'portfolio_content.symbol', 
                'foreignField': 'symbol', 
                'as': 'asset'
            }
        }, {
            '$unwind': '$asset'
        }, {
            '$addFields': {
                'asset.exch_rate': {
                    '$concat': [
                        '$asset.currency', '$portfolio_currency'
                    ]
                }
            }
        }, {
            '$lookup': {
                'from': 'FX_rates', 
                'localField': 'asset.exch_rate', 
                'foreignField': 'symbol', 
                'as': 'asset.asset_rate'
            }
        }, {
            '$unwind': '$asset.asset_rate'
        }, {
            '$group': {
                '_id': 0, 
                'name': {
                    '$first': '$name'
                }, 
                'owner': {
                    '$first': '$owner'
                }, 
                'converted_price': {
                    '$sum': {
                        '$multiply': [
                            '$asset.last_price', '$asset.asset_rate.last_rate', '$portfolio_content.qty'
                        ]
                    }
                }, 
                'converted_cost_price': {
                    '$sum': {
                        '$multiply': [
                            '$portfolio_content.cost_prices', '$asset.asset_rate.last_rate', '$portfolio_content.qty'
                        ]
                    }
                }, 
                'currency': {
                    '$first': '$portfolio_currency'
                }
            }
        }, {
            '$project': {
                'name': '$name', 
                'owner': '$owner', 
                'converted_price': '$converted_price', 
                'converted_cost_price': '$converted_cost_price', 
                'return': {
                    '$divide': [
                        {
                            '$subtract': [
                                '$converted_price', '$converted_cost_price'
                            ]
                        }, '$converted_cost_price'
                    ]
                }, 
                'currency': '$currency'
            }
        }, {
            '$unset': '_id'
        }
    ])
    return result.next()

@app.get("/portfolio/{portfolio_name}/return_by_asset_class", tags=["Portfolio Methods"])
async def get_portfolio_return_by_asset_class(portfolio_name:str, owner:Union[str, None] = None, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    owner = owner or username
    result = portfolios.aggregate([
        {
            '$match': {
                'name': portfolio_name, 
                'owner': owner
            }
        }, {
            '$unwind': '$portfolio_content'
        }, {
            '$lookup': {
                'from': 'assets', 
                'localField': 'portfolio_content.symbol', 
                'foreignField': 'symbol', 
                'as': 'asset'
            }
        }, {
            '$unwind': '$asset'
        }, {
            '$addFields': {
                'asset.exch_rate': {
                    '$concat': [
                        '$asset.currency', '$portfolio_currency'
                    ]
                }
            }
        }, {
            '$lookup': {
                'from': 'FX_rates', 
                'localField': 'asset.exch_rate', 
                'foreignField': 'symbol', 
                'as': 'asset.asset_rate'
            }
        }, {
            '$unwind': '$asset.asset_rate'
        }, {
            '$group': {
                '_id': '$asset.asset_class', 
                'name': {
                    '$first': '$name'
                }, 
                'owner': {
                    '$first': '$owner'
                }, 
                'converted_price': {
                    '$sum': {
                        '$multiply': [
                            '$asset.last_price', '$asset.asset_rate.last_rate', '$portfolio_content.qty'
                        ]
                    }
                }, 
                'converted_cost_price': {
                    '$sum': {
                        '$multiply': [
                            '$portfolio_content.cost_prices', '$asset.asset_rate.last_rate', '$portfolio_content.qty'
                        ]
                    }
                }, 
                'currency': {
                    '$first': '$portfolio_currency'
                }
            }
        }, {
            '$project': {
                'asset_class': '$_id', 
                'name': '$name', 
                'owner': '$owner', 
                'converted_price': '$converted_price', 
                'converted_cost_price': '$converted_cost_price', 
                'return': {
                    '$divide': [
                        {
                            '$subtract': [
                                '$converted_price', '$converted_cost_price'
                            ]
                        }, '$converted_cost_price'
                    ]
                }, 
                'currency': '$currency'
            }
        }, {
            '$unset': '_id'
        }
    ])
    return list(result)

@app.get("/portfolio/{portfolio_name}/return_by_geo_zone", tags=["Portfolio Methods"])
async def get_portfolio_return_by_geo_zone(portfolio_name:str, owner:Union[str, None] = None, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    owner = owner or username
    result = portfolios.aggregate([
        {
            '$match': {
                    'name': portfolio_name, 
                    'owner': owner
                }
        }, {
            '$unwind': '$portfolio_content'
        }, {
            '$lookup': {
                'from': 'assets', 
                'localField': 'portfolio_content.symbol', 
                'foreignField': 'symbol', 
                'as': 'asset'
            }
        }, {
            '$unwind': '$asset'
        }, {
            '$addFields': {
                'asset.exch_rate': {
                    '$concat': [
                        '$asset.currency', '$portfolio_currency'
                    ]
                }
            }
        }, {
            '$lookup': {
                'from': 'FX_rates', 
                'localField': 'asset.exch_rate', 
                'foreignField': 'symbol', 
                'as': 'asset.asset_rate'
            }
        }, {
            '$unwind': '$asset.asset_rate'
        }, {
            '$group': {
                '_id': '$asset.geo_zone', 
                'name': {
                    '$first': '$name'
                }, 
                'owner': {
                    '$first': '$owner'
                }, 
                'converted_price': {
                    '$sum': {
                        '$multiply': [
                            '$asset.last_price', '$asset.asset_rate.last_rate', '$portfolio_content.qty'
                        ]
                    }
                }, 
                'converted_cost_price': {
                    '$sum': {
                        '$multiply': [
                            '$portfolio_content.cost_prices', '$asset.asset_rate.last_rate', '$portfolio_content.qty'
                        ]
                    }
                }, 
                'currency': {
                    '$first': '$portfolio_currency'
                }
            }
        }, {
            '$project': {
                'asset_class': '$_id', 
                'name': '$name', 
                'owner': '$owner', 
                'converted_price': '$converted_price', 
                'converted_cost_price': '$converted_cost_price', 
                'return': {
                    '$divide': [
                        {
                            '$subtract': [
                                '$converted_price', '$converted_cost_price'
                            ]
                        }, '$converted_cost_price'
                    ]
                }, 
                'currency': '$currency'
            }
        }, {
            '$unset': '_id'
        }
    ])
    return list(result)

@app.get("/portfolio/{portfolio_name}/assets", tags=["Portfolio Methods"])
async def get_portfolio_assets(portfolio_name:str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    result = portfolios.aggregate([
    {
        '$match': {
            'name': portfolio_name
        }
    }, {
        '$lookup': {
            'from': 'assets', 
            'localField': 'portfolio_content.symbol', 
            'foreignField': 'symbol', 
            'as': 'assets'
        }
    }, {
        '$addFields': {
            'assets': {
                '$map': {
                    'input': '$assets', 
                    'as': 'asset', 
                    'in': {
                        'symbol': '$$asset.symbol', 
                        'name': '$$asset.name', 
                        'qty': {
                            '$arrayElemAt': [
                                '$portfolio_content.qty', {
                                    '$indexOfArray': [
                                        '$portfolio_content.symbol', '$$asset.symbol'
                                    ]
                                }
                            ]
                        }, 
                        'cost_price': {
                            '$arrayElemAt': [
                                '$portfolio_content.cost_prices', {
                                    '$indexOfArray': [
                                        '$portfolio_content.symbol', '$$asset.symbol'
                                    ]
                                }
                            ]
                        }, 
                        'last_price': '$$asset.last_price'
                    }
                }
            }
        }
    }, {
        '$project': {
            '_id': 0, 
            'owner': 1, 
            'name': 1, 
            'assets': 1
        }
    }
])
    return result.next()

@app.put("/portfolio/{portfolio_name}/buy/{symbol}", tags=["Portfolio Methods"])
async def buy_asset_in_portfolio(portfolio_name: str, symbol: str, qty: float, cost_price:Union[float, None] = None, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    # Get portfolio by name
    portfolio = Portfolio(**portfolios.find_one({"name": portfolio_name}))
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    # If asset in portfolio
    if asset := next((a for a in portfolio.portfolio_content if a["symbol"] == symbol), None):
        # Compute new price qnd qty
        new_qty = asset["qty"] + qty
        new_cost_price = (asset["cost_prices"] * asset["qty"] + cost_price * qty) / new_qty
        # Update portfolio
        portfolios.update_one(
            {"name": portfolio_name, "portfolio_content.symbol": symbol},
            {"$set": {"portfolio_content.$.qty": new_qty, "portfolio_content.$.cost_prices": new_cost_price, "last_updated_at": datetime.now(CH_timezone)}}
        )
        return {"message": f"Asset {symbol} updated successfully in portfolio {portfolio_name}."}
    #If asset not in portfolio
    else:
        #Find in DB the asset details
        asset_stored = assets.find_one({"symbol": symbol})
        if asset_stored is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        asset = {
            "asset_id": ObjectId(asset_stored["_id"]),
            "symbol": symbol,
            "qty": qty,
            "cost_prices": cost_price,
        }
        portfolios.update_one({"name": portfolio_name}, {"$push": {"portfolio_content": asset}})
        return {"message": f"Asset {symbol} added successfully to portfolio {portfolio_name}."}

@app.put("/portfolio/{portfolio_name}/sell/{symbol}", tags=["Portfolio Methods"])
async def sell_asset_in_portfolio(portfolio_name: str, symbol: str, qty: float, sell_price:Union[float, None] = None, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail="Could not validate credentials"
        ) from e
    username = payload["sub"]
    # Get portfolio by name
    portfolio = Portfolio(**portfolios.find_one({"name": portfolio_name}))
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    # Asset not in portfolio
    if not (asset := next((a for a in portfolio.portfolio_content if a["symbol"] == symbol),None,)):
        return {"message": f"Asset {symbol} does not exist in the portfolio {portfolio_name}."}
    # Asset in portfolio
    # Compute new price and qty(no neg)
    
    if qty > asset["qty"]:
        sold_qty = asset["qty"]
        remaining_qty = 0
    else : 
        sold_qty = qty
        remaining_qty = asset["qty"] - qty

    realizedPNL = asset["realized_pnl"] if "realized_pnl" in asset.keys() else 0
    realizedPNL += (sell_price - asset["cost_prices"])*abs(sold_qty)
    # Update portfolio
    portfolios.update_one(
        {"name": portfolio_name, "portfolio_content.symbol": symbol},
        {"$set": {"portfolio_content.$.qty": remaining_qty, "portfolio_content.$.realized_pnl": realizedPNL, "last_updated_at": datetime.now(CH_timezone)}}
    )
    return {"message": f"Asset {symbol} updated successfully in portfolio {portfolio_name}."}




