const PROD_URL = "https://bot-oferta.vagalimitada.com";
const DEV_URL = "http://127.0.0.1:10000";
const BACKEND_URL = "https://bot-ofertas-dashboard.onrender.com";

async function updateStatus() {
  try {
    const res = await fetch(`${BACKEND_URL}/status`);
    const data = await res.json();
    document.getElementById("status").innerText = data.status || "-";
    document.getElementById("count").innerText = data.mined_today ?? 0;
  } catch (e) {
    console.warn("Falha ao obter status:", e);
  }
}

async function updateFavoritos() {
  try {
    const res = await fetch(`${BACKEND_URL}/favoritos`);
    const data = await res.json();
    const cont = document.getElementById("favoritos");
    cont.innerHTML = "";
    const favs = Array.isArray(data.favoritos) ? data.favoritos : [];
    if (favs.length === 0) {
      cont.innerHTML = '<p class="muted">Nenhum favorito salvo ainda.</p>';
      return;
    }
    favs.forEach(fav => {
      const card = document.createElement("div");
      card.className = "card";
      card.innerHTML = `<strong>${fav.keyword}</strong> — ${fav.page_name}<br>
        <a href="${fav.ad_library_link}" target="_blank">Ver anúncio</a>`;
      cont.appendChild(card);
    });
  } catch (e) {
    console.warn("Falha ao obter favoritos:", e);
  }
}

document.getElementById("startBtn").onclick = async () => {
  const mode = document.getElementById("mode").value;
  const keyword = document.getElementById("keyword").value;
  try {
    const res = await fetch(`${BACKEND_URL}/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, keyword }),
    });
    const data = await res.json();
    alert(data.msg);
    updateStatus();
  } catch (e) {
    alert("Falha ao iniciar mineração");
  }
};

document.getElementById("stopBtn").onclick = async () => {
  try {
    const res = await fetch(`${BACKEND_URL}/stop`, { method: "POST" });
    const data = await res.json();
    alert(data.msg);
    updateStatus();
  } catch (e) {
    alert("Falha ao parar processo");
  }
};
