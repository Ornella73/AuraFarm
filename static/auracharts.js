/**
 * AuraCharts — Lightweight, zero-dependency SVG dataviz engine for AuraFarm.
 * Conforms to offline-first constraint (no external CDN required).
 */
const AuraCharts = (function () {
    function createSvg(width, height) {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svg.setAttribute("class", "w-full h-full overflow-visible");
        return svg;
    }

    // Chart 1: Rain & Cumulative Rain
    function rainChart(container, data) {
        container.innerHTML = "";
        const w = 700, h = 260, pad = 40;
        const svg = createSvg(w, h);

        const daily = data.daily_rain_mm || [];
        const cum = data.cumulative_rain_mm || [];
        const n = daily.length;
        if (n === 0) return;

        const maxDaily = Math.max(20, Math.max(...daily));
        const maxCum = Math.max(100, Math.max(...cum));
        const chartW = w - pad * 2;
        const chartH = h - pad * 2;

        // Grid lines
        for (let i = 0; i <= 4; i++) {
            const y = pad + (chartH / 4) * i;
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", pad);
            line.setAttribute("x2", w - pad);
            line.setAttribute("y1", y);
            line.setAttribute("y2", y);
            line.setAttribute("stroke", "#f1f5f9");
            line.setAttribute("stroke-width", "1");
            svg.appendChild(line);

            // Left Y-axis labels (Daily mm)
            const val = Math.round(maxDaily * (1 - i / 4));
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", pad - 6);
            text.setAttribute("y", y + 3);
            text.setAttribute("text-anchor", "end");
            text.setAttribute("class", "text-[9px] fill-slate-400 font-mono");
            text.textContent = val + "m";
            svg.appendChild(text);

            // Right Y-axis labels (Cum mm)
            const valCum = Math.round(maxCum * (1 - i / 4));
            const textR = document.createElementNS("http://www.w3.org/2000/svg", "text");
            textR.setAttribute("x", w - pad + 6);
            textR.setAttribute("y", y + 3);
            textR.setAttribute("text-anchor", "start");
            textR.setAttribute("class", "text-[9px] fill-emerald-600 font-mono font-bold");
            textR.textContent = valCum;
            svg.appendChild(textR);
        }

        // Daily rain bars
        const barW = Math.max(1.5, chartW / n - 0.5);
        daily.forEach((r, idx) => {
            if (r > 0) {
                const x = pad + (idx / n) * chartW;
                const barH = (r / maxDaily) * chartH;
                const y = h - pad - barH;
                const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                rect.setAttribute("x", x);
                rect.setAttribute("y", y);
                rect.setAttribute("width", barW);
                rect.setAttribute("height", barH);
                rect.setAttribute("fill", "#38bdf8");
                rect.setAttribute("rx", "1");
                svg.appendChild(rect);
            }
        });

        // Cumulative rain line
        let pathD = "";
        cum.forEach((c, idx) => {
            const x = pad + (idx / n) * chartW;
            const y = h - pad - (c / maxCum) * chartH;
            pathD += (idx === 0 ? "M " : " L ") + `${x} ${y}`;
        });
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", pathD);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", "#059669");
        path.setAttribute("stroke-width", "2.5");
        svg.appendChild(path);

        // Onset marker line
        if (data.onset_day_index !== null && data.onset_day_index !== undefined) {
            const onsetX = pad + (data.onset_day_index / n) * chartW;
            const vLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
            vLine.setAttribute("x1", onsetX);
            vLine.setAttribute("x2", onsetX);
            vLine.setAttribute("y1", pad);
            vLine.setAttribute("y2", h - pad);
            vLine.setAttribute("stroke", data.has_false_start ? "#ef4444" : "#10b981");
            vLine.setAttribute("stroke-width", "2");
            vLine.setAttribute("stroke-dasharray", "4");
            svg.appendChild(vLine);

            const badge = document.createElementNS("http://www.w3.org/2000/svg", "text");
            badge.setAttribute("x", onsetX + 4);
            badge.setAttribute("y", pad + 14);
            badge.setAttribute("class", `text-[10px] font-bold ${data.has_false_start ? "fill-red-600" : "fill-emerald-700"}`);
            badge.textContent = data.has_false_start ? "⚠️ Faux départ" : "🌱 Démarrage optimal";
            svg.appendChild(badge);
        }

        container.appendChild(svg);
    }

    // Chart 2: Temperature Profile
    function tempChart(container, data) {
        container.innerHTML = "";
        const w = 700, h = 260, pad = 40;
        const svg = createSvg(w, h);

        const tmin = data.tmin_c || [];
        const tmax = data.tmax_c || [];
        const n = tmin.length;
        if (n === 0) return;

        const minT = 15;
        const maxT = 42;
        const chartW = w - pad * 2;
        const chartH = h - pad * 2;

        // Grid & 35°C threshold line
        [20, 25, 30, 35, 40].forEach(t => {
            const y = h - pad - ((t - minT) / (maxT - minT)) * chartH;
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", pad);
            line.setAttribute("x2", w - pad);
            line.setAttribute("y1", y);
            line.setAttribute("y2", y);
            line.setAttribute("stroke", t === 35 ? "#f87171" : "#f1f5f9");
            line.setAttribute("stroke-width", t === 35 ? "1.5" : "1");
            if (t === 35) line.setAttribute("stroke-dasharray", "3");
            svg.appendChild(line);

            const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
            label.setAttribute("x", pad - 6);
            label.setAttribute("y", y + 3);
            label.setAttribute("text-anchor", "end");
            label.setAttribute("class", `text-[9px] font-mono ${t === 35 ? "fill-red-600 font-bold" : "fill-slate-400"}`);
            label.textContent = t + "°C";
            svg.appendChild(label);

            if (t === 35) {
                const note = document.createElementNS("http://www.w3.org/2000/svg", "text");
                note.setAttribute("x", w - pad - 4);
                note.setAttribute("y", y - 4);
                note.setAttribute("text-anchor", "end");
                note.setAttribute("class", "text-[9px] fill-red-600 font-bold");
                note.textContent = "Seuil critique floraison (35°C)";
                svg.appendChild(note);
            }
        });

        // Tmax curve
        let pathMax = "";
        tmax.forEach((t, i) => {
            const x = pad + (i / n) * chartW;
            const y = h - pad - ((t - minT) / (maxT - minT)) * chartH;
            pathMax += (i === 0 ? "M " : " L ") + `${x} ${y}`;
        });
        const pMax = document.createElementNS("http://www.w3.org/2000/svg", "path");
        pMax.setAttribute("d", pathMax);
        pMax.setAttribute("fill", "none");
        pMax.setAttribute("stroke", "#f97316");
        pMax.setAttribute("stroke-width", "2");
        svg.appendChild(pMax);

        // Tmin curve
        let pathMin = "";
        tmin.forEach((t, i) => {
            const x = pad + (i / n) * chartW;
            const y = h - pad - ((t - minT) / (maxT - minT)) * chartH;
            pathMin += (i === 0 ? "M " : " L ") + `${x} ${y}`;
        });
        const pMin = document.createElementNS("http://www.w3.org/2000/svg", "path");
        pMin.setAttribute("d", pathMin);
        pMin.setAttribute("fill", "none");
        pMin.setAttribute("stroke", "#0284c7");
        pMin.setAttribute("stroke-width", "1.5");
        svg.appendChild(pMin);

        container.appendChild(svg);
    }

    // Chart 3: Soil Moisture %
    function soilChart(container, data) {
        container.innerHTML = "";
        const w = 700, h = 260, pad = 40;
        const svg = createSvg(w, h);

        const moisture = data.soil_moisture_pct || [];
        const n = moisture.length;
        if (n === 0) return;

        const chartW = w - pad * 2;
        const chartH = h - pad * 2;

        // Threshold lines: 100% (Field capacity), 50% (Sowing threshold), 5% (Wilting point)
        const thresholds = [
            { val: 100, color: "#10b981", label: "Capacité au champ (100%)" },
            { val: 50, color: "#f59e0b", label: "Seuil déclenchement semis (50%)" },
            { val: 5, color: "#ef4444", label: "Point de flétrissement (5%)" }
        ];

        thresholds.forEach(th => {
            const y = h - pad - (th.val / 100) * chartH;
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", pad);
            line.setAttribute("x2", w - pad);
            line.setAttribute("y1", y);
            line.setAttribute("y2", y);
            line.setAttribute("stroke", th.color);
            line.setAttribute("stroke-width", "1.5");
            line.setAttribute("stroke-dasharray", "3");
            svg.appendChild(line);

            const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
            label.setAttribute("x", w - pad - 6);
            label.setAttribute("y", y - 4);
            label.setAttribute("text-anchor", "end");
            label.setAttribute("class", "text-[9px] font-bold");
            label.setAttribute("fill", th.color);
            label.textContent = th.label;
            svg.appendChild(label);
        });

        // Soil moisture filled area
        let areaD = `M ${pad} ${h - pad}`;
        moisture.forEach((m, i) => {
            const x = pad + (i / n) * chartW;
            const y = h - pad - (Math.min(100, Math.max(0, m)) / 100) * chartH;
            areaD += ` L ${x} ${y}`;
        });
        areaD += ` L ${pad + chartW} ${h - pad} Z`;

        const area = document.createElementNS("http://www.w3.org/2000/svg", "path");
        area.setAttribute("d", areaD);
        area.setAttribute("fill", "rgba(16, 185, 129, 0.15)");
        svg.appendChild(area);

        // Curve
        let pathD = "";
        moisture.forEach((m, i) => {
            const x = pad + (i / n) * chartW;
            const y = h - pad - (Math.min(100, Math.max(0, m)) / 100) * chartH;
            pathD += (i === 0 ? "M " : " L ") + `${x} ${y}`;
        });
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", pathD);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", "#047857");
        path.setAttribute("stroke-width", "2");
        svg.appendChild(path);

        container.appendChild(svg);
    }

    // Chart 4: Sowing Windows by Variety
    function windowsChart(container, windows) {
        container.innerHTML = "";
        const w = 700, h = 240, pad = 30;
        const svg = createSvg(w, h);

        if (!windows || windows.length === 0) return;

        const rowH = (h - pad * 2) / windows.length;
        const baseDay = 60; // March 1st (DOY 60)
        const totalDays = 150; // March to July (150 days)
        const chartW = w - 160 - pad;

        windows.forEach((win, idx) => {
            const y = pad + idx * rowH + 6;

            // Variety label
            const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
            label.setAttribute("x", pad);
            label.setAttribute("y", y + 14);
            label.setAttribute("class", "text-[11px] font-bold fill-slate-700");
            label.textContent = `${win.variety_name} (${win.cycle_days}j)`;
            svg.appendChild(label);

            // Calculate start and end offset
            const startD = new Date(win.start_date);
            const startDOY = Math.floor((startD - new Date(startD.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24));
            const duration = win.window_days || 21;

            const x = 160 + Math.max(0, ((startDOY - baseDay) / totalDays) * chartW);
            const barW = Math.max(20, (duration / totalDays) * chartW);

            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", x);
            rect.setAttribute("y", y);
            rect.setAttribute("width", barW);
            rect.setAttribute("height", rowH - 12);
            rect.setAttribute("fill", idx === 0 ? "#10b981" : "#3b82f6");
            rect.setAttribute("rx", "4");
            svg.appendChild(rect);

            const dateTxt = document.createElementNS("http://www.w3.org/2000/svg", "text");
            dateTxt.setAttribute("x", x + barW / 2);
            dateTxt.setAttribute("y", y + (rowH - 12) / 2 + 4);
            dateTxt.setAttribute("text-anchor", "middle");
            dateTxt.setAttribute("class", "text-[10px] font-semibold fill-white font-mono");
            dateTxt.textContent = `${win.start_date.slice(5)} → ${win.end_date.slice(5)}`;
            svg.appendChild(dateTxt);
        });

        container.appendChild(svg);
    }

    // Chart 5: Inter-Zone Comparison
    function zonesChart(container, zones) {
        container.innerHTML = "";
        const w = 700, h = 240, pad = 35;
        const svg = createSvg(w, h);

        if (!zones || zones.length === 0) return;
        const n = zones.length;
        const colW = (w - pad * 2) / n;
        const chartH = h - pad * 2;
        const maxRain = 1400;

        zones.forEach((z, i) => {
            const x = pad + i * colW + colW * 0.15;
            const barW = colW * 0.70;
            const barH = (z.annual_rainfall_mean_mm / maxRain) * chartH;
            const y = h - pad - barH;

            // Rainfall bar
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", x);
            rect.setAttribute("y", y);
            rect.setAttribute("width", barW);
            rect.setAttribute("height", barH);
            rect.setAttribute("fill", "#0284c7");
            rect.setAttribute("rx", "3");
            svg.appendChild(rect);

            // Value text
            const valTxt = document.createElementNS("http://www.w3.org/2000/svg", "text");
            valTxt.setAttribute("x", x + barW / 2);
            valTxt.setAttribute("y", y - 6);
            valTxt.setAttribute("text-anchor", "middle");
            valTxt.setAttribute("class", "text-[10px] font-bold fill-slate-700 font-mono");
            valTxt.textContent = `${Math.round(z.annual_rainfall_mean_mm)} mm`;
            svg.appendChild(valTxt);

            // False start probability badge
            const riskTxt = document.createElementNS("http://www.w3.org/2000/svg", "text");
            riskTxt.setAttribute("x", x + barW / 2);
            riskTxt.setAttribute("y", y + 15);
            riskTxt.setAttribute("text-anchor", "middle");
            riskTxt.setAttribute("class", "text-[9px] font-bold fill-white");
            riskTxt.textContent = `Risque: ${z.false_start_probability_baseline}%`;
            svg.appendChild(riskTxt);

            // Zone label
            const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
            label.setAttribute("x", x + barW / 2);
            label.setAttribute("y", h - pad + 16);
            label.setAttribute("text-anchor", "middle");
            label.setAttribute("class", "text-[11px] font-semibold fill-slate-800");
            label.textContent = z.zone_name;
            svg.appendChild(label);
        });

        container.appendChild(svg);
    }

    // Chart 6: Tornado Sensitivity
    function tornadoChart(container, tornadoData) {
        container.innerHTML = "";
        const w = 700, h = 260, pad = 30;
        const svg = createSvg(w, h);

        const items = (tornadoData || []).slice(0, 7);
        if (items.length === 0) return;

        const rowH = (h - pad * 2) / items.length;
        const midX = 350;
        const maxImpact = 40; // Max expected scale
        const scaleW = 200;

        // Center line
        const centerLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
        centerLine.setAttribute("x1", midX);
        centerLine.setAttribute("x2", midX);
        centerLine.setAttribute("y1", pad);
        centerLine.setAttribute("y2", h - pad);
        centerLine.setAttribute("stroke", "#cbd5e1");
        centerLine.setAttribute("stroke-width", "2");
        svg.appendChild(centerLine);

        items.forEach((item, idx) => {
            const y = pad + idx * rowH + 4;
            const barHeight = rowH - 8;

            // Factor label
            const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
            label.setAttribute("x", 20);
            label.setAttribute("y", y + barHeight / 2 + 4);
            label.setAttribute("class", "text-[10px] font-bold fill-slate-700");
            label.textContent = item.factor;
            svg.appendChild(label);

            // Shift width
            const shift = item.onset_shift_days || 0;
            const wShift = (Math.abs(shift) / maxImpact) * scaleW;
            const xShift = shift >= 0 ? midX : midX - wShift;

            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", xShift);
            rect.setAttribute("y", y);
            rect.setAttribute("width", Math.max(4, wShift));
            rect.setAttribute("height", barHeight);
            rect.setAttribute("fill", shift >= 0 ? "#ef4444" : "#10b981");
            rect.setAttribute("rx", "3");
            svg.appendChild(rect);

            // Text tag
            const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
            txt.setAttribute("x", shift >= 0 ? xShift + wShift + 6 : xShift - 6);
            txt.setAttribute("y", y + barHeight / 2 + 3);
            txt.setAttribute("text-anchor", shift >= 0 ? "start" : "end");
            txt.setAttribute("class", "text-[9px] font-mono fill-slate-600");
            txt.textContent = `${shift > 0 ? "+" : ""}${shift}j (Risque ${item.false_start_risk_delta_pct > 0 ? "+" : ""}${item.false_start_risk_delta_pct}%)`;
            svg.appendChild(txt);
        });

        container.appendChild(svg);
    }

    return {
        rainChart,
        tempChart,
        soilChart,
        windowsChart,
        zonesChart,
        tornadoChart
    };
})();

