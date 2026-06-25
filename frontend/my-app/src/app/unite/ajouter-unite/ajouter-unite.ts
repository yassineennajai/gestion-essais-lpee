import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { AlertService } from '../../services/alert';

@Component({
  selector: 'app-ajouter-unite',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './ajouter-unite.html',
  styleUrls: ['./ajouter-unite.css']
})
export class AjouterUniteComponent implements OnInit {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private alertService = inject(AlertService);

  uniteForm!: FormGroup;
  isSubmitted = false;
  isEditMode = false;
  currentUniteId: number | null = null;
  villes: any[] = [];

  private apiUrl = 'http://127.0.0.1:5000/api/unites';

  ngOnInit(): void {
    this.initForm();
    this.loadVilles();
    this.checkEditMode();
  }

  initForm(): void {
    this.uniteForm = this.fb.group({
      libelle: ['', Validators.required],
      id_ville: [null, Validators.required],
      contact: [''],
      type: ['', Validators.required]
    });
  }

  get f() { return this.uniteForm.controls; }

  compareVilles(v1: any, v2: any): boolean {
    if (v1 === undefined || v2 === undefined) return false;
    const id1 = v1 && typeof v1 === 'object' ? (v1.id_ville || v1.id) : v1;
    const id2 = v2 && typeof v2 === 'object' ? (v2.id_ville || v2.id) : v2;
    return id1 === id2;
  }

  loadVilles(): void {
    this.http.get<any[]>('http://127.0.0.1:5000/api/villes').subscribe({
      next: (data) => {
        this.villes = data || [];
      },
      error: (err) => {
        console.error('Erreur chargement villes:', err);
      }
    });
  }

  checkEditMode(): void {
    const stateData = window.history.state?.['data'];

    if (stateData) {
      this.isEditMode = true;
      this.currentUniteId = stateData.id_unite;

      this.uniteForm.patchValue({
        libelle: stateData.libelle,
        id_ville: stateData.id_ville ?? stateData.la_ville?.id_ville,
        contact: stateData.contact,
        type: stateData.type
      });
    }
  }

  save(): void {
    this.isSubmitted = true;

    if (this.uniteForm.invalid) {
      this.uniteForm.markAllAsTouched();
      this.alertService.error('Formulaire invalide ! Veuillez remplir tous les champs obligatoires.');
      return;
    }

    const payload = this.uniteForm.value;

    if (this.isEditMode && this.currentUniteId) {
      this.http.put(`${this.apiUrl}/${this.currentUniteId}`, payload).subscribe({
        next: () => {
          this.alertService.success('Modification réussie ! L\'unité a été modifiée avec succès.');

          setTimeout(() => {
            this.router.navigate(['/dashboard-admin/unite']);
          }, 1000);
        },
        error: (err) => {
          console.error('Erreur de modification d\'unité :', err);
          this.alertService.error('Échec de la modification ! Une erreur est survenue lors de la sauvegarde.');
        }
      });
    } else {
      this.http.post(this.apiUrl, payload).subscribe({
        next: () => {
          this.alertService.success('Enregistrement réussi ! L\'unité a été créée avec succès.');

          setTimeout(() => {
            this.router.navigate(['/dashboard-admin/unite']);
          }, 1000);
        },
        error: (err) => {
          console.error('Erreur de création d\'unité :', err);
          this.alertService.error('Échec de l\'enregistrement ! Une erreur est survenue lors de l\'envoi.');
        }
      });
    }
  }

  cancel(): void {
    this.router.navigate(['/dashboard-admin/unite']);
  }
}


