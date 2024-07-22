import os
from dotenv import load_dotenv

from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.id import ID

load_dotenv()

APPWRITE_API_KEY = os.environ["APPWRITE_API_KEY"]

client = Client()

(
    client.set_endpoint("https://cloud.appwrite.io/v1")  # Your API Endpoint
    .set_project("canvi")  # Your project ID
    .set_key(APPWRITE_API_KEY)  # Your secret API key
    .set_self_signed()  # Use only on dev mode with a self-signed SSL cert
)

users = Users(client)

result = users.create(
    ID.unique(),
    email="email@example.com",
    phone="+123456789",
    password="testing123",
    name="Walter O'Brien",
)
