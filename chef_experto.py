import collections
if not hasattr(collections, 'Mapping'):
    import collections.abc
    collections.Mapping = collections.abc.Mapping
    collections.MutableMapping = collections.abc.MutableMapping

from experta import Fact, KnowledgeEngine, Rule, TEST, MATCH
import json
import os
import ollama
from fpdf import FPDF

# ==========================================
# 1. DEFINICIÓN DE HECHOS (FACTS)
# ==========================================

class Plato(Fact):
    """Nombre del plato y sus instrucciones de preparacion."""
    nombre: str
    instrucciones: str
    macros: dict
    pass

class Ingrediente(Fact):
    """Relacion plato -> ingrediente necesario."""
    plato: str
    ingrediente: str
    pass

class Deseo(Fact):
    """Lo que el usuario expresa que quiere comer (termino de busqueda)."""
    termino: str
    contexto: list
    pass

class RecetaSugerida(Fact):
    """Resultado de la inferencia: plato que satisface el deseo."""
    plato: str
    instrucciones: str
    macros: dict
    pass

# ==========================================
# 2. LLM & LÓGICA LOCAL (Ollama)
# ==========================================

# ==========================================
# 2. LLM & LÓGICA LOCAL (Ollama) - CORREGIDO
# ==========================================

def _analisis_local(texto_usuario):
    """
    Lógica simple de respaldo si Ollama falla.
    Busca palabras clave en el texto del usuario directamente.
    """
    texto = texto_usuario.lower()
    termino = texto_usuario
    contexto = []

    if "ligero" in texto or "fresco" in texto or "ensalada" in texto:
        termino = "ensalada"
        contexto = ["ligero"]
    elif "caliente" in texto or "caldo" in texto or "sopa" in texto:
        termino = "sopa"
        contexto = ["caliente"]
    elif "dulce" in texto or "chocolate" in texto:
        termino = "chocolate"
        contexto = ["dulce"]
    else:
        # Buscar ingrediente simple
        ingredientes_posibles = ["pollo", "huevo", "cerdo", "tomate", "cebolla", "arroz", "pasta", "queso", "pan"]
        for ing in ingredientes_posibles:
            if ing in texto:
                termino = ing
                break
    
    print(f"   🛡️  Respaldo local: termino='{termino}', contexto={contexto}")
    return Deseo(termino=termino, contexto=contexto)

def _detectar_modelo_ollama():
    """
    Devuelve el nombre del primer modelo disponible en Ollama.
    Si no hay ninguno, devuelve None.

    FIX Bug 1: el modelo estaba hardcoded como "llama3", lo que provocaba
    una excepción si el usuario tenía un modelo con otro nombre (llama3.2,
    mistral, etc.) y dejaba la búsqueda sin resultado.
    """
    try:
        modelos = ollama.list().get('models', [])
        if modelos:
            nombre = modelos[0].get('name') or modelos[0].get('model', '')
            print(f"   🔍 Modelo Ollama detectado: {nombre}")
            return nombre
    except Exception:
        pass
    return None


