from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.auth.errors import register_all_errors
from app.core.config import settings
from app.core.routes import router as main_router
from app.core.middleware import register_middleware

description = """
A REST API for expense tracking.
handle all the requests for the expense tracking application.

"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    await register_all_errors(app)
    yield

app = FastAPI(title=settings.PROJECT_NAME,
              description=description,
              version=settings.VERSION,
              contact={
                  "name": "Expense Tracker Service",
                  "url": "https://expensetracker.app",
                  "email": "support@expensetracker.app",
              },
              lifespan=lifespan,
              )
version_prefix = "/api/v1"
app.include_router(main_router, prefix=version_prefix)

register_middleware(app)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Expense Tracker API!"}
