import base64
from fastapi import FastAPI, Depends, HTTPException, status, Request
from model import Item, ItemModel, get_db, Base, engine

app = FastAPI()

# create table
Base.metadata.create_all(bind=engine)


def read_token(file_path="/tmp/access_token.txt"):
    try:
        with open(file_path, "r") as file:
            access_token = file.read()
        return access_token
    except IOError as e:
        print(f"Error reading from file: {e}")
        return None


def get_custom_api_key(request: Request):
    api_key = request.headers.get("api-key")
    token = read_token()
    if api_key == token:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
    )


def get_bearer_api_key(request: Request):
    authorization: str = request.headers.get("Authorization")
    print(f"authorization: {authorization}")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
        )

    prefix = "Bearer"
    if authorization.startswith(prefix):
        api_key = authorization[len(prefix) :].strip()
        token = read_token()
        if api_key == token:
            return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
    )


def get_basic_api_key(request: Request):
    authorization: str = request.headers.get("Authorization")
    print(f"authorization: {authorization}")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
        )

    prefix = "Basic"
    if authorization.startswith(prefix):
        base64_api_key = authorization[len(prefix) :].strip()
        api_key = base64.b64decode(base64_api_key).decode("utf-8").strip()
        token = read_token()
        if api_key == token:
            return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
    )


# Async read Item from database
async def get_item_by_id(db, item_id: int):
    return db.query(ItemModel).filter(ItemModel.id == item_id).first()


# Async create Item to database
async def save_item(db, item: Item):
    db_item = ItemModel(
        name=item.name, description=item.description, price=item.price, tax=item.tax
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/items/{item_id}", dependencies=[Depends(get_bearer_api_key)])
async def read_item(item_id: int, db=Depends(get_db)):
    db_item = await get_item_by_id(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.post("/items/", dependencies=[Depends(get_bearer_api_key)])
async def create_item(item: Item, db=Depends(get_db)):
    return await save_item(db, item)
