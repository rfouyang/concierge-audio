"""Provider-scoped saved audio routes."""

from flask import Blueprint, current_app, jsonify, request, send_file


def history_store():
    return current_app.extensions["tts_history"]


def create_history_blueprint():
    blueprint = Blueprint("history_api", __name__)

    @blueprint.get("/<provider>/history")
    def list_history(provider):
        try:
            return jsonify({"history": history_store().list(provider)})
        except ValueError:
            return jsonify(error="未知服务。"), 404

    @blueprint.get("/<provider>/history/<record_id>/audio")
    def audio(provider, record_id):
        try:
            path = history_store().path(provider, record_id, ".wav")
            if not path.is_file():
                raise FileNotFoundError(record_id)
            return send_file(path, mimetype="audio/wav", as_attachment=request.args.get("download") == "1", download_name=f"{provider}_{record_id}.wav")
        except (ValueError, FileNotFoundError):
            return jsonify(error="音频不存在。"), 404

    @blueprint.delete("/<provider>/history/<record_id>")
    def delete(provider, record_id):
        try:
            history_store().delete(provider, record_id)
            return "", 204
        except (ValueError, FileNotFoundError):
            return jsonify(error="音频不存在。"), 404

    return blueprint
