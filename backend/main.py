from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_service import answer_resume_question
from database import Base, engine, get_db
from models import ChatMessage
from schemas import ChatMessageOut, ChatRequest, ChatResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Portfolio AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    db.add(ChatMessage(role="user", content=payload.question))
    db.commit()

    answer, model = await answer_resume_question(payload.question)

    db.add(ChatMessage(role="assistant", content=answer))
    db.commit()

    return ChatResponse(answer=answer, model=model)


@app.get("/api/chat/history", response_model=list[ChatMessageOut])
def history(db: Session = Depends(get_db)):
    result = db.execute(select(ChatMessage).order_by(ChatMessage.created_at.asc())).scalars()
    return list(result)
