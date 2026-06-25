import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { forkJoin, of, Subscription } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { EssaiService } from '../services/essais';
import { UtilisateurService } from '../services/utilisateur'; // Pour lier la recherche globale
import { AlertService } from '../services/alert';

@Component({
  selector: 'app-essais',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './essais.html',
  styleUrl: './essais.css'
})
export class EssaisComponent implements OnInit, OnDestroy {
  private essaiService = inject(EssaiService);
  private utilisateurService = inject(UtilisateurService);
  private router = inject(Router);
  private alertService = inject(AlertService);

  essaiList: any[] = [];
  filteredEssaiList: any[] = []; // Liste filtrée par la recherche
  paginatedEssaiList: any[] = []; // Liste finale découpée pour la page active
  allUnites: any[] = [];
  domaines: any[] = [];
  isLoading: boolean = true;

  isAdmin: boolean = false;
  isLNM: boolean = false;
  userUniteId: number | null = null;

  // 📊 Propriétés de Pagination
  currentPage: number = 1;
  pageSize: number = 5;
  totalPages: number = 1;
  pagesArray: number[] = [];
  searchTerm: string = '';

  private searchSubscription!: Subscription;

  ngOnInit(): void {
    this.checkUserRole();
    this.loadInitialData();

    
    const service = this.utilisateurService as any;
    const searchObservable = service.currentSearchTerm || service.searchTerm$;

    if (searchObservable) {
      this.searchSubscription = searchObservable.subscribe((term: string) => {
        this.searchTerm = term || '';
        this.currentPage = 1; // Retour à la première page lors d'une recherche
        this.filterAndPaginate();
      });
    }
  }

  ngOnDestroy(): void {
    if (this.searchSubscription) {
      this.searchSubscription.unsubscribe();
    }
  }

  private checkUserRole(): void {
    const currentUserString = localStorage.getItem('user') || localStorage.getItem('currentUser');
    if (currentUserString) {
      try {
        const user = JSON.parse(currentUserString);
        const roleStr = String(user.role || user.role_code || '').toUpperCase().trim();

        this.isAdmin = roleStr.includes('ADMIN');

        // تأمين جلب الـ ID بكلا الصفتين لتجنب القيمة الفارغة (null)
        this.userUniteId = user.id_unite ? Number(user.id_unite) : (user.idUnite ? Number(user.idUnite) : null);

        const nomUnite = String(user.nom_unite || user.unite || '').toUpperCase();
        if (nomUnite.includes('LNM') || nomUnite.includes('MECANIQUE')) {
          this.isLNM = true;
        }
      } catch (e) {
        console.error("Erreur lors du décodage du rôle :", e);
      }
    }
  }

  loadInitialData(): void {
    this.isLoading = true;

    forkJoin({
      unites: this.essaiService.getUnites().pipe(catchError(() => of([]))),
      domaines: this.essaiService.getDomaines().pipe(catchError(() => of([]))),
      essais: this.essaiService.getEssais().pipe(catchError(() => of([])))
    }).subscribe({
      next: (resultats: any) => {
        this.allUnites = resultats.unites || [];
        this.domaines = resultats.domaines || [];
        const rawEssais = resultats.essais || [];

        let filtered: any[] = [];
        if (this.isAdmin || this.isLNM) {
          filtered = rawEssais;
        } else {
          filtered = rawEssais.filter((e: any) => {
            const bId = e.id_unite ?? e.idUnite ?? e.unite_id ?? e.unite?.id;
            return bId !== null && bId !== undefined && Number(bId) === Number(this.userUniteId);
          });
        }

        this.essaiList = filtered.map((e: any) => {
          const matchingUnite = this.allUnites.find(u => Number(u.id_unite || u.id) === Number(e.id_unite));
          return {
            ...e,
            nom_domaine: e.nom_domaine || this.findDomaineName(e.id_domaine),
            nom_famille: e.nom_famille || '--',
            nom_unite: e.nom_unite || (matchingUnite ? (matchingUnite.libelle || matchingUnite.nom_unite) : '--'),
            nom_ville: e.nom_ville || (matchingUnite ? (matchingUnite.nom_ville || matchingUnite.ville?.nom_ville) : '--')
          };
        });

        this.filterAndPaginate();
        this.isLoading = false;
      },
      error: (err: any) => {
        console.error('Erreur lors du chargement initial :', err);
        this.isLoading = false;
        this.fallbackLoadEssais();
      }
    });
  }

  private fallbackLoadEssais(): void {
    this.essaiService.getEssais().subscribe({
      next: (data: any[]) => {
        const rawEssais = data || [];
        if (this.isAdmin || this.isLNM) {
          this.essaiList = rawEssais;
        } else {
          this.essaiList = rawEssais.filter((e: any) => {
            const bId = e.id_unite ?? e.idUnite ?? e.unite_id;
            return bId !== null && bId !== undefined && Number(bId) === Number(this.userUniteId);
          });
        }
        this.filterAndPaginate();
      },
      error: (err: any) => console.error('Erreur fallback :', err)
    });
  }

  filterAndPaginate(): void {
    let temp = [...this.essaiList];

    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase().trim();
      temp = temp.filter(e =>
        (e.intitule && e.intitule.toLowerCase().includes(term)) ||
        (e.type && e.type.toLowerCase().includes(term)) ||
        (e.nom_unite && e.nom_unite.toLowerCase().includes(term)) ||
        (e.nom_domaine && e.nom_domaine.toLowerCase().includes(term)) ||
        (e.nom_famille && e.nom_famille.toLowerCase().includes(term))
      );
    }

    this.filteredEssaiList = temp;
    this.totalPages = Math.ceil(this.filteredEssaiList.length / this.pageSize) || 1;

    if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages;
    }

    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginatedEssaiList = this.filteredEssaiList.slice(start, end);

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
    if (this.filteredEssaiList.length === 0) return 0;
    return (this.currentPage - 1) * this.pageSize + 1;
  }

  get endRecordIndex(): number {
    const calculatedEnd = this.currentPage * this.pageSize;
    return calculatedEnd > this.filteredEssaiList.length ? this.filteredEssaiList.length : calculatedEnd;
  }

  private findDomaineName(idDomaine: number): string {
    if (!idDomaine || !this.domaines.length) return '--';
    const found = this.domaines.find(d => Number(d.id_domaine) === Number(idDomaine));
    return found ? (found.libelle || found.nom_domaine) : '--';
  }

  naviguerVersAjout(): void {
    if (this.isAdmin) return;
    this.router.navigate(['/dashboard-admin/ajouter-essai']);
  }

  editEssai(essai: any): void {
    this.router.navigate(['/dashboard-admin/ajouter-essai'], {
      state: { data: { ...essai } }
    });
  }

  deleteEssai(id: any): void {
    if (this.isAdmin) return;
    const targetId = id?.id_essai || id;
    if (!targetId) return;

    this.alertService.confirm(
      'Voulez-vous vraiment supprimer cet essai ?',
      'Cette action est définitive et supprimera l\'essai de la base de données.',
      'Oui, supprimer',
      'Annuler'
    ).then((confirme: boolean) => {
      if (confirme) {
        this.essaiService.deleteEssai(targetId).subscribe({
          next: () => {
            this.alertService.success('L\'essai a été supprimé avec succès.');
            this.loadInitialData();
          },
          error: (err: any) => {
            console.error('Erreur lors de la suppression :', err);
            this.alertService.error('Échec de la suppression ! Une erreur est survenue.');
          }
        });
      }
    });
  }
}
