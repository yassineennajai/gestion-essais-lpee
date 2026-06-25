import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { FamilleService } from '../services/famille';
import { AlertService } from '../services/alert'; 
import { UtilisateurService } from '../services/utilisateur'; // 👈 Pour lier la recherche globale du header
import { Famille } from '../interfaces/famille';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-familles',
  templateUrl: './familles.html',
  styleUrls: ['./familles.css'],
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule]
})
export class Familles implements OnInit, OnDestroy {
  private familleService = inject(FamilleService);
  private alertService = inject(AlertService); // 👈 Injection du service d'alertes moderne
  private utilisateurService = inject(UtilisateurService); // 👈 Injection du service de recherche globale

  familles: (Famille & { isOpen?: boolean })[] = [];
  filteredFamillesList: any[] = [];
  paginatedFamillesList: any[] = []; // Liste finale découpée pour la page active lue par le HTML

  isLoading: boolean = true;
  idFamilleEnCoursDEdition: number | null = null;
  familleModifiee: Famille = { id_famille: 0, nom_famille: '', sousFamilles: [] };
  nouvelleSousFamille: string = '';
  nouvelleFamilleNom: string = '';

  // 📊 Propriétés de Pagination et Filtrage
  currentPage: number = 1;
  pageSize: number = 5; // Nombre de familles affichées par page
  totalPages: number = 1;
  pagesArray: number[] = [];
  searchTerm: string = '';

  private searchSubscription!: Subscription;

  ngOnInit(): void {
    this.loadFamilles();
    this.subscribeToSearch();
  }

  ngOnDestroy(): void {
    if (this.searchSubscription) {
      this.searchSubscription.unsubscribe();
    }
  }

  // 🔍 Écoute de la recherche globale pour filtrer et repaginer en temps réel
  subscribeToSearch(): void {
    const service = this.utilisateurService as any;
    const searchObservable = service.currentSearchTerm || service.searchTerm$;

    if (searchObservable) {
      this.searchSubscription = searchObservable.subscribe({
        next: (term: string) => {
          this.searchTerm = term || '';
          this.currentPage = 1; // Retour à la première page lors d'une nouvelle recherche
          this.filterAndPaginate();
        },
        error: (err: any) => console.error('Erreur recherche globale familles:', err)
      });
    }
  }

  loadFamilles(): void {
    this.isLoading = true;
    this.familleService.getAllFamilles().subscribe({
      next: (data) => {
        console.log('DATA COMPLETE VENANT DU BACKEND:', data);

        this.familles = (data || []).map(f => {
          const rawSousFamilles = f.sousFamilles || (f as any).sous_familles || [];

          const cleanSousFamilles = (rawSousFamilles || []).map((sf: any) => {
            return {
              id_sous_famille: sf.id_sous_famille || sf.id,
              libelle: sf.libelle || sf.nom_sous_famille || sf.nom || ''
            };
          });

          return {
            ...f,
            isOpen: (f as any).isOpen || false,
            sousFamilles: cleanSousFamilles
          };
        });

        this.filterAndPaginate();
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Erreur chargement familles:', err);
        this.isLoading = false;
      }
    });
  }

  /**
   * 🔍 Algorithme de filtrage et de découpage dynamique par page
   */
  filterAndPaginate(): void {
    const cleanTerm = this.searchTerm.trim().toLowerCase();
    let temp = [...this.familles];

    // 1. Filtrage par terme de recherche
    if (cleanTerm) {
      temp = temp.filter(f =>
        (f.nom_famille && f.nom_famille.toLowerCase().includes(cleanTerm)) ||
        (f.sousFamilles && f.sousFamilles.some((sf: any) => sf.libelle?.toLowerCase().includes(cleanTerm)))
      );
    }

    this.filteredFamillesList = temp;

    // 2. Calcul du nombre de pages
    this.totalPages = Math.ceil(this.filteredFamillesList.length / this.pageSize) || 1;

    // Sécurité : Réajustement de la page courante si elle dépasse le max après filtrage
    if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages;
    }

    // 3. Découpage pour la pagination physique (slice)
    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    this.paginatedFamillesList = this.filteredFamillesList.slice(startIndex, endIndex);

