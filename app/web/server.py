from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.web.dashboard_data import load_dashboard_data


app = FastAPI(

    title="Project Audo",

    version="1.0.0",

)

templates = Jinja2Templates(

    directory=Path("app/web/templates")

)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    data = load_dashboard_data()

    return templates.TemplateResponse(

        request=request,

        name="index.html",

        context={
            "request": request,
            **data,
        },

    )