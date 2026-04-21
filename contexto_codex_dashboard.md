# Sistema de Productividad JC – Documento de Especificación para Codex

## 1. Objetivo

Construir una aplicación en Python (Streamlit) que:
- Lea un archivo Excel como fuente única de datos
- Muestre un dashboard de productividad en una sola pantalla
- Ayude a tomar decisiones diarias (priorización, carga, alertas)
- NO permita edición de datos (solo lectura en esta fase)

---

## 2. Fuente de datos

Archivo Excel (ubicado en raíz del repo o ruta local):

G:\Mi unidad\Sistema_Productividad_JC_PRO.xlsx

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

---

### 4.4 Inbox

Mostrar todas las entradas del día actual

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

## 5. Interfaz (Streamlit)

### Estructura de la pantalla:

1. Título: Panel de Productividad JC

2. Secciones:

#### 🎯 FOCO DEL DÍA
Tabla con subtareas activas

#### 🔴 ALERTAS
Listas de:
- vencidos
- bloqueados
- alta prioridad

#### ⚡ CARGA DEL DÍA
Texto con:
- horas totales
- mensaje (OK / Sobrecargado)

#### 📥 INBOX
Tabla de entradas

#### 🔄 REACTIVO
Resumen de flujo

#### 🧱 ESTRATÉGICO
Resumen de proyectos

---

## 6. Reglas de negocio

- Subtareas son la unidad de trabajo
- No todas las entradas del inbox generan subtareas
- Reuniones son subtareas
- No eliminar registros, solo cambiar estado

---

## 7. Tecnologías

- Python
- pandas
- streamlit
- openpyxl

---

## 8. Ejecución

Instalar dependencias:

pip install streamlit pandas openpyxl

Ejecutar:

streamlit run app.py

---

## 9. Objetivo final

Responder:

¿Qué hago hoy?
¿Estoy sobrecargado?
¿Qué está en riesgo?

