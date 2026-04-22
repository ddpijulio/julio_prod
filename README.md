# Panel de Productividad JC

Dashboard en Streamlit para revisar proyectos, tareas, subtareas e inbox desde un único archivo Excel en modo solo lectura.

## Qué hace hoy

- Carga las hojas `Proyectos`, `Tareas`, `Subtareas` e `Inbox_Diario`.
- Muestra foco del día, carga estimada, alertas, inbox y agenda.
- Resume salud operativa por proyecto y tarea.
- Incluye vistas diaria, ejecutiva, operativa y agenda mensual/semanal.
- Permite filtrar por tipo de proyecto, prioridad y estado.

## Estructura del repo

- [app.py](/home/julio/julio/julio_prod/app.py): aplicación principal en Streamlit.
- [contexto_codex_dashboard.md](/home/julio/julio/julio_prod/contexto_codex_dashboard.md): especificación funcional actualizada.
- `Sistema_Productividad_JC_PLANTILLA_EJEMPLO.xlsx`: plantilla de ejemplo para pruebas locales.
- `Sistema_Productividad_JC_FINAL_MASTER.xlsx`: archivo de trabajo adicional.
- [tests/test_app.py](/home/julio/julio/julio_prod/tests/test_app.py): pruebas básicas de regresión.

## Requisitos

- Python 3.10 o superior
- Dependencias de [requirements.txt](/home/julio/julio/julio_prod/requirements.txt)

Instalación:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecutar

```bash
streamlit run app.py
```

La app toma por defecto `Sistema_Productividad_JC_PLANTILLA_EJEMPLO.xlsx`. También puedes indicar otro archivo desde la barra lateral.

## Estructura esperada del Excel

Hojas obligatorias:

- `Proyectos`
- `Tareas`
- `Subtareas`
- `Inbox_Diario`

La app valida que existan las columnas requeridas y muestra un error claro si falta alguna.

## Supuestos de datos

- La app tolera variantes comunes como `Sí/Si`, `Reunión/Reunion` y `Estratégico/Estrategico`.
- Los estados cerrados reconocidos son `Terminado`, `Hecho` y `Cerrado`.
- Las subtareas son la unidad operativa principal.
- La capacidad diaria recomendada usada para carga es `6.0 h`.

## Probar

```bash
python3 -m unittest discover -s tests
```
