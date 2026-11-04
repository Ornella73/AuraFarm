"""HTML views for the AuraFarm PWA Dashboard and interactive 2G Feature Phone Simulator."""

def render_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="fr" class="h-full bg-slate-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraFarm — Tableau de Bord Agro-Climatique Togo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .badge-semer { background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; }
        .badge-attendre { background-color: #fef9c3; color: #854d0e; border: 1px solid #fde047; }
        .badge-risque { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
        .badge-stale { background-color: #ffedd5; color: #9a3412; border: 1px solid #fdba74; }
    </style>
</head>
<body class="h-full flex flex-col font-sans text-slate-800">

    <!-- Top Navigation Bar -->
    <header class="bg-emerald-800 text-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-emerald-700 flex items-center justify-center text-emerald-200 text-xl font-bold border border-emerald-600">
                    🌾
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h1 class="text-xl font-bold tracking-tight">AuraFarm</h1>
                        <span class="text-xs bg-emerald-900 text-emerald-200 px-2 py-0.5 rounded-full font-medium">Togo Pilot 2026</span>
                    </div>
                    <p class="text-xs text-emerald-200 font-light">Cerveau connecté, dernier kilomètre sans internet</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="/ussd-simulator" target="_blank" class="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold px-4 py-2 rounded-lg text-sm shadow transition">
                    <i class="fa-solid fa-mobile-screen"></i>
                    <span>Simulateur Téléphone 2G</span>
                </a>
                <button onclick="runPipeline('optimal_onset')" class="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-600 text-white text-xs px-3 py-2 rounded-lg border border-emerald-600 transition">
                    <i class="fa-solid fa-arrows-rotate"></i>
                    <span>Actualiser Données</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Main Content Grid -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">

        <!-- Banner Alert & Simulation Toolbar -->
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-emerald-100 text-emerald-800">
                    <i class="fa-solid fa-satellite-dish text-lg"></i>
                </div>
                <div>
                    <h2 class="text-sm font-semibold text-slate-900">Sources Agro-Météo Connectées (CHIRPS v3, ECMWF & Pluviomètres)</h2>
                    <p class="text-xs text-slate-500">Supervision automatique de la fraîcheur des données (< 48h) — Respect de la loi togolaise 2019-014</p>
                </div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
                <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Simulations jury :</span>
                <button onclick="runPipeline('optimal_onset')" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded border border-slate-300 font-medium transition">
                    🟢 Saison Favorable
                </button>
                <button onclick="runPipeline('false_start')" class="text-xs bg-red-50 hover:bg-red-100 text-red-700 px-3 py-1.5 rounded border border-red-200 font-medium transition">
                    🔴 Faux Départ (9j secs)
                </button>
                <button onclick="runPipeline('insufficient_rain')" class="text-xs bg-amber-50 hover:bg-amber-100 text-amber-700 px-3 py-1.5 rounded border border-amber-200 font-medium transition">
                    🟡 Pluie Insuffisante
                </button>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="border-b border-slate-200 flex gap-6 text-sm font-medium">
            <button onclick="switchTab('tab-villages')" id="btn-tab-villages" class="pb-3 border-b-2 border-emerald-600 text-emerald-800 font-semibold flex items-center gap-2">
                <i class="fa-solid fa-map-location-dot"></i> Fiches Villages & Alertes
            </button>
            <button onclick="switchTab('tab-radio')" id="btn-tab-radio" class="pb-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-2">
                <i class="fa-solid fa-radio"></i> Bulletin Radio Communautaire
            </button>
            <button onclick="switchTab('tab-backtest')" id="btn-tab-backtest" class="pb-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-2">
                <i class="fa-solid fa-chart-line"></i> Validation & Backtest
            </button>
            <button onclick="switchTab('tab-observations')" id="btn-tab-observations" class="pb-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-2">
                <i class="fa-solid fa-cloud-rain"></i> Relevés Pluviomètres
            </button>
        </div>

        <!-- TAB 1: VILLAGES & ADVICE CARDS -->
        <section id="tab-villages" class="flex flex-col gap-4">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="cards-container">
                <!-- Injected via JavaScript -->
                <div class="col-span-full py-12 text-center text-slate-400">
                    <i class="fa-solid fa-spinner fa-spin text-2xl"></i>
                    <p class="mt-2 text-sm">Chargement des fiches pré-calculées...</p>
                </div>
            </div>
        </section>

        <!-- TAB 2: RADIO BROADCAST SCRIPT -->
        <section id="tab-radio" class="hidden bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-6">
            <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
                <div>
                    <h3 class="text-base font-bold text-slate-900">Générateur de Bulletin Radio Communautaire</h3>
                    <p class="text-xs text-slate-500">Diffusion hebdomadaire pour les producteurs analphabètes ou sans téléphone</p>
                </div>
                <div class="flex items-center gap-2">
                    <select id="radio-region" onchange="loadRadioBulletin()" class="text-xs border border-slate-300 rounded px-3 py-1.5 bg-slate-50 font-medium">
                        <option value="Maritime">Région Maritime (Éwé/Français)</option>
                        <option value="Plateaux">Région Plateaux (Éwé/Français)</option>
                        <option value="Centrale">Région Centrale (Kabiyè/Français)</option>
                        <option value="Kara">Région Kara (Kabiyè/Français)</option>
                        <option value="Savanes">Région Savanes (Kabiyè/Français)</option>
                    </select>
                    <button onclick="window.print()" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded border border-slate-300 font-medium">
                        <i class="fa-solid fa-print"></i> Imprimer
                    </button>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="flex flex-col gap-2">
                    <span class="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                        <i class="fa-solid fa-language"></i> Script Français (Présentateur)
                    </span>
                    <pre id="radio-script-fr" class="p-4 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono whitespace-pre-wrap leading-relaxed text-slate-800 h-96 overflow-y-auto">Chargement...</pre>
                </div>
                <div class="flex flex-col gap-2">
                    <span class="text-xs font-bold text-emerald-700 uppercase tracking-wider flex items-center gap-1.5">
                        <i class="fa-solid fa-comments"></i> Script Langue Locale (Éwé / Kabiyè)
                    </span>
                    <pre id="radio-script-local" class="p-4 bg-emerald-50 rounded-lg border border-emerald-200 text-xs font-mono whitespace-pre-wrap leading-relaxed text-emerald-950 h-96 overflow-y-auto">Chargement...</pre>
                </div>
            </div>
        </section>

        <!-- TAB 3: BACKTESTING & BENCHMARK -->
        <section id="tab-backtest" class="hidden bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-6">
            <div class="flex items-center justify-between border-b border-slate-100 pb-4">
                <div>
                    <h3 class="text-base font-bold text-slate-900">Validation & Performance Historique (1991–2025)</h3>
                    <p class="text-xs text-slate-500">Benchmark automatique sur les régimes pluviométriques bimodal et unimodal</p>
                </div>
                <button onclick="loadBacktest()" class="text-xs bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-3 py-1.5 rounded">
                    Relancer le Benchmark
                </button>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4" id="backtest-metrics">
                <div class="p-4 bg-slate-50 rounded-lg border border-slate-200 text-center">
                    <div class="text-2xl font-bold text-emerald-700" id="metric-accuracy">--</div>
                    <div class="text-xs text-slate-500 mt-1">Précision globale</div>
                </div>
                <div class="p-4 bg-slate-50 rounded-lg border border-slate-200 text-center">
                    <div class="text-2xl font-bold text-emerald-700" id="metric-safety">--</div>
                    <div class="text-xs text-slate-500 mt-1">Faux départs évités</div>
                </div>
                <div class="p-4 bg-slate-50 rounded-lg border border-slate-200 text-center">
                    <div class="text-2xl font-bold text-emerald-700" id="metric-tests">--</div>
                    <div class="text-xs text-slate-500 mt-1">Scénarios validés</div>
                </div>
                <div class="p-4 bg-slate-50 rounded-lg border border-slate-200 text-center">
                    <div class="text-2xl font-bold text-emerald-700" id="metric-errors">0</div>
                    <div class="text-xs text-slate-500 mt-1">Erreurs critiques de semis</div>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-xs text-left border-collapse">
                    <thead>
                        <tr class="bg-slate-100 border-b border-slate-200 text-slate-700">
                            <th class="p-2.5 font-semibold">Village sentinelle</th>
                            <th class="p-2.5 font-semibold">Scénario testé</th>
                            <th class="p-2.5 font-semibold">Alerte émise</th>
                            <th class="p-2.5 font-semibold">Niveau confiance</th>
                            <th class="p-2.5 font-semibold text-center">Statut</th>
                        </tr>
                    </thead>
                    <tbody id="backtest-table-body">
                        <!-- Populated via JS -->
                    </tbody>
                </table>
            </div>
        </section>

        <!-- TAB 4: FIELD RAIN OBSERVATIONS -->
        <section id="tab-observations" class="hidden bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-6">
            <div>
                <h3 class="text-base font-bold text-slate-900">Remontées Pluviométriques Paysannes</h3>
                <p class="text-xs text-slate-500">Données déclarées via USSD (*384*228# option 3) par les producteurs et agents d'encadrement</p>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-xs text-left border-collapse">
                    <thead>
                        <tr class="bg-slate-100 border-b border-slate-200 text-slate-700">
                            <th class="p-2.5 font-semibold">Date relevé</th>
                            <th class="p-2.5 font-semibold">Village</th>
                            <th class="p-2.5 font-semibold">Pluie relevée</th>
                            <th class="p-2.5 font-semibold">Source</th>
                            <th class="p-2.5 font-semibold">Horodatage</th>
                        </tr>
                    </thead>
                    <tbody id="obs-table-body">
                        <tr><td colspan="5" class="p-4 text-center text-slate-400">Aucun relevé récent enregistré.</td></tr>
                    </tbody>
                </table>
            </div>
        </section>

    </main>

    <footer class="bg-white border-t border-slate-200 py-3 text-center text-xs text-slate-500">
        AuraFarm &bull; Hackathon Climat & Innovation 2026 (Togolaises In Science) &bull; Partenaires : ITRA, ICAT, ANAMET Togo
    </footer>

    <script>
        let allSheets = [];

        async function loadSheets() {
            try {
                const res = await fetch('/api/sheets');
                allSheets = await res.json();
                renderCards(allSheets);
            } catch (e) {
                console.error(e);
            }
        }

        function renderCards(sheets) {
            const container = document.getElementById('cards-container');
            if (!sheets.length) {
                container.innerHTML = `<div class="col-span-full py-8 text-center text-slate-400">Aucune fiche pré-calculée. Cliquez sur "Actualiser Données".</div>`;
                return;
            }

            container.innerHTML = sheets.map(s => {
                let badgeClass = 'badge-attendre';
                let icon = 'fa-hourglass-half';
                let statusLabel = s.alert_status;

                if (s.alert_status === 'SEMER') {
                    badgeClass = 'badge-semer';
                    icon = 'fa-circle-check';
                    statusLabel = 'SEMER DÈS MAINTENANT';
                } else if (s.alert_status === 'RISQUE') {
                    badgeClass = 'badge-risque';
                    icon = 'fa-triangle-exclamation';
                    statusLabel = 'RISQUE FAUX DÉPART';
                } else if (s.alert_status === 'ATTENDRE_CONSULTER_AGENT') {
                    badgeClass = 'badge-stale';
                    icon = 'fa-shield-halved';
                    statusLabel = 'DONNÉES EN ATTENTE &bull; CONSULTER AGENT';
                }

                return `
                <div class="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow transition flex flex-col justify-between gap-4">
                    <div>
                        <div class="flex items-center justify-between gap-2 mb-2">
                            <div>
                                <h4 class="font-bold text-slate-900 text-sm">${s.village_name}</h4>
                                <span class="text-xs text-slate-400 font-mono">${s.village_id} &bull; ${s.crop_type.toUpperCase()}</span>
                            </div>
                            <span class="text-[11px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider ${badgeClass} flex items-center gap-1">
                                <i class="fa-solid ${icon}"></i> ${statusLabel}
                            </span>
                        </div>

                        <div class="bg-slate-50 p-2.5 rounded-lg border border-slate-100 my-3 text-xs flex flex-col gap-1">
                            <div class="flex justify-between text-slate-600">
                                <span>Variété homologuée ITRA :</span>
                                <strong class="text-emerald-800">${s.recommended_variety_name}</strong>
                            </div>
                            <div class="flex justify-between text-slate-600">
                                <span>Pluie 3 derniers jours :</span>
                                <strong>${s.rain_last_3days_mm} mm</strong>
                            </div>
                            <div class="flex justify-between text-slate-600">
                                <span>Relais prévision 7j :</span>
                                <strong>${s.rain_forecast_7days_mm} mm</strong>
                            </div>
                            <div class="flex justify-between text-slate-600">
                                <span>Risque poche de sécheresse :</span>
                                <strong class="${s.dry_spell_risk_days > 7 ? 'text-red-600' : 'text-slate-800'}">${s.dry_spell_risk_days} jours max</strong>
                            </div>
                            <div class="flex justify-between text-slate-600">
                                <span>Indice de confiance :</span>
                                <span class="font-semibold text-slate-700">${s.confidence}</span>
                            </div>
                        </div>

                        <div class="text-xs text-slate-700 italic border-l-2 border-emerald-500 pl-2 py-0.5">
                            "${s.advice_fr}"
                        </div>
                    </div>

                    <div class="border-t border-slate-100 pt-3 flex items-center justify-between text-[11px] text-slate-400">
                        <span>Maj: ${s.calculation_date}</span>
                        <a href="/ussd-simulator" target="_blank" class="text-emerald-700 hover:text-emerald-900 font-semibold flex items-center gap-1">
                            Tester sur 2G <i class="fa-solid fa-arrow-right"></i>
                        </a>
                    </div>
                </div>
                `;
            }).join('');
        }

        async function runPipeline(scenario) {
            try {
                const res = await fetch(`/api/pipeline/run?scenario=${scenario}`, { method: 'POST' });
                const data = await res.json();
                loadSheets();
                loadRadioBulletin();
            } catch (e) {
                alert('Erreur lors du calcul');
            }
        }

        async function loadRadioBulletin() {
            const reg = document.getElementById('radio-region').value;
            const res = await fetch(`/api/bulletin/${reg}`);
            const data = await res.json();
            document.getElementById('radio-script-fr').textContent = data.script_fr;
            document.getElementById('radio-script-local').textContent = data.script_local;
        }

        async function loadBacktest() {
            const res = await fetch('/api/backtest');
            const data = await res.json();
            document.getElementById('metric-accuracy').textContent = data.accuracy_pct + '%';
            document.getElementById('metric-safety').textContent = data.false_start_safety_rate_pct + '%';
            document.getElementById('metric-tests').textContent = data.total_tests;
            document.getElementById('metric-errors').textContent = data.critical_errors;

            const body = document.getElementById('backtest-table-body');
            body.innerHTML = data.scenarios.map(sc => `
                <tr class="border-b border-slate-100 hover:bg-slate-50">
                    <td class="p-2.5 font-medium">${sc.village}</td>
                    <td class="p-2.5 text-slate-600 font-mono">${sc.scenario}</td>
                    <td class="p-2.5 font-semibold ${sc.alert === 'SEMER' ? 'text-green-700' : (sc.alert === 'RISQUE' ? 'text-red-700' : 'text-amber-700')}">${sc.alert}</td>
                    <td class="p-2.5 text-slate-600">${sc.confidence}</td>
                    <td class="p-2.5 text-center">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${sc.success ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}">
                            ${sc.success ? 'SUCCÈS' : 'ÉCHEC'}
                        </span>
                    </td>
                </tr>
            `).join('');
        }

        function switchTab(tabId) {
            ['tab-villages', 'tab-radio', 'tab-backtest', 'tab-observations'].forEach(id => {
                document.getElementById(id).classList.add('hidden');
            });
            document.getElementById(tabId).classList.remove('hidden');

            ['btn-tab-villages', 'btn-tab-radio', 'btn-tab-backtest', 'btn-tab-observations'].forEach(btnId => {
                document.getElementById(btnId).className = 'pb-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-2';
            });
            document.getElementById('btn-' + tabId).className = 'pb-3 border-b-2 border-emerald-600 text-emerald-800 font-semibold flex items-center gap-2';

            if (tabId === 'tab-radio') loadRadioBulletin();
            if (tabId === 'tab-backtest') loadBacktest();
        }

        // Init
        loadSheets();
    </script>
</body>
</html>"""

def render_simulator_html() -> str:
    return """<!DOCTYPE html>
<html lang="fr" class="h-full bg-slate-900">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraFarm — Simulateur Téléphone 2G (USSD & Voix)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .lcd-screen {
            background-color: #9ea771;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
            font-family: 'Courier New', Courier, monospace;
            color: #1a2208;
            text-shadow: 0 1px 1px rgba(255,255,255,0.2);
        }
        .phone-body {
            background: linear-gradient(145deg, #1e293b, #0f172a);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
        }
        .key-btn {
            background: linear-gradient(145deg, #334155, #1e293b);
            box-shadow: 0 3px 0 #0f172a, 0 4px 6px rgba(0,0,0,0.3);
        }
        .key-btn:active {
            transform: translateY(2px);
            box-shadow: 0 1px 0 #0f172a, 0 2px 4px rgba(0,0,0,0.3);
        }
    </style>
</head>
<body class="h-full flex items-center justify-center p-4">

    <div class="max-w-4xl w-full flex flex-col md:flex-row items-center justify-center gap-8">

        <!-- 2G Feature Phone Mockup -->
        <div class="w-80 phone-body rounded-[40px] p-5 border-4 border-slate-700 flex flex-col items-center select-none">
            
            <!-- Speaker grill -->
            <div class="w-16 h-1.5 bg-slate-700 rounded-full mb-4"></div>

            <!-- Brand -->
            <div class="text-[10px] tracking-widest text-slate-500 font-bold uppercase mb-2">AURAFARM 2G</div>

            <!-- Monochrome LCD Screen -->
            <div class="w-full h-48 lcd-screen rounded-lg p-3 flex flex-col justify-between border-2 border-slate-800">
                <div class="flex justify-between items-center text-[10px] border-b border-[#7d8655] pb-1 font-bold">
                    <span>YAS TOGO 2G</span>
                    <span id="char-count">0/160</span>
                </div>
                <div id="screen-text" class="text-xs font-bold leading-tight whitespace-pre-wrap flex-1 my-2 overflow-y-auto">Composez *384*228# pour démarrer le service USSD AuraFarm</div>
                <div class="flex justify-between items-center text-[10px] border-t border-[#7d8655] pt-1">
                    <span id="action-left">ENVOYER</span>
                    <span id="action-right">EFFACER</span>
                </div>
            </div>

            <!-- Keypad -->
            <div class="w-full mt-5 flex flex-col gap-2">
                <!-- Action Buttons: Green Call, Nav, Red End -->
                <div class="grid grid-cols-3 gap-2 mb-2">
                    <button onclick="dialUssd()" class="h-10 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center shadow">
                        <i class="fa-solid fa-phone"></i>
                    </button>
                    <button onclick="triggerBip()" title="Bip (Appel manqué gratuit)" class="h-10 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-[10px] flex flex-col items-center justify-center shadow">
                        <span>BIP</span>
                        <span class="text-[8px] opacity-80">Rappel</span>
                    </button>
                    <button onclick="hangUp()" class="h-10 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs flex items-center justify-center shadow">
                        <i class="fa-solid fa-phone-slash"></i>
                    </button>
                </div>

                <!-- Input Display -->
                <div class="w-full bg-slate-800 text-emerald-400 font-mono text-center text-sm py-1.5 rounded-lg border border-slate-700 tracking-wider h-8 flex items-center justify-center">
                    <span id="keypad-input">*384*228#</span>
                </div>

                <!-- 12-Keys Numpad -->
                <div class="grid grid-cols-3 gap-2 mt-1">
                    <button onclick="pressKey('1')" class="key-btn h-11 rounded-lg text-white font-bold flex flex-col items-center justify-center">
                        <span class="text-sm">1</span><span class="text-[8px] text-slate-400">.</span>
                    </button>
                    <button onclick="pressKey('2')" class="key-btn h-11 rounded-lg text-white font-bold flex flex-col items-center justify-center">
                        <span class="text-sm">2</span><span class="text-[8px] text-slate-400">ABC</span>
                    </button>
                    <button onclick="pressKey('3')" class="key-btn h-11 rounded-lg text-white font-bold flex flex-col items-center justify-center">
                        <span class="text-sm">3</span><span class="text-[8px] text-slate-400">DEF</span>
                    </button>

                    <button onclick="pressKey('4')" class="key-btn h-11 rounded-lg text-white font-bold flex flex-col items-center justify-center">
                        <span class="text-sm">4</span><span class="text-[8px] text-slate-400">GHI</span>
                    </button>
                    <button onclick="pressKey('5')" class="key-btn h-11 rounded-lg text-white font-bold flex flex-col items-center justify-center">
                        <span class="text-sm">5</span><span class="text-[8px] text-slate-400">JKL</span>
                    </button>
                    <button onclick="pressKey('6')" class="key-btn h-11 rounded-lg text-white font-bold flex flex-col items-center justify-center">
                        <span class="text-sm">6</span><span class="text-[8px] text-slate-400">MNO</span>
                    </button>

                    <button onclick="pressKey('7')" class="key-btn h-11 rounded-lg text-white font-bold flex flex-col items-center justify-center">
                        <span class="text-sm">7</span><span class="text-[8px] text-slate-400">PQRS</span>
                    </button>
                    <button onclick="pressKey('8')" class="key-btn h-11 rounded-lg text-white font-bold flex flex-col items-center justify-center">
                        <span class="text-sm">8</span><span class="text-[8px] text-slate-400">TUV</span>
                    </button>
                    <button onclick="pressKey('9')" class="key-btn h-11 rounded-lg text-white font-bold flex flex-col items-center justify-center">
                        <span class="text-sm">9</span><span class="text-[8px] text-slate-400">WXYZ</span>
                    </button>

                    <button onclick="pressKey('*')" class="key-btn h-11 rounded-lg text-white font-bold text-sm flex items-center justify-center">*</button>
                    <button onclick="pressKey('0')" class="key-btn h-11 rounded-lg text-white font-bold flex flex-col items-center justify-center">
                        <span class="text-sm">0</span><span class="text-[8px] text-slate-400">+</span>
                    </button>
                    <button onclick="pressKey('#')" class="key-btn h-11 rounded-lg text-white font-bold text-sm flex items-center justify-center">#</button>
                </div>
            </div>
        </div>

        <!-- Instructions & Voice Call Player Column -->
        <div class="flex-1 max-w-md flex flex-col gap-4 text-white">
            <div class="bg-slate-800 p-5 rounded-2xl border border-slate-700">
                <h3 class="text-base font-bold text-emerald-400 flex items-center gap-2 mb-2">
                    <i class="fa-solid fa-signal"></i> Réalité Terrain Togo
                </h3>
                <p class="text-xs text-slate-300 leading-relaxed">
                    Ce simulateur reproduit fidèlement les contraintes d'un producteur togolais sur téléphone basique (Nokia/Itel 2G) sans connexion internet.
                </p>
                <div class="mt-3 flex flex-col gap-2 text-xs">
                    <div class="flex items-center gap-2">
                        <span class="w-6 h-6 rounded bg-emerald-900 text-emerald-300 flex items-center justify-center font-bold">1</span>
                        <span>Composez <strong>*384*228#</strong> puis appuyez sur la touche verte.</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="w-6 h-6 rounded bg-emerald-900 text-emerald-300 flex items-center justify-center font-bold">2</span>
                        <span>Choisissez votre langue (1: Éwé, 2: Kabiyè, 3: Mina, 4: Français).</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="w-6 h-6 rounded bg-emerald-900 text-emerald-300 flex items-center justify-center font-bold">3</span>
                        <span>Consultez l'alerte semis (&lt; 160 caractères) ou signalez la pluie tombée.</span>
                    </div>
                </div>
            </div>

            <!-- Voice IVR Playback Box -->
            <div class="bg-slate-800 p-5 rounded-2xl border border-slate-700 flex flex-col gap-3">
                <div class="flex items-center justify-between">
                    <h4 class="text-sm font-bold text-amber-400 flex items-center gap-2">
                        <i class="fa-solid fa-volume-high"></i> Démo Appel Vocal Sortant (IVR)
                    </h4>
                    <span class="text-[10px] bg-slate-700 text-slate-300 px-2 py-0.5 rounded">30–45s</span>
                </div>
                <p class="text-xs text-slate-300">
                    Déclenchez un appel vocal sortant simulé (comme après un "bip" gratuit) et écoutez la réponse vocale dans la langue choisie :
                </p>
                <div class="flex gap-2">
                    <select id="voice-lang" class="bg-slate-900 border border-slate-700 text-xs rounded px-3 py-1.5 flex-1">
                        <option value="francais">Français</option>
                        <option value="ewe">Éwé (Eʋegbe)</option>
                        <option value="kabiye">Kabiyè (Kabɩyɛ)</option>
                    </select>
                    <button onclick="playVoiceDemo()" class="bg-amber-500 hover:bg-amber-600 text-slate-900 font-bold px-3 py-1.5 rounded text-xs transition flex items-center gap-1.5">
                        <i class="fa-solid fa-play"></i> Écouter
                    </button>
                </div>
                <div id="voice-transcript" class="p-3 bg-slate-900 rounded-lg text-xs font-mono text-emerald-300 border border-slate-700 min-h-[60px] italic">
                    Cliquez sur "Écouter" pour simuler l'appel vocal reçu par le producteur.
                </div>
            </div>

            <div class="text-center">
                <a href="/dashboard" class="text-xs text-emerald-400 hover:underline">
                    &larr; Revenir au Tableau de Bord
                </a>
            </div>
        </div>

    </div>

    <script>
        let currentSessionId = 'sim_' + Math.floor(Math.random() * 1000000);
        let currentInputHistory = [];
        let inSession = false;

        function updateScreen(text, isTerminal) {
            document.getElementById('screen-text').textContent = text;
            document.getElementById('char-count').textContent = text.length + '/160';
            if (isTerminal) {
                inSession = false;
                currentInputHistory = [];
                document.getElementById('keypad-input').textContent = '*384*228#';
            }
        }

        function pressKey(key) {
            const el = document.getElementById('keypad-input');
            if (el.textContent === '*384*228#' && inSession) {
                el.textContent = key;
            } else if (el.textContent === '*384*228#' && !inSession) {
                // start typing custom code
                el.textContent = key;
            } else {
                el.textContent += key;
            }
        }

        function hangUp() {
            inSession = false;
            currentInputHistory = [];
            currentSessionId = 'sim_' + Math.floor(Math.random() * 1000000);
            document.getElementById('keypad-input').textContent = '*384*228#';
            updateScreen("Session terminée.\\nComposez *384*228# pour démarrer le service.", true);
        }

        async function dialUssd() {
            const inputEl = document.getElementById('keypad-input');
            const typed = inputEl.textContent.trim();

            if (!inSession) {
                // Initial dial of *384*228#
                inSession = true;
                currentInputHistory = [];
                currentSessionId = 'sim_' + Math.floor(Math.random() * 1000000);
                inputEl.textContent = '';
                await sendUssdHop('');
            } else {
                // Submit reply in active session
                if (typed) {
                    currentInputHistory.push(typed);
                    inputEl.textContent = '';
                    const fullText = currentInputHistory.join('*');
                    await sendUssdHop(fullText);
                }
            }
        }

        async function sendUssdHop(text) {
            const formData = new FormData();
            formData.append('sessionId', currentSessionId);
            formData.append('phoneNumber', '+22890123456');
            formData.append('text', text);

            try {
                const res = await fetch('/api/ussd', { method: 'POST', body: formData });
                const raw = await res.text();
                const isTerminal = raw.startsWith('END ');
                const content = raw.replace(/^(CON |END )/, '');
                updateScreen(content, isTerminal);
            } catch (e) {
                updateScreen("Erreur réseau USSD.", true);
            }
        }

        async function triggerBip() {
            const formData = new FormData();
            formData.append('phoneNumber', '+22890123456');
            const res = await fetch('/api/channels/missed-call', { method: 'POST', body: formData });
            const data = await res.json();
            updateScreen("BIP REÇU !\\nAppel manqué détecté.\\nRappel vocal gratuit programmé vers " + data.phone_masked, true);
        }

        async function playVoiceDemo() {
            const lang = document.getElementById('voice-lang').value;
            const res = await fetch(`/api/sheet/TG_MAR_ZIO_01/mais`);
            const sheet = await res.json();
            
            let transcript = sheet.advice_fr;
            if (lang === 'ewe') {
                transcript = sheet.advice_local;
            }
            
            document.getElementById('voice-transcript').textContent = '📞 [Appel vocal 30s] : "' + transcript + '"';

            // Use browser speech synthesis if available
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(transcript);
                utterance.lang = lang === 'francais' ? 'fr-FR' : 'fr-FR';
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(utterance);
            }
        }
    </script>
</body>
</html>"""
