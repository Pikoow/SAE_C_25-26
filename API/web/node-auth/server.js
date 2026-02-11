const express = require("express");
const session = require("express-session");
const bcrypt = require("bcrypt");
const cors = require("cors");
const { Pool } = require("pg");

const app = express();

// ======== CONFIG MIDDLEWARE ========
app.use(express.json());
app.use(cors({
  origin: "http://127.0.0.1:8080", // ton frontend
  credentials: true
}));

app.use(session({
  secret: "supersecretkey",
  resave: false,
  saveUninitialized: false,
  cookie: { secure: false } // true si HTTPS
}));

// ======== POSTGRES ========
const pool = new Pool({
  user: "postgres",
  host: "localhost",
  database: "postgres", 
  password: "6969",
  port: 5432,
});

// Vérification connexion
pool.query("SELECT NOW()")
  .then(res => console.log("Postgres connecté :", res.rows[0]))
  .catch(err => console.error("Erreur connexion Postgres :", err));

// ======== ROUTE LOGIN/REGISTER ========
app.post("/login", async (req, res) => {
  console.log("BODY LOGIN/REGISTER :", req.body);

  const { email, password, firstName, lastName } = req.body;

  if (!email || !password) {
    return res.json({ success: false, error: "Email et mot de passe requis" });
  }

  try {
    // Cherche l'utilisateur
    const userResult = await pool.query(
      "SELECT * FROM sae.users WHERE user_mail = $1",
      [email]
    );

    let user;

    if (userResult.rows.length === 0) {
      // Utilisateur n'existe pas → création
      if (!firstName || !lastName) {
        return res.json({ success: false, error: "Prénom et nom requis pour créer un compte" });
      }

      const hashedPassword = await bcrypt.hash(password, 10);

      const newUser = await pool.query(
        `INSERT INTO sae.users 
          (user_firstname, user_lastname, user_mail, user_password, user_year_created)
         VALUES ($1,$2,$3,$4,NOW())
         RETURNING user_id, user_firstname, user_mail`,
        [firstName, lastName, email, hashedPassword]
      );

      user = newUser.rows[0];
      console.log("NOUVEL UTILISATEUR :", user);

    } else {
      // Utilisateur existe → vérifier mot de passe
      user = userResult.rows[0];

      const validPassword = await bcrypt.compare(password, user.user_password);
      if (!validPassword) {
        return res.json({ success: false, error: "Mot de passe incorrect" });
      }

      console.log("UTILISATEUR TROUVE :", user);
    }

    // Crée session
    req.session.userId = user.user_id;

    res.json({
      success: true,
      message: "Connecté",
      user: {
        id: user.user_id,
        firstName: user.user_firstname,
        email: user.user_mail
      }
    });

  } catch (err) {
    console.error("ERREUR LOGIN/REGISTER :", err);
    res.status(500).json({ error: "Erreur serveur" });
  }
});

// ======== ROUTE DASHBOARD ========
app.get("/dashboard", async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ error: "Non connecté" });
  }

  try {
    const user = await pool.query(
      "SELECT user_id, user_firstname, user_mail FROM sae.users WHERE user_id = $1",
      [req.session.userId]
    );

    res.json({
      message: `Bienvenue ${user.rows[0].user_firstname}`,
      user: user.rows[0]
    });

  } catch (err) {
    console.error("ERREUR DASHBOARD :", err);
    res.status(500).json({ error: "Erreur serveur" });
  }
});

// ======== START SERVER ========
const PORT = 3000;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
