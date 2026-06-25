import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { UtilisateurService } from '../services/utilisateur';
import { AlertService } from '../services/alert';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-utilisateurs',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './utilisateurs.html',
  styleUrls: ['./utilisateurs.css']
})
export class UtilisateursComponent implements OnInit, OnDestroy {
  private utilisateurService = inject(UtilisateurService);
  private alertService = inject(AlertService);
  private router = inject(Router);

  utilisateurs: any[] = [];
  allFilteredUtilisateurs: any[] = [];
  filteredUtilisateurs: any[] = [];
  isLoading: boolean = true;

  private searchSubscription!: Subscription;
  searchTerm: string = '';


  currentPage: number = 1;
  pageSize: number = 6;
  totalPages: number = 1;
  pagesArray: number[] = [];

  ngOnInit(): void {
    this.chargerUtilisateurs();
    this.ecouterLaRecherche();
  }

  chargerUtilisateurs(): void {
    this.isLoading = true;
    this.utilisateurService.getUtilisateurs().subscribe({
      next: (res: any) => {
        this.utilisateurs = Array.isArray(res) ? res : res.utilisateurs || [];
        this.filterAndPaginate();
        this.isLoading = false;
      },
      error: (err: any) => {
        console.error('Erreur Backend Flask:', err);
        this.isLoading = false;
      }
    });
  }

  ecouterLaRecherche(): void {

    const service = this.utilisateurService as any;
    const searchObservable = service.currentSearchTerm || service.searchTerm$;

    if (searchObservable) {
      this.searchSubscription = searchObservable.subscribe({
        next: (term: string) => {
          this.searchTerm = term || '';
          this.currentPage = 1;
          this.filterAndPaginate();
        },
        error: (err: any) => console.error('Erreur recherche globale :', err)
      });
    }
  }



  filterAndPaginate(): void {
    const cleanTerm = this.searchTerm.trim().toLowerCase();
    let temp = [...this.utilisateurs];


    if (cleanTerm) {
      temp = temp.filter((u: any) =>
        u.email?.toLowerCase().includes(cleanTerm) ||
        u.nom_unite?.toLowerCase().includes(cleanTerm) ||
        u.role?.toLowerCase().includes(cleanTerm)
      );
    }

    this.allFilteredUtilisateurs = temp;

    this.totalPages = Math.ceil(this.allFilteredUtilisateurs.length / this.pageSize) || 1;


    if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages;
    }

    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    this.filteredUtilisateurs = this.allFilteredUtilisateurs.slice(startIndex, endIndex);


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
    return this.allFilteredUtilisateurs.length === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

  
  get endRecordIndex(): number {
    const calculatedEnd = this.currentPage * this.pageSize;
    return calculatedEnd > this.allFilteredUtilisateurs.length ? this.allFilteredUtilisateurs.length : calculatedEnd;
  }

  onModifier(user: any): void {
    const id = user.id_utilisateur || user.id;
    if (id) {
      this.router.navigate(['/dashboard-admin/ajouter-utilisateur', id]);
    } else {
      console.error("Impossible de modifier : ID introuvable", user);
    }
  }

  deleteUtilisateur(id: number): void {
    this.alertService.confirm(
      'Voulez-vous vraiment supprimer cet utilisateur ?',
      'Cette action retirera définitivement cet utilisateur de la base de données.',
      'Oui, supprimer',
      'Annuler'
    ).then((confirmed: boolean) => {
      if (confirmed) {
        this.utilisateurService.deleteUtilisateur(id).subscribe({
          next: () => {
            this.alertService.success('Utilisateur supprimé avec succès !');
            this.chargerUtilisateurs();
          },
          error: (err: any) => {
            console.error(err);
            this.alertService.error('Erreur lors de la suppression de l\'utilisateur.');
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
