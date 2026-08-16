from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config.paths import TEMPLATES_DIR
from app.web.charts import (
    candlestick_chart,
    candlestick_chart_omits_older_entries,
    score_chart,
    signal_distribution_chart,
)
from app.web.dashboard_data import load_dashboard_data
from app.web.live_status_data import load_live_status


app = FastAPI(

    title="Project Audo",

    version="1.0.0",

)

templates = Jinja2Templates(

    directory=TEMPLATES_DIR

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


@app.get("/live", response_class=HTMLResponse)
def live_status(request: Request):

    data = load_live_status()

    return templates.TemplateResponse(

        request=request,

        name="live.html",

        context={
            "request": request,
            "candlestick_chart": candlestick_chart(
                data["chart_decisions"]
            ),
            "candlestick_omits_older_entries": candlestick_chart_omits_older_entries(
                data["chart_decisions"]
            ),
            "score_chart": score_chart(
                data["chart_decisions"]
            ),
            "signal_distribution_chart": signal_distribution_chart(
                data["decisions"]
            ),
            **data,
        },

    )