from extensions import db
from datetime import datetime, timezone


class Role(db.Model):
    __tablename__ = 'role'

    id_role = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100))
    libelle = db.Column(db.String(255))

    def to_dict(self):
        return {"id_role": self.id_role, "code": self.code, "libelle": self.libelle}



class Ville(db.Model):
    __tablename__ = 'ville'

    id_ville = db.Column(db.Integer, primary_key=True)
    nom_ville = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {"id_ville": self.id_ville, "nom_ville": self.nom_ville}



class Unite(db.Model):
    __tablename__ = 'unite'

    id_unite = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(255))
    contact = db.Column(db.String(255))
    type = db.Column(db.String(255))
    id_ville = db.Column(db.Integer, db.ForeignKey('ville.id_ville', ondelete='SET NULL'), nullable=True)

    ville = db.relationship('Ville', backref='unites')

    def to_dict(self):
        return {
            "id_unite": self.id_unite,
            "libelle": self.libelle,
            "contact": self.contact,
            "type": self.type,
            "id_ville": self.id_ville,
            "ville": self.ville.to_dict() if self.ville else None
        }



class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'

    id_utilisateur = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    mot_de_passe = db.Column(db.String(255))
    statut = db.Column(db.String(100), default='Actif')
    cree = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    modifier = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    id_unite = db.Column(db.Integer, db.ForeignKey('unite.id_unite', ondelete='SET NULL'), nullable=True)
    id_role = db.Column(db.Integer, db.ForeignKey('role.id_role', ondelete='RESTRICT'), nullable=False)

    unite = db.relationship('Unite', backref='utilisateurs')
    role = db.relationship('Role', backref='utilisateurs')

    def to_dict(self):
        return {
            "id_utilisateur": self.id_utilisateur,
            "email": self.email,
            "statut": self.statut,
            "id_unite": self.id_unite,
            "id_role": self.id_role,
            "unite": self.unite.libelle if self.unite else None,
            "role": self.role.libelle if self.role else None
        }



class DomaineActivite(db.Model):
    __tablename__ = 'domaine_activite'

    id_domaine = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(255))

    def to_dict(self):
        return {"id_domaine": self.id_domaine, "libelle": self.libelle}


class Famille(db.Model):
    __tablename__ = 'famille'

    id_famille = db.Column(db.Integer, primary_key=True)
    nom_famille = db.Column(db.String(255))
    id_unite = db.Column(db.Integer, db.ForeignKey('unite.id_unite', ondelete='SET NULL'), nullable=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey('utilisateur.id_utilisateur', ondelete='CASCADE'), nullable=False)

    unite = db.relationship('Unite', backref='familles')
    utilisateur = db.relationship('Utilisateur', backref='familles')
    sous_familles = db.relationship('SousFamille', backref='famille', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id_famille": self.id_famille,
            "nom_famille": self.nom_famille,
            "id_unite": self.id_unite,
            "id_utilisateur": self.id_utilisateur,
            "sousFamilles": [
                {
                    "id_sous_famille": sf.id_sous_famille,
                    "libelle": sf.libelle
                } for sf in self.sous_familles
            ]
        }



class SousFamille(db.Model):
    __tablename__ = 'sous_famille'

    id_sous_famille = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(255))
    id_famille = db.Column(db.Integer, db.ForeignKey('famille.id_famille', ondelete='CASCADE'), nullable=False)

    def to_dict(self):
        return {"id_sous_famille": self.id_sous_famille, "libelle": self.libelle, "id_famille": self.id_famille}



