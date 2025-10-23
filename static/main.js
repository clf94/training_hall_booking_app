async function loadOccupancy() {
try {
const resp = await fetch('/occupancy');
const j = await resp.json();
const box = document.getElementById('occupancy-box');
box.innerHTML = `<p>${j.occupied} / ${j.capacity} occupied</p>`;
if (j.bookings.length) {
let html = '<ul>';
j.bookings.forEach(b => {
html += `<li>#${b.booking_id} ${b.user}` + (b.partner ? ` + ${b.partner}` : '') + (b.checked_in ? ' (checked in)' : '') + '</li>'
})
html += '</ul>';
box.innerHTML += html;
}
} catch (e) {
console.error(e);
}
}
// Poll occupancy every 5 seconds
setInterval(loadOccupancy, 5000);
window.addEventListener('load', loadOccupancy);

async function refreshBookings() {
    const resp = await fetch('/bookings_data');
    const data = await resp.json();
    // rebuild bookings table dynamically if needed
}

async function doCheckin(id) {
await fetch('/checkin', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({booking_id: id})});
// refresh
loadOccupancy();
location.reload();
}

async function doDelete(id) {
    if (!confirm('Are you sure you want to delete this booking?')) return;
    await fetch(`/delete/${id}`, { method: 'POST' });
    loadOccupancy();
    location.reload();
}


// Poll occupancy every 5 seconds
setInterval(loadOccupancy, 5000);
window.addEventListener('load', loadOccupancy);