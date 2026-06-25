import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';
import { UtilisateurService } from '../services/utilisateur'; // لربط البحث الفوري والوحدات
import { AlertService } from '../services/alert'; // 👈 تم تصحيح مسار استيراد الخدمة المشتركة هنا

@Component({
  selector: 'app-unites',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './unite.html', // تم تصحيح هذا المسار ليصبح مفرد ومطابقاً لاسم الملف المحلي!
  styleUrls: ['./unite.css']
})
export class UnitesComponent implements OnInit, OnDestroy {
  private fbService = inject(UtilisateurService);
  private router = inject(Router);
  private alertService = inject(AlertService);

  isLoading = true;

  uniteListRaw: any[] = [];
  filteredUniteList: any[] = [];
  uniteList: any[] = [];

  currentPage: number = 1;
  pageSize: number = 5;
  totalPages: number = 1;
  pagesArray: number[] = [];
  searchTerm: string = '';

  private searchSubscription!: Subscription;

  ngOnInit(): void {
    this.loadUnites();
    this.subscribeToSearch();
  }

  loadUnites(): void {
    this.isLoading = true;
    this.fbService.getUnites().subscribe({
      next: (data: any[]) => {
        this.uniteListRaw = data || [];
        this.filterAndPaginate();
        this.isLoading = false;
      },
      error: (err: any) => {
        console.error('Erreur lors du chargement des unités:', err);
        this.isLoading = false;
      }
    });
  }

  subscribeToSearch(): void {
    const service = this.fbService as any;
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

  filterAndPaginate(): void {
    let temp = [...this.uniteListRaw];

    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase().trim();
      temp = temp.filter((u: any) =>
        (u.libelle && u.libelle.toLowerCase().includes(term)) ||
        (u.contact && u.contact.toLowerCase().includes(term)) ||
        (u.type && u.type.toLowerCase().includes(term)) ||
        ((u.la_ville?.nom_ville || u.nom_ville) && String(u.la_ville?.nom_ville || u.nom_ville).toLowerCase().includes(term))
      );
    }

    this.filteredUniteList = temp;
    this.totalPages = Math.ceil(this.filteredUniteList.length / this.pageSize) || 1;

    if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages;
    }

    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    this.uniteList = this.filteredUniteList.slice(startIndex, endIndex);

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
    return this.filteredUniteList.length === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

  get endRecordIndex(): number {
    const calculatedEnd = this.currentPage * this.pageSize;
    return calculatedEnd > this.filteredUniteList.length ? this.filteredUniteList.length : calculatedEnd;
  }

  naviguerVersAjout(): void {
    this.router.navigate(['/dashboard-admin/ajouter-unite']);
  }

  editUnite(unite: any): void {
    this.router.navigate(['/dashboard-admin/ajouter-unite'], {
      state: { data: { ...unite } }
    });
  }

  deleteUnite(id: number): void {
    this.alertService.confirm(
      'Voulez-vous vraiment supprimer cette unité ?',
      'Cette action supprimera définitivement l\'unité de la base de données.',
      'Oui, supprimer',
      'Annuler'
    ).then((confirmed: boolean) => {
      if (confirmed) {
        const service = this.fbService as any;
        if (service.deleteUnite) {
          service.deleteUnite(id).subscribe({
            next: () => {
              this.alertService.success('Unité supprimée avec succès !');
              this.loadUnites();
            },
            error: (err: any) => {
              console.error(err);
              this.alertService.error('Impossible de supprimer cette unité. Elle est probablement liée à des essais.');
            }
          });
        }
      }
    });
  }

  ngOnDestroy(): void {
    if (this.searchSubscription) {
      this.searchSubscription.unsubscribe();
    }
  }
}
