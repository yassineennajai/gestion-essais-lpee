import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';
import { CommonModule, NgIf, NgFor, NgClass } from '@angular/common';
import { RouterModule, RouterLink } from '@angular/router';
import { DashboardService, DashboardResponse } from '../services/dashboard';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, NgIf, NgFor, NgClass, RouterModule],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class DashboardComponent implements OnInit {


  @ViewChild('adminChart1') adminChart1!: ElementRef;
  @ViewChild('adminChart2') adminChart2!: ElementRef;
  @ViewChild('userChart1') userChart1!: ElementRef;
  @ViewChild('userChart2') userChart2!: ElementRef;

  data!: DashboardResponse;
  loading: boolean = true;
  errorMessage: string = '';
  charts: any[] = [];

  constructor(private dashboardService: DashboardService) { }

  ngOnInit(): void {
    this.loadDashboardData();
  }

  loadDashboardData(): void {
    this.dashboardService.getDashboardStats().subscribe({
      next: (res) => {
        this.data = res;
        this.loading = false;

        setTimeout(() => this.initializeCharts(), 150);
      },
      error: (err) => {
        this.errorMessage = err.error?.message ||'Erreur lors de la récupération des données du tableau de bord.';
        this.loading = false;
      }
    });
  }

  initializeCharts(): void {

    this.charts.forEach(chart => chart.destroy());
    this.charts = [];

    if (this.data.role === 'ADMIN') {

      if (this.adminChart1) {
        const ctx1 = this.adminChart1.nativeElement.getContext('2d');
        this.charts.push(new Chart(ctx1, {
          type: 'bar',
          data: {
            labels: this.data.chart_data.unites_labels || [],
            datasets: [{
              label: "Nombre d'essais",
              data: this.data.chart_data.unites_data || [],
              backgroundColor: '#3b82f6',
              borderRadius: 6
            }]
          },
          options: { responsive: true }
        }));
      }


      if (this.adminChart2) {
        const ctx2 = this.adminChart2.nativeElement.getContext('2d');
        this.charts.push(new Chart(ctx2, {
          type: 'doughnut',
          data: {
            labels: this.data.chart_data.normes_unites_labels || [],
            datasets: [{
              data: this.data.chart_data.normes_unites_data || [],
              backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
            }]
          },
          options: { responsive: true }
        }));
      }

    } else {

      if (this.userChart1) {
        const ctxU1 = this.userChart1.nativeElement.getContext('2d');
        this.charts.push(new Chart(ctxU1, {
          type: 'line',
          data: {
            labels: this.data.chart_data.mensuels_labels || [],
            datasets: [{
              label: 'Essais réalisés ce mois',
              data: this.data.chart_data.mensuels_data || [],
              borderColor: '#10b981',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              fill: true,
              tension: 0.3
            }]
          },
          options: { responsive: true }
        }));
      }


      if (this.userChart2) {
        const ctxU2 = this.userChart2.nativeElement.getContext('2d');
        this.charts.push(new Chart(ctxU2, {
          type: 'pie',
          data: {
            labels: this.data.chart_data.type_labels || [],
            datasets: [{
              data: this.data.chart_data.type_data || [],
              backgroundColor: ['#3b82f6', '#6b7280']
            }]
          },
          options: { responsive: true }
        }));
      }
    }
  }
}
