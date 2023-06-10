from flask import Flask, request, jsonify, Response
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash # Para encriptar contraseñas
from flask_cors import CORS
from bson import json_util
import openai
import os

app = Flask(__name__)
CORS(app)
openai.api_key = os.environ['API_KEY']

# Base de Datos
client=MongoClient('mongodb+srv://Luis:Lomaximoluis02@cluster0.f6yp4mn.mongodb.net/?retryWrites=true&w=majority')
db = client['InfoChat']
user_collection = db['users']

@app.route('/users', methods=['POST'])
def create_users():
    username = request.json['username']
    password = request.json['password']
    email = request.json['email']
    
    if username and email and password:
        
        hashed_password = generate_password_hash(password)
        user_data = (
            {'username': username, 'email': email, 'password': hashed_password}
        )
        result = user_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        response = {
            'id': str(id),
            'username': username,
            'email': email,
            'password': hashed_password
        }
        return response
    else:
        return {'message': 'Incomplete data'}

    return {'message': 'received'}

@app.route('/users', methods=['GET'])
def get_users():
    users = user_collection.find()
    reponse = json_util.dumps(users)
    return Response(reponse, mimetype='application/json')
# manejo de errores
@app.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'message': 'Resource Not Found: ' + request.url,
        'status': 404
    })
    response.status_code = 404
    return response


# Configuracion de Chatbot
openai.api_key = os.environ['API_KEY']
context = {"role": "system", "content": "Eres un asistente muy útil llamado InfoChat, para la  escuela de informatica de la Universidad nacional de Trujillo."}
messages = [context]

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data["query"]

    messages.append({"role": "user", "content": query})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    response_content = response.choices[0].message.content

    messages.append({"role": "assistant", "content": response_content})

    response = {
        "message": response_content
    }

    return jsonify(response)

# Fin de configuracion de Chatbot

# Configura el servicio de envío de correos electrónicos
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-password'
mail = Mail(app)

@app.route("/submit_comment", methods=["POST"])
def submit_comment():
    data = request.get_json()
    comment = data["comment"]
    name = data["name"]
    email = data["email"]

    # Guardar los datos en la base de datos
    # Ejemplo con SQLAlchemy:
    # from models import Comment
    # comment_entry = Comment(name=name, email=email, comment=comment)
    # db.session.add(comment_entry)
    # db.session.commit()

    # Enviar el correo de confirmación
    msg = Message("Confirmación de queja", sender='your-email@example.com', recipients=[email])
    msg.body = f"Hola {name}, hemos recibido tu queja. Gracias por tu feedback."
    mail.send(msg)

    response = {
        "message": "¡Gracias por tu queja! Hemos recibido tu feedback y te hemos enviado un correo de confirmación."
    }

    return jsonify(response)

# Fin de configuracion de envío de correos electrónicos

if __name__ == "__main__":
    app.run(debug=True)
