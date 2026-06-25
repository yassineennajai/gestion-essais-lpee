import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { EssaiService } from '../../services/essais';
import { AlertService } from '../../services/alert';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Component({
  selector: 'app-ajouter-essai',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './ajouter-essai.html',
  styleUrls: ['./ajouter-essai.css']
})
export class AjouterEssaiComponent implements OnInit {
  private fb = inject(FormBuilder);
  private essaiService = inject(EssaiService);
  private router = inject(Router);
  private alertService = inject(AlertService);

  essaiForm!: FormGroup;
  isSubmitted = false;
  isEditMode = false;
  currentEssaiId: number | null = null;
  private pendingNavigationState: any = null;
  private originalEssaiData: any = null;

  isAdmin = false;
  isLNM = false;
  isCEREP = false;
  userUniteId: number | null = null;
  backupUniteIdForAdmin: number | null = null;

  domaines: any[] = [];
  allFamilles: any[] = [];
  normes: any[] = [];
  grandeurs: any[] = [];

  filteredFamilles: any[] = [];
  filteredSousFamilles: any[] = [];
  partiesFiltrees: any[] = [];

  ngOnInit(): void {
    this.checkUserRole();
    this.initForm();
    this.getNavigationStateEarly();
    this.loadInitialData();
  }

  private checkUserRole(): void {
    const currentUserString = localStorage.getItem('user') || localStorage.getItem('currentUser');
    if (currentUserString) {
      try {
        const user = JSON.parse(currentUserString);
        const roleStr = String(user.role || user.role_code || '').toUpperCase();

        this.isAdmin = (roleStr === 'ADMIN' || roleStr === 'ADMINISTRATEUR');
        this.userUniteId = user.id_unite ? Number(user.id_unite) : null;

        const nomUnite = String(user.nom_unite || user.unite || user.code_unite || '').toUpperCase();
        if (nomUnite.includes('LNM') || nomUnite.includes('MECANIQUE')) {
          this.isLNM = true;
        }

        // Vérification si l'unité de l'utilisateur connecté est CEREP
        if (nomUnite.includes('CEREP')) {
          this.isCEREP = true;
        } else {
          this.isCEREP = false;
        }
      } catch (e) {
        console.error("Erreur lors de la lecture des données utilisateur :", e);
      }
    }
  }

  initForm(): void {
    this.essaiForm = this.fb.group({
      intitule: ['', Validators.required],
      type: ['', Validators.required],
      idFamille: [null, Validators.required],
      idSousFamille: [null], // Rendu optionnel au départ car contrôlé dynamiquement
      idNorme: [null, Validators.required],
      idPartie: [[], Validators.required],
      grandeurs: [[]] // Validation dynamique activée pour CEREP
    });

    if (this.isAdmin || this.isLNM) {
      this.essaiForm.addControl('idDomaine', this.fb.control(null, Validators.required));
    }

    if (this.isAdmin) {
      this.essaiForm.disable();
    }

    // Initialisation de la validation des grandeurs selon l'unité
    this.updateGrandeursValidation(this.isCEREP);

    this.essaiForm.get('idFamille')?.valueChanges.subscribe(idFamille => {
      this.filterSousFamillesByFamille(idFamille);
    });
    this.essaiForm.get('idNorme')?.valueChanges.subscribe(idNorme => {
      this.filterPartiesByNorme(idNorme);
    });
  }

  get f() { return this.essaiForm.controls; }

  private getNavigationStateEarly(): void {
    const navigation = this.router.getCurrentNavigation();
    this.pendingNavigationState = navigation?.extras?.state?.['data'] || window.history.state?.['data'];
  }

  loadInitialData(): void {
    forkJoin({
      domaines: this.essaiService.getDomaines().pipe(catchError(() => of([]))),
      familles: this.essaiService.getFamilles().pipe(catchError(() => of([]))),
      normes: this.essaiService.getNormes().pipe(catchError(() => of([]))),
      grandeurs: this.essaiService.getGrandeurs().pipe(catchError(() => of([])))
    }).subscribe({
      next: (res: any) => {
        this.domaines = res.domaines || [];

        this.allFamilles = (res.familles || []).map((f: any) => ({
          id_famille: Number(f.id_famille ?? f.id),
          nom_famille: f.nom_famille ?? f.nom ?? f.libelle,
          rawSousFamilles: f.sousFamilles ?? f.sous_familles ?? f.sous_Familles ?? []
        }));

        this.filteredFamilles = this.allFamilles;

        this.normes = (res.normes || []).map((n: any) => ({
          id_norme: Number(n.id_norme || n.id),
          libelle: n.libelle || n.nom_norme,
          parties: n.parties || []
        }));

        this.grandeurs = (res.grandeurs || []).map((g: any) => ({
          id_grandeur: Number(g.id_grandeur || g.id),
          code: g.code || g.symbole || '',
          libelle: g.libelle || g.nom || ''
        }));

        if (this.pendingNavigationState) {
          this.openMode(this.pendingNavigationState);
          this.pendingNavigationState = null;
        } else {

          this.isEditMode = false;
          this.currentEssaiId = null;
          this.checkUserRole();
          this.updateGrandeursValidation(this.isCEREP);
        }
      },
      error: (err) => console.error("Erreur lors du chargement des données initiales :", err)
    });
  }

