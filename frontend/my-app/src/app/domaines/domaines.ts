import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AlertService } from '../services/alert';
import { UtilisateurService } from '../services/utilisateur';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-domaines',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './domaines.html',
  styleUrls: ['./domaines.css']
})
export class DomainesComponent implements OnInit, OnDestroy {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private alertService = inject(AlertService);
  private utilisateurService = inject(UtilisateurService);

  domaineForm!: FormGroup;
  isSubmitted = false;
  isEditMode = false;
  currentDomaineId: number | null = null;
  showModal = false;

  private apiUrl = 'http://127.0.0.1:5000/api/domaines';

  originalDomaines: any[] = [];
  filteredDomaines: any[] = [];
  paginatedDomaines: any[] = [];


  domaines: any[] = [];

  currentPage: number = 1;
  pageSize: number = 6;
  totalPages: number = 1;
  pagesArray: number[] = [];
  searchTerm: string = '';

  private searchSubscription!: Subscription;

  ngOnInit(): void {
    this.initForm();
    this.loadDomaines();
    this.subscribeToSearch();
  }

  initForm(): void {
    this.domaineForm = this.fb.group({
      libelle: ['', Validators.required]
    });
  }

  get f() { return this.domaineForm.controls; }

  subscribeToSearch(): void {
    const service = this.utilisateurService as any;
    const searchObservable = service.currentSearchTerm || service.searchTerm$;

    if (searchObservable) {
      this.searchSubscription = searchObservable.subscribe({
        next: (term: string) => {
          this.searchTerm = term || '';
          this.currentPage = 1;
          this.filterAndPaginate();
        }
      });
    }
  }

  loadDomaines(): void {
    this.http.get<any[]>(this.apiUrl).subscribe({
      next: (data) => {
        this.originalDomaines = data || [];
        this.filterAndPaginate();
      },
      error: (err) => console.error('Erreur chargement domaines:', err)
    });
  }


  filterAndPaginate(): void {
    let temp = [...this.originalDomaines];


    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase().trim();
      temp = temp.filter((d: any) => d.libelle?.toLowerCase().includes(term));
    }

    this.filteredDomaines = temp;


    this.totalPages = Math.ceil(this.filteredDomaines.length / this.pageSize) || 1;


    if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages;
    }


    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    this.paginatedDomaines = this.filteredDomaines.slice(startIndex, endIndex);


    this.domaines = this.paginatedDomaines;

    this.pagesArray = Array.from({ length: this.totalPages }, (_, i) => i + 1);
  }


  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.filterAndPaginate();
    }
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.filterAndPaginate();
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.filterAndPaginate();
    }
  }


  get startRecordIndex(): number {
    return this.filteredDomaines.length === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

 
  get endRecordIndex(): number {
    const calculatedEnd = this.currentPage * this.pageSize;
    return calculatedEnd > this.filteredDomaines.length ? this.filteredDomaines.length : calculatedEnd;
  }

  openAddModal(): void {
    this.isEditMode = false;
    this.isSubmitted = false;
    this.currentDomaineId = null;
    this.domaineForm.reset();
    this.showModal = true;
  }

  openEditModal(domaine: any): void {
    this.isEditMode = true;
    this.isSubmitted = false;
    this.currentDomaineId = domaine.id_domaine;
    this.domaineForm.patchValue({
      libelle: domaine.libelle
    });
    this.showModal = true;
  }

  closeModal(): void {
    this.showModal = false;
    this.domaineForm.reset();
  }

  save(): void {
    this.isSubmitted = true;
    if (this.domaineForm.invalid) {
      this.alertService.error('Formulaire invalide ! Veuillez saisir le libellé du domaine.');
      return;
    }

    const payload = this.domaineForm.value;

    if (this.isEditMode && this.currentDomaineId) {
      this.http.put(`${this.apiUrl}/${this.currentDomaineId}`, payload).subscribe({
        next: () => {
          this.alertService.success('Modification réussie ! Le domaine d\'activité a été modifié.');
          this.loadDomaines();
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
          this.alertService.success('Enregistrement réussi ! Le domaine d\'activité a été ajouté.');
          this.loadDomaines();
          this.closeModal();
        },
        error: (err) => {
          console.error(err);
          this.alertService.error('Échec de l\'enregistrement ! Une erreur est survenue.');
        }
      });
    }
  }

  deleteDomaine(id: number): void {
    this.alertService.confirm(
      'Êtes-vous sûr de vouloir supprimer ce domaine d\'activité ?',
      'Cette action supprimera définitivement le domaine de la base de données.',
      'Oui, supprimer',
      'Annuler'
    ).then((confirme) => {
      if (confirme) {
        this.http.delete(`${this.apiUrl}/${id}`).subscribe({
          next: () => {
            this.alertService.success('Supprimé ! Le domaine d\'activité a été retiré.');
            this.loadDomaines();
          },
          error: (err) => {
            console.error(err);
            this.alertService.error('Échec de la suppression ! Une erreur est survenue.');
          }
        });
      }
    });
  }

  ngOnDestroy(): void {
    if (this.searchSubscription) {
      this.searchSubscription.unsubscribe();
    }
  }
}
