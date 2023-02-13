
# Asset Vision API

A RESTful API for managing portfolios using FastAPI and MongoDB Atlas.

## Requirements

-   uvicorn
-   fastapi
-   pydantic
-   pyjwt
-   python-multipart
-   pymongo[snappy,gssapi,srv,tls]

## How to run the API

1.  Clone this repository to your local machine.
2.  Setup your Configuration.py file with your connection string to your MongoDB Atlas.
3.  Install the required packages by running `pip install -r requirements.txt`.
4.  Launch the API using the command `uvicorn main:app --reload`.
    

## API Endpoints

The API consists of the following endpoints:

-  `/docs`: This endpoint allows you to get all the infos you need.

- `/asset`: This endpoint allows you to create, read, update, and delete assets.

- `/assets`: This endpoint allows you to read all available assets.
    
-  `/portfolio`: This endpoint allows you to create, read, update, and delete portfolios.
    

## Security

The API uses JSON Web Tokens (JWT) for authentication.

## Database

The API uses MongoDB Atlas for storing its data.