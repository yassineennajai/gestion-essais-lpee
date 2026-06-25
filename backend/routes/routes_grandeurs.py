from flask import Blueprint, request, jsonify
from extensions import db
from models import GrandeurMesure

from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

routes_grandeurs = Blueprint('routes_grandeurs', __name__)


@routes_grandeurs.route('/api/grandeurs', methods=['GET'])
@jwt_required()
def get_grandeurs():
    try:
        claims = get_jwt()
        role_code = claims.get("role_code")
        id_unite_user = claims.get("id_unite")

        query = GrandeurMesure.query

      
        if role_code != "ADMIN":
            if id_unite_user is not None:
                query = query.filter(GrandeurMesure.id_unite == int(id_unite_user))
            else:
          
                return jsonify([]), 200

        grandeurs = query.all()
        return jsonify([g.to_dict() for g in grandeurs]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@routes_grandeurs.route('/api/grandeurs', methods=['POST'])
@jwt_required()
def add_grandeur():
    try:
        claims = get_jwt()
        id_unite_user = claims.get("id_unite")

        data = request.get_json()
        if not data or 'code' not in data or 'libelle' not in data:
            return jsonify({"error": "Le code et le libellé sont obligatoires"}), 400
        
        new_grandeur = GrandeurMesure(
            code=data['code'].strip(),
            libelle=data['libelle'].strip(),
         
            id_unite=int(id_unite_user) if id_unite_user is not None else None
        )
        db.session.add(new_grandeur)
        db.session.commit()
        return jsonify(new_grandeur.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@routes_grandeurs.route('/api/grandeurs/<int:id>', methods=['PUT'])
@jwt_required()
def update_grandeur(id):
    try:
        claims = get_jwt()
        role_code = claims.get("role_code")
        id_unite_user = claims.get("id_unite")

        grandeur = GrandeurMesure.query.get_or_404(id)
        
        
        if role_code != "ADMIN" and grandeur.id_unite != (int(id_unite_user) if id_unite_user else None):
            return jsonify({"message": "Modification non autorisée"}), 403

        data = request.get_json()
        if not data or 'code' not in data or 'libelle' not in data:
            return jsonify({"error": "Le code et le libellé sont obligatoires"}), 400
        
        grandeur.code = data['code'].strip()
        grandeur.libelle = data['libelle'].strip()
        
        db.session.commit()
        return jsonify(grandeur.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@routes_grandeurs.route('/api/grandeurs/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_grandeur(id):
    try:
        claims = get_jwt()
        role_code = claims.get("role_code")
        id_unite_user = claims.get("id_unite")

        grandeur = GrandeurMesure.query.get_or_404(id)
        
   
        if role_code != "ADMIN" and grandeur.id_unite != (int(id_unite_user) if id_unite_user else None):
            return jsonify({"message": "Suppression non autorisée"}), 403

        db.session.delete(grandeur)
        db.session.commit()
        return jsonify({"message": "Grandeur de mesure supprimée"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Impossible de supprimer cette grandeur: {str(e)}"}), 400