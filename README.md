
# Asset Vision API

Asset Vision API is a RESTful API for managing portfolios using FastAPI and MongoDB Atlas. 
The API allows users to create, read, update, and delete assets and portfolios, and uses JSON Web Tokens (JWT) for authentication. 
The API is deployed on Google Cloud Run and uses Google secrets to protect any credentials used in the project.



## Requirements

-   uvicorn
-   gunicorn
-   fastapi
-   pydantic
-   pyjwt
-   python-multipart
-   pymongo
-   google-cloud-secret-manager==2.10.0
-   pytz
-   bcrypt

## You can test the API here : 

[API Vision](https://asset-vision-api-zznkesfula-oa.a.run.app/) on Google Cloud

## How to run the API

1.  Clone this repository to your local machine.
2.  Either link to your google secrets, ot setup your connection string  to your MongoDB Atlas in the Mongo client parameters.
3.  Install the required packages by running `pip install -r requirements.txt`.
4.  Launch the API using the command `uvicorn main:app --reload`.
    

## API Endpoints
The API consists of the following endpoints:
### Documentation
-  **`/docs`**: This endpoint allows you to get all the infos you need.
### Authentification
-  **`/login`**: This endpoint allows you to authenticate a user on the API.
    - **POST** : Login
-  **`/sample_secured`**: This endpoint allows you to test that the authentification is working.
    - **GET** : Test secured endpoint
### Users Endpoints
-  **`/user`**: This endpoint allows you to create, read, update, and delete users.
    - **POST** /user: Create a new user.
    - **GET** /user/{username}: Retrieve a user by username.
    - **PUT** /user/{username}: Update a user by username.
    - **DELETE** /user/{username}: Delete a user by username.
- **`/users`**: This endpoint allows you to read all available users.
    - **GET** /users: Retrieve all users.
### Assets Endpoints
-  **`/asset`**: This endpoint allows you to create, read, update, and delete assets.
    - **POST** /asset: Create a new asset.
    - **GET** /asset/{asset_symbol}: Retrieve an asset by symbol.
    - **PUT** /asset/{asset_symbol}: Update an asset by symbol.
    - **DELETE** /asset/{asset_symbol}: Delete an asset by symbol.
- **`/assets`**: This endpoint allows you to read all available assets.
    - **GET** /assets: Retrieve all assets.
### Rates Endpoints
-  **`/rate`**: This endpoint allows you to create, read, update, and delete rates.
    - **POST** /rate: Create a new rate.
    - **GET** /rate/{rate_symbol}: Retrieve a rate by symbol.
    - **PUT** /rate/{rate_symbol}: Update a rate by symbol.
    - **DELETE** /rate/{rate_symbol}: Delete a rate by symbol.
- **`/rates`**: This endpoint allows you to read all available rates.
    - **GET** /rates: Retrieve all rates.
### Portfolio Endpoints
-  **`/portfolio`**: This endpoint allows you to create, read, update, and delete portfolios.
    - **POST** /portfolio: Create a new portfolio.
    - **GET** /portfolio/{portfolio_name}/value: Retrieve the portfolio by name and calculate its value in the portfolio base currency. 
    - **GET** /portfolio/{portfolio_name}/assets: Retrieve all the assets inside the portfolio. 
    - **GET** /portfolio/{portfolio_name}/cost: Retrieve the buying price of the portfolio. (**WIP** : Make it by asset_class)
    - **GET** /portfolio/{portfolio_name}/total_return: Calculate the return made on the portfolio.
    - **GET** /portfolio/{portfolio_name}/return_by_asset_class: Calculate the return made on the portfolio by asset class.
    - **GET** /portfolio/{portfolio_name}/buy/{symbol}: Buy an asset in the portfolio. 
    - **GET** /portfolio/{portfolio_name}/sell/{symbol}: Sell an asset in the portfolio.
    - **PUT** /portfolio/{portfolio_name}: Update an rate by name. (**WIP**)
    - **DELETE** /portfolio/{portfolio_name}: Delete an rate by name. (**WIP**)
- **`/portfolios`**: This endpoint allows you to read all available portfolios. (**WIP**)
    - **GET** /portfolios: Retrieve all portfolios. (**WIP**)

## Contribution Guidelines
We welcome contributions from the community! If you'd like to contribute to the project, please follow these guidelines:

-   Fork the repository and clone it to your local machine.
-   Create a new branch for your feature or bug fix.
-   Write your code and tests.
-   Run the tests using pytest.
-   Make a pull request with a description of your changes.

Please ensure that your code follows the existing style and formatting conventions, and that it includes appropriate tests. If you're unsure about anything, please don't hesitate to ask for help!

## Security

The API uses JSON Web Tokens (JWT) for authentication.
The API is deployed on Google Cloud Run is using Google secrets to protect any credentials used in the project.

## Database

The API uses MongoDB Atlas for storing its data.