def llm_interpretar_deseo(texto_usuario):
    """
    Llama a Ollama y garantiza que siempre devuelva un objeto Deseo válido.
    Incluye lógica de respaldo si el LLM falla.
    """
    if not ollama:
        print("⚠️  Ollama no disponible. Usando lógica local.")
        return _analisis_local(texto_usuario)

    # FIX Bug 1: detectar el modelo disponible en lugar de usar "llama3" fijo
    model_name = _detectar_modelo_ollama()
    if not model_name:
        print("⚠️  No hay modelos cargados en Ollama. Usando lógica local.")
        return _analisis_local(texto_usuario)

    prompt = f"""
    Eres un traductor de cocina. Entrada: "{texto_usuario}".
    Devuelve SOLO un JSON válido, sin texto extra, sin markdown, sin saltos de línea innecesarios:
    {{"termino": "palabra_clave", "contexto": ["etiqueta"]}}
    
    Reglas:
    1. "ligero", "fresco" -> termino: "ensalada", contexto: ["ligero"]
    2. "caliente", "sopa" -> termino: "sopa", contexto: ["caliente"]
    3. "dulce", "chocolate" -> termino: "chocolate", contexto: ["dulce"]
    4. Ingrediente directo -> termino: "INGREDIENTE", contexto: []
    
    Ejemplo de salida correcta: {{"termino": "ensalada", "contexto": ["ligero"]}}
    """

    try:
        response = ollama.chat(model=model_name, messages=[{'role': 'user', 'content': prompt}])
        contenido = response['message']['content']
        
        contenido = contenido.strip()
        if contenido.startswith("```json"):
            contenido = contenido[7:]
        elif contenido.startswith("```"):
            contenido = contenido[3:]
        if contenido.endswith("```"):
            contenido = contenido[:-3]
        contenido = contenido.replace("\n", " ").replace("\r", "").strip()
        
        import re
        json_match = re.search(r'\{.*\}', contenido, re.DOTALL)
        if json_match:
            contenido = json_match.group(0)
        
        datos = json.loads(contenido)
        termino = datos.get("termino", "").strip()
        contexto = datos.get("contexto", [])
        
        if not isinstance(contexto, list):
            contexto = []
        
        if termino == texto_usuario or termino == "":
            print("   ⚠️  LLM devolvió dato genérico. Usando lógica local.")
            return _analisis_local(texto_usuario)
            
        print(f"   ✅ LLM: termino='{termino}', contexto={contexto}")
        return Deseo(termino=termino, contexto=contexto)

    except json.JSONDecodeError as e:
        print(f"   ❌ Error JSON en respuesta de Ollama: {e}. Usando lógica local.")
        return _analisis_local(texto_usuario)
    except Exception as e:
        print(f"   ❌ Error general en Ollama: {e}. Usando lógica local.")
        return _analisis_local(texto_usuario)


def obtener_ingredientes(nombre_plato):
    """Retorna la lista de ingredientes para un plato específico."""
    mapping = {
        "Pollo al horno con especias": ["pollo", "sal", "pimienta", "romero", "ajo", "papas"],
        "Ensalada Cesar": ["lechuga", "pollo", "aderezo cesar", "crutones"],
        "Sopa de tomate": ["tomate", "cebolla", "ajo", "caldo"],
        "Tacos de carnitas": ["cerdo", "tortillas", "cebolla", "cilantro", "salsa"],
        "Pastel de chocolate": ["huevos", "azucar", "harina", "cacao", "levadura"],
        "Revuelto de champinones": ["champinones", "ajo", "huevo", "aceite"],
        "Ceviche de pescado": ["pescado", "limon", "cebolla morada", "cilantro", "aji"],
        "Ensalada de frutas": ["frutas variadas", "limon", "yogur natural"],
        "Ensalada de verduras": ["verduras frescas", "limon", "yogur natural"],
        "Ensalada de aguacate": ["aguacate", "limon", "yogur natural"],
        "Ensalada de lechuga y tomate": ["lechuga", "tomate", "limon", "yogur natural"],
        "Ensalada de zanahorias": ["zanahorias", "limon", "yogur natural"],
        "Natillas caseras": ["leche", "azucar", "vainilla", "huevos"],
        "Pastel de manzana": ["harina", "mantequilla", "azucar", "manzanas", "canela"],
        "Brownie de chocolate": ["chocolate", "mantequilla", "huevos", "azucar", "harina"],
        "Patata asada con romero": ["patatas", "romero", "aceite de oliva", "sal"],
        "Sopa de verduras": ["cebolla", "ajo", "verduras", "caldo"],
        "Macarrones con queso": ["macarrones", "queso", "leche", "mantequilla"],
        "Pollo al ajillo": ["pollo", "ajo", "aceite de oliva", "vino blanco"],
        "Tacos de pollo": ["pollo", "tortillas", "cebolla", "cilantro", "salsa"],
        "Ensalada de aguacate y tomate": ["aguacate", "tomate", "limon", "yogur natural"],
    }
    return mapping.get(nombre_plato, [])

