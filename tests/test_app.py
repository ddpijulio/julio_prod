import unittest
from datetime import date

import pandas as pd

from app import (
    build_pending_meetings,
    build_strategic_summary,
    build_upcoming_table,
    build_week_view,
    validate_required_columns,
)


class AppBehaviorTests(unittest.TestCase):
    def test_build_upcoming_table_sorts_by_real_date(self) -> None:
        subtasks = pd.DataFrame(
            [
                {
                    "ID_Subtarea": "S1",
                    "Subtarea": "Entrega mayo",
                    "Proyecto": "Proyecto A",
                    "Tarea": "Tarea A",
                    "Estado": "En proceso",
                    "Prioridad": "Alta",
                    "Fecha_limite_opcional": pd.Timestamp("2026-05-02"),
                },
                {
                    "ID_Subtarea": "S2",
                    "Subtarea": "Entrega abril",
                    "Proyecto": "Proyecto A",
                    "Tarea": "Tarea A",
                    "Estado": "En proceso",
                    "Prioridad": "Alta",
                    "Fecha_limite_opcional": pd.Timestamp("2026-04-30"),
                },
            ]
        )

        result = build_upcoming_table(subtasks, date(2026, 4, 29), 7)

        self.assertEqual(result["ID_Subtarea"].tolist(), ["S2", "S1"])

    def test_build_week_view_keeps_chronological_order(self) -> None:
        events = pd.DataFrame(
            [
                {
                    "Fecha": date(2026, 5, 2),
                    "Hora": "",
                    "Evento": "Entrega final",
                    "Categoria": "Tarea",
                    "Detalle": "Proyecto A",
                    "Prioridad": "Alta",
                },
                {
                    "Fecha": date(2026, 4, 30),
                    "Hora": "",
                    "Evento": "Revision",
                    "Categoria": "Tarea",
                    "Detalle": "Proyecto A",
                    "Prioridad": "Alta",
                },
            ]
        )

        result = build_week_view(events, date(2026, 4, 29))

        self.assertEqual(result["Evento"].tolist(), ["Revision", "Entrega final"])

    def test_build_pending_meetings_accepts_unaccented_values(self) -> None:
        subtasks = pd.DataFrame(
            [
                {
                    "ID_Subtarea": "S1",
                    "Tipo": "Reunion",
                    "Estado": "En proceso",
                    "Subtarea": "Kickoff",
                    "Proyecto": "Proyecto A",
                    "Tarea": "Preparacion",
                    "Prioridad": "Alta",
                }
            ]
        )
        inbox = pd.DataFrame(
            [
                {
                    "ID_Subtarea": "S1",
                    "Fecha": pd.Timestamp("2026-04-22"),
                    "Hora": "09:00",
                    "Entrada": "Kickoff",
                    "Estado": "Pendiente",
                }
            ]
        )

        result = build_pending_meetings(subtasks, inbox, date(2026, 4, 21))

        self.assertEqual(result["Subtarea"].tolist(), ["Kickoff"])

    def test_build_strategic_summary_accepts_unaccented_project_type(self) -> None:
        projects = pd.DataFrame(
            [
                {
                    "Proyecto": "Proyecto A",
                    "Tipo_Proyecto": "Estrategico",
                    "Estado": "En proceso",
                    "Prioridad": "Alta",
                    "Avance %": 50,
                    "Fecha_objetivo": pd.Timestamp("2026-05-01"),
                }
            ]
        )

        result = build_strategic_summary(projects)

        self.assertEqual(result["Proyecto"].tolist(), ["Proyecto A"])

    def test_validate_required_columns_reports_missing_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "Tipo_resolucion"):
            validate_required_columns(
                {
                    "Proyectos": pd.DataFrame(columns=["ID_Proyecto", "Proyecto", "Tipo_Proyecto", "Estado", "Prioridad", "Avance %", "Fecha_objetivo", "Pendientes", "Hoy_recibidos", "Hoy_cerrados"]),
                    "Tareas": pd.DataFrame(columns=["ID_Tarea", "ID_Proyecto", "Tarea", "Tipo_Tarea", "Estado", "Prioridad", "Fecha_objetivo"]),
                    "Subtareas": pd.DataFrame(columns=["ID_Subtarea", "ID_Tarea", "Subtarea", "Tipo", "Estado", "Prioridad", "Hoy", "Duracion_estimada", "Duracion_real", "Origen", "Bloqueado", "Fecha_limite_opcional"]),
                    "Inbox_Diario": pd.DataFrame(columns=["Fecha", "Hora", "Entrada", "Tipo", "Urgencia", "Origen", "Acción rápida", "Estado", "ID_Subtarea"]),
                }
            )


if __name__ == "__main__":
    unittest.main()
