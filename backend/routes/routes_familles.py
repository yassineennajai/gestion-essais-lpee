

from flask import Blueprint, request, jsonify
from models import Famille, SousFamille
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

familles_bp = Blueprint('familles', __name__)


@familles_bp.route('/api/familles', methods=['GET'])
@jwt_required()
def get_familles():
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        
        role_code = claims.get("role_code") 
        id_unite = claims.get("id_unite")
        id_unite_int = int(id_unite) if id_unite is not None else None

     
        if role_code == "ADMIN":
            familles = Famille.query.all()
        else:
            if id_unite_int is not None:
                familles = Famille.query.filter_by(id_unite=id_unite_int).all()
            else:
                return jsonify([]), 200
    
        resultat = []
        for f in familles:
            list_sf = []
        
            if hasattr(f, 'sous_familles') and f.sous_familles:
                list_sf = [{"id_sous_famille": sf.id_sous_famille, "libelle": sf.libelle, "id_famille": f.id_famille} for sf in f.sous_familles]

            resultat.append({
                "id_famille": f.id_famille,       
                "id": f.id_famille,               
                "nom_famille": f.nom_famille,
                "id_unite": f.id_unite,
                "id_utilisateur": f.id_utilisateur,
                "sous_familles": list_sf,         
                "sousFamilles": list_sf           
            })

        return jsonify(resultat), 200

    except Exception as e:
        return jsonify({
            "message": "Erreur lors du chargement des familles",
            "error": str(e)
        }), 500



@familles_bp.route('/api/familles/<int:id>', methods=['GET'])
@jwt_required()
def get_famille(id):
    try:
        claims = get_jwt()
        role_code = claims.get("role_code")
        id_unite = claims.get("id_unite")
        id_unite_int = int(id_unite) if id_unite is not None else None

        famille = Famille.query.get(id)
        if not famille:
            return jsonify({"message": "Famille introuvable"}), 404

       
        if role_code != "ADMIN" and famille.id_unite != id_unite_int:
            return jsonify({"message": "Accès non autorisé à cette famille"}), 403

        list_sf = []
        if hasattr(famille, 'sous_familles') and famille.sous_familles:
            list_sf = [{"id_sous_famille": sf.id_sous_famille, "libelle": sf.libelle, "id_famille": famille.id_famille} for sf in famille.sous_familles]

        return jsonify({
            "id_famille": famille.id_famille,
            "id": famille.id_famille,
            "nom_famille": famille.nom_famille,
            "id_unite": famille.id_unite,
            "id_utilisateur": famille.id_utilisateur,
            "sous_familles": list_sf,
            "sousFamilles": list_sf
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@familles_bp.route('/api/familles', methods=['POST'])
@jwt_required()
def create_famille():
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_unite = claims.get("id_unite") 
        user_unite_int = int(user_unite) if user_unite is not None else None
        
        data = request.get_json()
        if not data or not data.get("nom_famille"):
            return jsonify({"message": "Le nom de la famille est obligatoire"}), 400

        famille = Famille(
            nom_famille=data.get("nom_famille").strip(),
            id_unite=user_unite_int,  
            id_utilisateur=current_user_id  
        )

        db.session.add(famille)
        db.session.flush()  

      
        sous_familles_input = data.get("sous_familles") or data.get("sousFamilles") or []
        for sf in sous_familles_input:
            libelle_val = sf.get("libelle") or sf.get("nom_sous_famille")
            if libelle_val and str(libelle_val).strip():
                sous_famille = SousFamille(
                    libelle=str(libelle_val).strip(),
                    id_famille=famille.id_famille
                )
                db.session.add(sous_famille)

        db.session.commit()
        return jsonify({
            "message": "Famille créée avec succès",
            "id_famille": famille.id_famille
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@familles_bp.route('/api/familles/<int:id>', methods=['PUT'])
@jwt_required()
def update_famille(id):
    try:
        claims = get_jwt()
        role_code = claims.get("role_code")
        id_unite = claims.get("id_unite")
        id_unite_int = int(id_unite) if id_unite is not None else None
        
        famille = Famille.query.get(id)
        if not famille:
            return jsonify({"message": "Famille introuvable"}), 404

       
        if role_code != "ADMIN" and famille.id_unite != id_unite_int:
            return jsonify({"message": "Modification non autorisée"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"message": "Données invalides"}), 400

        if "nom_famille" in data:
            famille.nom_famille = data.get("nom_famille").strip()

        
        if "sous_familles" in data or "sousFamilles" in data:
       
            famille.sous_familles = []
            
            sous_familles_input = data.get("sous_familles") or data.get("sousFamilles") or []
            for sf in sous_familles_input:
                libelle_val = sf.get("libelle") or sf.get("nom_sous_famille")
                if libelle_val and str(libelle_val).strip():
                    new_sf = SousFamille(libelle=str(libelle_val).strip())
                    famille.sous_familles.append(new_sf)

        db.session.commit()
        return jsonify({"message": "Famille modifiée avec succès"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@familles_bp.route('/api/familles/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_famille(id):
    try:
        claims = get_jwt()
        role_code = claims.get("role_code")
        id_unite = claims.get("id_unite")
        id_unite_int = int(id_unite) if id_unite is not None else None
        
        famille = Famille.query.get(id)
        if not famille:
            return jsonify({"message": "Famille introuvable"}), 404

  
        if role_code != "ADMIN" and famille.id_unite != id_unite_int:
            return jsonify({"message": "Suppression non autorisée"}), 403

        db.session.delete(famille)
        db.session.commit()

        return jsonify({"message": "Famille et ses sous-familles supprimées avec succès"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500