def obtener_macros_ollama(nombre_plato):
    base_datos = {
        "Pollo al horno con especias": {"calorias": 450, "proteinas": 35, "carbos": 15, "grasas": 20},
        "Ensalada Cesar": {"calorias": 320, "proteinas": 18, "carbos": 10, "grasas": 22},
        "Sopa de tomate": {"calorias": 150, "proteinas": 5, "carbos": 25, "grasas": 4},
        "Tacos de carnitas": {"calorias": 600, "proteinas": 30, "carbos": 45, "grasas": 30},
        "Pastel de chocolate": {"calorias": 400, "proteinas": 6, "carbos": 60, "grasas": 12},
        "Revuelto de champinones": {"calorias": 220, "proteinas": 14, "carbos": 4, "grasas": 16},
        "Ceviche de pescado": {"calorias": 280, "proteinas": 28, "carbos": 10, "grasas": 8},
        "Ensalada de frutas": {"calorias": 150, "proteinas": 3, "carbos": 25, "grasas": 4},
        "Ensalada de verduras": {"calorias": 100, "proteinas": 2, "carbos": 15, "grasas": 0},
        "Ensalada de aguacate": {"calorias": 80, "proteinas": 2, "carbos": 10, "grasas": 0},
        "Ensalada de lechuga y tomate": {"calorias": 50, "proteinas": 1, "carbos": 5, "grasas": 0},
        "Ensalada de zanahorias": {"calorias": 40, "proteinas": 1, "carbos": 5, "grasas": 0},
        "Natillas caseras": {"calorias": 250, "proteinas": 6, "carbos": 30, "grasas": 8},
        "Pastel de manzana": {"calorias": 350, "proteinas": 4, "carbos": 50, "grasas": 10},
        "Brownie de chocolate": {"calorias": 450, "proteinas": 5, "carbos": 60, "grasas": 20},
        "Patata asada con romero": {"calorias": 200, "proteinas": 6, "carbos": 20, "grasas": 10},
        "Sopa de verduras": {"calorias": 120, "proteinas": 4, "carbos": 20, "grasas": 3},
        "Macarrones con queso": {"calorias": 500, "proteinas": 15, "carbos": 70, "grasas": 20},
        "Pollo al ajillo": {"calorias": 400, "proteinas": 30, "carbos": 10, "grasas": 15},
        "Tacos de pollo": {"calorias": 500, "proteinas": 30, "carbos": 45, "grasas": 30},
        "Ensalada de aguacate y tomate": {"calorias": 80, "proteinas": 2, "carbos": 10, "grasas": 0},
    }
    return base_datos.get(nombre_plato, {"calorias": 0, "proteinas": 0, "carbos": 0, "grasas": 0})

# ==========================================
# 3. MOTOR DE INFERENCIA
# ==========================================

class ChefExperto(KnowledgeEngine):
    @Rule(
        Deseo(termino=MATCH.t),
        Plato(nombre=MATCH.n, instrucciones=MATCH.i, macros=MATCH.m),
        TEST(lambda t, n: t.lower() in n.lower()),
        salience=10
    )
    def coincidir_nombre(self, t, n, i, m):
        self.declare(RecetaSugerida(plato=n, instrucciones=i, macros=m))

    @Rule(
        Deseo(termino=MATCH.t),
        Ingrediente(plato=MATCH.p, ingrediente=MATCH.ing),
        Plato(nombre=MATCH.p, instrucciones=MATCH.i, macros=MATCH.m),
        TEST(lambda t, ing: t.lower() == ing.lower()),
        salience=5
    )
    def coincidir_ingrediente(self, t, p, i, m):
        self.declare(RecetaSugerida(plato=p, instrucciones=i, macros=m))

    @Rule(
        Deseo(termino=MATCH.t, contexto=MATCH.ctx),
        Plato(nombre=MATCH.n, instrucciones=MATCH.i, macros=MATCH.m),
        TEST(lambda t, n, ctx: 
             t.lower() in n.lower() or
             ("ligero" in ctx and "ensalada" in n.lower()) or
             ("caliente" in ctx and "sopa" in n.lower()) or
             ("dulce" in ctx and "chocolate" in n.lower())
        ),
        salience=8
    )
    def coincidencia_semantica(self, t, n, i, m, ctx):
        self.declare(RecetaSugerida(plato=n, instrucciones=i, macros=m))

# ==========================================
# 4. BASE DE CONOCIMIENTO (CORREGIDA)
# ==========================================

