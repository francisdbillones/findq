document.addEventListener('DOMContentLoaded', () => {
    let submit_button = document.getElementById('submit_button');
    let lat_text = document.getElementById('lat_text');
    let lon_text = document.getElementById('lon_text');

    let lat_input = document.getElementById('lat_input');
    let lon_input = document.getElementById('lon_input');

    navigator.geolocation.getCurrentPosition((position) => {
        let lat = position.coords.latitude;
        let lon = position.coords.longitude;

        lat_input.value = lat;
        lon_input.value = lon;

        lat_text.innerText = `Latitude: ${lat.toFixed(3)}°`;
        lon_text.innerText = `Longitude: ${lon.toFixed(3)}°`;

        lat_text.classList.remove('list-group-item-warning');
        lat_text.classList.add('list-group-item-success');
        lon_text.classList.remove('list-group-item-warning');
        lon_text.classList.add('list-group-item-success');

        submit_button.disabled = false;
    }, () => {
        lat_text.innerText = 'Error loading latitude';
        lon_text.innerText = 'Error loading longitude';
    })
});