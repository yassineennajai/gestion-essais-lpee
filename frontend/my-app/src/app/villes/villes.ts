import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AlertService } from '../services/alert'; // 👈 تصحيح مسار استيراد خدمة التنبيهات
import { UtilisateurService } from '../services/utilisateur'; // Importation du service de recherche globale
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-villes',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './villes.html',
  styleUrls: ['./villes.css']
})
export class VillesComponent implements OnInit, OnDestroy {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private alertService = inject(AlertService); // Injection d'AlertService pour les retours utilisateur
  private utilisateurService = inject(UtilisateurService); // Injection du service de recherche globale

  villeForm!: FormGroup;
  isSubmitted = false;
  isEditMode = false;
  currentVilleId: number | null = null;
  showModal = false;

  private apiUrl = 'http://127.0.0.1:5000/api/villes';

  // Propriétés de contrôle pour la pagination et le filtrage
  originalVilles: any[] = [];
  filteredVilles: any[] = [];
  paginatedVilles: any[] = [];

  // Propriété publique requise directement par le template pour l'affichage réactif
  villes: any[] = [];

  currentPage: number = 1;
  pageSize: number = 6; // Nombre de villes affichées par page
  totalPages: number = 1;
  pagesArray: number[] = [];
  searchTerm: string = '';

  private searchSubscription!: Subscription;

  ngOnInit(): void {
    this.initForm();
    this.loadVilles();
    this.subscribeToSearch();
  }

  initForm(): void {
    this.villeForm = this.fb.group({
      nom_ville: ['', Validators.required]
    });
  }

  get f() { return this.villeForm.controls; }

  // Souscription au flux de recherche globale du header
  subscribeToSearch(): void {

    const service = this.utilisateurService as any;
    const searchObservable = service.currentSearchTerm || service.searchTerm$;

    if (searchObservable) {
      this.searchSubscription = searchObservable.subscribe({
        next: (term: string) => {
          this.searchTerm = term || '';
          this.currentPage = 1;
          this.filterAndPaginate();
        },
        error: (err: any) => console.error('Erreur recherche globale:', err)
      });
    }
  }

  loadVilles(): void {
    this.http.get<any[]>(this.apiUrl).subscribe({
      next: (data: any[]) => {
        this.originalVilles = data || [];
        this.filterAndPaginate();
      },
      error: (err: any) => console.error('Erreur lors du chargement des villes :', err)
    });
  }


  filterAndPaginate(): void {
    let temp = [...this.originalVilles];

    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase().trim();
      temp = temp.filter((v: any) => v.nom_ville?.toLowerCase().includes(term));
    }

    this.filteredVilles = temp;
    this.totalPages = Math.ceil(this.filteredVilles.length / this.pageSize) || 1;

    if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages;
    }

    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    this.paginatedVilles = this.filteredVilles.slice(startIndex, endIndex);


    this.villes = this.paginatedVilles;

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
    return this.filteredVilles.length === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

  get endRecordIndex(): number {
    const calculatedEnd = this.currentPage * this.pageSize;
    return calculatedEnd > this.filteredVilles.length ? this.filteredVilles.length : calculatedEnd;
  }

  openAddModal(): void {
    this.isEditMode = false;
    this.isSubmitted = false;
    this.currentVilleId = null;
    this.villeForm.reset();
    this.showModal = true;
  }

  openEditModal(ville: any): void {
    this.isEditMode = true;
    this.isSubmitted = false;
    this.currentVilleId = ville.id_ville;
    this.villeForm.patchValue({
      nom_ville: ville.nom_ville
    });
    this.showModal = true;
  }

  closeModal(): void {
    this.showModal = false;
    this.villeForm.reset();
  }

  save(): void {
    this.isSubmitted = true;
    if (this.villeForm.invalid) {
      this.alertService.error('Formulaire invalide ! Veuillez saisir le nom de la ville.');
      return;
    }

    const payload = this.villeForm.value;

    if (this.isEditMode && this.currentVilleId) {
      this.http.put(`${this.apiUrl}/${this.currentVilleId}`, payload).subscribe({
        next: (res: any) => {
          this.alertService.success('Modification réussie ! La ville a été modifiée avec succès.');
          this.loadVilles();
          this.closeModal();
        },
        error: (err: any) => {
          console.error(err);
          this.alertService.error('Échec de la modification ! Une erreur est survenue.');
        }
      });
    } else {
      this.http.post(this.apiUrl, payload).subscribe({
        next: (res: any) => {
          this.alertService.success('Enregistrement réussi ! La ville a été ajoutée avec succès.');
          this.loadVilles();
          this.closeModal();
        },
        error: (err: any) => {
          console.error(err);
          this.alertService.error('Échec de l\'enregistrement ! Une erreur est survenue.');
        }
      });
    }
  }

  deleteVille(id: number): void {
    this.alertService.confirm(
      'Voulez-vous vraiment supprimer cette ville ?',
      'Cette action est irréversible et retirera définitivement la ville de la base de données.',
      'Oui, supprimer',
      'Annuler'
    ).then((confirme: boolean) => {
      if (confirme) {
        this.http.delete(`${this.apiUrl}/${id}`).subscribe({
          next: (res: any) => {
            this.alertService.success('Ville supprimée avec succès !');
            this.loadVilles();
          },
          error: (err: any) => {
            console.error(err);
            this.alertService.error('Impossible de supprimer cette ville. Elle est probablement liée à des unités.');
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
