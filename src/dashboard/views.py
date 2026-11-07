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
    <link rel="stylesheet" href="/static/fiche.css">
    <script src="/static/auracharts.js"></script>
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
                        <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-500/40">
                            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> LIVE
                        </span>
                    </div>
                    <p class="text-xs text-emerald-200 font-light">Cerveau connecté, dernier kilomètre sans internet</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="/zones-overview" class="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-600 text-white font-medium px-3 py-2 rounded-lg text-xs border border-emerald-600 transition">
                    <i class="fa-solid fa-earth-africa"></i>
                    <span>Zones & Météo (E2)</span>
                </a>
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
                    🟢 Favorable
                </button>
                <button onclick="runPipeline('false_start')" class="text-xs bg-red-50 hover:bg-red-100 text-red-700 px-3 py-1.5 rounded border border-red-200 font-medium transition">
                    🔴 Faux Départ (9j secs)
                </button>
                <button onclick="simulateStaleData()" class="text-xs bg-red-100 hover:bg-red-200 text-red-900 px-3 py-1.5 rounded border border-red-300 font-bold transition">
                    ⛔ Périmée J-10 (Sécurité)
                </button>
                <button onclick="resetFilters()" class="text-xs bg-white hover:bg-slate-100 text-slate-700 px-3 py-1.5 rounded border border-slate-300 font-medium transition">
                    🔄 Réinitialiser
                </button>
            </div>
        </div>

        <!-- Live Stream Activity Bar (Step E5) -->
        <div class="bg-slate-900 text-white p-3.5 rounded-xl border border-slate-800 shadow flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
            <div class="flex items-center gap-2.5">
                <span class="relative flex h-3 w-3">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <span class="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                    <i class="fa-solid fa-tower-broadcast"></i> Flux Télécom en Direct
                </span>
                <span class="text-[11px] text-slate-400 hidden sm:inline">(USSD *384*228#, SMS & Relevés)</span>
            </div>
            <div id="live-events-ticker" class="flex-1 overflow-hidden h-6 flex items-center text-xs text-slate-300 font-mono pl-0 md:pl-4">
                <span class="text-slate-500 italic">En attente d'interactions producteurs...</span>
            </div>
            <div class="text-[11px] text-slate-400 font-mono flex items-center gap-2">
                <span>Maj: <span id="live-last-sync" class="text-emerald-400">il y a 0s</span></span>
            </div>
        </div>

        <!-- Navigation Tabs (5 Tabs) -->
        <div class="border-b border-slate-200 flex flex-wrap gap-6 text-sm font-medium">
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
            <button onclick="switchTab('tab-analytics')" id="btn-tab-analytics" class="pb-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-2">
                <i class="fa-solid fa-chart-pie"></i> Analyse & Simulations (E8)
            </button>
        </div>

                <!-- TAB 1: VILLAGES & ADVICE CARDS -->
        <section id="tab-villages" class="flex flex-col gap-5">

            <!-- Overview Dashboard: Multi-Village Climate & Soil Comparison -->
            <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-sm">
                            <i class="fa-solid fa-chart-column"></i>
                        </div>
                        <div>
                            <h2 class="text-sm font-bold text-slate-900">Supervision Multi-Localités : Gradient Sud &rarr; Nord du Togo</h2>
                            <p class="text-xs text-slate-500">Variabilité réelle observée : pluies cumulées, réserve en eau des sols et fenêtres de semis</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span id="overview-sync-badge" class="text-xs bg-emerald-50 text-emerald-700 font-semibold px-2.5 py-1 rounded-full border border-emerald-200">
                            12 Localités Connectées
                        </span>
                    </div>
                </div>

                <!-- 4 Quick KPI Summary Cards -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div class="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200 flex flex-col">
                        <span class="text-[11px] font-bold text-emerald-800 uppercase flex items-center gap-1.5">
                            <i class="fa-solid fa-circle-check"></i> Semis Recommandé
                        </span>
                        <div class="flex items-baseline gap-1 mt-1">
                            <span id="kpi-count-semer" class="text-xl font-extrabold text-emerald-700">0</span>
                            <span class="text-xs text-emerald-600 font-medium">localités</span>
                        </div>
                        <span class="text-[10px] text-emerald-600 mt-0.5">Conditions biophysiques réunies</span>
                    </div>

                    <div class="p-3 rounded-xl bg-amber-50/70 border border-amber-200 flex flex-col">
                        <span class="text-[11px] font-bold text-amber-800 uppercase flex items-center gap-1.5">
                            <i class="fa-solid fa-hourglass-half"></i> En Attente
                        </span>
                        <div class="flex items-baseline gap-1 mt-1">
                            <span id="kpi-count-attendre" class="text-xl font-extrabold text-amber-700">0</span>
                            <span class="text-xs text-amber-600 font-medium">localités</span>
                        </div>
                        <span class="text-[10px] text-amber-600 mt-0.5">Humidité du sol insuffisante</span>
                    </div>

                    <div class="p-3 rounded-xl bg-red-50/70 border border-red-200 flex flex-col">
                        <span class="text-[11px] font-bold text-red-800 uppercase flex items-center gap-1.5">
                            <i class="fa-solid fa-triangle-exclamation"></i> Risque Faux Départ
                        </span>
                        <div class="flex items-baseline gap-1 mt-1">
                            <span id="kpi-count-risque" class="text-xl font-extrabold text-red-700">0</span>
                            <span class="text-xs text-red-600 font-medium">localités</span>
                        </div>
                        <span class="text-[10px] text-red-600 mt-0.5">Poche sèche post-semis détectée</span>
                    </div>

                    <div class="p-3 rounded-xl bg-indigo-50/70 border border-indigo-200 flex flex-col">
                        <span class="text-[11px] font-bold text-indigo-800 uppercase flex items-center gap-1.5">
                            <i class="fa-solid fa-droplet"></i> Humidité Moyenne
                        </span>
                        <div class="flex items-baseline gap-1 mt-1">
                            <span id="kpi-avg-moisture" class="text-xl font-extrabold text-indigo-700">0%</span>
                            <span class="text-xs text-indigo-600 font-medium">réserve sol</span>
                        </div>
                        <span class="text-[10px] text-indigo-600 mt-0.5">Moyenne nationale pondérée</span>
                    </div>
                </div>

                <!-- Comparative SVG Chart: Soil Moisture & Rain across 5 Zones -->
                <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-col gap-2">
                    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                        <span class="text-xs font-bold text-slate-800 flex items-center gap-2">
                            <span>Comparatif Régional : Humidité du Sol (%) & Pluie 3j (mm)</span>
                        </span>
                        <div class="flex items-center gap-4 text-[11px] font-semibold">
                            <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-blue-500"></span> Humidité Sol (%)</span>
                            <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-indigo-600"></span> Pluie 3j (mm)</span>
                            <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-emerald-500"></span> Seuil critique (20 mm)</span>
                        </div>
                    </div>
                    <div id="regional-comparison-chart-container" class="w-full h-44 flex items-center justify-center">
                        <span class="text-xs text-slate-400">Génération du graphique comparatif...</span>
                    </div>
                </div>
            </div>

            <!-- Quick Filter Bar -->
            <div class="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
                <div class="flex flex-wrap items-center gap-1.5">
                    <span class="text-xs font-bold text-slate-500 uppercase mr-1">Régions :</span>
                    <button onclick="filterByRegion('all')" id="btn-reg-all" class="filter-reg-btn active text-xs px-2.5 py-1 rounded-lg font-bold bg-emerald-700 text-white transition">Toutes (12)</button>
                    <button onclick="filterByRegion('Maritime')" id="btn-reg-Maritime" class="filter-reg-btn text-xs px-2.5 py-1 rounded-lg font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition">Maritime</button>
                    <button onclick="filterByRegion('Plateaux')" id="btn-reg-Plateaux" class="filter-reg-btn text-xs px-2.5 py-1 rounded-lg font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition">Plateaux</button>
                    <button onclick="filterByRegion('Centrale')" id="btn-reg-Centrale" class="filter-reg-btn text-xs px-2.5 py-1 rounded-lg font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition">Centrale</button>
                    <button onclick="filterByRegion('Kara')" id="btn-reg-Kara" class="filter-reg-btn text-xs px-2.5 py-1 rounded-lg font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition">Kara</button>
                    <button onclick="filterByRegion('Savanes')" id="btn-reg-Savanes" class="filter-reg-btn text-xs px-2.5 py-1 rounded-lg font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition">Savanes</button>
                </div>

                <div class="flex flex-wrap items-center gap-2">
                    <span class="text-xs font-bold text-slate-500 uppercase">Culture :</span>
                    <select id="filter-crop-select" onchange="applyFilters()" class="text-xs bg-slate-50 border border-slate-300 rounded-lg p-1.5 font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                        <option value="all">Toutes (Maïs, Sorgho, Niébé)</option>
                        <option value="mais">Maïs uniquement</option>
                        <option value="sorgho">Sorgho uniquement</option>
                        <option value="niebe">Niébé uniquement</option>
                    </select>

                    <span class="text-xs font-bold text-slate-500 uppercase ml-1">Statut :</span>
                    <select id="filter-status-select" onchange="applyFilters()" class="text-xs bg-slate-50 border border-slate-300 rounded-lg p-1.5 font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                        <option value="all">Tous les statuts</option>
                        <option value="SEMER">🟢 SEMER uniquement</option>
                        <option value="ATTENDRE">🟡 ATTENDRE uniquement</option>
                        <option value="RISQUE">🔴 RISQUE uniquement</option>
                    </select>
                </div>
            </div>

            <!-- CARDS GRID -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="cards-container">
                <div class="col-span-full py-12 text-center text-slate-400">
                    <i class="fa-solid fa-spinner fa-spin text-2xl"></i>
                    <p class="mt-2 text-sm">Chargement des fiches agro-climatiques...</p>
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

        <!-- TAB 5: ANALYTICS & WHAT-IF SIMULATIONS (Step E8) -->
        <section id="tab-analytics" class="hidden flex flex-col gap-6">
            <!-- Controls Card: Selectors & Sliders -->
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-5">
                <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-3">
                    <div class="flex items-center gap-3">
                        <div class="p-2 rounded-lg bg-emerald-100 text-emerald-800">
                            <i class="fa-solid fa-sliders text-lg"></i>
                        </div>
                        <div>
                            <h3 class="text-base font-bold text-slate-900">Laboratoire de Simulation & Sensibilité Agro-Climatique</h3>
                            <p class="text-xs text-slate-500">Moteur biophysique couplé Hargreaves-Samani + Réservoir du sol + Phénologie culturale</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <select id="sim-village" onchange="runAnalyticsSimulation()" class="text-xs border border-slate-300 rounded px-3 py-1.5 bg-slate-50 font-medium">
                            <option value="TG_MAR_ZIO_01">Davié (Maritime - Terre de barre)</option>
                            <option value="TG_MAR_LAC_02">Glidji (Maritime - Sablo-littoral)</option>
                            <option value="TG_PLA_HAH_04">Kévé (Plateaux - Sols ferrallitiques)</option>
                            <option value="TG_CEN_TCH_07">Sotouboua (Centrale - Transition)</option>
                            <option value="TG_KAR_KOZ_09">Lassa (Kara - Sols gravillonnaires)</option>
                            <option value="TG_SAV_TON_10">Dapaong (Savanes - Sols ferrugineux)</option>
                        </select>
                        <select id="sim-crop" onchange="runAnalyticsSimulation()" class="text-xs border border-slate-300 rounded px-3 py-1.5 bg-slate-50 font-medium">
                            <option value="mais">Maïs</option>
                            <option value="sorgho">Sorgho</option>
                            <option value="niebe">Niébé</option>
                        </select>
                    </div>
                </div>

                <!-- Sliders Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                    <div class="flex flex-col gap-1 p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div class="flex justify-between items-center text-xs">
                            <span class="font-medium text-slate-700">🌧️ Pluie globale</span>
                            <span id="label-rain-factor" class="font-bold text-emerald-700 font-mono">0%</span>
                        </div>
                        <input id="slider-rain-factor" type="range" min="0.6" max="1.4" step="0.05" value="1.0" oninput="onWhatIfInput()" class="accent-emerald-600">
                        <div class="flex justify-between text-[10px] text-slate-400"><span>-40%</span><span>Normal</span><span>+40%</span></div>
                    </div>

                    <div class="flex flex-col gap-1 p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div class="flex justify-between items-center text-xs">
                            <span class="font-medium text-slate-700">🌡️ Température</span>
                            <span id="label-temp-delta" class="font-bold text-amber-700 font-mono">+0.0°C</span>
                        </div>
                        <input id="slider-temp-delta" type="range" min="-2.0" max="4.0" step="0.5" value="0.0" oninput="onWhatIfInput()" class="accent-amber-600">
                        <div class="flex justify-between text-[10px] text-slate-400"><span>-2°C</span><span>0°C</span><span>+4°C</span></div>
                    </div>

                    <div class="flex flex-col gap-1 p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div class="flex justify-between items-center text-xs">
                            <span class="font-medium text-slate-700">🌱 Rétention Sol (TAW)</span>
                            <span id="label-taw-factor" class="font-bold text-blue-700 font-mono">100%</span>
                        </div>
                        <input id="slider-taw-factor" type="range" min="0.5" max="1.5" step="0.1" value="1.0" oninput="onWhatIfInput()" class="accent-blue-600">
                        <div class="flex justify-between text-[10px] text-slate-400"><span>50%</span><span>100%</span><span>150%</span></div>
                    </div>

                    <div class="flex flex-col gap-1 p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div class="flex justify-between items-center text-xs">
                            <span class="font-medium text-slate-700">⏳ Retard Semis</span>
                            <span id="label-delay-days" class="font-bold text-slate-700 font-mono">0 j</span>
                        </div>
                        <input id="slider-delay-days" type="range" min="0" max="30" step="1" value="0" oninput="onWhatIfInput()" class="accent-slate-600">
                        <div class="flex justify-between text-[10px] text-slate-400"><span>0j</span><span>15j</span><span>30j</span></div>
                    </div>

                    <div class="flex flex-col gap-1 p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div class="flex justify-between items-center text-xs">
                            <span class="font-medium text-slate-700">🏜️ Sécheresse Post-Semis</span>
                            <span id="label-dry-spell" class="font-bold text-red-700 font-mono">0 j</span>
                        </div>
                        <input id="slider-dry-spell" type="range" min="0" max="20" step="1" value="0" oninput="onWhatIfInput()" class="accent-red-600">
                        <div class="flex justify-between text-[10px] text-slate-400"><span>0j</span><span>10j</span><span>20j</span></div>
                    </div>
                </div>

                <!-- Presets Buttons -->
                <div class="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-100">
                    <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Scénarios prédéfinis :</span>
                    <button onclick="applyPreset('normal')" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1 rounded font-medium border border-slate-300">
                        🟢 Climat Normal
                    </button>
                    <button onclick="applyPreset('dry_year')" class="text-xs bg-amber-50 hover:bg-amber-100 text-amber-800 px-3 py-1 rounded font-medium border border-amber-200">
                        📉 Année Sèche (-30% pluie, +1°C)
                    </button>
                    <button onclick="applyPreset('warming')" class="text-xs bg-red-50 hover:bg-red-100 text-red-800 px-3 py-1 rounded font-medium border border-red-200">
                        🔥 Réchauffement Global (+2.5°C)
                    </button>
                    <button onclick="applyPreset('false_start')" class="text-xs bg-purple-50 hover:bg-purple-100 text-purple-800 px-3 py-1 rounded font-medium border border-purple-200">
                        ⚠️ Faux Départ Brutal (12j secs)
                    </button>
                </div>
            </div>

            <!-- Simulation Live KPI Bar -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center text-center">
                    <span class="text-xs text-slate-500">Démarrage Saison</span>
                    <span id="kpi-onset-date" class="text-lg font-bold text-emerald-700 mt-1">--</span>
                    <span id="kpi-onset-shift" class="text-[10px] text-slate-400 mt-0.5">Base : --</span>
                </div>
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center text-center">
                    <span class="text-xs text-slate-500">Risque Faux Départ</span>
                    <span id="kpi-false-start-risk" class="text-lg font-bold text-amber-600 mt-1">--%</span>
                    <span id="kpi-risk-badge" class="text-[10px] font-semibold px-2 py-0.5 rounded mt-0.5 bg-slate-100 text-slate-600">Modéré</span>
                </div>
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center text-center">
                    <span class="text-xs text-slate-500">Stress Hydrique</span>
                    <span id="kpi-stress-days" class="text-lg font-bold text-slate-800 mt-1">0 j</span>
                    <span class="text-[10px] text-slate-400 mt-0.5">&lt; 35% réserve utile</span>
                </div>
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center text-center">
                    <span class="text-xs text-slate-500">Fenêtre Idéale Semis</span>
                    <span id="kpi-sowing-window" class="text-sm font-bold text-emerald-800 mt-1">-- → --</span>
                    <span id="kpi-rec-variety" class="text-[10px] text-slate-500 mt-0.5">Var: TZEE-W-SR</span>
                </div>
            </div>

            <!-- 6 Interactive Visualizations Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- 1. Pluviométrie journalière & cumulée -->
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-sky-400"></span>
                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-800">1. Pluviométrie journalière & cumulée</h4>
                        </div>
                        <span class="text-[10px] text-slate-400 font-mono">CHIRPS v3 Calibré</span>
                    </div>
                    <div id="chart-rain-container" class="h-64 w-full flex items-center justify-center text-slate-400 text-xs">
                        Chargement graphique...
                    </div>
                </div>

                <!-- 2. Profil thermique & stress (35°C) -->
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-orange-500"></span>
                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-800">2. Profil thermique & Seuil critique 35°C</h4>
                        </div>
                        <span class="text-[10px] text-red-600 font-bold">Seuil pollen : 35°C</span>
                    </div>
                    <div id="chart-temp-container" class="h-64 w-full flex items-center justify-center text-slate-400 text-xs">
                        Chargement graphique...
                    </div>
                </div>

                <!-- 3. Bilan hydrique du sol -->
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-emerald-600"></span>
                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-800">3. Bilan Hydrique & Réserve Utile (%)</h4>
                        </div>
                        <span class="text-[10px] text-slate-500 font-mono">Réservoir FAO-56</span>
                    </div>
                    <div id="chart-soil-container" class="h-64 w-full flex items-center justify-center text-slate-400 text-xs">
                        Chargement graphique...
                    </div>
                </div>

                <!-- 4. Fenêtres de semis par variété -->
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-blue-500"></span>
                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-800">4. Fenêtres optimales par variété</h4>
                        </div>
                        <span class="text-[10px] text-slate-400 font-mono">Cycle vs Fin des pluies</span>
                    </div>
                    <div id="chart-windows-container" class="h-64 w-full flex items-center justify-center text-slate-400 text-xs">
                        Chargement graphique...
                    </div>
                </div>

                <!-- 5. Comparaison Inter-Zones -->
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-sky-600"></span>
                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-800">5. Disparités agro-climatiques (5 zones du Togo)</h4>
                        </div>
                        <span class="text-[10px] text-slate-400 font-mono">Bimodal vs Unimodal</span>
                    </div>
                    <div id="chart-zones-container" class="h-64 w-full flex items-center justify-center text-slate-400 text-xs">
                        Chargement graphique...
                    </div>
                </div>

                <!-- 6. Tornado de sensibilité -->
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-purple-600"></span>
                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-800">6. Diagramme Tornado de Sensibilité</h4>
                        </div>
                        <span class="text-[10px] text-slate-400 font-mono">Impact Décalage Semis</span>
                    </div>
                    <div id="chart-tornado-container" class="h-64 w-full flex items-center justify-center text-slate-400 text-xs">
                        Chargement graphique...
                    </div>
                </div>
            </div>
        </section>

    </main>

    <footer class="bg-white border-t border-slate-200 py-3 text-center text-xs text-slate-500">
        AuraFarm &bull; Hackathon Climat & Innovation 2026 (Togolaises In Science) &bull; Partenaires : ITRA, ICAT, ANAMET Togo
    </footer>

    <script>
                let allSheets = [];
        let currentStaleHours = null;
        let activeRegionFilter = 'all';

        async function loadSheets() {
            try {
                let url = '/api/dashboard/fiches';
                if (currentStaleHours !== null) {
                    url += `?force_stale_hours=${currentStaleHours}`;
                }
                const res = await fetch(url);
                if (res.ok) {
                    allSheets = await res.json();
                    updateKPIs(allSheets);
                    renderRegionalChart(allSheets);
                    applyFilters();
                } else {
                    const fallbackRes = await fetch('/api/sheets');
                    allSheets = await fallbackRes.json();
                    updateKPIs(allSheets);
                    applyFilters();
                }
            } catch (e) {
                console.error(e);
            }
        }

        function filterByRegion(reg) {
            activeRegionFilter = reg;
            document.querySelectorAll('.filter-reg-btn').forEach(btn => {
                btn.className = 'filter-reg-btn text-xs px-2.5 py-1 rounded-lg font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition';
            });
            const activeBtn = document.getElementById('btn-reg-' + reg);
            if (activeBtn) {
                activeBtn.className = 'filter-reg-btn active text-xs px-2.5 py-1 rounded-lg font-bold bg-emerald-700 text-white transition';
            }
            applyFilters();
        }

        function applyFilters() {
            const cropFilter = document.getElementById('filter-crop-select').value;
            const statusFilter = document.getElementById('filter-status-select').value;

            const filtered = allSheets.filter(s => {
                if (activeRegionFilter !== 'all') {
                    if (s.region !== activeRegionFilter) return false;
                }
                if (cropFilter !== 'all') {
                    if (s.crop_type !== cropFilter) return false;
                }
                if (statusFilter !== 'all') {
                    if (s.alert_status !== statusFilter) return false;
                }
                return true;
            });

            renderFilteredCards(filtered);
        }

        function updateKPIs(sheets) {
            if (!sheets || !sheets.length) return;
            const countSemer = sheets.filter(s => s.alert_status === 'SEMER').length;
            const countAttendre = sheets.filter(s => s.alert_status === 'ATTENDRE' || s.alert_status === 'ATTENDRE_CONSULTER_AGENT').length;
            const countRisque = sheets.filter(s => s.alert_status === 'RISQUE').length;
            
            const totalMoisture = sheets.reduce((acc, s) => acc + (s.soil_moisture_pct || 40), 0);
            const avgMoisture = Math.round(totalMoisture / sheets.length);

            document.getElementById('kpi-count-semer').textContent = countSemer;
            document.getElementById('kpi-count-attendre').textContent = countAttendre;
            document.getElementById('kpi-count-risque').textContent = countRisque;
            document.getElementById('kpi-avg-moisture').textContent = avgMoisture + '%';
        }

        function renderRegionalChart(sheets) {
            const container = document.getElementById('regional-comparison-chart-container');
            if (!container || !sheets.length) return;

            const villageMap = new Map();
            sheets.forEach(s => {
                if (!villageMap.has(s.village_id)) {
                    villageMap.set(s.village_id, s);
                }
            });
            const list = Array.from(villageMap.values());

            const w = container.clientWidth || 800;
            const h = 150;
            const padL = 35;
            const padR = 20;
            const padT = 15;
            const padB = 32;
            const chartW = w - padL - padR;
            const chartH = h - padT - padB;
            const barW = Math.max(10, Math.floor(chartW / list.length - 8));

            let svg = `<svg width="${w}" height="${h}" class="w-full h-full overflow-visible">`;
            svg += `<line x1="${padL}" y1="${padT + chartH}" x2="${w - padR}" y2="${padT + chartH}" stroke="#cbd5e1" stroke-width="1"/>`;
            svg += `<line x1="${padL}" y1="${padT}" x2="${w - padR}" y2="${padT}" stroke="#e2e8f0" stroke-dasharray="3,3"/>`;
            
            const y20 = padT + chartH - (20.0 / 60.0) * chartH;
            svg += `<line x1="${padL}" y1="${y20}" x2="${w - padR}" y2="${y20}" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4,4"/>`;
            svg += `<text x="${padL - 4}" y="${y20 + 3}" font-size="9" fill="#10b981" text-anchor="end" font-weight="bold">20mm</text>`;
            svg += `<text x="${padL - 4}" y="${padT + 4}" font-size="9" fill="#94a3b8" text-anchor="end">60mm</text>`;
            svg += `<text x="${padL - 4}" y="${padT + chartH}" font-size="9" fill="#94a3b8" text-anchor="end">0</text>`;

            list.forEach((v, i) => {
                const x = padL + i * (chartW / list.length) + (chartW / list.length - barW) / 2;
                const rainH = Math.min(chartH, Math.max(3, ((v.rain_last_3days_mm || 0) / 60.0) * chartH));
                const rainY = padT + chartH - rainH;

                const moistH = Math.min(chartH, Math.max(3, ((v.soil_moisture_pct || 0) / 100.0) * chartH));
                const moistY = padT + chartH - moistH;

                const halfW = Math.floor(barW / 2);

                svg += `<rect x="${x}" y="${rainY}" width="${halfW}" height="${rainH}" rx="2" fill="#4f46e5" opacity="0.9">
                    <title>${v.village_name} (${v.region}): Pluie 3j = ${v.rain_last_3days_mm}mm</title>
                </rect>`;

                svg += `<rect x="${x + halfW + 1}" y="${moistY}" width="${halfW}" height="${moistH}" rx="2" fill="#3b82f6" opacity="0.75">
                    <title>${v.village_name} (${v.region}): Humidité Sol = ${v.soil_moisture_pct}%</title>
                </rect>`;

                const shortName = v.village_name.length > 7 ? v.village_name.substring(0, 6) + '..' : v.village_name;
                svg += `<text x="${x + barW / 2}" y="${padT + chartH + 13}" font-size="9" fill="#475569" text-anchor="middle" font-weight="600">${shortName}</text>`;
                svg += `<text x="${x + barW / 2}" y="${padT + chartH + 23}" font-size="8" fill="#94a3b8" text-anchor="middle">${v.pcode || ''}</text>`;
            });

            svg += `</svg>`;
            container.innerHTML = svg;
        }

        function renderFilteredCards(sheets) {
            const container = document.getElementById('cards-container');
            if (!sheets.length) {
                container.innerHTML = `<div class="col-span-full py-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
                    <i class="fa-solid fa-filter-circle-xmark text-2xl text-slate-300"></i>
                    <p class="mt-2 text-sm font-medium">Aucune fiche ne correspond aux filtres sélectionnés.</p>
                </div>`;
                return;
            }

            container.innerHTML = sheets.map(s => {
                if (s.html) return s.html;
                return `
                <div class="fiche-card p-4">
                    <h4 class="font-bold">${s.village_name}</h4>
                    <p class="text-xs text-slate-500">${s.crop_type}</p>
                </div>`;
            }).join('');
        }

        function renderCards(sheets) {
            updateKPIs(sheets);
            renderRegionalChart(sheets);
            applyFilters();
        }

        function simulateStaleData() {
            currentStaleHours = 240;
            loadSheets();
        }

        function resetFilters() {
            currentStaleHours = null;
            activeRegionFilter = 'all';
            document.getElementById('filter-crop-select').value = 'all';
            document.getElementById('filter-status-select').value = 'all';
            filterByRegion('all');
            runPipeline('optimal_onset');
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

        async function loadObservations() {
            try {
                const res = await fetch('/api/observations/recent');
                const data = await res.json();
                const tbody = document.getElementById('obs-table-body');
                if (!data || data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-slate-400">Aucun relevé récent enregistré.</td></tr>';
                    return;
                }
                tbody.innerHTML = data.map(o => `
                    <tr class="border-b border-slate-100 hover:bg-slate-50">
                        <td class="p-2.5 font-medium">${o.observation_date}</td>
                        <td class="p-2.5 font-semibold text-slate-800">${o.village_id}</td>
                        <td class="p-2.5 font-bold text-emerald-700">${o.rainfall_mm} mm</td>
                        <td class="p-2.5 text-slate-600">${o.reporter_type}</td>
                        <td class="p-2.5 text-slate-400 font-mono text-[11px]">${o.reported_at ? new Date(o.reported_at).toLocaleString() : '-'}</td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error('Error loading observations', err);
            }
        }

        // --- Real-Time Telecom Events Polling (Step E5) ---
        let lastKnownEventId = 0;
        async function pollLiveStream() {
            try {
                const res = await fetch('/api/dashboard/live?limit=10');
                if (!res.ok) return;
                const data = await res.json();
                document.getElementById('live-last-sync').textContent = new Date().toLocaleTimeString();

                if (data.events && data.events.length > 0) {
                    const latest = data.events[0];
                    const ticker = document.getElementById('live-events-ticker');
                    let actionText = '';
                    if (latest.event_type === 'consultation') {
                        actionText = `📞 Consultation USSD [${latest.village_id}] : ${latest.payload?.crop || ''} → ${latest.payload?.status || 'AVIS'}`;
                    } else if (latest.event_type === 'rain_report') {
                        actionText = `🌧️ Relevé Pluviomètre [${latest.village_id}] : ${latest.payload?.rainfall_mm || 0} mm`;
                    } else if (latest.event_type === 'planting_report') {
                        actionText = `🌱 Déclaration de Semis [${latest.village_id}] : ${latest.payload?.crop || ''} (${latest.payload?.variety || ''})`;
                    } else if (latest.event_type === 'village_change') {
                        actionText = `📍 Changement Village : ${latest.payload?.village_name || latest.village_id}`;
                    } else {
                        actionText = `⚡ ${latest.event_type} [${latest.village_id}]`;
                    }
                    ticker.innerHTML = `<span class="text-emerald-300 font-semibold animate-pulse">${actionText}</span> <span class="text-slate-400 text-[10px]">(${new Date(latest.timestamp).toLocaleTimeString()})</span>`;

                    if (latest.id > lastKnownEventId) {
                        lastKnownEventId = latest.id;
                        highlightVillageCards(latest.village_id);
                    }
                }
            } catch (err) {}
        }

        function highlightVillageCards(villageId) {
            const cards = document.querySelectorAll(`[data-village-id="${villageId}"]`);
            cards.forEach(card => {
                card.style.outline = '3px solid #f59e0b';
                card.style.transition = 'all 0.4s ease';
                setTimeout(() => { card.style.outline = 'none'; }, 3000);
            });
        }

        // --- Analytics & What-If Simulation Engine (Step E8) ---
        let currentChartsData = null;
        let whatIfDebounceTimer = null;

        async function loadAnalyticsCharts() {
            const vId = document.getElementById('sim-village').value;
            const crop = document.getElementById('sim-crop').value;
            try {
                const res = await fetch(`/api/dashboard/charts?village_id=${vId}&crop_type=${crop}`);
                if (!res.ok) return;
                currentChartsData = await res.json();

                // Render all 6 charts
                if (typeof AuraCharts !== 'undefined') {
                    AuraCharts.rainChart(document.getElementById('chart-rain-container'), currentChartsData.chart_rain);
                    AuraCharts.tempChart(document.getElementById('chart-temp-container'), currentChartsData.chart_temp);
                    AuraCharts.soilChart(document.getElementById('chart-soil-container'), currentChartsData.chart_soil);
                    AuraCharts.windowsChart(document.getElementById('chart-windows-container'), currentChartsData.chart_windows);
                    AuraCharts.zonesChart(document.getElementById('chart-zones-container'), currentChartsData.chart_zones);
                    AuraCharts.tornadoChart(document.getElementById('chart-tornado-container'), currentChartsData.chart_tornado);
                }

                // Initial KPI update
                runAnalyticsSimulation();
            } catch (err) {
                console.error('Error loading analytics charts', err);
            }
        }

        function onWhatIfInput() {
            const rain = parseFloat(document.getElementById('slider-rain-factor').value);
            const temp = parseFloat(document.getElementById('slider-temp-delta').value);
            const taw = parseFloat(document.getElementById('slider-taw-factor').value);
            const delay = parseInt(document.getElementById('slider-delay-days').value);
            const dry = parseInt(document.getElementById('slider-dry-spell').value);

            document.getElementById('label-rain-factor').textContent = (rain >= 1 ? `+${Math.round((rain-1)*100)}%` : `${Math.round((rain-1)*100)}%`);
            document.getElementById('label-temp-delta').textContent = (temp >= 0 ? `+${temp.toFixed(1)}°C` : `${temp.toFixed(1)}°C`);
            document.getElementById('label-taw-factor').textContent = `${Math.round(taw*100)}%`;
            document.getElementById('label-delay-days').textContent = `${delay} j`;
            document.getElementById('label-dry-spell').textContent = `${dry} j`;

            clearTimeout(whatIfDebounceTimer);
            whatIfDebounceTimer = setTimeout(runAnalyticsSimulation, 150);
        }

        async function runAnalyticsSimulation() {
            const vId = document.getElementById('sim-village').value;
            const crop = document.getElementById('sim-crop').value;
            const rain = parseFloat(document.getElementById('slider-rain-factor').value);
            const temp = parseFloat(document.getElementById('slider-temp-delta').value);
            const taw = parseFloat(document.getElementById('slider-taw-factor').value);
            const delay = parseInt(document.getElementById('slider-delay-days').value);
            const dry = parseInt(document.getElementById('slider-dry-spell').value);

            try {
                const res = await fetch('/api/simulate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        village_id: vId,
                        crop_type: crop,
                        rain_factor: rain,
                        temp_delta_c: temp,
                        taw_factor: taw,
                        delay_days: delay,
                        dry_spell_injection: dry > 0 ? dry : null,
                        seed: 42
                    })
                });
                if (!res.ok) return;
                const sim = await res.json();

                // Update KPIs
                document.getElementById('kpi-onset-date').textContent = sim.perturbed.onset_date;
                document.getElementById('kpi-onset-shift').textContent = `Base: ${sim.baseline.onset_date} (${sim.delta.onset_shift_days >= 0 ? '+' : ''}${sim.delta.onset_shift_days}j)`;
                document.getElementById('kpi-false-start-risk').textContent = `${sim.perturbed.false_start_risk_pct}%`;
                
                const badge = document.getElementById('kpi-risk-badge');
                if (sim.perturbed.has_false_start || sim.perturbed.false_start_risk_pct > 40) {
                    badge.className = 'text-[10px] font-bold px-2 py-0.5 rounded mt-0.5 bg-red-100 text-red-800';
                    badge.textContent = 'ÉLEVÉ (Danger)';
                } else {
                    badge.className = 'text-[10px] font-bold px-2 py-0.5 rounded mt-0.5 bg-emerald-100 text-emerald-800';
                    badge.textContent = 'FAIBLE (Favorable)';
                }

                document.getElementById('kpi-stress-days').textContent = `${sim.perturbed.water_stress_days} j`;
                document.getElementById('kpi-sowing-window').textContent = `${sim.perturbed.sowing_window_start.slice(5)} → ${sim.perturbed.sowing_window_end.slice(5)}`;
                document.getElementById('kpi-rec-variety').textContent = `Var: ${sim.perturbed.recommended_variety}`;

                // Update dynamic series charts 1, 2, 3
                if (typeof AuraCharts !== 'undefined') {
                    AuraCharts.rainChart(document.getElementById('chart-rain-container'), {
                        daily_rain_mm: sim.series.rain_perturbed_mm,
                        cumulative_rain_mm: sim.series.rain_cumulative_mm,
                        onset_day_index: sim.perturbed.onset_day_of_year ? sim.perturbed.onset_day_of_year - 1 : null,
                        has_false_start: sim.perturbed.has_false_start
                    });
                    AuraCharts.tempChart(document.getElementById('chart-temp-container'), {
                        tmin_c: sim.series.tmin_c,
                        tmax_c: sim.series.tmax_c
                    });
                    AuraCharts.soilChart(document.getElementById('chart-soil-container'), {
                        soil_moisture_pct: sim.series.soil_moisture_pct
                    });
                }
            } catch (err) {
                console.error('Simulation error', err);
            }
        }

        function applyPreset(preset) {
            if (preset === 'normal') {
                document.getElementById('slider-rain-factor').value = 1.0;
                document.getElementById('slider-temp-delta').value = 0.0;
                document.getElementById('slider-taw-factor').value = 1.0;
                document.getElementById('slider-delay-days').value = 0;
                document.getElementById('slider-dry-spell').value = 0;
            } else if (preset === 'dry_year') {
                document.getElementById('slider-rain-factor').value = 0.70;
                document.getElementById('slider-temp-delta').value = 1.0;
                document.getElementById('slider-taw-factor').value = 1.0;
                document.getElementById('slider-delay-days').value = 0;
                document.getElementById('slider-dry-spell').value = 0;
            } else if (preset === 'warming') {
                document.getElementById('slider-rain-factor').value = 1.0;
                document.getElementById('slider-temp-delta').value = 2.5;
                document.getElementById('slider-taw-factor').value = 1.0;
                document.getElementById('slider-delay-days').value = 0;
                document.getElementById('slider-dry-spell').value = 0;
            } else if (preset === 'false_start') {
                document.getElementById('slider-rain-factor').value = 1.0;
                document.getElementById('slider-temp-delta').value = 0.0;
                document.getElementById('slider-taw-factor').value = 1.0;
                document.getElementById('slider-delay-days').value = 0;
                document.getElementById('slider-dry-spell').value = 12;
            }
            onWhatIfInput();
        }

        function switchTab(tabId) {
            ['tab-villages', 'tab-radio', 'tab-backtest', 'tab-observations', 'tab-analytics'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.classList.add('hidden');
            });
            const target = document.getElementById(tabId);
            if (target) target.classList.remove('hidden');

            ['btn-tab-villages', 'btn-tab-radio', 'btn-tab-backtest', 'btn-tab-observations', 'btn-tab-analytics'].forEach(btnId => {
                const btn = document.getElementById(btnId);
                if (btn) btn.className = 'pb-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-2';
            });
            const activeBtn = document.getElementById('btn-' + tabId);
            if (activeBtn) activeBtn.className = 'pb-3 border-b-2 border-emerald-600 text-emerald-800 font-semibold flex items-center gap-2';

            if (tabId === 'tab-radio') loadRadioBulletin();
            if (tabId === 'tab-backtest') loadBacktest();
            if (tabId === 'tab-observations') loadObservations();
            if (tabId === 'tab-analytics') loadAnalyticsCharts();
        }

        // Init
        loadSheets();
        pollLiveStream();
        setInterval(pollLiveStream, 3000);
    </script>
</body>
</html>"""


def render_audio_eval_html() -> str:
    """HTML evaluation studio for native speakers and juries (Step E10)."""
    return """<!DOCTYPE html>
<html lang="fr" class="h-full bg-slate-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraFarm — Évaluation Vocale Terroir (Locuteurs Natifs)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="h-full flex flex-col font-sans text-slate-800">

    <!-- Header -->
    <header class="bg-indigo-950 text-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-indigo-900 flex items-center justify-center text-indigo-300 text-xl font-bold border border-indigo-700">
                    🎙️
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h1 class="text-xl font-bold tracking-tight">AuraFarm • Évaluation Vocale Terroir</h1>
                        <span class="text-xs bg-indigo-800 text-indigo-200 px-2.5 py-0.5 rounded-full font-semibold border border-indigo-600">Étape E10</span>
                    </div>
                    <p class="text-xs text-indigo-300 font-light">Validation d'intelligibilité, de clarté 2G et d'accent authentique (Éwé, Kabiyè, Mina, FR)</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="/dashboard" class="inline-flex items-center gap-2 bg-indigo-900 hover:bg-indigo-800 text-white text-xs px-3.5 py-2 rounded-lg border border-indigo-700 transition">
                    <i class="fa-solid fa-arrow-left"></i>
                    <span>Dashboard Principal</span>
                </a>
                <a href="/audio-recorder" class="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-600 text-white text-xs px-3.5 py-2 rounded-lg font-medium transition">
                    <i class="fa-solid fa-microphone"></i>
                    <span>Studio d'Enregistrement (E1)</span>
                </a>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">

        <!-- Banner Context & Methodology -->
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div class="flex items-start gap-3.5">
                <div class="p-3 rounded-xl bg-indigo-100 text-indigo-800 text-lg">
                    <i class="fa-solid fa-headphones-simple"></i>
                </div>
                <div>
                    <h2 class="text-sm font-bold text-slate-900">Protocole d'Évaluation de la Voix Rurale (Hackathon 2026)</h2>
                    <p class="text-xs text-slate-600 mt-0.5 max-w-3xl leading-relaxed">
                        Pour garantir qu'un producteur agricole en zone blanche comprenne immédiatement l'alerte agro-climatique via son combiné basique, chaque phrase modulaire est soumise au test de la voix du terroir : clarté sous compression téléphonique 2G (300-3400 Hz), fluidité sans robotisation, et respect strict de l'accentuation régionale.
                    </p>
                </div>
            </div>
            <div class="flex items-center gap-2 bg-indigo-50 border border-indigo-200 px-3.5 py-2 rounded-xl text-xs text-indigo-900">
                <i class="fa-solid fa-shield-halved text-indigo-600"></i>
                <span>Loi Togolaise N° 2019-014 • Anonymat Garanti</span>
            </div>
        </div>

        <!-- Evaluation Grid: Left Form & Audio Player / Right Live Aggregate Metrics -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

            <!-- Left Form & Player (7 cols) -->
            <div class="lg:col-span-7 flex flex-col gap-5">
                
                <!-- Audio Audition Player Card -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">1. Choix du Clip & Écoute</h3>
                        </div>
                        <span id="player-status-badge" class="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">Prêt</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Langue ciblée</label>
                            <select id="eval-lang" onchange="onLanguageChange()" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="ewe">Éwé (Eʋegbe) — Sud / Plateaux / Maritime</option>
                                <option value="kabiye">Kabiyè — Kara / Centrale</option>
                                <option value="mina">Mina (Gɛ̀ngbe) — Littoral / Golfe / Lacs</option>
                                <option value="francais">Français Facile — National</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Phrase ou consigne à auditer</label>
                            <select id="eval-clip" onchange="updatePromptPreview()" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="status_semer">Statut SEMER (Alerte favorable)</option>
                                <option value="status_attendre">Statut ATTENDRE (Sol trop sec / faux départ)</option>
                                <option value="status_risque">Statut RISQUE (Sécheresse précoce)</option>
                                <option value="variety_recommendation">Recommandation Variété (Cycle court)</option>
                                <option value="call_agent">Consigne Agent d'appui ICAT</option>
                            </select>
                        </div>
                    </div>

                    <!-- Prompt Display -->
                    <div class="bg-indigo-900 text-indigo-100 p-4 rounded-xl border border-indigo-800 flex flex-col gap-2">
                        <div class="flex items-center justify-between text-xs text-indigo-300 font-mono">
                            <span>TRANSCRIPTION LOCALE OFFICIELLE</span>
                            <span id="prompt-clip-tag">status_semer • ewe</span>
                        </div>
                        <p id="prompt-text-display" class="text-sm font-semibold italic text-white leading-relaxed">
                            "Míele gbeƒã ɖem na mi be míate ŋu aƒã nuku fifia. Tsi dza sɔgbɔ."
                        </p>
                        <p id="prompt-meaning-display" class="text-xs text-indigo-200 border-t border-indigo-800/60 pt-1.5">
                            Traduction FR : « Avis favorable pour semer. La réserve hydrique du sol est suffisante. »
                        </p>
                    </div>

                    <!-- 2G Telephone Filter Simulator Toggle -->
                    <div class="bg-amber-50 border border-amber-200 p-3.5 rounded-xl flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2.5">
                            <i class="fa-solid fa-phone-volume text-amber-600 text-lg"></i>
                            <div>
                                <p class="text-xs font-bold text-amber-900">Simulation Filtre Haut-Parleur Téléphone 2G</p>
                                <p class="text-[11px] text-amber-800">Bande passante GSM (300-3400 Hz) + compression 8 kHz</p>
                            </div>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" id="phone-filter-toggle" class="sr-only peer" checked>
                            <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-600"></div>
                        </label>
                    </div>

                    <!-- Audio Controls -->
                    <div class="flex flex-wrap items-center gap-3 pt-1">
                        <button onclick="playAudioAudit()" id="btn-play-audio" class="flex-1 inline-flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2.5 rounded-xl text-xs shadow transition">
                            <i class="fa-solid fa-play"></i>
                            <span>Écouter l'Extrait Vocal</span>
                        </button>
                        <button onclick="stopAudioAudit()" class="inline-flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-4 py-2.5 rounded-xl text-xs transition border border-slate-300">
                            <i class="fa-solid fa-stop"></i>
                            <span>Arrêter</span>
                        </button>
                    </div>
                </div>

                <!-- Evaluation Scoring Form -->
                <form id="evaluation-form" onsubmit="submitEvaluation(event)" class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">2. Grille de Notation par l'Évaluateur</h3>
                        </div>
                        <span class="text-xs text-slate-500 italic">* Tous les critères sont obligatoires</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Nom ou Pseudonyme de l'auditeur</label>
                            <input type="text" id="evaluator-name" placeholder="Ex: M. Koffi / Évaluateur Juré" required class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Région d'origine / Attachement</label>
                            <select id="evaluator-region" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="Maritime">Région Maritime (Zio, Yoto, Vo, Golfe)</option>
                                <option value="Plateaux">Région des Plateaux (Kloto, Ogou, Haho)</option>
                                <option value="Centrale">Région Centrale (Tchaoudjo, Sotouboua)</option>
                                <option value="Kara">Région de la Kara (Kozah, Assoli, Doufelgou)</option>
                                <option value="Savanes">Région des Savanes (Tône, Oti, Kpendjal)</option>
                            </select>
                        </div>
                    </div>

                    <!-- Criteria Sliders / Stars -->
                    <div class="flex flex-col gap-3 pt-2">
                        
                        <!-- Criterion 1: Clarity -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">1. Clarté & Intelligibilité sonore</span>
                                    <p class="text-[11px] text-slate-500">Même avec le bruit de fond ou sur haut-parleur bon marché</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="clarity-stars">
                                    <!-- 5 star radio inputs -->
                                    <input type="radio" name="clarity" value="1" id="c1" class="hidden peer/c1">
                                    <label for="c1" onclick="setRating('clarity', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c1:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="2" id="c2" class="hidden peer/c2">
                                    <label for="c2" onclick="setRating('clarity', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c2:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="3" id="c3" class="hidden peer/c3">
                                    <label for="c3" onclick="setRating('clarity', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c3:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="4" id="c4" class="hidden peer/c4">
                                    <label for="c4" onclick="setRating('clarity', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c4:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="5" id="c5" checked class="hidden peer/c5">
                                    <label for="c5" onclick="setRating('clarity', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c5:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <span id="clarity-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 2: Naturalness -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">2. Fluidité & Naturel du débit</span>
                                    <p class="text-[11px] text-slate-500">Cadence naturelle, absence d'artéfacts ou de saccades robotiques</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="naturalness-stars">
                                    <input type="radio" name="naturalness" value="1" id="n1" class="hidden">
                                    <label for="n1" onclick="setRating('naturalness', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="2" id="n2" class="hidden">
                                    <label for="n2" onclick="setRating('naturalness', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="3" id="n3" class="hidden">
                                    <label for="n3" onclick="setRating('naturalness', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="4" id="n4" class="hidden">
                                    <label for="n4" onclick="setRating('naturalness', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="5" id="n5" checked class="hidden">
                                    <label for="n5" onclick="setRating('naturalness', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <span id="naturalness-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 3: Accent Authenticity -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">3. Authenticité de l'accent du terroir</span>
                                    <p class="text-[11px] text-slate-500">Ton respectueux et naturel pour un producteur de la zone</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="authenticity-stars">
                                    <input type="radio" name="authenticity" value="1" id="a1" class="hidden">
                                    <label for="a1" onclick="setRating('authenticity', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="2" id="a2" class="hidden">
                                    <label for="a2" onclick="setRating('authenticity', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="3" id="a3" class="hidden">
                                    <label for="a3" onclick="setRating('authenticity', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="4" id="a4" class="hidden">
                                    <label for="a4" onclick="setRating('authenticity', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="5" id="a5" checked class="hidden">
                                    <label for="a5" onclick="setRating('authenticity', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <span id="authenticity-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 4: Immediate Comprehension Test -->
                        <div class="p-3.5 bg-indigo-50/60 rounded-xl border border-indigo-200 flex items-center justify-between">
                            <div>
                                <span class="text-xs font-bold text-indigo-950">4. Test de compréhension immédiate sans hésitation</span>
                                <p class="text-[11px] text-indigo-800">L'agriculteur sait-il exactement quoi faire dès la première écoute ?</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <label class="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-800 cursor-pointer">
                                    <input type="radio" name="comprehension" value="1" checked class="text-emerald-600 focus:ring-emerald-500">
                                    <span>Oui (Compris)</span>
                                </label>
                                <label class="inline-flex items-center gap-1.5 text-xs font-bold text-red-700 cursor-pointer ml-2">
                                    <input type="radio" name="comprehension" value="0" class="text-red-600 focus:ring-red-500">
                                    <span>Non (Ambigu)</span>
                                </label>
                            </div>
                        </div>

                    </div>

                    <!-- Comments -->
                    <div>
                        <label class="block text-xs font-semibold text-slate-700 mb-1">Commentaires qualitatifs & suggestions d'amélioration</label>
                        <textarea id="eval-comments" rows="2" placeholder="Ex: Débit un peu rapide sur le deuxième mot, sinon intonation parfaite pour la Kara." class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"></textarea>
                    </div>

                    <button type="submit" id="btn-submit-eval" class="w-full inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2.5 rounded-xl text-xs shadow transition">
                        <i class="fa-solid fa-circle-check"></i>
                        <span>Enregistrer l'Évaluation Vocale</span>
                    </button>
                    <div id="eval-submit-msg" class="hidden p-2.5 rounded-lg text-xs font-semibold text-center"></div>
                </form>

            </div>

            <!-- Right Dashboard: Live Evaluation Metrics & History (5 cols) -->
            <div class="lg:col-span-5 flex flex-col gap-5">
                
                <!-- Scorecards per Language -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">Moyennes de Validation par Langue</h3>
                        </div>
                        <button onclick="loadEvaluationSummary()" class="text-xs text-indigo-600 hover:underline flex items-center gap-1 font-semibold">
                            <i class="fa-solid fa-arrows-rotate"></i> Actualiser
                        </button>
                    </div>

                    <div id="summary-cards-container" class="flex flex-col gap-3">
                        <!-- Populated dynamically via JS -->
                        <div class="text-center py-6 text-xs text-slate-400">Chargement des indicateurs...</div>
                    </div>
                </div>

                <!-- Recent Feedback Stream -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-3">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">Dernières Évaluations Soumises</h3>
                        </div>
                        <span id="eval-count-badge" class="text-xs bg-slate-100 text-slate-700 font-bold px-2 py-0.5 rounded-full">0 avis</span>
                    </div>

                    <div id="recent-reviews-list" class="flex flex-col gap-2.5 max-h-[380px] overflow-y-auto pr-1">
                        <!-- Populated dynamically via JS -->
                        <div class="text-center py-6 text-xs text-slate-400">Aucune évaluation enregistrée pour le moment.</div>
                    </div>
                </div>

            </div>

        </div>

    </main>

    <footer class="bg-white border-t border-slate-200 mt-auto py-4 text-center text-xs text-slate-500">
        AuraFarm &bull; Hackathon Climat & Innovation 2026 &bull; Équipe GPS² (Togolaises In Science)
    </footer>

    <script>
        // State
        const promptBank = {
            "ewe": {
                "status_semer": { text: "Míele gbeƒã ɖem na mi be míate ŋu aƒã nuku fifia. Tsi dza sɔgbɔ.", fr: "Avis favorable pour semer. La réserve hydrique du sol est suffisante." },
                "status_attendre": { text: "Migalɔ̃ aƒã nuku o. Manyo fifia o, tsi medza sɔgbɔ o.", fr: "Attendez avant de semer. Humidité du sol insuffisante." },
                "status_risque": { text: "Nyanyanyɛ : Nuɖuɖu ƒe nɔnɔme gblẽ. Faux départ le dzɔdzɔm.", fr: "Risque élevé de faux départ de saison. Ne pas semer." },
                "variety_recommendation": { text: "Míedo kpɔ̃ TZEE-W-Pop miadze aƒã na ŋkeke blaenyi.", fr: "Semez la variété précoce TZEE-W-Pop adaptée à la durée de pluie." },
                "call_agent": { text: "Bip 90123456 ne ICAT ƒe agbledɔwɔla aƒo nu na wò.", fr: "Faites un bip au 90123456 pour parler à un agent ICAT." }
            },
            "kabiye": {
                "status_semer": { text: "Pɩwɛ ɖeu se ŋdu kɛlɛʊ nɔɔnɔɔ. Tɛʊ nɩwa pɩtɩŋa.", fr: "Vous pouvez semer maintenant. Pluie adéquate constatée." },
                "status_attendre": { text: "Taadʊ kɛlɛʊ nɔɔnɔɔ. Ðaŋ tɛʊ nɩʊ nɔɔnɔɔ.", fr: "Attendez encore avant les semis. Humidité insuffisante." },
                "status_risque": { text: "Kigbɛɖɛɛ wɛɛ : tɛʊ kaɣ hɛʊ kpaagbaa.", fr: "Alerte : risque critique de sécheresse précoce." },
                "variety_recommendation": { text: "Du Sotubua tɛ nuku ŋgʊ kɩtɛŋ lɔŋ yɔ.", fr: "Privilégiez la variété précoce recommandée pour votre sol." },
                "call_agent": { text: "Ya ICAT tɔm kɛ 90123456 taa.", fr: "Contactez le conseiller ICAT au 90123456." }
            },
            "mina": {
                "status_semer": { text: "Míatɛŋ ado nuku fifia. Tsi dza gbaŋgbaŋ le anyigba.", fr: "Vous pouvez semer dès maintenant. Bonne humidité du sol." },
                "status_attendre": { text: "Migado nuku o. Tsi megakpɔ dza nyuie o.", fr: "Ne semez pas encore. Attendez une nouvelle pluie continue." },
                "status_risque": { text: "Kpoɖoɖo li : Faux départ le agblea me.", fr: "Attention : risque de faux départ pluvieux." },
                "variety_recommendation": { text: "Do variety TZEE-W-Pop le ŋkeke blaenyi me.", fr: "Variété précoce recommandée pour sécuriser la récolte." },
                "call_agent": { text: "Yɔ ICAT tɔ le 90123456 jí.", fr: "Consultez l'agent ICAT de votre préfecture." }
            },
            "francais": {
                "status_semer": { text: "Avis favorable pour semer. La réserve hydrique du sol dépasse le seuil critique.", fr: "Avis favorable pour semer immédiatement." },
                "status_attendre": { text: "Attendez avant de semer. Le sol est trop sec pour garantir la levée des graines.", fr: "Humidité insuffisante." },
                "status_risque": { text: "Alerte agro-météo : risque élevé de faux départ. Pause sèche probable.", fr: "Sécheresse précoce détectée." },
                "variety_recommendation": { text: "Semez la variété précoce certifiée ITRA à cycle court 85 jours.", fr: "Variété à haut rendement adaptée." },
                "call_agent": { text: "Faites un bip au 90123456 pour être rappelé gratuitement par votre agent ICAT.", fr: "Assistance technique gratuite." }
            }
        };

        let currentRatings = { clarity: 5, naturalness: 5, authenticity: 5 };
        let audioContext = null;

        function setRating(metric, score) {
            currentRatings[metric] = score;
            document.getElementById(metric + '-score-label').textContent = score + '/5';
            
            // Highlight star icons
            const container = document.getElementById(metric + '-stars');
            const labels = container.querySelectorAll('label');
            labels.forEach((lbl, idx) => {
                if (idx < score) {
                    lbl.className = 'cursor-pointer text-amber-400 text-lg';
                } else {
                    lbl.className = 'cursor-pointer text-slate-300 hover:text-amber-400 text-lg';
                }
            });
        }

        function onLanguageChange() {
            updatePromptPreview();
            loadEvaluationSummary();
        }

        function updatePromptPreview() {
            const lang = document.getElementById('eval-lang').value;
            const clip = document.getElementById('eval-clip').value;
            const item = (promptBank[lang] && promptBank[lang][clip]) || { text: 'Phrase en cours d\'enregistrement...', fr: '' };
            
            document.getElementById('prompt-clip-tag').textContent = clip + ' • ' + lang;
            document.getElementById('prompt-text-display').textContent = '"' + item.text + '"';
            document.getElementById('prompt-meaning-display').textContent = 'Sens : « ' + item.fr + ' »';
        }

        function playAudioAudit() {
            const lang = document.getElementById('eval-lang').value;
            const clip = document.getElementById('eval-clip').value;
            const item = (promptBank[lang] && promptBank[lang][clip]) || { text: '' };
            const statusBadge = document.getElementById('player-status-badge');
            const useFilter = document.getElementById('phone-filter-toggle').checked;

            statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold animate-pulse';
            statusBadge.textContent = useFilter ? '📞 Lecture 2G GSM (Filtre actif)' : '🔊 Lecture Audio Direct';

            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(item.text);
                utterance.lang = lang === 'francais' ? 'fr-FR' : 'fr-FR';
                utterance.rate = useFilter ? 0.95 : 1.0;
                utterance.pitch = useFilter ? 1.15 : 1.0;

                utterance.onend = () => {
                    statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium';
                    statusBadge.textContent = 'Terminé';
                };
                window.speechSynthesis.speak(utterance);
            }
        }

        function stopAudioAudit() {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
            const statusBadge = document.getElementById('player-status-badge');
            statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium';
            statusBadge.textContent = 'Arrêté';
        }

        async function submitEvaluation(e) {
            e.preventDefault();
            const submitBtn = document.getElementById('btn-submit-eval');
            const msgBox = document.getElementById('eval-submit-msg');
            submitBtn.disabled = true;

            const payload = {
                clip_id: document.getElementById('eval-clip').value,
                language: document.getElementById('eval-lang').value,
                evaluator_name: document.getElementById('evaluator-name').value.trim() || 'Anonyme',
                evaluator_origin_region: document.getElementById('evaluator-region').value,
                clarity_rating: currentRatings.clarity,
                naturalness_rating: currentRatings.naturalness,
                accent_authenticity_rating: currentRatings.authenticity,
                comprehension_check_passed: document.querySelector('input[name="comprehension"]:checked').value === "1",
                comments: document.getElementById('eval-comments').value.trim()
            };

            try {
                const res = await fetch('/api/audio-eval', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    msgBox.className = 'p-2.5 rounded-lg text-xs font-semibold text-center bg-emerald-100 text-emerald-800 border border-emerald-300';
                    msgBox.textContent = '✓ Évaluation enregistrée avec succès (ID #' + data.evaluation_id + ') !';
                    msgBox.classList.remove('hidden');
                    document.getElementById('eval-comments').value = '';
                    loadEvaluationSummary();
                } else {
                    throw new Error(data.detail || 'Erreur lors de l\'enregistrement');
                }
            } catch (err) {
                msgBox.className = 'p-2.5 rounded-lg text-xs font-semibold text-center bg-red-100 text-red-800 border border-red-300';
                msgBox.textContent = 'Erreur : ' + err.message;
                msgBox.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
                setTimeout(() => { msgBox.classList.add('hidden'); }, 4000);
            }
        }

        async function loadEvaluationSummary() {
            try {
                const res = await fetch('/api/audio-eval/summary');
                const data = await res.json();
                renderSummaryCards(data);
            } catch (e) {
                console.error('Erreur chargement summary:', e);
            }

            try {
                const res = await fetch('/api/audio-eval/list?limit=10');
                const list = await res.json();
                renderRecentReviews(list);
            } catch (e) {
                console.error('Erreur chargement reviews:', e);
            }
        }

        function renderSummaryCards(data) {
            const container = document.getElementById('summary-cards-container');
            const langs = [
                { key: 'ewe', label: 'Éwé (Eʋegbe)', icon: '🌾' },
                { key: 'kabiye', label: 'Kabiyè', icon: '⛰️' },
                { key: 'mina', label: 'Mina (Gɛ̀ngbe)', icon: '🌊' },
                { key: 'francais', label: 'Français Facile', icon: '📢' }
            ];

            const byLang = data.by_language || {};
            let html = '';

            langs.forEach(l => {
                const item = byLang[l.key] || { count: 0, avg_clarity: 0, avg_naturalness: 0, avg_authenticity: 0, comprehension_rate_pct: 0, mean_overall_score: 0 };
                const countBadge = item.count > 0 ? `<span class="bg-indigo-100 text-indigo-800 text-[10px] font-bold px-2 py-0.5 rounded-full">${item.count} avis</span>` : `<span class="text-slate-400 text-[10px]">0 avis</span>`;
                
                html += `
                    <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col gap-2 hover:border-indigo-300 transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span>${l.icon}</span>
                                <span class="text-xs font-bold text-slate-900">${l.label}</span>
                            </div>
                            <div class="flex items-center gap-2">
                                ${countBadge}
                                <span class="text-xs font-extrabold text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">★ ${item.mean_overall_score}/5</span>
                            </div>
                        </div>
                        <div class="grid grid-cols-4 gap-1.5 text-center text-[10px]">
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Clarté</span>
                                <span class="font-bold text-slate-800">${item.avg_clarity || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Naturel</span>
                                <span class="font-bold text-slate-800">${item.avg_naturalness || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Accent</span>
                                <span class="font-bold text-slate-800">${item.avg_authenticity || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Compris</span>
                                <span class="font-bold ${item.comprehension_rate_pct >= 80 ? 'text-emerald-700' : 'text-slate-800'}">${item.comprehension_rate_pct ? item.comprehension_rate_pct + '%' : '—'}</span>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
        }

        function renderRecentReviews(list) {
            const container = document.getElementById('recent-reviews-list');
            document.getElementById('eval-count-badge').textContent = list.length + ' avis';
            if (!list || list.length === 0) {
                container.innerHTML = '<div class="text-center py-6 text-xs text-slate-400">Aucune évaluation enregistrée pour le moment.</div>';
                return;
            }

            let html = '';
            list.slice(0, 8).forEach(r => {
                const compBadge = r.comprehension_check_passed ? '<span class="text-emerald-700 font-bold text-[10px] bg-emerald-50 px-1.5 py-0.5 rounded">Compris</span>' : '<span class="text-red-700 font-bold text-[10px] bg-red-50 px-1.5 py-0.5 rounded">Ambigu</span>';
                html += `
                    <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex flex-col gap-1">
                        <div class="flex items-center justify-between text-[11px]">
                            <span class="font-bold text-slate-900">${r.evaluator_name || 'Anonyme'} (${r.evaluator_origin_region || 'Maritime'})</span>
                            <span class="text-slate-400">${r.language.toUpperCase()} • ${r.clip_id}</span>
                        </div>
                        <div class="flex items-center gap-3 text-[11px] text-slate-600">
                            <span>Clarté : <b class="text-amber-600">${r.clarity_rating}/5</b></span>
                            <span>Naturel : <b class="text-amber-600">${r.naturalness_rating}/5</b></span>
                            <span>Accent : <b class="text-amber-600">${r.accent_authenticity_rating}/5</b></span>
                            ${compBadge}
                        </div>
                        ${r.comments ? `<p class="text-[11px] text-slate-500 italic bg-white p-1.5 rounded border border-slate-100">« ${r.comments} »</p>` : ''}
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        // Init
        updatePromptPreview();
        setRating('clarity', 5);
        setRating('naturalness', 5);
        setRating('authenticity', 5);
        loadEvaluationSummary();
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
                inSession = true;
                currentInputHistory = [];
                currentSessionId = 'sim_' + Math.floor(Math.random() * 1000000);
                inputEl.textContent = '';
                await sendUssdHop('');
            } else {
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


def render_audio_eval_html() -> str:
    """HTML evaluation studio for native speakers and juries (Step E10)."""
    return """<!DOCTYPE html>
<html lang="fr" class="h-full bg-slate-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraFarm — Évaluation Vocale Terroir (Locuteurs Natifs)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="h-full flex flex-col font-sans text-slate-800">

    <!-- Header -->
    <header class="bg-indigo-950 text-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-indigo-900 flex items-center justify-center text-indigo-300 text-xl font-bold border border-indigo-700">
                    🎙️
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h1 class="text-xl font-bold tracking-tight">AuraFarm • Évaluation Vocale Terroir</h1>
                        <span class="text-xs bg-indigo-800 text-indigo-200 px-2.5 py-0.5 rounded-full font-semibold border border-indigo-600">Étape E10</span>
                    </div>
                    <p class="text-xs text-indigo-300 font-light">Validation d'intelligibilité, de clarté 2G et d'accent authentique (Éwé, Kabiyè, Mina, FR)</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="/dashboard" class="inline-flex items-center gap-2 bg-indigo-900 hover:bg-indigo-800 text-white text-xs px-3.5 py-2 rounded-lg border border-indigo-700 transition">
                    <i class="fa-solid fa-arrow-left"></i>
                    <span>Dashboard Principal</span>
                </a>
                <a href="/audio-recorder" class="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-600 text-white text-xs px-3.5 py-2 rounded-lg font-medium transition">
                    <i class="fa-solid fa-microphone"></i>
                    <span>Studio d'Enregistrement (E1)</span>
                </a>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">

        <!-- Banner Context & Methodology -->
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div class="flex items-start gap-3.5">
                <div class="p-3 rounded-xl bg-indigo-100 text-indigo-800 text-lg">
                    <i class="fa-solid fa-headphones-simple"></i>
                </div>
                <div>
                    <h2 class="text-sm font-bold text-slate-900">Protocole d'Évaluation de la Voix Rurale (Hackathon 2026)</h2>
                    <p class="text-xs text-slate-600 mt-0.5 max-w-3xl leading-relaxed">
                        Pour garantir qu'un producteur agricole en zone blanche comprenne immédiatement l'alerte agro-climatique via son combiné basique, chaque phrase modulaire est soumise au test de la voix du terroir : clarté sous compression téléphonique 2G (300-3400 Hz), fluidité sans robotisation, et respect strict de l'accentuation régionale.
                    </p>
                </div>
            </div>
            <div class="flex items-center gap-2 bg-indigo-50 border border-indigo-200 px-3.5 py-2 rounded-xl text-xs text-indigo-900">
                <i class="fa-solid fa-shield-halved text-indigo-600"></i>
                <span>Loi Togolaise N° 2019-014 • Anonymat Garanti</span>
            </div>
        </div>

        <!-- Evaluation Grid: Left Form & Audio Player / Right Live Aggregate Metrics -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

            <!-- Left Form & Player (7 cols) -->
            <div class="lg:col-span-7 flex flex-col gap-5">
                
                <!-- Audio Audition Player Card -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">1. Choix du Clip & Écoute</h3>
                        </div>
                        <span id="player-status-badge" class="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">Prêt</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Langue ciblée</label>
                            <select id="eval-lang" onchange="onLanguageChange()" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="ewe">Éwé (Eʋegbe) — Sud / Plateaux / Maritime</option>
                                <option value="kabiye">Kabiyè — Kara / Centrale</option>
                                <option value="mina">Mina (Gɛ̀ngbe) — Littoral / Golfe / Lacs</option>
                                <option value="francais">Français Facile — National</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Phrase ou consigne à auditer</label>
                            <select id="eval-clip" onchange="updatePromptPreview()" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="status_semer">Statut SEMER (Alerte favorable)</option>
                                <option value="status_attendre">Statut ATTENDRE (Sol trop sec / faux départ)</option>
                                <option value="status_risque">Statut RISQUE (Sécheresse précoce)</option>
                                <option value="variety_recommendation">Recommandation Variété (Cycle court)</option>
                                <option value="call_agent">Consigne Agent d'appui ICAT</option>
                            </select>
                        </div>
                    </div>

                    <!-- Prompt Display -->
                    <div class="bg-indigo-900 text-indigo-100 p-4 rounded-xl border border-indigo-800 flex flex-col gap-2">
                        <div class="flex items-center justify-between text-xs text-indigo-300 font-mono">
                            <span>TRANSCRIPTION LOCALE OFFICIELLE</span>
                            <span id="prompt-clip-tag">status_semer • ewe</span>
                        </div>
                        <p id="prompt-text-display" class="text-sm font-semibold italic text-white leading-relaxed">
                            "Míele gbeƒã ɖem na mi be míate ŋu aƒã nuku fifia. Tsi dza sɔgbɔ."
                        </p>
                        <p id="prompt-meaning-display" class="text-xs text-indigo-200 border-t border-indigo-800/60 pt-1.5">
                            Traduction FR : « Avis favorable pour semer. La réserve hydrique du sol est suffisante. »
                        </p>
                    </div>

                    <!-- 2G Telephone Filter Simulator Toggle -->
                    <div class="bg-amber-50 border border-amber-200 p-3.5 rounded-xl flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2.5">
                            <i class="fa-solid fa-phone-volume text-amber-600 text-lg"></i>
                            <div>
                                <p class="text-xs font-bold text-amber-900">Simulation Filtre Haut-Parleur Téléphone 2G</p>
                                <p class="text-[11px] text-amber-800">Bande passante GSM (300-3400 Hz) + compression 8 kHz</p>
                            </div>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" id="phone-filter-toggle" class="sr-only peer" checked>
                            <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-600"></div>
                        </label>
                    </div>

                    <!-- Audio Controls -->
                    <div class="flex flex-wrap items-center gap-3 pt-1">
                        <button onclick="playAudioAudit()" id="btn-play-audio" class="flex-1 inline-flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2.5 rounded-xl text-xs shadow transition">
                            <i class="fa-solid fa-play"></i>
                            <span>Écouter l'Extrait Vocal</span>
                        </button>
                        <button onclick="stopAudioAudit()" class="inline-flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-4 py-2.5 rounded-xl text-xs transition border border-slate-300">
                            <i class="fa-solid fa-stop"></i>
                            <span>Arrêter</span>
                        </button>
                    </div>
                </div>

                <!-- Evaluation Scoring Form -->
                <form id="evaluation-form" onsubmit="submitEvaluation(event)" class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">2. Grille de Notation par l'Évaluateur</h3>
                        </div>
                        <span class="text-xs text-slate-500 italic">* Tous les critères sont obligatoires</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Nom ou Pseudonyme de l'auditeur</label>
                            <input type="text" id="evaluator-name" placeholder="Ex: M. Koffi / Évaluateur Juré" required class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Région d'origine / Attachement</label>
                            <select id="evaluator-region" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="Maritime">Région Maritime (Zio, Yoto, Vo, Golfe)</option>
                                <option value="Plateaux">Région des Plateaux (Kloto, Ogou, Haho)</option>
                                <option value="Centrale">Région Centrale (Tchaoudjo, Sotouboua)</option>
                                <option value="Kara">Région de la Kara (Kozah, Assoli, Doufelgou)</option>
                                <option value="Savanes">Région des Savanes (Tône, Oti, Kpendjal)</option>
                            </select>
                        </div>
                    </div>

                    <!-- Criteria Sliders / Stars -->
                    <div class="flex flex-col gap-3 pt-2">
                        
                        <!-- Criterion 1: Clarity -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">1. Clarté & Intelligibilité sonore</span>
                                    <p class="text-[11px] text-slate-500">Même avec le bruit de fond ou sur haut-parleur bon marché</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="clarity-stars">
                                    <!-- 5 star radio inputs -->
                                    <input type="radio" name="clarity" value="1" id="c1" class="hidden peer/c1">
                                    <label for="c1" onclick="setRating('clarity', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c1:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="2" id="c2" class="hidden peer/c2">
                                    <label for="c2" onclick="setRating('clarity', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c2:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="3" id="c3" class="hidden peer/c3">
                                    <label for="c3" onclick="setRating('clarity', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c3:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="4" id="c4" class="hidden peer/c4">
                                    <label for="c4" onclick="setRating('clarity', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c4:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="5" id="c5" checked class="hidden peer/c5">
                                    <label for="c5" onclick="setRating('clarity', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c5:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <span id="clarity-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 2: Naturalness -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">2. Fluidité & Naturel du débit</span>
                                    <p class="text-[11px] text-slate-500">Cadence naturelle, absence d'artéfacts ou de saccades robotiques</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="naturalness-stars">
                                    <input type="radio" name="naturalness" value="1" id="n1" class="hidden">
                                    <label for="n1" onclick="setRating('naturalness', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="2" id="n2" class="hidden">
                                    <label for="n2" onclick="setRating('naturalness', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="3" id="n3" class="hidden">
                                    <label for="n3" onclick="setRating('naturalness', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="4" id="n4" class="hidden">
                                    <label for="n4" onclick="setRating('naturalness', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="5" id="n5" checked class="hidden">
                                    <label for="n5" onclick="setRating('naturalness', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <span id="naturalness-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 3: Accent Authenticity -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">3. Authenticité de l'accent du terroir</span>
                                    <p class="text-[11px] text-slate-500">Ton respectueux et naturel pour un producteur de la zone</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="authenticity-stars">
                                    <input type="radio" name="authenticity" value="1" id="a1" class="hidden">
                                    <label for="a1" onclick="setRating('authenticity', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="2" id="a2" class="hidden">
                                    <label for="a2" onclick="setRating('authenticity', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="3" id="a3" class="hidden">
                                    <label for="a3" onclick="setRating('authenticity', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="4" id="a4" class="hidden">
                                    <label for="a4" onclick="setRating('authenticity', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="5" id="a5" checked class="hidden">
                                    <label for="a5" onclick="setRating('authenticity', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <span id="authenticity-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 4: Immediate Comprehension Test -->
                        <div class="p-3.5 bg-indigo-50/60 rounded-xl border border-indigo-200 flex items-center justify-between">
                            <div>
                                <span class="text-xs font-bold text-indigo-950">4. Test de compréhension immédiate sans hésitation</span>
                                <p class="text-[11px] text-indigo-800">L'agriculteur sait-il exactement quoi faire dès la première écoute ?</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <label class="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-800 cursor-pointer">
                                    <input type="radio" name="comprehension" value="1" checked class="text-emerald-600 focus:ring-emerald-500">
                                    <span>Oui (Compris)</span>
                                </label>
                                <label class="inline-flex items-center gap-1.5 text-xs font-bold text-red-700 cursor-pointer ml-2">
                                    <input type="radio" name="comprehension" value="0" class="text-red-600 focus:ring-red-500">
                                    <span>Non (Ambigu)</span>
                                </label>
                            </div>
                        </div>

                    </div>

                    <!-- Comments -->
                    <div>
                        <label class="block text-xs font-semibold text-slate-700 mb-1">Commentaires qualitatifs & suggestions d'amélioration</label>
                        <textarea id="eval-comments" rows="2" placeholder="Ex: Débit un peu rapide sur le deuxième mot, sinon intonation parfaite pour la Kara." class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"></textarea>
                    </div>

                    <button type="submit" id="btn-submit-eval" class="w-full inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2.5 rounded-xl text-xs shadow transition">
                        <i class="fa-solid fa-circle-check"></i>
                        <span>Enregistrer l'Évaluation Vocale</span>
                    </button>
                    <div id="eval-submit-msg" class="hidden p-2.5 rounded-lg text-xs font-semibold text-center"></div>
                </form>

            </div>

            <!-- Right Dashboard: Live Evaluation Metrics & History (5 cols) -->
            <div class="lg:col-span-5 flex flex-col gap-5">
                
                <!-- Scorecards per Language -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">Moyennes de Validation par Langue</h3>
                        </div>
                        <button onclick="loadEvaluationSummary()" class="text-xs text-indigo-600 hover:underline flex items-center gap-1 font-semibold">
                            <i class="fa-solid fa-arrows-rotate"></i> Actualiser
                        </button>
                    </div>

                    <div id="summary-cards-container" class="flex flex-col gap-3">
                        <!-- Populated dynamically via JS -->
                        <div class="text-center py-6 text-xs text-slate-400">Chargement des indicateurs...</div>
                    </div>
                </div>

                <!-- Recent Feedback Stream -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-3">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">Dernières Évaluations Soumises</h3>
                        </div>
                        <span id="eval-count-badge" class="text-xs bg-slate-100 text-slate-700 font-bold px-2 py-0.5 rounded-full">0 avis</span>
                    </div>

                    <div id="recent-reviews-list" class="flex flex-col gap-2.5 max-h-[380px] overflow-y-auto pr-1">
                        <!-- Populated dynamically via JS -->
                        <div class="text-center py-6 text-xs text-slate-400">Aucune évaluation enregistrée pour le moment.</div>
                    </div>
                </div>

            </div>

        </div>

    </main>

    <footer class="bg-white border-t border-slate-200 mt-auto py-4 text-center text-xs text-slate-500">
        AuraFarm &bull; Hackathon Climat & Innovation 2026 &bull; Équipe GPS² (Togolaises In Science)
    </footer>

    <script>
        // State
        const promptBank = {
            "ewe": {
                "status_semer": { text: "Míele gbeƒã ɖem na mi be míate ŋu aƒã nuku fifia. Tsi dza sɔgbɔ.", fr: "Avis favorable pour semer. La réserve hydrique du sol est suffisante." },
                "status_attendre": { text: "Migalɔ̃ aƒã nuku o. Manyo fifia o, tsi medza sɔgbɔ o.", fr: "Attendez avant de semer. Humidité du sol insuffisante." },
                "status_risque": { text: "Nyanyanyɛ : Nuɖuɖu ƒe nɔnɔme gblẽ. Faux départ le dzɔdzɔm.", fr: "Risque élevé de faux départ de saison. Ne pas semer." },
                "variety_recommendation": { text: "Míedo kpɔ̃ TZEE-W-Pop miadze aƒã na ŋkeke blaenyi.", fr: "Semez la variété précoce TZEE-W-Pop adaptée à la durée de pluie." },
                "call_agent": { text: "Bip 90123456 ne ICAT ƒe agbledɔwɔla aƒo nu na wò.", fr: "Faites un bip au 90123456 pour parler à un agent ICAT." }
            },
            "kabiye": {
                "status_semer": { text: "Pɩwɛ ɖeu se ŋdu kɛlɛʊ nɔɔnɔɔ. Tɛʊ nɩwa pɩtɩŋa.", fr: "Vous pouvez semer maintenant. Pluie adéquate constatée." },
                "status_attendre": { text: "Taadʊ kɛlɛʊ nɔɔnɔɔ. Ðaŋ tɛʊ nɩʊ nɔɔnɔɔ.", fr: "Attendez encore avant les semis. Humidité insuffisante." },
                "status_risque": { text: "Kigbɛɖɛɛ wɛɛ : tɛʊ kaɣ hɛʊ kpaagbaa.", fr: "Alerte : risque critique de sécheresse précoce." },
                "variety_recommendation": { text: "Du Sotubua tɛ nuku ŋgʊ kɩtɛŋ lɔŋ yɔ.", fr: "Privilégiez la variété précoce recommandée pour votre sol." },
                "call_agent": { text: "Ya ICAT tɔm kɛ 90123456 taa.", fr: "Contactez le conseiller ICAT au 90123456." }
            },
            "mina": {
                "status_semer": { text: "Míatɛŋ ado nuku fifia. Tsi dza gbaŋgbaŋ le anyigba.", fr: "Vous pouvez semer dès maintenant. Bonne humidité du sol." },
                "status_attendre": { text: "Migado nuku o. Tsi megakpɔ dza nyuie o.", fr: "Ne semez pas encore. Attendez une nouvelle pluie continue." },
                "status_risque": { text: "Kpoɖoɖo li : Faux départ le agblea me.", fr: "Attention : risque de faux départ pluvieux." },
                "variety_recommendation": { text: "Do variety TZEE-W-Pop le ŋkeke blaenyi me.", fr: "Variété précoce recommandée pour sécuriser la récolte." },
                "call_agent": { text: "Yɔ ICAT tɔ le 90123456 jí.", fr: "Consultez l'agent ICAT de votre préfecture." }
            },
            "francais": {
                "status_semer": { text: "Avis favorable pour semer. La réserve hydrique du sol dépasse le seuil critique.", fr: "Avis favorable pour semer immédiatement." },
                "status_attendre": { text: "Attendez avant de semer. Le sol est trop sec pour garantir la levée des graines.", fr: "Humidité insuffisante." },
                "status_risque": { text: "Alerte agro-météo : risque élevé de faux départ. Pause sèche probable.", fr: "Sécheresse précoce détectée." },
                "variety_recommendation": { text: "Semez la variété précoce certifiée ITRA à cycle court 85 jours.", fr: "Variété à haut rendement adaptée." },
                "call_agent": { text: "Faites un bip au 90123456 pour être rappelé gratuitement par votre agent ICAT.", fr: "Assistance technique gratuite." }
            }
        };

        let currentRatings = { clarity: 5, naturalness: 5, authenticity: 5 };
        let audioContext = null;

        function setRating(metric, score) {
            currentRatings[metric] = score;
            document.getElementById(metric + '-score-label').textContent = score + '/5';
            
            // Highlight star icons
            const container = document.getElementById(metric + '-stars');
            const labels = container.querySelectorAll('label');
            labels.forEach((lbl, idx) => {
                if (idx < score) {
                    lbl.className = 'cursor-pointer text-amber-400 text-lg';
                } else {
                    lbl.className = 'cursor-pointer text-slate-300 hover:text-amber-400 text-lg';
                }
            });
        }

        function onLanguageChange() {
            updatePromptPreview();
            loadEvaluationSummary();
        }

        function updatePromptPreview() {
            const lang = document.getElementById('eval-lang').value;
            const clip = document.getElementById('eval-clip').value;
            const item = (promptBank[lang] && promptBank[lang][clip]) || { text: 'Phrase en cours d\'enregistrement...', fr: '' };
            
            document.getElementById('prompt-clip-tag').textContent = clip + ' • ' + lang;
            document.getElementById('prompt-text-display').textContent = '"' + item.text + '"';
            document.getElementById('prompt-meaning-display').textContent = 'Sens : « ' + item.fr + ' »';
        }

        function playAudioAudit() {
            const lang = document.getElementById('eval-lang').value;
            const clip = document.getElementById('eval-clip').value;
            const item = (promptBank[lang] && promptBank[lang][clip]) || { text: '' };
            const statusBadge = document.getElementById('player-status-badge');
            const useFilter = document.getElementById('phone-filter-toggle').checked;

            statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold animate-pulse';
            statusBadge.textContent = useFilter ? '📞 Lecture 2G GSM (Filtre actif)' : '🔊 Lecture Audio Direct';

            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(item.text);
                utterance.lang = lang === 'francais' ? 'fr-FR' : 'fr-FR';
                utterance.rate = useFilter ? 0.95 : 1.0;
                utterance.pitch = useFilter ? 1.15 : 1.0;

                utterance.onend = () => {
                    statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium';
                    statusBadge.textContent = 'Terminé';
                };
                window.speechSynthesis.speak(utterance);
            }
        }

        function stopAudioAudit() {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
            const statusBadge = document.getElementById('player-status-badge');
            statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium';
            statusBadge.textContent = 'Arrêté';
        }

        async function submitEvaluation(e) {
            e.preventDefault();
            const submitBtn = document.getElementById('btn-submit-eval');
            const msgBox = document.getElementById('eval-submit-msg');
            submitBtn.disabled = true;

            const payload = {
                clip_id: document.getElementById('eval-clip').value,
                language: document.getElementById('eval-lang').value,
                evaluator_name: document.getElementById('evaluator-name').value.trim() || 'Anonyme',
                evaluator_origin_region: document.getElementById('evaluator-region').value,
                clarity_rating: currentRatings.clarity,
                naturalness_rating: currentRatings.naturalness,
                accent_authenticity_rating: currentRatings.authenticity,
                comprehension_check_passed: document.querySelector('input[name="comprehension"]:checked').value === "1",
                comments: document.getElementById('eval-comments').value.trim()
            };

            try {
                const res = await fetch('/api/audio-eval', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    msgBox.className = 'p-2.5 rounded-lg text-xs font-semibold text-center bg-emerald-100 text-emerald-800 border border-emerald-300';
                    msgBox.textContent = '✓ Évaluation enregistrée avec succès (ID #' + data.evaluation_id + ') !';
                    msgBox.classList.remove('hidden');
                    document.getElementById('eval-comments').value = '';
                    loadEvaluationSummary();
                } else {
                    throw new Error(data.detail || 'Erreur lors de l\'enregistrement');
                }
            } catch (err) {
                msgBox.className = 'p-2.5 rounded-lg text-xs font-semibold text-center bg-red-100 text-red-800 border border-red-300';
                msgBox.textContent = 'Erreur : ' + err.message;
                msgBox.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
                setTimeout(() => { msgBox.classList.add('hidden'); }, 4000);
            }
        }

        async function loadEvaluationSummary() {
            try {
                const res = await fetch('/api/audio-eval/summary');
                const data = await res.json();
                renderSummaryCards(data);
            } catch (e) {
                console.error('Erreur chargement summary:', e);
            }

            try {
                const res = await fetch('/api/audio-eval/list?limit=10');
                const list = await res.json();
                renderRecentReviews(list);
            } catch (e) {
                console.error('Erreur chargement reviews:', e);
            }
        }

        function renderSummaryCards(data) {
            const container = document.getElementById('summary-cards-container');
            const langs = [
                { key: 'ewe', label: 'Éwé (Eʋegbe)', icon: '🌾' },
                { key: 'kabiye', label: 'Kabiyè', icon: '⛰️' },
                { key: 'mina', label: 'Mina (Gɛ̀ngbe)', icon: '🌊' },
                { key: 'francais', label: 'Français Facile', icon: '📢' }
            ];

            const byLang = data.by_language || {};
            let html = '';

            langs.forEach(l => {
                const item = byLang[l.key] || { count: 0, avg_clarity: 0, avg_naturalness: 0, avg_authenticity: 0, comprehension_rate_pct: 0, mean_overall_score: 0 };
                const countBadge = item.count > 0 ? `<span class="bg-indigo-100 text-indigo-800 text-[10px] font-bold px-2 py-0.5 rounded-full">${item.count} avis</span>` : `<span class="text-slate-400 text-[10px]">0 avis</span>`;
                
                html += `
                    <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col gap-2 hover:border-indigo-300 transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span>${l.icon}</span>
                                <span class="text-xs font-bold text-slate-900">${l.label}</span>
                            </div>
                            <div class="flex items-center gap-2">
                                ${countBadge}
                                <span class="text-xs font-extrabold text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">★ ${item.mean_overall_score}/5</span>
                            </div>
                        </div>
                        <div class="grid grid-cols-4 gap-1.5 text-center text-[10px]">
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Clarté</span>
                                <span class="font-bold text-slate-800">${item.avg_clarity || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Naturel</span>
                                <span class="font-bold text-slate-800">${item.avg_naturalness || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Accent</span>
                                <span class="font-bold text-slate-800">${item.avg_authenticity || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Compris</span>
                                <span class="font-bold ${item.comprehension_rate_pct >= 80 ? 'text-emerald-700' : 'text-slate-800'}">${item.comprehension_rate_pct ? item.comprehension_rate_pct + '%' : '—'}</span>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
        }

        function renderRecentReviews(list) {
            const container = document.getElementById('recent-reviews-list');
            document.getElementById('eval-count-badge').textContent = list.length + ' avis';
            if (!list || list.length === 0) {
                container.innerHTML = '<div class="text-center py-6 text-xs text-slate-400">Aucune évaluation enregistrée pour le moment.</div>';
                return;
            }

            let html = '';
            list.slice(0, 8).forEach(r => {
                const compBadge = r.comprehension_check_passed ? '<span class="text-emerald-700 font-bold text-[10px] bg-emerald-50 px-1.5 py-0.5 rounded">Compris</span>' : '<span class="text-red-700 font-bold text-[10px] bg-red-50 px-1.5 py-0.5 rounded">Ambigu</span>';
                html += `
                    <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex flex-col gap-1">
                        <div class="flex items-center justify-between text-[11px]">
                            <span class="font-bold text-slate-900">${r.evaluator_name || 'Anonyme'} (${r.evaluator_origin_region || 'Maritime'})</span>
                            <span class="text-slate-400">${r.language.toUpperCase()} • ${r.clip_id}</span>
                        </div>
                        <div class="flex items-center gap-3 text-[11px] text-slate-600">
                            <span>Clarté : <b class="text-amber-600">${r.clarity_rating}/5</b></span>
                            <span>Naturel : <b class="text-amber-600">${r.naturalness_rating}/5</b></span>
                            <span>Accent : <b class="text-amber-600">${r.accent_authenticity_rating}/5</b></span>
                            ${compBadge}
                        </div>
                        ${r.comments ? `<p class="text-[11px] text-slate-500 italic bg-white p-1.5 rounded border border-slate-100">« ${r.comments} »</p>` : ''}
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        // Init
        updatePromptPreview();
        setRating('clarity', 5);
        setRating('naturalness', 5);
        setRating('authenticity', 5);
        loadEvaluationSummary();
    </script>
</body>
</html>"""


def render_audio_recorder_html() -> str:
    return """<!DOCTYPE html>
<html lang="fr" class="h-full bg-slate-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraFarm — Kit d'Enregistrement Vocal Locutrices</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .recording-pulse { animation: pulse 1.5s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.05); }
        }
    </style>
</head>
<body class="h-full flex flex-col font-sans text-slate-800">

    <!-- Header -->
    <header class="bg-indigo-900 text-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-indigo-800 flex items-center justify-center text-indigo-200 text-xl font-bold border border-indigo-700">
                    🎙️
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h1 class="text-xl font-bold tracking-tight">AuraFarm &bull; Studio Vocale Terroir</h1>
                        <span class="text-xs bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded-full font-medium">Étape E1</span>
                    </div>
                    <p class="text-xs text-indigo-200 font-light">Enregistrement des phrases modulaires authentiques (Éwé, Kabiyè, Mina, Français)</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="/api/audio/export-csv" class="inline-flex items-center gap-2 bg-indigo-700 hover:bg-indigo-600 text-white font-medium px-3 py-2 rounded-lg text-xs border border-indigo-600 transition">
                    <i class="fa-solid fa-file-csv"></i>
                    <span>Télécharger CSV Traduction</span>
                </a>
                <a href="/dashboard" class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white font-medium px-3 py-2 rounded-lg text-xs transition">
                    <i class="fa-solid fa-arrow-left"></i>
                    <span>Tableau de Bord</span>
                </a>
            </div>
        </div>
    </header>

    <!-- Main Workspace -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">

        <!-- Speaker Info & Consent Box -->
        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div class="flex-1 flex flex-col gap-3">
                <h2 class="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-id-card text-indigo-600"></i> Fiche Locutrice & Consentement Éclairé (Loi Togolaise 2019-014)
                </h2>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Identifiant Locutrice (ex: Afia_Lome / Kossiwa_Tsevie)</label>
                        <input type="text" id="speaker-id" value="Locutrice_01" class="w-full text-xs border border-slate-300 rounded px-3 py-2 bg-slate-50 font-medium focus:bg-white focus:outline-indigo-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Langue de l'enregistrement</label>
                        <select id="select-language" onchange="loadPhraseBank()" class="w-full text-xs border border-slate-300 rounded px-3 py-2 bg-slate-50 font-bold text-indigo-900 focus:bg-white">
                            <option value="ewe">Eʋegbe (Éwé - Sud / Maritime / Plateaux)</option>
                            <option value="kabiye">Kabɩyɛ (Kabiyè - Nord / Kara / Savanes / Centrale)</option>
                            <option value="mina">Mina (Gẽ - Littoral / Lacs)</option>
                            <option value="francais">Français (Référence nationale)</option>
                        </select>
                    </div>
                </div>
                <div class="mt-1 flex items-start gap-2">
                    <input type="checkbox" id="consent-check" checked class="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500">
                    <label for="consent-check" class="text-xs text-slate-600 leading-tight">
                        <strong>Consentement explicite :</strong> J'autorise librement l'enregistrement de ma voix et son utilisation comme clips de référence pour la diffusion des alertes agricoles gratuites AuraFarm au Togo.
                    </label>
                </div>
            </div>

            <!-- Guidelines Box -->
            <div class="w-full md:w-80 bg-indigo-50 border border-indigo-100 rounded-lg p-3.5 text-xs text-indigo-950 flex flex-col gap-1.5">
                <span class="font-bold flex items-center gap-1 text-indigo-800">
                    <i class="fa-solid fa-circle-info"></i> Consignes d'enregistrement :
                </span>
                <ul class="list-disc list-inside space-y-1 text-[11px] text-indigo-900">
                    <li>Parler posément et distinctement (téléphone 2G).</li>
                    <li>Phrases courtes (≤ 10 mots) avec l'information clé en premier.</li>
                    <li>Laisser 0.5s de silence avant et après chaque phrase.</li>
                </ul>
            </div>
        </div>

        <!-- Filter Bar -->
        <div class="flex flex-wrap items-center justify-between gap-4">
            <div class="flex flex-wrap items-center gap-2" id="filter-buttons">
                <button onclick="filterCategory('all')" class="cat-btn active text-xs px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-semibold">Toutes (56)</button>
                <button onclick="filterCategory('status')" class="cat-btn text-xs px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 font-medium hover:bg-slate-50">Statuts d'alerte</button>
                <button onclick="filterCategory('crop')" class="cat-btn text-xs px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 font-medium hover:bg-slate-50">Cultures</button>
                <button onclick="filterCategory('variety')" class="cat-btn text-xs px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 font-medium hover:bg-slate-50">Variétés ITRA</button>
                <button onclick="filterCategory('number')" class="cat-btn text-xs px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 font-medium hover:bg-slate-50">Nombres 0–31</button>
                <button onclick="filterCategory('instruction')" class="cat-btn text-xs px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 font-medium hover:bg-slate-50">Consignes IVR</button>
            </div>
            <div class="text-xs text-slate-500 font-mono">
                <span id="stat-recorded" class="font-bold text-amber-600">0</span> enregistrées &bull; 
                <span id="stat-validated" class="font-bold text-emerald-600">0</span> validées &bull; 
                <span id="stat-missing" class="font-bold text-slate-400">0</span> manquantes
            </div>
        </div>

        <!-- Phrases Table -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-xs text-left border-collapse">
                    <thead>
                        <tr class="bg-slate-100 border-b border-slate-200 text-slate-700">
                            <th class="p-3 font-semibold w-24">Code</th>
                            <th class="p-3 font-semibold w-24">Catégorie</th>
                            <th class="p-3 font-semibold">Texte à prononcer (Langue sélectionnée)</th>
                            <th class="p-3 font-semibold w-36">Référence FR</th>
                            <th class="p-3 font-semibold w-24 text-center">Statut</th>
                            <th class="p-3 font-semibold w-56 text-right">Action micro / Envoi</th>
                        </tr>
                    </thead>
                    <tbody id="phrases-tbody">
                        <tr>
                            <td colspan="6" class="p-8 text-center text-slate-400">
                                <i class="fa-solid fa-spinner fa-spin text-xl"></i>
                                <p class="mt-2 text-xs">Chargement de la banque de phrases...</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </main>

    <footer class="bg-white border-t border-slate-200 py-3 text-center text-xs text-slate-500">
        AuraFarm Studio Vocale &bull; Étape E1 Kit d'enregistrement locutrices &bull; Conformité Loi Togolaise N° 2019-014
    </footer>

    <script>
        let allPhrases = [];
        let activeCategory = 'all';
        let mediaRecorder = null;
        let audioChunks = {};
        let recordedBlobs = {};
        let activeRecordingPhraseId = null;

        async function loadPhraseBank() {
            const lang = document.getElementById('select-language').value;
            const res = await fetch(`/api/audio/phrases?lang=${lang}`);
            const data = await res.json();
            allPhrases = data.phrases;
            updateStats();
            renderTable();
        }

        function updateStats() {
            let missing = 0, recorded = 0, validated = 0;
            allPhrases.forEach(p => {
                if (p.status === 'valide') validated++;
                else if (p.status === 'enregistre') recorded++;
                else missing++;
            });
            document.getElementById('stat-missing').textContent = missing;
            document.getElementById('stat-recorded').textContent = recorded;
            document.getElementById('stat-validated').textContent = validated;
        }

        function filterCategory(cat) {
            activeCategory = cat;
            document.querySelectorAll('.cat-btn').forEach(btn => {
                btn.className = 'cat-btn text-xs px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 font-medium hover:bg-slate-50';
            });
            event.target.className = 'cat-btn active text-xs px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-semibold';
            renderTable();
        }

        function renderTable() {
            const tbody = document.getElementById('phrases-tbody');
            const lang = document.getElementById('select-language').value;

            const filtered = activeCategory === 'all' 
                ? allPhrases 
                : allPhrases.filter(p => p.category === activeCategory);

            tbody.innerHTML = filtered.map(p => {
                let statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500 border border-slate-200">MANQUANT</span>';
                if (p.status === 'enregistre') {
                    statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">ENREGISTRÉ</span>';
                } else if (p.status === 'valide') {
                    statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">VALIDÉ</span>';
                }

                const isRecording = activeRecordingPhraseId === p.phrase_id;
                const hasBlob = !!recordedBlobs[p.phrase_id];

                return `
                <tr class="border-b border-slate-100 hover:bg-slate-50 transition">
                    <td class="p-3 font-mono font-bold text-slate-700">${p.phrase_id}</td>
                    <td class="p-3 font-semibold text-slate-500">${p.category}</td>
                    <td class="p-3">
                        <div class="text-sm font-bold text-indigo-950">${p.text_to_read}</div>
                        ${p.notes ? `<div class="text-[11px] text-slate-400 mt-0.5 italic">${p.notes}</div>` : ''}
                    </td>
                    <td class="p-3 text-slate-600 italic">
                        "${p.french_text}"
                        <span class="block text-[10px] text-slate-400 font-mono">(${p.word_count_fr} mots)</span>
                    </td>
                    <td class="p-3 text-center">${statusBadge}</td>
                    <td class="p-3 text-right">
                        <div class="flex items-center justify-end gap-1.5">
                            ${!isRecording ? `
                                <button onclick="startRecording('${p.phrase_id}')" class="px-2.5 py-1 rounded bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold border border-indigo-200 flex items-center gap-1">
                                    <i class="fa-solid fa-microphone"></i> Rec
                                </button>
                            ` : `
                                <button onclick="stopRecording('${p.phrase_id}')" class="px-2.5 py-1 rounded bg-red-600 text-white font-bold recording-pulse flex items-center gap-1">
                                    <i class="fa-solid fa-stop"></i> Arrêt
                                </button>
                            `}

                            ${hasBlob ? `
                                <button onclick="playLocalClip('${p.phrase_id}')" class="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700" title="Écouter">
                                    <i class="fa-solid fa-play"></i>
                                </button>
                                <button onclick="uploadClip('${p.phrase_id}')" class="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold" title="Transmettre">
                                    <i class="fa-solid fa-cloud-arrow-up"></i> Sauver
                                </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
                `;
            }).join('');
        }

        async function startRecording(phraseId) {
            const consent = document.getElementById('consent-check').checked;
            if (!consent) {
                alert("Veuillez cocher la case de consentement de la locutrice avant tout enregistrement.");
                return;
            }

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                audioChunks[phraseId] = [];
                mediaRecorder = new MediaRecorder(stream);
                activeRecordingPhraseId = phraseId;

                mediaRecorder.ondataavailable = e => {
                    if (e.data.size > 0) audioChunks[phraseId].push(e.data);
                };

                mediaRecorder.onstop = () => {
                    const blob = new Blob(audioChunks[phraseId], { type: 'audio/webm' });
                    recordedBlobs[phraseId] = blob;
                    activeRecordingPhraseId = null;
                    renderTable();
                };

                mediaRecorder.start();
                renderTable();
            } catch (err) {
                alert("Microphone inaccessible : " + err.message);
            }
        }

        function stopRecording(phraseId) {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
        }

        function playLocalClip(phraseId) {
            const blob = recordedBlobs[phraseId];
            if (blob) {
                const audio = new Audio(URL.createObjectURL(blob));
                audio.play();
            }
        }

        async function uploadClip(phraseId) {
            const blob = recordedBlobs[phraseId];
            if (!blob) return;

            const speakerId = document.getElementById('speaker-id').value.trim() || 'Locutrice';
            const lang = document.getElementById('select-language').value;
            const consent = document.getElementById('consent-check').checked ? '1' : '0';

            const formData = new FormData();
            formData.append('phrase_id', phraseId);
            formData.append('language', lang);
            formData.append('speaker_id', speakerId);
            formData.append('consent_given', consent);
            formData.append('audio_file', blob, `${phraseId}_${speakerId}.webm`);

            try {
                const res = await fetch('/api/audio/upload', { method: 'POST', body: formData });
                const data = await res.json();
                if (data.status === 'SUCCESS') {
                    // Refresh phrase bank
                    await loadPhraseBank();
                    delete recordedBlobs[phraseId];
                    renderTable();
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch (e) {
                alert('Erreur lors du transfert audio.');
            }
        }

        // Init
        loadPhraseBank();
    </script>
</body>
</html>"""


def render_audio_eval_html() -> str:
    """HTML evaluation studio for native speakers and juries (Step E10)."""
    return """<!DOCTYPE html>
<html lang="fr" class="h-full bg-slate-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraFarm — Évaluation Vocale Terroir (Locuteurs Natifs)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="h-full flex flex-col font-sans text-slate-800">

    <!-- Header -->
    <header class="bg-indigo-950 text-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-indigo-900 flex items-center justify-center text-indigo-300 text-xl font-bold border border-indigo-700">
                    🎙️
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h1 class="text-xl font-bold tracking-tight">AuraFarm • Évaluation Vocale Terroir</h1>
                        <span class="text-xs bg-indigo-800 text-indigo-200 px-2.5 py-0.5 rounded-full font-semibold border border-indigo-600">Étape E10</span>
                    </div>
                    <p class="text-xs text-indigo-300 font-light">Validation d'intelligibilité, de clarté 2G et d'accent authentique (Éwé, Kabiyè, Mina, FR)</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="/dashboard" class="inline-flex items-center gap-2 bg-indigo-900 hover:bg-indigo-800 text-white text-xs px-3.5 py-2 rounded-lg border border-indigo-700 transition">
                    <i class="fa-solid fa-arrow-left"></i>
                    <span>Dashboard Principal</span>
                </a>
                <a href="/audio-recorder" class="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-600 text-white text-xs px-3.5 py-2 rounded-lg font-medium transition">
                    <i class="fa-solid fa-microphone"></i>
                    <span>Studio d'Enregistrement (E1)</span>
                </a>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">

        <!-- Banner Context & Methodology -->
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div class="flex items-start gap-3.5">
                <div class="p-3 rounded-xl bg-indigo-100 text-indigo-800 text-lg">
                    <i class="fa-solid fa-headphones-simple"></i>
                </div>
                <div>
                    <h2 class="text-sm font-bold text-slate-900">Protocole d'Évaluation de la Voix Rurale (Hackathon 2026)</h2>
                    <p class="text-xs text-slate-600 mt-0.5 max-w-3xl leading-relaxed">
                        Pour garantir qu'un producteur agricole en zone blanche comprenne immédiatement l'alerte agro-climatique via son combiné basique, chaque phrase modulaire est soumise au test de la voix du terroir : clarté sous compression téléphonique 2G (300-3400 Hz), fluidité sans robotisation, et respect strict de l'accentuation régionale.
                    </p>
                </div>
            </div>
            <div class="flex items-center gap-2 bg-indigo-50 border border-indigo-200 px-3.5 py-2 rounded-xl text-xs text-indigo-900">
                <i class="fa-solid fa-shield-halved text-indigo-600"></i>
                <span>Loi Togolaise N° 2019-014 • Anonymat Garanti</span>
            </div>
        </div>

        <!-- Evaluation Grid: Left Form & Audio Player / Right Live Aggregate Metrics -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

            <!-- Left Form & Player (7 cols) -->
            <div class="lg:col-span-7 flex flex-col gap-5">
                
                <!-- Audio Audition Player Card -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">1. Choix du Clip & Écoute</h3>
                        </div>
                        <span id="player-status-badge" class="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">Prêt</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Langue ciblée</label>
                            <select id="eval-lang" onchange="onLanguageChange()" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="ewe">Éwé (Eʋegbe) — Sud / Plateaux / Maritime</option>
                                <option value="kabiye">Kabiyè — Kara / Centrale</option>
                                <option value="mina">Mina (Gɛ̀ngbe) — Littoral / Golfe / Lacs</option>
                                <option value="francais">Français Facile — National</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Phrase ou consigne à auditer</label>
                            <select id="eval-clip" onchange="updatePromptPreview()" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="status_semer">Statut SEMER (Alerte favorable)</option>
                                <option value="status_attendre">Statut ATTENDRE (Sol trop sec / faux départ)</option>
                                <option value="status_risque">Statut RISQUE (Sécheresse précoce)</option>
                                <option value="variety_recommendation">Recommandation Variété (Cycle court)</option>
                                <option value="call_agent">Consigne Agent d'appui ICAT</option>
                            </select>
                        </div>
                    </div>

                    <!-- Prompt Display -->
                    <div class="bg-indigo-900 text-indigo-100 p-4 rounded-xl border border-indigo-800 flex flex-col gap-2">
                        <div class="flex items-center justify-between text-xs text-indigo-300 font-mono">
                            <span>TRANSCRIPTION LOCALE OFFICIELLE</span>
                            <span id="prompt-clip-tag">status_semer • ewe</span>
                        </div>
                        <p id="prompt-text-display" class="text-sm font-semibold italic text-white leading-relaxed">
                            "Míele gbeƒã ɖem na mi be míate ŋu aƒã nuku fifia. Tsi dza sɔgbɔ."
                        </p>
                        <p id="prompt-meaning-display" class="text-xs text-indigo-200 border-t border-indigo-800/60 pt-1.5">
                            Traduction FR : « Avis favorable pour semer. La réserve hydrique du sol est suffisante. »
                        </p>
                    </div>

                    <!-- 2G Telephone Filter Simulator Toggle -->
                    <div class="bg-amber-50 border border-amber-200 p-3.5 rounded-xl flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2.5">
                            <i class="fa-solid fa-phone-volume text-amber-600 text-lg"></i>
                            <div>
                                <p class="text-xs font-bold text-amber-900">Simulation Filtre Haut-Parleur Téléphone 2G</p>
                                <p class="text-[11px] text-amber-800">Bande passante GSM (300-3400 Hz) + compression 8 kHz</p>
                            </div>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" id="phone-filter-toggle" class="sr-only peer" checked>
                            <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-600"></div>
                        </label>
                    </div>

                    <!-- Audio Controls -->
                    <div class="flex flex-wrap items-center gap-3 pt-1">
                        <button onclick="playAudioAudit()" id="btn-play-audio" class="flex-1 inline-flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2.5 rounded-xl text-xs shadow transition">
                            <i class="fa-solid fa-play"></i>
                            <span>Écouter l'Extrait Vocal</span>
                        </button>
                        <button onclick="stopAudioAudit()" class="inline-flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-4 py-2.5 rounded-xl text-xs transition border border-slate-300">
                            <i class="fa-solid fa-stop"></i>
                            <span>Arrêter</span>
                        </button>
                    </div>
                </div>

                <!-- Evaluation Scoring Form -->
                <form id="evaluation-form" onsubmit="submitEvaluation(event)" class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">2. Grille de Notation par l'Évaluateur</h3>
                        </div>
                        <span class="text-xs text-slate-500 italic">* Tous les critères sont obligatoires</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Nom ou Pseudonyme de l'auditeur</label>
                            <input type="text" id="evaluator-name" placeholder="Ex: M. Koffi / Évaluateur Juré" required class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Région d'origine / Attachement</label>
                            <select id="evaluator-region" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="Maritime">Région Maritime (Zio, Yoto, Vo, Golfe)</option>
                                <option value="Plateaux">Région des Plateaux (Kloto, Ogou, Haho)</option>
                                <option value="Centrale">Région Centrale (Tchaoudjo, Sotouboua)</option>
                                <option value="Kara">Région de la Kara (Kozah, Assoli, Doufelgou)</option>
                                <option value="Savanes">Région des Savanes (Tône, Oti, Kpendjal)</option>
                            </select>
                        </div>
                    </div>

                    <!-- Criteria Sliders / Stars -->
                    <div class="flex flex-col gap-3 pt-2">
                        
                        <!-- Criterion 1: Clarity -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">1. Clarté & Intelligibilité sonore</span>
                                    <p class="text-[11px] text-slate-500">Même avec le bruit de fond ou sur haut-parleur bon marché</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="clarity-stars">
                                    <!-- 5 star radio inputs -->
                                    <input type="radio" name="clarity" value="1" id="c1" class="hidden peer/c1">
                                    <label for="c1" onclick="setRating('clarity', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c1:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="2" id="c2" class="hidden peer/c2">
                                    <label for="c2" onclick="setRating('clarity', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c2:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="3" id="c3" class="hidden peer/c3">
                                    <label for="c3" onclick="setRating('clarity', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c3:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="4" id="c4" class="hidden peer/c4">
                                    <label for="c4" onclick="setRating('clarity', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c4:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="5" id="c5" checked class="hidden peer/c5">
                                    <label for="c5" onclick="setRating('clarity', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c5:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <span id="clarity-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 2: Naturalness -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">2. Fluidité & Naturel du débit</span>
                                    <p class="text-[11px] text-slate-500">Cadence naturelle, absence d'artéfacts ou de saccades robotiques</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="naturalness-stars">
                                    <input type="radio" name="naturalness" value="1" id="n1" class="hidden">
                                    <label for="n1" onclick="setRating('naturalness', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="2" id="n2" class="hidden">
                                    <label for="n2" onclick="setRating('naturalness', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="3" id="n3" class="hidden">
                                    <label for="n3" onclick="setRating('naturalness', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="4" id="n4" class="hidden">
                                    <label for="n4" onclick="setRating('naturalness', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="5" id="n5" checked class="hidden">
                                    <label for="n5" onclick="setRating('naturalness', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <span id="naturalness-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 3: Accent Authenticity -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">3. Authenticité de l'accent du terroir</span>
                                    <p class="text-[11px] text-slate-500">Ton respectueux et naturel pour un producteur de la zone</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="authenticity-stars">
                                    <input type="radio" name="authenticity" value="1" id="a1" class="hidden">
                                    <label for="a1" onclick="setRating('authenticity', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="2" id="a2" class="hidden">
                                    <label for="a2" onclick="setRating('authenticity', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="3" id="a3" class="hidden">
                                    <label for="a3" onclick="setRating('authenticity', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="4" id="a4" class="hidden">
                                    <label for="a4" onclick="setRating('authenticity', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="5" id="a5" checked class="hidden">
                                    <label for="a5" onclick="setRating('authenticity', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <span id="authenticity-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 4: Immediate Comprehension Test -->
                        <div class="p-3.5 bg-indigo-50/60 rounded-xl border border-indigo-200 flex items-center justify-between">
                            <div>
                                <span class="text-xs font-bold text-indigo-950">4. Test de compréhension immédiate sans hésitation</span>
                                <p class="text-[11px] text-indigo-800">L'agriculteur sait-il exactement quoi faire dès la première écoute ?</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <label class="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-800 cursor-pointer">
                                    <input type="radio" name="comprehension" value="1" checked class="text-emerald-600 focus:ring-emerald-500">
                                    <span>Oui (Compris)</span>
                                </label>
                                <label class="inline-flex items-center gap-1.5 text-xs font-bold text-red-700 cursor-pointer ml-2">
                                    <input type="radio" name="comprehension" value="0" class="text-red-600 focus:ring-red-500">
                                    <span>Non (Ambigu)</span>
                                </label>
                            </div>
                        </div>

                    </div>

                    <!-- Comments -->
                    <div>
                        <label class="block text-xs font-semibold text-slate-700 mb-1">Commentaires qualitatifs & suggestions d'amélioration</label>
                        <textarea id="eval-comments" rows="2" placeholder="Ex: Débit un peu rapide sur le deuxième mot, sinon intonation parfaite pour la Kara." class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"></textarea>
                    </div>

                    <button type="submit" id="btn-submit-eval" class="w-full inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2.5 rounded-xl text-xs shadow transition">
                        <i class="fa-solid fa-circle-check"></i>
                        <span>Enregistrer l'Évaluation Vocale</span>
                    </button>
                    <div id="eval-submit-msg" class="hidden p-2.5 rounded-lg text-xs font-semibold text-center"></div>
                </form>

            </div>

            <!-- Right Dashboard: Live Evaluation Metrics & History (5 cols) -->
            <div class="lg:col-span-5 flex flex-col gap-5">
                
                <!-- Scorecards per Language -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">Moyennes de Validation par Langue</h3>
                        </div>
                        <button onclick="loadEvaluationSummary()" class="text-xs text-indigo-600 hover:underline flex items-center gap-1 font-semibold">
                            <i class="fa-solid fa-arrows-rotate"></i> Actualiser
                        </button>
                    </div>

                    <div id="summary-cards-container" class="flex flex-col gap-3">
                        <!-- Populated dynamically via JS -->
                        <div class="text-center py-6 text-xs text-slate-400">Chargement des indicateurs...</div>
                    </div>
                </div>

                <!-- Recent Feedback Stream -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-3">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">Dernières Évaluations Soumises</h3>
                        </div>
                        <span id="eval-count-badge" class="text-xs bg-slate-100 text-slate-700 font-bold px-2 py-0.5 rounded-full">0 avis</span>
                    </div>

                    <div id="recent-reviews-list" class="flex flex-col gap-2.5 max-h-[380px] overflow-y-auto pr-1">
                        <!-- Populated dynamically via JS -->
                        <div class="text-center py-6 text-xs text-slate-400">Aucune évaluation enregistrée pour le moment.</div>
                    </div>
                </div>

            </div>

        </div>

    </main>

    <footer class="bg-white border-t border-slate-200 mt-auto py-4 text-center text-xs text-slate-500">
        AuraFarm &bull; Hackathon Climat & Innovation 2026 &bull; Équipe GPS² (Togolaises In Science)
    </footer>

    <script>
        // State
        const promptBank = {
            "ewe": {
                "status_semer": { text: "Míele gbeƒã ɖem na mi be míate ŋu aƒã nuku fifia. Tsi dza sɔgbɔ.", fr: "Avis favorable pour semer. La réserve hydrique du sol est suffisante." },
                "status_attendre": { text: "Migalɔ̃ aƒã nuku o. Manyo fifia o, tsi medza sɔgbɔ o.", fr: "Attendez avant de semer. Humidité du sol insuffisante." },
                "status_risque": { text: "Nyanyanyɛ : Nuɖuɖu ƒe nɔnɔme gblẽ. Faux départ le dzɔdzɔm.", fr: "Risque élevé de faux départ de saison. Ne pas semer." },
                "variety_recommendation": { text: "Míedo kpɔ̃ TZEE-W-Pop miadze aƒã na ŋkeke blaenyi.", fr: "Semez la variété précoce TZEE-W-Pop adaptée à la durée de pluie." },
                "call_agent": { text: "Bip 90123456 ne ICAT ƒe agbledɔwɔla aƒo nu na wò.", fr: "Faites un bip au 90123456 pour parler à un agent ICAT." }
            },
            "kabiye": {
                "status_semer": { text: "Pɩwɛ ɖeu se ŋdu kɛlɛʊ nɔɔnɔɔ. Tɛʊ nɩwa pɩtɩŋa.", fr: "Vous pouvez semer maintenant. Pluie adéquate constatée." },
                "status_attendre": { text: "Taadʊ kɛlɛʊ nɔɔnɔɔ. Ðaŋ tɛʊ nɩʊ nɔɔnɔɔ.", fr: "Attendez encore avant les semis. Humidité insuffisante." },
                "status_risque": { text: "Kigbɛɖɛɛ wɛɛ : tɛʊ kaɣ hɛʊ kpaagbaa.", fr: "Alerte : risque critique de sécheresse précoce." },
                "variety_recommendation": { text: "Du Sotubua tɛ nuku ŋgʊ kɩtɛŋ lɔŋ yɔ.", fr: "Privilégiez la variété précoce recommandée pour votre sol." },
                "call_agent": { text: "Ya ICAT tɔm kɛ 90123456 taa.", fr: "Contactez le conseiller ICAT au 90123456." }
            },
            "mina": {
                "status_semer": { text: "Míatɛŋ ado nuku fifia. Tsi dza gbaŋgbaŋ le anyigba.", fr: "Vous pouvez semer dès maintenant. Bonne humidité du sol." },
                "status_attendre": { text: "Migado nuku o. Tsi megakpɔ dza nyuie o.", fr: "Ne semez pas encore. Attendez une nouvelle pluie continue." },
                "status_risque": { text: "Kpoɖoɖo li : Faux départ le agblea me.", fr: "Attention : risque de faux départ pluvieux." },
                "variety_recommendation": { text: "Do variety TZEE-W-Pop le ŋkeke blaenyi me.", fr: "Variété précoce recommandée pour sécuriser la récolte." },
                "call_agent": { text: "Yɔ ICAT tɔ le 90123456 jí.", fr: "Consultez l'agent ICAT de votre préfecture." }
            },
            "francais": {
                "status_semer": { text: "Avis favorable pour semer. La réserve hydrique du sol dépasse le seuil critique.", fr: "Avis favorable pour semer immédiatement." },
                "status_attendre": { text: "Attendez avant de semer. Le sol est trop sec pour garantir la levée des graines.", fr: "Humidité insuffisante." },
                "status_risque": { text: "Alerte agro-météo : risque élevé de faux départ. Pause sèche probable.", fr: "Sécheresse précoce détectée." },
                "variety_recommendation": { text: "Semez la variété précoce certifiée ITRA à cycle court 85 jours.", fr: "Variété à haut rendement adaptée." },
                "call_agent": { text: "Faites un bip au 90123456 pour être rappelé gratuitement par votre agent ICAT.", fr: "Assistance technique gratuite." }
            }
        };

        let currentRatings = { clarity: 5, naturalness: 5, authenticity: 5 };
        let audioContext = null;

        function setRating(metric, score) {
            currentRatings[metric] = score;
            document.getElementById(metric + '-score-label').textContent = score + '/5';
            
            // Highlight star icons
            const container = document.getElementById(metric + '-stars');
            const labels = container.querySelectorAll('label');
            labels.forEach((lbl, idx) => {
                if (idx < score) {
                    lbl.className = 'cursor-pointer text-amber-400 text-lg';
                } else {
                    lbl.className = 'cursor-pointer text-slate-300 hover:text-amber-400 text-lg';
                }
            });
        }

        function onLanguageChange() {
            updatePromptPreview();
            loadEvaluationSummary();
        }

        function updatePromptPreview() {
            const lang = document.getElementById('eval-lang').value;
            const clip = document.getElementById('eval-clip').value;
            const item = (promptBank[lang] && promptBank[lang][clip]) || { text: 'Phrase en cours d\'enregistrement...', fr: '' };
            
            document.getElementById('prompt-clip-tag').textContent = clip + ' • ' + lang;
            document.getElementById('prompt-text-display').textContent = '"' + item.text + '"';
            document.getElementById('prompt-meaning-display').textContent = 'Sens : « ' + item.fr + ' »';
        }

        function playAudioAudit() {
            const lang = document.getElementById('eval-lang').value;
            const clip = document.getElementById('eval-clip').value;
            const item = (promptBank[lang] && promptBank[lang][clip]) || { text: '' };
            const statusBadge = document.getElementById('player-status-badge');
            const useFilter = document.getElementById('phone-filter-toggle').checked;

            statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold animate-pulse';
            statusBadge.textContent = useFilter ? '📞 Lecture 2G GSM (Filtre actif)' : '🔊 Lecture Audio Direct';

            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(item.text);
                utterance.lang = lang === 'francais' ? 'fr-FR' : 'fr-FR';
                utterance.rate = useFilter ? 0.95 : 1.0;
                utterance.pitch = useFilter ? 1.15 : 1.0;

                utterance.onend = () => {
                    statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium';
                    statusBadge.textContent = 'Terminé';
                };
                window.speechSynthesis.speak(utterance);
            }
        }

        function stopAudioAudit() {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
            const statusBadge = document.getElementById('player-status-badge');
            statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium';
            statusBadge.textContent = 'Arrêté';
        }

        async function submitEvaluation(e) {
            e.preventDefault();
            const submitBtn = document.getElementById('btn-submit-eval');
            const msgBox = document.getElementById('eval-submit-msg');
            submitBtn.disabled = true;

            const payload = {
                clip_id: document.getElementById('eval-clip').value,
                language: document.getElementById('eval-lang').value,
                evaluator_name: document.getElementById('evaluator-name').value.trim() || 'Anonyme',
                evaluator_origin_region: document.getElementById('evaluator-region').value,
                clarity_rating: currentRatings.clarity,
                naturalness_rating: currentRatings.naturalness,
                accent_authenticity_rating: currentRatings.authenticity,
                comprehension_check_passed: document.querySelector('input[name="comprehension"]:checked').value === "1",
                comments: document.getElementById('eval-comments').value.trim()
            };

            try {
                const res = await fetch('/api/audio-eval', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    msgBox.className = 'p-2.5 rounded-lg text-xs font-semibold text-center bg-emerald-100 text-emerald-800 border border-emerald-300';
                    msgBox.textContent = '✓ Évaluation enregistrée avec succès (ID #' + data.evaluation_id + ') !';
                    msgBox.classList.remove('hidden');
                    document.getElementById('eval-comments').value = '';
                    loadEvaluationSummary();
                } else {
                    throw new Error(data.detail || 'Erreur lors de l\'enregistrement');
                }
            } catch (err) {
                msgBox.className = 'p-2.5 rounded-lg text-xs font-semibold text-center bg-red-100 text-red-800 border border-red-300';
                msgBox.textContent = 'Erreur : ' + err.message;
                msgBox.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
                setTimeout(() => { msgBox.classList.add('hidden'); }, 4000);
            }
        }

        async function loadEvaluationSummary() {
            try {
                const res = await fetch('/api/audio-eval/summary');
                const data = await res.json();
                renderSummaryCards(data);
            } catch (e) {
                console.error('Erreur chargement summary:', e);
            }

            try {
                const res = await fetch('/api/audio-eval/list?limit=10');
                const list = await res.json();
                renderRecentReviews(list);
            } catch (e) {
                console.error('Erreur chargement reviews:', e);
            }
        }

        function renderSummaryCards(data) {
            const container = document.getElementById('summary-cards-container');
            const langs = [
                { key: 'ewe', label: 'Éwé (Eʋegbe)', icon: '🌾' },
                { key: 'kabiye', label: 'Kabiyè', icon: '⛰️' },
                { key: 'mina', label: 'Mina (Gɛ̀ngbe)', icon: '🌊' },
                { key: 'francais', label: 'Français Facile', icon: '📢' }
            ];

            const byLang = data.by_language || {};
            let html = '';

            langs.forEach(l => {
                const item = byLang[l.key] || { count: 0, avg_clarity: 0, avg_naturalness: 0, avg_authenticity: 0, comprehension_rate_pct: 0, mean_overall_score: 0 };
                const countBadge = item.count > 0 ? `<span class="bg-indigo-100 text-indigo-800 text-[10px] font-bold px-2 py-0.5 rounded-full">${item.count} avis</span>` : `<span class="text-slate-400 text-[10px]">0 avis</span>`;
                
                html += `
                    <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col gap-2 hover:border-indigo-300 transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span>${l.icon}</span>
                                <span class="text-xs font-bold text-slate-900">${l.label}</span>
                            </div>
                            <div class="flex items-center gap-2">
                                ${countBadge}
                                <span class="text-xs font-extrabold text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">★ ${item.mean_overall_score}/5</span>
                            </div>
                        </div>
                        <div class="grid grid-cols-4 gap-1.5 text-center text-[10px]">
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Clarté</span>
                                <span class="font-bold text-slate-800">${item.avg_clarity || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Naturel</span>
                                <span class="font-bold text-slate-800">${item.avg_naturalness || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Accent</span>
                                <span class="font-bold text-slate-800">${item.avg_authenticity || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Compris</span>
                                <span class="font-bold ${item.comprehension_rate_pct >= 80 ? 'text-emerald-700' : 'text-slate-800'}">${item.comprehension_rate_pct ? item.comprehension_rate_pct + '%' : '—'}</span>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
        }

        function renderRecentReviews(list) {
            const container = document.getElementById('recent-reviews-list');
            document.getElementById('eval-count-badge').textContent = list.length + ' avis';
            if (!list || list.length === 0) {
                container.innerHTML = '<div class="text-center py-6 text-xs text-slate-400">Aucune évaluation enregistrée pour le moment.</div>';
                return;
            }

            let html = '';
            list.slice(0, 8).forEach(r => {
                const compBadge = r.comprehension_check_passed ? '<span class="text-emerald-700 font-bold text-[10px] bg-emerald-50 px-1.5 py-0.5 rounded">Compris</span>' : '<span class="text-red-700 font-bold text-[10px] bg-red-50 px-1.5 py-0.5 rounded">Ambigu</span>';
                html += `
                    <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex flex-col gap-1">
                        <div class="flex items-center justify-between text-[11px]">
                            <span class="font-bold text-slate-900">${r.evaluator_name || 'Anonyme'} (${r.evaluator_origin_region || 'Maritime'})</span>
                            <span class="text-slate-400">${r.language.toUpperCase()} • ${r.clip_id}</span>
                        </div>
                        <div class="flex items-center gap-3 text-[11px] text-slate-600">
                            <span>Clarté : <b class="text-amber-600">${r.clarity_rating}/5</b></span>
                            <span>Naturel : <b class="text-amber-600">${r.naturalness_rating}/5</b></span>
                            <span>Accent : <b class="text-amber-600">${r.accent_authenticity_rating}/5</b></span>
                            ${compBadge}
                        </div>
                        ${r.comments ? `<p class="text-[11px] text-slate-500 italic bg-white p-1.5 rounded border border-slate-100">« ${r.comments} »</p>` : ''}
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        // Init
        updatePromptPreview();
        setRating('clarity', 5);
        setRating('naturalness', 5);
        setRating('authenticity', 5);
        loadEvaluationSummary();
    </script>
</body>
</html>"""


def render_zones_overview_html() -> str:
    """HTML view for Step E2: Agro-Climatic Zone Profiles and Stochastic Weather Simulation."""
    return """<!DOCTYPE html>
<html lang="fr" class="h-full bg-slate-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraFarm — Profils Agro-Climatiques & Simulateur Météo Togo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="h-full flex flex-col font-sans text-slate-800">

    <!-- Top Navigation Bar -->
    <header class="bg-emerald-900 text-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-emerald-800 flex items-center justify-center text-emerald-200 text-xl font-bold border border-emerald-700">
                    🌍
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h1 class="text-xl font-bold tracking-tight">AuraFarm • Profils Agro-Climatiques Régionaux</h1>
                        <span class="text-xs bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded-full font-medium">Étape E2</span>
                    </div>
                    <p class="text-xs text-emerald-200 font-light">Chaîne causale: Climat régional &bull; Régimes pluviométriques &bull; Sols sentinelles &bull; Simulation stochastique</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="/dashboard" class="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-600 text-white font-medium px-3 py-2 rounded-lg text-xs transition">
                    <i class="fa-solid fa-table-columns"></i>
                    <span>Tableau de Bord</span>
                </a>
                <a href="/audio-recorder" class="inline-flex items-center gap-2 bg-indigo-700 hover:bg-indigo-600 text-white font-medium px-3 py-2 rounded-lg text-xs transition">
                    <i class="fa-solid fa-microphone"></i>
                    <span>Studio Vocal (E1)</span>
                </a>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">

        <!-- Intro Banner -->
        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
                <h2 class="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-cloud-sun-rain text-emerald-600"></i> Modélisation Agro-Climatique des 5 Régions du Togo
                </h2>
                <p class="text-xs text-slate-600 mt-1 max-w-3xl">
                    Chaque zone possède ses normales de pluie (loi Gamma), d'occurrences (chaîne de Markov), de températures avec rafraîchissement sous la pluie, et ses régimes (unimodal au nord vs bimodal au sud avec seconde saison marquée <em>« à valider »</em>).
                </p>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="runAllSimulations()" class="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold px-4 py-2 rounded-lg text-xs shadow transition">
                    <i class="fa-solid fa-bolt"></i>
                    <span>Simuler 30 saisons (Toutes zones)</span>
                </button>
            </div>
        </div>

        <!-- 5 Zone Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="zones-container">
            <div class="col-span-full text-center py-8 text-slate-400">
                <i class="fa-solid fa-spinner fa-spin text-2xl"></i>
                <p class="mt-2 text-xs">Chargement des profils de zones...</p>
            </div>
        </div>

        <!-- Simulation Results Panel -->
        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-4">
            <div class="flex items-center justify-between">
                <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <i class="fa-solid fa-chart-line text-amber-600"></i> Résultats de Simulation Stochastique (Markov 1er ordre + Gamma)
                </h3>
                <span class="text-xs text-slate-500 font-mono" id="sim-timestamp">Graine reproductible: 42</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-xs text-left border-collapse">
                    <thead>
                        <tr class="bg-slate-100 border-b border-slate-200 text-slate-700">
                            <th class="p-3 font-semibold">Zone</th>
                            <th class="p-3 font-semibold">Régime</th>
                            <th class="p-3 font-semibold text-right">Pluie Annuelle (Moy ± Écart-type)</th>
                            <th class="p-3 font-semibold text-right">Jours de Pluie</th>
                            <th class="p-3 font-semibold text-center">Date Médiane Semis</th>
                            <th class="p-3 font-semibold text-center">Risque Faux Départ</th>
                            <th class="p-3 font-semibold">Saison 2 (Bimodal)</th>
                        </tr>
                    </thead>
                    <tbody id="sim-tbody">
                        <tr>
                            <td colspan="7" class="p-6 text-center text-slate-400 italic">
                                Cliquez sur « Simuler 30 saisons » pour exécuter le modèle stochastique.
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </main>

    <footer class="bg-white border-t border-slate-200 py-3 text-center text-xs text-slate-500">
        AuraFarm &bull; Étape E2 Profils Régionaux et Générateur Météo Stochastique &bull; Togo Hackathon 2026
    </footer>

    <script>
        let zonesData = [];

        async function loadZones() {
            try {
                const res = await fetch('/api/weather/zones');
                zonesData = await res.json();
                renderZoneCards();
            } catch (e) {
                console.error(e);
            }
        }

        function renderZoneCards() {
            const container = document.getElementById('zones-container');
            container.innerHTML = zonesData.map(z => {
                const isBimodal = z.regime === 'bimodal';
                const villagesList = z.sentinel_villages.map(v => 
                    `<li class="flex justify-between border-b border-slate-100 py-1">
                        <span class="font-medium text-slate-700">${v.village_name}</span>
                        <span class="text-slate-500 font-mono text-[11px]">${v.texture} &bull; TAW ${v.taw_mm_m} mm/m</span>
                    </li>`
                ).join('');

                const s2Badge = isBimodal
                    ? `<span class="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-[10px] font-bold border border-amber-200">S2: dès ${z.season_2_earliest_sowing_date} (${z.season_2_status})</span>`
                    : `<span class="bg-slate-100 text-slate-500 px-2 py-0.5 rounded text-[10px]">Unimodal</span>`;

                return `
                <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex flex-col justify-between gap-3 hover:border-emerald-300 transition">
                    <div>
                        <div class="flex items-start justify-between gap-2">
                            <div>
                                <h3 class="text-sm font-bold text-slate-900">${z.zone_name}</h3>
                                <div class="text-[11px] text-slate-500 font-mono mt-0.5">Code: ${z.zone_id}</div>
                            </div>
                            ${s2Badge}
                        </div>
                        <div class="grid grid-cols-2 gap-2 mt-3 text-xs bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                            <div>
                                <span class="text-slate-500 text-[10px] block">Pluviométrie normale</span>
                                <span class="font-bold text-emerald-800">${z.annual_rainfall_mean_mm} mm/an</span>
                            </div>
                            <div>
                                <span class="text-slate-500 text-[10px] block">Risque Faux Départ</span>
                                <span class="font-bold text-red-700">${Math.round(z.false_start_probability_baseline * 100)}%</span>
                            </div>
                            <div>
                                <span class="text-slate-500 text-[10px] block">Plancher Semis S1</span>
                                <span class="font-semibold text-slate-800">${z.season_1_earliest_sowing_date}</span>
                            </div>
                            <div>
                                <span class="text-slate-500 text-[10px] block">Sol par défaut (TAW)</span>
                                <span class="font-semibold text-slate-800">${z.soil_default_taw_mm_m} mm/m</span>
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-1">
                            <i class="fa-solid fa-location-dot text-emerald-600"></i> Villages sentinelles rattachés (${z.sentinel_villages.length})
                        </div>
                        <ul class="text-xs text-slate-600">
                            ${villagesList}
                        </ul>
                    </div>
                </div>`;
            }).join('');
        }

        async function runAllSimulations() {
            const tbody = document.getElementById('sim-tbody');
            tbody.innerHTML = `<tr><td colspan="7" class="p-6 text-center text-slate-500"><i class="fa-solid fa-spinner fa-spin text-xl"></i><p class="mt-2 text-xs">Exécution de 30 saisons stochastiques par zone...</p></td></tr>`;

            const rows = [];
            for (const z of zonesData) {
                try {
                    const res = await fetch('/api/weather/simulate-seasons', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ zone_id: z.zone_id, n_seasons: 30, seed: 42 })
                    });
                    const d = await res.json();
                    const s2Info = z.regime === 'bimodal'
                        ? `<span class="text-amber-700 font-bold">${z.season_2_earliest_sowing_date} (${z.season_2_status})</span>`
                        : `<span class="text-slate-400">—</span>`;

                    rows.push(`
                        <tr class="border-b border-slate-100 hover:bg-slate-50">
                            <td class="p-3 font-bold text-slate-800">${d.zone_id}</td>
                            <td class="p-3 text-slate-600">${z.regime}</td>
                            <td class="p-3 text-right font-mono font-bold text-emerald-800">${d.mean_annual_rainfall_mm} ± ${d.std_annual_rainfall_mm} mm</td>
                            <td class="p-3 text-right font-mono text-slate-700">${d.mean_rain_days} j</td>
                            <td class="p-3 text-center font-semibold text-indigo-900">${d.median_onset_date_str || 'N/A'}</td>
                            <td class="p-3 text-center font-bold text-red-600">${d.false_start_rate_pct}%</td>
                            <td class="p-3 text-xs">${s2Info}</td>
                        </tr>
                    `);
                } catch (e) {
                    console.error(e);
                }
            }
            tbody.innerHTML = rows.join('');
            document.getElementById('sim-timestamp').textContent = 'Calculé le ' + new Date().toLocaleTimeString();
        }

        // Init
        loadZones();
    </script>
</body>
</html>"""


def render_audio_eval_html() -> str:
    """HTML evaluation studio for native speakers and juries (Step E10)."""
    return """<!DOCTYPE html>
<html lang="fr" class="h-full bg-slate-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraFarm — Évaluation Vocale Terroir (Locuteurs Natifs)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="h-full flex flex-col font-sans text-slate-800">

    <!-- Header -->
    <header class="bg-indigo-950 text-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-indigo-900 flex items-center justify-center text-indigo-300 text-xl font-bold border border-indigo-700">
                    🎙️
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h1 class="text-xl font-bold tracking-tight">AuraFarm • Évaluation Vocale Terroir</h1>
                        <span class="text-xs bg-indigo-800 text-indigo-200 px-2.5 py-0.5 rounded-full font-semibold border border-indigo-600">Étape E10</span>
                    </div>
                    <p class="text-xs text-indigo-300 font-light">Validation d'intelligibilité, de clarté 2G et d'accent authentique (Éwé, Kabiyè, Mina, FR)</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="/dashboard" class="inline-flex items-center gap-2 bg-indigo-900 hover:bg-indigo-800 text-white text-xs px-3.5 py-2 rounded-lg border border-indigo-700 transition">
                    <i class="fa-solid fa-arrow-left"></i>
                    <span>Dashboard Principal</span>
                </a>
                <a href="/audio-recorder" class="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-600 text-white text-xs px-3.5 py-2 rounded-lg font-medium transition">
                    <i class="fa-solid fa-microphone"></i>
                    <span>Studio d'Enregistrement (E1)</span>
                </a>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">

        <!-- Banner Context & Methodology -->
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div class="flex items-start gap-3.5">
                <div class="p-3 rounded-xl bg-indigo-100 text-indigo-800 text-lg">
                    <i class="fa-solid fa-headphones-simple"></i>
                </div>
                <div>
                    <h2 class="text-sm font-bold text-slate-900">Protocole d'Évaluation de la Voix Rurale (Hackathon 2026)</h2>
                    <p class="text-xs text-slate-600 mt-0.5 max-w-3xl leading-relaxed">
                        Pour garantir qu'un producteur agricole en zone blanche comprenne immédiatement l'alerte agro-climatique via son combiné basique, chaque phrase modulaire est soumise au test de la voix du terroir : clarté sous compression téléphonique 2G (300-3400 Hz), fluidité sans robotisation, et respect strict de l'accentuation régionale.
                    </p>
                </div>
            </div>
            <div class="flex items-center gap-2 bg-indigo-50 border border-indigo-200 px-3.5 py-2 rounded-xl text-xs text-indigo-900">
                <i class="fa-solid fa-shield-halved text-indigo-600"></i>
                <span>Loi Togolaise N° 2019-014 • Anonymat Garanti</span>
            </div>
        </div>

        <!-- Evaluation Grid: Left Form & Audio Player / Right Live Aggregate Metrics -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

            <!-- Left Form & Player (7 cols) -->
            <div class="lg:col-span-7 flex flex-col gap-5">
                
                <!-- Audio Audition Player Card -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">1. Choix du Clip & Écoute</h3>
                        </div>
                        <span id="player-status-badge" class="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">Prêt</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Langue ciblée</label>
                            <select id="eval-lang" onchange="onLanguageChange()" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="ewe">Éwé (Eʋegbe) — Sud / Plateaux / Maritime</option>
                                <option value="kabiye">Kabiyè — Kara / Centrale</option>
                                <option value="mina">Mina (Gɛ̀ngbe) — Littoral / Golfe / Lacs</option>
                                <option value="francais">Français Facile — National</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Phrase ou consigne à auditer</label>
                            <select id="eval-clip" onchange="updatePromptPreview()" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="status_semer">Statut SEMER (Alerte favorable)</option>
                                <option value="status_attendre">Statut ATTENDRE (Sol trop sec / faux départ)</option>
                                <option value="status_risque">Statut RISQUE (Sécheresse précoce)</option>
                                <option value="variety_recommendation">Recommandation Variété (Cycle court)</option>
                                <option value="call_agent">Consigne Agent d'appui ICAT</option>
                            </select>
                        </div>
                    </div>

                    <!-- Prompt Display -->
                    <div class="bg-indigo-900 text-indigo-100 p-4 rounded-xl border border-indigo-800 flex flex-col gap-2">
                        <div class="flex items-center justify-between text-xs text-indigo-300 font-mono">
                            <span>TRANSCRIPTION LOCALE OFFICIELLE</span>
                            <span id="prompt-clip-tag">status_semer • ewe</span>
                        </div>
                        <p id="prompt-text-display" class="text-sm font-semibold italic text-white leading-relaxed">
                            "Míele gbeƒã ɖem na mi be míate ŋu aƒã nuku fifia. Tsi dza sɔgbɔ."
                        </p>
                        <p id="prompt-meaning-display" class="text-xs text-indigo-200 border-t border-indigo-800/60 pt-1.5">
                            Traduction FR : « Avis favorable pour semer. La réserve hydrique du sol est suffisante. »
                        </p>
                    </div>

                    <!-- 2G Telephone Filter Simulator Toggle -->
                    <div class="bg-amber-50 border border-amber-200 p-3.5 rounded-xl flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2.5">
                            <i class="fa-solid fa-phone-volume text-amber-600 text-lg"></i>
                            <div>
                                <p class="text-xs font-bold text-amber-900">Simulation Filtre Haut-Parleur Téléphone 2G</p>
                                <p class="text-[11px] text-amber-800">Bande passante GSM (300-3400 Hz) + compression 8 kHz</p>
                            </div>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" id="phone-filter-toggle" class="sr-only peer" checked>
                            <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-600"></div>
                        </label>
                    </div>

                    <!-- Audio Controls -->
                    <div class="flex flex-wrap items-center gap-3 pt-1">
                        <button onclick="playAudioAudit()" id="btn-play-audio" class="flex-1 inline-flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2.5 rounded-xl text-xs shadow transition">
                            <i class="fa-solid fa-play"></i>
                            <span>Écouter l'Extrait Vocal</span>
                        </button>
                        <button onclick="stopAudioAudit()" class="inline-flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-4 py-2.5 rounded-xl text-xs transition border border-slate-300">
                            <i class="fa-solid fa-stop"></i>
                            <span>Arrêter</span>
                        </button>
                    </div>
                </div>

                <!-- Evaluation Scoring Form -->
                <form id="evaluation-form" onsubmit="submitEvaluation(event)" class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">2. Grille de Notation par l'Évaluateur</h3>
                        </div>
                        <span class="text-xs text-slate-500 italic">* Tous les critères sont obligatoires</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Nom ou Pseudonyme de l'auditeur</label>
                            <input type="text" id="evaluator-name" placeholder="Ex: M. Koffi / Évaluateur Juré" required class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Région d'origine / Attachement</label>
                            <select id="evaluator-region" class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                                <option value="Maritime">Région Maritime (Zio, Yoto, Vo, Golfe)</option>
                                <option value="Plateaux">Région des Plateaux (Kloto, Ogou, Haho)</option>
                                <option value="Centrale">Région Centrale (Tchaoudjo, Sotouboua)</option>
                                <option value="Kara">Région de la Kara (Kozah, Assoli, Doufelgou)</option>
                                <option value="Savanes">Région des Savanes (Tône, Oti, Kpendjal)</option>
                            </select>
                        </div>
                    </div>

                    <!-- Criteria Sliders / Stars -->
                    <div class="flex flex-col gap-3 pt-2">
                        
                        <!-- Criterion 1: Clarity -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">1. Clarté & Intelligibilité sonore</span>
                                    <p class="text-[11px] text-slate-500">Même avec le bruit de fond ou sur haut-parleur bon marché</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="clarity-stars">
                                    <!-- 5 star radio inputs -->
                                    <input type="radio" name="clarity" value="1" id="c1" class="hidden peer/c1">
                                    <label for="c1" onclick="setRating('clarity', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c1:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="2" id="c2" class="hidden peer/c2">
                                    <label for="c2" onclick="setRating('clarity', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c2:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="3" id="c3" class="hidden peer/c3">
                                    <label for="c3" onclick="setRating('clarity', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c3:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="4" id="c4" class="hidden peer/c4">
                                    <label for="c4" onclick="setRating('clarity', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c4:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="clarity" value="5" id="c5" checked class="hidden peer/c5">
                                    <label for="c5" onclick="setRating('clarity', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg peer-checked/c5:text-amber-400"><i class="fa-solid fa-star"></i></label>
                                    <span id="clarity-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 2: Naturalness -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">2. Fluidité & Naturel du débit</span>
                                    <p class="text-[11px] text-slate-500">Cadence naturelle, absence d'artéfacts ou de saccades robotiques</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="naturalness-stars">
                                    <input type="radio" name="naturalness" value="1" id="n1" class="hidden">
                                    <label for="n1" onclick="setRating('naturalness', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="2" id="n2" class="hidden">
                                    <label for="n2" onclick="setRating('naturalness', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="3" id="n3" class="hidden">
                                    <label for="n3" onclick="setRating('naturalness', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="4" id="n4" class="hidden">
                                    <label for="n4" onclick="setRating('naturalness', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="naturalness" value="5" id="n5" checked class="hidden">
                                    <label for="n5" onclick="setRating('naturalness', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <span id="naturalness-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 3: Accent Authenticity -->
                        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-xs font-bold text-slate-900">3. Authenticité de l'accent du terroir</span>
                                    <p class="text-[11px] text-slate-500">Ton respectueux et naturel pour un producteur de la zone</p>
                                </div>
                                <div class="flex items-center gap-1.5" id="authenticity-stars">
                                    <input type="radio" name="authenticity" value="1" id="a1" class="hidden">
                                    <label for="a1" onclick="setRating('authenticity', 1)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="2" id="a2" class="hidden">
                                    <label for="a2" onclick="setRating('authenticity', 2)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="3" id="a3" class="hidden">
                                    <label for="a3" onclick="setRating('authenticity', 3)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="4" id="a4" class="hidden">
                                    <label for="a4" onclick="setRating('authenticity', 4)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <input type="radio" name="authenticity" value="5" id="a5" checked class="hidden">
                                    <label for="a5" onclick="setRating('authenticity', 5)" class="cursor-pointer text-slate-300 hover:text-amber-400 text-lg"><i class="fa-solid fa-star"></i></label>
                                    <span id="authenticity-score-label" class="text-xs font-bold text-amber-600 ml-2">5/5</span>
                                </div>
                            </div>
                        </div>

                        <!-- Criterion 4: Immediate Comprehension Test -->
                        <div class="p-3.5 bg-indigo-50/60 rounded-xl border border-indigo-200 flex items-center justify-between">
                            <div>
                                <span class="text-xs font-bold text-indigo-950">4. Test de compréhension immédiate sans hésitation</span>
                                <p class="text-[11px] text-indigo-800">L'agriculteur sait-il exactement quoi faire dès la première écoute ?</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <label class="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-800 cursor-pointer">
                                    <input type="radio" name="comprehension" value="1" checked class="text-emerald-600 focus:ring-emerald-500">
                                    <span>Oui (Compris)</span>
                                </label>
                                <label class="inline-flex items-center gap-1.5 text-xs font-bold text-red-700 cursor-pointer ml-2">
                                    <input type="radio" name="comprehension" value="0" class="text-red-600 focus:ring-red-500">
                                    <span>Non (Ambigu)</span>
                                </label>
                            </div>
                        </div>

                    </div>

                    <!-- Comments -->
                    <div>
                        <label class="block text-xs font-semibold text-slate-700 mb-1">Commentaires qualitatifs & suggestions d'amélioration</label>
                        <textarea id="eval-comments" rows="2" placeholder="Ex: Débit un peu rapide sur le deuxième mot, sinon intonation parfaite pour la Kara." class="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"></textarea>
                    </div>

                    <button type="submit" id="btn-submit-eval" class="w-full inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2.5 rounded-xl text-xs shadow transition">
                        <i class="fa-solid fa-circle-check"></i>
                        <span>Enregistrer l'Évaluation Vocale</span>
                    </button>
                    <div id="eval-submit-msg" class="hidden p-2.5 rounded-lg text-xs font-semibold text-center"></div>
                </form>

            </div>

            <!-- Right Dashboard: Live Evaluation Metrics & History (5 cols) -->
            <div class="lg:col-span-5 flex flex-col gap-5">
                
                <!-- Scorecards per Language -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">Moyennes de Validation par Langue</h3>
                        </div>
                        <button onclick="loadEvaluationSummary()" class="text-xs text-indigo-600 hover:underline flex items-center gap-1 font-semibold">
                            <i class="fa-solid fa-arrows-rotate"></i> Actualiser
                        </button>
                    </div>

                    <div id="summary-cards-container" class="flex flex-col gap-3">
                        <!-- Populated dynamically via JS -->
                        <div class="text-center py-6 text-xs text-slate-400">Chargement des indicateurs...</div>
                    </div>
                </div>

                <!-- Recent Feedback Stream -->
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-3">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wide">Dernières Évaluations Soumises</h3>
                        </div>
                        <span id="eval-count-badge" class="text-xs bg-slate-100 text-slate-700 font-bold px-2 py-0.5 rounded-full">0 avis</span>
                    </div>

                    <div id="recent-reviews-list" class="flex flex-col gap-2.5 max-h-[380px] overflow-y-auto pr-1">
                        <!-- Populated dynamically via JS -->
                        <div class="text-center py-6 text-xs text-slate-400">Aucune évaluation enregistrée pour le moment.</div>
                    </div>
                </div>

            </div>

        </div>

    </main>

    <footer class="bg-white border-t border-slate-200 mt-auto py-4 text-center text-xs text-slate-500">
        AuraFarm &bull; Hackathon Climat & Innovation 2026 &bull; Équipe GPS² (Togolaises In Science)
    </footer>

    <script>
        // State
        const promptBank = {
            "ewe": {
                "status_semer": { text: "Míele gbeƒã ɖem na mi be míate ŋu aƒã nuku fifia. Tsi dza sɔgbɔ.", fr: "Avis favorable pour semer. La réserve hydrique du sol est suffisante." },
                "status_attendre": { text: "Migalɔ̃ aƒã nuku o. Manyo fifia o, tsi medza sɔgbɔ o.", fr: "Attendez avant de semer. Humidité du sol insuffisante." },
                "status_risque": { text: "Nyanyanyɛ : Nuɖuɖu ƒe nɔnɔme gblẽ. Faux départ le dzɔdzɔm.", fr: "Risque élevé de faux départ de saison. Ne pas semer." },
                "variety_recommendation": { text: "Míedo kpɔ̃ TZEE-W-Pop miadze aƒã na ŋkeke blaenyi.", fr: "Semez la variété précoce TZEE-W-Pop adaptée à la durée de pluie." },
                "call_agent": { text: "Bip 90123456 ne ICAT ƒe agbledɔwɔla aƒo nu na wò.", fr: "Faites un bip au 90123456 pour parler à un agent ICAT." }
            },
            "kabiye": {
                "status_semer": { text: "Pɩwɛ ɖeu se ŋdu kɛlɛʊ nɔɔnɔɔ. Tɛʊ nɩwa pɩtɩŋa.", fr: "Vous pouvez semer maintenant. Pluie adéquate constatée." },
                "status_attendre": { text: "Taadʊ kɛlɛʊ nɔɔnɔɔ. Ðaŋ tɛʊ nɩʊ nɔɔnɔɔ.", fr: "Attendez encore avant les semis. Humidité insuffisante." },
                "status_risque": { text: "Kigbɛɖɛɛ wɛɛ : tɛʊ kaɣ hɛʊ kpaagbaa.", fr: "Alerte : risque critique de sécheresse précoce." },
                "variety_recommendation": { text: "Du Sotubua tɛ nuku ŋgʊ kɩtɛŋ lɔŋ yɔ.", fr: "Privilégiez la variété précoce recommandée pour votre sol." },
                "call_agent": { text: "Ya ICAT tɔm kɛ 90123456 taa.", fr: "Contactez le conseiller ICAT au 90123456." }
            },
            "mina": {
                "status_semer": { text: "Míatɛŋ ado nuku fifia. Tsi dza gbaŋgbaŋ le anyigba.", fr: "Vous pouvez semer dès maintenant. Bonne humidité du sol." },
                "status_attendre": { text: "Migado nuku o. Tsi megakpɔ dza nyuie o.", fr: "Ne semez pas encore. Attendez une nouvelle pluie continue." },
                "status_risque": { text: "Kpoɖoɖo li : Faux départ le agblea me.", fr: "Attention : risque de faux départ pluvieux." },
                "variety_recommendation": { text: "Do variety TZEE-W-Pop le ŋkeke blaenyi me.", fr: "Variété précoce recommandée pour sécuriser la récolte." },
                "call_agent": { text: "Yɔ ICAT tɔ le 90123456 jí.", fr: "Consultez l'agent ICAT de votre préfecture." }
            },
            "francais": {
                "status_semer": { text: "Avis favorable pour semer. La réserve hydrique du sol dépasse le seuil critique.", fr: "Avis favorable pour semer immédiatement." },
                "status_attendre": { text: "Attendez avant de semer. Le sol est trop sec pour garantir la levée des graines.", fr: "Humidité insuffisante." },
                "status_risque": { text: "Alerte agro-météo : risque élevé de faux départ. Pause sèche probable.", fr: "Sécheresse précoce détectée." },
                "variety_recommendation": { text: "Semez la variété précoce certifiée ITRA à cycle court 85 jours.", fr: "Variété à haut rendement adaptée." },
                "call_agent": { text: "Faites un bip au 90123456 pour être rappelé gratuitement par votre agent ICAT.", fr: "Assistance technique gratuite." }
            }
        };

        let currentRatings = { clarity: 5, naturalness: 5, authenticity: 5 };
        let audioContext = null;

        function setRating(metric, score) {
            currentRatings[metric] = score;
            document.getElementById(metric + '-score-label').textContent = score + '/5';
            
            // Highlight star icons
            const container = document.getElementById(metric + '-stars');
            const labels = container.querySelectorAll('label');
            labels.forEach((lbl, idx) => {
                if (idx < score) {
                    lbl.className = 'cursor-pointer text-amber-400 text-lg';
                } else {
                    lbl.className = 'cursor-pointer text-slate-300 hover:text-amber-400 text-lg';
                }
            });
        }

        function onLanguageChange() {
            updatePromptPreview();
            loadEvaluationSummary();
        }

        function updatePromptPreview() {
            const lang = document.getElementById('eval-lang').value;
            const clip = document.getElementById('eval-clip').value;
            const item = (promptBank[lang] && promptBank[lang][clip]) || { text: 'Phrase en cours d\'enregistrement...', fr: '' };
            
            document.getElementById('prompt-clip-tag').textContent = clip + ' • ' + lang;
            document.getElementById('prompt-text-display').textContent = '"' + item.text + '"';
            document.getElementById('prompt-meaning-display').textContent = 'Sens : « ' + item.fr + ' »';
        }

        function playAudioAudit() {
            const lang = document.getElementById('eval-lang').value;
            const clip = document.getElementById('eval-clip').value;
            const item = (promptBank[lang] && promptBank[lang][clip]) || { text: '' };
            const statusBadge = document.getElementById('player-status-badge');
            const useFilter = document.getElementById('phone-filter-toggle').checked;

            statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold animate-pulse';
            statusBadge.textContent = useFilter ? '📞 Lecture 2G GSM (Filtre actif)' : '🔊 Lecture Audio Direct';

            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(item.text);
                utterance.lang = lang === 'francais' ? 'fr-FR' : 'fr-FR';
                utterance.rate = useFilter ? 0.95 : 1.0;
                utterance.pitch = useFilter ? 1.15 : 1.0;

                utterance.onend = () => {
                    statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium';
                    statusBadge.textContent = 'Terminé';
                };
                window.speechSynthesis.speak(utterance);
            }
        }

        function stopAudioAudit() {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
            const statusBadge = document.getElementById('player-status-badge');
            statusBadge.className = 'text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium';
            statusBadge.textContent = 'Arrêté';
        }

        async function submitEvaluation(e) {
            e.preventDefault();
            const submitBtn = document.getElementById('btn-submit-eval');
            const msgBox = document.getElementById('eval-submit-msg');
            submitBtn.disabled = true;

            const payload = {
                clip_id: document.getElementById('eval-clip').value,
                language: document.getElementById('eval-lang').value,
                evaluator_name: document.getElementById('evaluator-name').value.trim() || 'Anonyme',
                evaluator_origin_region: document.getElementById('evaluator-region').value,
                clarity_rating: currentRatings.clarity,
                naturalness_rating: currentRatings.naturalness,
                accent_authenticity_rating: currentRatings.authenticity,
                comprehension_check_passed: document.querySelector('input[name="comprehension"]:checked').value === "1",
                comments: document.getElementById('eval-comments').value.trim()
            };

            try {
                const res = await fetch('/api/audio-eval', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    msgBox.className = 'p-2.5 rounded-lg text-xs font-semibold text-center bg-emerald-100 text-emerald-800 border border-emerald-300';
                    msgBox.textContent = '✓ Évaluation enregistrée avec succès (ID #' + data.evaluation_id + ') !';
                    msgBox.classList.remove('hidden');
                    document.getElementById('eval-comments').value = '';
                    loadEvaluationSummary();
                } else {
                    throw new Error(data.detail || 'Erreur lors de l\'enregistrement');
                }
            } catch (err) {
                msgBox.className = 'p-2.5 rounded-lg text-xs font-semibold text-center bg-red-100 text-red-800 border border-red-300';
                msgBox.textContent = 'Erreur : ' + err.message;
                msgBox.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
                setTimeout(() => { msgBox.classList.add('hidden'); }, 4000);
            }
        }

        async function loadEvaluationSummary() {
            try {
                const res = await fetch('/api/audio-eval/summary');
                const data = await res.json();
                renderSummaryCards(data);
            } catch (e) {
                console.error('Erreur chargement summary:', e);
            }

            try {
                const res = await fetch('/api/audio-eval/list?limit=10');
                const list = await res.json();
                renderRecentReviews(list);
            } catch (e) {
                console.error('Erreur chargement reviews:', e);
            }
        }

        function renderSummaryCards(data) {
            const container = document.getElementById('summary-cards-container');
            const langs = [
                { key: 'ewe', label: 'Éwé (Eʋegbe)', icon: '🌾' },
                { key: 'kabiye', label: 'Kabiyè', icon: '⛰️' },
                { key: 'mina', label: 'Mina (Gɛ̀ngbe)', icon: '🌊' },
                { key: 'francais', label: 'Français Facile', icon: '📢' }
            ];

            const byLang = data.by_language || {};
            let html = '';

            langs.forEach(l => {
                const item = byLang[l.key] || { count: 0, avg_clarity: 0, avg_naturalness: 0, avg_authenticity: 0, comprehension_rate_pct: 0, mean_overall_score: 0 };
                const countBadge = item.count > 0 ? `<span class="bg-indigo-100 text-indigo-800 text-[10px] font-bold px-2 py-0.5 rounded-full">${item.count} avis</span>` : `<span class="text-slate-400 text-[10px]">0 avis</span>`;
                
                html += `
                    <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col gap-2 hover:border-indigo-300 transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span>${l.icon}</span>
                                <span class="text-xs font-bold text-slate-900">${l.label}</span>
                            </div>
                            <div class="flex items-center gap-2">
                                ${countBadge}
                                <span class="text-xs font-extrabold text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">★ ${item.mean_overall_score}/5</span>
                            </div>
                        </div>
                        <div class="grid grid-cols-4 gap-1.5 text-center text-[10px]">
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Clarté</span>
                                <span class="font-bold text-slate-800">${item.avg_clarity || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Naturel</span>
                                <span class="font-bold text-slate-800">${item.avg_naturalness || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Accent</span>
                                <span class="font-bold text-slate-800">${item.avg_authenticity || '—'}/5</span>
                            </div>
                            <div class="p-1 rounded bg-white border border-slate-100">
                                <span class="text-slate-400 block">Compris</span>
                                <span class="font-bold ${item.comprehension_rate_pct >= 80 ? 'text-emerald-700' : 'text-slate-800'}">${item.comprehension_rate_pct ? item.comprehension_rate_pct + '%' : '—'}</span>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
        }

        function renderRecentReviews(list) {
            const container = document.getElementById('recent-reviews-list');
            document.getElementById('eval-count-badge').textContent = list.length + ' avis';
            if (!list || list.length === 0) {
                container.innerHTML = '<div class="text-center py-6 text-xs text-slate-400">Aucune évaluation enregistrée pour le moment.</div>';
                return;
            }

            let html = '';
            list.slice(0, 8).forEach(r => {
                const compBadge = r.comprehension_check_passed ? '<span class="text-emerald-700 font-bold text-[10px] bg-emerald-50 px-1.5 py-0.5 rounded">Compris</span>' : '<span class="text-red-700 font-bold text-[10px] bg-red-50 px-1.5 py-0.5 rounded">Ambigu</span>';
                html += `
                    <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex flex-col gap-1">
                        <div class="flex items-center justify-between text-[11px]">
                            <span class="font-bold text-slate-900">${r.evaluator_name || 'Anonyme'} (${r.evaluator_origin_region || 'Maritime'})</span>
                            <span class="text-slate-400">${r.language.toUpperCase()} • ${r.clip_id}</span>
                        </div>
                        <div class="flex items-center gap-3 text-[11px] text-slate-600">
                            <span>Clarté : <b class="text-amber-600">${r.clarity_rating}/5</b></span>
                            <span>Naturel : <b class="text-amber-600">${r.naturalness_rating}/5</b></span>
                            <span>Accent : <b class="text-amber-600">${r.accent_authenticity_rating}/5</b></span>
                            ${compBadge}
                        </div>
                        ${r.comments ? `<p class="text-[11px] text-slate-500 italic bg-white p-1.5 rounded border border-slate-100">« ${r.comments} »</p>` : ''}
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        // Init
        updatePromptPreview();
        setRating('clarity', 5);
        setRating('naturalness', 5);
        setRating('authenticity', 5);
        loadEvaluationSummary();
    </script>
</body>
</html>"""
