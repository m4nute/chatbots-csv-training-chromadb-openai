from fastapi import FastAPI, Depends, HTTPException, Request, status, Query, File, UploadFile, Form
from sqlalchemy.orm import sessionmaker, Session, joinedload
from os import environ as env
from .database import SessionLocal, get_db, Base, engine
from .models import Client, Chatbot
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
import concurrent.futures
import math
import tempfile
import chromadb
from .gpt import ask_openai
from typing import List, Annotated
from sqlalchemy import func
import asyncio
from .insert_csv import get_csv_embeddings

app = FastAPI()
chroma_client = chromadb.HttpClient(host='chroma', port=8000)
Base.metadata.create_all(bind=engine)

su_token = env['SUPERUSER_TOKEN']

@app.middleware('http')
async def token_protection(request: Request, call_next):
    authorization_header = request.headers.get("Authorization")
    if request.url.path.startswith('/client'):
        if authorization_header != f"Bearer {su_token}":
            return JSONResponse(content={"detail": "Unauthorized"}, status_code=401)
    response = await call_next(request)
    return response


@app.get("/clear")
async def clear_db():
    chroma_client.reset()

@app.get("/heartbeat")
async def heartbeat():
    return chroma_client.heartbeat()

@app.post("/client/create")
async def create_client(name: str = Form(...), max_bots_allowed: int = Form(...), db: Session = Depends(get_db)):
    db_client = Client(name=name, max_bots_allowed=max_bots_allowed)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@app.get("/bots")
async def get_bots(request: Request, db: Session = Depends(get_db)):
    if request.headers.get("Authorization") == None or len(request.headers.get("Authorization").split(" ")) != 2:
        return JSONResponse(content={"detail": "Unauthorized"}, status_code=401)
    auth = request.headers.get("Authorization").split(" ")[1]
    auth_client = db.query(Client).filter(Client.token == auth).first()
    if not auth_client:
        return JSONResponse(content={"detail": "Unauthorized"}, status_code=401)

    chatbots = db.query(Chatbot).join(Client).filter(Client.clientId == auth_client.clientId).all()
    return {"chatbots": chatbots}

@app.get("/clients")
async def get_clients(page: int = Query(default=1, description="Page number", gt=0),perPage: int= Query(default=10, description="Clients per page", gt=0, le=100), db: Session = Depends(get_db)):
    query = db.query(Client)
    total = query.count()
    query = query.limit(perPage).offset((page -1) * perPage)
    results = query.all()
    total_pages = math.ceil(total / perPage)
    return {"clients": results, "totalItems": total, "totalPages": total_pages, "page": page, "perPage": perPage}

@app.get("/client/{clientId}")
async def get_client(clientId, db: Session = Depends(get_db)):
    client = db.query(Client).filter_by(clientId=clientId).first()
    return {"client": client}

class BotInfo(BaseModel):
    name: str

@app.post("/bot/create")
async def create_bot(request: Request, name: Annotated[str, Form()], db: Session = Depends(get_db)):
    if request.headers.get("Authorization") == None or len(request.headers.get("Authorization").split(" ")) != 2:
        return JSONResponse(content={"detail": "Unauthorized"}, status_code=401)

    auth = request.headers.get("Authorization").split(" ")[1]
    client = db.query(Client).filter(Client.token == auth).first()

    if not client:
        return JSONResponse(content={"detail": "Unauthorized"}, status_code=401)

    chatbot_count = db.query(func.count()).filter(Chatbot.clientId == client.clientId).scalar()

    if chatbot_count >= client.max_bots_allowed:
        return JSONResponse(content={"detail": "Client has reached maximum amount of chatbots"}, status_code=400)

    db_chatbot = Chatbot(name=name, client=client)
    db.add(db_chatbot)
    db.commit()
    db.refresh(db_chatbot)
    return {"chatbot" : db_chatbot}

def process_file(db, token, auth, file_contents, source_id):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file_contents)
        tmp_file_path = tmp_file.name
    
    embeddings = get_csv_embeddings(tmp_file_path, source_id)
    collection = chroma_client.get_or_create_collection(token)
    collection.delete(
        where={"source": source_id}
    )
    collection.add(
        documents=embeddings['documents'], metadatas=embeddings['metadatas'], ids=embeddings['ids']
    )

@app.post("/bot/ingest")
async def upload_file(request: Request, token: Annotated[str, Form()], source_id: Annotated[str, Form()], file: UploadFile = File(...), db: Session = Depends(get_db)):
    if request.headers.get("Authorization") == None or len(request.headers.get("Authorization").split(" ")) != 2:
        return JSONResponse(content={"detail": "Unauthorized"}, status_code=401)
    auth = request.headers.get("Authorization").split(" ")[1]
    
    chatbot = db.query(Chatbot).filter_by(token=token).options(joinedload(Chatbot.client)).first()
    if not chatbot or not chatbot.client or auth != chatbot.client.token:
        return JSONResponse(content={"detail": "Unauthorized"}, status_code=401)


    file_contents = await file.read()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        await asyncio.to_thread(process_file, db, chatbot.token, auth, file_contents, source_id)
    
    return {"detail": "Embeddings added to chroma!"}


class BotQuery(BaseModel):
    body: str
    bot_token: str = Field(None)
    auth_token: str = Field(None)
    chat_context: List
    
@app.post("/bot/query")
async def query(request: Request, params: BotQuery, auth_token: str = '', bot_token: str = '', db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization").split(" ")[1] if request.headers.get("Authorization") and len(request.headers.get("Authorization").split(" ")) == 2 else (params.auth_token if params.auth_token else auth_token)

    if not auth:
        return JSONResponse(content={"detail": "Unauthorized"}, status_code=401)

    bot_token = params.bot_token if params.bot_token else bot_token
    chatbot = db.query(Chatbot).filter_by(token=bot_token).options(joinedload(Chatbot.client)).first()
    if not chatbot or auth != chatbot.client.token:
        return JSONResponse(content={"detail": "Unauthorized"}, status_code=401)

    user_prompt = params.body
    user_prompt += "Do not answer questions that are not related with the context. Don't justify your answers."
    chat_context = params.chat_context[-5:]
    chat_context.append({"role": "user", "content": user_prompt})
    results = chroma_client.get_or_create_collection(bot_token).query(
            include=["documents", "metadatas", "distances"],
            query_texts=[user_prompt],
            n_results=1
        )
    if not results['distances'][0][0] <= 0.75:
        return {"body": "I don't know the answer to that question. Please ask me something else.", "attach": ""}
        
    system_prompt = f"You are a virtual assistant that has to answer questions based on this context: ### {results['documents'][0][0]} ###"

    response = ask_openai(system_prompt, chat_context)
    response_data = {"body": response, "attach": ""}
    return response_data

    