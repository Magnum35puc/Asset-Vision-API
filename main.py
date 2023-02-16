from fastapi import FastAPI, HTTPException,  Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse

from models.Portfolio import Portfolio
from models.PortfolioRequest import PortfolioRequest
from models.Asset import Asset
from typing import Union
from bson.objectid import ObjectId

import jwt

from pymongo import MongoClient, ReturnDocument, errors
from pymongo.errors import PyMongoError
from google.cloud import secretmanager


from datetime import datetime, timedelta
import json



def access_secret_version(secret_id, version_id="latest"):
    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = f"projects/97612062608/secrets/{secret_id}/versions/{version_id}"
    # Access the secret version.
    response = client.access_secret_version(name=name)

    # Return the decoded payload.
    return response.payload.data.decode('UTF-8')




client = MongoClient(access_secret_version("mongodb_str"))
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
    asset = Asset(symbol=symbol,name=name, last_price=last_price, currency=currency, asset_class=asset_class, industry=industry,last_updated_by = username, created_by = username, last_updated_at = datetime.now() , created_at = datetime.now())
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
    for asset in assets.find():
        assets_list.append(deserialize_asset(asset))
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
    portfolio_content= {}
    for (index, symb) in enumerate(portfolio.assets_symbols) : 
        id = assets.find_one({"symbol": symb})["_id"]
        portfolio_content[symb] = {"asset_id":ObjectId(id),"qty":portfolio.shares[index]}

    portfolio = Portfolio(name=name, portfolio_content = portfolio_content, owner = username, created_at = datetime.now())

    try:
        portfolios.insert_one(portfolio.dict())
        return {"message": f"Portfolio { name } created by { username }"}

    except errors.DuplicateKeyError:
        raise HTTPException(status_code=409, detail="The portfolio already exist in the collection.")

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
