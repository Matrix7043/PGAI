from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    content: str
    reference: str
    title: str


async def validate_item(item: Item):
    if item.content.__len__() > 100:
        raise HTTPException(202, detail="content <= 100")
    if item.reference.__len__() > 30:
        raise HTTPException(202, detail="reference <= 30")
    if item.title.__len__() > 10:
        raise HTTPException(202, detail="title <= 10")
    return item


@app.post("/content")
async def getrequest(item: Item = Depends(validate_item)):
    return {"message": "Success", "Item": item}


@app.get("/")
async def root():
    return {"message": "Hello from server"}
