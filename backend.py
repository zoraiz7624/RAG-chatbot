from fastapi  import FastAPI ,UploadFile, File
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
import requests
import uuid
import os
from dotenv import load_dotenv
import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain

from langchain_core.output_parsers import StrOutputParser
from faster_whisper import WhisperModel
import tempfile
from fastapi.staticfiles import StaticFiles

from fastapi import Request, Response
import auth

app = FastAPI()

os.makedirs("replies", exist_ok=True)
app.mount("/replies", StaticFiles(directory="replies"), name="replies")
load_dotenv()

#pip install sentence-transformersGrab the hidden variables using os.getenv
MONGO_URI = os.getenv("MONGO_URI")
API_KEY = os.getenv("OPENAI_API_KEY")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



clinet=MongoClient(MONGO_URI)
db=clinet["chatbot_db"]
collection = db["chat_history"]

users_collection = db["users"]
sessions_collection = db["sessions"]
os.makedirs("face_uploads", exist_ok=True)

#GET
# -------server start here
@app.get("/")
async def root():
    return {"status": "Server is running! Go to /docs to test your API."}

# -------server ends here
@app.get("/session")
async def get_chat_history(username: str | None = None):
     hist = collection.find({"username": username}, {"_id": 0, "session_id": 1})
     return [i["session_id"] for i in hist]



@app.post("/session")
async def session(username: str | None = None):
     session_id = str(uuid.uuid4())
     collection.insert_one({
          "session_id": session_id,
          "username": username,
          "message":
            [{"role": "system", "content": "You are a helpful AI assistant."}]
     })
     print("Created session:", session_id, "for", username)
     return {"session_id": session_id, "username": username}


# -------get_his start here return the list of sessions

@app.get("/history/{session_id}")
async def get_his(session_id: str, username: str | None = None):
     doc = collection.find_one({"session_id": session_id}, {"_id": 0})
     if not doc:
         return {"error": "Session not found"}

     if doc.get("username") and doc["username"] != username:
         return {"error": "Not your session"}

     return doc["message"]



# -------get_his start here return the list of sessions


class RegisterBody(BaseModel):
    username: str
    password: str


class LoginBody(BaseModel):
    username: str
    password: str

#------------------------------------POST

#---------------------------------session id is given here plus the new system setting every
#time a new chat is started this run




#---------------------session id ends here

#--------------------------chat bot starts here


class reply(BaseModel):
    session_id:str 
    message:str

async def get_chatbot_reply(session_id:str, message: str):
    doc=collection.find_one({"session_id":session_id})
    print(doc)
    if doc:
      hist=doc["message"]
    else:
         hist=[]

    hist.append({
        "role": "user",
        "content": message
    })
    OPENROUTER_API_KEY = API_KEY  
    MODEL_NAME = "tencent/hy3:free"
    URL = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": hist
    }
    response = requests.post(
            url=URL,
            headers=headers,
            json=data
        )
       
    if response.status_code == 200:
            ai_reply = response.json()['choices'][0]['message']['content']
            hist.append({
                "role": "assistant",
                "content": ai_reply
            })
            collection.update_one({"session_id":session_id},
                                   {"$set":{"message":hist}}
                                   )
            return ai_reply
    else:
            return f"Error from OpenRouter (Status {response.status_code}): {response.text}"

async def rag(input:str):
     vector_db=FAISS.load_local("vector_db",HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),allow_dangerous_deserialization=True)
     context =vector_db.as_retriever(search_kwargs={"k":5})
     
     llm=ChatOpenAI(model="tencent/hy3:free",api_key=API_KEY,base_url="https://openrouter.ai/api/v1")
     promt=ChatPromptTemplate.from_template("""
     You are a helpful AI assistant.

    Use ONLY the information provided in the context below to answer the user's question.

    If the answer cannot be found in the context, reply:
    "I couldn't find the answer in the provided documents."

    Keep your answer clear, concise, and accurate.

    Context:
    {context}

    Question:
    {input}

    Answer:
    """)
     qc=create_stuff_documents_chain(llm,promt)
     rag=create_retrieval_chain(context ,qc)
     res=rag.invoke({"input":input})
     
     return res["answer"]
     

router_llm = ChatOpenAI(
    model="tencent/hy3:free",
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

router_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a routing classifier for a chatbot with access to uploaded documents.\n"
     "Decide if the user's message needs to look something up in those documents.\n\n"
     "Reply with EXACTLY one word, nothing else: rag or chat\n\n"
     "- rag: the user is asking about specific facts, data, or content that would "
     "live in an uploaded document (reports, policies, named details, 'what does the doc say about...').\n"
     "- chat: greetings, small talk, opinions, general knowledge, or anything unrelated to the documents."),
    ("human", "{question}")
])

