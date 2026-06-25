import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule, NgClass, NgIf, NgFor } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { NormeService } from '../services/norme';
import { AlertService } from '../services/alert';
import { UtilisateurService } from '../services/utilisateur';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-normes',
  templateUrl: './normes.html',
  styleUrls: ['./normes.css'],
  standalone: true,
  imports: [CommonModule, RouterLink, NgIf, NgFor, FormsModule]
})
export class Normes implements OnInit, OnDestroy {

  private normeService = inject(NormeService);
  private alertService = inject(AlertService);
  private utilisateurService = inject(UtilisateurService);

  normes: any[] = [];
  originalNormes: any[] = [];
  filteredNormesList: any[] = [];
  paginatedNormesList: any[] = [];

  isLoading: boolean = true;

  idNormeEnCoursDEdition: number | null = null;

  normeModifiee: any = {
    libelle: '',
    parties: []
  };

  nouvellePartieNo: string = '';
  nouvellePartieTitre: string = '';


  currentPage: number = 1;
  pageSize: number = 5;
  totalPages: number = 1;
  pagesArray: number[] = [];
  searchTerm: string = '';

  private searchSubscription!: Subscription;

  ngOnInit(): void {
    this.loadNormes();
    this.subscribeToSearch();
  }

  ngOnDestroy(): void {
    if (this.searchSubscription) {
      this.searchSubscription.unsubscribe();
    }
  }


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
        error: (err: any) => console.error('Erreur recherche globale normes:', err)
      });
    }
  }

  loadNormes(): void {
    this.isLoading = true;
    this.normeService.getAllNormes().subscribe({
      next: (data: any) => {
        this.originalNormes = (data || []).map((n: any) => ({
          ...n,
          isOpen: false,
          parties: n.parties || []
        }));
        this.filterAndPaginate();
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Erreur de chargement des normes:', err);
        this.isLoading = false;
      }
    });
  }


  filterAndPaginate(): void {
    const cleanTerm = this.searchTerm.trim().toLowerCase();
    let temp = [...this.originalNormes];


    if (cleanTerm) {
      temp = temp.filter(n =>
        (n.libelle && n.libelle.toLowerCase().includes(cleanTerm)) ||
        (n.parties && n.parties.some((p: any) => p.titre?.toLowerCase().includes(cleanTerm) || p.no_partie?.toString().includes(cleanTerm)))
      );
    }

    this.filteredNormesList = temp;


    this.totalPages = Math.ceil(this.filteredNormesList.length / this.pageSize) || 1;


    if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages;
    }


    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    this.paginatedNormesList = this.filteredNormesList.slice(startIndex, endIndex);


    this.normes = this.paginatedNormesList;


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
    return this.filteredNormesList.length === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

  get endRecordIndex(): number {
    const calculatedEnd = this.currentPage * this.pageSize;
    return calculatedEnd > this.filteredNormesList.length ? this.filteredNormesList.length : calculatedEnd;
  }

  activerModification(norme: any): void {
    this.idNormeEnCoursDEdition = norme.id_norme;

    this.normeModifiee = JSON.parse(JSON.stringify(norme));
    this.normeModifiee.parties = this.normeModifiee.parties || [];

    this.nouvellePartieNo = '';
    this.nouvellePartieTitre = '';
  }

  annulerModification(): void {
    this.idNormeEnCoursDEdition = null;
  }

  addPartieForm(): void {
    if (this.nouvellePartieNo.trim() && this.nouvellePartieTitre.trim()) {
      this.normeModifiee.parties.push({
        no_partie: this.nouvellePartieNo.trim(),
        titre: this.nouvellePartieTitre.trim()
      });

      this.nouvellePartieNo = '';
      this.nouvellePartieTitre = '';
    }
  }

  removePartieForm(index: number): void {
    this.normeModifiee.parties.splice(index, 1);
  }

  enregistrerModification(id: number): void {
    if (!this.normeModifiee.libelle.trim()) {
      this.alertService.error('Libellé obligatoire ! Le nom de la norme ne peut pas être vide.');
      return;
    }

  
    const payload = {
      libelle: this.normeModifiee.libelle.trim(),
      parties: this.normeModifiee.parties.map((p: any) => ({
        no_partie: p.no_partie,
        titre: p.titre
      }))
    };

    this.normeService.updateNorme(id, payload).subscribe({
      next: () => {
        this.alertService.success('Norme sauvegardée avec succès !');
        this.idNormeEnCoursDEdition = null;
        this.loadNormes();
      },
      error: (err) => {
        console.error(err);
        this.alertService.error('Erreur lors de la sauvegarde de la norme.');
      }
    });
  }

  supprimerNorme(id: number): void {
    this.alertService.confirm(
      'Voulez-vous vraiment supprimer cette norme ?',
      'Cette action supprimera également toutes ses parties de manière définitive.',
      'Oui, supprimer',
      'Annuler'
    ).then((confirme) => {
      if (confirme) {
        this.normeService.deleteNorme(id).subscribe({
          next: () => {
            this.alertService.success('Norme supprimée avec succès !');
            this.loadNormes();
          },
          error: (err) => {
            console.error(err);
            this.alertService.error('Erreur lors de la suppression de la norme. Elle est probablement liée à des essais.');
          }
        });
      }
    });
  }
}
