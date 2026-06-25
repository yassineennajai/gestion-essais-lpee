from flask import Blueprint, request, jsonify
from extensions import db
from models import Ville

routes_villes = Blueprint('routes_villes', __name__)

@routes_villes.route('/api/villes', methods=['GET'])
def get_villes():
    villes = Ville.query.all()
    return jsonify([v.to_dict() for v in villes]), 200

@routes_villes.route('/api/villes', methods=['POST'])
def add_ville():
    data = request.get_json()
    if not data or 'nom_ville' not in data or not data['nom_ville'].strip():
        return jsonify({"error": "Le nom de la ville est obligatoire"}), 400
    
    new_ville = Ville(nom_ville=data['nom_ville'].strip())
    db.session.add(new_ville)
    db.session.commit()
    return jsonify(new_ville.to_dict()), 201

@routes_villes.route('/api/villes/<int:id>', methods=['PUT'])
def update_ville(id):
    ville = Ville.query.get_or_404(id)
    data = request.get_json()
    if not data or 'nom_ville' not in data or not data['nom_ville'].strip():
        return jsonify({"error": "Le nom de la ville est obligatoire"}), 400
    
    ville.nom_ville = data['nom_ville'].strip()
    db.session.commit()
    return jsonify(ville.to_dict()), 200

@routes_villes.route('/api/villes/<int:id>', methods=['DELETE'])
def delete_ville(id):
    ville = Ville.query.get_or_404(id)
    try:
        db.session.delete(ville)
        db.session.commit()
        return jsonify({"message": "Ville supprimée avec succès"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Impossible de supprimer cette ville car elle est liée à d'autres entités"}), 400