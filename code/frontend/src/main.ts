import type { PredictResponse, Candidate } from "./types";
import { getHealth, predict } from "./api";

let loading = false;

const form  = document.getElementById("form")  as HTMLFormElement;
const inputEl = document.getElementById("description") as HTMLTextAreaElement;
const submitBtn = document.getElementById("submit-btn") as HTMLButtonElement;
const resultSection = document.getElementById("result-section") as HTMLElement;
const loadingEl = document.getElementById("loading") as HTMLElement;
const errorEl = document.getElementById("error-box") as HTMLElement;
const statusEl = document.getElementById("status") as HTMLElement;

getHealth()
  .then(() => { 
    statusEl.textContent = "Online 🟢"; 
    statusEl.style.color = "#4ade80"; 
  })
  .catch(() => { 
    // If it fails, say Offline!
    statusEl.textContent = "Offline 🔴"; 
    statusEl.style.color = "#f87171"; 
  });

inputEl.addEventListener("input",()=>{
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 200) + "px";
});

document.querySelectorAll<HTMLButtonElement>(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    inputEl.value = chip.dataset.text ?? "";
    inputEl.dispatchEvent(new Event("input"));
    inputEl.focus();
  });
});

form.addEventListener("submit", async (e) =>{
  e.preventDefault();
  const description = inputEl.value.trim()
  if(!description || loading) return;

  setLoading(true);
  resultSection.classList.add("hidden");
  errorEl.classList.add("hidden");

  try{
    const result = await predict(description);
    showResult(result);
  } catch (err) {
    errorEl.textContent = `Error: ${(err as Error).message}`;
    errorEl.classList.remove("hidden");
  } finally{
    setLoading(false);
  }
});


function showResult(r: PredictResponse):void{
  (document.getElementById("result-hscode")    as HTMLElement).textContent = r.hscode;
  (document.getElementById("result-description")    as HTMLElement).textContent = r.description;
  (document.getElementById("result-reason")    as HTMLElement).textContent = r.reason;
  (document.getElementById("result-latency")    as HTMLElement).textContent = `${r.latency} ms`;
  

  const tbody = document.getElementById("candidates-body") as HTMLElement;
  tbody.innerHTML = r.candidates.map((c: Candidate, i: number) => `
    <tr class="${c.hscode === r.hscode ? "highlight" : ""}">
      <td>${i + 1}</td>
      <td><code>${c.hscode}</code></td>
      <td>${c.description}</td>
      <td>${c.section}</td>
      <td>${c.score.toFixed(4)}</td>
    </tr>
  `).join("");

  resultSection.classList.remove("hidden");
  resultSection.scrollIntoView({behavior: "smooth"});
}

function setLoading(state: boolean): void{
  loading = state;
  submitBtn.disabled = state;
  loadingEl.classList.toggle("hidden",!state)
  submitBtn.textContent = state ? "Analyzing..." : "Generate HS Code"
}