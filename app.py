from flask import Flask, render_template, request, jsonify
from motor_logico import EntrenadorExperto, Sintoma

app = Flask(__name__)

# Diccionario simple de mapeo (Palabra en texto -> Síntoma técnico)
DICCIONARIO_SINTOMAS = {
    'lateral': 'lateral_ofensivo',
    'subir': 'lateral_ofensivo',
    'avanzar': 'lateral_ofensivo',
    'contraataque': 'contraataque_rival',
    'ataque': 'contraataque_rival',
    'veloz': 'contraataque_rival',
    'pérdida': 'pérdidas_centro',
    'pérdidas': 'pérdidas_centro',
    'robo': 'pérdidas_centro',
    'medio': 'presion_baja',
    'lento': 'velocidad_baja',
    'cansado': 'cansancio',
    'agotado': 'cansancio',
    'rodilla': 'dolor_rodilla',
    'pierna': 'dolor_rodilla',
    'cojear': 'cojera',
    'cojea': 'cojera',
    'calambre': 'calambre',
    'dolor': 'dolor_localizado',
    'golpe': 'golpe_cabeza',
    'confuso': 'confusion',
    'mareo': 'confusion'
}

def extraer_sintomas_simple(texto_usuario):
    """Busca palabras clave en el texto y devuelve síntomas detectados."""
    texto = texto_usuario.lower()
    encontrados = []
    
    for palabra, sintoma in DICCIONARIO_SINTOMAS.items():
        if palabra in texto:
            # Evitar duplicados
            if sintoma not in encontrados:
                encontrados.append(sintoma)
    
    return [(s, 1.0) for s in encontrados]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analizar', methods=['POST'])
def analizar():
    data = request.json
    texto_usuario = data.get('texto', '')
    
    if not texto_usuario:
        return jsonify({"error": "No se proporcionó texto"}), 400

    # 1. Extraer síntomas (Solo diccionario, sin IA)
    sintomas_detectados = extraer_sintomas_simple(texto_usuario)
    
    # 2. Inicializar Motor Experto
    engine = EntrenadorExperto()
    engine.reset()
    
    # 3. Inyectar síntomas
    for nombre, confianza in sintomas_detectados:
        engine.declare(Sintoma(nombre=nombre, confianza=confianza))
    
    # 4. Ejecutar reglas
    engine.run()
    resultados = engine.obtener_resultados()
    
    # 5. Retornar JSON
    return jsonify({
        "sintomas": sintomas_detectados,
        "diagnosticos": resultados
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)