  private filterSousFamillesByFamille(idFamille: any): void {
    if (!idFamille) {
      this.filteredSousFamilles = [];
      this.updateSousFamilleValidation(false);
      return;
    }

    const selectedFam = this.allFamilles.find(f => f.id_famille === Number(idFamille));


    if (selectedFam && selectedFam.rawSousFamilles && selectedFam.rawSousFamilles.length > 0) {
      this.filteredSousFamilles = selectedFam.rawSousFamilles.map((sf: any) => ({
        id_sous_famille: Number(sf.id_sous_famille || sf.id),
        libelle: sf.libelle || sf.nom_sous_famille || ''
      }));
      this.updateSousFamilleValidation(true);
    } else {
      this.filteredSousFamilles = [];
      this.updateSousFamilleValidation(false);
    }
  }


  private updateSousFamilleValidation(required: boolean): void {
    const control = this.essaiForm?.get('idSousFamille');
    if (control) {
      if (required) {
        control.setValidators([Validators.required]);
      } else {
        control.clearValidators();
        control.setValue(null);
      }
      control.updateValueAndValidity();
    }
  }

  
  private updateGrandeursValidation(required: boolean): void {
    const control = this.essaiForm?.get('grandeurs');
    if (control) {
      if (required) {
        control.setValidators([Validators.required]);
      } else {
        control.clearValidators();
        control.setValue([]);
      }
      control.updateValueAndValidity();
    }
  }

  private filterPartiesByNorme(idNorme: any): void {
    if (!idNorme) {
      this.partiesFiltrees = [];
      return;
    }
    const selectedNorme = this.normes.find(n => n.id_norme === Number(idNorme));
    this.partiesFiltrees = selectedNorme ? selectedNorme.parties : [];
  }

  openMode(essai: any): void {
    if (!this.isAdmin) {
      this.isEditMode = true;
    }
    this.isSubmitted = false;
    this.originalEssaiData = { ...essai };
    this.currentEssaiId = essai.id_essai || essai.id;

    const origUniteId = essai.id_unite ?? essai.idUnite ?? essai.unite_id ?? (essai.unite ? essai.unite.id : null);
    this.backupUniteIdForAdmin = origUniteId ? Number(origUniteId) : null;

    const idFamille = essai.id_famille ?? essai.idFamille ?? (essai.famille ? essai.famille.id : null);
    const idSousFamille = essai.id_sous_famille ?? essai.idSousFamille ?? (essai.sous_famille ? essai.sous_famille.id : null);
    const idNorme = essai.id_norme ?? essai.idNorme ?? (essai.norme ? essai.norme.id : null);
    const idDomaine = essai.id_domaine ?? essai.idDomaine ?? (essai.domaine ? essai.domaine.id : null);

    if (idFamille) this.filterSousFamillesByFamille(idFamille);
    if (idNorme) this.filterPartiesByNorme(idNorme);


    const nomUniteEssai = String(essai.nom_unite || (essai.unite ? essai.unite.libelle || essai.unite.nom_unite : '') || '').toUpperCase();
    if (nomUniteEssai.includes('CEREP')) {
      this.isCEREP = true;
      this.updateGrandeursValidation(true);
    } else {

      this.isCEREP = false;
      this.updateGrandeursValidation(false);
    }

    let selectedPartiesIds: number[] = [];
    if (essai.id_partie) {
      if (Array.isArray(essai.id_partie)) {
        selectedPartiesIds = essai.id_partie.map((p: any) => typeof p === 'object' ? Number(p.id_partie || p.id) : Number(p));
      } else if (typeof essai.id_partie === 'string') {
        selectedPartiesIds = essai.id_partie.split(',').filter((p: string) => p.trim()).map((p: string) => Number(p));
      } else {
        selectedPartiesIds = [Number(essai.id_partie)];
      }
    } else if (essai.idPartie) {
      selectedPartiesIds = Array.isArray(essai.idPartie) ? essai.idPartie.map((p: any) => Number(p)) : [Number(essai.idPartie)];
    }

    let selectedGrandeursIds: number[] = [];
    if (essai.grandeurs && essai.grandeurs.length > 0) {
      selectedGrandeursIds = essai.grandeurs.map((g: any) => typeof g === 'object' ? Number(g.id_grandeur || g.id) : Number(g));
    } else if (essai.id_grandeur || (essai.grandeur && essai.grandeur.id)) {
      selectedGrandeursIds = [Number(essai.id_grandeur || essai.grandeur.id)];
    }

    this.essaiForm.patchValue({
      intitule: essai.intitule,
      type: essai.type,
      idFamille: idFamille ? Number(idFamille) : null,
      idSousFamille: idSousFamille ? Number(idSousFamille) : null,
      idNorme: idNorme ? Number(idNorme) : null,
      idPartie: selectedPartiesIds,
      grandeurs: selectedGrandeursIds
    }, { emitEvent: false });

    if (this.essaiForm.get('idDomaine') && idDomaine) {
      this.essaiForm.get('idDomaine')?.patchValue(Number(idDomaine), { emitEvent: false });
    }
  }

