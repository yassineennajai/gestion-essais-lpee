import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AlertService } from '../services/alert';

@Component({
  selector: 'app-grandeurs',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './grandeurs.html',
  styleUrls: ['./grandeurs.css']
})
export class GrandeursComponent implements OnInit {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private alertService = inject(AlertService); //,

  grandeurForm!: FormGroup;
  grandeurs: any[] = [];
  isSubmitted = false;
  isEditMode = false;
  currentGrandeurId: number | null = null;
  showModal = false;

  private apiUrl = 'http://127.0.0.1:5000/api/grandeurs';

  ngOnInit(): void {
    this.initForm();
    this.loadGrandeurs();
  }

  initForm(): void {
    this.grandeurForm = this.fb.group({
      code: ['', [Validators.required, Validators.maxLength(10)]],
      libelle: ['', Validators.required]
    });
  }

  get f() { return this.grandeurForm.controls; }

  loadGrandeurs(): void {
    this.http.get<any[]>(this.apiUrl).subscribe({
      next: (data) => this.grandeurs = data || [],
      error: (err) => console.error('Erreur chargement grandeurs:', err)
    });
  }

  openAddModal(): void {
    this.isEditMode = false;
    this.isSubmitted = false;
    this.currentGrandeurId = null;
    this.grandeurForm.reset();
    this.showModal = true;
  }

  openEditModal(grandeur: any): void {
    this.isEditMode = true;
    this.isSubmitted = false;
    this.currentGrandeurId = grandeur.id_grandeur;
    this.grandeurForm.patchValue({
      code: grandeur.code,
      libelle: grandeur.libelle
    });
    this.showModal = true;
  }

  closeModal(): void {
    this.showModal = false;
    this.grandeurForm.reset();
  }

  save(): void {
    this.isSubmitted = true;
    if (this.grandeurForm.invalid) {
      this.alertService.error('Formulaire invalide ! Veuillez remplir correctement tous les champs.');
      return;
    }

    const payload = this.grandeurForm.value;

    if (this.isEditMode && this.currentGrandeurId) {
      this.http.put(`${this.apiUrl}/${this.currentGrandeurId}`, payload).subscribe({
        next: () => {

          this.alertService.success('Modification réussie ! La grandeur a été modifiée avec succès.');
          this.loadGrandeurs();
          this.closeModal();
        },
        error: (err) => {
          console.error(err);
          this.alertService.error('Échec de la modification ! Une erreur est survenue.');
        }
      });
    } else {
      this.http.post(this.apiUrl, payload).subscribe({
        next: () => {

          this.alertService.success('Enregistrement réussi ! La grandeur a été ajoutée avec succès.');
          this.loadGrandeurs();
          this.closeModal();
        },
        error: (err) => {
          console.error(err);
          this.alertService.error('Échec de l\'enregistrement ! Une erreur est survenue.');
        }
      });
    }
  }

  deleteGrandeur(id: number): void {

    this.alertService.confirm(
      'Voulez-vous vraiment supprimer cette grandeur ?',
      'Cette action supprimera définitivement cette grandeur de la base de données.',
      'Oui, supprimer',
      'Annuler'
    ).then((confirme) => {
      if (confirme) {
        this.http.delete(`${this.apiUrl}/${id}`).subscribe({
          next: () => {
           
            this.alertService.success('Grandeur supprimée ! La grandeur a bien été retirée.');
            this.loadGrandeurs();
          },
          error: (err) => {
            console.error(err);
            this.alertService.error('Échec de la suppression ! Une erreur est survenue.');
          }
        });
      }
    });
  }
}
