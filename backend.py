import os
import uuid #every chat session needs its own unique ID
import requests#this library sends HTTP requests
from fastapi import FastAPI, HTTPException, status #Instead of crashingyou send proper errors
from pydantic import BaseModel#Pydantic validates incoming data from frontend before my function runs
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware#Since Streamlit and FastAPI run on different ports, the browser blocks communication unless CORS is enabled
from dotenv import load_dotenv
import numpy as np
import cv2#processes images
from fastapi import APIRouter, HTTPException, UploadFile, File #UploadFile Allows frontend to send photo.jpg to backend
from login import get_face_embedding, verify_embedding
from jose import jwt, JWTError #creates and verifies JWT tokens
from datetime import datetime, timedelta #datetime gets current time and timedelta sets an expiration time
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

router = APIRouter(prefix="/auth", tags=["Face Authentication"]) #FastAPI lets us group related endpoints together using an APIRouter
                                                                 #tags is just a label that keeps the documentation organized

# initialize environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
)

app = FastAPI(title="Secure AI Chatbot Backend")

# setup CORS Policy - security configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #allow requests from any website
    allow_credentials=True, #allows cookies or login credentials to be sent
    allow_methods=["*"], #allow every HTTP method
    allow_headers=["*"],
)

# 3. Setup Safe Database Connection
client = MongoClient(MONGO_URI)
db = client["chatbot_db"] #MongoDB server can contain many databases
collection = db["chat_history"] #inside one database, MongoDB stores collections
                                #every endpoint reuses this same collection object instead of reconnecting to the database
users_collection = db["users"]

class ChatMessagePayload(BaseModel): #this class represents incoming request data
    session_id: str 
    message: str



def create_access_token(data: dict): #Generates a signed JWT access token

    payload = data.copy()

    expire = datetime.utcnow() + timedelta( #calculates when the token should expire
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload.update({"exp": expire})

    token = jwt.encode( #generates jwt token, server signs is using secret key
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return token


security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode( #backend extracts jwt token
            token,
            JWT_SECRET_KEY, #verifies signature using secret key and checks whether token has expired
            algorithms=[JWT_ALGORITHM]
        )

        username = payload.get("sub") #reads username

        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return username

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

# Helper Function for OpenRouter
async def get_chatbot_reply( username: str,session_id: str, message_text: str):
    doc = collection.find_one({ #load previous chat whose session_id matches the one I received
        "session_id": session_id,
        "username": username
    })
    hist = doc.get("message", []) if doc else [] #getting the document itself and storing in hist array

    hist.append({ #newest user message stored
        "role": "user",
        "content": message_text
    })
    
    URL = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}", #This proves I have permission to use OpenRouter
        "Content-Type": "application/json"
    }
    data = { # actual request body
        "model": MODEL_NAME,
        "messages": hist
    }
    
    try:
        response = requests.post(url=URL, headers=headers, json=data) #sending request
        if response.status_code == 200:#success
            ai_reply = response.json()['choices'][0]['message']['content']
            hist.append({ #AI's answer is also added to the conversation
                "role": "assistant",
                "content": ai_reply
            })
            collection.update_one( #this updates MongoDtB
                {"session_id": session_id},
                {"$set": {"message": hist}} #replace the old message list with the updated one
            )
            return ai_reply
        else:
            return f"Error from OpenRouter (Status {response.status_code}): {response.text}"
    except Exception as e:
        return f"AI Generation Fail: {str(e)}"

# HTTP API Endpoints
@app.get("/")
async def root():
    return {"status": "Server is running smoothly!"}

@app.get("/history/{session_id}") #Switching/Loading a Past Chat Session
async def get_his(
    session_id: str,
    username: str = Depends(verify_token)
):
    doc = collection.find_one(
        {
            "session_id": session_id,
            "username": username
        },
        {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found.")
    return doc.get("message", [])

@app.get("/session") #Fetching Past Sidebar History Lists
async def get_chat_history(
    username: str = Depends(verify_token) #only authenticated users view the session list
):
    hist = collection.find({"username": username}, {"_id": 0, "session_id": 1}) #Find every document, but only return session id and a user only gets their own session IDs
    return [i["session_id"] for i in hist if "session_id" in i]

@app.post("/session", status_code=status.HTTP_201_CREATED) # starting a new chat
async def create_session(
    username: str = Depends(verify_token)
):
    session_id = str(uuid.uuid4())
    collection.insert_one({ #creates a new MongoDB document
        "username": username,
        "session_id": session_id,
        "message": [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Remember everything the user tells you."
            }
        ]
    })
    return {"session_id": session_id}

@app.post("/message") #endpoint your Streamlit app calls every time you press Send
async def getreply(
    m: ChatMessagePayload,
    username: str = Depends(verify_token) #Before running this endpoint, first verify the JWT
):
    y = await get_chatbot_reply(username,m.session_id, m.message)
    return {"e": y} #sends ai response back to the frontend






@router.post("/register-face/{username}")
async def register_face(username: str, file: UploadFile = File(...)): # 2 things are coming from frontend: username and image captured by the webcam
    try:
        print("STEP 1")

        contents = await file.read() #this reads the uploaded file which is in the form of bytes into memory
        nparr = np.frombuffer(contents, np.uint8) #this converts the uploaded bytes into a NumPy array
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR) #OpenCV converts those bytes into an actual image, frame contains image matrix and size

        embedding = get_face_embedding(frame) # Generate a 512-dimensional AI embedding that uniquely represents this face

        print("STEP 4")

        if embedding is None:
             raise HTTPException(status_code=400, detail="No face embedding generated.")

        
        embedding_list_for_db = embedding.tolist() #NumPy Array to Python List
                                                    #MongoDB cannot serialize NumPy arrays, so I convert the face embedding into a regular Python list before storing it
        print("STEP 5")

        users_collection.update_one(
            {"username": username},
            {
                "$set": {
                    "username": username,
                    "face_embedding": embedding_list_for_db
                }
            },
            upsert=True
       )

        print("STEP 6")

        return {
            "status": "success",
            "message": "Registration Complete"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login-face/{username}")
async def login_face(username: str, file: UploadFile = File(...)):
    """Automatically triggered by frontend to verify a user's identity."""

    user_record = users_collection.find_one({"username": username}) #Go to MongoDB and Find this user
    if not user_record or "face_embedding" not in user_record:
        raise HTTPException(status_code=404, detail="User or face profile not found.")
    
    saved_embedding = np.array(user_record["face_embedding"], dtype=np.float32)
    
    # Process the incoming live login frame snapshotcd
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR) #Now we have the new image.
    
    live_embedding = get_face_embedding(frame)

    if live_embedding is None:
          raise HTTPException(
              status_code=400,
              detail="Face tracking lost. Position your face in view."
          )
     
    
   
        
    
    
    # Run your verification logic function!
    is_valid = verify_embedding(live_embedding, saved_embedding, threshold=0.60)
    
    if is_valid:
        # Generate your chatbot JWT access token here
        token = create_access_token(
            {"sub": username}
        )
        return {"status": "authenticated", "token": token}
    else:
        raise HTTPException(status_code=401, detail="Authentication failed. Face biometric mismatch.")
    
app.include_router(router) #Take all the endpoints inside this router and add them to my main application