def cargar_conocimiento(engine):
    """Declara los hechos en el motor (CORREGIDO: ahora declara hechos, no retorna lista)."""
    recetas = [
        ("Pollo al horno con especias", "1. Adobar el pollo con sal, pimienta, romero y ajo. 2. Hornear a 180°C por 45 min. 3. Servir con papas.", {"calorias": 450, "proteinas": 35, "carbos": 15, "grasas": 20}),
        ("Ensalada Cesar", "1. Lavar la lechuga. 2. Agregar pollo desmenuzado. 3. Añadir aderezo Cesar y crutones.", {"calorias": 320, "proteinas": 18, "carbos": 10, "grasas": 22}),
        ("Sopa de tomate", "1. Sofreir cebolla y ajo. 2. Agregar tomates pelados y caldo. 3. Cocinar 20 min y licuar.", {"calorias": 150, "proteinas": 5, "carbos": 25, "grasas": 4}),
        ("Tacos de carnitas", "1. Dorar la carne de cerdo en su grasa. 2. Calentar tortillas. 3. Servir con cebolla, cilantro y salsa.", {"calorias": 600, "proteinas": 30, "carbos": 45, "grasas": 30}),
        ("Pastel de chocolate", "1. Batir huevos con azucar. 2. Agregar harina, cacao y levadura. 3. Hornear 30 min a 180°C.", {"calorias": 400, "proteinas": 6, "carbos": 60, "grasas": 12}),
        ("Revuelto de champinones", "1. Saltear champinones laminados con ajo. 2. Incorporar huevo batido. 3. Cocinar hasta cuajar.", {"calorias": 220, "proteinas": 14, "carbos": 4, "grasas": 16}),
        ("Ceviche de pescado", "1. Cortar pescado en cubos. 2. Marinar con jugo de limon, cebolla morada, cilantro y aji. 3. Reposar 20 min.", {"calorias": 280, "proteinas": 28, "carbos": 10, "grasas": 8}),
        ("Ensalada de frutas", "1. Cortar frutas. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 150, "proteinas": 3, "carbos": 25, "grasas": 4}),
        ("Ensalada de verduras", "1. Cortar verduras. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 100, "proteinas": 2, "carbos": 15, "grasas": 0}),
        ("Ensalada de aguacate", "1. Cortar aguacate. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 80, "proteinas": 2, "carbos": 10, "grasas": 0}),
        ("Ensalada de lechuga y tomate", "1. Cortar lechuga y tomate. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 50, "proteinas": 1, "carbos": 5, "grasas": 0}),
        ("Ensalada de zanahorias", "1. Cortar zanahorias. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 40, "proteinas": 1, "carbos": 5, "grasas": 0}),
        ("Natillas caseras", "1. Calentar leche con azucar y vainilla. 2. Batir huevos y agregar a la leche. 3. Cocinar a fuego bajo hasta espesar.", {"calorias": 250, "proteinas": 6, "carbos": 30, "grasas": 8}),
        ("Pastel de manzana", "1. Preparar masa con harina, mantequilla y azucar. 2. Rellenar con manzanas cortadas y canela. 3. Hornear 40 min a 180°C.", {"calorias": 350, "proteinas": 4, "carbos": 50, "grasas": 10}),
        ("Brownie de chocolate", "1. Derretir chocolate con mantequilla. 2. Batir huevos con azucar. 3. Agregar harina y mezclar. 4. Hornear 25 min a 180°C.", {"calorias": 450, "proteinas": 5, "carbos": 60, "grasas": 20}),
        ("Patata asada con romero", "1. Lavar patatas y pintar. 2. Hornear a 180°C por 20 min. 3. Servir con salsa de romero.", {"calorias": 200, "proteinas": 6, "carbos": 20, "grasas": 10}),
        ("Sopa de verduras", "1. Sofreir cebolla y ajo. 2. Agregar verduras picadas y caldo. 3. Cocinar 30 min y servir.", {"calorias": 120, "proteinas": 4, "carbos": 20, "grasas": 3}),
        ("Macarrones con queso", "1. Cocer macarrones. 2. Preparar salsa con queso y leche. 3. Mezclar todo y gratinar.", {"calorias": 500, "proteinas": 15, "carbos": 70, "grasas": 20}),
        ("Pollo al ajillo", "1. Dorar pollo con ajo en aceite de oliva. 2. Agregar vino blanco y cocinar hasta reducir.", {"calorias": 400, "proteinas": 30, "carbos": 10, "grasas": 15}),
        ("Tacos de pollo", "1. Dorar pollo en su grasa. 2. Calentar tortillas. 3. Servir con cebolla, cilantro y salsa.", {"calorias": 500, "proteinas": 30, "carbos": 45, "grasas": 30}),
        ("Ensalada de aguacate y tomate", "1. Cortar aguacate y tomate. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 80, "proteinas": 2, "carbos": 10, "grasas": 0}),
    ]

    # Declara todos los platos y sus ingredientes
    for nombre, instrucciones, macros in recetas:
        engine.declare(Plato(nombre=nombre, instrucciones=instrucciones, macros=macros))
        for ing in obtener_ingredientes(nombre):
            engine.declare(Ingrediente(plato=nombre, ingrediente=ing))

# ==========================================
# 5. GENERACIÓN DE PDF
# ==========================================

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Chef Privado - Tu Receta', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf(datos_receta):
    """
    Genera un PDF con la receta seleccionada.

    FIX Bug 3: las claves del dict que llega de buscar_recetas_por_deseo son:
      - 'plato'         (no cambia)
      - 'instrucciones' (antes buscaba 'preparacion' → fallaba silenciosamente)
      - 'macros'        (antes buscaba 'nutricion'   → fallaba silenciosamente)
      - 'ingredientes'  (antes no existía en el dict → lista vacía en el PDF)
    
    FIX Bug 3b: dentro de macros, la clave es 'carbos', no 'carbohidratos'.
    """
    from fpdf import FPDF

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        def txt(s):
            """Codifica la cadena a latin-1 reemplazando caracteres problemáticos.
            fpdf (versión clásica) no soporta UTF-8 con fuentes estándar; así
            evitamos UnicodeEncodeError con tildes y la ñ."""
            return s.encode('latin-1', 'replace').decode('latin-1')

        # 1. Título
        titulo = datos_receta.get('plato', 'Receta sin nombre')
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt(f"Receta: {titulo}"), ln=True, align='C')
        pdf.ln(8)

        # 2. Ingredientes  (FIX Bug 4: ahora existe la clave 'ingredientes')
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, txt("Ingredientes:"), ln=True)
        pdf.set_font("Arial", size=11)

        ingredientes = datos_receta.get('ingredientes', [])
        if not ingredientes:
            pdf.multi_cell(0, 8, txt("- No se encontraron ingredientes."))
        else:
            for ing in ingredientes:
                pdf.cell(5)
                pdf.multi_cell(0, 8, txt(f"- {ing}"))

        pdf.ln(5)

        # 3. Preparación  (FIX Bug 3: clave correcta es 'instrucciones')
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, txt("Preparacion:"), ln=True)
        pdf.set_font("Arial", size=11)

        instrucciones = datos_receta.get('instrucciones', '')  # FIX: era 'preparacion'
        pasos = instrucciones.split('. ') if isinstance(instrucciones, str) else instrucciones
        if not pasos:
            pdf.multi_cell(0, 8, txt("- No se encontraron pasos."))
        else:
            for paso in pasos:
                if paso.strip():
                    pdf.multi_cell(0, 8, txt(f"  {paso.strip()}"))

        pdf.ln(5)

        # 4. Información Nutricional  (FIX Bug 3: clave correcta es 'macros')
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, txt("Informacion Nutricional (por racion):"), ln=True)
        pdf.set_font("Arial", size=11)

        macros = datos_receta.get('macros', {})        # FIX: era 'nutricion'
        calorias  = macros.get('calorias',  0)
        proteinas = macros.get('proteinas', 0)
        grasas    = macros.get('grasas',    0)
        carbos    = macros.get('carbos',    0)          # FIX: era 'carbohidratos'

        pdf.multi_cell(0, 8, txt(f"  Calorias:      {calorias} kcal"))
        pdf.multi_cell(0, 8, txt(f"  Proteinas:     {proteinas} g"))
        pdf.multi_cell(0, 8, txt(f"  Carbohidratos: {carbos} g"))
        pdf.multi_cell(0, 8, txt(f"  Grasas:        {grasas} g"))

        # Guardar archivo
        nombre_seguro = "".join(c for c in titulo if c.isalnum() or c in (' ', '_')).strip()
        nombre_archivo = f"receta_{nombre_seguro.lower().replace(' ', '_')}.pdf"
        pdf.output(nombre_archivo)
        print(f"\n✅ PDF generado: {nombre_archivo}")

    except Exception as e:
        print(f"\n❌ Error al generar el PDF: {e}")
        print(f"   Claves disponibles: {list(datos_receta.keys())}")

# ==========================================
# 6. INTERFAZ DE USUARIO | MAIN
# ==========================================

def buscar_recetas_por_deseo(texto_usuario):
    engine = ChefExperto()
    engine.reset()
    cargar_conocimiento(engine)

    print("🤖 Consultando a Ollama (LLM local)...")
    deseo_fact = llm_interpretar_deseo(texto_usuario)
    engine.declare(deseo_fact)
    engine.run()

    sugerencias = _recoger_sugerencias(engine)

    # FIX Bug 2: si el LLM extrajo un término que no dio resultados (p.ej.
    # "pollo asado" en vez de "pollo"), probamos cada palabra individual del
    # texto original hasta encontrar coincidencias.
    if not sugerencias:
        palabras = [p for p in texto_usuario.lower().split() if len(p) > 3]
        for palabra in palabras:
            print(f"   🔄 Sin resultados, probando palabra: '{palabra}'")
            engine2 = ChefExperto()
            engine2.reset()
            cargar_conocimiento(engine2)
            engine2.declare(Deseo(termino=palabra, contexto=[]))
            engine2.run()
            sugerencias = _recoger_sugerencias(engine2)
            if sugerencias:
                break

    return sugerencias


def _recoger_sugerencias(engine):
    """Extrae los hechos RecetaSugerida del motor y los convierte en dicts.

    FIX Bug 4: ahora añadimos la lista de 'ingredientes' al dict para que
    generar_pdf() pueda encontrarla con datos_receta.get('ingredientes').
    """
    resultado = []
    for f in engine.facts.values():
        if isinstance(f, RecetaSugerida):
            nombre = f['plato']
            resultado.append({
                'plato':         nombre,
                'instrucciones': f['instrucciones'],
                'macros':        f['macros'],
                'ingredientes':  obtener_ingredientes(nombre),  # FIX Bug 4
            })
    return resultado

def main():
    print("\n" + "=" * 55)
    print("👨‍🍳 CHEF PRIVADO (CON OLLAMA LOCAL)")
    print("=" * 55)
    print("Prueba: 'quiero algo ligero', 'tengo ganas de pollo', 'quiero sopa caliente'")

    # Verificar si Ollama está corriendo
    if ollama:
        try:
            ollama.list()
            print("✅ Ollama detectado y listo.")
        except:
            print("⚠️  Advertencia: No se pudo conectar con Ollama. Asegúrate de que esté corriendo (ollama serve).")

    sugerencias = []  # Variable global para guardar las sugerencias entre opciones

    while True:
        print("\n1. Buscar receta (IA Local)")
        print("2. Generar PDF de la última búsqueda")
        print("3. Salir")
        opcion = input("Selecciona una opción: ").strip()

        if opcion == "1":
            texto_usuario = input("\nDescribe lo que quieres comer: ").strip()
            if not texto_usuario:
                print("❌ No escribiste nada.")
                continue

            sugerencias = buscar_recetas_por_deseo(texto_usuario)

            if sugerencias:
                print("\n🍽️ Recetas Sugeridas:")
                for idx, s in enumerate(sugerencias, 1):
                    print(f"{idx}. {s['plato']} (Calorías: {s['macros']['calorias']} kcal)")
            else:
                print("\n❌ No se encontraron recetas que coincidan con tu deseo.")

        elif opcion == "2":
            if not sugerencias:
                print("\n❌ Debes buscar una receta primero.")
                continue
            
            print("\n📄 Selecciona la receta para generar el PDF:")
            for idx, s in enumerate(sugerencias, 1):
                print(f"{idx}. {s['plato']}")
            
            entrada = input("\nNúmero de receta: ").strip()
            
            # Validación robusta
            if not entrada.isdigit():
                print(f"❌ '{entrada}' no es un número válido.")
                continue
            
            seleccion = int(entrada)
            if 1 <= seleccion <= len(sugerencias):
                receta_elegida = sugerencias[seleccion - 1]
                generar_pdf(receta_elegida)
            else:
                print(f"❌ El número {seleccion} está fuera del rango (1-{len(sugerencias)}).")

        elif opcion == "3":
            print("\n👋 ¡Hasta luego! ¡Que tengas un buen día!")
            break

        else:
            print("\n❌ Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    main()