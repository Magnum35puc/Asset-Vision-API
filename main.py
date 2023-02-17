from fastapi import FastAPI, HTTPException,  Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, FileResponse

from models.Portfolio import Portfolio
from models.PortfolioRequest import PortfolioRequest
from models.Asset import Asset
from models.User import User
from typing import Union
from bson.objectid import ObjectId
from utils.secret_tools import access_secret_version

import jwt

from pymongo import MongoClient, ReturnDocument, errors
from pymongo.errors import PyMongoError

import bcrypt


from datetime import datetime, timedelta
import pytz
import json




client = MongoClient(access_secret_version("mongodb_str"))
db = client.AssetVision
assets = db.assets
portfolios = db.portfolios
users = db.users

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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
    try : 
         hpwd = user["hashed_password"].encode("utf-8")
    except AttributeError :
        hpwd = user["hashed_password"]
    if user and bcrypt.checkpw(str(password).encode("utf-8"), hpwd):
        # Password is correct
        return True
    else:
        # Password is incorrect
        return False

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(CH_timezone) + expires_delta
    else:
        expire = datetime.now(CH_timezone) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "secret", algorithm="HS256")
    return encoded_jwt

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/sample_secured")
async def test_secured_endpoint(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    return {"message": "Welcome to the secure endpoint "+username}

####################################################################################################
#                   User interactions
####################################################################################################
@app.post("/user")
async def create_user(username :str, password:str, email:Union[str, None],token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    creator = payload["sub"]
    hashed_password = bcrypt.hashpw(str(password).encode("utf-8"), bcrypt.gensalt())
    user = User(username=username,hashed_password=hashed_password, email=email, roles=["user"], created_at = datetime.now(CH_timezone))
    try:
        users.insert_one(user.dict())
        return {"message": f"User { username } created by {creator}"}

    except errors.DuplicateKeyError:
        raise HTTPException(status_code=409, detail="The user already exist in the collection.")

@app.get("/user/{username}")
async def read_user(username: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    reader = payload["sub"]
    requested_user = User(**users.find_one({"username": username}))
    return requested_user

@app.put("/user/{username}")
async def update_user(username, user_details: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    interactor = payload["sub"]
    try:
        user_details = json.loads(user_details)
        if "password" in user_details.keys():
            hashed_password = bcrypt.hashpw(str(user_details["password"]).encode("utf-8"), bcrypt.gensalt())
            user_details.pop("password")
            user_details["hashed_password"] = hashed_password
        updated_user = users.find_one_and_update(
            {"username": username},
            {"$set": user_details},
            return_document=ReturnDocument.AFTER
        )
        return {"message": f"User {username} updated by {interactor}", "updated_asset" : User(**updated_user)}
    except PyMongoError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/user/{username}")
async def delete_user(username: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    interactor = payload["sub"]
    result = users.delete_one({"username": username})
    if result.deleted_count >= 1:
        return {"message": f"User deleted by {interactor}"}
    raise HTTPException(status_code=500, detail="Something went wrong with the deletion")

@app.get("/users/")
async def get_all_users(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    interactor = payload["sub"]
    users_list = []
    for user in users.find():
        users_list.append(User(**user))
    return users_list
####################################################################################################
#                   Unique Asset interactions
####################################################################################################
@app.post("/asset")
async def create_asset(symbol:str,name:str, currency:Union[str, None] = None, asset_class:Union[str, None] = None, industry:Union[str, None] = None,last_price:Union[float, None] = 0, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    asset = Asset(symbol=symbol,name=name, last_price=last_price, currency=currency, asset_class=asset_class, industry=industry,last_updated_by = username, created_by = username, last_updated_at = datetime.now(CH_timezone) , created_at = datetime.now(CH_timezone))
    try:
        assets.insert_one(asset.dict())
        return {"message": f"Asset { symbol } created by { username }"}

    except errors.DuplicateKeyError:
        raise HTTPException(status_code=409, detail="The asset already exist in the collection.")

@app.get("/asset/{asset_symbol}")
async def read_asset(asset_symbol: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    requested_asset = Asset(**assets.find_one({"symbol": asset_symbol}))
    return requested_asset

@app.put("/asset/{asset_symbol}")
async def update_asset(asset_symbol, asset_details: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
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
        raise HTTPException(status_code=400, detail=str(e))
    
@app.delete("/asset/{asset_symbol}")
async def delete_asset(asset_symbol: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    result = assets.delete_one({"symbol": asset_symbol})
    if result.deleted_count >= 1:
        return {"message": "Asset deleted"}
    raise HTTPException(status_code=500, detail="Something went wrong with the deletion")

@app.get("/assets/")
async def get_all_assets(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    assets_list = []
    for asset in assets.find():
        assets_list.append(Asset(**asset))
    return assets_list

####################################################################################################
#                   Portfolios
####################################################################################################
@app.post("/portfolio")
async def create_portfolio(name:str, portfolio: PortfolioRequest,  token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]

    ##User input management
    #Case Shares not filled by the user
    if portfolio.shares == [] :
        portfolio.shares = [0] * len(portfolio.assets_symbols)
    if len(portfolio.assets_symbols)< len(portfolio.shares) : 
        portfolio.shares = portfolio.shares[:len(portfolio.assets_symbols)]
    #Case Shares partially filled
    while len(portfolio.assets_symbols)> len(portfolio.shares): 
        portfolio.shares.append(0)
    #Creation of the portfolio content
    portfolio_content= []
    for (index, symb) in enumerate(portfolio.assets_symbols) : 
        id = assets.find_one({"symbol": symb})["_id"]
        portfolio_content.append({"asset_id":ObjectId(id),"symbol":symb,"qty":portfolio.shares[index]})

    portfolio = Portfolio(name=name, portfolio_content = portfolio_content, owner = username, created_at = datetime.now(CH_timezone))

    try:
        portfolios.insert_one(portfolio.dict())
        return {"message": f"Portfolio { name } created by { username }"}

    except errors.DuplicateKeyError:
        raise HTTPException(status_code=409, detail="The portfolio already exist in the collection.")

@app.get("/portfolio/value/{portfolio_name}")
async def get_portfolio_value(portfolio_name:str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    result = portfolios.aggregate([
        {
            '$match': {
                'name': portfolio_name
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
            '$group': {
                '_id': 0, 
                'owner': {
                    '$first': '$owner'
                }, 
                'name': {
                    '$first': '$name'
                }, 
                'value': {
                    '$sum': {
                        '$multiply': [
                            '$portfolio_content.qty', '$asset.last_price'
                        ]
                    }
                }
            }
        }, {
        '$unset': '_id'
    }
    ])
    return result.next()
