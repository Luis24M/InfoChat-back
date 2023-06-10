from flask import Flask, request, jsonify, Response
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash # Para encriptar contraseñas
from flask_cors import CORS
from bson import json_util, ObjectId
import openai
import os

app = Flask(__name__)
CORS(app)
openai.api_key = os.environ['API_KEY']

# Base de Datos
client=MongoClient('mongodb+srv://Luis:Lomaximoluis02@cluster0.f6yp4mn.mongodb.net/?retryWrites=true&w=majority')
db = client['InfoChat']
user_collection = db['users']

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465  # Puerto para SSL
app.config['MAIL_USE_TLS'] = False  # No se utiliza TLS
app.config['MAIL_USE_SSL'] = True  # Se utiliza SSL
app.config['MAIL_USERNAME'] = 'luno2402@gmail.com'
app.config['MAIL_PASSWORD'] = 'lomaximoluis24'
mail = Mail(app)

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

@app.route('/users/<id>', methods=['GET'])
def get_user(id):
    user = user_collection.find_one({'_id': ObjectId(id)})
    reponse = json_util.dumps(user)
    return Response(reponse, mimetype='application/json')
    return {'message': id}

@app.route('/users/username/<username>', methods=['GET'])
def get_user_by_username(username):
    user = user_collection.find({'username': username})
    if user:
        response = json_util.dumps(user)
        return Response(response, mimetype='application/json')
    else:
        return jsonify({'message': 'User not found'})



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
def send_confirmation_email(email):
    msg = Message('Confirmación de comentario', sender='tu_correo_electronico', recipients=[email])
    msg.body = 'Gracias por tu comentario. Lo hemos recibido correctamente.'
    mail.send(msg)

# Fin de configuracion de envío de correos electrónicos

# Recibir comentarios
@app.route('/comments', methods=['POST'])
def create_comment():
    name = request.json['name']
    email = request.json['email']
    comment = request.json['comment']
    estado = 'peding'
    if name and email and comment:
        comment_data = {
            'name': name,
            'email': email,
            'comment': comment,
            'status': estado
        }
        
        comment_id = db.comments.insert_one(comment_data).inserted_id
        send_confirmation_email(email)

        response = {
            'id': str(comment_id),
            'name': name,
            'email': email,
            'comment': comment,
            'status': estado
        }
        
        return jsonify(response)
    else:
        return jsonify({'message': 'Invalid data'})

if __name__ == "__main__":
    app.run(debug=True)
