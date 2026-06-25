from flask import Blueprint, request, jsonify
from extensions import db
from models import DomaineActivite

routes_domaines = Blueprint('routes_domaines', __name__)

@routes_domaines.route('/api/domaines', methods=['GET'])
def get_domaines():
    domaines = DomaineActivite.query.all()
    return jsonify([d.to_dict() for d in domaines]), 200

@routes_domaines.route('/api/domaines', methods=['POST'])
def add_domaine():
    data = request.get_json()
    if not data or 'libelle' not in data or not data['libelle'].strip():
        return jsonify({"error": "Le libellé du domaine est obligatoire"}), 400
    
    new_domaine = DomaineActivite(libelle=data['libelle'].strip())
    db.session.add(new_domaine)
    db.session.commit()
    return jsonify(new_domaine.to_dict()), 201

@routes_domaines.route('/api/domaines/<int:id>', methods=['PUT'])
def update_domaine(id):
    domaine = DomaineActivite.query.get_or_404(id)
    data = request.get_json()
    if not data or 'libelle' not in data or not data['libelle'].strip():
        return jsonify({"error": "Le libellé du domaine est obligatoire"}), 400
    
    domaine.libelle = data['libelle'].strip()
    db.session.commit()
    return jsonify(domaine.to_dict()), 200

@routes_domaines.route('/api/domaines/<int:id>', methods=['DELETE'])
def delete_domaine(id):
    domaine = DomaineActivite.query.get_or_404(id)
    try:
        db.session.delete(domaine)
        db.session.commit()
        return jsonify({"message": "Domaine d'activité supprimé"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Impossible de supprimer ce domaine"}), 400