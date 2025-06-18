from fastapi import FastAPI
from console_link.api.metadata import metadata_router
from console_link.api.clusters import router as cluster_router

app = FastAPI(
    title="Migration Assistant API",
    version="0.0.1"
)

app.include_router(metadata_router)
app.include_router(cluster_router)
