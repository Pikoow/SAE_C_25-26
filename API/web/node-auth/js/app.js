const logoutBtn = document.getElementById("logoutBtn");

logoutBtn.addEventListener("click", async () => {
  try {
    const res = await fetch("http://localhost:3000/logout", {
      method: "POST",
      credentials: "include"
    });

    const result = await res.json();

    if (result.success) {
      window.location.href = "../../accueil.html"; // redirige vers login
    } else {
      alert(result.error);
    }
  } catch (err) {
    console.error(err);
    alert("Erreur réseau");
  }
});
