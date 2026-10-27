// QuickDrop front-end: calls the API, animates frames on a canvas, shows metrics,
// the live waiting queue, and a strategy comparison chart.

const COLORS = {
  street: "#ffffff", building: "#c5cfcc", free: "#1f9e6e", busy: "#d1373f",
  rest: "#f2a900", cust: "#5b5bd6", ink: "#1b2a2f",
};

const $ = (id) => document.getElementById(id);
const canvas = $("map");
const ctx = canvas.getContext("2d");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

let sim = null;          // last /api/simulate response
let frame = 0;           // current frame index
let playing = !reduceMotion;
let lastTick = 0;
let staticLayer = null;  // offscreen canvas with streets/buildings/restaurants
let compareChart = null;

// ---------- helpers ----------

function hhmm(minutes) {
  const day = Math.floor(minutes / 1440);
  const m = ((minutes % 1440) + 1440) % 1440;
  const s = `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
  return day > 0 ? `${s} +${day}d` : s;
}

function readForm() {
  const f = new FormData($("controls"));
  return {
    riders: Number(f.get("riders")),
    orders: Number(f.get("orders")),
    city_size: Number(f.get("city_size")),
    seed: Number(f.get("seed")),
    strategy: f.get("strategy"),
  };
}

async function post(url, body) {
  const res = await fetch(url, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status}).`;
    try {
      const err = await res.json();
      if (Array.isArray(err.detail)) {
        detail = err.detail.map((d) => `${d.loc.at(-1)}: ${d.msg}`).join("; ");
      }
    } catch (_) { /* keep default message */ }
    throw new Error(detail);
  }
  return res.json();
}

// ---------- canvas drawing ----------

function sizeCanvas() {
  const box = canvas.parentElement.getBoundingClientRect();
  const side = Math.floor(Math.min(box.width, box.height || box.width));
  const dpr = window.devicePixelRatio || 1;
  canvas.width = side * dpr;
  canvas.height = side * dpr;
  canvas.style.width = `${side}px`;
  canvas.style.height = `${side}px`;
  buildStaticLayer();
  draw();
}

function cellSize() {
  return sim ? canvas.width / sim.city.size : 1;
}

function buildStaticLayer() {
  if (!sim) return;
  const c = cellSize();
  staticLayer = document.createElement("canvas");
  staticLayer.width = canvas.width;
  staticLayer.height = canvas.height;
  const g = staticLayer.getContext("2d");
  g.fillStyle = COLORS.street;
  g.fillRect(0, 0, staticLayer.width, staticLayer.height);
  g.fillStyle = COLORS.building;
  for (const [x, y] of sim.city.obstacles) g.fillRect(x * c, y * c, c + 0.5, c + 0.5);
  g.fillStyle = COLORS.rest;
  for (const r of sim.restaurants) {
    const pad = c * 0.08;
    g.fillRect(r.x * c - pad, r.y * c - pad, c + 2 * pad, c + 2 * pad);
  }
}

