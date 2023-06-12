from flask import Flask, request, jsonify, Response
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash # Para encriptar contraseñas
from flask_cors import CORS
from bson import json_util, ObjectId
import openai
import os
import random
import string
import requests

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
app.config['MAIL_USERNAME'] = 'infochatunt@gmail.com'
app.config['MAIL_PASSWORD'] = 'rnuwpvlavldtjhnm'
mail = Mail(app)


@app.route('/check_auth', methods=['GET'])
def check_auth():
    # Aquí puedes realizar la lógica para verificar si el usuario está autenticado
    # Por ejemplo, puedes usar información de la sesión, cookies o tokens JWT
    # Devuelve un JSON con el estado de autenticación
    authenticated = True  # Cambia esto según tu lógica de autenticación
    return jsonify({'authenticated': authenticated})


# Validar usuario
def validate_user(email, password):
    user = user_collection.find_one({'email': email})
    if user and check_password_hash(user['password'], password):
        return True
    return False

def verify_email(email):
    api_key = 'b930a43d82b5429eb863eae4be1b77e1'
    url = f'https://api.zerobounce.net/v2/validate?api_key={api_key}&email={email}'

    response = requests.get(url)
    data = response.json()

    if data['status'] == 'valid':
        return True
    else:
        return False


@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
    
    if validate_user(email, password):
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid email or password'})

# Registrar nuevo usuario
@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    password = request.json['password']
    email = request.json['email']
    
    if username and email and password:
        existing_user = user_collection.find_one({'username': username})
        if existing_user:
            return jsonify({'message': 'Username already exists'})
        
        # Verificar si el correo electrónico es válido antes de registrarlo
        if not verify_email(email):
            return jsonify({'message': 'Invalid email'})

        hashed_password = generate_password_hash(password)
        user_data = {
            'username': username,
            'email': email,
            'password': hashed_password
        }
        result = user_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        response = {
            'id': user_id,
            'username': username,
            'email': email
        }
        
        # Enviar el correo de verificación de correo electrónico
        verification_link = generate_verification_link(email)
        send_verification_email(email, verification_link)

        return jsonify(response)
    else:
        return jsonify({'message': 'Incomplete data'})

def generate_verification_link(email):
    # Generar un token aleatorio para el enlace de verificación
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    # Guardar el token en la base de datos junto con el correo electrónico del usuario
    db.email_verification_tokens.insert_one({'email': email, 'token': token})
    
    # Generar el enlace de verificación de correo electrónico
    verification_link = f'file:///c%3A/Users/luism/Documents/web/verify_email?token={token}'
    
    return verification_link

def send_verification_email(email, verification_link):
    msg = Message('Verificación de correo electrónico', 
                  sender=('InfoChat','InfoChat@support.com'), 
                  recipients=[email])
    msg.body = f'Haz clic en el siguiente enlace para verificar tu correo electrónico:\n{verification_link}'
    mail.send(msg)


# Generar enlace de restablecimiento de contraseña
def generate_reset_password_link(email):
    # Generar un token aleatorio para el enlace de restablecimiento de contraseña
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    # Guardar el token en la base de datos junto con el correo electrónico del usuario
    db.reset_password_tokens.insert_one({'email': email, 'token': token})
    
    # Generar el enlace de restablecimiento de contraseña
    reset_password_link = f'http://tu-sitio-web.com/reset_password?token={token}'
    
    return reset_password_link

# Recuperar contraseña
@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.json['email']
    
    user = user_collection.find_one({'email': email})
    if user:
        # Generar el enlace de restablecimiento de contraseña
        reset_password_link = generate_reset_password_link(email)
        
        # Enviar el enlace por correo electrónico
        msg = Message('Restablecer contraseña', 
                      sender=('InfoChat','InfoChat@support.com'), 
                      recipients=[email])
        msg.body = f'Haz clic en el siguiente enlace para restablecer tu contraseña:\n{reset_password_link}'
        mail.send(msg)

        return jsonify({'message': 'Password reset link sent to your email'})
    else:
        return jsonify({'message': 'Email not found'})

# Restablecer contraseña
@app.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.json['email']
    token = request.json['token']
    new_password = request.json['new_password']
    
    # Verificar que el token sea válido para el correo electrónico dado
    reset_token = db.reset_password_tokens.find_one({'email': email, 'token': token})
    if reset_token:
        # Actualizar la contraseña del usuario en la base de datos
        hashed_password = generate_password_hash(new_password)
        user_collection.update_one({'email': email}, {'$set': {'password': hashed_password}})
        
        # Eliminar el token de restablecimiento de contraseña de la base de datos
        db.reset_password_tokens.delete_one({'email': email, 'token': token})
        
        return jsonify({'message': 'Password reset successful'})
    else:
        return jsonify({'message': 'Invalid token'})

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
        
        msg = Message('Gracias por tu Feedback', 
                      sender=('InfoChat','InfoChat@support.com'), 
                      recipients=[email])
        msg.body = f'''Hola {name},

Hemos recibido tu mensaje: "{comment}"

Gracias por tu Feedback. Queremos que sepas que valoramos tus comentarios y nos aseguraremos de abordar cualquier problema que hayas mencionado. Si es necesario, nos comunicaremos contigo para obtener más detalles.

Atentamente,
El equipo de InfoChat'''
        mail.send(msg)

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