router_chain = router_prompt | router_llm | StrOutputParser()

async def router(q:str):
     raw = await router_chain.ainvoke({"question": q})
     decision = raw.strip().lower()
     return "rag" if "rag" in decision else "chat"
        



@app.post("/message")
async def getreply(m: reply):
    decision=await router(m.message)

    if decision == "rag":
        y = await rag(m.message)  
    else:
        y = await get_chatbot_reply(m.session_id, m.message)

    return {"e": y, "debug_route": decision}

#--------------------------chat bot end here

#------------------vioce feaature

whisper_model=WhisperModel("base",device="cpu",compute_type="int8")
@app.post("/voice")
async def type_the_vioce_promt(f:UploadFile=File(...)):
     with tempfile.NamedTemporaryFile(suffix=".wav",delete=False) as temp:
      temp.write(await f.read())
     seg, _=whisper_model.transcribe(temp.name)
     tesxt=" ".join(s.text for s in seg).strip()
     os.remove(temp.name)
     return {"text":tesxt}

import pyttsx3
engine = pyttsx3.init()
def text_to_speech(text: str, out_path: str):
    engine.save_to_file(text, out_path)
    engine.runAndWait()

@app.post("/voice_message")
async def get_vioce_reply(m: reply):
    decision=await router(m.message)

    if decision == "rag":
        y = await rag(m.message)  
    else:
        y = await get_chatbot_reply(m.session_id, m.message)
    os.makedirs("replies", exist_ok=True)
    audio_path = f"replies/{uuid.uuid4()}.mp3"
    text_to_speech(y, audio_path)

    return {"e": y, "audio_url": f"/replies/{os.path.basename(audio_path)}"}


#--------------------end vioce feature


#--------------------------file upload starts here
file="rag_doc"
os.makedirs(file,exist_ok=True)
async def upl_file(f:UploadFile=File(...)):
    if f.content_type!="application/pdf":
        return {"error":" not a pdf"}
    
    file_path=os.path.join(file,f.filename)

    with open(file_path,"wb") as buffer:
         shutil.copyfileobj(f.file,buffer)
    
    await pre_rag(file_path)

    return{f.filename:"mission complete sucess"}

#-------pre rag
async def pre_rag(f:str):
     loadedpdf=PyPDFLoader(f)
     doc=loadedpdf.load()
     sp=RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=100)
     chunk=sp.split_documents(doc)
     embedding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
     vector_db=FAISS.from_documents(documents=chunk,embedding=embedding)
     vector_db.save_local("vector_db")
     return 

     
    
@app.post("/upload")
async def up(f:UploadFile=File(...)):
     y=await upl_file(f)
     return y




#--------------------------file upload ends here

@app.post("/auth/register")
async def register(body: RegisterBody):
    if users_collection.find_one({"username": body.username}):
        return {"error": "Username already taken"}

    users_collection.insert_one({
        "username": body.username,
        "password": body.password
    })

    return {
        "status": "registered",
        "username": body.username,
        "success": True
    }


@app.post("/auth/login")
async def login(body: LoginBody):
    user = users_collection.find_one({"username": body.username})

    if user is None:
        return {"error": "Invalid username or password"}

    if user["password"] != body.password:
        return {"error": "Invalid username or password"}

    return {
        "status": "logged in",
        "username": body.username,
        "success": True
    }

@app.post("/auth/login-face")
async def login_face(f: UploadFile = File(...)):
    temp_path = os.path.join("face_uploads", f"{uuid.uuid4()}_{f.filename}")

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(f.file, buffer)

    try:
        embedding = auth.get_face_embedding(temp_path)
    except ValueError as e:
        os.remove(temp_path)
        return {"error": str(e)}

    os.remove(temp_path)

    username, score = auth.find_matching_user(embedding, users_collection)

    if not username:
        return {
            "error": "No matching face found",
            "best_score": score
        }

    return {
        "status": "logged in",
        "username": username,
        "match_score": score,
        "success": True
    }

@app.post("/auth/register-face")
async def register_face(username: str, f: UploadFile = File(...)):
    user = users_collection.find_one({"username": username})
    if not user:
        return {"error": "No account with that username. Register with a password first."}

    os.makedirs("face_uploads", exist_ok=True)
    temp_path = os.path.join("face_uploads", f"{uuid.uuid4()}_{f.filename}")

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(f.file, buffer)

    try:
        embedding = auth.get_face_embedding(temp_path)
    except ValueError as e:
        os.remove(temp_path)
        return {"error": str(e)}

    os.remove(temp_path)

    users_collection.update_one(
        {"username": username},
        {"$set": {"face_embedding": embedding}}
    )

    return {"status": "face registered", "username": username, "success": True}
