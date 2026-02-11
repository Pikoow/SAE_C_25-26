const express = require("express");
const session = require("express-session");
const bcrypt = require("bcrypt");
const cors = require("cors");
const { Pool } = require("pg");
const path = require("path");

var dotenv = require('dotenv');
dotenv.config({ path: path.join(__dirname, "../../../.env") });

const app = express();

app.use(express.json());
app.use(cors({
  origin: "http://127.0.0.1:8080",
  credentials: true
}));
app.use(session({
  secret: "supersecretkey",
  resave: false,
  saveUninitialized: false,
  cookie: { secure: false }
}));

app.use(express.static(path.join(__dirname, ".."))); 

app.get("/connexion.html", (req, res) => {
  res.sendFile(path.join(__dirname, "../connexion.html"));
});

app.use("/images", express.static(path.join(__dirname, "../API/images")));

const pool = new Pool({
  user: process.env.POSTGRES_USER,
  host: "localhost",
  database: process.env.POSTGRES_DBNAME,
  password: process.env.POSTGRES_PASSWORD,
  port: parseInt(process.env.POSTGRES_PORT || "5432")
});

pool.query("SELECT NOW()")
  .then(res => console.log("Postgres connecté :", res.rows[0]))
  .catch(err => console.error("Erreur connexion Postgres :", err));

// ======== LOGIN / REGISTER ========
app.post("/login", async (req, res) => {
  const { firstName, lastName, email, password, age, gender, location } = req.body;

  if (!email || !password) return res.json({ success: false, error: "Email et mot de passe requis" });

  try {
    let userResult = await pool.query(
      "SELECT * FROM sae.users WHERE user_mail = $1",
      [email]
    );

    let user;

    if (userResult.rows.length === 0) {
      // Création utilisateur
      if (!firstName || !lastName) return res.json({ success: false, error: "Prénom et nom requis" });

      const hashedPassword = await bcrypt.hash(password, 10);

      const newUser = await pool.query(
        `INSERT INTO sae.users 
          (user_firstname, user_lastname, user_mail, user_password, user_age, user_gender, user_location, user_year_created)
         VALUES ($1,$2,$3,$4,$5,$6,$7,NOW())
         RETURNING user_id, user_firstname, user_mail`,
        [firstName, lastName, email, hashedPassword, age || null, gender || null, location || null]
      );

      user = newUser.rows[0];
    } else {
      // Login
      user = userResult.rows[0];
      const validPassword = await bcrypt.compare(password, user.user_password);
      if (!validPassword) return res.status(401).json({ success: false, error: "Mot de passe incorrect" });
    }

    // Session
    req.session.userId = user.user_id;

    console.log("Session après login :", req.session);

    res.json({ success: true, message: "Connecté", user });

  } catch (err) {
    console.error("ERREUR LOGIN/REGISTER :", err);
    res.status(500).json({ success: false, error: "Erreur serveur" });
  }
});

// ======== DASHBOARD ========
app.get("/dashboard", async (req, res) => {
  if (!req.session.userId) return res.status(401).json({ error: "Non connecté" });

  try {
    const user = await pool.query(
      "SELECT user_id, user_firstname, user_mail FROM sae.users WHERE user_id=$1",
      [req.session.userId]
    );
    res.json({ message: `Bienvenue ${user.rows[0].user_firstname}`, user: user.rows[0] });
  } catch (err) {
    console.error("ERREUR DASHBOARD :", err);
    res.status(500).json({ error: "Erreur serveur" });
  }
});

// ======== LOGOUT ========
app.post("/logout", (req, res) => {
  req.session.destroy(err => {
    if (err) {
      console.error("ERREUR LOGOUT :", err);
      return res.status(500).json({ success: false });
    }

    res.clearCookie("connect.sid");
    res.json({ success: true });
  });
});




const PORT = 3000;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
