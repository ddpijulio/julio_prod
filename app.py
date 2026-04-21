from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path

try:
    import altair as alt
except ImportError:  # pragma: no cover
    alt = None

import pandas as pd
import streamlit as st


DEFAULT_FILE = "Sistema_Productividad_JC_PLANTILLA_EJEMPLO.xlsx"
CAPACIDAD_RECOMENDADA = 6.0
ESTADOS_CERRADOS = {"terminado", "hecho", "cerrado"}
ALERT_COLUMNS = [
    "ID_Subtarea",
    "Subtarea",
    "Proyecto",
    "Tarea",
    "Estado",
    "Prioridad",
    "Fecha limite",
]

PRIORITY_ORDER = {"Alta": 0, "Media": 1, "Baja": 2}
MONTH_NAMES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]
STATUS_COLORS = {
    "En proceso": "#f59e0b",
    "No iniciado": "#94a3b8",
    "En espera": "#ef4444",
    "Terminado": "#16a34a",
    "Hecho": "#16a34a",
    "Pendiente": "#f97316",
}
PRIORITY_COLORS = {"Alta": "#dc2626", "Media": "#d97706", "Baja": "#2563eb"}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def is_yes(value: object) -> bool:
    return normalize_text(value).lower() in {"si", "sí", "s", "yes", "true", "1"}


def is_closed(value: object) -> bool:
    return normalize_text(value).lower() in ESTADOS_CERRADOS


def priority_rank(value: object) -> int:
    return PRIORITY_ORDER.get(normalize_text(value), 9)


def find_default_excel() -> str:
    default_path = Path(DEFAULT_FILE)
    if default_path.exists():
        return str(default_path)

    excel_files = sorted(Path(".").glob("*.xlsx"))
    if excel_files:
        return str(excel_files[0])
    return DEFAULT_FILE


@st.cache_data(show_spinner=False)
def load_excel_data(path: str) -> dict[str, pd.DataFrame]:
    sheets = {
        "Proyectos": pd.read_excel(path, sheet_name="Proyectos"),
        "Tareas": pd.read_excel(path, sheet_name="Tareas"),
        "Subtareas": pd.read_excel(path, sheet_name="Subtareas"),
        "Inbox_Diario": pd.read_excel(path, sheet_name="Inbox_Diario"),
    }

    projects = sheets["Proyectos"].copy()
    tasks = sheets["Tareas"].copy()
    subtasks = sheets["Subtareas"].copy()
    inbox = sheets["Inbox_Diario"].copy()

    for df in (projects, tasks, subtasks, inbox):
        df.columns = [normalize_text(col) for col in df.columns]

    for column in ["Fecha_objetivo"]:
        if column in projects:
            projects[column] = pd.to_datetime(projects[column], errors="coerce")
        if column in tasks:
            tasks[column] = pd.to_datetime(tasks[column], errors="coerce")

    if "Fecha_limite_opcional" in subtasks:
        subtasks["Fecha_limite_opcional"] = pd.to_datetime(
            subtasks["Fecha_limite_opcional"], errors="coerce"
        )

    if "Fecha" in inbox:
        inbox["Fecha"] = pd.to_datetime(inbox["Fecha"], errors="coerce")

    numeric_columns = {
        "projects": ["Avance %", "Pendientes", "Hoy_recibidos", "Hoy_cerrados"],
        "subtasks": ["Duracion_estimada", "Duracion_real"],
    }

    for column in numeric_columns["projects"]:
        if column in projects:
            projects[column] = pd.to_numeric(projects[column], errors="coerce")

    for column in numeric_columns["subtasks"]:
        if column in subtasks:
            subtasks[column] = pd.to_numeric(subtasks[column], errors="coerce")

    tasks = tasks.merge(
        projects[["ID_Proyecto", "Proyecto", "Tipo_Proyecto"]],
        on="ID_Proyecto",
        how="left",
    )

    subtasks = subtasks.merge(
        tasks[
            [
                "ID_Tarea",
                "ID_Proyecto",
                "Tarea",
                "Tipo_Tarea",
                "Estado",
                "Prioridad",
                "Fecha_objetivo",
            ]
        ].rename(
            columns={
                "Estado": "Estado_Tarea",
                "Prioridad": "Prioridad_Tarea",
                "Fecha_objetivo": "Fecha_objetivo_tarea",
            }
        ),
        on="ID_Tarea",
        how="left",
    )

    subtasks = subtasks.merge(
        projects[
            [
                "ID_Proyecto",
                "Proyecto",
                "Tipo_Proyecto",
                "Estado",
                "Prioridad",
                "Avance %",
                "Fecha_objetivo",
                "Pendientes",
                "Hoy_recibidos",
                "Hoy_cerrados",
            ]
        ].rename(
            columns={
                "Estado": "Estado_Proyecto",
                "Prioridad": "Prioridad_Proyecto",
                "Fecha_objetivo": "Fecha_objetivo_proyecto",
            }
        ),
        on="ID_Proyecto",
        how="left",
    )

    inbox = inbox.merge(
        subtasks[
            [
                "ID_Subtarea",
                "Subtarea",
                "ID_Tarea",
                "Tarea",
                "ID_Proyecto",
                "Proyecto",
                "Tipo_Proyecto",
            ]
        ],
        on="ID_Subtarea",
        how="left",
    )

    return {
        "Proyectos": projects,
        "Tareas": tasks,
        "Subtareas": subtasks,
        "Inbox_Diario": inbox,
    }


def format_date(value: object) -> str:
    if pd.isna(value):
        return "-"
    return pd.to_datetime(value).strftime("%d/%m/%Y")


def format_hours(value: float) -> str:
    if pd.isna(value):
        return "0 h"
    return f"{value:.1f} h"


