#Pytest
import pytest
# Code to test
from main import create_access_token, authenticate_user,secret_key
#Utils
import jwt
from datetime import datetime, timedelta
import pytz

# Constants
CH_timezone = pytz.timezone('Europe/Zurich')


@pytest.mark.parametrize("username", [
    "",
    2222,
    None,
    "Never odd or even",
    "Do geese see God?",
])

def test_create_access_token(username):
    # Test case 1: Verify that the function returns a JWT token
    data = {"sub": username}
    token = create_access_token(data)
    assert isinstance(token, str)

    # Test case 2: Verify that the token can be decoded using the same secret key
    decoded_data = jwt.decode(token, secret_key, algorithms=["HS256"])
    assert decoded_data["sub"] == username

    # Test case 3: Verify that the "exp" claim in the token is set correctly
    expires_delta = timedelta(minutes=30)
    token = create_access_token(data, expires_delta=expires_delta)
    decoded_data = jwt.decode(token, secret_key, algorithms=["HS256"])
    expire_timestamp = decoded_data["exp"]
    expected_expire = datetime.now(CH_timezone) + expires_delta
    assert int(expire_timestamp) == int(expected_expire.timestamp())

    # Test case 4: Verify that the default expiration time is 15 minutes
    token = create_access_token(data)
    decoded_data = jwt.decode(token, secret_key, algorithms=["HS256"])
    expire_timestamp = decoded_data["exp"]
    expected_expire = datetime.now(CH_timezone) + timedelta(minutes=15)
    assert int(expire_timestamp) == int(expected_expire.timestamp())

@pytest.mark.parametrize("username,password,expected_output", [
    ("test","test", True),
    ("test","invalidpwd", False),
    ("nonexistentuser","test", False),
    ("","test", False),
    ("test","", False),
    (None,None, False),
    (None,"None", False),
    ("None",None, False),    
])

def test_authenticate_user_valid(username,password,expected_output):
    assert authenticate_user(username, password) == expected_output




"""pytest.fixture
def example_fixture():
    return 1

def test_with_fixture(example_fixture):
    assert example_fixture == 1
"""
