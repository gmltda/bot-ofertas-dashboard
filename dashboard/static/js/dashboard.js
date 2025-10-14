document.getElementById("startBtn").onclick = async () => {
  const mode = document.getElementById("mode").value;
  const keyword = document.getElementById("keyword").value;
  const res = await fetch("/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, keyword }),
  });
  const data = await res.json();
  alert(data.msg);
  location.reload();
};

document.getElementById("stopBtn").onclick = async () => {
  const res = await fetch("/stop", { method: "POST" });
  const data = await res.json();
  alert(data.msg);
  location.reload();
};