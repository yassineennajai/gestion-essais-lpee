% -----------------------------
% Faits de base
% -----------------------------

% Etudiants
etudiant(fatima).
etudiant(youssef).
etudiant(karim).

% Enseignants
enseignant(ahmed).
enseignant(leila).

% Cours
cours(math101).
cours(ai202).

% Départements
departement(mathematiques).
departement(informatique).

% Examens
examen(exam_math101).
examen(exam_ai202).

% -----------------------------
% Relations
% -----------------------------

% Relations étudiant - cours
suit(fatima, math101).
suit(youssef, ai202).

% Relations enseignant - cours
enseigne(ahmed, math101).
enseigne(leila, ai202).

% Appartenance cours - département
appartient(math101, mathematiques).
appartient(ai202, informatique).

% Relations étudiant - examen
passe(fatima, exam_math101).
passe(karim, exam_math101).
passe(karim, exam_ai202).

% Examens associés aux cours
concerne(exam_math101, math101).

% -----------------------------
% Règles
% -----------------------------

% Un étudiant est un apprenant actif s'il suit un cours
apprenant_actif(X) :- etudiant(X), suit(X, _).

% Un enseignant est un intervenant s'il enseigne un cours
intervenant(X) :- enseignant(X), enseigne(X, _).

% Un étudiant est évalué s'il passe un examen
evalue(X) :- etudiant(X), passe(X, _).

% Un cours est disciplinaire s'il appartient à un département
disciplinaire(X) :- cours(X), appartient(X, _).

% -----------------------------
% Projets
% -----------------------------

projet(projetAI).
projet(projetWeb).

realise(fatima, projetAI).
realise(youssef, projetWeb).

% Attributs
age(fatima, 21).
age(youssef, 22).
age(karim, 23).
age(ahmed, 20).

niveau(fatima, licence).
niveau(youssef, master).
niveau(karim, master).

nom_cours(math101, 'Mathematiques Generales').
nom_cours(ai202, 'Intelligence Artificielle').

% Diplôme : un étudiant passe les deux examens
diplome(X) :-
    etudiant(X),
    passe(X, exam_math101),
    passe(X, exam_ai202).

% Enseignant expérimenté : +40 ans
experimente(X) :-
    enseignant(X),
    age(X, Age),
    Age > 40.

% Projet technique : réalisé par un étudiant de niveau master
projet_technique(P) :-
    realise(Etu, P),
    niveau(Etu, master).

% Notes
note(fatima, exam_math101, 15).
note(karim, exam_ai202, 7).
