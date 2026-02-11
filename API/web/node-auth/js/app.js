// -------------------- REGISTER --------------------
const registerForm = document.getElementById("registerForm");
if(registerForm){
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = e.target.email.value;
    const password = e.target.password.value;

    const res = await fetch("http://localhost:3000/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      credentials: "include"
    });

    const data = await res.json();
    alert(JSON.stringify(data));

    if(data.success) window.location.href = "dashboard.html";
  });
}

// -------------------- LOGIN --------------------
const loginForm = document.getElementById("loginForm");
if(loginForm){
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = e.target.email.value;
    const password = e.target.password.value;

    const res = await fetch("http://localhost:3000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      credentials: "include"
    });

    const data = await res.json();
    alert(JSON.stringify(data));

    if(data.success) window.location.href = "dashboard.html";
  });
}

// -------------------- DASHBOARD --------------------
const welcomeDiv = document.getElementById("welcome");
const logoutBtn = document.getElementById("logoutBtn");

if(welcomeDiv){
  async function loadDashboard(){
    try{
      const res = await fetch("http://localhost:3000/dashboard", {
        method: "GET",
        credentials: "include"
      });

      if(res.status === 401){
        alert("Non connecté");
        window.location.href = "login.html";
        return;
      }

      const data = await res.json();
      welcomeDiv.innerText = data.message;

    }catch(err){
      console.error(err);
    }
  }

  loadDashboard();

  logoutBtn.addEventListener("click", async () => {
    await fetch("http://localhost:3000/logout", {
      method: "POST",
      credentials: "include"
    });
    window.location.href = "login.html";
  });
}
