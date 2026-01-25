let map, impactCircle;

function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 21.1458, lng: 79.0882 }, 
        zoom: 5,
        styles: [
            { "elementType": "geometry", "stylers": [{ "color": "#1d2c4d" }] },
            { "elementType": "labels.text.fill", "stylers": [{ "color": "#8ec3b9" }] },
            { "featureType": "water", "elementType": "geometry", "stylers": [{ "color": "#0e1626" }] }
        ]
    });
}

// Sidebar Toggle Logic
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleSidebar');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            toggleBtn.innerText = sidebar.classList.contains('collapsed') ? "▶" : "◀";
            
            // Resize map after sidebar transition
            setTimeout(() => {
                google.maps.event.trigger(map, "resize");
            }, 400);
        });
    }
});

async function runAudit() {
    const btn = document.getElementById("auditBtn");
    btn.innerText = "ANALYZING...";
    btn.disabled = true;

    const payload = {
        name: document.getElementById('name').value,
        type: document.getElementById('type').value,
        production: document.getElementById('prod').value,
        energy: document.getElementById('energy').value,
        water: document.getElementById('water').value,
        purity: document.getElementById('purity').value
    };

    try {
        const resp = await fetch('/audit', {
            method: 'POST', 
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        const res = await resp.json();

        // 1. Update Visibility
        document.getElementById('stats-dashboard').style.display = 'flex';
        document.getElementById('solution-box').style.display = 'block';

        // 2. Update Headers and Stats
        const statusHeader = document.getElementById('status-header');
        statusHeader.innerText = res.zone;
        statusHeader.style.color = res.color;

        document.getElementById('val-co2').innerText = res.co2_footprint_kg + " KG";
        document.getElementById('val-circ').innerText = (res.circularity || "0") + "%";
        document.getElementById('val-status').innerText = res.level;
        document.getElementById('val-status').style.color = res.color;
        document.getElementById('val-score').innerText = res.score;

        // 3. Build Dynamic Report (Impact + Range + Precautions)
        let listContainer = document.getElementById('sol-list');
        listContainer.innerHTML = ""; 

        // A. Affected Range
        listContainer.innerHTML += `<div class="section-title impact-title">SITE IMPACT ASSESSMENT:</div>`;
        listContainer.innerHTML += `
            <div class="impact-item distance-highlight">
                📍 <strong>AFFECTED RANGE:</strong> ${res.impact_radius_km || 0} KM 
                <br><small>(Primary Environmental Influence Zone)</small>
            </div>`;

        // B. Impacts
        res.environmental_impacts.forEach(impact => {
            listContainer.innerHTML += `<div class="impact-item">⚠️ ${impact}</div>`;
        });

        // C. Precautions
        listContainer.innerHTML += `<div class="section-title precaution-title">REQUIRED PRECAUTIONS:</div>`;
        res.solutions.forEach(s => {
            listContainer.innerHTML += `<div class="sol-item">✅ ${s}</div>`;
        });

        // 4. Update Map Location and Impact Circle
        if (res.location && res.location.lat) {
            const newPos = { 
                lat: parseFloat(res.location.lat), 
                lng: parseFloat(res.location.lng) 
            };
            
            map.panTo(newPos);
            map.setZoom(11);

            if(impactCircle) impactCircle.setMap(null);

            impactCircle = new google.maps.Circle({
                strokeColor: res.color,
                strokeOpacity: 0.8,
                strokeWeight: 2,
                fillColor: res.color,
                fillOpacity: 0.3,
                map: map,
                center: newPos,
                radius: res.impact_radius_meters || 1000 
            });
        }

    } catch (error) {
        console.error("Audit Error:", error);
        alert("System encountered an error during audit.");
    } finally {
        btn.innerText = "⚡ RUN SYSTEM AUDIT";
        btn.disabled = false;
    }
}

window.onload = initMap;