def empty_table(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(14, 165, 233, 0.10), transparent 28%),
                radial-gradient(circle at top right, rgba(249, 115, 22, 0.12), transparent 24%),
                linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        }
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2.5rem;
            max-width: 1500px;
        }
        h1, h2, h3 {
            letter-spacing: -0.02em;
        }
        .hero-panel {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 48%, #0f766e 100%);
            color: #f8fafc;
            border-radius: 24px;
            padding: 1.4rem 1.5rem;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.18);
            margin-bottom: 1rem;
        }
        .hero-kicker {
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            opacity: 0.8;
            margin-bottom: 0.45rem;
        }
        .hero-title {
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
        }
        .hero-text {
            margin-top: 0.55rem;
            max-width: 760px;
            color: rgba(248, 250, 252, 0.88);
        }
        .section-chip-row {
            display: flex;
            gap: 0.6rem;
            flex-wrap: wrap;
            margin: 0.85rem 0 0.1rem 0;
        }
        .section-chip {
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 999px;
            padding: 0.4rem 0.75rem;
            font-size: 0.82rem;
        }
        .section-card {
            background: rgba(255, 255, 255, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 22px;
            padding: 0.8rem 1rem 0.2rem 1rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
            margin: 0.55rem 0 1.05rem 0;
        }
        .mini-note {
            color: #475569;
            font-size: 0.92rem;
            margin-top: -0.25rem;
            margin-bottom: 0.75rem;
        }
        .agenda-card {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border-left: 5px solid #0ea5e9;
            border-radius: 16px;
            padding: 0.8rem 0.9rem;
            margin-bottom: 0.7rem;
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.05);
        }
        .agenda-time {
            color: #0f172a;
            font-size: 0.84rem;
            font-weight: 700;
        }
        .agenda-title {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 700;
            margin-top: 0.2rem;
        }
        .agenda-meta {
            color: #475569;
            font-size: 0.88rem;
            margin-top: 0.22rem;
        }
        .month-grid {
            display: grid;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            gap: 0.55rem;
            margin-top: 0.55rem;
        }
        .month-head {
            font-size: 0.82rem;
            font-weight: 700;
            color: #475569;
            padding: 0.15rem 0.2rem;
        }
        .month-day {
            min-height: 172px;
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 16px;
            padding: 0.62rem 0.62rem 0.52rem 0.62rem;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
        }
        .month-day.muted {
            background: rgba(226, 232, 240, 0.45);
            border-style: dashed;
            box-shadow: none;
        }
        .month-day.today {
            border: 2px solid #0f766e;
            box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.12);
            background: linear-gradient(180deg, #f0fdfa 0%, rgba(255, 255, 255, 0.94) 100%);
        }
        .month-day-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.35rem;
        }
        .month-day-number {
            font-size: 0.95rem;
            font-weight: 800;
            color: #0f172a;
        }
        .month-day-count {
            font-size: 0.74rem;
            color: #64748b;
        }
        .month-day-badge {
            display: inline-block;
            margin-top: 0.18rem;
            font-size: 0.68rem;
            font-weight: 700;
            color: #0f766e;
            background: rgba(15, 118, 110, 0.12);
            border-radius: 999px;
            padding: 0.12rem 0.42rem;
        }
        .month-event {
            font-size: 0.8rem;
            line-height: 1.25;
            border-left: 4px solid #0ea5e9;
            background: #f8fafc;
            color: #0f172a;
            padding: 0.34rem 0.4rem;
            border-radius: 10px;
            margin-top: 0.3rem;
            overflow: hidden;
        }
        .month-event.reunion {
            border-left-color: #ef4444;
            background: #fff1f2;
        }
        .month-event.tarea {
            border-left-color: #2563eb;
            background: #eff6ff;
        }
        .month-event.subtarea {
            border-left-color: #f59e0b;
            background: #fffbeb;
        }
        .month-event-label {
            display: block;
            font-weight: 700;
            white-space: normal;
            word-break: break-word;
        }
        .month-more {
            margin-top: 0.35rem;
            font-size: 0.74rem;
            color: #64748b;
        }
        .task-card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 0.8rem;
            margin-top: 0.45rem;
        }
        .task-card {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 16px;
            padding: 0.85rem 0.9rem;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.05);
        }
        .task-card.blocked {
            border-left: 5px solid #dc2626;
            background: linear-gradient(180deg, #fff7f7 0%, #fff1f2 100%);
        }
        .task-card.overdue {
            border-left: 5px solid #f97316;
            background: linear-gradient(180deg, #fffaf5 0%, #fff7ed 100%);
        }
        .task-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.5rem;
        }
        .task-card-title {
            font-size: 0.95rem;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.25;
        }
        .task-card-meta {
            margin-top: 0.28rem;
            color: #475569;
            font-size: 0.82rem;
            line-height: 1.3;
        }
        .task-card-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin-top: 0.6rem;
        }
        .task-chip {
            display: inline-block;
            border-radius: 999px;
            padding: 0.18rem 0.48rem;
            font-size: 0.72rem;
            font-weight: 700;
        }
        .task-chip.priority-alta {
            background: #fee2e2;
            color: #991b1b;
        }
        .task-chip.priority-media {
            background: #ffedd5;
            color: #9a3412;
        }
        .task-chip.priority-baja {
            background: #dbeafe;
            color: #1d4ed8;
        }
        .task-chip.status {
            background: #e2e8f0;
            color: #334155;
        }
        .task-chip.blocked {
            background: #fecaca;
            color: #991b1b;
        }
        .task-chip.date {
            background: #ecfeff;
            color: #155e75;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 18px;
            padding: 0.85rem 1rem;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_section_card(title: str, note: str | None = None) -> None:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader(title)
    if note:
        st.markdown(f'<div class="mini-note">{note}</div>', unsafe_allow_html=True)


def close_section_card() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_hero(analysis_date: date, focus_count: int, total_focus_hours: float, pending_meetings: int) -> None:
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-kicker">Panel Diario</div>
            <p class="hero-title">Panel de Productividad JC</p>
            <div class="hero-text">
                Vista ejecutiva para empezar la mañana con contexto: primero proyectos, luego tareas y subtareas, y finalmente la agenda del dia <strong>{analysis_date.strftime("%d/%m/%Y")}</strong>.
            </div>
            <div class="section-chip-row">
                <div class="section-chip">{focus_count} actividades marcadas para hoy</div>
                <div class="section-chip">{format_hours(total_focus_hours)} de carga estimada</div>
                <div class="section-chip">{pending_meetings} reuniones pendientes</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_table(df: pd.DataFrame) -> pd.DataFrame | "pd.io.formats.style.Styler":
    try:
        styler = df.style
    except AttributeError:
        return df

    if "Prioridad" in df.columns:
        styler = styler.map(
            lambda value: f"color: white; font-weight: 700; background-color: {PRIORITY_COLORS.get(normalize_text(value), '#475569')}; border-radius: 8px;",
            subset=["Prioridad"],
        )
    if "Estado" in df.columns:
        styler = styler.map(
            lambda value: f"font-weight: 700; color: {STATUS_COLORS.get(normalize_text(value), '#0f172a')};",
            subset=["Estado"],
        )
    return styler


def render_agenda_cards(events_for_day: pd.DataFrame) -> None:
    if events_for_day.empty:
        st.info("No hay eventos programados para la fecha seleccionada.")
        return

    for _, row in events_for_day.iterrows():
        time_label = normalize_text(row.get("Hora")) or "Sin hora"
        priority = normalize_text(row.get("Prioridad")) or "Sin prioridad"
        detail = normalize_text(row.get("Detalle")) or "Sin detalle"
        category = normalize_text(row.get("Categoria")) or "Evento"
        title = normalize_text(row.get("Evento"))
        st.markdown(
            f"""
            <div class="agenda-card">
                <div class="agenda-time">{time_label} · {category}</div>
                <div class="agenda-title">{title}</div>
                <div class="agenda-meta">{detail} · Prioridad: {priority}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def simplify_event_label(row: pd.Series) -> str:
    category = normalize_text(row.get("Categoria")).lower()
    title = normalize_text(row.get("Evento"))
    detail = normalize_text(row.get("Detalle"))
    time_label = normalize_text(row.get("Hora"))

    if "reuni" in title.lower() or "reuni" in category:
        label = title if title.lower().startswith("reunion") else f"Reunion {title}"
    elif category == "tarea":
        label = f"Avanzar {title}"
    elif category == "subtarea":
        label = f"Entrega {title}" if time_label == "" else title
    else:
        label = title

    if detail:
        label = f"{label} · {detail}"

    if len(label) > 62:
        label = f"{label[:59]}..."
    return label


def month_event_class(category: str, title: str) -> str:
    category = normalize_text(category).lower()
    title = normalize_text(title).lower()
    if "reuni" in category or "reuni" in title:
        return "reunion"
    if category == "tarea":
        return "tarea"
    return "subtarea"


def render_month_calendar(events: pd.DataFrame, selected_month: date) -> None:
    headers = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    month_days = calendar.monthcalendar(selected_month.year, selected_month.month)
    today = date.today()

    if events.empty:
        month_events = pd.DataFrame(columns=["Fecha", "Hora", "Evento", "Categoria", "Detalle", "Prioridad"])
    else:
        month_events = events[
            events["Fecha"].apply(
                lambda value: value.year == selected_month.year and value.month == selected_month.month
            )
        ].copy()

    if not month_events.empty:
        month_events["_priority_rank"] = month_events["Prioridad"].map(priority_rank).fillna(9)
        month_events["_is_meeting"] = month_events.apply(
            lambda row: 0 if "reuni" in normalize_text(row["Evento"]).lower() or "reuni" in normalize_text(row["Categoria"]).lower() else 1,
            axis=1,
        )
        month_events = month_events.sort_values(
            ["Fecha", "_is_meeting", "_priority_rank", "Hora", "Evento"]
        )

    events_by_day: dict[date, list[dict[str, str]]] = {}
    if not month_events.empty:
        for day, group in month_events.groupby("Fecha"):
            entries = []
            for _, row in group.head(4).iterrows():
                entries.append(
                    {
                        "label": simplify_event_label(row),
                        "class": month_event_class(row.get("Categoria"), row.get("Evento")),
                    }
                )
            events_by_day[day] = entries

    html = ['<div class="month-grid">']
    for header in headers:
        html.append(f'<div class="month-head">{header}</div>')

    for week in month_days:
        for day in week:
            if day == 0:
                html.append('<div class="month-day muted"></div>')
                continue

            current = date(selected_month.year, selected_month.month, day)
            day_events = events_by_day.get(current, [])
            total_events = 0 if month_events.empty else int((month_events["Fecha"] == current).sum())
            is_today = current == today
            html.append(f'<div class="month-day{" today" if is_today else ""}">')
            html.append(
                f'<div class="month-day-header"><span class="month-day-number">{day}</span><span class="month-day-count">{total_events} act.</span></div>'
            )
            if is_today:
                html.append('<div class="month-day-badge">Hoy</div>')
            if day_events:
                for event in day_events:
                    html.append(
                        f'<div class="month-event {event["class"]}"><span class="month-event-label">{event["label"]}</span></div>'
                    )
                if total_events > len(day_events):
                    html.append(f'<div class="month-more">+{total_events - len(day_events)} mas</div>')
            html.append("</div>")

    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_portfolio_mix_chart(portfolio_mix: pd.DataFrame) -> None:
    if portfolio_mix.empty:
        st.info("No hay datos para graficar la composicion del portafolio.")
        return

    if alt is None:
        st.bar_chart(portfolio_mix.set_index("Tipo")["Cantidad"])
        return

    chart_data = portfolio_mix.copy()
    color_scale = alt.Scale(
        domain=["Estratégico", "Reactivo", "Soporte", "Sin tipo"],
        range=["#0f766e", "#ea580c", "#2563eb", "#94a3b8"],
    )
    chart = (
        alt.Chart(chart_data)
        .mark_arc(innerRadius=55, outerRadius=95)
        .encode(
            theta=alt.Theta("Cantidad:Q"),
            color=alt.Color("Tipo:N", scale=color_scale, legend=alt.Legend(title=None, orient="bottom")),
            tooltip=["Tipo:N", "Cantidad:Q"],
        )
        .properties(height=250)
    )
    st.altair_chart(chart, use_container_width=True)


def render_strategic_progress_chart(strategic: pd.DataFrame) -> None:
    if strategic.empty:
        st.info("No hay proyectos estrategicos para graficar.")
        return

    chart_data = strategic[["Proyecto", "Avance %", "Prioridad"]].copy()
    chart_data["Proyecto corto"] = chart_data["Proyecto"].apply(
        lambda value: value if len(str(value)) <= 28 else f"{str(value)[:25]}..."
    )

    if alt is None:
        st.bar_chart(chart_data.set_index("Proyecto corto")["Avance %"])
        return

    color_scale = alt.Scale(
        domain=["Alta", "Media", "Baja"],
        range=["#dc2626", "#d97706", "#2563eb"],
    )

    bars = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
        .encode(
            x=alt.X("Avance %:Q", scale=alt.Scale(domain=[0, 100]), title="Avance (%)"),
            y=alt.Y("Proyecto corto:N", sort="-x", title=None),
            color=alt.Color("Prioridad:N", scale=color_scale, legend=alt.Legend(title="Prioridad")),
            tooltip=["Proyecto:N", "Avance %:Q", "Prioridad:N"],
        )
    )

    labels = (
        alt.Chart(chart_data)
        .mark_text(align="left", baseline="middle", dx=6, color="#0f172a", fontWeight="bold")
        .encode(
            x="Avance %:Q",
            y=alt.Y("Proyecto corto:N", sort="-x"),
            text=alt.Text("Avance %:Q", format=".0f"),
        )
    )

    chart = (bars + labels).properties(height=max(220, len(chart_data) * 44))
    st.altair_chart(chart, use_container_width=True)


def project_health_label(blocked: int, upcoming: int, open_subtasks: int, status: object) -> str:
    status_text = normalize_text(status)
    if is_closed(status_text):
        return "Verde"
    if blocked > 0 or upcoming >= 3:
        return "Rojo"
    if upcoming > 0 or open_subtasks >= 5:
        return "Amarillo"
    return "Verde"


def task_health_label(blocked: int, upcoming: int, open_subtasks: int, in_progress: int, status: object) -> str:
    status_text = normalize_text(status)
    if is_closed(status_text):
        return "Verde"
    if blocked > 0 or upcoming >= 2:
        return "Rojo"
    if open_subtasks >= 4 or in_progress == 0:
        return "Amarillo"
    return "Verde"


def render_project_overview_table(project_overview: pd.DataFrame) -> None:
    if project_overview.empty:
        st.info("No hay proyectos para mostrar con los filtros actuales.")
        return

    icon_map = {"Rojo": "Rojo", "Amarillo": "Amarillo", "Verde": "Verde"}
    table = project_overview.copy()
    table["Salud"] = table["Salud"].map(lambda value: icon_map.get(value, value))

    try:
        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Avance %": st.column_config.ProgressColumn(
                    "Avance %",
                    min_value=0,
                    max_value=100,
                    format="%d%%",
                ),
                "Salud": st.column_config.TextColumn(
                    "Salud",
                    help="Verde: estable. Amarillo: atencion. Rojo: riesgo alto por bloqueos o acumulacion de vencimientos.",
                    width="small",
                ),
                "Fecha objetivo": st.column_config.TextColumn("Fecha objetivo", width="small"),
                "Tipo_Proyecto": st.column_config.TextColumn("Tipo", width="small"),
                "Tareas activas": st.column_config.NumberColumn("Tareas", width="small"),
                "Subtareas abiertas": st.column_config.NumberColumn("Subtareas", width="small"),
                "Bloqueadas": st.column_config.NumberColumn("Bloq.", width="small"),
                "Por vencer 7d": st.column_config.NumberColumn("Vence 7d", width="small"),
            },
        )
    except Exception:  # noqa: BLE001
        st.dataframe(style_table(table), use_container_width=True, hide_index=True)


def render_task_overview_table(task_overview: pd.DataFrame) -> None:
    if task_overview.empty:
        st.info("No hay tareas para mostrar con los filtros actuales.")
        return

    table = task_overview.copy()
    try:
        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Progreso operativo %": st.column_config.ProgressColumn(
                    "Progreso operativo",
                    min_value=0,
                    max_value=100,
                    format="%d%%",
                ),
                "Salud": st.column_config.TextColumn(
                    "Salud",
                    help="Verde: estable. Amarillo: atencion. Rojo: riesgo alto por bloqueos o vencimientos proximos.",
                    width="small",
                ),
                "Tipo_Tarea": st.column_config.TextColumn("Tipo", width="small"),
                "Fecha objetivo": st.column_config.TextColumn("Fecha objetivo", width="small"),
                "Subtareas abiertas": st.column_config.NumberColumn("Subtareas", width="small"),
                "En proceso": st.column_config.NumberColumn("En proc.", width="small"),
                "Bloqueadas": st.column_config.NumberColumn("Bloq.", width="small"),
                "Por vencer 7d": st.column_config.NumberColumn("Vence 7d", width="small"),
            },
        )
    except Exception:  # noqa: BLE001
        st.dataframe(style_table(table), use_container_width=True, hide_index=True)


def render_subtask_cards(table: pd.DataFrame, empty_message: str) -> None:
    if table.empty:
        st.info(empty_message)
        return

    html = ['<div class="task-card-grid">']
    for _, row in table.iterrows():
        title = normalize_text(row.get("Subtarea"))
        project = normalize_text(row.get("Proyecto"))
        task = normalize_text(row.get("Tarea"))
        state = normalize_text(row.get("Estado"))
        priority = normalize_text(row.get("Prioridad")).lower()
        blocked = normalize_text(row.get("Bloqueado")).lower()
        deadline = normalize_text(row.get("Fecha limite"))
        hours = row.get("Horas")

        card_classes = ["task-card"]
        if blocked in {"si", "sí", "yes", "true", "1"}:
            card_classes.append("blocked")
        elif deadline not in {"", "-"}:
            card_classes.append("overdue")

        chips = [
            f'<span class="task-chip priority-{priority if priority in {"alta", "media", "baja"} else "media"}">{normalize_text(row.get("Prioridad")) or "Sin prioridad"}</span>',
            f'<span class="task-chip status">{state or "Sin estado"}</span>',
        ]
        if blocked in {"si", "sí", "yes", "true", "1"}:
            chips.append('<span class="task-chip blocked">Bloqueado</span>')
        if deadline not in {"", "-"}:
            chips.append(f'<span class="task-chip date">Limite {deadline}</span>')
        if hours is not None and pd.notna(hours):
            chips.append(f'<span class="task-chip date">{float(hours):.1f} h</span>')

        html.append(
            f"""
            <div class="{' '.join(card_classes)}">
                <div class="task-card-header">
                    <div class="task-card-title">{title}</div>
                </div>
                <div class="task-card-meta">{project}</div>
                <div class="task-card-meta">{task}</div>
                <div class="task-card-chips">{''.join(chips)}</div>
            </div>
            """
        )

    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def build_portfolio_mix(projects: pd.DataFrame) -> pd.DataFrame:
    return (
        projects["Tipo_Proyecto"]
        .fillna("Sin tipo")
        .value_counts()
        .rename_axis("Tipo")
        .reset_index(name="Cantidad")
    )


def pick_default_analysis_date(inbox: pd.DataFrame) -> date:
    valid_dates = inbox["Fecha"].dropna() if "Fecha" in inbox else pd.Series(dtype="datetime64[ns]")
    if not valid_dates.empty:
        return valid_dates.max().date()
    return date.today()


def build_focus_table(subtasks: pd.DataFrame) -> pd.DataFrame:
    focus = subtasks[
        subtasks["Hoy"].apply(is_yes) & ~subtasks["Estado"].apply(is_closed)
    ].copy()
    focus["Fecha limite"] = focus["Fecha_limite_opcional"].apply(format_date)
    focus["Duracion_estimada"] = focus["Duracion_estimada"].fillna(0.0)
    return focus[
        [
            "ID_Subtarea",
            "Subtarea",
            "Proyecto",
            "Tarea",
            "Tipo",
            "Estado",
            "Prioridad",
            "Duracion_estimada",
            "Bloqueado",
            "Fecha limite",
        ]
    ].rename(
        columns={
            "Duracion_estimada": "Horas",
        }
    )


def build_alerts(subtasks: pd.DataFrame, analysis_date: date) -> dict[str, pd.DataFrame]:
    overdue = subtasks[
        subtasks["Fecha_limite_opcional"].notna()
        & (subtasks["Fecha_limite_opcional"].dt.date < analysis_date)
        & ~subtasks["Estado"].apply(is_closed)
    ].copy()

    blocked = subtasks[subtasks["Bloqueado"].apply(is_yes)].copy()
    blocked = blocked[~blocked["Estado"].apply(is_closed)]

    high_priority = subtasks[
        subtasks["Prioridad"].astype(str).str.lower().eq("alta")
        & subtasks["Estado"].astype(str).str.lower().eq("no iniciado")
    ].copy()

    for df in (overdue, blocked, high_priority):
        if "Fecha_limite_opcional" in df:
            df["Fecha limite"] = df["Fecha_limite_opcional"].apply(format_date)

    return {
        "vencidos": overdue[ALERT_COLUMNS] if not overdue.empty else empty_table(ALERT_COLUMNS),
        "bloqueados": blocked[ALERT_COLUMNS] if not blocked.empty else empty_table(ALERT_COLUMNS),
        "alta_prioridad": high_priority[ALERT_COLUMNS]
        if not high_priority.empty
        else empty_table(ALERT_COLUMNS),
    }


def build_upcoming_table(subtasks: pd.DataFrame, analysis_date: date, days: int) -> pd.DataFrame:
    end_date = analysis_date + pd.Timedelta(days=days)
    upcoming = subtasks[
        subtasks["Fecha_limite_opcional"].notna()
        & subtasks["Fecha_limite_opcional"].dt.date.ge(analysis_date)
        & subtasks["Fecha_limite_opcional"].dt.date.le(end_date)
        & ~subtasks["Estado"].apply(is_closed)
    ].copy()
    if upcoming.empty:
        return empty_table(ALERT_COLUMNS)

    upcoming["Fecha limite"] = upcoming["Fecha_limite_opcional"].apply(format_date)
    return upcoming[ALERT_COLUMNS].sort_values(["Fecha limite", "Prioridad", "Proyecto", "Tarea"])


def build_inbox_table(inbox: pd.DataFrame, analysis_date: date) -> pd.DataFrame:
    today_inbox = inbox[inbox["Fecha"].dt.date.eq(analysis_date)].copy()
    if today_inbox.empty:
        return today_inbox

    today_inbox["Hora"] = today_inbox["Hora"].apply(normalize_text)
    return today_inbox[
        [
            "Hora",
            "Entrada",
            "Tipo",
            "Urgencia",
            "Origen",
            "Acción rápida",
            "Tipo_resolucion",
            "Estado",
            "Subtarea",
            "Proyecto",
        ]
    ]


def build_project_overview(
    projects: pd.DataFrame, tasks: pd.DataFrame, subtasks: pd.DataFrame, analysis_date: date
) -> pd.DataFrame:
    end_date = analysis_date + pd.Timedelta(days=7)
    open_subtasks = subtasks[~subtasks["Estado"].apply(is_closed)].copy()
    active_tasks = tasks[~tasks["Estado"].apply(is_closed)].copy()
    upcoming = subtasks[
        subtasks["Fecha_limite_opcional"].notna()
        & subtasks["Fecha_limite_opcional"].dt.date.ge(analysis_date)
        & subtasks["Fecha_limite_opcional"].dt.date.le(end_date)
        & ~subtasks["Estado"].apply(is_closed)
    ].copy()

    project_view = projects.copy()
    project_view["Fecha objetivo"] = project_view["Fecha_objetivo"].apply(format_date)

    task_counts = active_tasks.groupby("ID_Proyecto").size().rename("Tareas activas")
    subtask_counts = open_subtasks.groupby("ID_Proyecto").size().rename("Subtareas abiertas")
    blocked_counts = open_subtasks[open_subtasks["Bloqueado"].apply(is_yes)].groupby("ID_Proyecto").size().rename("Bloqueadas")
    upcoming_counts = upcoming.groupby("ID_Proyecto").size().rename("Por vencer 7d")

    project_view = project_view.merge(task_counts, on="ID_Proyecto", how="left")
    project_view = project_view.merge(subtask_counts, on="ID_Proyecto", how="left")
    project_view = project_view.merge(blocked_counts, on="ID_Proyecto", how="left")
    project_view = project_view.merge(upcoming_counts, on="ID_Proyecto", how="left")

    for column in ["Tareas activas", "Subtareas abiertas", "Bloqueadas", "Por vencer 7d"]:
        project_view[column] = project_view[column].fillna(0).astype(int)

    project_view["Avance %"] = project_view["Avance %"].fillna(0).astype(int)
    project_view["Salud"] = project_view.apply(
        lambda row: project_health_label(
            int(row["Bloqueadas"]),
            int(row["Por vencer 7d"]),
            int(row["Subtareas abiertas"]),
            row["Estado"],
        ),
        axis=1,
    )

    return project_view[
        [
            "Proyecto",
            "Tipo_Proyecto",
            "Estado",
            "Salud",
            "Prioridad",
            "Avance %",
            "Fecha objetivo",
            "Tareas activas",
            "Subtareas abiertas",
            "Bloqueadas",
            "Por vencer 7d",
        ]
    ].sort_values(["Prioridad", "Tipo_Proyecto", "Proyecto"])


def build_task_overview(tasks: pd.DataFrame, subtasks: pd.DataFrame, analysis_date: date) -> pd.DataFrame:
    end_date = analysis_date + pd.Timedelta(days=7)
    task_view = tasks.copy()
    task_view["Fecha objetivo"] = task_view["Fecha_objetivo"].apply(format_date)

    open_subtasks = subtasks[~subtasks["Estado"].apply(is_closed)].copy()
    in_progress = subtasks[subtasks["Estado"].astype(str).str.lower().eq("en proceso")].copy()
    total_subtasks = subtasks.groupby("ID_Tarea").size().rename("Total subtareas")
    upcoming = subtasks[
        subtasks["Fecha_limite_opcional"].notna()
        & subtasks["Fecha_limite_opcional"].dt.date.ge(analysis_date)
        & subtasks["Fecha_limite_opcional"].dt.date.le(end_date)
        & ~subtasks["Estado"].apply(is_closed)
    ].copy()

    open_counts = open_subtasks.groupby("ID_Tarea").size().rename("Subtareas abiertas")
    in_progress_counts = in_progress.groupby("ID_Tarea").size().rename("En proceso")
    blocked_counts = open_subtasks[open_subtasks["Bloqueado"].apply(is_yes)].groupby("ID_Tarea").size().rename("Bloqueadas")
    upcoming_counts = upcoming.groupby("ID_Tarea").size().rename("Por vencer 7d")

    task_view = task_view.merge(total_subtasks, on="ID_Tarea", how="left")
    task_view = task_view.merge(open_counts, on="ID_Tarea", how="left")
    task_view = task_view.merge(in_progress_counts, on="ID_Tarea", how="left")
    task_view = task_view.merge(blocked_counts, on="ID_Tarea", how="left")
    task_view = task_view.merge(upcoming_counts, on="ID_Tarea", how="left")

    for column in ["Total subtareas", "Subtareas abiertas", "En proceso", "Bloqueadas", "Por vencer 7d"]:
        task_view[column] = task_view[column].fillna(0).astype(int)

    task_view["Progreso operativo %"] = task_view.apply(
        lambda row: 0
        if int(row["Total subtareas"]) == 0
        else int(round(((int(row["Total subtareas"]) - int(row["Subtareas abiertas"])) / int(row["Total subtareas"])) * 100)),
        axis=1,
    )
    task_view["Salud"] = task_view.apply(
        lambda row: task_health_label(
            int(row["Bloqueadas"]),
            int(row["Por vencer 7d"]),
            int(row["Subtareas abiertas"]),
            int(row["En proceso"]),
            row["Estado"],
        ),
        axis=1,
    )

    return task_view[
        [
            "Proyecto",
            "Tarea",
            "Tipo_Tarea",
            "Estado",
            "Salud",
            "Prioridad",
            "Progreso operativo %",
            "Fecha objetivo",
            "Subtareas abiertas",
            "En proceso",
            "Bloqueadas",
            "Por vencer 7d",
        ]
    ].sort_values(["Prioridad", "Fecha objetivo", "Proyecto", "Tarea"])


def build_reactive_summary(projects: pd.DataFrame) -> pd.DataFrame:
    reactive = projects[projects["Tipo_Proyecto"].astype(str).str.lower().eq("reactivo")].copy()
    if reactive.empty:
        return reactive

    for column in ["Pendientes", "Hoy_recibidos", "Hoy_cerrados"]:
        reactive[column] = reactive[column].fillna(0).astype(int)

    return reactive[
        [
            "Proyecto",
            "Estado",
            "Prioridad",
            "Pendientes",
            "Hoy_recibidos",
            "Hoy_cerrados",
        ]
    ]


def build_strategic_summary(projects: pd.DataFrame) -> pd.DataFrame:
    strategic = projects[projects["Tipo_Proyecto"].astype(str).str.lower().eq("estratégico")].copy()
    if strategic.empty:
        return strategic

    strategic["Avance %"] = strategic["Avance %"].fillna(0).astype(int)
    strategic["Fecha objetivo"] = strategic["Fecha_objetivo"].apply(format_date)
    return strategic[
        ["Proyecto", "Estado", "Prioridad", "Avance %", "Fecha objetivo"]
    ]


def build_pending_meetings(subtasks: pd.DataFrame, inbox: pd.DataFrame, analysis_date: date) -> pd.DataFrame:
    meetings = subtasks[
        subtasks["Tipo"].astype(str).str.lower().eq("reunión") & ~subtasks["Estado"].apply(is_closed)
    ].copy()
    if meetings.empty:
        return pd.DataFrame(
            columns=["Fecha", "Hora", "Subtarea", "Proyecto", "Tarea", "Prioridad", "Estado"]
        )

    meeting_inbox = inbox[["ID_Subtarea", "Fecha", "Hora", "Entrada", "Estado"]].copy()
    meetings = meetings.merge(meeting_inbox, on="ID_Subtarea", how="left")
    meetings["Fecha evento"] = meetings["Fecha"].dt.date
    meetings = meetings[
        meetings["Fecha evento"].isna() | meetings["Fecha evento"].ge(analysis_date)
    ].copy()
    meetings["Fecha"] = meetings["Fecha"].apply(format_date)
    meetings["Hora"] = meetings["Hora"].apply(normalize_text)
    return meetings[
        ["Fecha", "Hora", "Subtarea", "Proyecto", "Tarea", "Prioridad", "Estado_x"]
    ].rename(columns={"Estado_x": "Estado"}).sort_values(["Fecha", "Hora", "Prioridad"])


def build_event_table(tasks: pd.DataFrame, subtasks: pd.DataFrame, inbox: pd.DataFrame) -> pd.DataFrame:
    events: list[pd.DataFrame] = []

    task_events = tasks[tasks["Fecha_objetivo"].notna()].copy()
    if not task_events.empty:
        task_events["Fecha"] = task_events["Fecha_objetivo"].dt.date
        task_events["Hora"] = ""
        task_events["Evento"] = task_events["Tarea"]
        task_events["Categoria"] = "Tarea"
        task_events["Detalle"] = task_events["Proyecto"]
        events.append(task_events[["Fecha", "Hora", "Evento", "Categoria", "Detalle", "Prioridad"]])

    subtask_events = subtasks[subtasks["Fecha_limite_opcional"].notna()].copy()
    if not subtask_events.empty:
        subtask_events["Fecha"] = subtask_events["Fecha_limite_opcional"].dt.date
        subtask_events["Hora"] = ""
        subtask_events["Evento"] = subtask_events["Subtarea"]
        subtask_events["Categoria"] = "Subtarea"
        subtask_events["Detalle"] = subtask_events["Proyecto"]
        events.append(subtask_events[["Fecha", "Hora", "Evento", "Categoria", "Detalle", "Prioridad"]])

    inbox_events = inbox[inbox["Fecha"].notna()].copy()
    if not inbox_events.empty:
        inbox_events["Fecha"] = inbox_events["Fecha"].dt.date
        inbox_events["Evento"] = inbox_events["Entrada"]
        inbox_events["Categoria"] = inbox_events["Tipo"].fillna("Inbox")
        inbox_events["Detalle"] = inbox_events["Proyecto"].fillna(inbox_events["Origen"])
        events.append(
            inbox_events[["Fecha", "Hora", "Evento", "Categoria", "Detalle", "Urgencia"]].rename(
                columns={"Urgencia": "Prioridad"}
            )
        )

    if not events:
        return pd.DataFrame(columns=["Fecha", "Hora", "Evento", "Categoria", "Detalle", "Prioridad"])

    event_table = pd.concat(events, ignore_index=True)
    event_table["Hora"] = event_table["Hora"].apply(normalize_text)
    event_table["Prioridad"] = event_table["Prioridad"].apply(normalize_text)
    return event_table.sort_values(["Fecha", "Hora", "Categoria", "Evento"])


def apply_global_filters(
    projects: pd.DataFrame,
    tasks: pd.DataFrame,
    subtasks: pd.DataFrame,
    inbox: pd.DataFrame,
    selected_project_types: list[str],
    selected_priorities: list[str],
    selected_states: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    filtered_projects = projects.copy()
    filtered_tasks = tasks.copy()
    filtered_subtasks = subtasks.copy()
    filtered_inbox = inbox.copy()

    if selected_project_types:
        filtered_projects = filtered_projects[filtered_projects["Tipo_Proyecto"].isin(selected_project_types)]
        valid_project_ids = set(filtered_projects["ID_Proyecto"].dropna())
        filtered_tasks = filtered_tasks[filtered_tasks["ID_Proyecto"].isin(valid_project_ids)]
        valid_task_ids = set(filtered_tasks["ID_Tarea"].dropna())
        filtered_subtasks = filtered_subtasks[filtered_subtasks["ID_Tarea"].isin(valid_task_ids)]
        filtered_inbox = filtered_inbox[
            filtered_inbox["ID_Proyecto"].isin(valid_project_ids) | filtered_inbox["ID_Proyecto"].isna()
        ]

    if selected_priorities:
        filtered_projects = filtered_projects[filtered_projects["Prioridad"].isin(selected_priorities)]
        filtered_tasks = filtered_tasks[filtered_tasks["Prioridad"].isin(selected_priorities)]
        filtered_subtasks = filtered_subtasks[filtered_subtasks["Prioridad"].isin(selected_priorities)]
        filtered_inbox = filtered_inbox[
            filtered_inbox["Urgencia"].isin(selected_priorities)
            | filtered_inbox["Prioridad"].isin(selected_priorities)
            | filtered_inbox["Urgencia"].isna()
        ]

    if selected_states:
        filtered_projects = filtered_projects[filtered_projects["Estado"].isin(selected_states)]
        filtered_tasks = filtered_tasks[filtered_tasks["Estado"].isin(selected_states)]
        filtered_subtasks = filtered_subtasks[filtered_subtasks["Estado"].isin(selected_states)]
        filtered_inbox = filtered_inbox[
            filtered_inbox["Estado"].isin(selected_states) | filtered_inbox["Estado"].isna()
        ]

    return filtered_projects, filtered_tasks, filtered_subtasks, filtered_inbox


def build_week_view(events: pd.DataFrame, analysis_date: date) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=["Fecha", "Hora", "Evento", "Categoria", "Detalle", "Prioridad"])

    start_week = analysis_date - pd.Timedelta(days=analysis_date.weekday())
    end_week = start_week + pd.Timedelta(days=6)
    week_events = events[
        events["Fecha"].ge(start_week) & events["Fecha"].le(end_week)
    ].copy()
    if week_events.empty:
        return week_events

    week_events["Fecha"] = week_events["Fecha"].apply(format_date)
    return week_events.sort_values(["Fecha", "Hora", "Categoria", "Evento"])


def metric_card(label: str, value: str, help_text: str) -> None:
    st.metric(label, value, help=help_text)


def main() -> None:
    st.set_page_config(page_title="Panel de Productividad JC", layout="wide")
    inject_styles()

    with st.sidebar:
        st.header("Configuracion")
        excel_path = st.text_input("Archivo Excel", value=find_default_excel())
        st.caption("La app es de solo lectura y usa las hojas Proyectos, Tareas, Subtareas e Inbox_Diario. Por defecto carga la plantilla de ejemplo enriquecida.")

    try:
        data = load_excel_data(excel_path)
    except FileNotFoundError:
        st.error(f"No se encontro el archivo Excel: {excel_path}")
        st.stop()
    except ValueError as exc:
        st.error(f"No se pudo leer el Excel. Verifica las hojas requeridas. Detalle: {exc}")
        st.stop()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Ocurrio un error al leer el Excel: {exc}")
        st.stop()

    projects = data["Proyectos"]
    tasks = data["Tareas"]
    subtasks = data["Subtareas"]
    inbox = data["Inbox_Diario"]

    default_analysis_date = pick_default_analysis_date(inbox)
    with st.sidebar:
        analysis_date = st.date_input("Fecha de analisis", value=default_analysis_date)
        st.caption("Por defecto se usa la fecha mas reciente encontrada en Inbox_Diario para que el ejemplo sea util al abrir la app.")
        st.markdown("### Filtros globales")
        project_type_options = sorted(projects["Tipo_Proyecto"].dropna().unique().tolist())
        priority_options = sorted(
            {
                *projects["Prioridad"].dropna().tolist(),
                *tasks["Prioridad"].dropna().tolist(),
                *subtasks["Prioridad"].dropna().tolist(),
            },
            key=priority_rank,
        )
        state_options = sorted(
            {
                *projects["Estado"].dropna().tolist(),
                *tasks["Estado"].dropna().tolist(),
                *subtasks["Estado"].dropna().tolist(),
            }
        )
        selected_project_types = st.multiselect(
            "Tipo de proyecto",
            options=project_type_options,
            default=[],
            placeholder="Todos",
        )
        selected_priorities = st.multiselect(
            "Prioridad",
            options=priority_options,
            default=[],
            placeholder="Todas",
        )
        selected_states = st.multiselect(
            "Estado",
            options=state_options,
            default=[],
            placeholder="Todos",
        )

    projects, tasks, subtasks, inbox = apply_global_filters(
        projects,
        tasks,
        subtasks,
        inbox,
        selected_project_types,
        selected_priorities,
        selected_states,
    )

    focus = build_focus_table(subtasks)
    alerts = build_alerts(subtasks, analysis_date)
    upcoming_3d = build_upcoming_table(subtasks, analysis_date, 3)
    upcoming_7d = build_upcoming_table(subtasks, analysis_date, 7)
    inbox_today = build_inbox_table(inbox, analysis_date)
    project_overview = build_project_overview(projects, tasks, subtasks, analysis_date)
    task_overview = build_task_overview(tasks, subtasks, analysis_date)
    reactive = build_reactive_summary(projects)
    strategic = build_strategic_summary(projects)
    portfolio_mix = build_portfolio_mix(projects)
    pending_meetings = build_pending_meetings(subtasks, inbox, analysis_date)
    events = build_event_table(tasks, subtasks, inbox)
    week_view = build_week_view(events, analysis_date)
    events_for_day = events[events["Fecha"].eq(analysis_date)].copy() if not events.empty else empty_table(
        ["Fecha", "Hora", "Evento", "Categoria", "Detalle", "Prioridad"]
    )

    total_focus_hours = float(focus["Horas"].sum()) if not focus.empty else 0.0
    overload = total_focus_hours > CAPACIDAD_RECOMENDADA
    at_risk_count = len(alerts["vencidos"]) + len(alerts["bloqueados"])
    strategic_count = projects["Tipo_Proyecto"].astype(str).str.lower().eq("estratégico").sum()
    reactive_count = projects["Tipo_Proyecto"].astype(str).str.lower().eq("reactivo").sum()
    support_count = projects["Tipo_Proyecto"].astype(str).str.lower().eq("soporte").sum()

    render_hero(analysis_date, len(focus), total_focus_hours, len(pending_meetings))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Proyectos", str(len(projects)), "Total de proyectos leidos desde el Excel.")
    with col2:
        metric_card("Tareas activas", str(len(tasks[~tasks["Estado"].apply(is_closed)])), "Tareas no cerradas.")
    with col3:
        metric_card("Subtareas abiertas", str(len(subtasks[~subtasks["Estado"].apply(is_closed)])), "Subtareas aun no terminadas.")
    with col4:
        metric_card("En riesgo", str(at_risk_count), "Total de vencidos y bloqueados.")

    top_tabs = st.tabs(["Hoy", "Resumen", "Ejecucion", "Agenda"])

    with top_tabs[0]:
        today_left, today_right = st.columns([1.2, 1])
        with today_left:
            render_section_card("Hoy", "Atajo ejecutivo para responder rapido que toca, que preocupa y que se mueve primero.")
            if focus.empty:
                st.info("No hay subtareas activas para el dia seleccionado.")
            else:
                focus_view = focus.assign(_rank=focus["Prioridad"].map(priority_rank)).sort_values(
                    ["_rank", "Proyecto", "Tarea", "ID_Subtarea"]
                ).drop(columns="_rank")
                st.dataframe(style_table(focus_view), use_container_width=True, hide_index=True)
            close_section_card()

            render_section_card("Alertas de hoy", "Resumen corto de riesgos inmediatos para no entrar al detalle demasiado pronto.")
            quick_alerts = pd.DataFrame(
                [
                    {"Indicador": "Vencidos", "Cantidad": len(alerts["vencidos"])},
                    {"Indicador": "Por vencer 3d", "Cantidad": len(upcoming_3d)},
                    {"Indicador": "Bloqueados", "Cantidad": len(alerts["bloqueados"])},
                    {"Indicador": "Reuniones pendientes", "Cantidad": len(pending_meetings)},
                ]
            )
            st.dataframe(quick_alerts, use_container_width=True, hide_index=True)
            close_section_card()

        with today_right:
            render_section_card("Carga e inbox", "Vista resumida del dia para balancear tiempo comprometido y entradas entrantes.")
            if overload:
                st.error(
                    f"Carga estimada: {format_hours(total_focus_hours)} frente a una capacidad recomendada de {format_hours(CAPACIDAD_RECOMENDADA)}."
                )
            else:
                st.success(
                    f"Carga estimada: {format_hours(total_focus_hours)} dentro de una capacidad recomendada de {format_hours(CAPACIDAD_RECOMENDADA)}."
                )
            direct_count = (
                inbox_today["Tipo_resolucion"].astype(str).str.lower().eq("directo").sum()
                if not inbox_today.empty
                else 0
            )
            escala_count = (
                inbox_today["Tipo_resolucion"].astype(str).str.lower().eq("escala").sum()
                if not inbox_today.empty
                else 0
            )
            st.write(
                f"Inbox del dia: {len(inbox_today)} entradas. Directo: {direct_count}. Escala: {escala_count}."
            )
            if not pending_meetings.empty:
                st.dataframe(style_table(pending_meetings.head(5)), use_container_width=True, hide_index=True)
            close_section_card()

            render_section_card("Agenda del dia", "Lo programado hoy en orden cronologico para arrancar sin perder contexto.")
            render_agenda_cards(events_for_day.sort_values(["Hora", "Categoria", "Evento"]))
            close_section_card()

    with top_tabs[1]:
        mix_left, mix_right = st.columns([1.3, 1])
        with mix_left:
            render_section_card("Vista general de proyectos", "Resumen alto nivel para ubicar estado, avance y zonas de friccion antes de entrar al detalle.")
            render_project_overview_table(project_overview)
            close_section_card()
        with mix_right:
            dist_left, dist_right = st.columns(2)
            with dist_left:
                render_section_card("Composicion del portafolio", "Cantidad de proyectos por tipo. Aqui si estamos viendo distribucion real.")
                st.write(
                    f"Estrategicos: {strategic_count} | Reactivos: {reactive_count} | Soporte: {support_count}"
                )
                render_portfolio_mix_chart(portfolio_mix)
                close_section_card()
            with dist_right:
                render_section_card("Avance estrategico", "Porcentaje de avance de cada proyecto estrategico, separado de la composicion del portafolio.")
                render_strategic_progress_chart(strategic)
                close_section_card()

        summary_left, summary_right = st.columns(2)
        with summary_left:
            render_section_card("Reactivo", "Flujo de pedidos y consultas de respuesta corta o alta recurrencia.")
            if reactive.empty:
                st.info("No hay proyectos reactivos.")
            else:
                st.dataframe(style_table(reactive), use_container_width=True, hide_index=True)
            close_section_card()
        with summary_right:
            render_section_card("Estrategico", "Seguimiento del portafolio que mueve objetivos mayores y necesita control de avance.")
            if strategic.empty:
                st.info("No hay proyectos estrategicos.")
            else:
                st.dataframe(style_table(strategic), use_container_width=True, hide_index=True)
            close_section_card()

    with top_tabs[2]:
        render_section_card("Nivel tareas", "Puente entre la vista de proyectos y la ejecucion operativa. Aqui se ve donde se concentra la carga real.")
        render_task_overview_table(task_overview)
        close_section_card()

        left, right = st.columns([1.25, 1])
        with left:
            render_section_card("Nivel subtareas y alertas", "Incluye vencidos, proximos vencimientos, bloqueos y trabajo de alta prioridad todavia no iniciado.")
            alert_tabs = st.tabs(
                [
                    f"Vencidos ({len(alerts['vencidos'])})",
                    f"Por vencer 3d ({len(upcoming_3d)})",
                    f"Por vencer 7d ({len(upcoming_7d)})",
                    f"Bloqueados ({len(alerts['bloqueados'])})",
                    f"Alta prioridad ({len(alerts['alta_prioridad'])})",
                ]
            )

            for tab, key in zip(
                alert_tabs,
                [
                    "vencidos",
                    "upcoming_3d",
                    "upcoming_7d",
                    "bloqueados",
                    "alta_prioridad",
                ],
            ):
                with tab:
                    table = {
                        "vencidos": alerts["vencidos"],
                        "upcoming_3d": upcoming_3d,
                        "upcoming_7d": upcoming_7d,
                        "bloqueados": alerts["bloqueados"],
                        "alta_prioridad": alerts["alta_prioridad"],
                    }[key]
                    if table.empty:
                        st.success("Sin elementos en esta alerta.")
                    else:
                        st.dataframe(style_table(table), use_container_width=True, hide_index=True)
            close_section_card()

        with right:
            render_section_card("Reuniones pendientes", "Separadas del resto porque suelen ordenar la mañana y condicionan la disponibilidad del dia.")
            if pending_meetings.empty:
                st.info("No hay reuniones pendientes registradas.")
            else:
                st.dataframe(style_table(pending_meetings), use_container_width=True, hide_index=True)
            close_section_card()

            render_section_card("Carga del dia", "Chequeo rapido de capacidad versus tiempo comprometido en subtareas marcadas para hoy.")
            if overload:
                st.error(
                    f"Carga estimada: {format_hours(total_focus_hours)}. Estado: Sobrecargado frente a la capacidad recomendada de {format_hours(CAPACIDAD_RECOMENDADA)}."
                )
            else:
                st.success(
                    f"Carga estimada: {format_hours(total_focus_hours)}. Estado: OK dentro de la capacidad recomendada de {format_hours(CAPACIDAD_RECOMENDADA)}."
                )

            completion_hint = "Hay trabajo priorizado, revisa bloqueos y vencimientos primero." if len(alerts["bloqueados"]) or len(alerts["vencidos"]) else "No se observan riesgos criticos inmediatos."
            st.write(completion_hint)

            direct_count = (
                inbox_today["Tipo_resolucion"].astype(str).str.lower().eq("directo").sum()
                if not inbox_today.empty
                else 0
            )
            escala_count = (
                inbox_today["Tipo_resolucion"].astype(str).str.lower().eq("escala").sum()
                if not inbox_today.empty
                else 0
            )
            st.write(
                f"Entradas del inbox para {analysis_date.strftime('%d/%m/%Y')}: {len(inbox_today)}. Directo: {direct_count}. Escala: {escala_count}."
            )
            close_section_card()

        render_section_card("Actividades del dia", "Lista operativa para arrancar. Reune las subtareas marcadas para hoy que siguen abiertas.")
        if focus.empty:
            st.info("No hay subtareas activas para el dia seleccionado.")
        else:
            focus_view = focus.assign(_rank=focus["Prioridad"].map(priority_rank)).sort_values(
                ["_rank", "Proyecto", "Tarea", "ID_Subtarea"]
            ).drop(columns="_rank")
            st.dataframe(style_table(focus_view), use_container_width=True, hide_index=True)
        close_section_card()

        render_section_card("Inbox", "Entradas del dia para distinguir rapido lo directo de lo que requiere escalamiento o seguimiento.")
        if inbox_today.empty:
            st.info("No hay entradas registradas para la fecha de analisis.")
        else:
            st.dataframe(style_table(inbox_today.sort_values(["Hora", "Urgencia"], ascending=[True, True])), use_container_width=True, hide_index=True)
        close_section_card()

    with top_tabs[3]:
        cal_controls_left, cal_controls_right, _ = st.columns([1.2, 0.8, 2.2])
        with cal_controls_left:
            calendar_month_name = st.selectbox(
                "Mes",
                options=MONTH_NAMES,
                index=analysis_date.month - 1,
                key="agenda_month",
            )
        with cal_controls_right:
            calendar_year = st.number_input(
                "Ano",
                min_value=2024,
                max_value=2100,
                value=analysis_date.year,
                step=1,
                key="agenda_year",
            )
        selected_month = date(int(calendar_year), MONTH_NAMES.index(calendar_month_name) + 1, 1)

        render_section_card("Calendario mensual", "Lectura visual del mes: cada dia muestra actividades concretas para detectar reuniones, avances planeados y entregables de un vistazo.")
        render_month_calendar(events, selected_month)
        st.caption("Cada dia muestra hasta cuatro actividades visibles y, si hay mas, un indicador resumido.")
        close_section_card()

        agenda_left, agenda_right = st.columns([1, 1.05])
        with agenda_left:
            render_section_card("Agenda del dia", "Tarjetas cronologicas para revisar reuniones, entregables y eventos relevantes sin perder contexto.")
            render_agenda_cards(events_for_day.sort_values(["Hora", "Categoria", "Evento"]))
            close_section_card()

        with agenda_right:
            render_section_card("Vista semanal", "Semana en curso para revisar concentracion de entregables, reuniones y carga sin ir dia por dia.")
            if week_view.empty:
                st.info("No hay eventos en la semana de la fecha seleccionada.")
            else:
                st.dataframe(style_table(week_view), use_container_width=True, hide_index=True)
            close_section_card()


if __name__ == "__main__":
    main()
