import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AjouterEssai } from './ajouter-essai';

describe('AjouterEssai', () => {
  let component: AjouterEssai;
  let fixture: ComponentFixture<AjouterEssai>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AjouterEssai]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AjouterEssai);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
