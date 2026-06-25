import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AjouterUnite } from './ajouter-unite';

describe('AjouterUnite', () => {
  let component: AjouterUnite;
  let fixture: ComponentFixture<AjouterUnite>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AjouterUnite]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AjouterUnite);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
