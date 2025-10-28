from fastapi import FastAPI
from fastapi.testclient import TestClient

app=FastAPI()

@app.get('/hello')
def read_hello():
    return {"msg":"hello world"}

client=TestClient(app)

def test_read_hello():
    response=client.get("/hello")
    assert response.status_code==200
    assert response.json()=={"msg":"hello world"}

