import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Unite } from './unite';

describe('Unite', () => {
  let component: Unite;
  let fixture: ComponentFixture<Unite>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Unite]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Unite);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
