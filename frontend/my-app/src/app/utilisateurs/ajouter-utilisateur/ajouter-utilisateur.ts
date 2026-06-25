import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { UtilisateurService } from '../../services/utilisateur';
import { AlertService } from '../../services/alert';

@Component({
  selector: 'app-ajouter-utilisateur',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './ajouter-utilisateur.html',
  styleUrl: './ajouter-utilisateur.css'
})
export class AjouterUtilisateur implements OnInit {
  private fb = inject(FormBuilder);
  private utilisateurService = inject(UtilisateurService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private alertService = inject(AlertService);

  userForm!: FormGroup;
  isEditMode: boolean = false;
  isSubmitted: boolean = false;
  uniteList: any[] = [];
  userId: number | null = null;

  ngOnInit(): void {
    this.userForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      mot_de_passe: ['', [Validators.required, Validators.minLength(6)]],
      id_role: [2, Validators.required],
      id_unite: [null, Validators.required]
    });

    this.utilisateurService.getUnites().subscribe({
      next: (data: any[]) => {
        this.uniteList = data || [];
      },
      error: (err: any) => console.error(err)
    });

    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.userId = +idParam;
      this.isEditMode = true;

      this.userForm.get('mot_de_passe')?.clearValidators();
      this.userForm.get('mot_de_passe')?.updateValueAndValidity();

      this.utilisateurService.getUtilisateurs().subscribe({
        next: (res: any) => {
          const users = Array.isArray(res) ? res : res.utilisateurs || [];
          const userToEdit = users.find((u: any) => (u.id_utilisateur === this.userId) || (u.id === this.userId));

          if (userToEdit) {
            this.userForm.patchValue({
              email: userToEdit.email,
              id_role: userToEdit.id_role,
              id_unite: userToEdit.id_unite
            });
          }
        },
        error: (err: any) => console.error(err)
      });
    }
  }

  get f() {
    return this.userForm.controls;
  }

  save(): void {
    this.isSubmitted = true;

    if (this.userForm.invalid) {
      this.alertService.error('Formulaire invalide ! Veuillez remplir correctement tous les champs obligatoires.');
      return;
    }

    const userData = this.userForm.value;

    if (this.isEditMode && this.userId) {
      this.utilisateurService.updateUtilisateur(this.userId, userData).subscribe({
        next: (res: any) => {
          this.alertService.success('Modification réussie ! L\'utilisateur a été modifié avec succès.');
          this.router.navigate(['/dashboard-admin/utilisateur']);
        },
        error: (err: any) => {
          console.error(err);
          this.alertService.error('Échec de la modification ! Une erreur est survenue.');
        }
      });
    } else {
      this.utilisateurService.createUtilisateur(userData).subscribe({
        next: (res: any) => {
          this.alertService.success('Enregistrement réussi ! L\'utilisateur a été enregistré avec succès.');
          this.router.navigate(['/dashboard-admin/utilisateur']);
        },
        error: (err: any) => {
          console.error(err);
          this.alertService.error('Échec de l\'enregistrement ! Une erreur est survenue.');
        }
      });
    }
  }

  cancel(): void {
    this.router.navigate(['/dashboard-admin/utilisateur']);
  }
}
