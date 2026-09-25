from decimal import Decimal

from sqlmodel import Session,select

from app.models.rater import Rater
from app.models.ratings import Movie_Rating

# τωρα αυτο γινεται επειδη το dataset με τα ratings ειχε ηδη user_id και movie_id και εγινε λιγο περιπλοκο
# αλλα αν δεν ειχε, θα επρεπε να φτιαξουμε ενα rater για καθε user και να το χρησιμοποιησουμε για να φτιαξουμε τα ratings.
# Αυτο γινεται με την get_or_create_rater_for_user
# Δεν εγινε με τον καλυτερο τροπο αλλα πανω στο μπερδεμα τωρα λειτουργει.
# Απλα να ξερουμε οτι καθε user εχει ενα rater και καθε rating εχει ενα rater_id και movie_id και stars.

def get_or_create_rater_for_user(
    *,
    session: Session,
    user_id: int,
) -> Rater:
    rater = session.exec(
        select(Rater).where(Rater.user_id == user_id)
    ).first()

    if rater is not None:
        return rater

    rater = Rater(user_id=user_id)
    session.add(rater)

    # flush uncommited orm update 
    session.flush()
    session.refresh(rater)

    return rater


def upsert_movie_rating(
    *,
    session: Session,
    rater_id: int,
    movie_id: int,
    stars: Decimal,
) -> Movie_Rating:
    movie_rating = session.exec(
        select(Movie_Rating).where(
            Movie_Rating.rater_id == rater_id,
            Movie_Rating.movie_id == movie_id,
        )
    ).first()

    if movie_rating is not None:
        movie_rating.stars = stars
        session.add(movie_rating)
        return movie_rating

    movie_rating = Movie_Rating(
        rater_id=rater_id,
        movie_id=movie_id,
        stars=stars,
    )

    session.add(movie_rating)
    return movie_rating    