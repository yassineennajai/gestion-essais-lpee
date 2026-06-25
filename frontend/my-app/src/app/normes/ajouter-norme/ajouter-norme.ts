import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, FormArray, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { NormeService } from '../../services/norme';
import { AlertService } from '../../services/alert';

@Component({
  selector: 'app-ajouter-norme',
  templateUrl: './ajouter-norme.html',
  styleUrls: ['./ajouter-norme.css'],
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule]
})
export class AjouterNormeComponent implements OnInit {
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private normeService = inject(NormeService);
  private alertService = inject(AlertService);

  normeForm!: FormGroup;
  isSubmitted: boolean = false;

  ngOnInit(): void {
    this.initForm();
  }

  initForm(): void {
    this.normeForm = this.fb.group({
      libelle: ['', Validators.required],
      parties: this.fb.array([])
    });

    this.ajouterPartie();
  }

  get parties(): FormArray {
    return this.normeForm.get('parties') as FormArray;
  }

  createPartieFormGroup(): FormGroup {
    return this.fb.group({
      no_partie: ['', Validators.required],
      titre: ['', Validators.required]
    });
  }

  ajouterPartie(): void {
    this.parties.push(this.createPartieFormGroup());
  }

  supprimerPartie(index: number): void {
    if (this.parties.length > 1) {
      this.parties.removeAt(index);
    } else {

      this.alertService.error("Il faut avoir au moins une partie pour cette norme !");
    }
  }

  save(): void {
    this.isSubmitted = true;
    if (this.normeForm.invalid) {

      this.alertService.error("Formulaire invalide ! Veuillez remplir tous les champs obligatoires.");
      return;
    }

    const payload = this.normeForm.value;
    console.log('Payload envoyé à l\'API :', payload);

    this.normeService.createNorme(payload).subscribe({
      next: (response) => {

        this.alertService.success('Norme ajoutée avec succès !');
        this.router.navigate(['/dashboard-admin/normes']);
      },
      error: (err: any) => {
        console.error('Erreur lors de la création de la norme:', err);
      
        this.alertService.error('Une erreur est survenue lors de l\'enregistrement de la norme.');
      }
    });
  }

  cancel(): void {
    this.router.navigate(['/dashboard-admin/normes']);
  }
}
