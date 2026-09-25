# 1. Χρησιμοποιούμε την επίσημη εικόνα του Node.js (έκδοση 20 ή 22 που καλύπτει την Angular 19)
FROM node:22-alpine

# 2. Ορίζουμε τον φάκελο εργασίας μέσα στο container
WORKDIR /app

# 3. Αντιγράφουμε τα αρχεία των εξαρτήσεων
COPY package*.json ./

# 4. Εγκαθιστούμε το Angular CLI και όλες τις βιβλιοθήκες του package.json
RUN npm install -g @angular/cli@19.2.26
RUN npm install

# 5. Αντιγράφουμε τον υπόλοιπο κώδικα της εφαρμογής
COPY . .

# 6. Ανοίγουμε τη θύρα 4200
EXPOSE 4200

# 7. Τρέχουμε την Angular και την αναγκάζουμε να ακούει σε όλες τις IP (0.0.0.0) ώστε να είναι προσβάσιμη εκτός container
CMD ["ng", "serve", "--host", "0.0.0.0"]

# docker run -p 4200:4200 -v %cd%:/app -v /app/node_modules movies-angular-app