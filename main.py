from fastapi import FastAPI, Header, HTTPException,  Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from models.Portfolio import Portfolio
from models.Asset import Asset
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
import json
import pickle


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

portfolios = []
assets = {}
# {"symbol":"BTC", "name":"Bitcoin","shares" : 0.128318,"price":22000,"purchase_price" : 23030,"currency" : "USD","asset_class" : "Cryptocurrency","industry" : "Blockchain"}
# {"symbol":"ETH", "name":"Ethereum","shares" : 0.7098,"price":1540,"purchase_price" : 1536,"currency" : "USD","asset_class" : "Cryptocurrency","industry" : "Blockchain"}
def save_assets(assets, filename="assets_list.txt"):
    with open(filename, 'wb') as f:
        pickle.dump(assets, f)

def load_assets(filename="assets_list.txt"):
    with open(filename, 'rb') as f:
        return pickle.load(f)
assets = load_assets()



class LoginRequest(BaseModel):
    username: str
    password: str

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
async def create_asset(asset_details, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    asset = Asset(**json.loads(asset_details))
    assets[asset.symbol] = asset
    save_assets(assets)
    return {"message": "Asset created by user "+username}

@app.get("/asset/{asset_symbol}")
async def read_asset(asset_symbol: str, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    return assets[asset_symbol]

@app.put("/asset/{asset_symbol}")
async def update_asset(asset_symbol, asset_details, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    asset = Asset(**json.loads(asset_details))
    assets[asset_symbol] = asset
    save_assets(assets)
    return {"message": "Asset updated"}

@app.delete("/asset/{asset_symbol}")
async def delete_asset(asset_symbol: int, token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    assets.pop(asset_symbol)
    save_assets(assets)
    return {"message": "Asset deleted"}
####################################################################################################
#                   Assets
####################################################################################################
@app.get("/assets/")
async def read_assets(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    return assets

@app.get("/assets/value")
async def value_of_assets(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    somme = 0
    for asset in assets.values() : 
        print(asset)
        somme += asset.value()
    return {"total_value" : somme}

@app.get("/assets/cost")
async def cost_of_assets(token: str = Depends(oauth2_scheme)):
    try:        
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    username = payload["sub"]
    somme = 0
    for asset in assets.values() : 
        print(asset)
        somme += asset.cost()
    return {"total_value" : somme}