    // 4. Génération de l'index des pages à afficher
    this.pagesArray = Array.from({ length: this.totalPages }, (_, i) => i + 1);
  }

  // 🔀 Méthodes de Navigation de pagination
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
    return this.filteredFamillesList.length === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

  get endRecordIndex(): number {
    const calculatedEnd = this.currentPage * this.pageSize;
    return calculatedEnd > this.filteredFamillesList.length ? this.filteredFamillesList.length : calculatedEnd;
  }

  toggleSection(famille: any): void {
    famille.isOpen = !famille.isOpen;
  }

  activerModification(famille: any): void {
    this.idFamilleEnCoursDEdition = famille.id_famille;
    famille.isOpen = true;

    this.familleModifiee = JSON.parse(JSON.stringify(famille));

    if (this.familleModifiee.sousFamilles) {
      this.familleModifiee.sousFamilles = this.familleModifiee.sousFamilles.map((sf: any) => ({
        id_sous_famille: sf.id_sous_famille,
        libelle: sf.libelle || sf.nom_sous_famille || sf.nom || ''
      }));
    } else {
      this.familleModifiee.sousFamilles = [];
    }

    (this.familleModifiee as any).isOpen = true;
    this.nouvelleSousFamille = '';
  }

  annulerModification(): void {
    this.idFamilleEnCoursDEdition = null;
  }

  addSousFamilleForm(): void {
    if (this.nouvelleSousFamille.trim()) {
      if (!this.familleModifiee.sousFamilles) {
        this.familleModifiee.sousFamilles = [];
      }

      this.familleModifiee.sousFamilles.push({
        id_sous_famille: 0,
        libelle: this.nouvelleSousFamille.trim()
      } as any);

      this.nouvelleSousFamille = '';
    }
  }

  removeSousFamilleForm(index: number): void {
    this.familleModifiee.sousFamilles?.splice(index, 1);
  }

  enregistrerModification(id: number): void {
    if (!this.familleModifiee.nom_famille.trim()) {
      this.alertService.error('Le nom de la famille est obligatoire !');
      return;
    }

    const cleanPayload = {
      id_famille: this.familleModifiee.id_famille,
      nom_famille: this.familleModifiee.nom_famille.trim(),
      sousFamilles: this.familleModifiee.sousFamilles
    };

    console.log('Envoi de la modification au FamilleService:', cleanPayload);

    this.familleService.updateFamille(id, cleanPayload).subscribe({
      next: () => {
        this.alertService.success('Modification réussie ! La famille a bien été mise à jour.');
        this.idFamilleEnCoursDEdition = null;
        this.loadFamilles();
      },
      error: (err) => {
        console.error('Erreur lors de la modification:', err);
        this.alertService.error('Échec de la modification ! Une erreur est survenue.');
      }
    });
  }

  creerFamille(): void {
    if (!this.nouvelleFamilleNom.trim()) {
      this.alertService.error('Veuillez saisir le nom de la famille !');
      return;
    }

    const nouvelleFamille = {
      nom_famille: this.nouvelleFamilleNom.trim(),
      sousFamilles: []
    };

    this.familleService.createFamille(nouvelleFamille).subscribe({
      next: () => {
        this.alertService.success('Succès ! La famille a bien été ajoutée.');
        this.nouvelleFamilleNom = '';
        this.loadFamilles();
      },
      error: (err) => {
        console.error('Erreur lors de la création:', err);
        this.alertService.error('Erreur lors de la création de la famille.');
      }
    });
  }

  supprimerFamille(id: number): void {
    this.alertService.confirm(
      'Voulez-vous vraiment supprimer cette famille ?',
      'Cette action supprimera également toutes ses sous-familles de manière définitive.',
      'Oui, supprimer',
      'Annuler'
    ).then((confirme) => {
      if (confirme) {
        this.familleService.deleteFamille(id).subscribe({
          next: () => {
            this.alertService.success('Supprimé ! La famille et ses sous-familles ont été retirées.');
            this.loadFamilles();
          },
          error: (err) => {
            console.error('Erreur lors de la suppression :', err);
            this.alertService.error('Impossible de supprimer cette famille. Elle est probablement liée à des essais.');
          }
        });
      }
    });
  }
}
