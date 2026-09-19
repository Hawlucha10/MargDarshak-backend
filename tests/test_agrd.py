"""
Unit tests for AGRD spatial calculations.
"""

from app.core.agrd import haversine_distance_km, point_in_ellipse


def test_haversine_distance_known():
    # New Delhi (approx 28.6139, 77.2090) to Mumbai (approx 19.0760, 72.8777) ~ 1150-1200 km
    dist = haversine_distance_km(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1100 <= dist <= 1250


def test_point_in_ellipse_intermediate():
    # Gwalior (26.2183, 78.1828) to Pune (18.5204, 73.8567)
    # Bhopal (23.2599, 77.4126) lies right in the corridor between Gwalior and Pune
    gwl = (26.2183, 78.1828)
    pune = (18.5204, 73.8567)
    bhopal = (23.2599, 77.4126)

    is_inside = point_in_ellipse(
        bhopal[0], bhopal[1],
        gwl[0], gwl[1],
        pune[0], pune[1],
        focal_slack=1.3,
    )
    assert is_inside is True


def test_point_in_ellipse_far_away():
    # Kolkata (22.5726, 88.3639) should NOT be in the Gwalior -> Pune corridor ellipse
    gwl = (26.2183, 78.1828)
    pune = (18.5204, 73.8567)
    kolkata = (22.5726, 88.3639)

    is_inside = point_in_ellipse(
        kolkata[0], kolkata[1],
        gwl[0], gwl[1],
        pune[0], pune[1],
        focal_slack=1.3,
    )
    assert is_inside is False
