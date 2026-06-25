import { TestBed } from '@angular/core/testing';

import { Unite } from './unite';

describe('Unite', () => {
  let service: Unite;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Unite);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