function draw() {
  if (!sim || !staticLayer) return;
  const c = cellSize();
  const size = sim.city.size;
  const f = sim.frames[frame];
  const t = f.t;
  ctx.drawImage(staticLayer, 0, 0);

  // Customers: filled once a rider is on the way, hollow while still waiting.
  for (const o of sim.orders) {
    if (o.created_at > t || o.delivered_at <= t) continue;
    const cx = (o.x + 0.5) * c, cy = (o.y + 0.5) * c;
    ctx.beginPath();
    ctx.arc(cx, cy, c * 0.32, 0, Math.PI * 2);
    if (o.assigned_at !== null && o.assigned_at <= t) {
      ctx.fillStyle = COLORS.cust; ctx.fill();
    } else {
      ctx.strokeStyle = COLORS.cust; ctx.lineWidth = Math.max(1, c * 0.12); ctx.stroke();
    }
  }

  // Remaining route of each busy rider.
  ctx.lineWidth = Math.max(1, c * 0.18);
  ctx.strokeStyle = "rgba(209, 55, 63, 0.45)";
  ctx.lineJoin = "round";
  for (const [, , busy, oid] of f.riders) {
    if (!busy) continue;
    const o = sim.orders[oid];
    const start = Math.min(Math.max(0, t - o.assigned_at), o.path.length - 1);
    ctx.beginPath();
    for (let i = start; i < o.path.length; i++) {
      const px = (o.path[i] % size + 0.5) * c, py = (Math.floor(o.path[i] / size) + 0.5) * c;
      if (i === start) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.stroke();
  }

  // Riders on top.
  for (const [x, y, busy] of f.riders) {
    ctx.beginPath();
    ctx.arc((x + 0.5) * c, (y + 0.5) * c, Math.max(2.5, c * 0.42), 0, Math.PI * 2);
    ctx.fillStyle = busy ? COLORS.busy : COLORS.free;
    ctx.fill();
    ctx.lineWidth = Math.max(1, c * 0.1);
    ctx.strokeStyle = COLORS.street;
    ctx.stroke();
  }

  updateLive(f);
}

// ---------- side panels ----------

function updateLive(f) {
  const busy = f.riders.filter((r) => r[2]).length;
  $("clock").textContent = hhmm(f.t);
  $("liveStats").textContent =
    `${busy}/${f.riders.length} riders busy, ${f.delivered}/${sim.orders.length} delivered`;
  $("scrub").value = frame;

  const count = $("queueCount");
  count.textContent = f.waiting_count;
  count.classList.toggle("zero", f.waiting_count === 0);
  const body = $("queueBody");
  if (f.waiting.length === 0) {
    body.innerHTML = '<tr><td colspan="4" class="empty">No orders waiting.</td></tr>';
    return;
  }
  let html = f.waiting.map(([id, vip, created]) =>
    `<tr><td>#${id}</td><td>${vip ? '<span class="vip">VIP</span>' : "Normal"}</td>` +
    `<td>${hhmm(created)}</td><td>${f.t - created} min</td></tr>`).join("");
  if (f.waiting_count > f.waiting.length) {
    html += `<tr><td colspan="4" class="empty">+ ${f.waiting_count - f.waiting.length} more</td></tr>`;
  }
  body.innerHTML = html;
}

function showMetrics(m) {
  $("mDelivery").innerHTML = `${m.avg_delivery_time.toFixed(1)} <small>min</small>`;
  $("mWait").innerHTML = `${m.avg_wait_time.toFixed(1)} <small>min</small>`;
  $("mUtil").innerHTML = `${(m.utilization * 100).toFixed(1)}<small>%</small>`;
  $("mOph").textContent = m.orders_per_hour.toFixed(1);
}

// ---------- animation loop ----------

function tick(now) {
  if (sim && playing) {
    const fps = Number($("speed").value);
    if (now - lastTick >= 1000 / fps) {
      lastTick = now;
      if (frame < sim.frames.length - 1) {
        frame += 1;
        draw();
      } else {
        setPlaying(false);
      }
    }
  }
  requestAnimationFrame(tick);
}

function setPlaying(on) {
  playing = on;
  const btn = $("playBtn");
  btn.textContent = on ? "❚❚" : "▶";
  btn.setAttribute("aria-label", on ? "Pause" : "Play");
}

// ---------- actions ----------

async function runSimulation(event) {
  if (event) event.preventDefault();
  const btn = $("runBtn");
  const msg = $("formMsg");
  btn.disabled = true;
  btn.textContent = "Running…";
  msg.textContent = "";
  try {
    sim = await post("/api/simulate", readForm());
    frame = 0;
    $("scrub").max = sim.frames.length - 1;
    showMetrics(sim.metrics);
    buildStaticLayer();
    draw();
    setPlaying(!reduceMotion);
  } catch (err) {
    msg.textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Run simulation";
  }
}

async function runCompare() {
  const btn = $("compareBtn");
  btn.disabled = true;
  btn.textContent = "Comparing…";
  try {
    const data = await post("/api/compare", readForm());
    renderCompare(data);
  } catch (err) {
    $("formMsg").textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Compare strategies";
  }
}

function renderCompare(data) {
  const g = data.greedy, n = data.naive;
  const labels = ["Avg delivery (min)", "P90 delivery (min)", "Avg wait (min)"];
  const keys = ["avg_delivery_time", "p90_delivery_time", "avg_wait_time"];
  const datasets = [
    { label: "Nearest rider (heap)", data: keys.map((k) => g[k]), backgroundColor: COLORS.free },
    { label: "First free rider (scan)", data: keys.map((k) => n[k]), backgroundColor: COLORS.busy },
  ];
  if (window.Chart) {
    if (compareChart) compareChart.destroy();
    compareChart = new Chart($("compareChart"), {
      type: "bar",
      data: { labels, datasets },
      options: {
        responsive: true, maintainAspectRatio: false,
        animation: reduceMotion ? false : { duration: 500 },
        scales: { y: { beginAtZero: true, title: { display: true, text: "minutes" } } },
        plugins: { legend: { position: "bottom" } },
      },
    });
  }

  const rows = [
    ["Avg delivery", g.avg_delivery_time, n.avg_delivery_time, " min", true],
    ["Avg wait", g.avg_wait_time, n.avg_wait_time, " min", true],
    ["Utilization", g.utilization * 100, n.utilization * 100, "%", null],  // neither is "better"
    ["Orders per hour", g.orders_per_hour, n.orders_per_hour, "", false],
    ["Runtime", g.runtime_ms, n.runtime_ms, " ms", true],
  ];
  const table = $("compareTable");
  table.querySelector("tbody").innerHTML = rows.map(([name, a, b, unit, lowerWins]) => {
    const aWins = lowerWins !== null && (lowerWins ? a < b : a > b);
    const bWins = lowerWins !== null && (lowerWins ? b < a : b > a);
    return `<tr><td>${name}</td><td class="${aWins ? "win" : ""}">${a.toFixed(1)}${unit}</td>` +
           `<td class="${bWins ? "win" : ""}">${b.toFixed(1)}${unit}</td></tr>`;
  }).join("");
  table.hidden = false;
}

// ---------- wiring ----------

$("controls").addEventListener("submit", runSimulation);
$("compareBtn").addEventListener("click", runCompare);
$("playBtn").addEventListener("click", () => {
  if (!sim) return;
  if (!playing && frame >= sim.frames.length - 1) frame = 0;
  setPlaying(!playing);
});
$("scrub").addEventListener("input", (e) => {
  frame = Number(e.target.value);
  draw();
});
window.addEventListener("resize", sizeCanvas);

sizeCanvas();
requestAnimationFrame(tick);
runSimulation();
