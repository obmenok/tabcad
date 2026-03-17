from dash import Input, Output, State, callback, ctx
import dash
from core.i18n import t

@callback(
    Output("lang-store", "data"),
    [Input("btn-lang-en", "n_clicks"),
     Input("btn-lang-ru", "n_clicks"),
     Input("btn-lang-cn", "n_clicks")],
    State("lang-store", "data"),
    prevent_initial_call=True
)
def set_language(n_en, n_ru, n_cn, current_lang):
    if not ctx.triggered_id:
        raise dash.exceptions.PreventUpdate

    btn_id = ctx.triggered_id
    if btn_id == "btn-lang-en":
        return "en"
    elif btn_id == "btn-lang-ru":
        return "ru"
    elif btn_id == "btn-lang-cn":
        return "cn"
    return current_lang

dash.clientside_callback(
    """
    function(lang) {
        const active = "primary";
        const inactive = "outline-primary";
        if (!lang) lang = "en";
        return [
            lang === "en" ? active : inactive,
            lang === "ru" ? active : inactive,
            lang === "cn" ? active : inactive
        ];
    }
    """,
    [Output("btn-lang-en", "color"),
     Output("btn-lang-ru", "color"),
     Output("btn-lang-cn", "color")],
    Input("lang-store", "data")
)

@callback(
    [
        Output("modal-title", "children"),
        Output("constraints-close-btn", "children"),
        Output("label-shape-title", "children"),
        Output("shape-round-btn", "children"),
        Output("shape-capsule-btn", "children"),
        Output("shape-oval-btn", "children"),
        Output("label-cup-title", "children"),
        Output("profile-btn-con", "title"),
        Output("profile-btn-com", "title"),
        Output("profile-btn-cbe", "title"),
        Output("profile-btn-ffre", "title"),
        Output("profile-btn-ffbe", "title"),
        Output("profile-btn-mod", "title"),
        Output("label-dim-title", "children"),
        Output("constraints-open-btn", "children"),
        Output("label-input-l", "children"),
        Output("label-input-re", "children"),
        Output("label-input-rs", "children"),
        Output("label-input-dc", "children"),
        Output("label-input-r-maj-maj", "children"),
        Output("label-input-r-maj-min", "children"),
        Output("label-input-r-min-maj", "children"),
        Output("label-input-r-min-min", "children"),
        Output("label-input-bev-d", "children"),
        Output("label-input-bev-a", "children"),
        Output("label-input-r-edge", "children"),
        Output("label-input-blend-r", "children"),
        Output("label-input-land", "children"),
        Output("label-input-hb", "children"),
        Output("label-input-tt", "children"),
        Output("label-input-density", "children"),
        Output("label-input-weight", "children"),
        Output("label-scoring-title", "children"),
        Output("bisect-btn-none", "children"),
        Output("bisect-btn-none", "title"),
        Output("bisect-btn-standard", "children"),
        Output("bisect-btn-standard", "title"),
        Output("bisect-btn-cut", "children"),
        Output("bisect-btn-cut", "title"),
        Output("bisect-btn-dec", "children"),
        Output("bisect-btn-dec", "title"),
        Output("bisect-edit-btn", "children"),
        Output("label-input-b-width", "children"),
        Output("label-input-b-depth", "children"),
        Output("label-input-b-angle", "children"),
        Output("label-input-b-ri", "children"),
        Output("btn-generate", "children"),
        Output("export-pdf-btn", "children"),
        Output("constraints-modified", "options"),
        Output("modified-switch", "options"),
        Output("bisect-cruciform", "options"),
        Output("bisect-double-sided", "options"),
    ],
    Input("lang-store", "data")
)
def update_texts(lang):
    return (
        t("modal.title", lang),
        t("modal.close", lang),
        t("shape.title", lang),
        t("shape.round", lang),
        t("shape.capsule", lang),
        t("shape.oval", lang),
        t("cup.title", lang),
        t("cup.con", lang),
        t("cup.com", lang),
        t("cup.cbe", lang),
        t("cup.ffre", lang),
        t("cup.ffbe", lang),
        t("cup.mod", lang),
        t("dim.title", lang),
        t("dim.constraints", lang),
        t("dim.l", lang),
        t("dim.re", lang),
        t("dim.rs", lang),
        t("dim.dc", lang),
        t("dim.r_maj_maj", lang),
        t("dim.r_maj_min", lang),
        t("dim.r_min_maj", lang),
        t("dim.r_min_min", lang),
        t("dim.bev_d", lang),
        t("dim.bev_a", lang),
        t("dim.r_edge", lang),
        t("dim.blend_r", lang),
        t("dim.land", lang),
        t("dim.hb", lang),
        t("dim.tt", lang),
        t("dim.density", lang),
        t("dim.weight", lang),
        t("scoring.title", lang),
        t("scoring.none", lang), t("scoring.none", lang),
        t("scoring.std", lang), t("scoring.std", lang),
        t("scoring.cut", lang), t("scoring.cut", lang),
        t("scoring.decr", lang), t("scoring.decr", lang),
        t("scoring.edit", lang),
        t("scoring.width", lang),
        t("scoring.depth", lang),
        t("scoring.angle", lang),
        t("scoring.ri", lang),
        t("actions.generate", lang),
        t("actions.export_pdf", lang),
        [{"label": t("cup.modified", lang), "value": True}],
        [{"label": t("cup.modified", lang), "value": True}],
        [{"label": t("scoring.cross", lang), "value": "on"}],
        [{"label": t("scoring.double", lang), "value": "on"}],
    )
