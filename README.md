# 👨‍🍳 Chef Privado — Sistema Experto con IA Local

Sistema experto basado en reglas que interpreta en lenguaje natural lo que el usuario quiere comer y sugiere recetas con sus instrucciones de preparación e información nutricional. Integra un LLM local mediante Ollama para el procesamiento del lenguaje, con un mecanismo de respaldo que garantiza el funcionamiento aunque el modelo no esté disponible.

---

## 📋 Características

- Motor de inferencia con tres reglas de producción (coincidencia por nombre, por ingrediente y semántica).
- Integración con Ollama para interpretar frases en lenguaje natural ("quiero algo ligero con pollo").
- Fallback automático por palabras clave cuando el LLM no está disponible o devuelve un término no reconocido.
- Detección dinámica del modelo Ollama disponible (sin hardcoding).
- Generación de PDF con ingredientes, instrucciones y macronutrientes por ración.
- Base de conocimiento con 21 recetas y sus ingredientes asociados.

---

## 🗂️ Arquitectura

El sistema sigue la estructura clásica de un sistema experto:

```
Entrada usuario (lenguaje natural)
        │
        ▼
┌───────────────────────┐
│  LLM (Ollama)         │  extrae término clave
│  + Fallback local     │  "quiero pollo" → "pollo"
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Motor de inferencia  │  ChefExperto (experta)
│  Reglas + salience    │  dispara reglas sobre hechos
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Base de conocimiento │  Plato · Ingrediente · Deseo
│  (hechos estáticos)   │  RecetaSugerida (inferido)
└───────────┬───────────┘
            │
            ▼
   Recetas sugeridas + PDF
```

### Hechos (Facts)

| Hecho | Campos | Descripción |
|---|---|---|
| `Plato` | `nombre`, `instrucciones`, `macros` | Receta completa con macronutrientes |
| `Ingrediente` | `plato`, `ingrediente` | Relación plato → ingrediente |
| `Deseo` | `termino`, `contexto` | Intención del usuario (inferida por el LLM) |
| `RecetaSugerida` | `plato`, `instrucciones`, `macros` | Resultado generado por el motor |

### Reglas

| Regla | Salience | Condición |
|---|---|---|
| `coincidir_nombre` | 10 | `termino` es subcadena del nombre del plato |
| `coincidencia_semantica` | 8 | Coincidencia por contexto ("ligero" → ensaladas, "caliente" → sopas) |
| `coincidir_ingrediente` | 5 | `termino` coincide exactamente con un ingrediente |

---

## ⚙️ Instalación

**Requisitos:** Python 3.8+, Ollama instalado y corriendo.

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd chef-privado

# Instalar dependencias Python
pip install experta fpdf ollama

# Arrancar Ollama con un modelo (si no lo tienes ya)
ollama pull llama3.2
ollama serve
```

---

## 🚀 Uso

```bash
python chef_experto.py
```

```
========================================
👨‍🍳 CHEF PRIVADO (CON OLLAMA LOCAL)
========================================

1. Buscar receta (IA Local)
2. Generar PDF de la última búsqueda
3. Salir
```

### Opción 1 — Buscar receta

El sistema acepta frases en lenguaje natural:

```
Describe lo que quieres comer: quiero pollo

🤖 Consultando a Ollama (LLM local)...
   ✅ LLM: termino='pollo', contexto=[]

🍽️ Recetas Sugeridas:
1. Pollo al horno con especias  (Calorías: 450 kcal)
2. Ensalada Cesar               (Calorías: 320 kcal)
3. Pollo al ajillo              (Calorías: 400 kcal)
4. Tacos de pollo               (Calorías: 500 kcal)
```

Ejemplos de frases reconocidas:

- `"quiero pollo"` → platos con pollo
- `"algo ligero y fresco"` → ensaladas
- `"sopa caliente"` → sopas
- `"algo dulce"` → postres con chocolate
- `"tengo huevos en la nevera"` → revueltos

### Opción 2 — Generar PDF

Tras hacer una búsqueda, genera un PDF con la receta elegida que incluye lista de ingredientes, instrucciones paso a paso y tabla de macronutrientes. El archivo se guarda en el directorio actual como `receta_<nombre_plato>.pdf`.

---

## 🔄 Mecanismo de fallback

Si Ollama no está disponible o devuelve un término que no produce resultados, el sistema aplica dos niveles de respaldo sin interrumpir la ejecución:

1. **Fallback semántico local:** detecta palabras clave como "ligero", "sopa", "chocolate" directamente en el texto del usuario.
2. **Fallback por palabras:** si aun así no hay resultados, prueba cada palabra individual del texto (filtrando artículos y preposiciones cortas) hasta encontrar coincidencias en la base de conocimiento.

---

## 📦 Estructura del proyecto

```
chef-privado/
├── chef_experto.py   # Código principal (hechos, reglas, motor, PDF)
└── README.md
```

---

## 🛠️ Dependencias

| Librería | Versión mínima | Uso |
|---|---|---|
| `experta` | 1.9.4 | Motor de inferencia (sistema experto) |
| `fpdf` | 1.7.2 | Generación de PDF |
| `ollama` | 0.1.0 | Cliente para LLM local |

---

## 📝 Notas técnicas

**Compatibilidad Python 3.10+:** el archivo incluye un parche para `collections.Mapping` que fue eliminado en Python 3.10 pero que `experta` aún referencia internamente.

**Encoding PDF:** `fpdf` (versión clásica) no soporta UTF-8 con fuentes estándar. El código codifica los textos a `latin-1` con reemplazo de caracteres para evitar errores con tildes y la ñ. Si se migra a `fpdf2`, este paso puede eliminarse.

**Modelo Ollama:** el sistema detecta automáticamente el primer modelo disponible mediante `ollama.list()`, por lo que no es necesario configurar ningún nombre de modelo manualmente.