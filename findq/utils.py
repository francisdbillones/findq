def generate_gmaps_embed_link(lat: float, lon: float, zoom: int):
    return f"//maps.google.com/maps?q={lat},{lon}&z={zoom}&output=embed"