class Essai(db.Model):
    __tablename__ = 'essai'

    id_essai = db.Column(db.Integer, primary_key=True)
    intitule = db.Column(db.String(255))
    type = db.Column(db.String(100))

    id_domaine = db.Column(db.Integer, db.ForeignKey('domaine_activite.id_domaine', ondelete='SET NULL'), nullable=True)
    id_famille = db.Column(db.Integer, db.ForeignKey('famille.id_famille', ondelete='SET NULL'), nullable=True)
    id_sous_famille = db.Column(db.Integer, db.ForeignKey('sous_famille.id_sous_famille', ondelete='SET NULL'), nullable=True)
    

    id_partie = db.Column(db.Integer, db.ForeignKey('partie.id_partie', ondelete='SET NULL'), nullable=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey('utilisateur.id_utilisateur', ondelete='CASCADE'), nullable=False)
    cree = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    domaine = db.relationship('DomaineActivite', backref='essais_associes')
    famille = db.relationship('Famille', backref='essais_associes')
    sous_famille = db.relationship('SousFamille', backref='essais_associes')
    partie = db.relationship('Partie', backref='essais_associes')
    utilisateur = db.relationship('Utilisateur', backref='essais_associes')

    normes = db.relationship('Norme', secondary='essai_norme', backref='essais')
    unites = db.relationship('Unite', secondary='essai_unite', backref='essais')
    grandeurs = db.relationship('GrandeurMesure', secondary='essai_grandeur', backref='essais')

    def to_dict(self):
        return {
            "id_essai": self.id_essai,
            "intitule": self.intitule,
            "type": self.type,
            "id_domaine": self.id_domaine,
            "id_famille": self.id_famille,
            "id_sous_famille": self.id_sous_famille,
            "id_partie": self.id_partie,
            "id_utilisateur": self.id_utilisateur,
            "cree": self.cree.isoformat() if self.cree else None,
            "domaine_libelle": self.domaine.libelle if self.domaine else None,
            "famille_nom": self.famille.nom_famille if self.famille else None,
            "sous_famille_libelle": self.sous_famille.libelle if self.sous_famille else None,
            "normes": [{"id_norme": n.id_norme, "libelle": n.libelle} for n in self.normes],
            "grandeurs": [{"id_grandeur": g.id_grandeur, "code": g.code, "libelle": g.libelle} for g in self.grandeurs],
            "unites": [{"id_unite": u.id_unite, "libelle": u.libelle} for u in self.unites]
        }



class Norme(db.Model):
    __tablename__ = 'norme'

    id_norme = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(255))
    id_utilisateur = db.Column(db.Integer, db.ForeignKey('utilisateur.id_utilisateur', ondelete='CASCADE'), nullable=False)
    id_unite = db.Column(db.Integer, db.ForeignKey('unite.id_unite', ondelete='SET NULL'), nullable=True)

    utilisateur = db.relationship('Utilisateur', backref='normes')
    unite = db.relationship('Unite', backref='normes_associees')
    
 
    parties = db.relationship('Partie', backref='norme', cascade='all, delete-orphan', lazy='joined')

    def to_dict(self):
        return {
            "id_norme": self.id_norme,
            "libelle": self.libelle,
            "id_utilisateur": self.id_utilisateur,
            "id_unite": self.id_unite,
            "parties": [
                {
                    "id_partie": p.id_partie,
                    "no_partie": p.no_partie,
                    "titre": p.titre
                } for p in self.parties
            ]
        }



class Partie(db.Model):
    __tablename__ = 'partie'

    id_partie = db.Column(db.Integer, primary_key=True)
    no_partie = db.Column(db.String(100))
    titre = db.Column(db.String(255))
    
    # 🌟 إضافة ondelete='CASCADE' لحذف الأجزاء تلقائياً بمجرد حذف المعيار أو تعديله
    id_norme = db.Column(db.Integer, db.ForeignKey('norme.id_norme', ondelete='CASCADE'), nullable=False)

    def to_dict(self):
        return {"id_partie": self.id_partie, "no_partie": self.no_partie, "titre": self.titre, "id_norme": self.id_norme}



class GrandeurMesure(db.Model):
    __tablename__ = 'grandeur_mesure'

    id_grandeur = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100))
    libelle = db.Column(db.String(255))
    id_unite = db.Column(db.Integer, db.ForeignKey('unite.id_unite', ondelete='SET NULL'), nullable=True)

    unite = db.relationship('Unite', backref='grandeurs_associees')

    def to_dict(self):
        return {
            "id_grandeur": self.id_grandeur, 
            "code": self.code, 
            "libelle": self.libelle,
            "id_unite": self.id_unite
        }



class EssaiNorme(db.Model):
    __tablename__ = 'essai_norme'
    id_essai = db.Column(db.Integer, db.ForeignKey('essai.id_essai', ondelete='CASCADE'), primary_key=True)
    id_norme = db.Column(db.Integer, db.ForeignKey('norme.id_norme', ondelete='CASCADE'), primary_key=True)


class EssaiGrandeur(db.Model):
    __tablename__ = 'essai_grandeur'
    id_essai = db.Column(db.Integer, db.ForeignKey('essai.id_essai', ondelete='CASCADE'), primary_key=True)
    id_grandeur = db.Column(db.Integer, db.ForeignKey('grandeur_mesure.id_grandeur', ondelete='CASCADE'), primary_key=True)


class EssaiUnite(db.Model):
    __tablename__ = 'essai_unite'
    id_essai = db.Column(db.Integer, db.ForeignKey('essai.id_essai', ondelete='CASCADE'), primary_key=True)
    id_unite = db.Column(db.Integer, db.ForeignKey('unite.id_unite', ondelete='CASCADE'), primary_key=True)