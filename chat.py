from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)
openai.api_key = "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"

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

if __name__ == "__main__":
    app.run()