  cancel(): void {
    this.essaiForm.reset({ type: '', grandeurs: [], idPartie: [] });
    this.isSubmitted = false;
    this.isEditMode = false;
    this.currentEssaiId = null;
    this.backupUniteIdForAdmin = null;
    this.originalEssaiData = null;


    this.checkUserRole();
    this.updateGrandeursValidation(this.isCEREP);

    this.router.navigate(['/dashboard-admin/essais']);
  }

  save(): void {
    if (this.isAdmin) return;

    this.isSubmitted = true;
    if (this.essaiForm.invalid) {
      this.essaiForm.markAllAsTouched();
      this.alertService.error('Formulaire incomplet ! Veuillez remplir tous les champs obligatoires.');
      return;
    }

    const formValue = this.essaiForm.getRawValue();
    const finalUniteId = this.isEditMode ? (this.backupUniteIdForAdmin || this.userUniteId) : this.userUniteId;

    const selectedGrandeursRaw = formValue.grandeurs || [];
    const finalGrandeursArray = selectedGrandeursRaw.map((id: any) => Number(id));

    const selectedPartiesRaw = formValue.idPartie || [];
    const finalPartiesArray = selectedPartiesRaw.map((id: any) => Number(id));

    let finalDomaineId = null;
    if (this.isAdmin || this.isLNM) {
      finalDomaineId = formValue.idDomaine ? Number(formValue.idDomaine) : null;
    } else if (this.isEditMode) {
      const origDomId = this.originalEssaiData?.id_domaine ?? this.originalEssaiData?.idDomaine ?? (this.originalEssaiData?.domaine ? this.originalEssaiData.domaine.id : null);
      finalDomaineId = origDomId ? Number(origDomId) : null;
    }

    const bodyPayload = {
      intitule: formValue.intitule,
      type: formValue.type,
      id_domaine: finalDomaineId,
      id_famille: formValue.idFamille ? Number(formValue.idFamille) : null,
      id_sous_famille: formValue.idSousFamille ? Number(formValue.idSousFamille) : null,
      id_norme: formValue.idNorme ? Number(formValue.idNorme) : null,
      id_partie: finalPartiesArray.length > 0 ? finalPartiesArray : null,
      id_unite: finalUniteId ? Number(finalUniteId) : null,
      id_grandeur: finalGrandeursArray.length > 0 ? finalGrandeursArray[0] : null,
      grandeurs: finalGrandeursArray
    };

    if (this.isEditMode && this.currentEssaiId) {
      this.essaiService.updateEssai(this.currentEssaiId, bodyPayload).subscribe({
        next: () => {
          this.alertService.success('Modification réussie ! L\'essai a été modifié avec succès.');
          this.cancel();
        },
        error: (err) => {
          console.error("Erreur de modification détaillée :", err);
          this.alertService.error('Échec de la modification ! Impossible d\'enregistrer les modifications.');
        }
      });
    } else {
      this.essaiService.createEssai(bodyPayload).subscribe({
        next: () => {
          this.alertService.success('Enregistrement réussi ! L\'essai a été enregistré avec succès.');
          this.cancel();
        },
        error: (err) => {
          console.error("Erreur de création :", err);
          this.alertService.error('Échec de l\'enregistrement ! Une erreur est survenue.');
        }
      });
    }
  }
}
