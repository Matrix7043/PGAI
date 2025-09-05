from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from .workflow import run_workflow

app = FastAPI()


class Item(BaseModel):
    content: str
    reference: str
    title: str


async def validate_item(item: Item):
    if item.content.__len__() > 150:
        raise HTTPException(202, detail="content <= 150")
    if item.reference.__len__() > 30:
        raise HTTPException(202, detail="reference <= 80")
    if item.title.__len__() > 12:
        raise HTTPException(202, detail="title <= 12")
    return item


@app.post("/content")
async def getrequest(item: Item = Depends(validate_item)):
    try:
        run_workflow(item.content, item.reference, item.title)
    except Exception as e:
        raise HTTPException(202, detail=f"Post Generation failed: {e}")

    return {"message": "Success", "Item": item}


@app.get("/")
async def root():
    return {"message": "Hello from server"}
