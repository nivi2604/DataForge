from fastapi import FastAPI

app = FastAPI(title="DataForge API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "DataForge API"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
