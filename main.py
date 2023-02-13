from fastapi import FastAPI, Header, HTTPException,  Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, JSONResponse

from models.Portfolio import Portfolio
from models.Asset import Asset
import Configuration
from typing import Union,List

import jwt

from pymongo import MongoClient, ReturnDocument, errors
from pymongo.errors import PyMongoError


from datetime import datetime, timedelta
import json

client = MongoClient(Configuration.mongoDB_str)
db = client.AssetVision
assets = db.assets
portfolios = db.portfolios

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")



####################################################################################################
#                   Main Page
####################################################################################################
@app.get("/")
async def root():
    with open("static/homepage.html") as f:
        content = f.read()
    return HTMLResponse(content=content)

####################################################################################################
#                   Documentation
####################################################################################################
@app.get("/docs")
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="AssetVision API",
        description="AssetVision API documentation"
    )
####################################################################################################
#                   Login
####################################################################################################

def authenticate_user(username: str, password: str):
    # logic to authenticate the user and return a user object
    # if the username and password are valid, otherwise return None
    if username == "admin" and password == "1234" : 
        return True
    else : 
        return False

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
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
async def read_items(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    return {"message": "Welcome to the secure endpoint "+username}

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
    asset = Asset(symbol=symbol,name=name, last_price=last_price, currency=currency, asset_class=asset_class, industry=industry,last_updated_by = username, created_by = username)
    try:
        assets.insert_one(asset.serialize_asset())
        return {"message": f"Asset { symbol } created by { username }"}

    except errors.DuplicateKeyError:
        return "The asset already exist in the collection."

@app.get("/asset/{asset_symbol}")
async def read_asset(asset_symbol: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    requested_asset = deserialize_asset(assets.find_one({"symbol": asset_symbol}))
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
        asset_details["last_updated_by"] = username
        asset_details["last_updated_at"] = datetime.now()
        print(asset_details)
        updated_asset = assets.find_one_and_update(
            {"symbol": asset_symbol},
            {"$set": asset_details},
            return_document=ReturnDocument.AFTER
        )
        return {"message": "Asset updated", "updated_asset" : deserialize_asset(updated_asset)}
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
    async for asset in assets.find():
        assets_list.append(asset)
    return assets_list


    
####################################################################################################
#                   Portfolios
####################################################################################################
@app.post("/portfolio")
async def create_portfolio(name:str, symbols:List[str] = [], token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    asset_in_portfolio = []
    for i in list(assets.find({"symbol": {"$in": symbols}})):
        asset_in_portfolio.append(deserialize_asset(i))
    portfolio = Portfolio(name=name, assets = asset_in_portfolio, owner = username)
    try:
        portfolios.insert_one(portfolio.serialize_asset())
        return {"message": f"Portfolio { name } created by { username }"}

    except errors.DuplicateKeyError:
        return "The portfolio already exist in the collection."

####################################################################################################
#                   Useful tools
####################################################################################################
def deserialize_asset(data):
    return Asset(
        symbol=data['symbol'],
        name=data['name'],
        asset_class=data['asset_class'],
        last_price=data['last_price'],
        currency=data['currency'],
        industry=data['industry'],
        created_by=data['created_by'],
        created_at=data['created_at'],
        last_updated_by=data['last_updated_by'],
        last_updated_at=data['last_updated_at']
    )

        