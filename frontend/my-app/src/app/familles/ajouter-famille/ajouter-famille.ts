import { Component, OnInit, inject } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormArray,
  Validators,
  ReactiveFormsModule
} from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import { FamilleService } from '../../services/famille';
import { AlertService } from '../../services/alert';

@Component({
  selector: 'app-ajouter-famille',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './ajouter-famille.html',
  styleUrls: ['./ajouter-famille.css']
})
export class AjouterFamilleComponent implements OnInit {

  private fb = inject(FormBuilder);
  private router = inject(Router);
  private familleService = inject(FamilleService);
  private alertService = inject(AlertService);

  familleForm!: FormGroup;
  isSubmitted = false;

  ngOnInit(): void {
    this.initForm();
  }

  initForm(): void {
    this.familleForm = this.fb.group({
      nom_famille: ['', Validators.required],
      sousFamilles: this.fb.array([])
    });

    // ❌ Ne pas ajouter automatiquement une sous-famille
  }

  get sousFamilles(): FormArray {
    return this.familleForm.get('sousFamilles') as FormArray;
  }

  createSousFamilleGroup(): FormGroup {
    return this.fb.group({
      libelle: ['']
    });
  }

  ajouterSousFamille(): void {
    this.sousFamilles.push(this.createSousFamilleGroup());
  }

  supprimerSousFamille(index: number): void {
    this.sousFamilles.removeAt(index);
  }

  save(): void {
    this.isSubmitted = true;

    if (this.familleForm.invalid) {
      this.familleForm.markAllAsTouched();

      this.alertService.error(
        'Veuillez saisir le nom de la famille.'
      );
      return;
    }

    const formValues = this.familleForm.value;

    const sousFamillesFiltrees = formValues.sousFamilles.filter(
      (sf: any) => sf.libelle && sf.libelle.trim() !== ''
    );

    const payload = {
      nom_famille: formValues.nom_famille,
      sous_familles: sousFamillesFiltrees
    };

    console.log('Payload envoyé :', payload);

    this.familleService.createFamille(payload).subscribe({
      next: (response) => {
        console.log('Succès :', response);

        this.alertService.success(
          'Famille ajoutée avec succès !'
        );

        this.isSubmitted = false;
        this.familleForm.reset();

        while (this.sousFamilles.length) {
          this.sousFamilles.removeAt(0);
        }

        this.router.navigate(['/dashboard-admin/familles']);
      },

      error: (error) => {
        console.error('Erreur :', error);

        this.alertService.error(
          'Erreur lors de l’ajout de la famille.'
        );
      }
    });
  }

  cancel(): void {
    this.router.navigate(['/dashboard-admin/familles']);
  }
}
