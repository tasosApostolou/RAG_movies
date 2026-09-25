import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UserMoviesComponent } from './user-movies.component';

describe('UserMoviesComponent', () => {
  let component: UserMoviesComponent;
  let fixture: ComponentFixture<UserMoviesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserMoviesComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(UserMoviesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
