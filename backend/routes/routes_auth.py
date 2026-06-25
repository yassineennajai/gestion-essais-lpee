from flask import Blueprint, request, jsonify
from models import Utilisateur, Essai, Norme, Unite
from extensions import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timezone
from sqlalchemy import func

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'email' not in data or 'mot_de_passe' not in data:
        return jsonify({'message': 'Données invalides'}), 400

    uti = Utilisateur.query.filter_by(email=data['email']).first()
    if not uti or uti.mot_de_passe != data['mot_de_passe']:
        return jsonify({'message': 'Email ou mot de passe incorrect'}), 401

    role_libelle = uti.role.libelle if uti.role else "Utilisateur"
    role_code = uti.role.code if uti.role else "USER" 
    
    token = create_access_token(
        identity=str(uti.id_utilisateur),
        additional_claims={
            "email": uti.email,
            "role": role_libelle,
            "role_code": role_code, 
            "id_unite": uti.id_unite
        }
    )

    return jsonify({
        'token': token,
        'role': role_libelle,                
        'id_unite': uti.id_unite,          
        'nom_unite': uti.unite.libelle if uti.unite else None,
        'message': 'Connexion réussie'
    }), 200


@auth_bp.route('/api/dashboard', methods=['GET'])
@jwt_required() 
def dashboard():
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        role_code = claims.get("role_code")
        id_unite_user = claims.get("id_unite")

        today = datetime.today()

     
        total_essais = db.session.query(Essai).filter_by(id_utilisateur=current_user_id).count()
        essais_aujourdhui = db.session.query(Essai).filter(
         
            Essai.id_utilisateur == current_user_id,
            func.date(Essai.cree) == today.date()
        ).count()
        
        if role_code == "ADMIN":
         
            total_normes = db.session.query(Norme).count()
        else:
      
            total_normes = db.session.query(Norme).filter_by(id_unite=id_unite_user).count() if id_unite_user else 0
        
        total_utilisateurs = db.session.query(Utilisateur).count()
        total_unites = db.session.query(Unite).count()

        return jsonify({
            "essais": total_essais,
            "essais_aujourdhui": essais_aujourdhui,
            "normes": total_normes,
            "utilisateurs": total_utilisateurs,
            "unites": total_unites
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500