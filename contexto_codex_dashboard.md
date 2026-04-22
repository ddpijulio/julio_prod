# Sistema de Productividad JC – Documento de Especificación para Codex

## 1. Objetivo

Construir y mantener una aplicación en Python (Streamlit) que:
- Lea un archivo Excel como fuente única de datos
- Muestre un dashboard ejecutivo y operativo en modo solo lectura
- Ayude a tomar decisiones diarias (priorización, carga, alertas, agenda)
- Tolere variaciones comunes de captura manual en el Excel

---

## 2. Fuente de datos

Archivo Excel ubicado en la raíz del repo o en una ruta local indicada por el usuario desde la barra lateral.

Archivo por defecto en este repo:

`Sistema_Productividad_JC_PLANTILLA_EJEMPLO.xlsx`

---

## 3. Estructura del Excel

### 3.1 Hoja: Proyectos

Campos:
- ID_Proyecto: identificador único
- Proyecto: nombre del proyecto
- Tipo_Proyecto: Estratégico / Reactivo / Soporte
- Estado: En proceso / Terminado
- Prioridad: Alta / Media / Baja
- Avance %: solo para proyectos estratégicos
- Fecha_objetivo: fecha de finalización (solo estratégico)
- Pendientes: solo para proyectos reactivos
- Hoy_recibidos: solo reactivo
- Hoy_cerrados: solo reactivo

---

### 3.2 Hoja: Tareas

Campos:
- ID_Tarea
- ID_Proyecto
- Tarea
- Tipo_Tarea: Planificación / Producción / Soporte
- Estado
- Prioridad
- Fecha_objetivo

---

### 3.3 Hoja: Subtareas (NIVEL PRINCIPAL)

Campos:
- ID_Subtarea
- ID_Tarea
- Subtarea
- Tipo: Producción / Reunión / Análisis
- Estado: No iniciado / En proceso / En espera / Terminado
- Prioridad
- Hoy: Sí / No
- Duracion_estimada (horas)
- Duracion_real (opcional)
- Origen
- Bloqueado: Sí / No
- Fecha_limite_opcional

---

### 3.4 Hoja: Inbox_Diario

Campos:
- Fecha
- Hora
- Entrada
- Tipo
- Urgencia
- Origen
- Acción rápida
- Tipo_resolucion: Directo / Escala
- Estado
- ID_Subtarea (opcional)

---

## 4. Lógica del sistema

### 4.1 Foco del día
Filtrar subtareas donde:
Hoy = Sí AND Estado != Terminado

---

### 4.2 Carga del día
Suma de Duracion_estimada de subtareas con Hoy = Sí

Capacidad recomendada: 6 horas

---

### 4.3 Alertas

Mostrar:

1. Subtareas vencidas:
Fecha_limite_opcional < hoy AND Estado != Terminado

2. Subtareas bloqueadas:
Bloqueado = Sí

3. Alta prioridad no iniciadas:
Prioridad = Alta AND Estado = No iniciado

4. Próximos vencimientos:
Fecha_limite_opcional entre la fecha de análisis y los próximos 3 o 7 días AND Estado no cerrado

---

### 4.4 Inbox

Mostrar todas las entradas del día seleccionado para análisis

Diferenciar:
- Tipo_resolucion = Directo
- Tipo_resolucion = Escala

---

### 4.5 Flujo reactivo

Para proyecto tipo Reactivo:
Mostrar:
- Pendientes
- Hoy_recibidos
- Hoy_cerrados

---

### 4.6 Progreso estratégico

Para proyectos tipo Estratégico:
Mostrar:
- Avance %
- Fecha_objetivo

---

### 4.7 Salud operativa

La aplicación calcula una etiqueta de salud para proyectos y tareas:
- Verde: sin señales críticas
- Amarillo: atención por carga abierta o falta de avance
- Rojo: riesgo alto por bloqueos o acumulación de vencimientos cercanos

---

### 4.8 Agenda consolidada

La agenda combina:
- Fechas objetivo de tareas
- Fechas límite de subtareas
- Entradas del inbox con fecha

Se muestran vistas:
- del día
- semanal
- calendario mensual

---

## 5. Interfaz (Streamlit)

### 5.1 Barra lateral

- Selector de archivo Excel
- Fecha de análisis
- Filtros globales por tipo de proyecto, prioridad y estado

### 5.2 Encabezado principal

- Título: Panel de Productividad JC
- Resumen rápido de actividades del día, carga estimada y reuniones pendientes
- Métricas de proyectos, tareas activas, subtareas abiertas y elementos en riesgo

### 5.3 Pestañas principales

#### Hoy
- Foco del día
- Alertas resumidas
- Carga e inbox
- Agenda del día

#### Resumen
- Vista general de proyectos
- Composición del portafolio
- Avance estratégico
- Resumen reactivo
- Resumen estratégico

#### Ejecución
- Nivel tareas
- Alertas detalladas
- Reuniones pendientes
- Carga del día
- Actividades del día
- Inbox del día

#### Agenda
- Calendario mensual
- Agenda del día
- Vista semanal

---

## 6. Reglas de negocio

- Subtareas son la unidad de trabajo
- No todas las entradas del inbox generan subtareas
- Reuniones son subtareas
- No eliminar registros, solo cambiar estado
- La fecha de análisis por defecto es la más reciente encontrada en `Inbox_Diario`
- La capacidad recomendada del día es 6 horas
- La app valida columnas obligatorias antes de renderizar
- La app normaliza variaciones comunes de acentos para evitar excluir datos válidos

---

## 7. Tecnologías

- Python
- pandas
- streamlit
- openpyxl
- altair opcional para gráficos; si no está instalada se usan gráficos de respaldo

---

## 8. Ejecución

Instalar dependencias:

pip install -r requirements.txt

Ejecutar:

streamlit run app.py

---

## 9. Objetivo final

Responder:

¿Qué hago hoy?
¿Estoy sobrecargado?
¿Qué está en riesgo?
¿Cómo se distribuye mi portafolio?
¿Qué viene esta semana y este mes?
