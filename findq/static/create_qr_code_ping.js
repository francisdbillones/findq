document.addEventListener('DOMContentLoaded', () => {
    let lat_text = document.getElementById('lat_text');
    let lon_text = document.getElementById('lon_text');

    let lat_input = document.getElementById('lat_input');
    let lon_input = document.getElementById('lon_input');

    navigator.geolocation.getCurrentPosition((position) => {
        let lat = position.coords.latitude;
        let lon = position.coords.longitude;

        lat_text.innerText = lat.toFixed(3);
        lon_text.innerText = lon.toFixed(3);

        lat_input.value = lat;
        lon_input.value = lon;
    })
});