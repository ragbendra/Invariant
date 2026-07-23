from fastapi import FastAPI

app = FastAPI(title="Blog App")


@app.get("/health")
def health_check():
    return {"status": "ok"}
