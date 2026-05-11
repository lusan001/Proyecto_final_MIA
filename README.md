# 👨‍🍳 Sistema Experto: Chef Privado

**Chef Privado** es un sistema experto basado en reglas desarrollado en Python con la librería `experta`. El usuario expresa lo que desea comer (ingrediente o nombre de un plato) y el sistema sugiere recetas que coinciden, mostrando además las instrucciones de preparación.

## 📌 Características

- Motor de inferencia con dos reglas de producción.
- Coincidencia por **nombre** (subcadena) y por **ingrediente** (exacta).
- Interfaz interactiva en consola con menú.
- Base de conocimiento inicial con 7 recetas y sus ingredientes.
- Código limpio, comentado y compatible con Python 3.8+ (incluye parche para `collections.Mapping`).

## ⚙️ ¿Cómo funciona?

El sistema sigue la arquitectura clásica de un sistema experto:

### 1. Hechos (Facts)
- `Plato(nombre, instrucciones)`
- `Ingrediente(plato, ingrediente)`
- `Deseo(termino)`
- `RecetaSugerida(plato, instrucciones)`  *(inferido)*

### 2. Base de conocimiento
Declaración de hechos iniciales: 7 platos con sus recetas y una lista de ingredientes asociados a cada plato.

### 3. Motor de inferencia (Reglas)
| Regla | Prioridad | Condición | Acción |
|-------|-----------|-----------|--------|
| Coincidencia por nombre | 10 | `termino.lower() in nombre_plato.lower()` | Genera `RecetaSugerida` |
| Coincidencia por ingrediente | 5  | `termino == ingrediente` (exacto) | Genera `RecetaSugerida` |

### 4. Interfaz de usuario
Menú interactivo en terminal:

1. Buscar receta por lo que deseo comer  
2. Ver todas las recetas disponibles  
3. Salir  

## 🧪 Ejemplos de uso
### Ejemplo 1: Búsqueda por nombre parcial

¿Qué te apetece comer? (ej: 'pollo', 'chocolate', 'sopa'): pollo

✅ Encontradas 2 receta(s) para 'pollo':
1. Pollo al horno con especias
2. Ensalada César

¿Quieres ver la preparación de alguna? (número o 'no'): 1

🍽️  POLLO AL HORNO CON ESPECIAS
📖 Preparación:
   - 1. Adobar el pollo con sal, pimienta, romero y ajo.
   - 2. Hornear a 180°C por 45 min.
   - 3. Servir con papas.
El término "pollo" aparece en el nombre del primer plato y también es ingrediente de la Ensalada César.

### Ejemplo 2: Búsqueda por ingrediente exacto

¿Qué te apetece comer?: chocolate

✅ Encontradas 1 receta(s) para 'chocolate':
1. Pastel de chocolate

### Ejemplo 3: Búsqueda sin coincidencias

¿Qué te apetece comer?: pizza

😕 No tengo ninguna receta con 'pizza'. Prueba con otro ingrediente o nombre.

### Ejemplo 4: Ver todas las recetas
Opción 2 del menú → lista numerada de los 7 platos. Luego se puede elegir uno para ver su preparación.