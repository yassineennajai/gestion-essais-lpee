import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AjouterUtilisateur } from './ajouter-utilisateur';

describe('AjouterUtilisateur', () => {
  let component: AjouterUtilisateur;
  let fixture: ComponentFixture<AjouterUtilisateur>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AjouterUtilisateur]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AjouterUtilisateur);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
