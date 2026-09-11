import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS

from config import Config
from routes.api import api


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.register_blueprint(api)

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "404 - not found. Ironic."}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "500 - something broke."}), 500

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print()
    print("  AntiSearch backend")
    print(f"  -> http://127.0.0.1:{port}")
    print(f"  env={Config.ENV}  llm={'on' if Config.OPENAI_API_KEY else 'off'}  cache={Config.CACHE_TTL}s")
    print()
    app.run(host="0.0.0.0", port=port, debug=(Config.ENV == "development"))
